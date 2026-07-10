<script setup lang="ts">
import { computed, toRef } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

function maxStepForSection(id: string) {
  const m: Record<string, number> = {
    theory: 3,
    'daily-temperatures': 3,
    'next-greater': 3,
    'largest-rectangle': 3,
    'trapping-rain': 3,
    summary: 0,
  }
  return m[id] ?? 3
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

const caption = computed(() => {
  const m: Record<string, string> = {
    theory: '单调栈：维护递增/递减，不满足则 pop 处理',
    'daily-temperatures': '739：T[i] 更大时弹栈，ans[栈顶]=i-栈顶',
    'next-greater': '496：从右向左，递减栈记录下一个更大',
    'largest-rectangle': '84：遇更小高度 pop，算以 h 为高的矩形',
    'trapping-rain': '42：凹槽 min(墙)-底 × 宽，累加雨水',
    summary: '温度 · 下一个更大 · 矩形 · 雨水',
  }
  return m[props.sectionId] ?? '单调栈示意'
})

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'theory') {
    return ['当前元素入栈', '与栈顶比较，破坏单调则 pop', '被 pop 的下标得到答案', ''][i] ?? ''
  }
  if (s === 'daily-temperatures') {
    return ['单调递减栈存下标', '74>73：弹0，ans[0]=1', '75>74：弹1，ans[1]=1', '71,69入栈，剩余无更高温'][i] ?? ''
  }
  if (s === 'next-greater') {
    return ['从 nums2 末尾向左扫', '弹栈直到栈顶 > 当前', 'map 记录下一个更大', ''][i] ?? ''
  }
  if (s === 'largest-rectangle') {
    return ['递增栈存高度下标', '5,6 依次入栈', 'h=2 触发 pop 5,6', 'maxArea = 10'][i] ?? ''
  }
  if (s === 'trapping-rain') {
    return ['柱状图，求能接多少雨水', '凹槽①：(min(1,2)-0)×1 = 1', '凹槽②：(2-1)+(2-0)+(2-1) = 4', '凹槽③：(min(2,2)-1)×1 = 1，总计 6'][i] ?? ''
  }
  return ''
})

const stackTop = computed(() => {
  const frames: Record<string, string[]> = {
    theory: ['4', '2', '1'],
    'daily-temperatures': ['0', '1', '2', '2,3,4'],
    'next-greater': ['2', '4', '4,3', '4,3,1'],
    'largest-rectangle': ['0', '1,2', '1,4', '1,4,5'],
    'trapping-rain': ['—', '3', '7', '7,8,10'],
  }
  return (frames[props.sectionId] ?? [])[step.value] ?? ''
})

const rainCols = computed(() => {
  const heights = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
  const s = step.value
  const scale = 20
  const base = 12
  // 三个凹槽：左墙、右墙、水位线、有水的列
  const slots = [
    { minStep: 1, left: 1, right: 3, level: 1, waterIndices: new Set([2]) },
    { minStep: 2, left: 3, right: 7, level: 2, waterIndices: new Set([4, 5, 6]) },
    { minStep: 3, left: 8, right: 10, level: 2, waterIndices: new Set([9]) },
  ]
  return heights.map((h, i) => {
    const barH = base + h * scale
    let waterH = 0
    let isWall = false
    let isHot = false
    for (const slot of slots) {
      if (s >= slot.minStep) {
        if (i === slot.left || i === slot.right) { isWall = true; isHot = true }
        if (slot.waterIndices.has(i)) { waterH = Math.max(waterH, (slot.level - h) * scale) }
      }
    }
    return { height: h, barH, waterH, isWall, isHot, index: i }
  })
})
</script>

