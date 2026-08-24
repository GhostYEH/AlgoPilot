<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import TraceSequenceViz from '@/components/oj/trace/TraceSequenceViz.vue'
import TraceAssociativeViz from '@/components/oj/trace/TraceAssociativeViz.vue'
import type { TraceVarSnapshot, TraceVarValue } from '@/types/codeTrace'
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

type ContainerId =
  | 'array'
  | 'vector'
  | 'deque'
  | 'list'
  | 'forward_list'
  | 'stack'
  | 'queue'
  | 'priority_queue'
  | AssociativeViewHint

interface ContainerDef {
  id: ContainerId
  label: string
  cppName: string
  kind: 'sequence' | 'associative'
  viewHint: SequenceViewHint | AssociativeViewHint
  setLike?: boolean
  multi?: boolean
}

const CONTAINERS: ContainerDef[] = [
  { id: 'array', label: 'Array', cppName: 'std::array', kind: 'sequence', viewHint: 'array' },
  { id: 'vector', label: 'Vector', cppName: 'std::vector', kind: 'sequence', viewHint: 'vector' },
  { id: 'deque', label: 'Deque', cppName: 'std::deque', kind: 'sequence', viewHint: 'deque' },
  { id: 'list', label: 'List', cppName: 'std::list', kind: 'sequence', viewHint: 'list' },
  { id: 'forward_list', label: 'Forward List', cppName: 'std::forward_list', kind: 'sequence', viewHint: 'forward_list' },
  { id: 'stack', label: 'Stack', cppName: 'std::stack', kind: 'sequence', viewHint: 'stack' },
  { id: 'queue', label: 'Queue', cppName: 'std::queue', kind: 'sequence', viewHint: 'queue' },
  { id: 'priority_queue', label: 'Priority Queue', cppName: 'std::priority_queue', kind: 'sequence', viewHint: 'priority_queue' },
  { id: 'map', label: 'Map', cppName: 'std::map', kind: 'associative', viewHint: 'map' },
  { id: 'multimap', label: 'Multimap', cppName: 'std::multimap', kind: 'associative', viewHint: 'multimap', multi: true },
  { id: 'set', label: 'Set', cppName: 'std::set', kind: 'associative', viewHint: 'set', setLike: true },
  { id: 'multiset', label: 'Multiset', cppName: 'std::multiset', kind: 'associative', viewHint: 'multiset', setLike: true, multi: true },
  { id: 'unordered_map', label: 'Unordered Map', cppName: 'std::unordered_map', kind: 'associative', viewHint: 'unordered_map' },
  { id: 'unordered_multimap', label: 'Unordered Multimap', cppName: 'std::unordered_multimap', kind: 'associative', viewHint: 'unordered_multimap', multi: true },
  { id: 'unordered_set', label: 'Unordered Set', cppName: 'std::unordered_set', kind: 'associative', viewHint: 'unordered_set', setLike: true },
  { id: 'unordered_multiset', label: 'Unordered Multiset', cppName: 'std::unordered_multiset', kind: 'associative', viewHint: 'unordered_multiset', setLike: true, multi: true },
]

const CONTAINER_GROUPS = [
  { label: '序列容器', ids: ['array', 'vector', 'deque', 'list', 'forward_list'] as ContainerId[] },
  { label: '容器适配器', ids: ['stack', 'queue', 'priority_queue'] as ContainerId[] },
  { label: '有序关联容器', ids: ['map', 'multimap', 'set', 'multiset'] as ContainerId[] },
  { label: '无序关联容器', ids: ['unordered_map', 'unordered_multimap', 'unordered_set', 'unordered_multiset'] as ContainerId[] },
].map((group) => ({
  ...group,
  options: group.ids.map((id) => CONTAINERS.find((container) => container.id === id)!),
}))

interface OpDef {
  id: string
  label: string
}

