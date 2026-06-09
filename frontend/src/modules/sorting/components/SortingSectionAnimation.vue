<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ sectionId: string }>()

const frames = computed(() => {
  if (props.sectionId === 'merge') {
    return [
      { label: '左区间', values: [1, 5, 7], color: 'primary' },
      { label: '右区间', values: [2, 3, 9], color: 'accent' },
      { label: '合并结果', values: [1, 2, 3, 5, 7, 9], color: 'done' },
    ]
  }
  if (props.sectionId === 'quick') {
    return [
      { label: '待分区', values: [6, 2, 8, 4, 7, 3], color: 'primary' },
      { label: 'pivot = 4', values: [2, 3, 4, 6, 7, 8], color: 'accent' },
    ]
  }
  if (props.sectionId === 'heap') {
    return [
      { label: '原数组', values: [4, 10, 3, 5, 1], color: 'primary' },
      { label: '最大堆', values: [10, 5, 3, 4, 1], color: 'accent' },
    ]
  }
  return [
    { label: '输入', values: [5, 1, 4, 2, 8], color: 'primary' },
    { label: '有序', values: [1, 2, 4, 5, 8], color: 'done' },
  ]
})
</script>

<template>
  <div class="sorting-viz" aria-label="排序过程示意">
    <div class="viz-title">Sorting Trace · {{ sectionId }}</div>
    <div v-for="frame in frames" :key="frame.label" class="frame-row">
      <span class="frame-label">{{ frame.label }}</span>
      <div class="cells">
        <span
          v-for="(value, index) in frame.values"
          :key="`${frame.label}-${index}`"
          class="cell"
          :class="`cell--${frame.color}`"
        >
          {{ value }}
        </span>
      </div>
    </div>
    <p class="viz-note">答辩演示可结合 OJ Trace 查看指针、区间与交换位置的真实执行轨迹。</p>
  </div>
</template>

<style scoped>
.sorting-viz {
  padding: 18px;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 24%, var(--alp-color-border));
  border-radius: 14px;
  background: color-mix(in srgb, var(--alp-color-primary) 5%, var(--alp-bg-surface));
}
.viz-title {
  margin-bottom: 14px;
  color: var(--alp-color-primary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.frame-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 10px 0;
}
.frame-label {
  width: 76px;
  color: var(--alp-color-muted);
  font-size: 13px;
}
.cells {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.cell {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border: 1px solid var(--alp-color-border);
  border-radius: 9px;
  background: var(--alp-bg-surface);
  color: var(--alp-color-text);
  font-weight: 700;
}
.cell--primary {
  border-color: #38bdf8;
}
.cell--accent {
  border-color: #a78bfa;
  background: color-mix(in srgb, #a78bfa 12%, var(--alp-bg-surface));
}
.cell--done {
  border-color: #22c55e;
  background: color-mix(in srgb, #22c55e 12%, var(--alp-bg-surface));
}
.viz-note {
  margin: 14px 0 0;
  color: var(--alp-color-muted);
  font-size: 12px;
}
</style>
