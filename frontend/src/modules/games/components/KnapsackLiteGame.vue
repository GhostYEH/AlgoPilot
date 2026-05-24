<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('knapsack-lite', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const items = [
  { w: 2, v: 3 },
  { w: 3, v: 4 },
  { w: 4, v: 5 },
]
const capacity = 7
const choices = ref<boolean[]>([])
const robHouses = ref<number[]>([2, 7, 9, 3, 1])
const robPick = ref<boolean[]>([])
const stairsN = 5
const stairsDp = ref<(number | null)[]>([1, 1])
const stairsCursor = ref(2)
const msg = ref('')
const won = ref(false)
const fail = ref(false)

const bestValue = computed(() => {
  let w = 0
  let v = 0
  choices.value.forEach((take, i) => {
    if (take) {
      w += items[i]!.w
      v += items[i]!.v
    }
  })
  return { w, v }
})

const robSum = computed(() => {
  let sum = 0
  robPick.value.forEach((p, j) => {
    if (p) sum += robHouses.value[j]!
  })
  return sum
})

watch(
  () => props.levelId,
  () => {
    choices.value = items.map(() => false)
    robPick.value = robHouses.value.map(() => false)
    stairsDp.value = [1, 1]
    stairsCursor.value = 2
    msg.value = ''
    won.value = false
    fail.value = false
    clearLog('背包小偷开始')
  },
  { immediate: true },
)

const stepIndex = computed(() => {
  if (won.value) return (shellMeta.value?.stepCount ?? 3) - 1
  if (props.levelId === 'stairs') return Math.min(stairsCursor.value, 5)
  if (props.levelId === 'rob') return Math.min(robPick.value.filter(Boolean).length, 4)
  const taken = choices.value.filter(Boolean).length
  return Math.min(taken, 2)
})

const stateValues = computed(() => {
  if (props.levelId === 'knapsack') {
    return { w: `${bestValue.value.w}/${capacity}`, v: String(bestValue.value.v) }
  }
  if (props.levelId === 'rob') {
    return { sum: `$${robSum.value}`, picked: String(robPick.value.filter(Boolean).length) }
  }
  return { i: `dp[${stairsCursor.value}]` }
})

function toggleItem(i: number) {
  if (props.levelId !== 'knapsack' || won.value) return
  choices.value[i] = !choices.value[i]
  const { w, v } = bestValue.value
  if (w > capacity) {
    choices.value[i] = false
    fail.value = true
    msg.value = '超重了！'
    pushLog('超重，撤销选择')
    return
  }
  fail.value = false
  msg.value = `重量 ${w}，价值 ${v}`
  pushLog(choices.value[i] ? `选择物品 ${i + 1}` : `取消物品 ${i + 1}`)
  if (v === 9 && w <= capacity) {
    won.value = true
    pushLog('最优价值 9，通关')
    emit('cleared')
  }
}

function toggleRob(i: number) {
  if (props.levelId !== 'rob' || won.value) return
  const willPick = !robPick.value[i]
  if (willPick && (robPick.value[i - 1] || robPick.value[i + 1])) {
    fail.value = true
    msg.value = '相邻房屋不能同时偷'
    pushLog('相邻冲突')
    return
  }
  robPick.value[i] = willPick
  fail.value = false
  msg.value = `金额 ${robSum.value}`
  pushLog(willPick ? `偷房 ${i}` : `放弃房 ${i}`)
  if (robSum.value === 12) {
    won.value = true
    pushLog('最大金额 12')
    emit('cleared')
  }
}

function fillStairCell(i: number) {
  if (props.levelId !== 'stairs' || won.value) return
  if (i !== stairsCursor.value) {
    fail.value = true
    msg.value = `请按顺序填写 dp[${stairsCursor.value}]`
    return
  }
  const expected = stairsDp.value[i - 1]! + stairsDp.value[i - 2]!
  fail.value = false
  stairsDp.value[i] = expected
  msg.value = `dp[${i}] = dp[${i - 1}] + dp[${i - 2}] = ${expected}`
  pushLog(`dp[${i}] = ${expected}`)
  stairsCursor.value++
  if (stairsCursor.value > stairsN) {
    won.value = true
    pushLog('爬楼梯 DP 完成')
    emit('cleared')
  }
}

function doReset() {
  choices.value = items.map(() => false)
  robPick.value = robHouses.value.map(() => false)
  stairsDp.value = [1, 1]
  stairsCursor.value = 2
  won.value = false
  fail.value = false
  msg.value = ''
  clearLog('已重置')
}
</script>

<template>
  <GamePlayShell
    v-if="shellMeta"
    :meta="shellMeta"
    :hint="msg || '选择物品 / 房屋 / 填写 dp 格子'"
    :fail="fail"
    :won="won"
    :step-index="stepIndex"
    :state-values="stateValues"
    :action-log="actionLog"
    @reset="doReset"
  >
    <div class="workbench">
      <template v-if="levelId === 'knapsack'">
        <div class="workbench-head">
          <span class="workbench-title">0/1 背包</span>
          <code class="workbench-snap">容量 {{ capacity }} · 价值 {{ bestValue.v }}</code>
        </div>
        <div class="item-grid">
          <button
            v-for="(it, i) in items"
            :key="i"
            type="button"
            class="item-card"
            :class="{ selected: choices[i] }"
            @click="toggleItem(i)"
          >
            <span class="item-name">物品 {{ i + 1 }}</span>
            <span>重量 {{ it.w }} · 价值 {{ it.v }}</span>
          </button>
        </div>
      </template>
      <template v-else-if="levelId === 'rob'">
        <div class="workbench-head">
          <span class="workbench-title">打家劫舍</span>
          <code class="workbench-snap">当前金额 ${{ robSum }} · 目标 $12</code>
        </div>
        <div class="house-row">
          <button
            v-for="(h, i) in robHouses"
            :key="i"
            type="button"
            class="house-card"
            :class="{ selected: robPick[i] }"
            @click="toggleRob(i)"
          >
            <span class="house-idx">房屋 {{ i }}</span>
            <span class="house-val">${{ h }}</span>
          </button>
        </div>
      </template>
      <template v-else>
        <div class="workbench-head">
          <span class="workbench-title">爬楼梯 DP 表</span>
        </div>
        <p class="sub">点击格子填写 dp[i]（需先填好前两格）</p>
        <div class="dp-row">
          <button
            v-for="(_, i) in stairsN + 1"
            :key="i"
            type="button"
            class="dp-cell"
            :class="{
              filled: stairsDp[i] != null,
              current: i === stairsCursor && !won,
              locked: i < 2,
            }"
            :disabled="i < 2 || won"
            @click="fillStairCell(i)"
          >
            <small>i={{ i }}</small>
            {{ stairsDp[i] ?? '?' }}
          </button>
        </div>
      </template>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.item-grid,
