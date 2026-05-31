<script setup lang="ts">
import { computed, toRef } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

/** 演示用 6 顶点无向图：0-1-2, 0-3-4, 2-5 */
const NODES = [
  { id: 0, x: 80, y: 100, label: '0' },
  { id: 1, x: 160, y: 60, label: '1' },
  { id: 2, x: 240, y: 100, label: '2' },
  { id: 3, x: 80, y: 180, label: '3' },
  { id: 4, x: 160, y: 220, label: '4' },
  { id: 5, x: 240, y: 180, label: '5' },
]
const EDGES = [
  [0, 1],
  [1, 2],
  [2, 5],
  [0, 3],
  [3, 4],
]

const BFS_STEPS = [
  { visited: [0], queue: [0], active: 0, hint: '起点 0 入队并标记 visited' },
  { visited: [0, 1, 3], queue: [1, 3], active: 0, hint: '出队 0，邻居 1、3 入队（入队即 visited）' },
  { visited: [0, 1, 3], queue: [3], active: 1, hint: '出队 1，扩展邻居 2' },
  { visited: [0, 1, 2, 3], queue: [2, 3], active: 1, hint: '2 入队；队列 [2,3]' },
  { visited: [0, 1, 2, 3, 4, 5], queue: [], active: 2, hint: '依次出队至全图访问完毕' },
]

const DFS_STEPS = [
  { visited: [0], stack: [0], active: 0, hint: '从 0 开始 DFS，标记并访问' },
  { visited: [0, 1], stack: [0, 1], active: 1, hint: '深入邻居 1' },
  { visited: [0, 1, 2], stack: [0, 1, 2], active: 2, hint: '1 → 2 继续深入' },
  { visited: [0, 1, 2, 5], stack: [0, 1, 2, 5], active: 5, hint: '2 → 5 到达叶子' },
  { visited: [0, 1, 2, 3, 4, 5], stack: [3], active: 3, hint: '回溯后从 0 的未访问邻居 3 继续' },
]

function maxStepForSection(id: string) {
  const m: Record<string, number> = {
    theory: 2,
    representation: 2,
    bfs: BFS_STEPS.length - 1,
    dfs: DFS_STEPS.length - 1,
    pitfalls: 3,
    practice: 0,
    summary: 0,
  }
  return m[id] ?? 2
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

const caption = computed(() => {
  const m: Record<string, string> = {
    theory: '图 G=(V,E)：顶点与边',
    representation: '邻接矩阵 · 邻接表',
    bfs: 'BFS：队列按层扩展',
    dfs: 'DFS：递归/栈深入',
    pitfalls: 'visited 时机 · 勿漏连通分量',
    practice: '200 岛屿 · 207 课程表',
    summary: 'BFS 最短路 · DFS 连通/环',
  }
  return m[props.sectionId] ?? '图遍历示意'
})

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'theory') {
    return ['顶点 V、边 E', '有向 / 无向 / 权重', '网格也可建图', ''][i] ?? ''
  }
  if (s === 'representation') {
    return ['邻接矩阵：O(V²) 空间', '邻接表：稀疏图省空间', '竞赛常用 vector/list', ''][i] ?? ''
  }
  if (s === 'bfs') return BFS_STEPS[i]?.hint ?? ''
  if (s === 'dfs') return DFS_STEPS[i]?.hint ?? ''
  if (s === 'pitfalls') {
    return [
      'BFS：入队时 mark visited',
      'DFS：进入结点时 mark',
      '外层 for 扫全图计分量',
      '勿把 DFS 深度当最短路',
    ][i] ?? ''
  }
  return ''
})

const graphState = computed(() => {
  if (props.sectionId === 'bfs') return BFS_STEPS[Math.min(step.value, BFS_STEPS.length - 1)]
  if (props.sectionId === 'dfs') return DFS_STEPS[Math.min(step.value, DFS_STEPS.length - 1)]
  return null
})

const bfsState = computed(() =>
  props.sectionId === 'bfs'
    ? BFS_STEPS[Math.min(step.value, BFS_STEPS.length - 1)]
    : null,
)
const dfsState = computed(() =>
  props.sectionId === 'dfs'
    ? DFS_STEPS[Math.min(step.value, DFS_STEPS.length - 1)]
    : null,
)

function nodeClass(id: number) {
  const st = graphState.value
  if (!st) return id === 0 && step.value >= 0 ? 'hot' : ''
  if (st.active === id) return 'active'
  if (st.visited.includes(id)) return 'visited'
  return ''
}

function edgeOpacity(a: number, b: number) {
  const st = graphState.value
  if (!st) return 0.35
  const va = st.visited.includes(a)
  const vb = st.visited.includes(b)
  return va && vb ? 0.9 : 0.25
}
</script>