const OPS_BY_CONTAINER: Record<ContainerId, OpDef[]> = {
  array: [
    { id: 'set_at', label: 'Set At' },
    { id: 'fill', label: 'Fill' },
    { id: 'reset', label: 'Reset' },
  ],
  vector: [
    { id: 'push_back', label: 'Push Back' },
    { id: 'pop_back', label: 'Pop Back' },
    { id: 'clear', label: 'Clear' },
  ],
  deque: [
    { id: 'push_front', label: 'Push Front' },
    { id: 'push_back', label: 'Push Back' },
    { id: 'pop_front', label: 'Pop Front' },
    { id: 'pop_back', label: 'Pop Back' },
    { id: 'clear', label: 'Clear' },
  ],
  list: [
    { id: 'push_front', label: 'Push Front' },
    { id: 'push_back', label: 'Push Back' },
    { id: 'pop_front', label: 'Pop Front' },
    { id: 'pop_back', label: 'Pop Back' },
    { id: 'clear', label: 'Clear' },
  ],
  forward_list: [
    { id: 'push_front', label: 'Push Front' },
    { id: 'pop_front', label: 'Pop Front' },
    { id: 'clear', label: 'Clear' },
  ],
  stack: [
    { id: 'push', label: 'Push' },
    { id: 'pop', label: 'Pop' },
    { id: 'clear', label: 'Clear' },
  ],
  queue: [
    { id: 'enqueue', label: 'Enqueue' },
    { id: 'dequeue', label: 'Dequeue' },
    { id: 'clear', label: 'Clear' },
  ],
  priority_queue: [
    { id: 'push', label: 'Push' },
    { id: 'pop', label: 'Pop Top' },
    { id: 'clear', label: 'Clear' },
  ],
  map: associativeOps(),
  multimap: associativeOps(),
  set: associativeOps(),
  multiset: associativeOps(),
  unordered_map: associativeOps(),
  unordered_multimap: associativeOps(),
  unordered_set: associativeOps(),
  unordered_multiset: associativeOps(),
}

function associativeOps(): OpDef[] {
  return [
    { id: 'insert', label: 'Insert' },
    { id: 'erase', label: 'Erase' },
    { id: 'find', label: 'Find' },
    { id: 'clear', label: 'Clear' },
  ]
}

const activeContainer = ref<ContainerId>('stack')
const inputValue = ref('42')
const inputKey = ref('foo')
const stepIndex = ref(0)
const lastPseudo = ref('// 选择容器后，可直接载入演示或执行操作')
const operationLog = ref<string[]>([])

const mockState = ref<TraceVarSnapshot>(emptySequenceSnapshot('stack'))
const prevSnapshot = ref<TraceVarSnapshot | null>(null)
const changedKeys = ref<Set<string>>(new Set())

const activeDef = computed(() => CONTAINERS.find((container) => container.id === activeContainer.value)!)
const currentOps = computed(() => OPS_BY_CONTAINER[activeContainer.value])
const isAssociative = computed(() => activeDef.value.kind === 'associative')
const keyLabel = computed(() => activeContainer.value === 'array' ? 'Index' : 'Key')
const showKeyInput = computed(() => isAssociative.value || activeContainer.value === 'array')
const showValueInput = computed(() => !activeDef.value.setLike)

const sequenceItemsCurr = computed(() => !isAssociative.value ? sequenceItems(mockState.value) : [])
const sequenceItemsPrev = computed(() => prevSnapshot.value && !isAssociative.value ? sequenceItems(prevSnapshot.value) : [])
const sequenceHint = computed(() => !isAssociative.value ? sequenceViewHint(mockState.value) : 'vector')
const assocEntriesCurr = computed(() => isAssociative.value ? associativeEntries(mockState.value) : [])
const assocEntriesPrev = computed(() => prevSnapshot.value && isAssociative.value ? associativeEntries(prevSnapshot.value) : [])
const assocHint = computed(() => isAssociative.value ? associativeViewHint(mockState.value) : 'unordered_map')
const varChanged = computed(() => changedKeys.value.has(VAR_NAME))

