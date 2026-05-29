<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TreeGraph } from '@/types/codeTrace'

const props = defineProps<{
  name: string
  graph: TreeGraph
  hotNodeIds?: Set<string>
  varChanged?: boolean
}>()

const LAZY_DEPTH = 4
const NODE_WIDTH = 48
const NODE_HEIGHT = 38
const LEAF_GAP = 74
const LEVEL_GAP = 78
const PAD_X = 42
const PAD_Y = 32

interface DraftNode {
  id: string
  label: string
  hidden?: boolean
  children: DraftNode[]
}

interface RenderNode {
  id: string
  label: string
  x: number
  y: number
  hidden?: boolean
}

interface RenderEdge {
  id: string
  x1: number
  y1: number
  x2: number
  y2: number
}

const expanded = ref(false)

const nodeCount = computed(() => Object.keys(props.graph.nodes).length)
const useLazy = computed(() => nodeCount.value > 14)

function formatNodeLabel(value: unknown): string {
  const raw = String(value)
  if (raw === '<string?>' || raw === '<未初始化>') return '?'
  return raw
}

function buildDraft(id: string | null, depth = 0): DraftNode | null {
  if (!id) return null
  const node = props.graph.nodes[id]
  if (!node) return null

  const hasHiddenChildren = Boolean(node.left || node.right)
  if (useLazy.value && !expanded.value && depth >= LAZY_DEPTH && hasHiddenChildren) {
    return {
      id: node.id,
      label: formatNodeLabel(node.val),
      children: [{ id: `${node.id}-more`, label: '...', hidden: true, children: [] }],
    }
  }

  const children = [buildDraft(node.left, depth + 1), buildDraft(node.right, depth + 1)].filter(
    Boolean,
  ) as DraftNode[]

  return {
    id: node.id,
    label: formatNodeLabel(node.val),
    children,
  }
}

const root = computed(() => buildDraft(props.graph.root))

const layout = computed(() => {
  const draft = root.value
  if (!draft) {
    return {
      nodes: [] as RenderNode[],
      edges: [] as RenderEdge[],
      width: 0,
      height: 0,
    }
  }

  const nodes: RenderNode[] = []
  const edges: RenderEdge[] = []
  const nodeById = new Map<string, RenderNode>()
  let leafCursor = 0
  let maxDepth = 0

  function walk(node: DraftNode, depth: number): number {
    maxDepth = Math.max(maxDepth, depth)
    const childXs = node.children.map((child) => walk(child, depth + 1))
    const x = childXs.length ? (childXs[0]! + childXs[childXs.length - 1]!) / 2 : leafCursor++
    const rendered = {
      id: node.id,
      label: node.label,
      x: PAD_X + x * LEAF_GAP,
      y: PAD_Y + depth * LEVEL_GAP,
      hidden: node.hidden,
    }
    nodes.push(rendered)
    nodeById.set(node.id, rendered)
    return x
  }

  function connect(node: DraftNode) {
    const from = nodeById.get(node.id)
    if (!from) return
    for (const child of node.children) {
      const to = nodeById.get(child.id)
      if (to) {
        edges.push({
          id: `${node.id}-${child.id}`,
          x1: from.x,
          y1: from.y + NODE_HEIGHT / 2,
          x2: to.x,
          y2: to.y - NODE_HEIGHT / 2,
        })
      }
      connect(child)
    }
  }

  walk(draft, 0)
  connect(draft)

  const leafCount = Math.max(1, leafCursor)
  return {
    nodes,
    edges,
    width: Math.max(320, PAD_X * 2 + (leafCount - 1) * LEAF_GAP + NODE_WIDTH),
    height: Math.max(220, PAD_Y * 2 + maxDepth * LEVEL_GAP + NODE_HEIGHT),
  }
})

const viewBox = computed(() => `0 0 ${layout.value.width} ${layout.value.height}`)

function nodeClass(node: RenderNode) {
  return {
    'trace-tree-node--hot': props.hotNodeIds?.has(node.id),
    'trace-tree-node--hidden': node.hidden,
  }
}
</script>

