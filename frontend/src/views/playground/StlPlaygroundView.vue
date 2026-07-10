<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import TraceSequenceViz from '@/components/oj/trace/TraceSequenceViz.vue'
import TraceAssociativeViz from '@/components/oj/trace/TraceAssociativeViz.vue'
import type { TraceStep, TraceVarSnapshot, TraceVarValue } from '@/types/codeTrace'
import {
  associativeEntries,
  associativeViewHint,
  sequenceItems,
  sequenceViewHint,
  type AssociativeEntry,
  type AssociativeViewHint,
  type SequenceViewHint,
} from '@/utils/traceProtocol'

const VAR_NAME = 'mock_container'

type ContainerId = 'stack' | 'queue' | 'vector' | 'unordered_map'

interface ContainerDef {
  id: ContainerId
  label: string
  cppName: string
  kind: 'sequence' | 'associative'
  viewHint: SequenceViewHint | AssociativeViewHint
}

const CONTAINERS: ContainerDef[] = [
  { id: 'stack', label: 'Stack', cppName: 'std::stack', kind: 'sequence', viewHint: 'stack' },
  { id: 'queue', label: 'Queue', cppName: 'std::queue', kind: 'sequence', viewHint: 'queue' },
  { id: 'vector', label: 'Vector', cppName: 'std::vector', kind: 'sequence', viewHint: 'vector' },
  {
    id: 'unordered_map',
    label: 'Unordered Map',
    cppName: 'std::unordered_map',
    kind: 'associative',
    viewHint: 'unordered_map',
  },
]

interface OpDef {
  id: string
  label: string
  needsValue?: boolean
  needsKey?: boolean
}

const OPS_BY_CONTAINER: Record<ContainerId, OpDef[]> = {
  stack: [
    { id: 'push', label: 'Push', needsValue: true },
    { id: 'pop', label: 'Pop' },
    { id: 'clear', label: 'Clear' },
  ],
  queue: [
    { id: 'enqueue', label: 'Enqueue', needsValue: true },
    { id: 'dequeue', label: 'Dequeue' },
    { id: 'clear', label: 'Clear' },
  ],
  vector: [
    { id: 'push_back', label: 'Push Back', needsValue: true },
    { id: 'pop_back', label: 'Pop Back' },
    { id: 'clear', label: 'Clear' },
  ],
  unordered_map: [
    { id: 'insert', label: 'Insert', needsKey: true, needsValue: true },
    { id: 'erase', label: 'Erase', needsKey: true },
    { id: 'find', label: 'Find', needsKey: true },
  ],
}

const activeContainer = ref<ContainerId>('stack')
const inputValue = ref('42')
const inputKey = ref('foo')
const stepIndex = ref(0)
const lastPseudo = ref('// 选择容器并点击操作按钮开始体验')
const operationLog = ref<string[]>([])

const mockState = ref<TraceVarSnapshot>(emptySequenceSnapshot('stack'))
const prevSnapshot = ref<TraceVarSnapshot | null>(null)
const changedKeys = ref<Set<string>>(new Set())
const lastTraceStep = ref<TraceStep | null>(null)

const activeDef = computed(() => CONTAINERS.find((c) => c.id === activeContainer.value)!)
const currentOps = computed(() => OPS_BY_CONTAINER[activeContainer.value])
const isAssociative = computed(() => activeDef.value.kind === 'associative')

const sequenceItemsCurr = computed(() =>
  !isAssociative.value ? sequenceItems(mockState.value) : [],
)
const sequenceItemsPrev = computed(() =>
  prevSnapshot.value && !isAssociative.value ? sequenceItems(prevSnapshot.value) : [],
)
const sequenceHint = computed(() =>
  !isAssociative.value ? sequenceViewHint(mockState.value) : 'vector',
)

