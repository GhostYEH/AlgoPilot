<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { VueFlow, type Edge, type Node } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

import {
  buildConceptGraphEdges,
  buildConceptGraphNodes,
  topoSortConceptIds,
  type ConceptGraphNode,
} from '@/constants/conceptGraph'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { useConceptMastery } from '@/composables/useConceptMastery'

const props = withDefaults(
  defineProps<{
    moduleKey?: string
    highlightPathIds?: string[]
    height?: string
  }>(),
  {
    height: '420px',
  },
)

const router = useRouter()
const { masteryMap } = useConceptMastery()
const selectedId = ref<string | null>(null)

const graphNodes = computed(() =>
  buildConceptGraphNodes(masteryMap.value, {
    moduleKey: props.moduleKey,
    includeProblems: true,
    limit: props.moduleKey ? 40 : 28,
  }),
)

const graphEdges = computed(() => buildConceptGraphEdges(graphNodes.value))

const layoutNodes = computed<Node[]>(() => {
  const order = topoSortConceptIds(graphNodes.value)
  const depth = new Map<string, number>()
  for (let i = 0; i < order.length; i++) {
    depth.set(order[i], i)
  }
  const byDepth = new Map<number, ConceptGraphNode[]>()
  for (const n of graphNodes.value) {
    const d = depth.get(n.id) ?? 0
    if (!byDepth.has(d)) byDepth.set(d, [])
    byDepth.get(d)!.push(n)
  }
  const nodes: Node[] = []
  const colW = 200
  const rowH = 88
  for (const [d, row] of [...byDepth.entries()].sort((a, b) => a[0] - b[0])) {
    row.forEach((n, col) => {
      const highlighted = props.highlightPathIds?.includes(n.id)
      nodes.push({
        id: n.id,
        position: { x: col * colW, y: d * rowH },
        label: n.label,
        data: { ...n, highlighted },
        style: {
          border: `2px solid ${highlighted ? '#fbbf24' : n.accent}`,
          borderRadius: '10px',
          padding: '8px 12px',
          fontSize: '12px',
          background: n.kind === 'problem' ? 'var(--alp-bg-soft-block)' : 'var(--alp-bg-surface-solid)',
          color: 'var(--alp-color-text)',
          minWidth: '100px',
          boxShadow: highlighted ? '0 0 12px rgba(251, 191, 36, 0.45)' : undefined,
        },
      })
    })
  }
  return nodes
})

const flowEdges = computed<Edge[]>(() =>
  graphEdges.value.map((e, i) => ({
    id: `e-${i}-${e.source}-${e.target}`,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: props.highlightPathIds?.includes(e.target),
    style: { stroke: 'var(--alp-color-muted)' },
    labelStyle: { fill: 'var(--alp-color-muted)', fontSize: 10 },
  })),
)

const selectedNode = computed(() => graphNodes.value.find((n) => n.id === selectedId.value))

const moduleLabel = computed(() => {
  if (!selectedNode.value) return ''
  return ALGORITHM_MODULES.find((m) => m.key === selectedNode.value?.moduleKey)?.label ?? ''
})

function onNodeClick({ node }: { node: Node }) {
  selectedId.value = node.id
  const data = node.data as ConceptGraphNode
  const routeName = MODULE_ROUTE_NAMES[data.moduleKey as keyof typeof MODULE_ROUTE_NAMES]
  if (routeName && data.kind === 'concept') {
    void router.push({ name: routeName })
  } else if (data.kind === 'problem' && data.slug) {
    void router.push({ name: 'practice', query: { problem: data.slug } })
  }
}

</script>

<template>
  <div class="concept-flow-wrap" :style="{ height: props.height }">
    <VueFlow
      :nodes="layoutNodes"
      :edges="flowEdges"
      :min-zoom="0.25"
      :max-zoom="2"
      fit-view-on-init
      @node-click="onNodeClick"
    >
      <Background pattern-color="var(--alp-color-border)" :gap="18" />
      <Controls position="bottom-right" />
    </VueFlow>
    <div v-if="selectedNode" class="concept-flow-hint">
      <strong>{{ selectedNode.label }}</strong>
      <span v-if="moduleLabel"> · {{ moduleLabel }}</span>
      <span class="hint-muted"> — 点击概念节点可跳转模块</span>
    </div>
  </div>
</template>

<style scoped>
.concept-flow-wrap {
  position: relative;
  width: 100%;
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-main-panel);
  overflow: hidden;
}

.concept-flow-hint {
  position: absolute;
  left: 12px;
  bottom: 12px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  background: var(--alp-bg-surface-solid);
  border: 1px solid var(--alp-color-border);
  color: var(--alp-color-text);
  pointer-events: none;
  max-width: 90%;
}

.hint-muted {
  color: var(--alp-color-muted);
}
</style>
