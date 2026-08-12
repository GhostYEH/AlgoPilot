<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { Medal, Refresh, VideoPlay, Upload, View, MagicStick } from '@element-plus/icons-vue'
import CodeEditor from '@/components/oj/CodeEditor.vue'
import OjAiDiagnosisPanel from '@/components/oj/OjAiDiagnosisPanel.vue'
import OjStruggleInterventionPanel from '@/components/oj/OjStruggleInterventionPanel.vue'
import OjTraceDiagnosisReport from '@/components/oj/OjTraceDiagnosisReport.vue'
import OjDsHintCard from '@/components/oj/OjDsHintCard.vue'
import OjCodeHintCard from '@/components/oj/OjCodeHintCard.vue'
import AgentThinkingConsole from '@/components/agents/AgentThinkingConsole.vue'
import type { OjStruggleInterventionView } from '@/composables/useOjStruggleIntervention'
import type { AgentConsoleLine } from '@/utils/agentConsole'
import type { JudgeResponse, ProblemDetail, Verdict } from '@/api/oj'
import type { AiDiagnoseResponse, TraceDiagnosisReport } from '@/types/codeTrace'
import {
  formatSampleInput,
  formatSampleOutput,
  isStdioJudgeMode,
} from '@/utils/ojSampleFormat'
import { useTraceHighlightLine } from '@/composables/useTraceHighlight'
import { getStarterForLanguage } from '@/utils/ojStarterCode'
import { renderAiReplyHtml } from '@/utils/renderAiReply'

const code = defineModel<string>({ required: true })
const language = defineModel<'python' | 'cpp'>('language', { default: 'python' })

const props = defineProps<{
  problem: ProblemDetail
  running?: boolean
  submitting?: boolean
  tracing?: boolean
  diagnosing?: boolean
  visualTraceDiagnosing?: boolean
  result?: JudgeResponse | null
  diagnosis?: AiDiagnoseResponse | null
  traceReport?: TraceDiagnosisReport | null
  traceReportLoading?: boolean
  apiOnline?: boolean
  traceCpp?: boolean
  /** 可视化分屏：仅保留代码编辑区 */
  traceLayout?: boolean
  agentConsoleLines?: AgentConsoleLine[]
  struggleView?: OjStruggleInterventionView | null
  consecutiveFailures?: number
}>()

const emit = defineEmits<{
  run: []
  submit: []
  reset: []
  trace: []
  diagnose: []
  visualTraceDiagnose: []
  viewDiagnosisTrace: []
  demo: []
}>()

const fontSize = ref('14px')
const diagnosisPanelRef = ref<{ $el?: HTMLElement } | null>(null)
const traceHighlightLine = useTraceHighlightLine()

const renderedDesc = computed(() => renderAiReplyHtml(props.problem.description ?? ''))

const VERDICT_LABEL: Record<Verdict, string> = {
  AC: '通过',
  WA: '答案错误',
  TLE: '超时',
  RE: '运行错误',
  CE: '编译错误',
}

const editorHeight = computed(() => {
  if (props.traceLayout) return 'calc(100vh - var(--alp-header-height, 60px) - 120px)'
  return props.result ? '360px' : '440px'
})

const stdioMode = computed(() =>
  isStdioJudgeMode(props.problem.judge_mode, props.problem.entry),
)

const canTrace = computed(() => {
  if (!props.problem.ready) return false
  if (language.value === 'cpp' && props.traceCpp === false) return false
  return true
})

const judging = computed(() => props.running || props.submitting)

const busy = computed(() => props.running || props.submitting || props.tracing || props.diagnosing)

const hasJudgeDemo = computed(() => props.problem.slug === 'reverse-linked-list')

const traceDisableReason = computed(() => {
  if (props.apiOnline === false) return '判题服务未连接'
  if (!props.problem.ready) return '本题测例完善中'
  if (language.value === 'cpp' && !props.traceCpp) {
    return '若 C++ 追踪失败，请确认已安装 MinGW g++/gdb 并重启后端；Python 3 无需 gdb'
  }
  return ''
})