const assocEntriesCurr = computed(() =>
  isAssociative.value ? associativeEntries(mockState.value) : [],
)
const assocEntriesPrev = computed(() =>
  prevSnapshot.value && isAssociative.value ? associativeEntries(prevSnapshot.value) : [],
)
const assocHint = computed(() =>
  isAssociative.value ? associativeViewHint(mockState.value) : 'unordered_map',
)

const varChanged = computed(() => changedKeys.value.has(VAR_NAME))

function emptySequenceSnapshot(hint: SequenceViewHint): TraceVarSnapshot {
  return { type: 'sequence', view_hint: hint, value: [] }
}

function emptyAssociativeSnapshot(hint: AssociativeViewHint): TraceVarSnapshot {
  return { type: 'associative', view_hint: hint, value: [] as unknown as TraceVarValue }
}

function asSequenceValue(items: string[]): TraceVarValue {
  return items as unknown as TraceVarValue
}

function asAssociativeValue(entries: AssociativeEntry[]): TraceVarValue {
  return entries as unknown as TraceVarValue
}

function cloneSnapshot(snap: TraceVarSnapshot): TraceVarSnapshot {
  return JSON.parse(JSON.stringify(snap)) as TraceVarSnapshot
}

function commitSnapshot(next: TraceVarSnapshot, pseudo: string) {
  prevSnapshot.value = cloneSnapshot(mockState.value)
  mockState.value = next
  changedKeys.value = new Set([VAR_NAME])
  stepIndex.value += 1
  lastPseudo.value = pseudo
  lastTraceStep.value = {
    line: stepIndex.value,
    vars: { [VAR_NAME]: next },
    changed: [VAR_NAME],
  }
  operationLog.value = [`#${stepIndex.value}  ${pseudo}`, ...operationLog.value].slice(0, 12)
}

function resetChangedPulse() {
  window.setTimeout(() => {
    if (changedKeys.value.has(VAR_NAME)) {
      changedKeys.value = new Set()
    }
  }, 700)
}

function parseScalar(raw: string): string {
  const t = raw.trim()
  if (!t) throw new Error('请输入有效数值')
  return t
}

function runOperation(op: OpDef) {
  const def = activeDef.value
  try {
    if (def.kind === 'sequence') {
      runSequenceOp(op)
    } else {
      runAssociativeOp(op)
    }
    resetChangedPulse()
  } catch (e) {
    const msg = e instanceof Error ? e.message : '操作失败'
    ElMessage.warning(msg)
  }
}

function runSequenceOp(op: OpDef) {
  const hint = defSequenceHint()
  const curr = [...sequenceItems(mockState.value)]

  if (op.id === 'push' || op.id === 'enqueue' || op.id === 'push_back') {
    const v = parseScalar(inputValue.value)
    const next = [...curr, v]
    commitSnapshot(
      { type: 'sequence', view_hint: hint, value: asSequenceValue(next) },
      `${pseudoPrefix()}.${opLabel(op)}(${formatCppLiteral(v)});`,
    )
    inputValue.value = ''
    return
  }

  if (op.id === 'pop' || op.id === 'dequeue' || op.id === 'pop_back') {
    if (!curr.length) throw new Error('容器为空，无法弹出')
    if (op.id === 'dequeue') {
      const removed = curr[0]
      const next = curr.slice(1)
      commitSnapshot(
        { type: 'sequence', view_hint: hint, value: asSequenceValue(next) },
        `auto val = ${pseudoPrefix()}.front();  // 拿到队头值 ${formatCppLiteral(removed)}\n${pseudoPrefix()}.pop();`,
      )
    } else if (op.id === 'pop') {
      const removed = curr[curr.length - 1]
      const next = curr.slice(0, -1)
      commitSnapshot(
        { type: 'sequence', view_hint: hint, value: asSequenceValue(next) },
        `auto val = ${pseudoPrefix()}.top();  // 拿到栈顶值 ${formatCppLiteral(removed)}\n${pseudoPrefix()}.pop();`,
      )
    } else {
      const removed = curr[curr.length - 1]
      const next = curr.slice(0, -1)
      commitSnapshot(
        { type: 'sequence', view_hint: hint, value: asSequenceValue(next) },
        `${pseudoPrefix()}.pop_back();  // ${formatCppLiteral(removed)}`,
      )
    }
    return
  }

  if (op.id === 'clear') {
    commitSnapshot(
      { type: 'sequence', view_hint: hint, value: asSequenceValue([]) },
      `${pseudoPrefix()}.clear();`,
    )
  }
}

