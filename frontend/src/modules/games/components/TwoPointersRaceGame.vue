<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GameArrayBoard from '@/modules/games/shared/GameArrayBoard.vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import GameToolPalette from '@/modules/games/shared/GameToolPalette.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('two-pointers-race', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const nums = ref<number[]>([])
const left = ref(0)
const right = ref(0)
const slow = ref(0)
const fast = ref(0)
const writePos = ref(0)
const activeTool = ref('L')
const msg = ref('')
const won = ref(false)
const fail = ref(false)
const moveCount = ref(0)

const dedupTarget = computed(() => {
  const arr = [...nums.value]
  let w = 0
  for (let r = 1; r < arr.length; r++) {
    if (arr[r] !== arr[w]) {
      w++
      arr[w] = arr[r]!
    }
  }
  return { length: w + 1, arr: arr.slice(0, w + 1) }
})

function reset() {
  fail.value = false
  won.value = false
  moveCount.value = 0
  if (props.levelId === 'sum') {
    nums.value = [-1, 0, 1, 2, 3, 5]
    left.value = 0
    right.value = nums.value.length - 1
    activeTool.value = 'L'
    msg.value = '目标和为 0：先点「选 L/R」再点数组下标设置指针；然后选移动方向'
  } else if (props.levelId === 'cycle') {
    nums.value = [1, 2, 3, 4, 5]
    slow.value = 0
    fast.value = 0
    activeTool.value = 'slow'
    msg.value = '① 移动 slow 到 0，fast 到 0（已默认）→ ② 交替点 slow+1 / fast+2'
  } else {
    nums.value = [1, 1, 2, 2, 3, 4]
    left.value = 0
    right.value = 1
    writePos.value = 0
    activeTool.value = 'write'
    msg.value = '有序去重：用 write 写下标。若 nums[right]≠nums[write] 则 write++ 并写入'
  }
  clearLog('双指针赛跑开始')
}

watch(() => props.levelId, reset, { immediate: true })

const pointers = computed(() => {
  if (props.levelId === 'cycle') {
    return { slow: slow.value, fast: fast.value }
  }
  return { L: left.value, R: right.value, w: writePos.value }
})

const tools = computed(() => {
  if (props.levelId === 'sum') {
    return [
      { id: 'L', label: '设置 L' },
      { id: 'R', label: '设置 R' },
      { id: 'move-left', label: 'L++（和太小）' },
      { id: 'move-right', label: 'R--（和太大）' },
    ]
  }
  if (props.levelId === 'cycle') {
    return [
      { id: 'slow', label: 'slow +1' },
      { id: 'fast', label: 'fast +2' },
    ]
  }
  return [
    { id: 'write', label: '移动 write' },
    { id: 'right', label: '移动 right' },
    { id: 'commit', label: '写入/跳过' },
  ]
})

const stepIndex = computed(() => {
  if (won.value) return 2
  return Math.min(moveCount.value, 2)
})

const stateValues = computed(() => {
  if (props.levelId === 'cycle') {
    return { slow: String(slow.value), fast: String(fast.value) }
  }
  if (props.levelId === 'sum') {
    return {
      L: String(left.value),
      R: String(right.value),
    }
  }
  return {
    L: String(writePos.value),
    R: String(right.value),
    w: String(writePos.value),
  }
})

const arraySnap = computed(() => nums.value.join(', '))

function onSelect(i: number) {
  if (won.value) return
  if (props.levelId === 'sum') {
    if (activeTool.value === 'L') {
      left.value = i
      msg.value = `L = ${i}`
      fail.value = false
      pushLog(`L = ${i}`)
    } else if (activeTool.value === 'R') {
      right.value = i
      msg.value = `R = ${i}`
      fail.value = false
      pushLog(`R = ${i}`)
    } else {
      fail.value = true
      msg.value = '请先选择「设置 L」或「设置 R」'
    }
    return
  }
  if (props.levelId === 'dedup') {
    if (activeTool.value === 'write') writePos.value = i
    else if (activeTool.value === 'right') right.value = i
    else {
      fail.value = true
      return
    }
    msg.value = `write=${writePos.value} right=${right.value}`
    fail.value = false
    pushLog(`write=${writePos.value} right=${right.value}`)
  }
}

function moveSum(dir: 'left' | 'right') {
  if (props.levelId !== 'sum' || won.value) return
  const s = nums.value[left.value]! + nums.value[right.value]!
  moveCount.value++
  if (s === 0) {
    won.value = true
    msg.value = `nums[${left.value}]+nums[${right.value}]=0，找到解！`
    pushLog('找到和为 0')
    emit('cleared')
    return
  }
  if (dir === 'left' && s < 0) {
    left.value++
    msg.value = `和=${s}<0，L 右移`
    fail.value = false
    pushLog('和太小，L++')
  } else if (dir === 'right' && s > 0) {
    right.value--
    msg.value = `和=${s}>0，R 左移`
    fail.value = false
    pushLog('和太大，R--')
  } else {
    fail.value = true
    msg.value = s < 0 ? '和太小应 L++' : '和太大应 R--'
  }
}

function dedupCommit() {
  if (props.levelId !== 'dedup' || won.value) return
  moveCount.value++
  if (right.value >= nums.value.length) {
    won.value = true
    msg.value = `去重完成，有效长度 ${writePos.value + 1}`
    pushLog('去重完成')
    emit('cleared')
    return
  }
  if (nums.value[right.value] !== nums.value[writePos.value]) {
    writePos.value++
    nums.value[writePos.value] = nums.value[right.value]!
    msg.value = '新值写入 write 位置'
    pushLog('写入不重复元素')
  } else {
    msg.value = '重复元素，仅 right 前进'
    pushLog('跳过重复')
  }
  right.value++
  fail.value = false
  if (right.value >= nums.value.length) {
    won.value = true
    msg.value = `完成！结果 [${dedupTarget.value.arr.join(', ')}]`
    pushLog('通关')
    emit('cleared')
  }
}

function cycleStep(kind: 'slow' | 'fast') {
  if (props.levelId !== 'cycle' || won.value) return
  moveCount.value++
  if (kind === 'slow') slow.value++
  else fast.value = Math.min(fast.value + 2, nums.value.length - 1)
  msg.value = `slow=${slow.value} fast=${fast.value}`
  fail.value = false
  pushLog(`${kind} 前进`)
  if (fast.value >= nums.value.length) {
    won.value = true
    msg.value = 'fast 到达尾部 → 无环'
    pushLog('无环')
    emit('cleared')
  } else if (slow.value === fast.value) {
    won.value = true
    msg.value = '相遇 → 有环！'
    pushLog('相遇有环')
    emit('cleared')
  }
}

function onTool(id: string) {
  activeTool.value = id
  if (id === 'move-left') moveSum('left')
  if (id === 'move-right') moveSum('right')
  if (id === 'commit') dedupCommit()
  if (id === 'slow') cycleStep('slow')
  if (id === 'fast') cycleStep('fast')
}
</script>

<template>
  <GamePlayShell
    v-if="shellMeta"
    :meta="shellMeta"
    :hint="msg"
    :fail="fail"
    :won="won"
    :step-index="stepIndex"
    :state-values="stateValues"
    :action-log="actionLog"
    @reset="reset"
  >
    <div class="workbench">
      <div class="workbench-head">
        <span class="workbench-title">数组跑道</span>
        <code class="workbench-snap">[{{ arraySnap }}]</code>
      </div>
      <GameToolPalette :tools="tools" :active-id="activeTool" @select="onTool" />
      <GameArrayBoard
        :values="nums"
        :pointers="pointers"
        clickable
        @select="onSelect"
      />
      <p v-if="levelId === 'sum'" class="sum-line">
        当前和 = {{ nums[left] }} + {{ nums[right] }} = {{ nums[left]! + nums[right]! }}
      </p>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.sum-line {
  margin: 12px 0 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--game-accent, #38bdf8);
}
</style>
