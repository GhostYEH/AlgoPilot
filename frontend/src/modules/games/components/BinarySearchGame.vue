<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GameArrayBoard from '@/modules/games/shared/GameArrayBoard.vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import GameToolPalette from '@/modules/games/shared/GameToolPalette.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('binary-search', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const LEVELS: Record<string, { nums: number[]; target: number; answer: number; hint: string }> = {
  find: {
    nums: [2, 5, 8, 12, 16, 23, 38, 56, 72, 91],
    target: 23,
    answer: 5,
    hint: '先点「设 L/R」再点下标；然后点「猜 mid」根据比较收缩区间',
  },
  lower: {
    nums: [2, 5, 8, 12, 16, 20, 25],
    target: 15,
    answer: 4,
    hint: 'lower_bound：nums[mid] < target 则 L=mid+1，否则 R=mid',
  },
  rotated: {
    nums: [4, 5, 6, 7, 0, 1, 2],
    target: 0,
    answer: 4,
    hint: '旋转数组：nums[mid]>nums[R] 则 L=mid+1，否则 R=mid',
  },
}

const cfg = computed(() => LEVELS[props.levelId] ?? LEVELS.find!)
const left = ref(0)
const right = ref(0)
const mid = ref(-1)
const activeTool = ref('L')
const feedback = ref('')
const won = ref(false)
const fail = ref(false)
const guessCount = ref(0)
const awaitingDecision = ref(false)

watch(
  () => props.levelId,
  () => {
    left.value = 0
    right.value = cfg.value.nums.length - 1
    mid.value = -1
    feedback.value = cfg.value.hint
    won.value = false
    fail.value = false
    activeTool.value = 'L'
    guessCount.value = 0
    awaitingDecision.value = false
    clearLog('关卡开始：设置 L/R 后猜 mid')
  },
  { immediate: true },
)

const pointers = computed(() => {
  const p: Record<string, number> = { L: left.value, R: right.value }
  if (mid.value >= 0) p.M = mid.value
  return p
})

const stepIndex = computed(() => {
  if (won.value) return 3
  if (awaitingDecision.value || guessCount.value > 0) return 2
  if (mid.value >= 0 || activeTool.value !== 'L') return 1
  return 0
})

const stateValues = computed(() => ({
  L: String(left.value),
  R: String(right.value),
  M: mid.value >= 0 ? String(mid.value) : '—',
}))

const arraySnap = computed(() => cfg.value.nums.join(', '))

const tools = [
  { id: 'L', label: '设置 L' },
  { id: 'R', label: '设置 R' },
  { id: 'mid', label: '猜 mid 并收缩' },
]

function onSelect(i: number) {
  if (won.value || activeTool.value === 'mid') return
  if (activeTool.value === 'L') left.value = i
  else right.value = i
  if (left.value > right.value) {
    fail.value = true
    feedback.value = 'left 不能大于 right'
    return
  }
  fail.value = false
  feedback.value = `L=${left.value} R=${right.value}`
  pushLog(`设置 ${activeTool.value} = ${i}`)
}

function tryWinAt(m: number) {
  if (m !== cfg.value.answer) return false
  won.value = true
  feedback.value =
    props.levelId === 'rotated'
      ? `最小值下标 ${m}`
      : props.levelId === 'lower'
        ? `第一个 ≥ ${cfg.value.target} 的下标是 ${m}`
        : '找到目标！'
  pushLog('找到答案，通关')
  emit('cleared')
  return true
}

function guessMid() {
  activeTool.value = 'mid'
  if (won.value || awaitingDecision.value || left.value > right.value) return
  const m = Math.floor((left.value + right.value) / 2)
  mid.value = m
  guessCount.value++
  const v = cfg.value.nums[m]!
  awaitingDecision.value = true
  fail.value = false
  feedback.value =
    props.levelId === 'rotated'
      ? `mid=${m}，nums[mid]=${v}，nums[R]=${cfg.value.nums[right.value]}。请判断最小值在哪一半。`
      : `mid=${m}，nums[mid]=${v}。请根据比较结果选择下一步。`
  pushLog(`计算 mid=${m}，nums[mid]=${v}`)
}

function chooseDecision(decision: 'found' | 'discard-left' | 'discard-right' | 'keep-left') {
  if (!awaitingDecision.value || won.value || mid.value < 0) return
  const m = mid.value
  const v = cfg.value.nums[m]!
  const n = cfg.value.nums

  if (props.levelId === 'rotated') {
    const correct = n[m]! > n[right.value]! ? 'discard-left' : 'keep-left'
    if (decision !== correct) {
      fail.value = true
      feedback.value = '旋转数组要比较 nums[mid] 与 nums[R]，判断最小值是否在右半。'
      return
    }
    if (decision === 'discard-left') left.value = m + 1
    else right.value = m
    awaitingDecision.value = false
    fail.value = false
    feedback.value = `决策正确，新区间 [${left.value},${right.value}]`
    pushLog(`旋转二分决策：${decision === 'discard-left' ? 'L=mid+1' : 'R=mid'}`)
    if (left.value === right.value) tryWinAt(left.value)
    return
  }

  if (props.levelId === 'lower') {
    const correct = v < cfg.value.target ? 'discard-left' : 'keep-left'
    if (decision !== correct) {
      fail.value = true
      feedback.value = 'lower_bound 中 nums[mid] ≥ target 时不能丢掉 mid，只能令 R=mid。'
      return
    }
    if (decision === 'discard-left') left.value = m + 1
    else right.value = m
    awaitingDecision.value = false
    fail.value = false
    feedback.value =
      decision === 'discard-left'
        ? `nums[${m}]=${v} < target，L→${left.value}`
        : `nums[${m}]=${v} ≥ target，R→${right.value}`
    pushLog(`lower_bound 决策：${decision === 'discard-left' ? 'L=mid+1' : 'R=mid'}`)
    if (left.value === right.value) tryWinAt(left.value)
    return
  }

  const correct = v === cfg.value.target ? 'found' : v < cfg.value.target ? 'discard-left' : 'discard-right'
  if (decision !== correct) {
    fail.value = true
    feedback.value = '请根据 nums[mid] 与 target 的大小关系决定丢弃哪一半。'
    return
  }
  awaitingDecision.value = false
  if (decision === 'found') {
    tryWinAt(m)
    return
  }
  if (decision === 'discard-left') {
    left.value = m + 1
    feedback.value = `小了，L→${left.value}`
  } else {
    right.value = m - 1
    feedback.value = `大了，R→${right.value}`
  }
  pushLog(`二分决策：${decision === 'discard-left' ? 'L=mid+1' : 'R=mid-1'}`)
  fail.value = false
}

function doReset() {
  left.value = 0
  right.value = cfg.value.nums.length - 1
  mid.value = -1
  feedback.value = cfg.value.hint
  won.value = false
  fail.value = false
  guessCount.value = 0
  activeTool.value = 'L'
  awaitingDecision.value = false
  clearLog('已重置')
}
</script>

<template>
  <GamePlayShell
    v-if="shellMeta"
    :meta="shellMeta"
    :hint="feedback || cfg.hint"
    :fail="fail"
    :won="won"
    :step-index="stepIndex"
    :state-values="stateValues"
    :action-log="actionLog"
    @reset="doReset"
  >
    <div class="workbench">
      <div class="workbench-head">
        <span class="workbench-title">有序数组</span>
        <code class="workbench-snap">[{{ arraySnap }}]</code>
      </div>
      <p class="target-line">
        目标：{{ levelId === 'rotated' ? '最小值下标' : cfg.target }}
      </p>
      <GameToolPalette :tools="tools" :active-id="activeTool" @select="activeTool = $event" />
      <GameArrayBoard
        :values="cfg.nums"
        :pointers="pointers"
        :active-index="mid"
        :correct-index="won ? cfg.answer : undefined"
        :clickable="activeTool !== 'mid'"
        @select="onSelect"
      />
    </div>
    <template #actions>
      <el-button v-if="!awaitingDecision" type="primary" size="large" :disabled="won" @click="guessMid">
        计算 mid
      </el-button>
      <template v-else-if="levelId === 'rotated'">
        <el-button type="primary" plain @click="chooseDecision('discard-left')">nums[mid] &gt; nums[R]，丢左半</el-button>
        <el-button type="primary" plain @click="chooseDecision('keep-left')">nums[mid] ≤ nums[R]，保留左半</el-button>
      </template>
      <template v-else-if="levelId === 'lower'">
        <el-button type="primary" plain @click="chooseDecision('discard-left')">nums[mid] &lt; target，丢左半</el-button>
        <el-button type="primary" plain @click="chooseDecision('keep-left')">nums[mid] ≥ target，保留 mid</el-button>
      </template>
      <template v-else>
        <el-button type="success" plain @click="chooseDecision('found')">命中 target</el-button>
        <el-button type="primary" plain @click="chooseDecision('discard-left')">太小，丢左半</el-button>
        <el-button type="primary" plain @click="chooseDecision('discard-right')">太大，丢右半</el-button>
      </template>
    </template>
  </GamePlayShell>
</template>

<style scoped>
.target-line {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--game-accent, #22d3ee);
}
</style>