.house-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.item-card,
.house-card {
  padding: 16px 20px;
  border-radius: 12px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  cursor: pointer;
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  transition: border-color 0.12s, transform 0.12s;
}
.item-card:hover,
.house-card:hover {
  transform: translateY(-2px);
  border-color: #38bdf8;
}
.item-card.selected,
.house-card.selected {
  border-color: #38bdf8;
  background: color-mix(in srgb, #38bdf8 18%, transparent);
}
.item-name,
.house-idx {
  display: block;
  font-weight: 700;
  margin-bottom: 4px;
}
.house-val {
  font-size: 18px;
  color: #fbbf24;
}
.sub {
  font-size: 12px;
  color: var(--alp-color-muted);
  margin: 0 0 12px;
}
.dp-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.dp-cell {
  min-width: 64px;
  padding: 12px;
  border-radius: 10px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-weight: 700;
  cursor: pointer;
}
.dp-cell.current {
  border-color: #fbbf24;
  box-shadow: 0 0 0 2px color-mix(in srgb, #fbbf24 30%, transparent);
}
.dp-cell.locked {
  opacity: 0.7;
  cursor: default;
}
.dp-cell small {
  display: block;
  font-size: 9px;
  font-weight: 400;
  color: var(--alp-color-muted);
}
</style>
