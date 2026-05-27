<script setup lang="ts">
import { computed, ref, toRef, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DArrowLeft,
  DArrowRight,
  ChatLineRound,
  MagicStick,
  VideoPause,
  VideoPlay,
  RefreshRight,
} from '@element-plus/icons-vue'
import { traceBugDiagnose, type OjLanguage } from '@/api/oj'
import {
  TRACE_PLAYBACK_SPEEDS,
  type TracePlaybackSpeed,
} from '@/composables/useCodeTracePlayback'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import GameArrayBoard from '@/modules/games/shared/GameArrayBoard.vue'
import TraceMatrixGrid from '@/components/oj/trace/TraceMatrixGrid.vue'
import TraceLinkedList from '@/components/oj/trace/TraceLinkedList.vue'
import TraceTreePanel from '@/components/oj/trace/TraceTreePanel.vue'
import { useCodeTracePlayback } from '@/composables/useCodeTracePlayback'
import type { MatrixValue, TraceBugDiagnoseResponse, TraceResponse } from '@/types/codeTrace'
import {
  classifyStepVars,
  diffMatrixCells,
  isTreeGraph,
  matrixFromSnapshot,
  isMatrixOverflow,
  matrixOverflowMessage,
} from '@/utils/traceViz'

type MatrixVarItem =
  | { name: string; overflow: true; message: string }
  | {
      name: string
      overflow: false
      matrix: MatrixValue
      hotCells: string[]
      activeRow: number | null
      activeCol: number | null
    }
import { diffLinkedList, mergeLinkedListScene } from '@/utils/traceLinkedList'
import { parseDpCursor } from '@/utils/traceMatrix'
import { usePrefersReducedMotion } from '@/composables/usePrefersReducedMotion'
import TraceSlidingWindowScene from '@/components/oj/trace/TraceSlidingWindowScene.vue'
import TraceHashLookupScene from '@/components/oj/trace/TraceHashLookupScene.vue'
import TraceDictPanel from '@/components/oj/trace/TraceDictPanel.vue'
import TraceSequenceViz from '@/components/oj/trace/TraceSequenceViz.vue'
import TraceAssociativeViz from '@/components/oj/trace/TraceAssociativeViz.vue'
import { buildSlidingWindowScene } from '@/utils/traceSlidingWindow'
import {
  buildHashLookupScene,
  mergeTraceVarsForViz,
  parseMapEntries,
} from '@/utils/traceHashLookup'
import { buildMonotonicQueueScene } from '@/utils/traceQueue'
import TraceQueueScene from '@/components/oj/trace/TraceQueueScene.vue'
import { buildStackScene } from '@/utils/traceStack'
import TraceStackScene from '@/components/oj/trace/TraceStackScene.vue'
import TraceMemoryLayout from '@/components/oj/trace/TraceMemoryLayout.vue'
import { useTraceHighlightLine } from '@/composables/useTraceHighlight'
import { extractMemorySlots, diffMemorySlotIds, hasMemoryLayout } from '@/utils/traceMemory'
import {
  buildLevelOrderTreeInference,
  traceHasTreeBuildPattern,
} from '@/utils/traceTreeBuild'

const props = defineProps<{
  trace: TraceResponse | null
  userCode: string
  /** 发起 trace 时的源码快照（行号对齐） */
  traceSourceCode?: string
  loading?: boolean
  narrating?: boolean
  /** 分屏右侧：不重复展示代码，仅高亮行提示 */
  splitMode?: boolean
  /** 题目 slug，用于 AI 轨迹诊断 */
  slug?: string
  problemDescription?: string
  language?: OjLanguage
  /** 最近一次判题结果，用于控制诊断按钮展示 */
  judgeVerdict?: string | null
  /** 外部注入的 AI 轨迹诊断（一键诊断流程） */
  bugDiagnosis?: TraceBugDiagnoseResponse | null
}>()

const emit = defineEmits<{ narrate: [] }>()

const traceRef = toRef(props, 'trace')
const {
  playing,
  frame,
  maxFrame,
  current,
  hasTrace,
  playbackSpeed,
  togglePlay,
  next,
  prev,
  reset,
  setPlaybackSpeed,
  stop,
  jumpToFrame,
} = useCodeTracePlayback(traceRef)

const traceDiagnosis = ref<TraceBugDiagnoseResponse | null>(null)
const diagnosingTrace = ref(false)
const bugStepIndex = ref<number | null>(null)

const effectiveDiagnosis = computed(() => props.bugDiagnosis ?? traceDiagnosis.value)

const showTraceDiagnoseBtn = computed(() => {
  if (!props.slug || !hasTrace.value) return false
  return (props.trace?.steps.length ?? 0) > 0
})

const isOnBugFrame = computed(
  () => bugStepIndex.value !== null && frame.value === bugStepIndex.value,
)

const bugHighlightLine = computed(() => {
  if (bugStepIndex.value === null || !props.trace) return 0
  return props.trace.steps[bugStepIndex.value]?.line ?? 0
})

