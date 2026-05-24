<script setup lang="ts">
import { computed, toRef } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'
import BinaryTreeTraversalCards from './BinaryTreeTraversalCards.vue'
import {
  BST_EDGES,
  BST_NODES,
  DEMO_EDGES,
  DEMO_NODES,
  frameForSection,
  maxStepForSection,
  nodeRole,
  treeKindForSection,
  type TreeNodeDef,
} from '../binaryTreeAnimFrames'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

const SUMMARY_SECTION_IDS = new Set([
  'summary',
  'checkpoint-1',
  'checkpoint-2',
  'checkpoint-3',
  'checkpoint-4',
])

const CHECKPOINT_GROUPS: Record<string, { title: string; tags: string[]; color: string }[]> = {
  'checkpoint-1': [
    { title: 'DFS 遍历', tags: ['前序', '中序', '后序'], color: 'blue' },
    { title: 'BFS', tags: ['层序 102', '翻转 226'], color: 'cyan' },
  ],
  'checkpoint-2': [
    { title: '属性', tags: ['最大深度', '最小深度', '平衡'], color: 'blue' },
    { title: '路径', tags: ['所有路径', '路径和'], color: 'cyan' },
  ],
  'checkpoint-3': [
    { title: '构造', tags: ['106 切分', '654 最大树'], color: 'blue' },
    { title: '合并', tags: ['617 合并'], color: 'cyan' },
  ],
  'checkpoint-4': [
    { title: 'BST', tags: ['700 搜索', '98 验证'], color: 'blue' },
    { title: 'LCA', tags: ['235 BST', '236 普通'], color: 'violet' },
  ],
}

/** 226 翻转：每步完整布局 */
type InvertNode = { id: string; label: string; cx: number; cy: number }
type InvertFrame = {
  nodes: InvertNode[]
  edges: [string, string][]
  focusId: string
  swapArc?: string
  swapIds?: [string, string]
}

const INVERT_FRAMES: InvertFrame[] = [
  {
    focusId: '1',
    nodes: [
      { id: '1', label: '1', cx: 110, cy: 18 },
      { id: '2', label: '2', cx: 70, cy: 58 },
      { id: '3', label: '3', cx: 150, cy: 58 },
      { id: '4', label: '4', cx: 50, cy: 92 },
      { id: '5', label: '5', cx: 90, cy: 92 },
    ],
    edges: [
      ['1', '2'],
      ['1', '3'],
      ['2', '4'],
      ['2', '5'],
    ],
  },
  {
    focusId: '1',
    swapIds: ['2', '3'],
    swapArc: 'M 70 52 Q 110 72 150 52',
    nodes: [
      { id: '1', label: '1', cx: 110, cy: 18 },
      { id: '3', label: '3', cx: 70, cy: 58 },
      { id: '2', label: '2', cx: 150, cy: 58 },
      { id: '4', label: '4', cx: 130, cy: 92 },
      { id: '5', label: '5', cx: 170, cy: 92 },
    ],
    edges: [
      ['1', '3'],
      ['1', '2'],
      ['2', '4'],
      ['2', '5'],
    ],
  },
  {
    focusId: '2',
    swapIds: ['4', '5'],
    swapArc: 'M 130 88 Q 150 72 170 88',
    nodes: [
      { id: '1', label: '1', cx: 110, cy: 18 },
      { id: '3', label: '3', cx: 70, cy: 58 },
      { id: '2', label: '2', cx: 150, cy: 58 },
      { id: '5', label: '5', cx: 130, cy: 92 },
      { id: '4', label: '4', cx: 170, cy: 92 },
    ],
    edges: [
      ['1', '3'],
      ['1', '2'],
      ['2', '5'],
      ['2', '4'],
    ],
  },
  {
    focusId: '1',
    nodes: [
      { id: '1', label: '1', cx: 110, cy: 18 },
      { id: '3', label: '3', cx: 70, cy: 58 },
      { id: '2', label: '2', cx: 150, cy: 58 },
      { id: '5', label: '5', cx: 130, cy: 92 },
      { id: '4', label: '4', cx: 170, cy: 92 },
    ],
    edges: [
      ['1', '3'],
      ['1', '2'],
      ['2', '5'],
      ['2', '4'],
    ],
  },
]

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

const animFrame = computed(() => frameForSection(props.sectionId, step.value))

const treeNodes = computed((): TreeNodeDef[] =>
  treeKindForSection(props.sectionId) === 'bst' ? BST_NODES : DEMO_NODES,
)

const treeEdges = computed((): [string, string][] =>
  treeKindForSection(props.sectionId) === 'bst' ? BST_EDGES : DEMO_EDGES,
)

