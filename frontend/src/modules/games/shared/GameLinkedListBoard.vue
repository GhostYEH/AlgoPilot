<script setup lang="ts">
/**
 * 链表可视化：节点可点选，指针可拖拽到节点（通过先选指针再点节点）
 */
const props = withDefaults(
  defineProps<{
    values: number[]
    pointers?: Record<string, number | null | undefined>
    highlightIndex?: number
    removedIndex?: number | null
    hasCycle?: boolean
    clickable?: boolean
  }>(),
  {
    pointers: () => ({}),
    clickable: true,
    removedIndex: null,
    hasCycle: false,
  },
)

const emit = defineEmits<{ select: [index: number] }>()

const pointerColors: Record<string, string> = {
  pre: '#3a8a9e',
  cur: '#9e6e88',
  slow: '#7a6e9e',
  fast: '#9e6e4a',
  dummy: '#94a3b8',
}
</script>

<template>
  <div class="ll-board">
    <span v-if="pointers.dummy === undefined" class="head-label">head</span>
    <div v-if="pointers.dummy !== undefined" class="dummy-node">
      <span class="node-box dummy">dummy</span>
      <span class="arrow">→</span>
    </div>

    <template v-for="(v, i) in values" :key="i">
      <button
        type="button"
        class="ll-node-wrap"
        :class="{
          'is-highlight': highlightIndex === i,
          'is-removed': removedIndex === i,
          'is-clickable': clickable,
        }"
        :disabled="!clickable"
        @click="emit('select', i)"
      >
        <span class="node-box">{{ v }}</span>
        <span class="node-idx">{{ i }}</span>
        <span class="node-ptrs">
          <span
            v-for="(idx, name) in pointers"
            v-show="idx === i && name !== 'dummy'"
            :key="name"
            class="ptr-tag"
            :style="{ '--ptr-color': pointerColors[name] ?? '#3a8a9e' }"
          >{{ name }}</span>
        </span>
      </button>
      <span v-if="i < values.length - 1 || hasCycle" class="arrow">→</span>
    </template>

    <span v-if="!hasCycle" class="null-tag">null</span>
    <span v-else class="cycle-tag">↩ 回环</span>
  </div>
</template>

<style scoped>
.ll-board {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
  padding: 20px 18px;
  border-radius: 12px;
  border: 1px dashed var(--alp-color-border);
  background: color-mix(in srgb, var(--alp-color-primary, #3a8a9e) 4%, transparent);
}

.head-label {
  padding: 4px 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #6a9eb0;
  border-radius: 4px;
  background: color-mix(in srgb, #3a8a9e 12%, transparent);
}

.dummy-node {
  display: flex;
  align-items: center;
  gap: 4px;
}

.ll-node-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0;
  border: none;
  background: transparent;
  cursor: default;
}

.ll-node-wrap.is-clickable {
  cursor: pointer;
}

.ll-node-wrap.is-clickable:hover .node-box {
  transform: translateY(-3px);
  border-color: #3a8a9e;
  box-shadow: var(--alp-shadow-btn-hover);
  filter: brightness(1.08);
}

.ll-node-wrap.is-highlight .node-box {
  border-color: #9c8540;
  box-shadow: 0 0 0 3px color-mix(in srgb, #9c8540 30%, transparent);
}

.ll-node-wrap.is-removed .node-box {
  opacity: 0.35;
  text-decoration: line-through;
}

.node-box {
  min-width: 48px;
  padding: 12px 16px;
  border-radius: 10px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-weight: 700;
  font-size: 15px;
  transition: transform 0.12s, border-color 0.12s, filter var(--alp-transition-fast);
}

.node-box.dummy {
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-muted);
  border-style: dashed;
}

.node-idx {
  font-size: 10px;
  color: var(--alp-color-muted);
  margin-top: 4px;
}

.node-ptrs {
  position: absolute;
  top: -10px;
  display: flex;
  gap: 3px;
}

.ptr-tag {
  padding: 1px 6px;
  font-size: 9px;
  font-weight: 700;
  border-radius: 4px;
  background: var(--ptr-color);
  color: #0f172a;
}

.arrow {
  color: var(--alp-color-muted);
  font-size: 18px;
  user-select: none;
}

.null-tag,
.cycle-tag {
  font-size: 12px;
  color: var(--alp-color-muted);
  margin-left: 4px;
}

.cycle-tag {
  color: #9e6e88;
}
</style>