const diagnosisBugLine = computed(() => {
  if (!effectiveDiagnosis.value || !props.trace) return 0
  const idx = effectiveDiagnosis.value.bug_step_index
  return props.trace.steps[idx]?.line ?? 0
})

watch(
  [() => props.bugDiagnosis, () => props.trace?.steps.length ?? 0],
  ([diag, stepLen]) => {
    if (diag && stepLen > 0) focusBugStep(diag.bug_step_index)
  },
  { immediate: true },
)

watch(
  () => props.trace,
  () => {
    if (!props.bugDiagnosis) {
      traceDiagnosis.value = null
      bugStepIndex.value = null
    }
  },
)

async function onTraceBugDiagnose() {
  if (!props.slug || !props.trace?.steps.length) return
  diagnosingTrace.value = true
  traceDiagnosis.value = null
  bugStepIndex.value = null
  try {
    const res = await traceBugDiagnose(props.slug, {
      code: props.traceSourceCode ?? props.userCode,
      language: props.language ?? 'python',
      steps: props.trace.steps,
      problem_description: props.problemDescription,
    })
    const idx = clampBugStepIndex(res.bug_step_index)
    traceDiagnosis.value = { ...res, bug_step_index: idx }
    focusBugStep(idx)
    if (res.source === 'empty') {
      ElMessage.info(res.diagnosis_title)
    } else {
      ElMessage.success(`AI 已定位第 ${idx + 1} 步，已跳转至可疑帧`)
    }
  } catch {
    ElMessage.warning('AI 轨迹诊断失败，请检查 SPARK_API_PASSWORD 与判题服务')
  } finally {
    diagnosingTrace.value = false
  }
}

function clampBugStepIndex(index: number): number {
  const max = props.trace?.steps.length ? props.trace.steps.length - 1 : 0
  return Math.max(0, Math.min(index, max))
}

function focusBugStep(index: number) {
  const idx = clampBugStepIndex(index)
  bugStepIndex.value = idx
  jumpToFrame(idx)
  stop()
}

function onDiagnosisCardClick() {
  if (!effectiveDiagnosis.value) return
  focusBugStep(effectiveDiagnosis.value.bug_step_index)
}
const { prefersReducedMotion } = usePrefersReducedMotion()
const traceHighlightLine = useTraceHighlightLine()

const codeLines = computed(() => (props.traceSourceCode ?? props.userCode).split('\n'))
const highlightLine = computed(() => current.value?.line ?? 0)

const activeCodeLine = computed(() =>
  isOnBugFrame.value && bugHighlightLine.value > 0 ? bugHighlightLine.value : highlightLine.value,
)

watch(
  activeCodeLine,
  (line) => {
    traceHighlightLine.value = line
  },
  { immediate: true },
)
const changedSet = computed(() => new Set(current.value?.changed ?? []))

const prevStep = computed(() => {
  const i = frame.value
  if (!props.trace || i <= 0) return null
  return props.trace.steps[i - 1] ?? null
})

const mergedVars = computed(() => {
  if (!props.trace?.steps.length) return {}
  return mergeTraceVarsForViz(props.trace.steps, frame.value)
})

const currentForViz = computed(() => {
  if (!current.value) return null
  return { ...current.value, vars: mergedVars.value }
})

const classified = computed(() => classifyStepVars(currentForViz.value))
const prevClassified = computed(() => classifyStepVars(prevStep.value))

const memorySlots = computed(() => extractMemorySlots(currentForViz.value))
const prevMemorySlots = computed(() => extractMemorySlots(prevStep.value))
const hotMemoryIds = computed(() =>
  prevStep.value
    ? [...diffMemorySlotIds(prevMemorySlots.value, memorySlots.value)]
    : [],
)
const showMemoryLayout = computed(
  () =>
    (props.language === 'cpp' || hasMemoryLayout(currentForViz.value)) &&
    memorySlots.value.length > 0,
)
const memoryLayoutChanged = computed(() =>
  memorySlots.value.some((s) => hotMemoryIds.value.includes(s.id)),
)

const stackScene = computed(() =>
  props.trace
    ? buildStackScene(current.value, mergedVars.value, props.trace.steps)
    : null,
)

const queueScene = computed(() =>
  props.trace && !stackScene.value
    ? buildMonotonicQueueScene(current.value, mergedVars.value, props.trace.steps)
    : null,
)

const slidingWindowScene = computed(() =>
  stackScene.value || queueScene.value
    ? null
    : buildSlidingWindowScene(current.value, mergedVars.value),
)

const hashLookupScene = computed(() =>
  props.trace && !stackScene.value && !queueScene.value && !slidingWindowScene.value
    ? buildHashLookupScene(current.value, mergedVars.value, props.trace.steps, frame.value)
    : null,
)

const narrationText = computed(() => {
  const lines = props.trace?.narrations
  if (!lines?.length) return ''
  const hit = lines.find((n) => n.step_index === frame.value)
  return hit?.text ?? hit?.narration ?? ''
})

