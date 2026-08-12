import { ref } from 'vue'
import type { Ref } from 'vue'
import type { JudgeResponse, Verdict } from '@/api/oj'
import {
  evaluateOjStruggle,
  type OjStruggleEvaluationResult,
  type SkillCardSummary,
} from '@/api/orchestrator'
import { buildLearningOverview } from '@/utils/learningOverview'
import { isLoggedIn } from '@/stores/auth'
import {
  markOjStruggleTriggered,
  OJ_STRUGGLE_THRESHOLD,
  recordOjVerdictForStruggle,
  resetOjStruggleSession,
  shouldAutoTriggerOjStruggle,
} from '@/utils/ojStruggleSession'
import {
  lineFromAgentLog,
  linesFromAgentLogs,
  systemLine,
  type AgentConsoleLine,
} from '@/utils/agentConsole'

export interface OjStruggleInterventionView {
  loading: boolean
  consecutiveFailures: number
  errorPattern: string
  fallbackMode: boolean
  fallbackMessage: string
  errorMessage: string
  result: OjStruggleEvaluationResult | null
  memoryWritten: boolean
  masteryLinked: boolean
  pathAdjustSuggested: boolean
}

export function useOjStruggleIntervention(options: {
  slug: Ref<string>
  result: Ref<JudgeResponse | null>
  inferErrorPattern: (res: JudgeResponse | null) => string
  inferKnowledgePoint: () => string
  inferModuleKey: () => string
  onAgentLogs?: (lines: AgentConsoleLine[]) => void
  onStruggleComplete?: (res: OjStruggleEvaluationResult) => void | Promise<void>
}) {
  const struggleView = ref<OjStruggleInterventionView | null>(null)
  let struggleInFlight = false

  function buildFallbackMessage(verdict: Verdict, count: number): string {
    return `本题已连续 ${count} 次未通过（${verdict}）。建议先使用「AI 诊断」或「可视化调试」定位错因，复习相关先修模块后再提交。登录后可由 EvaluatorAgent 自动写入学习记忆并调整路径。`
  }

  function applyAgentLogs(res: OjStruggleEvaluationResult) {
    const lines: AgentConsoleLine[] = [
      systemLine('OJ 连续受挫 · EvaluatorAgent 自动干预', 'running'),
      ...linesFromAgentLogs(res.agent_logs),
    ]
    options.onAgentLogs?.(lines)
  }

  async function triggerOjStruggleIntervention(verdict: Verdict) {
    const slug = options.slug.value
    const count = recordOjVerdictForStruggle(slug, verdict)
    if (verdict === 'AC' || count < OJ_STRUGGLE_THRESHOLD) {
      if (verdict === 'AC') struggleView.value = null
      return
    }
    if (!shouldAutoTriggerOjStruggle(slug) || struggleInFlight) return

    const errorPattern = options.inferErrorPattern(options.result.value)
    markOjStruggleTriggered(slug)
    struggleInFlight = true

    if (!isLoggedIn.value) {
      struggleView.value = {
        loading: false,
        consecutiveFailures: count,
        errorPattern,
        fallbackMode: true,
        fallbackMessage: buildFallbackMessage(verdict, count),
        errorMessage: '',
        result: null,
        memoryWritten: false,
        masteryLinked: false,
        pathAdjustSuggested: false,
      }
      struggleInFlight = false
      return
    }

    struggleView.value = {
      loading: true,
      consecutiveFailures: count,
      errorPattern,
      fallbackMode: false,
      fallbackMessage: '',
      errorMessage: '',
      result: null,
      memoryWritten: false,
      masteryLinked: false,
      pathAdjustSuggested: false,
    }
    options.onAgentLogs?.([
      systemLine('OJ 连续受挫 · EvaluatorAgent 自动干预', 'running'),
      lineFromAgentLog({
        agent: 'EvaluatorAgent',
        action: '分析学习短板',
        detail: `连续 ${count} 次未通过（${verdict}），正在调用 oj-struggle…`,
        status: 'running',
      }),
    ])

    const overview = buildLearningOverview()
    try {
      const evalRes = await evaluateOjStruggle({
        module_key: options.inferModuleKey(),
        problem_slug: slug,
        knowledge_point: options.inferKnowledgePoint(),
        verdict,
        consecutive_failures: count,
        error_pattern: errorPattern,
        overall_percent: overview.overallPercent,
        modules: overview.rows.map((r) => ({
          key: r.key,
          label: r.label,
          phase: r.phase,
          available: r.available,
          percent: r.percent,
          done_count: r.doneCount,
          total_count: r.totalCount,
        })),
      })

      applyAgentLogs(evalRes)
      await options.onStruggleComplete?.(evalRes)

      const masteryLinked = evalRes.agent_logs.some(
        (l) =>
          /Mastery|掌握度/i.test(l.agent) ||
          /mastery|掌握度/i.test(l.detail ?? ''),
      )

      struggleView.value = {
        loading: false,
        consecutiveFailures: count,
        errorPattern,
        fallbackMode: !evalRes.struggle_detected,
        fallbackMessage: evalRes.struggle_detected
          ? ''
          : `已记录 ${count} 次未通过，当前掌握度暂未触发路径降级（${evalRes.agent_logs[0]?.detail ?? '继续练习'}）。`,
        errorMessage: '',
        result: evalRes,
        memoryWritten: evalRes.struggle_detected,
        masteryLinked: masteryLinked || evalRes.struggle_detected,
        pathAdjustSuggested: evalRes.struggle_detected && (evalRes.planner_notified || evalRes.path_updated),
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'oj-struggle 请求失败'
      struggleView.value = {
        loading: false,
        consecutiveFailures: count,
        errorPattern,
        fallbackMode: true,
        fallbackMessage: buildFallbackMessage(verdict, count),
        errorMessage: msg,
        result: null,
        memoryWritten: false,
        masteryLinked: false,
        pathAdjustSuggested: false,
      }
      options.onAgentLogs?.([
        systemLine('OJ 连续受挫干预失败，已降级为本地提示', 'warn'),
        lineFromAgentLog({
          agent: 'EvaluatorAgent',
          action: 'oj-struggle 不可用',
          detail: msg,
          status: 'warn',
        }),
      ])
    } finally {
      struggleInFlight = false
    }
  }

  function onVerdictRecorded(verdict: Verdict | undefined) {
    if (!verdict) return
    void triggerOjStruggleIntervention(verdict)
  }

  function resetStruggleForSlug(slug?: string) {
    resetOjStruggleSession(slug)
    struggleView.value = null
    struggleInFlight = false
  }

  return {
    struggleView,
    onVerdictRecorded,
    resetStruggleForSlug,
    OJ_STRUGGLE_THRESHOLD,
  }
}

export type { SkillCardSummary }
