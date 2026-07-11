<script setup lang="ts">
import { computed, toRef } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'
import {
  bubbleSortSteps,
  selectionSortSteps,
  insertionSortSteps,
  mergeSortSteps,
  quickSortSteps,
  heapSortSteps,
  type SortAnimStep,
} from '@/utils/sortAnimationSteps'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

// 各节演示用的初始数组
const DEMO_BASIC = [5, 1, 4, 2, 8, 3]
const DEMO_MERGE = [6, 3, 8, 2, 9, 1]
const DEMO_QUICK = [6, 2, 8, 4, 7, 3]
const DEMO_HEAP = [4, 10, 3, 5, 1, 8]

// 为每节预生成排序步骤
const BASIC_STEPS = bubbleSortSteps(DEMO_BASIC)
const SELECTION_STEPS = selectionSortSteps(DEMO_BASIC)
const INSERTION_STEPS = insertionSortSteps(DEMO_BASIC)
const MERGE_STEPS = mergeSortSteps(DEMO_MERGE)
const QUICK_STEPS = quickSortSteps(DEMO_QUICK)
const HEAP_STEPS = heapSortSteps(DEMO_HEAP)

// 基础排序节：三种排序之间的分隔步骤（重置为原始数组，提示即将切换算法）
const SEP_TO_SELECTION: SortAnimStep = {
  values: [...DEMO_BASIC],
  active: [],
  hint: '—— 冒泡排序结束，接下来展示选择排序 ——',
}
const SEP_TO_INSERTION: SortAnimStep = {
  values: [...DEMO_BASIC],
  active: [],
  hint: '—— 选择排序结束，接下来展示插入排序 ——',
}

// 概念节：稳定性对比（3 步）—— 用 tags 区分相同值，直观展示稳定性
const CONCEPT_STEPS: SortAnimStep[] = [
  {
    values: [3, 1, 3, 1],
    active: [0, 2],
    tags: ['a', '', 'b', ''],
    hint: '两个 3 分别记为 3ₐ 与 3ᵦ，3ₐ 在前（稳定排序应保持此顺序）',
  },
  {
    values: [1, 1, 3, 3],
    active: [2, 3],
    tags: ['', '', 'a', 'b'],
    hint: '稳定排序（如归并/插入）后：3ₐ 仍在 3ᵦ 前',
  },
  {
    values: [1, 1, 3, 3],
    active: [2, 3],
    tags: ['', '', 'b', 'a'],
    hint: '不稳定排序（如选择/堆）可能颠倒：3ᵦ 排到了 3ₐ 前',
  },
]

// Trace 节：展示归并 Trace 关键变量（3 步）
// 归并排序在最终合并前，左右两半都已排好序
const TRACE_STEPS: SortAnimStep[] = [
  {
    values: [6, 3, 8, 2, 9, 1],
    active: [0, 5],
    range: [0, 5],
    hint: '归并 Trace：初始数组，最终将合并区间 [0,5]，切点 mid=2',
  },
  {
    values: [3, 6, 8, 1, 2, 9],
    active: [0, 3],
    range: [0, 5],
    hint: '左右两半已分别排好：左 [3,6,8]，右 [1,2,9]；双指针 i=0, j=0，比较 3 与 1',
  },
  {
    values: [1, 2, 3, 6, 8, 9],
    active: [],
    range: [0, 5],
    hint: '最终合并完成，Trace 可验证双指针移动与剩余元素拷贝',
  },
]

// 各节对应的步骤数组
function stepsForSection(id: string): SortAnimStep[] {
  switch (id) {
    case 'concepts':
      return CONCEPT_STEPS
    case 'basic':
      return BASIC_STEPS
    case 'merge':
      return MERGE_STEPS
    case 'quick':
      return QUICK_STEPS
    case 'heap':
      return HEAP_STEPS
    case 'trace':
      return TRACE_STEPS
    default:
      return []
  }
}

const currentSteps = computed(() => {
  if (props.sectionId === 'basic') {
    // 基础排序节：冒泡 → 分隔 → 选择 → 分隔 → 插入
    return [
      ...BASIC_STEPS,
      SEP_TO_SELECTION,
      ...SELECTION_STEPS,
      SEP_TO_INSERTION,
      ...INSERTION_STEPS,
    ]
  }
  return stepsForSection(props.sectionId)
})

