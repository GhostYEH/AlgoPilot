<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import {
  bubbleSortSteps,
  quickSortSteps,
  selectionSortSteps,
  type SortAnimStep,
} from '@/utils/sortAnimationSteps'

const INITIAL = [38, 12, 27, 44, 5, 19, 31]
const MAX_VAL = Math.max(...INITIAL, 1)
const TICK_MS = 850

type AlgoKey = 'bubble' | 'selection' | 'quick'

type SortPanel = {
  key: AlgoKey
  title: string
  hint: string
  steps: SortAnimStep[]
  stepIndex: number
  values: number[]
  active: number[]
  pivot: number | null
}

function createPanel(
  key: AlgoKey,
  title: string,
  hint: string,
  steps: SortAnimStep[],
): SortPanel {
  const first = steps[0]
  return {
    key,
    title,
    hint,
    steps,
    stepIndex: 0,
    values: first ? [...first.values] : [...INITIAL],
    active: first?.active ?? [],
    pivot: first?.pivot ?? null,
  }
}

const panels = ref<SortPanel[]>([
  createPanel('bubble', '冒泡排序', '相邻比较，较大者向后交换', bubbleSortSteps(INITIAL)),
  createPanel('selection', '选择排序', '每轮找最小放到前端', selectionSortSteps(INITIAL)),
  createPanel('quick', '快速排序', 'Lomuto 分区，末元作枢轴', quickSortSteps(INITIAL)),
])

let timer: ReturnType<typeof setInterval> | null = null

function applyStep(panel: SortPanel, idx: number): SortPanel {
  const list = panel.steps
  if (!list.length) return panel
  const s = list[idx % list.length]!
  return {
    ...panel,
    stepIndex: idx % list.length,
    values: [...s.values],
    active: s.active,
    pivot: s.pivot ?? null,
  }
}

function advanceAll() {
  panels.value = panels.value.map((p) => applyStep(p, p.stepIndex + 1))
}

onMounted(() => {
  timer = setInterval(advanceAll, TICK_MS)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="sort-demos" aria-label="排序算法可视化演示">
    <div class="sort-demos-head">
      <span class="sort-demos-title">算法可视化</span>
      <span class="sort-demos-sub">三种排序同步自动播放，体现平台可视化讲义特色</span>
    </div>

    <div class="sort-grid">
      <div
        v-for="panel in panels"
        :key="panel.key"
        class="sort-demo"
        :aria-label="`${panel.title}演示`"
      >
        <div class="sort-head">
          <span class="sort-title">{{ panel.title }}</span>
          <span class="sort-sub">{{ panel.hint }}</span>
        </div>
        <div class="bars">
          <div
            v-for="(v, i) in panel.values"
            :key="i"
            class="bar-wrap"
            :class="{
              active: panel.active.includes(i),
              pivot: panel.pivot === i,
            }"
          >
            <div class="bar" :style="{ height: `${(v / MAX_VAL) * 100}%` }" />
            <span class="bar-val">{{ v }}</span>
          </div>
        </div>
        <p class="sort-foot">
          帧 {{ panel.stepIndex + 1 }} / {{ panel.steps.length }}
          <span v-if="panel.pivot !== null" class="sort-pivot-tag">枢轴</span>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sort-demos {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border-strong);
  background: var(--alp-color-primary-soft);
}

.sort-demos-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 14px;
}

.sort-demos-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.sort-demos-sub {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.sort-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

@media (width <= 1100px) {
  .sort-grid {
    grid-template-columns: 1fr;
  }
}

.sort-demo {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: rgba(15, 23, 42, 0.35);
  min-width: 0;
}

.sort-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 10px;
}

.sort-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.sort-sub {
  font-size: 10px;
  line-height: 1.35;
  color: var(--alp-color-muted);
}

.bars {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 6px;
  height: 88px;
}

.bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  flex: 1;
  max-width: 36px;
  height: 100%;
  justify-content: flex-end;
  transition: transform 0.35s ease;
}

.bar-wrap.active {
  transform: translateY(-3px);
}

.bar {
  width: 100%;
  min-height: 6px;
  border-radius: 5px 5px 2px 2px;
  background: var(--alp-color-primary);
  transition:
    height 0.35s ease,
    background 0.25s ease;
}

.bar-wrap.active .bar {
  background: var(--alp-color-accent);
  box-shadow: 0 0 10px var(--alp-color-primary-glow);
}

.bar-wrap.pivot .bar {
  background: var(--alp-color-accent);
  box-shadow: 0 0 8px var(--alp-color-primary-glow);
}

.bar-val {
  font-size: 10px;
  color: var(--alp-color-muted);
}

.sort-foot {
  margin: 8px 0 0;
  font-size: 10px;
  color: var(--alp-color-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}

.sort-pivot-tag {
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 9px;
  color: #9c8540;
  background: rgba(156, 133, 64, 0.12);
}
</style>