function runAssociativeOp(op: OpDef) {
  const hint = associativeViewHint(mockState.value)
  const curr = [...associativeEntries(mockState.value)]
  const key = parseScalar(inputKey.value)

  if (op.id === 'insert') {
    const val = parseScalar(inputValue.value)
    const idx = curr.findIndex((e) => e.key === key)
    const entry: AssociativeEntry = { key, value: val }
    const next =
      idx >= 0
        ? curr.map((e, i) => (i === idx ? entry : e))
        : [...curr, entry]
    commitSnapshot(
      { type: 'associative', view_hint: hint, value: asAssociativeValue(next) },
      `${pseudoPrefix()}[${formatCppLiteral(key)}] = ${formatCppLiteral(val)};`,
    )
    inputValue.value = ''
    return
  }

  if (op.id === 'erase') {
    if (!curr.some((e) => e.key === key)) throw new Error(`未找到键 ${key}`)
    const next = curr.filter((e) => e.key !== key)
    commitSnapshot(
      { type: 'associative', view_hint: hint, value: asAssociativeValue(next) },
      `${pseudoPrefix()}.erase(${formatCppLiteral(key)});`,
    )
    inputValue.value = ''
    return
  }

  if (op.id === 'find') {
    const hit = curr.find((e) => e.key === key)
    if (hit) {
      ElMessage.success(`find → 命中：${hit.key} → ${hit.value ?? '∅'}`)
      lastPseudo.value = `auto r = ${pseudoPrefix()}.find(${formatCppLiteral(key)});  // 命中`
    } else {
      ElMessage.info(`find → 未找到键 ${key}`)
      lastPseudo.value = `auto r = ${pseudoPrefix()}.find(${formatCppLiteral(key)});  // end()`
    }
  }
}

function defSequenceHint(): SequenceViewHint {
  const id = activeContainer.value
  if (id === 'stack') return 'stack'
  if (id === 'queue') return 'queue'
  return 'vector'
}

function pseudoPrefix(): string {
  const id = activeContainer.value
  if (id === 'stack') return 'st'
  if (id === 'queue') return 'q'
  if (id === 'vector') return 'nums'
  return 'mp'
}

function opLabel(op: OpDef): string {
  if (activeContainer.value === 'stack' && op.id === 'push') return 'push'
  if (activeContainer.value === 'vector' && op.id === 'push_back') return 'push_back'
  return op.id
}

function formatCppLiteral(v: string): string {
  if (/^-?\d+(\.\d+)?$/.test(v)) return v
  if (v === 'true' || v === 'false') return v
  return `"${v.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`
}

function onContainerChange(id: ContainerId) {
  activeContainer.value = id
}