const invertFrame = computed(() => {
  if (props.sectionId !== 'invert-tree') return null
  const i = Math.min(step.value, INVERT_FRAMES.length - 1)
  return INVERT_FRAMES[i] ?? INVERT_FRAMES[0]
})

function nodePos(frame: InvertFrame, id: string) {
  return frame.nodes.find((n) => n.id === id)!
}

function nodePosTree(nodes: TreeNodeDef[], id: string) {
  return nodes.find((n) => n.id === id)!
}

function circleClass(id: string) {
  const frame = animFrame.value
  if (!frame) return 'bt-node'
  const role = nodeRole(id, frame)
  if (role === 'hot' || role === 'path') return 'bt-node bt-node--hot'
  if (role === 'done') return 'bt-node bt-node--done'
  if (role === 'dim') return 'bt-node bt-node--dim'
  if (role === 'p') return 'bt-node bt-node--p'
  if (role === 'q') return 'bt-node bt-node--q'
  if (role === 'lca') return 'bt-node bt-node--lca'
  return 'bt-node'
}

function nodeClassInvert(id: string) {
  const frame = invertFrame.value
  if (!frame) return 'bt-node'
  if (id === frame.focusId) return 'bt-node bt-node--hot'
  if (frame.swapIds?.includes(id)) return 'bt-node bt-node--swap'
  if (step.value >= 3) return 'bt-node bt-node--done'
  if (step.value >= 2 && ['1', '3'].includes(id)) return 'bt-node bt-node--done'
  return 'bt-node'
}

const showStack = computed(
  () =>
    !!animFrame.value?.stack &&
    (props.sectionId === 'traversal-iterative' || props.sectionId === 'unified-traversal'),
)

const showQueue = computed(
  () =>
    !!animFrame.value?.queue &&
    (props.sectionId === 'level-order' || props.sectionId === 'find-bottom-left'),
)

const showArrays = computed(() => !!animFrame.value?.arrays?.length)

const caption = computed(() => {
  const m: Record<string, string> = {
    theory: '满/完全/BST/平衡树 · DFS 与 BFS 框架',
    'traversal-iterative': '144：栈模拟前序（先压右再压左）',
    'unified-traversal': '94：迭代中序（一路向左再弹栈 visit）',
    'level-order': '102：队列层序 BFS',
    'invert-tree': '226：交换每个结点的左右孩子',
    'symmetric-tree': '101：镜像结点成对比较',
    'max-depth': '104：1 + max(左深, 右深)',
    'min-depth': '111：到最近叶子的路径长度',
    'balanced-tree': '110：|左高−右高| ≤ 1',
    'lowest-common-ancestor': '236：p=4、q=5，LCA=2',
    'bst-lca': '235：BST 上自上而下找分叉点',
    'path-sum': '112：根到叶路径和 = target',
    'count-nodes': '222：左+右+1',
    'all-paths': '257：DFS 收集根到叶路径',
    'sum-left-leaves': '404：仅累加左叶子',
    'find-bottom-left': '513：最深层最左结点 → 4',
    'build-tree-in-post': '106：中序+后序切分建树',
    'maximum-binary-tree': '654：数组最大值作根',
    'merge-trees': '617：对应结点值相加',
    'bst-search': '700：6 在 BST 中 8→4→6',
    'validate-bst': '98：中序严格递增',
    'bst-min-diff': '530：中序相邻最小差',
    'bst-modes': '501：中序统计众数',
    'bst-insert': '701：按 BST 性质插入',
    'bst-delete': '450：替换或接子树',
    'bst-trim': '669：剪枝到 [low,high]',
    'sorted-array-to-bst': '108：有序数组转平衡 BST',
    'bst-to-greater-sum': '538：反序中序累加',
    summary: '遍历 · 属性 · 路径 · 构造 · BST',
    'checkpoint-1': '周末总结：遍历与层序',
    'checkpoint-2': '周末总结：属性与路径',
    'checkpoint-3': '周末总结：构造与合并',
    'checkpoint-4': '周末总结：BST 与 LCA',
  }
  return m[props.sectionId] ?? '二叉树示意'
})

const stepHint = computed(() => animFrame.value?.note ?? '')

const isSummarySection = computed(() => SUMMARY_SECTION_IDS.has(props.sectionId))

const summaryPills = computed(() => {
  const m: Record<string, string[]> = {
    summary: ['前序', '中序', '后序', '层序', '翻转', '对称', '深度', '路径', 'BST', 'LCA'],
  }
  return m[props.sectionId] ?? []
})

const checkpointGroups = computed(() => CHECKPOINT_GROUPS[props.sectionId] ?? [])
</script>