function maxStepForSection(id: string): number {
  if (id === 'practice' || id === 'summary') return 0
  const steps = id === 'basic' ? currentSteps.value : stepsForSection(id)
  return Math.max(0, steps.length - 1)
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

const caption = computed(() => {
  const m: Record<string, string> = {
    concepts: '稳定性 · 原地性 · 复杂度对比',
    basic: '冒泡 / 选择 / 插入排序',
    merge: '归并排序：分治 · 双指针合并',
    quick: '快速排序：pivot · 分区',
    heap: '堆排序：建堆 · 下沉 · 提取',
    trace: 'Trace 可视化：合并 · pivot · 堆化',
    practice: 'OJ 分层实操',
  }
  return m[props.sectionId] ?? '排序算法示意'
})

const currentStep = computed(() => {
  const steps = props.sectionId === 'basic' ? currentSteps.value : stepsForSection(props.sectionId)
  if (steps.length === 0) return null
  return steps[Math.min(step.value, steps.length - 1)]
})

const stepHint = computed(() => {
  const s = currentStep.value
  if (!s) return ''
  // 基础排序节：标注当前展示的是哪种排序
  if (props.sectionId === 'basic') {
    const bubbleLen = BASIC_STEPS.length
    // 分隔步骤占 1 步
    const selStart = bubbleLen + 1
    const selLen = SELECTION_STEPS.length
    const insStart = selStart + selLen + 1
    if (step.value === bubbleLen || step.value === selStart + selLen) {
      // 分隔步骤本身
      return s.hint ?? ''
    }
    let label = '冒泡排序'
    if (step.value >= insStart) label = '插入排序'
    else if (step.value >= selStart) label = '选择排序'
    return `[${label}] ${s.hint ?? ''}`
  }
  return s.hint ?? ''
})

function cellClass(index: number): string {
  const s = currentStep.value
  if (!s) return ''
  // pivot 优先于 active：快速排序比较时 pivot 同时在 active 中，
  // 需用紫色区分枢轴，否则用户看不出哪个是 pivot
  if (s.pivot === index) return 'cell--pivot'
  if (s.active?.includes(index)) return 'cell--active'
  // 已就位标记：sortedFrom 标记后缀，sortedUntil 标记前缀
  if (s.sortedFrom !== undefined && index >= s.sortedFrom) return 'cell--done'
  if (s.sortedUntil !== undefined && index <= s.sortedUntil) return 'cell--done'
  if (s.range) {
    const [lo, hi] = s.range
    if (index >= lo && index <= hi) return 'cell--range'
  }
  return ''
}

function isHeapArea(index: number): boolean {
  const s = currentStep.value
  if (!s || s.heapSize === undefined) return false
  return index < s.heapSize
}
</script>

<template>
  <SteppedAnimShell
    :caption="caption"
    :use-stepped="useStepped"
    :step-hint="stepHint"
    :step="step"
    :max-step="maxStep"
    :playing="playing"
    @toggle-play="togglePlay"
    @next="manualNext"
    @reset="resetAnim"
  >
    <div class="sorting-viz" aria-label="排序过程分步演示">
      <!-- 数组条形可视化 -->
      <div v-if="currentStep" class="bar-stage">
        <div
          v-for="(value, index) in currentStep.values"
          :key="`cell-${index}`"
          class="bar-cell"
          :class="[cellClass(index), { 'bar-cell--heap': isHeapArea(index) }]"
        >
          <span class="bar-value">
            {{ value }}<sub v-if="currentStep.tags?.[index]" class="bar-tag">{{ currentStep.tags[index] }}</sub>
          </span>
          <span class="bar-index">{{ index }}</span>
        </div>
      </div>

      <!-- 无步骤的节（practice 等）显示静态说明 -->
      <div v-else class="static-hint">
        <p>本节侧重 OJ 实操，可结合下方在线练习观察真实运行轨迹。</p>
      </div>

      <!-- 图例 -->
      <div v-if="currentStep" class="legend">
        <span class="legend-item"><i class="dot dot--active" /> 比较中</span>
        <span class="legend-item"><i class="dot dot--pivot" /> pivot</span>
        <span class="legend-item"><i class="dot dot--range" /> 当前区间</span>
        <span class="legend-item"><i class="dot dot--done" /> 已就位</span>
      </div>
    </div>
  </SteppedAnimShell>
</template>

<style scoped>
.sorting-viz {
  padding: 16px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--alp-color-primary) 4%, var(--alp-bg-surface));
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 20%, var(--alp-color-border));
}

.bar-stage {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  min-height: 80px;
  align-items: flex-end;
}

.bar-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 52px;
  border: 2px solid var(--alp-color-border);
  border-radius: 8px;
  background: var(--alp-bg-surface);
  color: var(--alp-color-text);
  transition:
    border-color 0.25s ease,
    background 0.25s ease,
    transform 0.25s ease;
}

.bar-cell--heap {
  border-style: dashed;
  border-color: color-mix(in srgb, #7a6e9e 40%, var(--alp-color-border));
}

.bar-value {
  font-size: 16px;
  font-weight: 700;
}

.bar-tag {
  font-size: 10px;
  font-weight: 600;
  color: var(--alp-color-primary);
  vertical-align: sub;
  margin-left: 1px;
}

.bar-index {
  margin-top: 2px;
  font-size: 10px;
  color: var(--alp-color-muted);
}

.bar-cell.cell--active {
  border-color: #e8a838;
  background: color-mix(in srgb, #e8a838 18%, var(--alp-bg-surface));
  transform: translateY(-4px);
}

.bar-cell.cell--pivot {
  border-color: #c050c0;
  background: color-mix(in srgb, #c050c0 18%, var(--alp-bg-surface));
}

.bar-cell.cell--range {
  border-color: #7a6e9e;
  background: color-mix(in srgb, #7a6e9e 10%, var(--alp-bg-surface));
}

.bar-cell.cell--done {
  border-color: #4a8a5e;
  background: color-mix(in srgb, #4a8a5e 14%, var(--alp-bg-surface));
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 14px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
  border: 2px solid var(--alp-color-border);
}

.dot--active {
  border-color: #e8a838;
  background: color-mix(in srgb, #e8a838 30%, transparent);
}

.dot--pivot {
  border-color: #c050c0;
  background: color-mix(in srgb, #c050c0 30%, transparent);
}

.dot--range {
  border-color: #7a6e9e;
  background: color-mix(in srgb, #7a6e9e 30%, transparent);
}

.dot--done {
  border-color: #4a8a5e;
  background: color-mix(in srgb, #4a8a5e 30%, transparent);
}

.static-hint {
  padding: 20px 8px;
  color: var(--alp-color-muted);
  font-size: 13px;
  text-align: center;
}
</style>