<template>
  <figure v-if="sectionId === 'summary' || sectionId === 'practice'" class="graph-summary">
    <figcaption class="graph-cap">{{ caption }}</figcaption>
    <div class="pill-row">
      <span class="pill">BFS</span>
      <span class="pill">DFS</span>
      <span class="pill">200</span>
      <span class="pill">207</span>
      <span class="pill">ch06-graph</span>
    </div>
  </figure>

  <SteppedAnimShell
    v-else
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
    <div v-if="sectionId === 'theory'" class="panel theory">
      <span class="pill" :class="{ hot: step >= 0 }">顶点 V</span>
      <span class="arrow">+</span>
      <span class="pill" :class="{ hot: step >= 0 }">边 E</span>
      <span class="arrow">→</span>
      <span class="pill" :class="{ hot: step >= 1 }">有向/无向</span>
      <span v-if="step >= 2" class="pill hot">权重 w</span>
    </div>

    <div v-else-if="sectionId === 'representation'" class="panel repr">
      <div class="repr-col" :class="{ hot: step >= 0 }">
        <span class="repr-title">邻接矩阵</span>
        <div class="matrix">
          <span v-for="i in 9" :key="i" class="cell" :class="{ on: i === 1 || i === 3 || i === 5 || i === 7 }" />
        </div>
        <span class="repr-note">O(V²)</span>
      </div>
      <div class="repr-col" :class="{ hot: step >= 1 }">
        <span class="repr-title">邻接表</span>
        <ul class="adj-list">
          <li>0 → 1, 3</li>
          <li>1 → 0, 2</li>
          <li>2 → 1, 5</li>
        </ul>
        <span class="repr-note">O(V+E)</span>
      </div>
    </div>

    <div v-else-if="sectionId === 'pitfalls'" class="panel pitfalls">
      <ul class="pitfall-list">
        <li :class="{ hot: step >= 0 }">BFS 入队时 mark visited</li>
        <li :class="{ hot: step >= 1 }">DFS 用栈/递归，勿混队列</li>
        <li :class="{ hot: step >= 2 }">for 全图启动，勿漏分量</li>
        <li :class="{ hot: step >= 3, warn: step >= 3 }">BFS 层数 ≠ 带权最短路</li>
      </ul>
    </div>

    <div v-else class="graph-viz">
      <svg viewBox="0 0 320 280" class="graph-svg" aria-label="图遍历示意">
        <line
          v-for="(e, ei) in EDGES"
          :key="'e' + ei"
          :x1="NODES[e[0]].x"
          :y1="NODES[e[0]].y"
          :x2="NODES[e[1]].x"
          :y2="NODES[e[1]].y"
          class="edge"
          :style="{ opacity: edgeOpacity(e[0], e[1]) }"
        />
        <g v-for="n in NODES" :key="n.id">
          <circle
            :cx="n.x"
            :cy="n.y"
            r="22"
            class="node"
            :class="nodeClass(n.id)"
          />
          <text :x="n.x" :y="n.y + 5" text-anchor="middle" class="node-label">{{ n.label }}</text>
        </g>
      </svg>
      <div v-if="bfsState" class="side-state">
        <span class="state-lbl">queue</span>
        <span v-for="q in bfsState.queue" :key="'q' + q" class="state-chip">{{ q }}</span>
        <span v-if="!bfsState.queue.length" class="state-empty">空</span>
      </div>
      <div v-if="dfsState" class="side-state">
        <span class="state-lbl">stack</span>
        <span v-for="s in dfsState.stack" :key="'s' + s" class="state-chip">{{ s }}</span>
      </div>
    </div>
  </SteppedAnimShell>
</template>

<style scoped>
.graph-cap {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.panel {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-height: 72px;
}

.panel .pill.hot {
  background: color-mix(in srgb, var(--el-color-primary) 12%, var(--alp-bg-surface));
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.arrow {
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}

.repr {
  gap: 16px;
}

.repr-col {
  flex: 1;
  min-width: 120px;
  padding: 10px;
  border-radius: 8px;
  border: 1px dashed var(--alp-color-border);
  opacity: 0.55;
  transition: opacity 0.2s;
}

.repr-col.hot {
  opacity: 1;
  border-color: var(--el-color-primary);
}

.repr-title {
  display: block;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
}

.matrix {
  display: grid;
  grid-template-columns: repeat(3, 20px);
  gap: 3px;
}

.matrix .cell {
  width: 20px;
  height: 20px;
  background: var(--alp-bg-soft-block);
  border-radius: 3px;
}

.matrix .cell.on {
  background: var(--el-color-primary);
}

.adj-list {
  margin: 0;
  padding-left: 1rem;
  font-size: 11px;
  font-family: ui-monospace, Consolas, monospace;
}

.repr-note {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.pitfall-list {
  list-style: none;
  margin: 0;
  padding: 0;
  width: 100%;
}

.pitfall-list li {
  padding: 8px 10px;
  margin-bottom: 6px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  font-size: 13px;
  opacity: 0.45;
  transition: opacity 0.2s;
}

.pitfall-list li.hot {
  opacity: 1;
  border-color: color-mix(in srgb, var(--el-color-warning) 50%, var(--alp-color-border));
  background: color-mix(in srgb, var(--el-color-warning) 8%, var(--alp-bg-surface));
}

.pitfall-list li.warn {
  border-color: var(--el-color-danger);
}

.graph-viz {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
}

.graph-svg {
  width: 100%;
  max-width: 320px;
  height: auto;
}

.edge {
  stroke: var(--el-color-primary);
  stroke-width: 2;
}

.node {
  fill: var(--alp-bg-surface);
  stroke: var(--alp-color-border);
  stroke-width: 2;
  transition: fill 0.2s, stroke 0.2s;
}

.node.visited {
  fill: color-mix(in srgb, var(--el-color-primary) 15%, var(--alp-bg-surface));
  stroke: var(--el-color-primary);
}

.node.active {
  fill: var(--el-color-primary);
  stroke: var(--el-color-primary);
}

.node.active + .node-label,
.node.active ~ .node-label {
  fill: #fff;
}

.node-label {
  font-size: 13px;
  font-weight: 600;
  fill: var(--el-text-color-primary);
  pointer-events: none;
}

.node.active + text,
text:has(+ .node.active) {
  fill: #fff;
}

.side-state {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.state-lbl {
  font-weight: 600;
  color: var(--el-color-primary);
  margin-right: 4px;
}

.state-chip {
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  font-family: ui-monospace, Consolas, monospace;
}

.state-empty {
  color: var(--el-text-color-placeholder);
}
</style>