function emptySequenceSnapshot(hint: SequenceViewHint): TraceVarSnapshot {
  const value = hint === 'array' ? ['0', '0', '0', '0', '0'] : []
  return { type: 'sequence', view_hint: hint, value: value as unknown as TraceVarValue }
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

function cloneSnapshot(snapshot: TraceVarSnapshot): TraceVarSnapshot {
  return JSON.parse(JSON.stringify(snapshot)) as TraceVarSnapshot
}

function commitSnapshot(next: TraceVarSnapshot, pseudo: string) {
  prevSnapshot.value = cloneSnapshot(mockState.value)
  mockState.value = next
  changedKeys.value = new Set([VAR_NAME])
  stepIndex.value += 1
  lastPseudo.value = pseudo
  operationLog.value = [`#${stepIndex.value}  ${pseudo.replace(/\n/g, ' ')}`, ...operationLog.value].slice(0, 8)
}

function resetChangedPulse() {
  window.setTimeout(() => {
    if (changedKeys.value.has(VAR_NAME)) changedKeys.value = new Set()
  }, 700)
}

function parseScalar(raw: string, label = '值'): string {
  const value = raw.trim()
  if (!value) throw new Error(`请输入有效${label}`)
  return value
}

function runPrimaryOperation() {
  const first = currentOps.value[0]
  if (first) runOperation(first)
}

function runOperation(op: OpDef) {
  try {
    if (activeDef.value.kind === 'sequence') runSequenceOp(op)
    else runAssociativeOp(op)
    resetChangedPulse()
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : '操作失败')
  }
}

function runSequenceOp(op: OpDef) {
  const hint = activeDef.value.viewHint as SequenceViewHint
  const curr = [...sequenceItems(mockState.value)]
  const prefix = pseudoPrefix()

  if (op.id === 'set_at') {
    const index = Number.parseInt(parseScalar(inputKey.value, '下标'), 10)
    if (!Number.isInteger(index) || index < 0 || index >= curr.length) {
      throw new Error(`下标范围为 0–${Math.max(0, curr.length - 1)}`)
    }
    const value = parseScalar(inputValue.value)
    const next = [...curr]
    next[index] = value
    commitSnapshot({ type: 'sequence', view_hint: hint, value: asSequenceValue(next) }, `${prefix}[${index}] = ${formatCppLiteral(value)};`)
    return
  }

  if (op.id === 'fill') {
    const value = parseScalar(inputValue.value)
    commitSnapshot({ type: 'sequence', view_hint: hint, value: asSequenceValue(curr.map(() => value)) }, `${prefix}.fill(${formatCppLiteral(value)});`)
    return
  }

  if (op.id === 'reset') {
    commitSnapshot(emptySequenceSnapshot('array'), `${prefix}.fill(0);`)
    return
  }

  if (['push', 'enqueue', 'push_back', 'push_front'].includes(op.id)) {
    const value = parseScalar(inputValue.value)
    let next = op.id === 'push_front' ? [value, ...curr] : [...curr, value]
    if (activeContainer.value === 'priority_queue') next = sortPriorityQueue(next)
    const method = op.id === 'enqueue' ? 'push' : op.id
    commitSnapshot({ type: 'sequence', view_hint: hint, value: asSequenceValue(next) }, `${prefix}.${method}(${formatCppLiteral(value)});`)
    return
  }

  if (['pop', 'dequeue', 'pop_back', 'pop_front'].includes(op.id)) {
    if (!curr.length) throw new Error('容器为空，无法弹出')
    const removesFront = op.id === 'dequeue' || op.id === 'pop_front' || activeContainer.value === 'priority_queue'
    const removed = removesFront ? curr[0]! : curr[curr.length - 1]!
    const next = removesFront ? curr.slice(1) : curr.slice(0, -1)
    const access = activeContainer.value === 'stack' || activeContainer.value === 'priority_queue' ? 'top' : removesFront ? 'front' : 'back'
    const method = op.id === 'dequeue' || activeContainer.value === 'priority_queue' ? 'pop' : op.id
    commitSnapshot(
      { type: 'sequence', view_hint: hint, value: asSequenceValue(next) },
      `auto value = ${prefix}.${access}();  // ${formatCppLiteral(removed)}\n${prefix}.${method}();`,
    )
    return
  }

  if (op.id === 'clear') {
    const pseudo = ['stack', 'queue', 'priority_queue'].includes(activeContainer.value)
      ? `while (!${prefix}.empty()) ${prefix}.pop();`
      : `${prefix}.clear();`
    commitSnapshot({ type: 'sequence', view_hint: hint, value: asSequenceValue([]) }, pseudo)
  }
}