const isCriticalNarration = computed(() => {
  const lines = props.trace?.narrations
  if (!lines?.length) return false
  const hit = lines.find((n) => n.step_index === frame.value)
  return Boolean(hit?.critical)
})

const listVars = computed(() => {
  const out: {
    name: string
    values: (number | string)[]
    pointers: Record<string, number | undefined>
  }[] = []
  for (const { name, snap } of classified.value.lists) {
    if (!Array.isArray(snap.value)) continue
    const values = (snap.value as number[]).map((x) => String(x))
    const pointers: Record<string, number | undefined> = {}
    for (const { name: pn, snap: ps } of classified.value.scalars) {
      if (ps.type === 'int' && typeof ps.value === 'number' && ps.value >= 0 && ps.value < values.length) {
        pointers[pn] = ps.value
      }
    }
    out.push({ name, values, pointers })
  }
  return out
})

const dpCursor = computed(() => parseDpCursor(current.value))

const matrixVars = computed((): MatrixVarItem[] => {
  const cursor = dpCursor.value
  const out: MatrixVarItem[] = []
  for (const { name, snap } of classified.value.matrices) {
    if (isMatrixOverflow(snap)) {
      out.push({ name, overflow: true, message: matrixOverflowMessage(snap) })
      continue
    }
    const matrix = matrixFromSnapshot(snap)
    if (!matrix) continue
    const prevSnap = prevClassified.value.matrices.find((m) => m.name === name)?.snap
    const prevMatrix =
      prevSnap && !isMatrixOverflow(prevSnap) ? matrixFromSnapshot(prevSnap) : null
    out.push({
      name,
      overflow: false,
      matrix,
      hotCells: diffMatrixCells(prevMatrix, matrix),
      activeRow: cursor?.row ?? null,
      activeCol: cursor?.col ?? null,
    })
  }
  return out
})

const listScene = computed(() => mergeLinkedListScene(current.value))
const prevListScene = computed(() => mergeLinkedListScene(prevStep.value))

const listDiff = computed(() =>
  diffLinkedList(prevListScene.value, listScene.value, [...changedSet.value]),
)

const listSceneChanged = computed(() =>
  [...changedSet.value].some(
    (k) =>
      listScene.value?.pointerRefs.some((p) => p.name === k) ||
      k === 'head' ||
      classified.value.linkedLists.some((l) => l.name === k),
  ),
)

const treePointerHotIds = computed(() => {
  const hot = new Set<string>()
  for (const { name, snap } of classified.value.treeNodeRefs) {
    const ref = snap.value as { node?: string | null }
    if (ref?.node) hot.add(ref.node)
    if (changedSet.value.has(name) && ref?.node) hot.add(ref.node)
  }
  return hot
})

const levelOrderInference = computed(() => {
  if (classified.value.trees.length > 0) return null
  if (!props.trace?.steps.length || !traceHasTreeBuildPattern(props.trace.steps)) return null
  return buildLevelOrderTreeInference(mergedVars.value)
})

const usingTreeInference = computed(() => levelOrderInference.value != null)

const inferredQueueItems = computed(() => levelOrderInference.value?.queueLabels ?? [])

const treeVars = computed(() => {
  const trees = classified.value.trees
  const primary =
    trees.find((t) => t.name === 'root') ??
    trees.find((t) => ['tree', 't1'].includes(t.name)) ??
    trees[0]
  if (primary && isTreeGraph(primary.snap.value)) {
    const hot = new Set<string>(treePointerHotIds.value)
    if (changedSet.value.has(primary.name)) {
      Object.keys(primary.snap.value.nodes).forEach((id) => hot.add(id))
    }
    return [{ name: primary.name, graph: primary.snap.value, hotNodeIds: hot }]
  }
  const inf = levelOrderInference.value
  if (!inf) return []
  return [{ name: 'root', graph: inf.graph, hotNodeIds: inf.hotNodeIds }]
})

const mapVars = computed(() => {
  if (stackScene.value || queueScene.value || hashLookupScene.value || slidingWindowScene.value) return []
  return classified.value.maps.map(({ name, snap }) => ({
    name,
    entries: parseMapEntries(snap),
  }))
})

/** 已由专用场景接管的变量名，避免重复渲染 */
const specializedVarNames = computed(() => {
  const names = new Set<string>()
  if (stackScene.value) names.add(stackScene.value.name)
  if (queueScene.value) names.add(queueScene.value.queueName)
  if (hashLookupScene.value) names.add(hashLookupScene.value.mapName)
  if (usingTreeInference.value) names.add('q')
  return names
})

const genericSequences = computed(() =>
  classified.value.sequences.filter((s) => !specializedVarNames.value.has(s.name)),
)

const prevSequences = computed(() => classifyStepVars(prevStep.value).sequences)

const genericAssociatives = computed(() =>
  classified.value.associatives.filter((a) => !specializedVarNames.value.has(a.name)),
)

const prevAssociatives = computed(() => classifyStepVars(prevStep.value).associatives)

