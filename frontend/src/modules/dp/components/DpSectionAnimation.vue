<script setup lang="ts">
import { computed, toRef } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

function maxStepForSection(id: string) {
  const m: Record<string, number> = {
    theory: 2,
    'five-steps': 4,
    'climbing-stairs': 3,
    'knapsack-01': 3,
    'unbounded-knapsack': 3,
    'coin-change': 3,
    lis: 3,
    summary: 0,
  }
  return m[id] ?? 3
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

const caption = computed(() => {
  const m: Record<string, string> = {
    theory: 'DP：重叠子问题 + 最优子结构',
    'five-steps': '五部曲：定义 · 递推 · 初始化 · 顺序 · 验证',
    'climbing-stairs': '70：dp[i]=dp[i-1]+dp[i-2]',
    'knapsack-01': '01 背包：容量逆序遍历',
    'unbounded-knapsack': '完全背包：容量正序（可重复选）',
    'coin-change': '322：最少硬币数',
    lis: '300：以 i 结尾的 LIS',
    summary: '线性 · 背包 · 子序列',
  }
  return m[props.sectionId] ?? '动态规划示意'
})

const dpRow = computed(() => {
  if (props.sectionId === 'climbing-stairs') {
    return [['1'], ['1', '1'], ['1', '1', '2'], ['1', '1', '2', '3']][step.value] ?? []
  }
  if (props.sectionId === 'coin-change') {
    return [['0'], ['∞', '1'], ['∞', '1', '2'], ['∞', '1', '2', '2']][step.value] ?? []
  }
  if (props.sectionId === 'knapsack-01') {
    return [['F'], ['F', 'T'], ['F', 'T', 'T'], ['F', 'T', 'T', 'T']][step.value] ?? []
  }
  if (props.sectionId === 'lis') {
    return [['1'], ['1', '2'], ['1', '2', '2'], ['1', '2', '3']][step.value] ?? []
  }
  if (props.sectionId === 'unbounded-knapsack') {
    return [['—'], ['1'], ['1', '2'], ['1', '2', '2']][step.value] ?? []
  }
  return []
})

const fiveSteps = ['① 定义 dp', '② 递推式', '③ 初始化', '④ 遍历顺序', '⑤ 验证样例']

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'theory') {
    return ['子问题重叠：fib(n) 重复计算', '用 dp 表保存已算结果', ''][i] ?? ''
  }
  if (s === 'five-steps') {
    return [
      '明确 dp[i] 或 dp[i][j] 含义',
      '写出状态转移方程',
      '边界 dp[0]、dp[1] 等初始化',
      '01 背包逆序 / 完全背包正序',
      '打印 dp 表对照样例',
    ][i] ?? ''
  }
  if (s === 'climbing-stairs') {
    return ['dp[0]=1', 'dp[1]=1', 'dp[2]=dp[1]+dp[0]=2', 'dp[3]=2+1=3', ''][i] ?? ''
  }
  if (s === 'knapsack-01') {
    return ['dp[0] 空集', '物品1 更新容量', '逆序避免重复使用', ''][i] ?? ''
  }
  if (s === 'unbounded-knapsack') {
    return ['dp[0]=0', '硬币1：正序更新', '同一硬币可再用', 'dp[4]=2', ''][i] ?? ''
  }
  if (s === 'coin-change') {
    return ['dp[0]=0', '硬币1：dp[1]=1', '再枚硬币2', 'dp[4]=2', ''][i] ?? ''
  }
  if (s === 'lis') {
    return ['以 0 结尾长度 1', '以 1 结尾长度 2', '以 2 结尾长度 2', '以 3 结尾长度 3', ''][i] ?? ''
  }
  return ''
})

const summaryPills = ['70 爬楼梯', '01 背包', '322 零钱', '300 LIS']
</script>

<template>
  <figure v-if="sectionId === 'summary'" class="dp-summary">
    <figcaption class="dp-cap">{{ caption }}</figcaption>
    <div class="pill-row">
      <span v-for="p in summaryPills" :key="p" class="pill">{{ p }}</span>
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
    <div v-if="sectionId === 'theory'" class="panel overlap">
      <span class="cell" :class="{ hot: step >= 0 }">fib(4)</span>
      <span class="branch">├ fib(3)</span>
      <span class="branch dim" :class="{ hot: step >= 1 }">│ ├ fib(2) …</span>
      <span class="hint">重复子问题 → 用 dp[] 缓存</span>
    </div>

    <div v-else-if="sectionId === 'five-steps'" class="panel steps">
      <span
        v-for="(t, i) in fiveSteps"
        :key="i"
        class="step-pill"
        :class="{ hot: step >= i, dim: step < i }"
      >{{ t }}</span>
    </div>

    <div v-else-if="sectionId === 'unbounded-knapsack'" class="panel order">
      <div class="order-col">
        <span class="lbl">01 背包</span>
        <span class="arrow-down">j: W → w</span>
        <span class="cell dim">逆序</span>
      </div>
      <div class="order-col hot-col">
        <span class="lbl">完全背包</span>
        <span class="arrow-down">j: w → W</span>
        <span class="cell hot">正序</span>
      </div>
      <div class="dp-mini">
        <span v-for="(v, i) in dpRow" :key="i" class="cell" :class="{ hot: i === dpRow.length - 1 }">{{ v }}</span>
      </div>
    </div>

    <div v-else-if="dpRow.length" class="panel dp-grid">
      <span v-for="(v, i) in dpRow" :key="i" class="cell" :class="{ hot: i === dpRow.length - 1 }">{{ v }}</span>
    </div>
  </SteppedAnimShell>
</template>

<style scoped>
.dp-summary {
  margin: 0;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}
.dp-cap {
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
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  background: #fff;
  border: 1px solid #e2e8f0;
}
.overlap {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 8px 12px;
}
.branch {
  font-size: 11px;
  color: #64748b;
  font-family: ui-monospace, monospace;
}
.branch.dim {
  opacity: 0.5;
}
.branch.hot,
.branch.dim.hot {
  opacity: 1;
  color: var(--alp-color-primary, #2563eb);
  font-weight: 600;
}
.hint {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 4px;
}
.steps {
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}
.step-pill {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}
.step-pill.hot {
  background: rgba(37, 99, 235, 0.15);
  border-color: #2563eb;
  color: #1d4ed8;
}
.step-pill.dim {
  opacity: 0.45;
}
.order {
  gap: 12px;
  flex-wrap: wrap;
}
.order-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}
.order-col.hot-col {
  border-color: #2563eb;
  background: rgba(37, 99, 235, 0.06);
}
.lbl {
  font-size: 10px;
  font-weight: 700;
}
.arrow-down {
  font-size: 10px;
  color: #64748b;
}
.dp-mini {
  display: flex;
  gap: 4px;
}
.dp-grid {
  gap: 6px;
}
</style>