<template>
  <BinaryTreeTraversalCards v-if="sectionId === 'traversal-recursive'" />

  <SteppedAnimShell
    v-else-if="!isSummarySection"
    :caption="caption"
    :use-stepped="useStepped"
    :step-hint="stepHint"
    :step="step"
    :max-step="maxStep"
    :playing="playing"
    @toggle-play="togglePlay"
    @next="manualNext"
    @reset="resetAnim"
  >
    <!-- 226 翻转 -->
    <div
      v-if="sectionId === 'invert-tree' && invertFrame"
      class="learn-viz-panel bt-panel"
    >
      <svg viewBox="0 0 220 110" class="bt-svg" aria-hidden="true">
        <line
          v-for="([a, b], ei) in invertFrame.edges"
          :key="'inv-e' + ei"
          :x1="nodePos(invertFrame, a).cx"
          :y1="nodePos(invertFrame, a).cy + 10"
          :x2="nodePos(invertFrame, b).cx"
          :y2="nodePos(invertFrame, b).cy - 8"
          class="bt-edge"
        />
        <path v-if="invertFrame.swapArc" class="bt-swap-arc" :d="invertFrame.swapArc" fill="none" />
        <g v-for="n in invertFrame.nodes" :key="n.id">
          <circle :cx="n.cx" :cy="n.cy" r="12" :class="nodeClassInvert(n.id)" />
          <text :x="n.cx" :y="n.cy + 4" class="bt-lbl" text-anchor="middle">{{ n.label }}</text>
        </g>
      </svg>
    </div>

    <!-- 通用：树 + 栈/队列/数组辅助 -->
    <div v-else-if="animFrame" class="learn-viz-panel bt-panel">
      <div v-if="showArrays" class="bt-arrays">
        <div v-for="(arr, ai) in animFrame.arrays" :key="ai" class="bt-array-block">
          <span class="bt-array-title">{{ arr.title }}</span>
          <div class="bt-array-cells">
            <span
              v-for="(item, ii) in arr.items"
              :key="ii"
              class="learn-viz-cell bt-array-cell"
              :class="{ 'learn-viz-cell--hot': arr.hotIdx?.includes(ii) }"
            >{{ item }}</span>
          </div>
        </div>
      </div>

      <div class="bt-main-row">
        <svg viewBox="0 0 220 110" class="bt-svg" aria-hidden="true">
          <line
            v-for="([a, b], ei) in treeEdges"
            :key="'e' + ei"
            :x1="nodePosTree(treeNodes, a).cx"
            :y1="nodePosTree(treeNodes, a).cy + 10"
            :x2="nodePosTree(treeNodes, b).cx"
            :y2="nodePosTree(treeNodes, b).cy - 8"
            class="bt-edge"
            :class="{ 'bt-edge--hot': animFrame.hot.length > 0 }"
          />
          <g v-for="n in treeNodes" :key="n.id">
            <circle :cx="n.cx" :cy="n.cy" r="12" :class="circleClass(n.id)" />
            <text :x="n.cx" :y="n.cy + 4" class="bt-lbl" text-anchor="middle">{{ n.label }}</text>
            <text
              v-if="animFrame.labels?.[n.id]"
              :x="n.cx"
              :y="n.cy - 18"
              class="bt-tag"
              text-anchor="middle"
            >{{ animFrame.labels[n.id] }}</text>
          </g>
        </svg>

        <aside v-if="showStack" class="bt-aux bt-aux--stack">
          <span class="bt-aux-title">栈（顶→底）</span>
          <div class="bt-aux-lane">
            <span
              v-for="(c, si) in animFrame.stack"
              :key="si"
              class="learn-viz-cell"
              :class="{ 'learn-viz-cell--hot': si === 0 }"
            >{{ c }}</span>
            <span v-if="!animFrame.stack?.length" class="bt-aux-empty">空</span>
          </div>
        </aside>

        <aside v-if="showQueue" class="bt-aux bt-aux--queue">
          <span class="bt-aux-title">队列（头→尾）</span>
          <div class="bt-aux-lane bt-aux-lane--queue">
            <span
              v-for="(c, qi) in animFrame.queue"
              :key="qi"
              class="learn-viz-cell"
              :class="{
                'learn-viz-cell--hot': qi === 0,
                'learn-viz-cell--link': qi < (animFrame.queue?.length ?? 0) - 1,
              }"
            >{{ c }}</span>
          </div>
        </aside>
      </div>
    </div>
  </SteppedAnimShell>

  <!-- 总结 / checkpoint -->
  <figure v-else class="bt-summary" role="img" :aria-label="caption">
    <figcaption class="bt-summary-caption">{{ caption }}</figcaption>
    <div v-if="checkpointGroups.length" class="bt-checkpoint-grid">
      <article
        v-for="g in checkpointGroups"
        :key="g.title"
        class="bt-checkpoint-card"
        :class="`bt-checkpoint-card--${g.color}`"
      >
        <h4 class="bt-checkpoint-title">{{ g.title }}</h4>
        <div class="bt-checkpoint-tags">
          <span v-for="t in g.tags" :key="t" class="learn-viz-pill">{{ t }}</span>
        </div>
      </article>
    </div>
    <div v-else class="pill-row">
      <span v-for="p in summaryPills" :key="p" class="learn-viz-pill">{{ p }}</span>
    </div>
  </figure>
