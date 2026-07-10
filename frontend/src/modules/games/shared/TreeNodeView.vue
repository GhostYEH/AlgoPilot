<script setup lang="ts">
export interface TreeNodeData {
  id: string
  label: string
  val?: number
  children?: TreeNodeData[]
}

const props = defineProps<{
  node: TreeNodeData
  nodeState: (id: string) => string
  shakeId?: string
}>()

const emit = defineEmits<{ pick: [node: TreeNodeData] }>()
</script>

<template>
  <div class="tree-node-col">
    <button
      type="button"
      class="tree-node-btn"
      :class="[nodeState(node.id), { shake: shakeId === node.id }]"
      @click="emit('pick', node)"
    >
      {{ node.label }}
    </button>
    <div v-if="node.children?.length" class="tree-children">
      <TreeNodeView
        v-for="c in node.children"
        :key="c.id"
        :node="c"
        :node-state="nodeState"
        :shake-id="shakeId"
        @pick="emit('pick', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.tree-node-col {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.tree-children {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--alp-color-border);
}
.tree-node-btn {
  min-width: 44px;
  padding: 10px 14px;
  border-radius: 50%;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.12s, border-color 0.12s;
}
.tree-node-btn:hover {
  transform: scale(1.06);
  border-color: #22d3ee;
}
.tree-node-btn.visited {
  background: color-mix(in srgb, #22c55e 20%, transparent);
  border-color: #22c55e;
}
.tree-node-btn.picked {
  border-color: #fbbf24;
}
.tree-node-btn.shake {
  animation: shake 0.35s ease;
}
@keyframes shake {
  25% {
    transform: translateX(-4px);
  }
  75% {
    transform: translateX(4px);
  }
}
</style>