const langHint = computed(() => {
  if (stdioMode.value) {
    return language.value === 'cpp'
      ? 'C++17 · 洛谷风格 main + cin/cout'
      : 'Python 3 · 洛谷风格 stdin/stdout'
  }
  return language.value === 'cpp'
    ? 'C++17（需本机 g++，力扣风格 class Solution）'
    : 'Python 3'
})

function diffLabel(d: string) {
  if (d === 'easy') return '简单'
  if (d === 'hard') return '困难'
  return '中等'
}

function applyStarter() {
  code.value = getStarterForLanguage(props.problem, language.value)
}

watch(language, (_lang, prev) => {
  if (prev === undefined) return
  applyStarter()
})

watch(
  () => props.problem.slug,
  (_slug, prev) => {
    // 分屏重挂载时保留用户已编辑代码，避免被模板覆盖
    if (prev === undefined && code.value.trim()) return
    applyStarter()
  },
  { immediate: true },
)

watch(
  () => props.diagnosis,
  async (value) => {
    if (!value || props.traceLayout) return
    await nextTick()
    diagnosisPanelRef.value?.$el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  },
)

function onReset() {
  applyStarter()
  emit('reset')
}
</script>

<template>
  <div class="oj-workbench" :class="{ 'oj-workbench--trace-layout': traceLayout }">
    <aside v-show="!traceLayout" class="oj-problem-pane">
      <header class="problem-header">
        <h2 class="problem-title">{{ problem.title }}</h2>
        <div class="problem-tags">
          <el-tag
            size="small"
            :type="
              problem.difficulty === 'easy'
                ? 'success'
                : problem.difficulty === 'hard'
                  ? 'danger'
                  : 'warning'
            "
          >
            {{ diffLabel(problem.difficulty) }}
          </el-tag>
          <el-tag v-if="problem.ready" type="success" size="small">可提交</el-tag>
          <el-tag v-else type="warning" size="small">测例完善中</el-tag>
          <el-tag v-if="apiOnline === false" type="danger" size="small">判题服务未连接</el-tag>
          <el-tag v-else type="success" size="small">判题服务已连接</el-tag>
        </div>
      </header>

      <div class="problem-scroll">
        <div class="problem-desc" v-html="renderedDesc"></div>
        <template v-if="problem.samples.length">
          <h4 class="block-title">示例</h4>
          <div v-for="(s, i) in problem.samples" :key="i" class="io-block">
            <div class="io-row">
              <span class="io-label">输入</span>
              <pre class="io-val">{{ formatSampleInput(s) }}</pre>
            </div>
            <div class="io-row">
              <span class="io-label">输出</span>
              <pre class="io-val">{{ formatSampleOutput(s) }}</pre>
            </div>
          </div>
        </template>
        <p v-if="stdioMode" class="method-hint">
          洛谷格式：编写完整程序，按上方样例从<strong>标准输入</strong>读入、向<strong>标准输出</strong>写出（{{ langHint }}）
        </p>
        <p v-else-if="problem.entry?.method" class="method-hint">
          力扣判题格式：在 <code>class Solution</code> 中实现
          <code>{{ problem.entry.method }}</code>（方法名需与题目一致，{{ langHint }}）
        </p>
      </div>
    </aside>

    <section class="oj-code-pane">
      <header class="code-pane-header">
        <div class="header-left">
          <span class="pane-title">代码</span>
          <el-select v-model="language" size="small" class="lang-select">
            <el-option label="Python 3" value="python" />
            <el-option label="C++" value="cpp" />
          </el-select>
          <el-select v-model="fontSize" size="small" class="font-select">
            <el-option label="12px" value="12px" />
            <el-option label="14px" value="14px" />
            <el-option label="16px" value="16px" />
          </el-select>
        </div>
        <div class="header-actions">
          <el-button
            v-if="!traceLayout && hasJudgeDemo"
            size="small"
            type="warning"
            plain
            :icon="Medal"
            @click="emit('demo')"
          >
            一键演示：错误代码 → OJ → Trace 诊断
          </el-button>
          <el-button size="small" :icon="Refresh" @click="onReset">重置代码</el-button>
        </div>
      </header>

      <CodeEditor
        v-model="code"
        class="main-editor"
        :language="language"
        :font-size="fontSize"
        :min-height="editorHeight"
        :highlight-line="traceLayout ? traceHighlightLine : 0"
      />

      <footer class="code-pane-footer">
        <el-button :icon="VideoPlay" :loading="running" :disabled="!problem.ready || (busy && !running)" @click="emit('run')">
          运行
        </el-button>
        <el-button
          :icon="View"
          :loading="tracing"
          :disabled="!canTrace || (busy && !tracing)"
          :title="
            traceDisableReason ||
            (language === 'cpp'
              ? 'GDB 单步追踪（需本机 gdb）'
              : stdioMode
                ? '按行追踪 main 程序执行（首个样例 stdin）'
                : '按行记录变量变化并动画回放（首个样例）')
          "
          @click="emit('trace')"
        >
          可视化调试
        </el-button>
        <el-button
          type="danger"
          plain
          :icon="MagicStick"
          :loading="diagnosing"
          :disabled="!canTrace || (busy && !diagnosing)"
          title="追踪真实失败用例（无判题结果时使用首个样例）→ AI 定位首次可疑步骤"
          @click="emit('diagnose')"
        >
          AI 诊断
        </el-button>
        <el-button
          type="primary"
          :icon="Upload"
          :loading="submitting"
          :disabled="!problem.ready || (busy && !submitting)"
          @click="emit('submit')"
        >
          提交
        </el-button>
        <span v-if="apiOnline === false" class="footer-hint">
          判题服务未连接：在 backend 目录执行
          <code>.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 9000</code>
        </span>
        <span v-else-if="!problem.ready" class="footer-hint">
          本题测例完善中，暂无法运行/提交（可先写代码）
        </span>
        <span v-else-if="traceDisableReason" class="footer-hint footer-hint--muted">
          {{ traceDisableReason }}
        </span>
      </footer>

      <div v-if="result" class="console-panel">
        <div v-if="result.verdict !== 'AC'" class="learning-loop-note">
          系统不仅判断对错，还基于 Trace 捕捉学生错误发生的具体步骤，并反向更新学习画像与路径规划。
        </div>
        <div class="verdict-line">
          <el-tag
            :type="
              result.verdict === 'AC'
                ? 'success'
                : result.verdict === 'WA'
                  ? 'warning'
                  : 'danger'
            "
          >
            {{ VERDICT_LABEL[result.verdict as Verdict] }}
          </el-tag>
          <span class="verdict-score">{{ result.passed }} / {{ result.total }} 通过</span>
        </div>

        <pre
          v-for="c in result.cases.filter((x) => x.verdict !== 'AC')"
          :key="c.index"
          class="case-line"
        >用例 {{ c.index + 1 }}：{{ c.message }}</pre>

      </div>
    </section>

    <aside v-if="!traceLayout" class="oj-result-pane">
      <header class="result-pane-header">
        <span class="pane-title">判题结果</span>
        <span class="result-state" :class="result ? `is-${result.verdict.toLowerCase()}` : judging ? 'is-judging' : ''">
          {{ result ? VERDICT_LABEL[result.verdict as Verdict] : judging ? '判题中' : '等待运行' }}
        </span>
      </header>
      <div class="result-pane-body">
        <div v-if="judging" class="result-loading" aria-live="polite">
          <el-skeleton :rows="5" animated />
          <p>{{ submitting ? '正在提交并运行完整测试用例…' : '正在运行样例并同步结果…' }}</p>
        </div>
        <template v-else-if="result">
          <div class="result-summary">
            <div><span>通过用例</span><strong>{{ result.passed }} / {{ result.total }}</strong></div>
            <div><span>判题状态</span><strong>{{ result.verdict }}</strong></div>
          </div>
          <div class="case-table">
            <div class="case-table__head"><span>#</span><span>状态</span><span>结果</span></div>
            <div v-for="item in result.cases" :key="item.index" class="case-table__row">
              <span>{{ item.index + 1 }}</span>
              <span :class="item.verdict === 'AC' ? 'case-ok' : 'case-error'">{{ item.verdict }}</span>
              <span>{{ item.message || (item.verdict === 'AC' ? '通过' : '未通过') }}</span>
            </div>
          </div>
        </template>
        <div v-else class="result-empty">
          <el-icon><VideoPlay /></el-icon>
          <h3>运行代码查看结果</h3>
          <p>测试用例、运行状态和诊断建议会集中显示在这里。</p>
          <ol>
            <li>在中间编辑器完成代码</li>
            <li>点击运行验证样例</li>
            <li>提交后查看完整判题结果</li>
          </ol>
        </div>
      </div>
    </aside>

    <section v-if="!traceLayout" class="oj-ai-hint-row" aria-label="AI 数据结构与思路提示">
      <OjDsHintCard :problem="problem" :language="language" class="oj-ai-hint-cell" />
      <OjCodeHintCard
        :problem="problem"
        :language="language"
        :user-code="code"
        class="oj-ai-hint-cell"
      />
    </section>

    <section
      v-if="!traceLayout && (traceReport || traceReportLoading || struggleView)"
      class="oj-diagnosis-workspace"
      aria-label="AI Trace 诊断结果"
    >
      <OjTraceDiagnosisReport
        v-if="traceReport || traceReportLoading"
        :report="traceReport ?? null"
        :loading="traceReportLoading"
        :consecutive-failures="consecutiveFailures"
      />
      <OjStruggleInterventionPanel :state="struggleView ?? null" />
    </section>

    <AgentThinkingConsole
      v-if="
        !traceLayout &&
        (tracing ||
          struggleView?.loading ||
          (agentConsoleLines?.length ?? 0) > 0)
      "
      class="oj-workbench-agent-console"
      :lines="agentConsoleLines ?? []"
      :active="tracing || struggleView?.loading"
      mode="diagnosis"
      title="Agent Synergy Terminal"
      subtitle="OJ 诊断 · 学情评估 · 路径降级"
    />
    <OjAiDiagnosisPanel
      v-if="!traceLayout"
      ref="diagnosisPanelRef"
      class="oj-workbench-diagnosis"
      :diagnosis="diagnosis ?? null"
      :loading="diagnosing"
      :trace-available="Boolean(diagnosis?.trace?.steps?.length)"
      @view-trace="emit('viewDiagnosisTrace')"
    />
  </div>
