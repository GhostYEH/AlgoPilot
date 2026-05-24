<script setup lang="ts">
import { computed } from 'vue'
import type { SlidingWindowScene } from '@/utils/traceSlidingWindow'

const props = defineProps<{
  scene: SlidingWindowScene
  changed: Set<string>
}>()

const windowLen = computed(() => {
  const l = props.scene.left ?? 0
  const r = props.scene.right ?? l
  return Math.max(0, r - l + 1)
})
</script>

<template>
  <div class="sw-trace">
    <header class="sw-head">
      <span class="sw-tag">滑动窗口</span>
      <span v-if="scene.target != null" class="sw-badge">target = {{ scene.target }}</span>
      <span v-if="scene.sum != null" class="sw-badge sw-badge--sum">窗口和 sum = {{ scene.sum }}</span>
      <span v-if="scene.minLen != null" class="sw-badge sw-badge--ans">
        min_len = {{ scene.minLen > 1000 ? '∞' : scene.minLen }}
      </span>
    </header>

    <p v-if="scene.shrinking" class="sw-hint sw-hint--shrink">
      sum ≥ target：收缩左边界 left，尝试更短子数组
    </p>
    <p v-else-if="scene.right != null" class="sw-hint">
      右指针 right 扩展窗口，累加 nums[right]
    </p>

    <div class="sw-array">
      <div
        v-for="(v, i) in scene.nums"
        :key="i"
        class="sw-cell-wrap"
      >
        <span
          class="sw-cell"
          :class="{
            'sw-cell--in': scene.left != null && scene.right != null && i >= scene.left && i <= scene.right,
            'sw-cell--left': i === scene.left,
            'sw-cell--right': i === scene.right,
            'sw-cell--pulse': changed.has('right') || changed.has('left'),
          }"
        >{{ v }}</span>
        <span class="sw-idx">{{ i }}</span>
        <span v-if="i === scene.left" class="sw-ptr sw-ptr--l">L</span>
        <span v-if="i === scene.right" class="sw-ptr sw-ptr--r">R</span>
      </div>
    </div>

    <div v-if="scene.left != null && scene.right != null" class="sw-bracket">
      <span class="sw-bracket-bar" :style="{ '--len': windowLen }">
        [{{ scene.left }} … {{ scene.right }}] 长度 {{ windowLen }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.sw-trace {
  margin-bottom: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, #2dd4bf 35%, var(--alp-color-border));
  background: linear-gradient(165deg, var(--alp-bg-surface) 0%, color-mix(in srgb, #2dd4bf 8%, var(--alp-bg-soft-block)) 100%);
  box-shadow: var(--alp-shadow-card);
}

.sw-head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.sw-tag {
  font-size: 12px;
  font-weight: 700;
  color: #2dd4bf;
}

.sw-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-muted);
}

.sw-badge--sum {
  color: #38bdf8;
  border: 1px solid color-mix(in srgb, #38bdf8 40%, transparent);
}

.sw-badge--ans {
  color: #fbbf24;
  border: 1px solid color-mix(in srgb, #fbbf24 40%, transparent);
}

.sw-hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--alp-color-text);
}

.sw-hint--shrink {
  color: #f472b6;
  font-weight: 600;
}

.sw-array {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: flex-end;
}

.sw-cell-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.sw-cell {
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
  opacity: 0.45;
  transition: all 0.15s ease;
}

.sw-cell--in {
  opacity: 1;
  border-color: color-mix(in srgb, #2dd4bf 50%, var(--alp-color-border));
  background: color-mix(in srgb, #2dd4bf 12%, var(--alp-bg-soft-block));
}

.sw-cell--left {
  border-color: #f472b6;
  box-shadow: 0 0 0 2px color-mix(in srgb, #f472b6 30%, transparent);
}

.sw-cell--right {
  border-color: #38bdf8;
  box-shadow: 0 0 0 2px color-mix(in srgb, #38bdf8 30%, transparent);
}

.sw-cell--pulse {
  animation: sw-pulse 0.55s ease;
}

.sw-idx {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.sw-ptr {
  position: absolute;
  top: -18px;
  font-size: 10px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
}

.sw-ptr--l {
  color: #f472b6;
  background: color-mix(in srgb, #f472b6 20%, transparent);
}

.sw-ptr--r {
  color: #38bdf8;
  background: color-mix(in srgb, #38bdf8 20%, transparent);
}

.sw-bracket {
  margin-top: 12px;
  text-align: center;
}

.sw-bracket-bar {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  color: #2dd4bf;
  padding: 4px 12px;
  border-radius: 8px;
  border: 1px dashed color-mix(in srgb, #2dd4bf 50%, transparent);
}

@keyframes sw-pulse {
  50% {
    transform: scale(1.06);
  }
}
</style>