const hasViz = computed(
  () =>
    showMemoryLayout.value ||
    stackScene.value != null ||
    queueScene.value != null ||
    slidingWindowScene.value != null ||
    hashLookupScene.value != null ||
    genericSequences.value.length > 0 ||
    genericAssociatives.value.length > 0 ||
    listVars.value.length > 0 ||
    matrixVars.value.length > 0 ||
    listScene.value != null ||
    treeVars.value.length > 0 ||
    (usingTreeInference.value && inferredQueueItems.value.length > 0) ||
    mapVars.value.length > 0 ||
    visibleScalars.value.length > 0,
)

function isGarbageScalar(snap: import('@/types/codeTrace').TraceVarSnapshot): boolean {
  if (snap.type !== 'str' || typeof snap.value !== 'string') return false
  const v = snap.value
  return /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(v) || (/\\0\d{2,3}/.test(v) && v.length > 8)
}

function isRawPointerScalar(snap: import('@/types/codeTrace').TraceVarSnapshot): boolean {
  if (snap.type !== 'other' || typeof snap.value !== 'string') return false
  return /^0x[0-9a-f]+/i.test(snap.value.trim())
}

function isNoisyChangedVar(name: string, snap: import('@/types/codeTrace').TraceVarSnapshot | undefined): boolean {
  if (!snap) return false
  if ((name === 'root' || name === 'curr') && isRawPointerScalar(snap)) return true
  if (name === 'q' && snap.type === 'other' && String(snap.value).includes('std::queue')) return true
  return false
}

const stepHint = computed(() => {
  if (narrationText.value) return narrationText.value
  if (!current.value) return ''
  const ch = current.value.changed.filter((k) => !isNoisyChangedVar(k, current.value?.vars[k]))
  if (!ch.length) return `第 ${current.value.line} 行：无变量变化`
  if (usingTreeInference.value) {
    return `第 ${current.value.line} 行：根据 nodes / idx 推断当前树与建树队列（GDB 未展开指针）`
  }
  return `第 ${current.value.line} 行：${ch.join('、')} 已更新`
})

const visibleScalars = computed(() =>
  classified.value.scalars.filter(({ name, snap }) => {
    if (stackScene.value && (name === 's' || name === 'is_valid' || name === 'c')) return false
    if (snap.type === 'int' && name === 'c' && snap.value === 0) return false
    if (isRawPointerScalar(snap)) return false
    if (usingTreeInference.value && (name === 'root' || name === 'curr' || name === 'q')) return false
    return !isGarbageScalar(snap)
  }),
)

const caption = computed(() => {
  if (!props.trace) return '可视化调试'
  if (props.trace.verdict !== 'OK') return props.trace.message
  const n = props.trace.steps.length
  return `共 ${n} 步${props.trace.result_preview ? ` · 返回 ${props.trace.result_preview}` : ''}`
})

const showNarrateBtn = computed(
  () =>
    props.trace?.verdict === 'OK' &&
    hasTrace.value &&
    !(props.trace.narrations?.length),
)

</script>

