import { computed, ref, type Ref, watch } from 'vue'
import type { Router } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  probeApiOnline,
  runSamples,
  submitCode,
  traceExecution,
  traceNarration,
  traceBugDiagnose,
  aiDiagnose,
  fetchTraceReport,
  fetchOjCapabilities,
  inferTraceCpp,
  type JudgeResponse,
  type OjLanguage,
  type ProblemDetail,
  type Verdict,
} from '@/api/oj'
import type { AiDiagnoseResponse, TraceBugDiagnoseResponse, TraceDiagnosisReport, TraceResponse } from '@/types/codeTrace'
import { isLoggedIn } from '@/stores/auth'
import { showJudgeResultMessage } from '@/utils/ojErrors'
import { recordOjPractice } from '@/utils/ojPracticeHistory'
import {
  astAnalyzerLine,
  systemLine,
  traceBootstrapLines,
  linesFromEventLogs,
  type AgentConsoleLine,
} from '@/utils/agentConsole'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'
import { useLearningPathStore } from '@/stores/pinia/learningPath'
import { usePersonaUi } from '@/composables/usePersonaUiProvider'
import { useOjStruggleIntervention } from '@/composables/useOjStruggleIntervention'
import { getConsecutiveFailures } from '@/utils/ojStruggleSession'
import type { OjStruggleEvaluationResult } from '@/api/orchestrator'

