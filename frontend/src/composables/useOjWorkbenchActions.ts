import { ref, type Ref, watch } from 'vue'
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
  fetchOjCapabilities,
  inferTraceCpp,
  type JudgeResponse,
  type OjLanguage,
  type ProblemDetail,
  type Verdict,
} from '@/api/oj'
import type { AiDiagnoseResponse, TraceBugDiagnoseResponse, TraceResponse } from '@/types/codeTrace'
import { evaluateOjStruggle } from '@/api/orchestrator'
import { buildLearningOverview } from '@/utils/learningOverview'
import { isLoggedIn } from '@/stores/auth'
import { showJudgeResultMessage } from '@/utils/ojErrors'
import {
  diagnosisBootstrapLines,
  linesFromAgentLogs,
  type AgentConsoleLine,
} from '@/utils/agentConsole'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'

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
  router: Router
  loginRedirect: () => string
}) {
  const running = ref(false)
  const submitting = ref(false)
  const tracing = ref(false)
  const narrating = ref(false)
  const diagnosing = ref(false)
  /** 一键可视化诊断（Trace + AI 破案）进行中 */
  const visualTraceDiagnosing = ref(false)
  const traceSplitOpen = ref(false)
  /** 发起 trace 时快照的源码，避免分屏重挂载后行号与编辑器内容错位 */
  const traceSourceCode = ref('')
  const agentConsoleLines = ref<AgentConsoleLine[]>([])
  const consecutiveFailures = ref(0)
  const { loadPlan } = useLearningPathPlan()

  function recordVerdict(verdict: Verdict | undefined) {
    if (!verdict || verdict === 'AC') {
      consecutiveFailures.value = 0
      return
    }
    if (verdict === 'WA' || verdict === 'RE' || verdict === 'TLE' || verdict === 'CE') {
      consecutiveFailures.value += 1
    }
  }

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

  async function maybeTriggerStruggleReplan(verdict: Verdict | undefined) {
    if (!isLoggedIn.value || consecutiveFailures.value < 3) return
    if (!verdict || verdict === 'AC') return
    const overview = buildLearningOverview()
    try {
      const evalRes = await evaluateOjStruggle({
        module_key: '',
        problem_slug: options.slug.value,
        knowledge_point: inferKnowledgePoint(),
        verdict,
        consecutive_failures: consecutiveFailures.value,
        error_pattern: inferErrorPattern(options.result.value),
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
      agentConsoleLines.value = [
        ...diagnosisBootstrapLines(),
        ...linesFromAgentLogs(evalRes.agent_logs),
      ]
      if (evalRes.path_updated) {
        await loadPlan()
        ElMessage.success(
          `PlannerAgent 已插入巩固关卡：${evalRes.remediation_label || evalRes.remediation_module_key}`,
        )
      }
    } catch {
      /* 降级路径失败不阻断诊断 */
    }
  }

  function closeTraceSplit() {
    traceSplitOpen.value = false
  }

  watch(options.slug, () => {
    traceSplitOpen.value = false
    consecutiveFailures.value = 0
    agentConsoleLines.value = []
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
      void maybeTriggerStruggleReplan(options.result.value?.verdict)
    } catch {
      /* judgeClient 拦截器已提示 */
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
      void maybeTriggerStruggleReplan(options.result.value?.verdict)
    } catch {
      /* judgeClient 拦截器已提示 */
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
      ElMessage.warning('可视化诊断失败，请检查判题服务与 SILICONFLOW_API_KEY')
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
    try {
      options.trace.value = await traceExecution(
        options.slug.value,
        options.code.value,
        options.language.value,
      )
      if (options.trace.value.verdict === 'OK') {
        ElMessage.success(`已生成 ${options.trace.value.steps.length} 步执行动画`)
      } else {
        ElMessage.error(options.trace.value.message.slice(0, 160))
      }
    } catch {
      /* judgeClient 拦截器已提示 */
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
      ElMessage.warning('旁白生成失败，请检查 SILICONFLOW_API_KEY')
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
    agentConsoleLines.value = diagnosisBootstrapLines()
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
      if (res.trace?.steps?.length) traceSplitOpen.value = true
      const verdict = options.result.value?.verdict ?? 'WA'
      recordVerdict(verdict)
      await maybeTriggerStruggleReplan(verdict)
      ElMessage.success('AI 诊断完成：已生成边界测例与可视化回放')
    } catch {
      ElMessage.warning('AI 诊断失败，请检查 SILICONFLOW_API_KEY 与判题服务')
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
    onRun,
    onSubmit,
    onTrace,
    onNarrate,
    onAiDiagnose,
    onVisualTraceDiagnose,
    refreshTraceCaps,
    agentConsoleLines,
    consecutiveFailures,
  }
}