</template>

<style scoped>
.oj-workbench {
  display: grid;
  grid-template-columns: minmax(280px, 29%) minmax(420px, 42%) minmax(280px, 29%);
  grid-template-rows: auto auto auto auto auto;
  min-height: 0;
  height: 100%;
  width: 100%;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  overflow-x: hidden;
  overflow-y: auto;
  background: var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
}

.oj-problem-pane {
  grid-column: 1;
  grid-row: 1;
  border-right: 1px solid var(--alp-color-border);
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--alp-bg-surface-muted);
}
.oj-code-pane {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #1e1e1e;
}

.oj-result-pane {
  grid-column: 3;
  grid-row: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-muted);
}

.result-pane-header {
  min-height: 45px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 14px;
  border-bottom: 1px solid var(--alp-color-border);
}
.result-state { font-size: 12px; color: var(--alp-color-muted); }
.result-state.is-ac { color: var(--alp-color-success); }
.result-state.is-wa, .result-state.is-re, .result-state.is-tle, .result-state.is-ce { color: var(--alp-color-danger); }
.result-pane-body { flex: 1; min-height: 0; overflow: auto; padding: 14px; }
.result-loading p { margin: 12px 0 0; color: var(--alp-color-muted); font-size: 12px; text-align: center; }
.result-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border: 1px solid var(--alp-color-border); }
.result-summary > div { padding: 12px; }
.result-summary > div + div { border-left: 1px solid var(--alp-color-border); }
.result-summary span, .result-summary strong { display: block; }
.result-summary span { color: var(--alp-color-muted); font-size: 11px; }
.result-summary strong { margin-top: 5px; color: var(--alp-color-text); font-size: 16px; }
.case-table { margin-top: 14px; border: 1px solid var(--alp-color-border); }
.case-table__head, .case-table__row { display: grid; grid-template-columns: 34px 56px minmax(0, 1fr); gap: 8px; padding: 8px 10px; font-size: 12px; }
.case-table__head { background: var(--alp-bg-soft-block); color: var(--alp-color-muted); font-weight: 600; }
.case-table__row + .case-table__row { border-top: 1px solid var(--alp-color-border); }
.case-ok { color: var(--alp-color-success); }
.case-error { color: var(--alp-color-danger); }
.result-empty { max-width: 280px; margin: 18vh auto 0; color: var(--alp-color-muted); text-align: center; }
.result-empty > .el-icon { font-size: 28px; color: var(--alp-color-primary); }
.result-empty h3 { margin: 12px 0 6px; color: var(--alp-color-text); font-size: 15px; }
.result-empty p { margin: 0; font-size: 12px; line-height: 1.6; }
.result-empty ol { margin: 18px 0 0; padding: 14px 14px 14px 32px; border-top: 1px solid var(--alp-color-border); text-align: left; font-size: 12px; line-height: 2; }