export function useOjWorkbenchActions(options: {
  slug: Ref<string>
  code: Ref<string>
  language: Ref<OjLanguage>
  problem: Ref<ProblemDetail | null>
  apiOnline: Ref<boolean>
  traceCpp: Ref<boolean>
  result: Ref<JudgeResponse | null>
  trace: Ref<TraceResponse | null>
  diagnosis: Ref<AiDiagnoseResponse | null>
  traceBugDiagnosis: Ref<TraceBugDiagnoseResponse | null>
  traceReport: Ref<TraceDiagnosisReport | null>
  traceReportLoading: Ref<boolean>
  router: Router
  loginRedirect: () => string
}) {
  const personaUi = usePersonaUi()
  const running = ref(false)
  const submitting = ref(false)
  const tracing = ref(false)
  const narrating = ref(false)
  const diagnosing = ref(false)
  const visualTraceDiagnosing = ref(false)
  const traceSplitOpen = ref(false)
  const traceSourceCode = ref('')
  const agentConsoleLines = ref<AgentConsoleLine[]>([])
  const { loadPlan, recordExternalReplan } = useLearningPathPlan()
  const pathStore = useLearningPathStore()

  function inferErrorPattern(res: JudgeResponse | null): string {
    const msg = res?.cases?.find((c) => c.verdict !== 'AC')?.message ?? ''
    if (/边界|overflow|越界/i.test(msg)) return '边界溢出'
    if (/timeout|TLE/i.test(msg)) return '超时'
    if (/null|空指针/i.test(msg)) return '空指针'
    return msg.slice(0, 40) || res?.verdict || 'WA'
  }

  function inferKnowledgePoint(): string {
    const title = options.problem.value?.title ?? ''
    const slug = options.slug.value
    const hints = ['动态规划', 'dp', '二叉树', 'tree', '贪心', '回溯', '图', 'graph', '数组', '链表']
    for (const h of hints) {
      if (title.includes(h) || slug.includes(h)) return h
    }
    return title || slug
  }

  function inferModuleKey(): string {
    const declared = options.problem.value?.module_key?.trim()
    if (declared) return declared
    const slug = options.slug.value
    const title = options.problem.value?.title ?? ''
    const pairs: [string, string][] = [
      ['dp', 'dp'],
      ['linked', 'linked-list'],
      ['list', 'linked-list'],
      ['tree', 'binary-tree'],
      ['graph', 'graph'],
      ['greedy', 'greedy'],
      ['monotonic', 'monotonic-stack'],
      ['sorting', 'sorting'],
      ['sort', 'sorting'],
      ['queue', 'stack-queue'],
      ['stack', 'stack-queue'],
      ['hash', 'hash-table'],
    ]
    for (const [hint, key] of pairs) {
      if (slug.includes(hint) || title.includes(hint)) return key
    }
    return ''
  }

  async function onStruggleComplete(evalRes: OjStruggleEvaluationResult) {
    if (!evalRes.path_updated) return
    const beforeKeys = [...(pathStore.plan?.ordered_keys ?? [])]
    const beforeSteps = pathStore.plan?.steps ?? []
    await loadPlan()
    await recordExternalReplan(
      beforeKeys,
      {
        trigger: 'oj_struggle',
        triggerLabel: 'OJ 连续受挫自动干预',
        evidence: [
          `连续 ${evalRes.consecutive_failures} 次未通过`,
          evalRes.remediation_label ? `巩固关卡：${evalRes.remediation_label}` : '',
          evalRes.plan_summary,
          inferErrorPattern(options.result.value)
            ? `错因模式：${inferErrorPattern(options.result.value)}`
            : '',
        ].filter(Boolean),
      },
      beforeSteps,
    )
    ElMessage.success(
      `PlannerAgent 已插入巩固关卡：${evalRes.remediation_label || evalRes.remediation_module_key}`,
    )
  }

  const consecutiveFailures = computed(() => getConsecutiveFailures(options.slug.value))

  const { struggleView, onVerdictRecorded, resetStruggleForSlug } = useOjStruggleIntervention({
    slug: options.slug,
    result: options.result,
    inferErrorPattern,
    inferKnowledgePoint,
    inferModuleKey,
    onAgentLogs: (lines) => {
      agentConsoleLines.value = lines
    },
    onStruggleComplete,
  })

  let traceReportRequestId = 0

  function invalidateTraceReport() {
    traceReportRequestId += 1
    options.traceReportLoading.value = false
    options.traceReport.value = null
  }

  async function autoTriggerTraceReport(verdict: Verdict | undefined) {
    if (!verdict || verdict === 'AC') return
    if (!options.apiOnline.value) return
    if (!options.problem.value?.ready) return
    if (!options.code.value.trim()) return

    const requestId = ++traceReportRequestId
    options.traceReportLoading.value = true
    options.traceReport.value = null
    try {
      const failed = options.result.value?.cases.filter((c) => c.verdict !== 'AC') ?? []
      const report = await fetchTraceReport(options.slug.value, {
        code: options.code.value,
        language: options.language.value,
        judge_verdict: verdict,
        failed_cases: failed,
      })
      if (requestId === traceReportRequestId) {
        options.traceReport.value = report
      }
    } catch {
      if (requestId === traceReportRequestId) {
        options.traceReport.value = null
      }
    } finally {
      if (requestId === traceReportRequestId) {
        options.traceReportLoading.value = false
      }
    }
  }

  function recordVerdict(verdict: Verdict | undefined) {
    if (!verdict) return
    recordOjPractice(options.slug.value, verdict)
  }

  function closeTraceSplit() {
    traceSplitOpen.value = false
  }

  function openDiagnosisTrace() {
    if (!options.trace.value?.steps.length) {
      ElMessage.info('当前诊断没有可回放的执行轨迹')
      return
    }
    traceSplitOpen.value = true
  }

  watch(options.slug, () => {
    traceSplitOpen.value = false
    agentConsoleLines.value = []
    invalidateTraceReport()
    resetStruggleForSlug(options.slug.value)
  })

  async function ensureApiOnline(): Promise<boolean> {
    if (options.apiOnline.value) return true
    options.apiOnline.value = await probeApiOnline()
    if (!options.apiOnline.value) {
      ElMessage.warning(
        '判题服务未连接。请在 backend 目录执行：uvicorn main:app --port 9000',
      )
    }
    return options.apiOnline.value
  }

  async function refreshTraceCaps() {
    const caps = await fetchOjCapabilities()
    options.traceCpp.value = inferTraceCpp(caps)
  }

  async function onRun() {
    if (!(await ensureApiOnline())) return
    if (!options.problem.value?.ready) {
      ElMessage.warning('本题测例尚未配置，暂无法运行（可先写代码）')
      return
    }
    running.value = true
    invalidateTraceReport()
    options.result.value = null
    options.traceBugDiagnosis.value = null
    try {
      options.result.value = await runSamples(
        options.slug.value,
        options.code.value,
        options.language.value,
      )
      showJudgeResultMessage(options.result.value, 'run')
      recordVerdict(options.result.value?.verdict)
      onVerdictRecorded(options.result.value?.verdict)
      autoTriggerTraceReport(options.result.value?.verdict)
    } catch {
      ElMessage.warning('运行请求失败，请检查网络或判题服务')
    } finally {
      running.value = false
    }
  }

  async function onSubmit() {
    if (!isLoggedIn.value) {
      ElMessage.warning('提交需先登录')
      options.router.push({
        name: 'login',
        query: { redirect: options.loginRedirect() },
      })
      return
    }
    if (!(await ensureApiOnline())) return
    if (!options.problem.value?.ready) {
      ElMessage.warning('本题测例尚未配置，暂无法提交')
      return
    }
    submitting.value = true
    invalidateTraceReport()
    options.result.value = null
    options.traceBugDiagnosis.value = null
    try {
      options.result.value = await submitCode(
        options.slug.value,
        options.code.value,
        options.language.value,
      )
      showJudgeResultMessage(options.result.value, 'submit')
      recordVerdict(options.result.value?.verdict)
      if (options.result.value?.event_logs?.length) {
        agentConsoleLines.value = linesFromEventLogs(options.result.value.event_logs)
      }
      onVerdictRecorded(options.result.value?.verdict)
      autoTriggerTraceReport(options.result.value?.verdict)
      if (options.result.value?.verdict === 'AC') {
        await loadPlan().catch(() => {})
      }
    } catch {
      ElMessage.warning('提交请求失败，请检查网络或判题服务')
    } finally {
      submitting.value = false
    }
  }

  function clampBugStepIndex(index: number, stepCount: number): number {
    const max = stepCount > 0 ? stepCount - 1 : 0
    return Math.max(0, Math.min(index, max))
  }

  function pickTraceCaseIndex(): number {
    const failed = options.result.value?.cases.filter((c) => c.verdict !== 'AC') ?? []
    const failedIndex = failed[0]?.index
    if (failedIndex !== undefined) {
      const sampleCount = options.problem.value?.samples?.length ?? 0
      if (sampleCount > 0 && failedIndex >= sampleCount) return 0
      return failedIndex
    }
    return 0
  }

  async function onVisualTraceDiagnose() {
    if (!(await ensureApiOnline())) return
    if (!options.problem.value?.ready) {
      ElMessage.warning('本题测例尚未配置，暂无法可视化诊断')
      return
    }
    if (options.apiOnline.value) await refreshTraceCaps()
    if (!options.code.value.trim()) {
      ElMessage.warning('请先编写代码，再使用可视化诊断')
      return
    }
    visualTraceDiagnosing.value = true
    options.traceBugDiagnosis.value = null
    options.trace.value = null
    options.diagnosis.value = null
    traceSourceCode.value = options.code.value
    try {
      const caseIndex = pickTraceCaseIndex()
      const traceRes = await traceExecution(
        options.slug.value,
        options.code.value,
        options.language.value,
        caseIndex,
      )
      options.trace.value = traceRes

      if (traceRes.steps.length > 0) {
        const bugRes = await traceBugDiagnose(options.slug.value, {
          code: traceSourceCode.value,
          language: options.language.value,
          steps: traceRes.steps,
          problem_description: options.problem.value?.description,
          judge_verdict: options.result.value?.verdict ?? 'WA',
        })
        const idx = clampBugStepIndex(bugRes.bug_step_index, traceRes.steps.length)
        options.traceBugDiagnosis.value = { ...bugRes, bug_step_index: idx }
      }

      traceSplitOpen.value = true
      if (options.traceBugDiagnosis.value) {
        ElMessage.success(
          `AI 已定位第 ${options.traceBugDiagnosis.value.bug_step_index + 1} 步，已跳转至可疑帧`,
        )
      } else if (traceRes.verdict === 'OK') {
        ElMessage.success(`已生成 ${traceRes.steps.length} 步执行动画`)
      } else {
        ElMessage.warning(traceRes.message.slice(0, 160))
      }
    } catch {
      ElMessage.warning('可视化诊断失败，请检查判题服务与代码是否可执行')
    } finally {
      visualTraceDiagnosing.value = false
    }
  }

  async function onTrace() {
    if (!(await ensureApiOnline())) return
    if (!options.problem.value?.ready) {
      ElMessage.warning('本题测例尚未配置，暂无法可视化调试')
      return
    }
    if (options.apiOnline.value) await refreshTraceCaps()
    if (!options.code.value.trim()) {
      ElMessage.warning('请先编写代码，再使用可视化调试')
      return
    }
    traceSplitOpen.value = true
    tracing.value = true
    traceSourceCode.value = options.code.value
    options.trace.value = null
    options.traceBugDiagnosis.value = null
    agentConsoleLines.value = traceBootstrapLines()
    try {
      const traceRes = await traceExecution(
        options.slug.value,
        options.code.value,
        options.language.value,
      )
      options.trace.value = traceRes
      if (traceRes.static_audit?.status === 'rejected') {
        const lines = [systemLine('可视化调试管线 — 静动结合双轨诊断', 'warn')]
        if (personaUi.value.showAstAudit) {
          lines.push(astAnalyzerLine(false, traceRes.static_audit.reason ?? traceRes.message))
        }
        agentConsoleLines.value = lines
        ElMessage.error(traceRes.message.slice(0, 200))
      } else {
        const lines = [systemLine('可视化调试管线 — 静动结合双轨诊断', 'success')]
        if (personaUi.value.showAstAudit) {
          lines.push(astAnalyzerLine(true))
        }
        agentConsoleLines.value = lines
        if (traceRes.verdict === 'OK') {
          ElMessage.success(`已生成 ${traceRes.steps.length} 步执行动画`)
        } else {
          ElMessage.error(traceRes.message.slice(0, 160))
        }
      }
    } catch {
      ElMessage.warning('追踪请求失败，请检查网络或判题服务')
    } finally {
      tracing.value = false
    }
  }

  async function onNarrate() {
    if (!options.trace.value?.steps.length) return
    narrating.value = true
    try {
      const res = await traceNarration(options.slug.value, {
        code: options.code.value,
        language: options.language.value,
        steps: options.trace.value.steps,
        problem_title: options.problem.value?.title,
      })
      options.trace.value = { ...options.trace.value, narrations: res.narrations }
      ElMessage.success('AI 旁白已生成')
    } catch {
      ElMessage.warning('旁白生成失败，请检查判题服务；无 API Key 时将使用规则旁白')
    } finally {
      narrating.value = false
    }
  }

  async function onAiDiagnose() {
    if (!(await ensureApiOnline())) return
    if (!options.problem.value?.ready) {
      ElMessage.warning('本题测例尚未配置，暂无法 AI 诊断')
      return
    }
    if (!options.code.value.trim()) {
      ElMessage.warning('请先编写代码，再使用 AI 诊断')
      return
    }
    diagnosing.value = true
    agentConsoleLines.value = []
    options.diagnosis.value = null
    options.trace.value = null
    options.traceBugDiagnosis.value = null
    traceSourceCode.value = options.code.value
    try {
      const failed = options.result.value?.cases.filter((c) => c.verdict !== 'AC') ?? []
      const res = await aiDiagnose(options.slug.value, {
        code: options.code.value,
        language: options.language.value,
        judge_verdict: options.result.value?.verdict,
        failed_cases: failed,
      })
      options.diagnosis.value = res
      options.trace.value = res.trace
      if (res.diagnosis) {
        options.traceBugDiagnosis.value = {
          bug_step_index: res.diagnosis.bug_step_index,
          diagnosis_title: res.diagnosis.title,
          detailed_analysis: res.diagnosis.root_cause,
          source: res.diagnosis.source,
          fix_suggestion: res.diagnosis.fix_direction,
          tutoring: res.tutoring,
        }
      }
      const verdict = options.result.value?.verdict
      if (verdict) {
        recordVerdict(verdict)
        onVerdictRecorded(verdict)
      }
      ElMessage.success('AI 诊断完成：已生成失败证据与分层提示')
    } catch {
      ElMessage.warning('诊断失败，请检查判题服务；无 API Key 时系统将自动使用规则诊断')
    } finally {
      diagnosing.value = false
    }
  }

  return {
    running,
    submitting,
    tracing,
    narrating,
    diagnosing,
    visualTraceDiagnosing,
    traceSplitOpen,
    traceSourceCode,
    closeTraceSplit,
    openDiagnosisTrace,
    onRun,
    onSubmit,
    onTrace,
    onNarrate,
    onAiDiagnose,
    onVisualTraceDiagnose,
    refreshTraceCaps,
    agentConsoleLines,
    consecutiveFailures,
    struggleView,
  }
}
