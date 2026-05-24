<script setup lang="ts">
import { computed } from 'vue'
import TreeNodeView from '@/modules/games/shared/TreeNodeView.vue'
import type { TreeGraph } from '@/types/codeTrace'
import type { TreeNodeData } from '@/modules/games/shared/TreeNodeView.vue'

const props = defineProps<{
  name: string
  graph: TreeGraph
  hotNodeIds?: Set<string>
  varChanged?: boolean
}>()

function build(id: string | null): TreeNodeData | null {
  if (!id) return null
  const n = props.graph.nodes[id]
  if (!n) return null
  const left = build(n.left)
  const right = build(n.right)
  const children = [left, right].filter(Boolean) as TreeNodeData[]
  const raw = String(n.val)
  const label = raw === '<string?>' || raw === '<未初始化>' ? '?' : raw
  return {
    id: n.id,
    label,
    val: typeof n.val === 'number' ? n.val : undefined,
    children: children.length ? children : undefined,
  }
}

const root = computed(() => build(props.graph.root))

function nodeState(id: string) {
  if (props.hotNodeIds?.has(id)) return 'picked'
  return ''
}
</script>

<template>
  <div class="trace-tree" :class="{ 'trace-tree--hot': varChanged }">
    <div class="trace-tree-label">{{ name }} <span class="tag">树</span></div>
    <div v-if="root" class="trace-tree-stage">
      <TreeNodeView :node="root" :node-state="nodeState" />
    </div>
    <p v-else class="trace-tree-empty">空树</p>
  </div>
</template>

<style scoped>
.trace-tree {
  margin-bottom: 14px;
}

.trace-tree-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
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
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.trace-tree-empty {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
}
</style>
