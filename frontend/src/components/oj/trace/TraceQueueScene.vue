<script setup lang="ts">
import { computed } from 'vue'
import type { MonotonicQueueScene } from '@/utils/traceQueue'

const props = defineProps<{
  scene: MonotonicQueueScene
  previousIndices?: number[]
  changed: Set<string>
}>()

function numsVal(idx: number): string | null {
  if (idx < 0 || idx >= props.scene.nums.length) return null
  return props.scene.nums[idx] ?? null
}

const operationSummary = computed(() => {
  const previous = props.previousIndices ?? []
  const current = props.scene.queueIndices
  if (!props.previousIndices || previous.join(',') === current.join(',')) return ''
  const added = current.filter((value) => !previous.includes(value))
  const removed = previous.filter((value) => !current.includes(value))
  const parts: string[] = []
  if (added.length) parts.push(`入队 ${added.join('、')}`)
  if (removed.length) parts.push(`移出 ${removed.join('、')}`)
  return parts.join('；') || '队列顺序已更新'
})

const inWindow = (i: number) => {
  const start = props.scene.windowStart
  const end = props.scene.windowEnd
  if (start == null || end == null) return false
  return i >= start && i <= end
}
</script>

<template>
  <div class="tq-trace">
    <header class="tq-head">
      <span class="tq-tag">单调队列 {{ scene.queueName }}</span>
      <span v-if="scene.windowSize != null" class="tq-badge">k = {{ scene.windowSize }}</span>
      <span v-if="scene.maxInWindow != null" class="tq-badge tq-badge--max">
        窗口最大 = {{ scene.maxInWindow }}
      </span>
      <span v-if="scene.activeIndex != null" class="tq-badge">当前 i = {{ scene.activeIndex }}</span>
    </header>

    <p v-if="operationSummary" class="tq-operation" aria-live="polite">本步{{ operationSummary }}</p>

    <div v-if="scene.nums.length" class="tq-array" aria-label="输入数组与当前窗口">
      <div v-for="(v, i) in scene.nums" :key="i" class="tq-cell-wrap">
        <span
          class="tq-cell"
          :class="{
            'tq-cell--win': inWindow(i),
            'tq-cell--idx': scene.activeIndex === i,
            'tq-cell--pulse': changed.has('i') || changed.has('j') || changed.has(scene.queueName),
          }"
        >{{ v }}</span>
        <span class="tq-idx">i={{ i }}</span>
      </div>
    </div>

    <div class="tq-deque-wrap">
      <span class="tq-deque-label">{{ scene.queueName }}（存下标，队头 → 队尾）</span>
      <div class="tq-deque-lane" :class="{ 'tq-deque-lane--hot': changed.has(scene.queueName) }">
        <span class="tq-port">队头</span>
        <template v-if="scene.queueIndices.length">
          <span
            v-for="(idx, pos) in scene.queueIndices"
            :key="`${idx}-${pos}`"
            class="tq-dq-cell"
            :class="{
              'tq-dq-cell--front': pos === 0,
              'tq-dq-cell--hot': changed.has(scene.queueName),
            }"
          >
            {{ idx }}
            <small v-if="numsVal(idx) != null" class="tq-dq-val">→ {{ numsVal(idx) }}</small>
          </span>
        </template>
        <span v-else class="tq-empty">（空队列）</span>
        <span class="tq-port">队尾</span>
      </div>
      <p v-if="!scene.queueIndices.length" class="tq-hint">
        当前步队列内容未采集到（C++ 需 gdb 能展开 deque）。
      </p>
    </div>
  </div>
</template>

<style scoped>
.tq-trace {
  margin-bottom: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--alp-color-accent) 35%, var(--alp-color-border));
  background: var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
}

.tq-head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.tq-tag {
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-accent);
}

.tq-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-accent) 14%, transparent);
  color: var(--alp-color-muted);
}

.tq-badge--max {
  color: #6aa878;
  font-weight: 600;
}

.tq-operation {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-accent);
}

.tq-array {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.tq-cell-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.tq-cell {
  display: inline-flex;
  min-width: 44px;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.tq-cell--win {
  border-color: color-mix(in srgb, #3d8a7e 50%, var(--alp-color-border));
  background: color-mix(in srgb, #3d8a7e 12%, var(--alp-bg-soft-block));
}

.tq-cell--idx {
  border-color: var(--alp-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--alp-color-primary) 30%, transparent);
}

.tq-cell--pulse {
  animation: tq-pulse 0.55s ease;
}

.tq-idx {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.tq-deque-wrap {
  border-top: 1px dashed var(--alp-color-border);
  padding-top: 12px;
}

.tq-deque-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  margin-bottom: 8px;
}

.tq-deque-lane {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px dashed color-mix(in srgb, var(--alp-color-accent) 40%, var(--alp-color-border));
  background: var(--alp-bg-soft-block);
}

.tq-deque-lane--hot {
  border-style: solid;
  border-color: var(--alp-color-accent);
}

.tq-port {
  font-size: 11px;
  color: var(--alp-color-muted);
  font-weight: 600;
}

.tq-dq-cell {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  min-width: 40px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 2px solid var(--alp-color-border);
  font-weight: 700;
  font-size: 15px;
}

.tq-dq-cell--front {
  border-color: #6aa878;
  background: color-mix(in srgb, #6aa878 14%, transparent);
}

.tq-dq-cell--hot {
  animation: tq-pulse 0.55s ease;
}

.tq-dq-val {
  font-size: 10px;
  font-weight: 500;
  color: var(--alp-color-muted);
}

.tq-empty {
  font-size: 13px;
  color: var(--alp-color-muted);
  font-style: italic;
}

.tq-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.45;
}

@keyframes tq-pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.06);
  }
  100% {
    transform: scale(1);
  }
}
</style>