<template>
  <div v-loading="loading" class="code-trace-panel">
    <el-alert
      v-if="trace && trace.verdict !== 'OK'"
      :type="hasTrace ? 'warning' : 'error'"
      :title="trace.message"
      show-icon
      :closable="false"
      class="trace-verdict-alert"
    />

    <SteppedAnimShell
      v-if="hasTrace"
      :caption="caption"
      :use-stepped="true"
      :step-hint="stepHint"
      :step="frame"
      :max-step="maxFrame"
      :playing="playing"
      :hide-toolbar="splitMode"
      :compact-hint="splitMode"
      @toggle-play="togglePlay"
      @next="next"
      @reset="reset"
    >
      <div
        v-if="narrationText"
        class="trace-narration"
        :class="{ 'trace-narration--critical': isCriticalNarration }"
        role="status"
        aria-live="polite"
      >
        <span
          class="trace-narration-badge"
          :class="{ 'trace-narration-badge--critical': isCriticalNarration }"
        >
          {{ isCriticalNarration ? 'AI 诊断' : trace?.narrations?.length && !narrating ? '演示旁白' : '旁白' }}
        </span>
        {{ narrationText }}
      </div>

      <div class="trace-layout" :class="{ 'trace-layout--split': splitMode }">
        <div
          v-if="!splitMode"
          class="trace-code"
          role="region"
          aria-label="当前执行行"
        >
          <div class="trace-code-title">执行位置</div>
          <div
            v-for="(line, i) in codeLines"
            :key="i"
            class="code-line"
            :class="{
              'code-line--active': i + 1 === activeCodeLine && !isOnBugFrame,
              'code-line--bug': i + 1 === activeCodeLine && isOnBugFrame,
            }"
          >
            <span class="ln">{{ i + 1 }}</span>
            <code class="txt">{{ line || ' ' }}</code>
          </div>
        </div>

        <template v-else>
          <header
            v-if="highlightLine > 0"
            class="trace-split-header"
            :class="{ 'trace-split-header--bug': isOnBugFrame }"
            role="status"
            aria-live="polite"
          >
            <div class="trace-split-header__line">
              <span class="trace-line-bar__label">第 {{ highlightLine }} 行</span>
              <code v-if="codeLines[highlightLine - 1]" class="trace-split-header__code">{{
                codeLines[highlightLine - 1].trim() || ' '
              }}</code>
            </div>
            <p v-if="stepHint" class="trace-split-header__hint">{{ stepHint }}</p>
          </header>

          <div
            class="trace-split-body"
            :class="{ 'trace-split-body--solo': !showMemoryLayout }"
          >
            <aside v-if="showMemoryLayout" class="trace-split-memory">
              <TraceMemoryLayout
                compact
                :slots="memorySlots"
                :hot-ids="hotMemoryIds"
                :var-changed="memoryLayoutChanged"
              />
            </aside>

            <div class="trace-split-viz">
              <TraceStackScene
                v-if="stackScene"
                :scene="stackScene"
                :changed="changedSet"
              />
              <TraceQueueScene
                v-else-if="queueScene"
                :scene="queueScene"
                :changed="changedSet"
              />
              <TraceSlidingWindowScene
                v-else-if="slidingWindowScene"
                :scene="slidingWindowScene"
                :changed="changedSet"
              />
              <TraceHashLookupScene
                v-else-if="hashLookupScene"
                :scene="hashLookupScene"
                :changed="changedSet"
              />

              <TraceSequenceViz
                v-for="seq in genericSequences"
                :key="'seq-' + seq.name"
                :name="seq.name"
                :view-hint="seq.viewHint"
                :items="seq.items"
                :prev-items="prevSequences.find((p) => p.name === seq.name)?.items"
                :var-changed="changedSet.has(seq.name)"
              />

              <TraceAssociativeViz
                v-for="assoc in genericAssociatives"
                :key="'assoc-' + assoc.name"
                :name="assoc.name"
                :view-hint="assoc.viewHint"
                :entries="assoc.entries"
                :prev-entries="prevAssociatives.find((p) => p.name === assoc.name)?.entries"
                :var-changed="changedSet.has(assoc.name)"
              />

              <template v-for="m in matrixVars" :key="m.name">
                <el-alert
                  v-if="m.overflow"
                  type="warning"
                  :title="m.message"
                  show-icon
                  :closable="false"
                  class="matrix-overflow-alert"
                />
                <TraceMatrixGrid
                  v-else
                  :name="m.name"
                  :matrix="m.matrix"
                  :hot-cells="m.hotCells"
                  :active-row="m.activeRow"
                  :active-col="m.activeCol"
                  :var-changed="changedSet.has(m.name)"
                />
              </template>

              <TraceLinkedList
                v-if="listScene"
                name="链表"
                :graph="listScene.graph"
                :pointer-labels="listScene.pointerLabels"
                :hot-nodes="listDiff.hotNodes"
                :hot-edges="listDiff.hotEdges"
                :hot-pointers="listDiff.hotPointers"
                :var-changed="listSceneChanged"
              />

              <TraceSequenceViz
                v-if="usingTreeInference"
                name="q"
                view-hint="tree_build_queue"
                :items="inferredQueueItems"
                :var-changed="changedSet.has('q') || changedSet.has('idx')"
              />

              <p v-if="usingTreeInference" class="trace-infer-hint">
                根据 <code>nodes</code> 与 <code>idx</code> 推断（层序建树）；若指针未展开则以推断为准。
              </p>

              <TraceTreePanel
                v-for="t in treeVars"
                :key="t.name"
                :name="t.name"
                :graph="t.graph"
                :hot-node-ids="t.hotNodeIds"
                :var-changed="changedSet.has(t.name) || changedSet.has('idx')"
              />

              <TraceDictPanel
                v-for="m in mapVars"
                :key="m.name"
                :name="m.name"
                :entries="m.entries"
                :var-changed="changedSet.has(m.name)"
              />

              <div
                v-for="arr in listVars"
                v-show="!hashLookupScene && !queueScene && !stackScene"
                :key="arr.name"
                class="var-block"
              >
                <div class="var-label" :class="{ 'var-label--hot': changedSet.has(arr.name) }">
                  {{ arr.name }}
                </div>
                <GameArrayBoard :values="arr.values" :pointers="arr.pointers" :clickable="false" />
              </div>

              <div
                v-if="visibleScalars.length && !hashLookupScene && !slidingWindowScene && !queueScene && !stackScene"
                class="scalar-row"
              >
                <div
                  v-for="s in visibleScalars"
                  :key="s.name"
                  class="scalar-chip"
                  :class="{ 'scalar-chip--hot': changedSet.has(s.name) }"
                >
                  <span class="scalar-name">{{ s.name }}</span>
                  <span class="scalar-val">{{ String(s.snap.value ?? 'None') }}</span>
                </div>
              </div>

              <p v-if="!hasViz" class="trace-empty">本步暂无可视化变量</p>
            </div>
          </div>
        </template>

        <div
          v-if="!splitMode"
          class="trace-viz trace-viz--primary"
        >
          <TraceMemoryLayout
            v-if="showMemoryLayout"
            :slots="memorySlots"
            :hot-ids="hotMemoryIds"
            :var-changed="memoryLayoutChanged"
          />

          <TraceStackScene
            v-if="stackScene"
            :scene="stackScene"
            :changed="changedSet"
          />
          <TraceQueueScene
            v-else-if="queueScene"
            :scene="queueScene"
            :changed="changedSet"
          />
          <TraceSlidingWindowScene
            v-else-if="slidingWindowScene"
            :scene="slidingWindowScene"
            :changed="changedSet"
          />
          <TraceHashLookupScene
            v-else-if="hashLookupScene"
            :scene="hashLookupScene"
            :changed="changedSet"
          />

          <TraceSequenceViz
            v-for="seq in genericSequences"
            :key="'seq-' + seq.name"
            :name="seq.name"
            :view-hint="seq.viewHint"
            :items="seq.items"
            :prev-items="prevSequences.find((p) => p.name === seq.name)?.items"
            :var-changed="changedSet.has(seq.name)"
          />

          <TraceAssociativeViz
            v-for="assoc in genericAssociatives"
            :key="'assoc-' + assoc.name"
            :name="assoc.name"
            :view-hint="assoc.viewHint"
            :entries="assoc.entries"
            :prev-entries="prevAssociatives.find((p) => p.name === assoc.name)?.entries"
            :var-changed="changedSet.has(assoc.name)"
          />

          <template v-for="m in matrixVars" :key="m.name">
            <el-alert
              v-if="m.overflow"
              type="warning"
              :title="m.message"
              show-icon
              :closable="false"
              class="matrix-overflow-alert"
            />
            <TraceMatrixGrid
              v-else
              :name="m.name"
              :matrix="m.matrix"
              :hot-cells="m.hotCells"
              :active-row="m.activeRow"
              :active-col="m.activeCol"
              :var-changed="changedSet.has(m.name)"
            />
          </template>

          <TraceLinkedList
            v-if="listScene"
            name="链表"
            :graph="listScene.graph"
            :pointer-labels="listScene.pointerLabels"
            :hot-nodes="listDiff.hotNodes"
            :hot-edges="listDiff.hotEdges"
            :hot-pointers="listDiff.hotPointers"
            :var-changed="listSceneChanged"
          />

          <TraceSequenceViz
            v-if="usingTreeInference"
            name="q"
            view-hint="tree_build_queue"
            :items="inferredQueueItems"
            :var-changed="changedSet.has('q') || changedSet.has('idx')"
          />

          <p v-if="usingTreeInference" class="trace-infer-hint">
            根据 <code>nodes</code> 与 <code>idx</code> 推断（层序建树）；若指针未展开则以推断为准。
          </p>

          <TraceTreePanel
            v-for="t in treeVars"
            :key="t.name"
            :name="t.name"
            :graph="t.graph"
            :hot-node-ids="t.hotNodeIds"
            :var-changed="changedSet.has(t.name) || changedSet.has('idx')"
          />

          <TraceDictPanel
            v-for="m in mapVars"
            :key="m.name"
            :name="m.name"
            :entries="m.entries"
            :var-changed="changedSet.has(m.name)"
          />

          <div
            v-for="arr in listVars"
            v-show="!hashLookupScene && !queueScene && !stackScene"
            :key="arr.name"
            class="var-block"
          >
            <div class="var-label" :class="{ 'var-label--hot': changedSet.has(arr.name) }">
              {{ arr.name }}
            </div>
            <GameArrayBoard :values="arr.values" :pointers="arr.pointers" :clickable="false" />
          </div>

          <div
            v-if="visibleScalars.length && !hashLookupScene && !slidingWindowScene && !queueScene && !stackScene"
            class="scalar-row"
          >
            <div
              v-for="s in visibleScalars"
              :key="s.name"
              class="scalar-chip"
              :class="{ 'scalar-chip--hot': changedSet.has(s.name) }"
            >
              <span class="scalar-name">{{ s.name }}</span>
              <span class="scalar-val">{{ String(s.snap.value ?? 'None') }}</span>
            </div>
          </div>

          <p v-if="!hasViz" class="trace-empty">本步暂无可视化变量</p>
        </div>
      </div>

      <div
        class="trace-playback-bar"
        :class="{ 'trace-playback-bar--split': splitMode }"
        role="group"
        aria-label="回放控制"
      >
        <el-button-group size="small">
          <el-button :icon="playing ? VideoPause : VideoPlay" @click="togglePlay">
            {{ playing ? '暂停' : prefersReducedMotion ? '步进' : '播放' }}
          </el-button>
          <el-button :icon="DArrowLeft" @click="prev">上一步</el-button>
          <el-button :icon="DArrowRight" @click="next">下一步</el-button>
          <el-button :icon="RefreshRight" @click="reset">重置</el-button>
        </el-button-group>

        <div class="trace-speed" aria-label="播放速度">
          <span class="trace-speed-label">速度</span>
          <el-radio-group
            :model-value="playbackSpeed"
            size="small"
            @update:model-value="setPlaybackSpeed($event as TracePlaybackSpeed)"
          >
            <el-radio-button
              v-for="s in TRACE_PLAYBACK_SPEEDS"
              :key="s"
              :value="s"
            >
              {{ s }}×
            </el-radio-button>
          </el-radio-group>
        </div>

        <span class="trace-frame-meta">步 {{ frame + 1 }} / {{ maxFrame + 1 }}</span>

        <el-button
          v-if="showNarrateBtn"
          size="small"
          :icon="ChatLineRound"
          :loading="narrating"
          class="trace-narrate-btn"
          @click="emit('narrate')"
        >
          生成 AI 旁白
        </el-button>

        <el-button
          v-if="showTraceDiagnoseBtn"
          size="small"
          type="danger"
          plain
          :icon="MagicStick"
          :loading="diagnosingTrace"
          class="trace-diagnose-btn"
          @click="onTraceBugDiagnose"
        >
          ✨ AI 破案诊断
        </el-button>
      </div>

      <button
        v-if="effectiveDiagnosis"
        type="button"
        class="trace-ai-diagnosis-card"
        :class="{ 'trace-ai-diagnosis-card--focused': isOnBugFrame }"
        @click="onDiagnosisCardClick"
      >
        <span class="trace-ai-diagnosis-badge">AI 破案</span>
        <strong class="trace-ai-diagnosis-title">{{ effectiveDiagnosis.diagnosis_title }}</strong>
        <p class="trace-ai-diagnosis-body">{{ effectiveDiagnosis.detailed_analysis }}</p>
        <span class="trace-ai-diagnosis-jump">
          点击跳转到第 {{ effectiveDiagnosis.bug_step_index + 1 }} 步 · 代码第
          {{ diagnosisBugLine || '?' }} 行
        </span>
      </button>
    </SteppedAnimShell>

    <el-empty
      v-else
      description="点击「可视化调试」：将运行你当前编辑器中的代码，按真实变量变化生成逐步动画"
    />
  </div>