function runAssociativeOp(op: OpDef) {
  const hint = activeDef.value.viewHint as AssociativeViewHint
  const curr = [...associativeEntries(mockState.value)]
  const key = op.id === 'clear' ? '' : parseScalar(inputKey.value, '键')
  const prefix = pseudoPrefix()

  if (op.id === 'insert') {
    const value = activeDef.value.setLike ? null : parseScalar(inputValue.value)
    const entry: AssociativeEntry = { key, value }
    let next: AssociativeEntry[]
    if (activeDef.value.multi) next = [...curr, entry]
    else if (curr.some((item) => item.key === key)) next = curr.map((item) => item.key === key ? entry : item)
    else next = [...curr, entry]
    if (!hint.startsWith('unordered_')) next = sortAssociative(next)
    const pseudo = activeDef.value.setLike
      ? `${prefix}.insert(${formatCppLiteral(key)});`
      : `${prefix}${activeDef.value.multi ? '.insert({' : '['}${formatCppLiteral(key)}${activeDef.value.multi ? ', ' : '] = '}${formatCppLiteral(value ?? '')}${activeDef.value.multi ? '});' : ';'}`
    commitSnapshot({ type: 'associative', view_hint: hint, value: asAssociativeValue(next) }, pseudo)
    return
  }

  if (op.id === 'erase') {
    if (!curr.some((item) => item.key === key)) throw new Error(`未找到键 ${key}`)
    const next = curr.filter((item) => item.key !== key)
    commitSnapshot({ type: 'associative', view_hint: hint, value: asAssociativeValue(next) }, `${prefix}.erase(${formatCppLiteral(key)});`)
    return
  }

  if (op.id === 'find') {
    const hits = curr.filter((item) => item.key === key)
    lastPseudo.value = `auto it = ${prefix}.find(${formatCppLiteral(key)});  // ${hits.length ? `命中 ${hits.length} 项` : 'end()'}`
    ElMessage[hits.length ? 'success' : 'info'](hits.length ? `找到 ${hits.length} 项` : `未找到键 ${key}`)
    return
  }

  if (op.id === 'clear') {
    commitSnapshot({ type: 'associative', view_hint: hint, value: asAssociativeValue([]) }, `${prefix}.clear();`)
  }
}

function sortPriorityQueue(items: string[]): string[] {
  return [...items].sort((a, b) => {
    const an = Number(a)
    const bn = Number(b)
    if (Number.isFinite(an) && Number.isFinite(bn)) return bn - an
    return b.localeCompare(a, 'zh-CN')
  })
}

function sortAssociative(entries: AssociativeEntry[]): AssociativeEntry[] {
  return [...entries].sort((a, b) => a.key.localeCompare(b.key, 'zh-CN', { numeric: true }))
}

function pseudoPrefix(): string {
  const prefixes: Record<ContainerId, string> = {
    array: 'arr', vector: 'nums', deque: 'dq', list: 'lst', forward_list: 'flst',
    stack: 'st', queue: 'q', priority_queue: 'pq', map: 'mp', multimap: 'mmp',
    set: 's', multiset: 'ms', unordered_map: 'ump', unordered_multimap: 'ummp',
    unordered_set: 'us', unordered_multiset: 'ums',
  }
  return prefixes[activeContainer.value]
}

function formatCppLiteral(value: string): string {
  if (/^-?\d+(\.\d+)?$/.test(value) || value === 'true' || value === 'false') return value
  return `"${value.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`
}