.oj-workbench-agent-console {
  grid-column: 1 / -1;
  grid-row: 4;
  min-width: 0;
  max-height: 220px;
}

.oj-workbench-diagnosis {
  grid-column: 1 / -1;
  grid-row: 5;
  min-width: 0;
  padding: 0 clamp(14px, 2vw, 28px) 24px;
  background: var(--alp-bg-surface-muted);
}

.oj-diagnosis-workspace {
  grid-column: 1 / -1;
  grid-row: 3;
  min-width: 0;
  padding: 18px clamp(14px, 2vw, 28px) 24px;
  border-top: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-muted);
}

/* AI 提示行：代码区下方，左右两栏（数据结构提示 / AI 思路提示） */
.oj-ai-hint-row {
  grid-column: 1 / -1;
  grid-row: 2;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding: 16px clamp(14px, 2vw, 28px);
  border-top: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-muted);
}

.oj-ai-hint-cell {
  min-width: 0;
  display: flex;
}

.oj-ai-hint-cell :deep(.oj-agent-card) {
  width: 100%;
  margin-top: 0;
}

.oj-diagnosis-workspace :deep(.trace-report) {
  margin-top: 0;
  min-height: 360px;
}

.oj-diagnosis-workspace :deep(.oj-struggle-intervention) {
  margin-top: 16px;
}