</template>

<style scoped>
.trace-verdict-alert {
  margin-bottom: 12px;
}

.code-trace-panel {
  margin-top: 0;
  border: none;
  border-radius: 0;
  padding: 14px 0 18px;
  background: transparent;
  width: 100%;
  box-sizing: border-box;
}

.code-trace-panel :deep(.step-anim) {
  width: 100%;
  max-width: none;
  margin: 0;
}

.code-trace-panel :deep(.anim-viz-stage) {
  width: 100%;
  max-width: none;
}

.trace-narration {
  margin-bottom: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color-primary) 12%, var(--alp-bg-surface));
  border-left: 3px solid var(--el-color-primary);
  font-size: 14px;
  line-height: 1.55;
}

.trace-narration-badge {
  display: inline-block;
  margin-right: 8px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  background: var(--el-color-primary);
  color: #fff;
}

.trace-narration--critical {
  background: color-mix(in srgb, var(--el-color-danger) 14%, var(--alp-bg-surface));
  border-left-color: var(--el-color-danger);
  animation: trace-critical-pulse 1.2s ease-in-out 2;
}

.trace-narration-badge--critical {
  background: var(--el-color-danger);
}

@keyframes trace-critical-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 transparent;
  }
  50% {
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-danger) 25%, transparent);
  }
}