function loadDemo() {
  const def = activeDef.value
  if (def.kind === 'sequence') {
    const hint = def.viewHint as SequenceViewHint
    let demo: string[] = []
    let pseudo = ''
    if (def.id === 'stack') {
      demo = ['(', '[', '{']
      pseudo = 'st.push("("); st.push("["); st.push("{");'
    } else if (def.id === 'queue') {
      demo = ['A', 'B', 'C']
      pseudo = 'q.push("A"); q.push("B"); q.push("C");'
    } else {
      demo = ['10', '20', '30']
      pseudo = 'nums = {10, 20, 30};'
    }
    prevSnapshot.value = cloneSnapshot(mockState.value)
    mockState.value = { type: 'sequence', view_hint: hint, value: asSequenceValue(demo) }
    changedKeys.value = new Set([VAR_NAME])
    stepIndex.value += 1
    lastPseudo.value = pseudo
    lastTraceStep.value = { line: stepIndex.value, vars: { [VAR_NAME]: mockState.value }, changed: [VAR_NAME] }
    operationLog.value = [`#${stepIndex.value}  载入演示数据`, ...operationLog.value].slice(0, 12)
    resetChangedPulse()
    return
  }
  const entries: AssociativeEntry[] = [
    { key: 'apple', value: '3' },
    { key: 'banana', value: '7' },
    { key: 'cherry', value: '1' },
  ]
  prevSnapshot.value = cloneSnapshot(mockState.value)
  mockState.value = {
    type: 'associative',
    view_hint: 'unordered_map',
    value: asAssociativeValue(entries),
  }
  changedKeys.value = new Set([VAR_NAME])
  stepIndex.value += 1
  lastPseudo.value = 'mp["apple"]=3; mp["banana"]=7; mp["cherry"]=1;'
  lastTraceStep.value = { line: stepIndex.value, vars: { [VAR_NAME]: mockState.value }, changed: [VAR_NAME] }
  operationLog.value = [`#${stepIndex.value}  载入演示数据`, ...operationLog.value].slice(0, 12)
  resetChangedPulse()
}

function resetAll() {
  const def = activeDef.value
  prevSnapshot.value = null
  changedKeys.value = new Set()
  stepIndex.value = 0
  lastPseudo.value = '// 已重置'
  lastTraceStep.value = null
  operationLog.value = []
  mockState.value =
    def.kind === 'sequence'
      ? emptySequenceSnapshot(def.viewHint as SequenceViewHint)
      : emptyAssociativeSnapshot(def.viewHint as AssociativeViewHint)
}

watch(activeContainer, (id) => {
  const def = CONTAINERS.find((c) => c.id === id)!
  prevSnapshot.value = null
  changedKeys.value = new Set()
  stepIndex.value = 0
  lastPseudo.value = `// 已切换至 ${def.cppName}`
  lastTraceStep.value = null
  operationLog.value = []
  mockState.value =
    def.kind === 'sequence'
      ? emptySequenceSnapshot(def.viewHint as SequenceViewHint)
      : emptyAssociativeSnapshot(def.viewHint as AssociativeViewHint)
})
</script>

