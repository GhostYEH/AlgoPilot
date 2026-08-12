<script setup lang="ts">
import { computed, toRef } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

function maxStepForSection(id: string) {
  const m: Record<string, number> = {
    theory: 2,
    'assign-cookies': 3,
    'non-overlapping-intervals': 3,
    'jump-game': 3,
    'gas-station': 3,
    'stock-greedy': 3,
    summary: 0,
  }
  return m[id] ?? 3
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

const caption = computed(() => {
  const m: Record<string, string> = {
    theory: '贪心：局部最优 → 需证明全局最优',
    'assign-cookies': '455：小胃口配小饼干（双指针）',
    'non-overlapping-intervals': '435：按右端点排序保留最多区间',
    'jump-game': '55/45：维护最远可达',
    'gas-station': '134：累计亏空则换起点',
    'stock-greedy': '121/122：一次买卖 vs 多次累加涨幅',
    summary: '排序 · 区间 · 覆盖 · 环',
  }
  return m[props.sectionId] ?? '贪心示意'
})

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'theory') {
    return ['每步选当前最优', '需证明不会错过全局最优', '反例则改用 DP', ''][i] ?? ''
  }
  if (s === 'assign-cookies') {
    return ['g、s 升序', 's[j]>=g[i] 满足', 'j 前进', ''][i] ?? ''
  }
  if (s === 'non-overlapping-intervals') {
    return ['按 end 排序', '选 end 最小区间', '重叠则移除当前', ''][i] ?? ''
  }
  if (s === 'jump-game') {
    return ['maxReach 随下标更新', 'i>maxReach 失败', '45：到 curEnd 步数+1', ''][i] ?? ''
  }
  if (s === 'gas-station') {
    return ['总油 < 总耗 → -1', 'curSum 亏空 → 起点 i+1', '唯一解起点可行', ''][i] ?? ''
  }
  if (s === 'stock-greedy') {
    return ['121：维护最低价', '每日更新 maxProfit', '122：累加上涨日差价', ''][i] ?? ''
  }
  return ''
})
</script>

<template>
  <figure v-if="sectionId === 'summary'" class="gr-summary">
    <figcaption class="gr-cap">{{ caption }}</figcaption>
    <div class="pill-row">
      <span class="pill">455</span>
      <span class="pill">435</span>
      <span class="pill">55</span>
      <span class="pill">134</span>
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
    <div v-if="sectionId === 'theory'" class="panel theory">
      <span class="pill" :class="{ hot: step >= 0 }">局部最优</span>
      <span class="arrow">→</span>
      <span class="pill" :class="{ hot: step >= 1 }">全局最优?</span>
      <span v-if="step >= 2" class="warn">需证明</span>
    </div>

    <div v-else-if="sectionId === 'assign-cookies'" class="panel cookies">
      <div class="row">
        <span class="lbl">g</span>
        <span v-for="(v, i) in ['1', '2', '3']" :key="'g' + i" class="cell" :class="{ hot: step >= i }">{{ v }}</span>
      </div>
      <div class="row">
        <span class="lbl">s</span>
        <span
          v-for="(v, i) in ['1', '1', '2', '3']"
          :key="'s' + i"
          class="cell"
          :class="{ hot: step >= 1 && i <= step + 1 }"
        >{{ v }}</span>
      </div>
      <span class="ptr">i, j 双指针 →</span>
    </div>

    <div v-else-if="sectionId === 'non-overlapping-intervals'" class="panel intervals">
      <span
        v-for="i in 3"
        :key="i"
        class="bar"
        :class="{ hot: step >= i, dim: step >= 2 && i === 1 }"
        :style="{ width: 48 + i * 24 + 'px' }"
      />
    </div>

    <div v-else-if="sectionId === 'jump-game'" class="panel">
      <span
        v-for="(v, i) in [2, 3, 1, 1, 4]"
        :key="i"
        class="cell"
        :class="{ hot: step >= 1 && i <= 2, dim: step >= 2 && i > 3 }"
      >{{ v }}</span>
      <span v-if="step >= 1" class="reach">maxReach</span>
    </div>

    <div v-else-if="sectionId === 'gas-station'" class="panel gas">
      <span
        v-for="(g, i) in ['+3', '-2', '+1', '-1']"
        :key="i"
        class="cell"
        :class="{ hot: step >= 1 && i === step - 1, dim: step >= 2 && i < 2 }"
      >{{ g }}</span>
      <span class="ring">环</span>
    </div>

    <div v-else-if="sectionId === 'stock-greedy'" class="panel stock">
      <span
        v-for="(p, i) in [7, 1, 5, 3, 6, 4]"
        :key="i"
        class="cell"
        :class="{
          low: step >= 0 && i === 1,
          hot: step >= 1 && (i === 4 || (step >= 2 && i > 1 && p < 6)),
        }"
      >{{ p }}</span>
      <span v-if="step >= 2" class="gain">+5</span>
    </div>
  </SteppedAnimShell>
</template>

<style scoped>
.gr-summary {
  margin: 0;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}
.gr-cap {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
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
.theory .warn {
  font-size: 10px;
  color: #9c7a3d;
  font-weight: 700;
}
.cookies {
  flex-direction: column;
  gap: 8px;
}
.row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.lbl {
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  width: 14px;
}
.ptr {
  font-size: 10px;
  color: var(--alp-color-primary, #2563eb);
  font-weight: 600;
}
.intervals {
  align-items: flex-end;
  min-height: 64px;
}
.bar {
  display: block;
  height: 12px;
  border-radius: 6px;
  background: var(--alp-color-border);
  transition: background 0.35s ease, opacity 0.35s ease;
}
.bar.hot {
  background: var(--alp-color-primary, #2563eb);
}
.bar.dim {
  opacity: 0.35;
}
.reach {
  font-size: 10px;
  font-weight: 700;
  color: #4a8a5e;
}
.gas .ring {
  font-size: 10px;
  color: #a855f7;
  font-weight: 700;
}
.stock .cell.low {
  border-color: #4a8a5e;
  color: #3a6e4a;
}
.gain {
  font-size: 11px;
  font-weight: 700;
  color: #4a8a5e;
}
</style>