function loadDemo() {
  const def = activeDef.value
  prevSnapshot.value = cloneSnapshot(mockState.value)
  if (def.kind === 'sequence') {
    const demos: Record<string, string[]> = {
      array: ['2', '4', '6', '8', '10'], vector: ['10', '20', '30'], deque: ['front', 'mid', 'back'],
      list: ['A', 'B', 'C'], forward_list: ['head', 'next', 'tail'], stack: ['(', '[', '{'],
      queue: ['A', 'B', 'C'], priority_queue: ['9', '5', '3'],
    }
    mockState.value = { type: 'sequence', view_hint: def.viewHint, value: asSequenceValue(demos[def.id] ?? []) }
  } else {
    const entries: AssociativeEntry[] = def.setLike
      ? [{ key: 'apple', value: null }, { key: 'banana', value: null }, ...(def.multi ? [{ key: 'apple', value: null }] : [])]
      : [{ key: 'apple', value: '3' }, { key: 'banana', value: '7' }, ...(def.multi ? [{ key: 'apple', value: '5' }] : [])]
    const demoEntries = String(def.viewHint).startsWith('unordered_') ? entries : sortAssociative(entries)
    mockState.value = { type: 'associative', view_hint: def.viewHint, value: asAssociativeValue(demoEntries) }
  }
  changedKeys.value = new Set([VAR_NAME])
  stepIndex.value += 1
  lastPseudo.value = `// 已载入 ${def.cppName} 演示数据`
  operationLog.value = [`#${stepIndex.value}  载入 ${def.label} 演示`, ...operationLog.value].slice(0, 8)
  resetChangedPulse()
}

function resetAll() {
  resetForContainer(activeDef.value, '// 已清空并重置')
}

function resetForContainer(def: ContainerDef, pseudo: string) {
  prevSnapshot.value = null
  changedKeys.value = new Set()
  stepIndex.value = 0
  lastPseudo.value = pseudo
  operationLog.value = []
  mockState.value = def.kind === 'sequence'
    ? emptySequenceSnapshot(def.viewHint as SequenceViewHint)
    : emptyAssociativeSnapshot(def.viewHint as AssociativeViewHint)
}

watch(activeContainer, (id) => {
  const def = CONTAINERS.find((container) => container.id === id)!
  inputKey.value = id === 'array' ? '0' : 'foo'
  resetForContainer(def, `// 已切换至 ${def.cppName}`)
})
</script>

<template>
  <div class="stl-playground">
    <div class="pg-bg" aria-hidden="true">
      <div class="pg-glow pg-glow--a" />
      <div class="pg-glow pg-glow--b" />
    </div>

    <header class="pg-hero">
      <div class="pg-hero-text">
        <p class="pg-kicker">Algorithm Playground</p>
        <h1 class="pg-title">交互式 STL 沙盒</h1>
        <p class="pg-subtitle">覆盖 C++ 标准序列、适配器、有序与无序关联容器；选择容器后即可直接观察状态变化。</p>
      </div>
      <div class="pg-hero-meta">
        <span class="pg-chip">16 类 STL 容器</span>
        <span class="pg-chip">本地状态模拟</span>
        <span class="pg-chip">Step {{ stepIndex }}</span>
      </div>
    </header>

    <div class="pg-layout">
      <aside class="pg-console">
        <section class="pg-panel pg-panel--controls">
          <div class="pg-control-head">
            <h2 class="pg-panel-title">容器与操作</h2>
            <el-button text type="primary" size="small" @click="loadDemo">载入演示</el-button>
          </div>

          <el-select v-model="activeContainer" class="pg-container-select" aria-label="选择 STL 容器">
            <el-option-group v-for="group in CONTAINER_GROUPS" :key="group.label" :label="group.label">
              <el-option v-for="option in group.options" :key="option.id" :label="option.label" :value="option.id">
                <span>{{ option.label }}</span>
                <small>{{ option.cppName }}</small>
              </el-option>
            </el-option-group>
          </el-select>

          <p class="pg-cpp-hint"><code>{{ activeDef.cppName }}&lt;…&gt; {{ pseudoPrefix() }};</code></p>

          <div class="pg-input-row">
            <label v-if="showKeyInput" class="pg-field">
              <span>{{ keyLabel }}</span>
              <el-input v-model="inputKey" :placeholder="activeContainer === 'array' ? '0–4' : '例如 apple'" clearable @keyup.enter="runPrimaryOperation" />
            </label>
            <label v-if="showValueInput" class="pg-field">
              <span>Value</span>
              <el-input v-model="inputValue" placeholder="例如 42" clearable @keyup.enter="runPrimaryOperation" />
            </label>
          </div>

          <div class="pg-op-grid">
            <el-button v-for="op in currentOps" :key="op.id" type="primary" plain class="pg-op-btn" @click="runOperation(op)">
              {{ op.label }}
            </el-button>
          </div>

          <div class="pg-quick-actions">
            <span>输入后按 Enter 可直接执行首个操作</span>
            <el-button text size="small" @click="resetAll">重置</el-button>
          </div>
        </section>

        <section class="pg-panel pg-panel--code">
          <h2 class="pg-panel-title">本步对应代码</h2>
          <pre class="pg-pseudo">{{ lastPseudo }}</pre>
        </section>

        <details v-if="operationLog.length" class="pg-panel pg-disclosure">
          <summary>操作记录（{{ operationLog.length }}）</summary>
          <ul class="pg-log-list"><li v-for="(line, index) in operationLog" :key="index">{{ line }}</li></ul>
        </details>

        <details class="pg-panel pg-disclosure">
          <summary>此页面如何运行</summary>
          <ul class="pg-sandbox-list">
            <li>此页在浏览器内模拟 STL 容器状态，不会编译或执行 C++ 代码。</li>
            <li>它复用可视化的数据格式与组件；OJ 可视化调试则由后端独立执行用户代码并生成轨迹。</li>
          </ul>
        </details>
      </aside>

      <main class="pg-canvas">
        <div class="pg-canvas-head">
          <div>
            <h2>{{ activeDef.label }}</h2>
            <p>{{ activeDef.cppName }} · {{ assocEntriesCurr.length || sequenceItemsCurr.length }} 项</p>
          </div>
          <span class="pg-var-tag">{{ VAR_NAME }}</span>
        </div>

        <div class="pg-viz-stage">
          <TraceSequenceViz
            v-if="!isAssociative"
            :key="activeContainer"
            :name="VAR_NAME"
            :view-hint="sequenceHint"
            :items="sequenceItemsCurr"
            :prev-items="sequenceItemsPrev"
            :var-changed="varChanged"
          />
          <TraceAssociativeViz
            v-else
            :key="activeContainer"
            :name="VAR_NAME"
            :view-hint="assocHint"
            :entries="assocEntriesCurr"
            :prev-entries="assocEntriesPrev"
            :var-changed="varChanged"
          />
        </div>

      </main>
    </div>
  </div>