<template>
  <figure v-if="sectionId === 'summary'" class="ms-summary">
    <figcaption class="ms-cap">{{ caption }}</figcaption>
    <div class="pill-row">
      <span class="pill">739</span>
      <span class="pill">496</span>
      <span class="pill">84</span>
      <span class="pill">42</span>
    </div>
  </figure>

  <SteppedAnimShell
    v-else
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
    <!-- 理论：栈 + pop -->
    <div v-if="sectionId === 'theory'" class="learn-viz-panel theory-stack">
      <div class="learn-stack-well">
        <div class="learn-well-cap learn-well-cap--top">栈顶</div>
        <div class="learn-stack-body alp-vstack-body alp-vslots-3">
          <span
            v-for="(v, i) in ['1', '3', '5']"
            :key="i"
            class="learn-viz-cell"
            :class="{
              'learn-viz-cell--hot': step >= i,
              'learn-viz-cell--dim': step >= 2 && i === 2,
            }"
          >{{ v }}</span>
        </div>
        <div class="learn-well-cap learn-well-cap--bottom">栈底</div>
      </div>
      <span class="learn-viz-arrow">← pop</span>
      <span class="learn-viz-cell learn-viz-cell--hot">7</span>
    </div>

    <!-- 739：温度条 -->
    <div v-else-if="sectionId === 'daily-temperatures'" class="panel bars">
      <span
        v-for="(t, i) in ['73', '74', '75', '71', '69']"
        :key="i"
        class="cell bar-cell"
        :class="{
          hot: (step === 1 && i <= 1) || (step === 2 && i <= 2) || (step === 3 && i >= 2),
          done: (step >= 2 && i < 2) || (step === 3 && i >= 3),
        }"
        :style="{ height: (Number(t) - 64) * 4 + 'px' }"
      >{{ t }}</span>
      <p v-if="stackTop" class="sub">栈下标: {{ stackTop }}</p>
    </div>

    <!-- 496：nums2 + 栈 -->
    <div v-else-if="sectionId === 'next-greater'" class="panel ng">
      <span class="lbl">nums2</span>
      <span
        v-for="(v, i) in ['1', '3', '4', '2']"
        :key="i"
        class="cell"
        :class="{ hot: step >= 3 - i, dim: step < 3 - i }"
      >{{ v }}</span>
      <span class="arrow">→</span>
      <span class="pill">栈 {{ stackTop || '—' }}</span>
    </div>

    <!-- 84：柱状图 -->
    <div v-else-if="sectionId === 'largest-rectangle'" class="panel bars hist">
      <span
        v-for="(h, i) in [2, 1, 5, 6, 2, 3]"
        :key="i"
        class="cell bar-cell"
        :class="{
          hot: (step === 1 && i === 2) || (step === 2 && (i === 2 || i === 3)),
          pop: step === 2 && (i === 2 || i === 3),
        }"
        :style="{ height: 12 + h * 12 + 'px' }"
      >{{ h }}</span>
      <p v-if="step === 1" class="sub">递增栈：5 入栈</p>
      <p v-if="step === 2" class="sub">h=2 触发 pop：5,6 出栈，面积 10</p>
      <p v-if="step === 3" class="sub">maxArea = 10</p>
    </div>

    <!-- 42：接雨水 -->
    <div v-else-if="sectionId === 'trapping-rain'" class="panel bars rain">
      <div v-for="col in rainCols" :key="col.index" class="col">
        <span
          v-if="col.waterH > 0"
          class="water"
          :style="{ height: col.waterH + 'px' }"
        />
        <span
          class="cell bar-cell"
          :class="{ hot: col.isHot, wall: col.isWall }"
          :style="{ height: col.barH + 'px' }"
        >{{ col.height > 0 ? col.height : '' }}</span>
      </div>
      <p v-if="stackTop && stackTop !== '—'" class="sub">栈: {{ stackTop }}</p>
    </div>
  </SteppedAnimShell>
</template>

<style scoped>
.ms-summary,
.panel {
  margin: 0;
}
.ms-summary {
  padding: 14px 16px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}
.ms-cap {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-text-secondary, #64748b);
}
.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
.pill {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.theory-stack {
  gap: 10px;
}
.stack-box {
  display: flex;
  flex-direction: column-reverse;
  gap: 4px;
}
.bars {
  flex-direction: row;
  align-items: flex-end;
  gap: 6px;
}
.bars.hist,
.bars.rain {
  min-height: 120px;
}
.rain .col {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  width: 24px;
  margin: 0 2px;
}
.rain .cell.bar-cell {
  min-width: 0;
  width: 100%;
  padding: 0;
  font-size: 10px;
}
.water {
  width: 100%;
  background: rgba(59, 130, 246, 0.45);
  border-radius: 2px 2px 0 0;
}
.bar-cell.wall {
  outline: 2px solid #2563eb;
}
.cell.done {
  border-color: #4ade80;
  background: rgba(74, 222, 128, 0.15);
}
.cell.pop {
  opacity: 0.35;
  text-decoration: line-through;
}
.ng {
  flex-wrap: wrap;
  gap: 6px;
}
.lbl {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  width: 100%;
  text-align: center;
}
.sub {
  margin: 0;
  font-size: 10px;
  color: var(--alp-color-primary, #2563eb);
  font-weight: 600;
  width: 100%;
  text-align: center;
}
</style>