<template>
  <div class="stl-playground">
    <div class="pg-bg" aria-hidden="true">
      <div class="pg-grid" />
      <div class="pg-glow pg-glow--a" />
      <div class="pg-glow pg-glow--b" />
    </div>

    <header class="pg-hero">
      <div class="pg-hero-text">
        <p class="pg-kicker">Algorithm Playground</p>
        <h1 class="pg-title">交互式 STL 沙盒</h1>
        <p class="pg-subtitle">
          无需写代码，点击即可观察栈、队列、向量与哈希表的状态变化——动画与 OJ 可视化调试同源。
        </p>
      </div>
      <div class="pg-hero-meta">
        <span class="pg-chip">纯前端 Mock</span>
        <span class="pg-chip">trace_viz 协议</span>
        <span class="pg-chip">OJ 沙盒：限时 / 限内存 / 禁危险调用</span>
        <span class="pg-chip">Step {{ stepIndex }}</span>
      </div>
    </header>

    <div class="pg-layout">
      <aside class="pg-console">
        <section class="pg-panel">
          <h2 class="pg-panel-title">容器类型</h2>
          <el-segmented
            :model-value="activeContainer"
            :options="CONTAINERS.map((c) => ({ label: c.label, value: c.id }))"
            block
            class="pg-segmented"
            @change="onContainerChange"
          />
          <p class="pg-cpp-hint">
            <code>{{ activeDef.cppName }}&lt;…&gt; c;</code>
          </p>
        </section>

        <section class="pg-panel">
          <h2 class="pg-panel-title">操作</h2>
          <div class="pg-op-grid">
            <el-button
              v-for="op in currentOps"
              :key="op.id"
              type="primary"
              plain
              class="pg-op-btn"
              @click="runOperation(op)"
            >
              {{ op.label }}
            </el-button>
          </div>
        </section>

        <section class="pg-panel pg-panel--inputs">
          <h2 class="pg-panel-title">参数</h2>
          <template v-if="isAssociative">
            <label class="pg-field">
              <span>Key</span>
              <el-input v-model="inputKey" placeholder="键，如 apple" clearable />
            </label>
            <label class="pg-field">
              <span>Value</span>
              <el-input v-model="inputValue" placeholder="值，如 42" clearable />
            </label>
          </template>
          <label v-else class="pg-field">
            <span>Value</span>
            <el-input v-model="inputValue" placeholder="数值或字符串" clearable />
          </label>
        </section>

        <section class="pg-panel pg-panel--actions">
          <el-button @click="loadDemo">载入演示</el-button>
          <el-button @click="resetAll">清空重置</el-button>
        </section>

        <section class="pg-panel pg-panel--code">
          <h2 class="pg-panel-title">伪代码</h2>
          <pre class="pg-pseudo">{{ lastPseudo }}</pre>
          <div v-if="lastTraceStep" class="pg-trace-meta">
            <span>traceStep.changed</span>
            <code>{{ JSON.stringify(lastTraceStep.changed) }}</code>
          </div>
        </section>

        <section class="pg-panel pg-panel--sandbox">
          <h2 class="pg-panel-title">沙盒安全限制</h2>
          <ul class="pg-sandbox-list">
            <li>限时执行：样例运行与 Trace 均设置超时上限。</li>
            <li>内存限制：生产部署按题目配置 cgroup / 容器内存。</li>
            <li>危险调用：拦截 system / fork / exec 与危险头文件。</li>
            <li>隔离策略：判题子进程执行，生产部署应使用 Docker 或更强隔离。</li>
          </ul>
        </section>

        <section v-if="operationLog.length" class="pg-panel pg-panel--log">
          <h2 class="pg-panel-title">操作历史</h2>
          <ul class="pg-log-list">
            <li v-for="(line, i) in operationLog" :key="i">{{ line }}</li>
          </ul>
        </section>
      </aside>

      <main class="pg-canvas">
        <div class="pg-canvas-head">
          <h2>可视化画布</h2>
          <span class="pg-var-tag">{{ VAR_NAME }}</span>
        </div>

        <div class="pg-viz-stage">
          <TraceSequenceViz
            v-if="!isAssociative"
            :name="VAR_NAME"
            :view-hint="sequenceHint"
            :items="sequenceItemsCurr"
            :prev-items="sequenceItemsPrev"
            :var-changed="varChanged"
          />

          <TraceAssociativeViz
            v-else
            :name="VAR_NAME"
            :view-hint="assocHint"
            :entries="assocEntriesCurr"
            :prev-entries="assocEntriesPrev"
            :var-changed="varChanged"
          />
        </div>

        <details class="pg-protocol">
          <summary>当前 mockState（trace_viz 协议）</summary>
          <pre>{{ JSON.stringify(mockState, null, 2) }}</pre>
        </details>
      </main>
    </div>
  </div>
</template>

<style scoped>
.stl-playground {
  position: relative;
  min-height: calc(100vh - 64px);
  padding: 28px 24px 48px;
  overflow: hidden;
}

.pg-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.pg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(color-mix(in srgb, var(--alp-color-primary) 8%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--alp-color-primary) 8%, transparent) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 30%, black 20%, transparent 75%);
}

.pg-glow {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
}

.pg-glow--a {
  top: -80px;
  right: 10%;
  background: #22d3ee;
}

.pg-glow--b {
  bottom: -120px;
  left: 5%;
  background: #a78bfa;
}

.pg-hero,
.pg-layout {
  position: relative;
  z-index: 1;
}

.pg-hero {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 28px;
}

.pg-kicker {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--alp-color-primary);
  font-weight: 700;
}

