<script setup lang="ts">
import { computed } from 'vue'
import type { SequenceViewHint } from '@/utils/traceProtocol'
import { diffSequenceItems } from '@/utils/traceProtocol'

const props = defineProps<{
  name: string
  viewHint: SequenceViewHint
  items: string[]
  prevItems?: string[]
  varChanged?: boolean
}>()

const diff = computed(() => diffSequenceItems(props.prevItems ?? [], props.items))

const isStack = computed(() => props.viewHint === 'stack')
const isQueueLike = computed(
  () =>
    props.viewHint === 'queue' ||
    props.viewHint === 'priority_queue' ||
    props.viewHint === 'deque' ||
    props.viewHint === 'tree_build_queue',
)
const isHorizontalGrid = computed(() => props.viewHint === 'vector' || props.viewHint === 'deque')

/** 栈：展示栈顶在上（items 为栈底→栈顶） */
const stackCellsTopFirst = computed(() => [...props.items].reverse())

const label = computed(() => {
  const map: Record<SequenceViewHint, string> = {
    vector: '数组',
    deque: '双端队列',
    stack: '栈',
    queue: '队列',
    priority_queue: '优先队列',
    tree_build_queue: '建树队列',
  }
  return map[props.viewHint] ?? '序列'
})

function cellHot(index: number): boolean {
  if (!props.varChanged) return false
  return diff.value.added.includes(index) || diff.value.removed.includes(index)
}
</script>

<template>
  <div
    class="seq-trace"
    :class="{
      'seq-trace--stack': isStack,
      'seq-trace--queue': isQueueLike && !isHorizontalGrid,
      'seq-trace--grid': isHorizontalGrid,
    }"
  >
    <header class="seq-head">
      <span class="seq-tag">{{ label }} · {{ name }}</span>
      <span v-if="viewHint === 'stack'" class="seq-badge">LIFO</span>
      <span v-else-if="isQueueLike" class="seq-badge">FIFO</span>
    </header>

    <!-- vector / deque：水平格子 -->
    <div v-if="isHorizontalGrid" class="seq-grid-wrap" :class="{ 'seq-wrap--hot': varChanged }">
      <template v-if="items.length">
        <span
          v-for="(cell, i) in items"
          :key="i + '-' + cell"
          class="seq-grid-cell"
          :class="{ 'seq-cell--hot': cellHot(i) }"
        >{{ cell }}</span>
      </template>
      <span v-else class="seq-empty">（空）</span>
    </div>

    <!-- stack：垂直桶 -->
    <div v-else-if="isStack" class="seq-stack-wrap">
      <span class="seq-cap seq-cap--top">栈顶 ↑</span>
      <div class="seq-stack-lane" :class="{ 'seq-wrap--hot': varChanged }">
        <template v-if="stackCellsTopFirst.length">
          <span
            v-for="(cell, i) in stackCellsTopFirst"
            :key="i + '-' + cell"
            class="seq-stack-cell"
            :class="{
              'seq-cell--top': i === 0,
              'seq-cell--hot': varChanged && i === 0,
            }"
          >{{ cell }}</span>
        </template>
        <span v-else class="seq-empty">（空栈）</span>
      </div>
      <span class="seq-cap seq-cap--bottom">栈底</span>
    </div>

    <!-- queue / priority_queue：水平管道 -->
    <div v-else class="seq-pipe-wrap">
      <span class="seq-pipe-label seq-pipe-label--in">入队 →</span>
      <div class="seq-pipe" :class="{ 'seq-wrap--hot': varChanged }">
        <template v-if="items.length">
          <span
            v-for="(cell, i) in items"
            :key="i + '-' + cell"
            class="seq-pipe-cell"
            :class="{
              'seq-pipe-cell--head': i === 0,
              'seq-pipe-cell--tail': i === items.length - 1,
              'seq-cell--hot': cellHot(i),
            }"
          >{{ cell }}</span>
        </template>
        <span v-else class="seq-empty">（空队列）</span>
      </div>
      <span class="seq-pipe-label seq-pipe-label--out">→ 出队</span>
    </div>
  </div>