</template>

<style scoped>
.stl-playground {
  position: relative;
  min-height: calc(100vh - var(--alp-header-height, 60px));
  padding: clamp(18px, 3vw, 32px) clamp(14px, 3vw, 32px) 44px;
  overflow: hidden;
}

.pg-bg { position: absolute; inset: 0; pointer-events: none; z-index: 0; }
.pg-glow { position: absolute; width: 380px; height: 380px; border-radius: 50%; filter: blur(90px); opacity: 0.22; }
.pg-glow--a { top: -120px; right: 8%; background: #3a8a9e; }
.pg-glow--b { bottom: -160px; left: 2%; background: #7a6e9e; }
.pg-hero, .pg-layout { position: relative; z-index: 1; }

.pg-hero {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 22px;
}

.pg-kicker { margin: 0 0 6px; font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--alp-color-primary); font-weight: 700; }
.pg-title { margin: 0 0 8px; font-size: clamp(1.65rem, 3vw, 2.25rem); font-weight: 800; color: var(--alp-color-text); }
.pg-subtitle { margin: 0; max-width: 62ch; font-size: 14px; line-height: 1.6; color: var(--alp-color-muted); }
.pg-hero-meta { display: flex; flex-wrap: wrap; gap: 8px; }
.pg-chip { font-size: 11px; padding: 6px 11px; border-radius: 999px; border: 1px solid color-mix(in srgb, var(--alp-color-primary) 35%, var(--alp-color-border)); background: color-mix(in srgb, var(--alp-color-primary) 8%, var(--alp-bg-surface)); color: var(--alp-color-text); }

.pg-layout { display: grid; grid-template-columns: minmax(280px, 340px) minmax(0, 1fr); gap: 20px; align-items: start; }
.pg-console { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.pg-panel { padding: 15px 16px; border-radius: 14px; border: 1px solid color-mix(in srgb, var(--alp-color-primary) 22%, var(--alp-color-border)); background: color-mix(in srgb, var(--alp-bg-surface) 94%, transparent); box-shadow: var(--alp-shadow-card); }
.pg-panel-title { margin: 0 0 10px; font-size: 13px; font-weight: 700; color: var(--alp-color-text); }
.pg-control-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.pg-control-head .pg-panel-title { margin-bottom: 0; }
.pg-container-select { width: 100%; margin-top: 10px; }
.pg-container-select :deep(.el-select-dropdown__item) small { float: right; margin-left: 18px; color: var(--alp-color-muted); }
.pg-cpp-hint { margin: 9px 0 12px; font-size: 12px; color: var(--alp-color-muted); }
.pg-cpp-hint code { font-family: ui-monospace, Consolas, monospace; color: var(--alp-color-primary); }
.pg-input-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-bottom: 10px; }
.pg-field { display: flex; flex-direction: column; gap: 5px; min-width: 0; font-size: 11px; color: var(--alp-color-muted); }
.pg-input-row .pg-field:only-child { grid-column: 1 / -1; }
.pg-op-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.pg-op-btn { margin: 0; min-width: 0; }
.pg-quick-actions { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 8px; color: var(--alp-color-muted); font-size: 11px; }
.pg-pseudo { margin: 0; padding: 11px 12px; border-radius: 9px; font-size: 12px; line-height: 1.5; font-family: ui-monospace, Consolas, monospace; background: var(--alp-bg-code-ish); border: 1px solid var(--alp-color-border); color: #6a9eb0; white-space: pre-wrap; word-break: break-word; }
.pg-disclosure { padding-block: 12px; }
.pg-disclosure summary { cursor: pointer; user-select: none; font-size: 12px; font-weight: 600; color: var(--alp-color-primary); }
.pg-log-list { margin: 10px 0 0; padding: 0; list-style: none; font-size: 11px; font-family: ui-monospace, Consolas, monospace; color: var(--alp-color-muted); max-height: 120px; overflow-y: auto; }
.pg-log-list li { padding: 4px 0; border-bottom: 1px solid color-mix(in srgb, var(--alp-color-border) 60%, transparent); }
.pg-sandbox-list { margin: 10px 0 0; padding-left: 18px; color: var(--alp-color-muted); font-size: 12px; line-height: 1.65; }

.pg-canvas { min-width: 0; min-height: clamp(360px, 58vh, 620px); padding: 18px 20px 16px; border-radius: 16px; border: 1px solid color-mix(in srgb, var(--alp-color-accent) 30%, var(--alp-color-border)); background: color-mix(in srgb, var(--alp-bg-surface) 94%, transparent); box-shadow: var(--alp-shadow-card); display: flex; flex-direction: column; }
.pg-canvas-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.pg-canvas-head h2 { margin: 0; font-size: 16px; font-weight: 700; }
.pg-canvas-head p { margin: 3px 0 0; font-size: 11px; color: var(--alp-color-muted); }
.pg-var-tag { flex-shrink: 0; font-size: 11px; padding: 4px 9px; border-radius: 6px; background: color-mix(in srgb, var(--alp-color-accent) 16%, var(--alp-bg-surface)); font-family: ui-monospace, Consolas, monospace; color: var(--alp-color-accent); }
.pg-viz-stage { flex: 1; min-height: 240px; min-width: 0; display: grid; align-items: center; overflow: auto; padding: 4px 0; }
.pg-viz-stage > :deep(*) { min-width: 0; margin-bottom: 0; }

@media (max-width: 960px) {
  .pg-layout { grid-template-columns: 1fr; }
  .pg-console { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(240px, 0.7fr); align-items: start; }
  .pg-panel--controls { grid-row: span 3; }
  .pg-canvas { min-height: 420px; }
}

@media (max-width: 640px) {
  .pg-hero { align-items: flex-start; margin-bottom: 16px; }
  .pg-console { display: flex; }
  .pg-input-row { grid-template-columns: 1fr; }
  .pg-input-row .pg-field:only-child { grid-column: auto; }
  .pg-canvas { min-height: 360px; padding: 14px; }
  .pg-viz-stage { min-height: 210px; }
}
</style>