.pg-title {
  margin: 0 0 10px;
  font-size: clamp(1.6rem, 3vw, 2.2rem);
  font-weight: 800;
  background: linear-gradient(120deg, #e8eef7 30%, #22d3ee 70%, #a78bfa);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.pg-subtitle {
  margin: 0;
  max-width: 52ch;
  font-size: 14px;
  line-height: 1.65;
  color: var(--alp-color-muted);
}

.pg-hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pg-chip {
  font-size: 11px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 35%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-primary) 10%, var(--alp-bg-surface));
  color: var(--alp-color-text);
  font-family: ui-monospace, Consolas, monospace;
}

.pg-layout {
  display: grid;
  grid-template-columns: minmax(280px, 360px) 1fr;
  gap: 22px;
  align-items: start;
}

.pg-console {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.pg-panel {
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 22%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-bg-surface) 88%, transparent);
  backdrop-filter: blur(12px);
  box-shadow: var(--alp-shadow-card);
}

.pg-panel-title {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.pg-segmented {
  width: 100%;
}

.pg-segmented :deep(.el-segmented) {
  width: 100%;
}

.pg-cpp-hint {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.pg-cpp-hint code {
  font-family: ui-monospace, Consolas, monospace;
  color: var(--alp-color-primary);
}

.pg-op-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.pg-op-btn {
  margin: 0;
}

.pg-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.pg-field:last-child {
  margin-bottom: 0;
}

.pg-panel--actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.pg-pseudo {
  margin: 0;
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.55;
  font-family: ui-monospace, Consolas, monospace;
  background: var(--alp-bg-code-ish);
  border: 1px solid var(--alp-color-border);
  color: #7dd3fc;
  white-space: pre-wrap;
  word-break: break-word;
}

.pg-trace-meta {
  margin-top: 10px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.pg-trace-meta code {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: #c4b5fd;
}

.pg-log-list {
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 11px;
  font-family: ui-monospace, Consolas, monospace;
  color: var(--alp-color-muted);
  max-height: 140px;
  overflow-y: auto;
}

.pg-log-list li {
  padding: 4px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--alp-color-border) 60%, transparent);
}

.pg-sandbox-list {
  margin: 0;
  padding-left: 18px;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.7;
}

.pg-canvas {
  padding: 20px 22px 24px;
  border-radius: 16px;
  border: 1px solid color-mix(in srgb, var(--alp-color-accent) 30%, var(--alp-color-border));
  background: linear-gradient(
    160deg,
    color-mix(in srgb, var(--alp-bg-surface) 92%, transparent) 0%,
    color-mix(in srgb, var(--alp-color-primary) 6%, var(--alp-bg-soft-block)) 100%
  );
  backdrop-filter: blur(14px);
  box-shadow:
    var(--alp-shadow-card),
    0 0 60px color-mix(in srgb, var(--alp-color-primary) 8%, transparent);
  min-height: 420px;
}

.pg-canvas-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.pg-canvas-head h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.pg-var-tag {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--alp-color-accent) 18%, var(--alp-bg-surface));
  font-family: ui-monospace, Consolas, monospace;
  color: var(--alp-color-accent);
}

.pg-viz-stage {
  min-height: 280px;
  padding: 8px 4px 20px;
}

.pg-protocol {
  margin-top: 8px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.pg-protocol summary {
  cursor: pointer;
  user-select: none;
  color: var(--alp-color-primary);
}

.pg-protocol pre {
  margin: 10px 0 0;
  padding: 12px;
  border-radius: 10px;
  font-size: 11px;
  overflow: auto;
  max-height: 200px;
  background: var(--alp-bg-code-ish);
  border: 1px solid var(--alp-color-border);
}

@media (max-width: 960px) {
  .pg-layout {
    grid-template-columns: 1fr;
  }

  .pg-op-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 520px) {
  .stl-playground {
    padding: 18px 14px 32px;
  }

  .pg-op-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
