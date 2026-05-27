<script setup lang="ts">
import { computed, ref } from 'vue'
import TreeNodeView from '@/modules/games/shared/TreeNodeView.vue'
import type { TreeGraph } from '@/types/codeTrace'
import type { TreeNodeData } from '@/modules/games/shared/TreeNodeView.vue'

const props = defineProps<{
  name: string
  graph: TreeGraph
  hotNodeIds?: Set<string>
  varChanged?: boolean
}>()

/** 大树默认折叠深度，展开后再渲染深层子树（双阶段懒加载思路） */
const LAZY_DEPTH = 3
const expanded = ref(false)

const nodeCount = computed(() => Object.keys(props.graph.nodes).length)
const useLazy = computed(() => nodeCount.value > 12)

function build(id: string | null, depth = 0): TreeNodeData | null {
  if (!id) return null
  const n = props.graph.nodes[id]
  if (!n) return null
  const left = build(n.left, depth + 1)
  const right = build(n.right, depth + 1)
  let children = [left, right].filter(Boolean) as TreeNodeData[]
  if (useLazy.value && !expanded.value && depth >= LAZY_DEPTH) {
    const hasHidden = n.left || n.right
    children = hasHidden
      ? [{ id: `${id}-more`, label: '…', children: undefined }]
      : []
  }
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
    <div class="trace-tree-label">
      {{ name }} <span class="tag">树</span>
      <el-button
        v-if="useLazy"
        link
        type="primary"
        size="small"
        class="expand-btn"
        @click="expanded = !expanded"
      >
        {{ expanded ? '收起深层' : `展开全部 (${nodeCount} 节点)` }}
      </el-button>
    </div>
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
  flex-wrap: wrap;
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
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.trace-tree-empty {
  font-size: 12px;
  color: var(--alp-color-muted);
}
</style>
