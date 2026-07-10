<script setup lang="ts">
import type { MonotonicQueueScene } from '@/utils/traceQueue'

const props = defineProps<{
  scene: MonotonicQueueScene
  changed: Set<string>
}>()

function numsVal(idx: number): string | null {
  if (idx < 0 || idx >= props.scene.nums.length) return null
  return props.scene.nums[idx] ?? null
}

const inWindow = (i: number) => {
  const s = props.scene.windowStart
  const e = props.scene.windowEnd
  if (s == null || e == null) return false
  return i >= s && i <= e
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
    </header>

    <div class="tq-array">
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
        当前步队列内容未采集到（C++ 需 gdb 能展开 deque）；仍显示数组与窗口下标 i、k。
      </p>
    </div>
  </div>
</template>

<style scoped>
.tq-trace {
  margin-bottom: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, #a78bfa 35%, var(--alp-color-border));
  background: linear-gradient(
    165deg,
    var(--alp-bg-surface) 0%,
    color-mix(in srgb, #a78bfa 8%, var(--alp-bg-soft-block)) 100%
  );
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
  color: #a78bfa;
}

.tq-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, #a78bfa 14%, transparent);
  color: var(--alp-color-muted);
}

.tq-badge--max {
  color: #4ade80;
  font-weight: 600;
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
  border-color: color-mix(in srgb, #2dd4bf 50%, var(--alp-color-border));
  background: color-mix(in srgb, #2dd4bf 12%, var(--alp-bg-soft-block));
}

.tq-cell--idx {
  border-color: #22d3ee;
  box-shadow: 0 0 0 2px color-mix(in srgb, #22d3ee 30%, transparent);
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
  border: 1px dashed color-mix(in srgb, #a78bfa 40%, var(--alp-color-border));
  background: var(--alp-bg-soft-block);
}

.tq-deque-lane--hot {
  border-style: solid;
  border-color: #a78bfa;
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
  border-color: #4ade80;
  background: color-mix(in srgb, #4ade80 14%, transparent);
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
