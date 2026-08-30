<script setup lang="ts">
import { computed, ref, watch } from 'vue'
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
  type ConceptGraphNode,
} from '@/constants/conceptGraph'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { useConceptMastery } from '@/composables/useConceptMastery'

const props = withDefaults(
  defineProps<{
    moduleKey?: string
    highlightPathIds?: string[]
    height?: string
    navigateOnClick?: boolean
  }>(),
  {
    height: '420px',
    navigateOnClick: true,
  },
)

const emit = defineEmits<{
  select: [node: ConceptGraphNode]
}>()

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
  const nodeById = new Map(graphNodes.value.map((node) => [node.id, node]))
  const depth = new Map<string, number>()
  const resolving = new Set<string>()
  const resolveDepth = (id: string): number => {
    if (depth.has(id)) return depth.get(id) ?? 0
    if (resolving.has(id)) return 0
    resolving.add(id)
    const node = nodeById.get(id)
    const localPrerequisites = (node?.prerequisites ?? []).filter((key) => nodeById.has(key))
    const value = localPrerequisites.length
      ? Math.max(...localPrerequisites.map((key) => resolveDepth(key))) + 1
      : 0
    resolving.delete(id)
    depth.set(id, value)
    return value
  }
  for (const node of graphNodes.value) resolveDepth(node.id)
  const byDepth = new Map<number, ConceptGraphNode[]>()
  for (const n of graphNodes.value) {
    const d = depth.get(n.id) ?? 0
    if (!byDepth.has(d)) byDepth.set(d, [])
    byDepth.get(d)!.push(n)
  }
  const nodes: Node[] = []
  const colW = 210
  const rowH = 96
  for (const [d, row] of [...byDepth.entries()].sort((a, b) => a[0] - b[0])) {
    row.forEach((n, col) => {
      const highlighted = props.highlightPathIds?.includes(n.id)
      nodes.push({
        id: n.id,
        position: { x: d * colW, y: col * rowH },
        label: n.label,
        data: { ...n, highlighted },
        style: {
          border: `2px solid ${highlighted ? 'var(--alp-color-primary)' : n.accent}`,
          borderRadius: '10px',
          padding: '8px 12px',
          fontSize: '12px',
          background: n.kind === 'problem' ? 'var(--alp-bg-soft-block)' : 'var(--alp-bg-surface-solid)',
          color: 'var(--alp-color-text)',
          minWidth: '100px',
          boxShadow: highlighted ? '0 0 0 3px var(--alp-color-primary-glow)' : undefined,
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
    label:
      e.label === 'prerequisite'
        ? '先修'
        : e.label === 'applies'
          ? '应用'
          : e.label === 'uses'
            ? '使用'
            : e.label === 'extends'
              ? '扩展'
              : e.label === 'requires_sort'
                ? '依赖排序'
                : e.label,
    animated: props.highlightPathIds?.includes(e.target),
    style: { stroke: 'var(--alp-color-muted)' },
    labelStyle: { fill: 'var(--alp-color-muted)', fontSize: 10 },
  })),
)

const selectedNode = computed(() => graphNodes.value.find((n) => n.id === selectedId.value))

const conceptCount = computed(() => graphNodes.value.filter((node) => node.kind === 'concept').length)
const problemCount = computed(() => graphNodes.value.filter((node) => node.kind === 'problem').length)

watch(
  () => props.moduleKey,
  () => {
    selectedId.value = null
  },
)

const moduleLabel = computed(() => {
  if (!selectedNode.value) return ''
  return ALGORITHM_MODULES.find((m) => m.key === selectedNode.value?.moduleKey)?.label ?? ''
})

function onNodeClick({ node }: { node: Node }) {
  selectedId.value = node.id
  const data = node.data as ConceptGraphNode
  emit('select', data)
  if (!props.navigateOnClick) return
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
    <div class="graph-summary" aria-label="图谱内容统计">
      <span><b>{{ conceptCount }}</b> 个概念</span>
      <span><b>{{ graphEdges.length }}</b> 条依赖</span>
      <span><b>{{ problemCount }}</b> 道关联题</span>
    </div>
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
      <div class="hint-heading">
        <strong>{{ selectedNode.label }}</strong>
        <span>{{ selectedNode.kind === 'problem' ? '关联题目' : moduleLabel }}</span>
      </div>
      <p>{{ selectedNode.description || (selectedNode.kind === 'problem' ? '用这道题检验概念是否真正掌握。' : '沿依赖关系学习并完成对应练习。') }}</p>
      <div class="hint-meta">
        <span>掌握度 {{ Math.round(selectedNode.mastery) }}%</span>
        <span>{{ props.navigateOnClick ? '再次点击可打开内容' : '已在当前模块中定位' }}</span>
      </div>
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

.graph-summary {
  position: absolute;
  z-index: 5;
  top: 12px;
  left: 12px;
  display: flex;
  gap: 6px;
  padding: 6px;
  border: 1px solid var(--alp-color-border);
  border-radius: 9px;
  background: color-mix(in srgb, var(--alp-bg-surface-solid) 94%, transparent);
  box-shadow: var(--alp-shadow-sm);
  pointer-events: none;
}

.graph-summary span {
  padding: 3px 7px;
  color: var(--alp-color-muted);
  font-size: 10px;
}

.graph-summary b {
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
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
  width: min(340px, calc(100% - 88px));
  box-shadow: var(--alp-shadow-sm);
}

.hint-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.hint-heading > span { color: var(--alp-color-primary); font-size: 10px; font-weight: 650; }
.concept-flow-hint p { margin: 5px 0; color: var(--alp-color-text-secondary); line-height: 1.5; }
.hint-meta { display: flex; justify-content: space-between; gap: 10px; color: var(--alp-color-muted); font-size: 10px; }
</style>