</template>

<style scoped>
.seq-trace {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  box-shadow: var(--alp-shadow-card);
}

.seq-trace--stack {
  border-color: color-mix(in srgb, #f59e0b 35%, var(--alp-color-border));
  background: linear-gradient(
    165deg,
    var(--alp-bg-surface) 0%,
    color-mix(in srgb, #f59e0b 8%, var(--alp-bg-soft-block)) 100%
  );
}

.seq-trace--queue {
  border-color: color-mix(in srgb, #38bdf8 35%, var(--alp-color-border));
  background: linear-gradient(
    165deg,
    var(--alp-bg-surface) 0%,
    color-mix(in srgb, #38bdf8 8%, var(--alp-bg-soft-block)) 100%
  );
}

.seq-head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.seq-tag {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.seq-trace--stack .seq-tag {
  color: #f59e0b;
}

.seq-trace--queue .seq-tag {
  color: #38bdf8;
}

.seq-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--alp-bg-surface);
  color: var(--el-text-color-secondary);
}

.seq-grid-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px;
  border-radius: 8px;
  border: 1px dashed var(--alp-color-border);
}

.seq-grid-cell {
  min-width: 40px;
  padding: 8px 12px;
  text-align: center;
  font-family: ui-monospace, Consolas, monospace;
  font-weight: 600;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.seq-stack-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.seq-stack-lane {
  display: flex;
  flex-direction: column-reverse;
  align-items: center;
  gap: 4px;
  min-width: 56px;
  padding: 12px 16px;
  border-radius: 8px 8px 4px 4px;
  border: 2px solid color-mix(in srgb, #f59e0b 50%, var(--alp-color-border));
  background: color-mix(in srgb, #f59e0b 6%, var(--alp-bg-surface));
}

.seq-stack-cell {
  display: block;
  min-width: 44px;
  padding: 8px 14px;
  text-align: center;
  font-weight: 700;
  font-family: ui-monospace, Consolas, monospace;
  border-radius: 6px;
  background: var(--alp-bg-surface);
  border: 1px solid color-mix(in srgb, #f59e0b 40%, var(--alp-color-border));
  animation: seq-drop 0.35s ease-out;
}

.seq-cell--top {
  border-color: #f59e0b;
  box-shadow: 0 2px 8px color-mix(in srgb, #f59e0b 30%, transparent);
}

.seq-cap {
  font-size: 10px;
  color: var(--el-text-color-secondary);
}

.seq-pipe-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.seq-pipe {
  display: flex;
  flex: 1;
  min-width: 120px;
  gap: 6px;
  padding: 10px 14px;
  border-radius: 999px;
  border: 2px solid color-mix(in srgb, #38bdf8 45%, var(--alp-color-border));
  background: color-mix(in srgb, #38bdf8 6%, var(--alp-bg-surface));
  overflow-x: auto;
}

.seq-pipe-cell {
  flex-shrink: 0;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-family: ui-monospace, Consolas, monospace;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  animation: seq-slide 0.3s ease-out;
}

.seq-pipe-cell--head {
  border-color: #22c55e;
  box-shadow: 0 0 0 2px color-mix(in srgb, #22c55e 25%, transparent);
}

.seq-pipe-cell--tail {
  border-color: #38bdf8;
}

.seq-pipe-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.seq-empty {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.seq-wrap--hot {
  animation: seq-pulse-wrap 0.5s ease;
}

.seq-cell--hot {
  animation: seq-pulse-cell 0.6s ease 2;
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 35%, transparent);
}

@keyframes seq-drop {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes seq-slide {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes seq-pulse-wrap {
  0%,
  100% {
    box-shadow: none;
  }
  50% {
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-primary) 20%, transparent);
  }
}

@keyframes seq-pulse-cell {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.06);
  }
}
</style>