.oj-workbench--trace-layout {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.oj-workbench--trace-layout .oj-code-pane {
  flex: 1;
  min-height: 0;
}

.problem-header {
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--alp-color-border);
}
.problem-title {
  margin: 0 0 8px;
  font-size: 1.15rem;
  font-weight: 600;
}
.problem-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.problem-scroll {
  flex: 1;
  overflow: auto;
  padding: 12px 16px 20px;
  min-height: 360px;
  max-height: min(560px, calc(100vh - var(--alp-header-height, 60px) - 200px));
}
.problem-desc {
  font-size: 14px;
  line-height: 1.65;
  margin: 0 0 16px;
}
.problem-desc :deep(.ai-md-h) {
  margin: 0 0 8px;
  font-size: 1.05rem;
  font-weight: 600;
}
.problem-desc :deep(.ai-md-h--2) {
  font-size: 1.15rem;
}
.problem-desc :deep(.ai-md-p) {
  margin: 0 0 8px;
}
.problem-desc :deep(.ai-md-code) {
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 0.9em;
  background: var(--el-fill-color-light);
}
.problem-desc :deep(.ai-md-ul),
.problem-desc :deep(.ai-md-ol) {
  margin: 4px 0 8px;
  padding-left: 1.25rem;
}
.problem-desc :deep(.ai-md-pre) {
  margin: 8px 0;
  padding: 8px 12px;
  border-radius: 6px;
  background: var(--el-fill-color-lighter);
  overflow-x: auto;
}
.block-title {
  margin: 0 0 8px;
  font-size: 14px;
}
.io-block {
  margin-bottom: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}