.trace-layout {
  display: grid;
  grid-template-columns: minmax(260px, 0.42fr) minmax(0, 1.58fr);
  gap: 20px;
  align-items: stretch;
  min-height: 320px;
}

.trace-layout--split {
  grid-template-columns: 1fr;
  gap: 8px;
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.trace-split-header {
  flex-shrink: 0;
  padding: 6px 10px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color-primary) 10%, var(--alp-bg-soft-block));
  border: 1px solid var(--alp-color-border);
}

.trace-split-header--bug {
  background: color-mix(in srgb, var(--el-color-danger) 12%, var(--alp-bg-soft-block));
  border-color: color-mix(in srgb, var(--el-color-danger) 35%, var(--alp-color-border));
}

.trace-split-header__line {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 10px;
  font-size: 12px;
}

.trace-split-header__code {
  flex: 1 1 100%;
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  color: var(--alp-color-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.trace-split-header__hint {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--alp-color-text);
}

.trace-split-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(168px, 220px) minmax(0, 1fr);
  gap: 10px;
  align-items: stretch;
}

.trace-split-body--solo {
  grid-template-columns: 1fr;
}

.trace-split-memory {
  min-height: 0;
  overflow: hidden;
}

.trace-split-viz {
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 2px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.trace-split-viz :deep(.trace-tree) {
  flex: 1 1 auto;
  min-height: 160px;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
}

.trace-split-viz :deep(.trace-tree-stage) {
  flex: 1;
  min-height: 140px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.trace-playback-bar--split {
  flex-shrink: 0;
  margin-top: 8px;
  position: sticky;
  bottom: 0;
  z-index: 2;
  background: var(--alp-bg-surface-solid);
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.12);
}

@media (max-width: 720px) {
  .trace-split-body {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .trace-split-memory {
    max-height: 130px;
  }
}

.trace-line-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  padding: 4px 10px;
  border-radius: 6px;
  background: #1e1e1e;
  border: 1px solid #333;
  font-size: 12px;
  color: #d4d4d4;
  flex-shrink: 0;
  max-height: 44px;
  overflow: hidden;
}

.trace-line-bar__label {
  font-weight: 600;
  color: var(--alp-color-muted);
}

.trace-line-bar__line {
  color: #38bdf8;
  font-weight: 700;
}

.trace-line-bar__snippet {
  flex: 1 1 100%;
  font-family: ui-monospace, Consolas, monospace;
  white-space: pre;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.9;
}

.trace-viz--primary {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.trace-viz--split {
  min-height: 0;
  max-height: none;
  flex: 1 1 auto;
  overflow: auto;
}

.trace-code-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  padding: 6px 10px 4px;
  border-bottom: 1px solid #333;
}

.trace-code {
  min-height: 280px;
  max-height: min(480px, 52vh);
  overflow: auto;
  border-radius: 8px;
  background: #1e1e1e;
  padding: 8px 0;
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  border: 1px solid #333;
}

.code-line {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 8px;
  padding: 2px 10px;
  color: #d4d4d4;
}

.code-line--active {
  background: rgba(56, 189, 248, 0.18);
  box-shadow: inset 3px 0 0 #38bdf8;
}

.ln {
  color: #6e7681;
  text-align: right;
  user-select: none;
}

.txt {
  white-space: pre;
}

.trace-viz {
  min-height: 200px;
  max-height: min(480px, 52vh);
  overflow: auto;
  padding: 4px 2px;
}

.var-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
}