<template>
  <section class="trace-tree" :class="{ 'trace-tree--hot': varChanged }">
    <header class="trace-tree-label">
      <span class="trace-tree-title">{{ name }}</span>
      <span class="tag">树</span>
      <span class="trace-tree-meta">{{ nodeCount }} 节点</span>
      <el-button
        v-if="useLazy"
        link
        type="primary"
        size="small"
        class="expand-btn"
        @click="expanded = !expanded"
      >
        {{ expanded ? '收起深层' : '展开全部' }}
      </el-button>
    </header>

    <div v-if="root" class="trace-tree-stage">
      <svg
        class="trace-tree-canvas"
        :viewBox="viewBox"
        :width="layout.width"
        :height="layout.height"
        role="img"
        :aria-label="`${name} 树结构可视化`"
      >
        <g class="trace-tree-edges">
          <path
            v-for="edge in layout.edges"
            :key="edge.id"
            :d="`M ${edge.x1} ${edge.y1} C ${edge.x1} ${(edge.y1 + edge.y2) / 2}, ${edge.x2} ${(edge.y1 + edge.y2) / 2}, ${edge.x2} ${edge.y2}`"
          />
        </g>

        <g
          v-for="node in layout.nodes"
          :key="node.id"
          class="trace-tree-node"
          :class="nodeClass(node)"
          :transform="`translate(${node.x}, ${node.y})`"
        >
          <rect
            :x="-NODE_WIDTH / 2"
            :y="-NODE_HEIGHT / 2"
            :width="NODE_WIDTH"
            :height="NODE_HEIGHT"
            rx="10"
          />
          <text text-anchor="middle" dominant-baseline="middle">{{ node.label }}</text>
        </g>
      </svg>
    </div>

    <p v-else class="trace-tree-empty">空树</p>
  </section>
</template>

<style scoped>
.trace-tree {
  margin-bottom: 14px;
  min-width: 0;
}

.trace-tree-label {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 8px;
  min-width: 0;
  font-size: 13px;
  font-weight: 600;
}

.trace-tree-title {
  min-width: 0;
  max-width: 18ch;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trace-tree-meta {
  font-size: 11px;
  font-weight: 500;
  color: var(--alp-color-muted);
}

.expand-btn {
  margin-left: auto;
  font-size: 12px;
}

.trace-tree--hot .trace-tree-label {
  color: var(--el-color-primary);
}

.tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.trace-tree-stage {
  overflow: auto;
  padding: 12px;
  border-radius: 8px;
  background:
    linear-gradient(var(--alp-bg-soft-block), var(--alp-bg-soft-block)) padding-box,
    radial-gradient(circle at 20% 0%, rgba(56, 189, 248, 0.22), transparent 34%) border-box;
  border: 1px solid var(--alp-color-border);
  width: 100%;
  max-height: min(520px, 56vh);
  box-sizing: border-box;
}

.trace-tree-canvas {
  display: block;
  min-width: 100%;
}

.trace-tree-edges path {
  fill: none;
  stroke: color-mix(in srgb, var(--alp-color-muted) 54%, transparent);
  stroke-width: 2;
  stroke-linecap: round;
}

.trace-tree-node rect {
  fill: var(--alp-bg-surface-solid);
  stroke: var(--alp-color-border);
  stroke-width: 2;
  filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.12));
  transition:
    fill 0.16s ease,
    stroke 0.16s ease,
    filter 0.16s ease;
}

.trace-tree-node text {
  fill: var(--alp-color-text);
  font-size: 13px;
  font-weight: 700;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  pointer-events: none;
}

.trace-tree-node--hot rect {
  fill: color-mix(in srgb, #fbbf24 22%, var(--alp-bg-surface-solid));
  stroke: #fbbf24;
  filter: drop-shadow(0 0 12px color-mix(in srgb, #fbbf24 45%, transparent));
}

.trace-tree-node--hidden rect {
  fill: color-mix(in srgb, var(--alp-color-muted) 12%, var(--alp-bg-surface-solid));
  stroke-dasharray: 5 4;
}

.trace-tree-node--hidden text {
  fill: var(--alp-color-muted);
  letter-spacing: 1px;
}

.trace-tree-empty {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
}

@media (max-width: 720px) {
  .trace-tree-stage {
    max-height: 360px;
  }

  .expand-btn {
    flex-basis: 100%;
    margin-left: 0;
    justify-content: flex-start;
  }
}
</style>