.io-row {
  display: grid;
  grid-template-columns: 52px 1fr;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}
.io-label {
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 600;
  background: var(--el-fill-color-light);
}
.io-val {
  margin: 0;
  padding: 8px 10px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, Consolas, monospace;
}
.method-hint {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.code-pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  background: #252526;
  border-bottom: 1px solid #333;
  min-width: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pane-title {
  font-size: 13px;
  font-weight: 600;
  color: #ccc;
}
.lang-select {
  width: 120px;
}
.font-select {
  width: 88px;
}
.main-editor {
  flex: 1;
}
.main-editor :deep(.oj-editor) {
  border: none;
  border-radius: 0;
}
.code-pane-footer {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 12px;
  background: #252526;
  border-top: 1px solid #333;
}
.footer-hint {
  font-size: 12px;
  color: #f56c6c;
}

.footer-hint--muted {
  color: #a8abb2;
}
.console-panel {
  padding: 10px 12px;
  background: #1a1a1a;
  border-top: 1px solid #333;
  max-height: min(420px, 46vh);
  overflow: auto;
}
.learning-loop-note {
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 40%, #444);
  border-radius: 8px;
  color: #dbeafe;
  background: color-mix(in srgb, var(--el-color-primary) 14%, #1a1a1a);
  font-size: 13px;
  line-height: 1.6;
}
.verdict-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.verdict-score {
  color: #aaa;
  font-size: 13px;
}
.case-line {
  margin: 0;
  font-size: 12px;
  color: #f48771;
  white-space: pre-wrap;
}

@media (min-width: 1400px) {
  .oj-workbench {
    grid-template-columns: minmax(300px, 29%) minmax(440px, 42%) minmax(300px, 29%);
  }
}

@media (max-width: 1100px) {
  .oj-workbench {
    grid-template-columns: 1fr;
    height: auto;
  }

  .oj-problem-pane {
    border-right: none;
    border-bottom: 1px solid var(--alp-color-border);
    grid-row: 1;
  }

  .oj-code-pane { grid-column: 1; grid-row: 2; }
  .oj-result-pane { grid-column: 1; grid-row: 3; min-height: 320px; border-left: 0; border-top: 1px solid var(--alp-color-border); }

  .oj-ai-hint-row {
    grid-row: 4;
    grid-template-columns: 1fr;
  }

  .oj-diagnosis-workspace { grid-row: 5; }
  .oj-workbench-agent-console { grid-row: 6; }
  .oj-workbench-diagnosis { grid-row: 7; }

  .problem-scroll {
    max-height: 320px;
    min-height: 0;
  }
}

@media (max-width: 600px) {
  .oj-workbench,
  .oj-code-pane,
  .main-editor {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .oj-code-pane {
    overflow: hidden;
  }

  .oj-ai-hint-row {
    padding: 12px;
    gap: 10px;
  }

  .code-pane-header {
    flex-wrap: wrap;
    justify-content: flex-start;
    width: 100%;
    box-sizing: border-box;
    overflow: hidden;
  }

  .header-left {
    flex: 1 1 100%;
    flex-wrap: wrap;
  }

  .lang-select {
    width: min(120px, calc(50vw - 28px));
  }

  .font-select {
    width: min(88px, calc(50vw - 28px));
  }

  .code-pane-header > .el-button {
    flex: 1 1 100%;
    margin-left: 0;
  }

  .code-pane-footer {
    align-items: stretch;
  }

  .code-pane-footer :deep(.el-button) {
    flex: 1 1 calc(50% - 8px);
    margin-left: 0;
  }

  .oj-diagnosis-workspace {
    padding: 12px;
  }

  .oj-diagnosis-workspace :deep(.trace-report) {
    min-height: 0;
  }
}
</style>