.var-label--hot {
  color: var(--el-color-primary);
}

.scalar-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.scalar-chip {
  display: flex;
  flex-direction: column;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  min-width: 64px;
}

.scalar-chip--hot {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
}

.scalar-name {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.scalar-val {
  font-size: 15px;
  font-weight: 600;
  font-family: ui-monospace, Consolas, monospace;
}

.trace-infer-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: 0 0 10px;
  line-height: 1.5;
}

.trace-infer-hint code {
  font-size: 11px;
  padding: 1px 4px;
  border-radius: 4px;
  background: var(--alp-bg-soft-block);
}

.trace-empty {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.trace-playback-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.trace-speed {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trace-speed-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.trace-frame-meta {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  font-variant-numeric: tabular-nums;
}

.trace-narrate-btn {
  margin-left: auto;
}

.trace-diagnose-btn {
  margin-left: 4px;
  border-color: color-mix(in srgb, var(--el-color-danger) 55%, transparent) !important;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--el-color-danger) 12%, transparent),
    color-mix(in srgb, #a78bfa 14%, transparent)
  ) !important;
}

.trace-ai-diagnosis-card {
  display: block;
  width: 100%;
  margin-top: 14px;
  padding: 14px 16px;
  text-align: left;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--el-color-danger) 45%, var(--alp-color-border));
  background: linear-gradient(
    145deg,
    color-mix(in srgb, var(--el-color-danger) 10%, var(--alp-bg-surface)),
    color-mix(in srgb, #a78bfa 8%, var(--alp-bg-soft-block))
  );
  box-shadow: 0 8px 28px color-mix(in srgb, var(--el-color-danger) 12%, transparent);
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.trace-ai-diagnosis-card:hover {
  transform: translateY(-1px);
  border-color: var(--el-color-danger);
  box-shadow: 0 10px 32px color-mix(in srgb, var(--el-color-danger) 22%, transparent);
}

.trace-ai-diagnosis-card--focused {
  animation: trace-critical-pulse 1.2s ease-in-out 2;
}

.trace-ai-diagnosis-badge {
  display: inline-block;
  margin-bottom: 8px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(90deg, var(--el-color-danger), #a78bfa);
}

.trace-ai-diagnosis-title {
  display: block;
  margin: 0 0 8px;
  font-size: 15px;
  color: var(--alp-color-text);
}

.trace-ai-diagnosis-body {
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--alp-color-muted);
}

.trace-ai-diagnosis-jump {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-danger);
}

.code-line--bug {
  background: color-mix(in srgb, var(--el-color-danger) 22%, #1e1e1e) !important;
  box-shadow: inset 3px 0 0 var(--el-color-danger);
}

.code-line--bug .ln {
  color: #fca5a5;
  font-weight: 800;
}

.trace-line-bar--bug {
  border-color: var(--el-color-danger) !important;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-danger) 30%, transparent);
}

.trace-line-bar--bug .trace-line-bar__line {
  color: #f87171;
}

.matrix-overflow-alert {
  margin-bottom: 12px;
}

@media (max-width: 720px) {
  .trace-narrate-btn {
    margin-left: 0;
    width: 100%;
  }
}

@media (max-width: 900px) {
  .trace-layout {
    grid-template-columns: 1fr;
    min-height: 0;
  }

  .trace-code {
    max-height: 220px;
    min-height: 160px;
  }

  .trace-viz {
    max-height: 360px;
  }
}
</style>