</template>

<style scoped>
.bt-panel {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: calc(var(--lv-stage-h, 248px) - 8px);
  width: 100%;
}

.bt-main-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  width: 100%;
}

.bt-svg {
  width: 100%;
  max-width: 280px;
  height: auto;
  flex-shrink: 0;
}

.bt-edge {
  stroke: var(--alp-color-border);
  stroke-width: 2;
  transition: stroke 0.35s ease;
}

.bt-edge--hot {
  stroke: color-mix(in srgb, var(--alp-color-primary) 55%, var(--alp-color-border));
}

.bt-swap-arc {
  stroke: #f59e0b;
  stroke-width: 2;
  stroke-dasharray: 5 4;
  animation: bt-dash 1.2s linear infinite;
}

.bt-node {
  fill: var(--alp-bg-surface-solid);
  stroke: var(--alp-color-border);
  stroke-width: 2;
  transition:
    fill 0.35s ease,
    stroke 0.35s ease;
}

.bt-lbl {
  font-size: 11px;
  font-weight: 700;
  fill: var(--alp-color-text);
  pointer-events: none;
}

.bt-tag {
  font-size: 9px;
  font-weight: 700;
  fill: var(--alp-color-primary, #38bdf8);
}

.bt-node--hot {
  fill: color-mix(in srgb, var(--alp-color-primary) 25%, var(--alp-bg-surface-solid));
  stroke: var(--alp-color-primary, #38bdf8);
  stroke-width: 2.5;
}

.bt-node--done {
  fill: color-mix(in srgb, #22c55e 15%, var(--alp-bg-surface-solid));
  stroke: #22c55e;
}

.bt-node--dim {
  opacity: 0.4;
}

.bt-node--swap {
  fill: color-mix(in srgb, #f59e0b 20%, var(--alp-bg-surface-solid));
  stroke: #f59e0b;
}

.bt-node--p {
  fill: color-mix(in srgb, #a855f7 20%, var(--alp-bg-surface-solid));
  stroke: #a855f7;
}

.bt-node--q {
  fill: color-mix(in srgb, #ec4899 20%, var(--alp-bg-surface-solid));
  stroke: #ec4899;
}

.bt-node--lca {
  fill: color-mix(in srgb, #22c55e 28%, var(--alp-bg-surface-solid));
  stroke: #16a34a;
  stroke-width: 3;
}

.bt-aux {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 72px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-code-ish, rgba(15, 23, 42, 0.5));
}

.bt-aux--stack {
  border-color: color-mix(in srgb, var(--alp-color-primary) 35%, var(--alp-color-border));
}

.bt-aux--queue {
  border-color: color-mix(in srgb, #4ade80 35%, var(--alp-color-border));
}

.bt-aux-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--alp-color-muted);
  text-align: center;
}

.bt-aux-lane {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-height: 48px;
}

.bt-aux-lane--queue {
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
}

.bt-aux-empty {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.bt-arrays {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  width: 100%;
}

.bt-array-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.bt-array-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.bt-array-cells {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.bt-array-cell {
  min-width: 32px;
  height: 32px;
  font-size: 13px;
}

.bt-summary {
  margin: 0;
  padding: 14px 16px 12px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.bt-summary-caption {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  text-align: center;
  line-height: 1.45;
}

.pill-row,
.bt-checkpoint-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.bt-checkpoint-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

@media (max-width: 560px) {
  .bt-checkpoint-grid {
    grid-template-columns: 1fr;
  }
}

.bt-checkpoint-card {
  padding: 12px 10px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-code-ish, rgba(15, 23, 42, 0.45));
}

.bt-checkpoint-card--blue {
  border-top: 3px solid var(--alp-color-primary, #38bdf8);
}

.bt-checkpoint-card--cyan {
  border-top: 3px solid #4ade80;
}

.bt-checkpoint-card--violet {
  border-top: 3px solid #c4b5fd;
}

.bt-checkpoint-title {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-text);
  text-align: center;
}

@keyframes bt-dash {
  to {
    stroke-dashoffset: -18;
  }
}

@media (prefers-reduced-motion: reduce) {
  .bt-swap-arc {
    animation: none !important;
  }
}
</style>
