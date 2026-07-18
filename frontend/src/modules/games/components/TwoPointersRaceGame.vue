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
// cycle 关：记录上一次移动的是 slow 还是 fast，强制交替
const lastCycleKind = ref<'slow' | 'fast' | null>(null)

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
  lastCycleKind.value = null
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
    msg.value = '环形数组：slow 每次走 1 步、fast 每次 2 步，必须交替点击直到两者相遇（有环）'
  } else {
    nums.value = [1, 1, 2, 2, 3, 4]
    left.value = 0
    right.value = 1
    writePos.value = 0
    activeTool.value = 'write'
    msg.value = '有序去重：比较 nums[right] 与 nums[write]，不同点「写入」，相同点「跳过」'
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
    { id: 'write', label: '写入新值' },
    { id: 'skip', label: '跳过重复' },
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

// dedup 关：当前比较的两个值，用于在界面上提示
const dedupCompare = computed(() => {
  if (props.levelId !== 'dedup' || won.value) return null
  if (right.value >= nums.value.length) return null
  return {
    writeVal: nums.value[writePos.value],
    rightVal: nums.value[right.value],
    same: nums.value[writePos.value] === nums.value[right.value],
  }
})

function onSelect(i: number) {
  if (won.value) return
  if (props.levelId === 'sum') {
    if (activeTool.value !== 'L' && activeTool.value !== 'R') {
      fail.value = true
      msg.value = '请先选择「设置 L」或「设置 R」'
      return
    }
    if (activeTool.value === 'L') {
      if (i >= right.value) {
        fail.value = true
        msg.value = `L 必须在 R(${right.value}) 左侧`
        return
      }
      left.value = i
      msg.value = `L = ${i}`
      fail.value = false
      pushLog(`L = ${i}`)
    } else {
      if (i <= left.value) {
        fail.value = true
        msg.value = `R 必须在 L(${left.value}) 右侧`
        return
      }
      right.value = i
      msg.value = `R = ${i}`
      fail.value = false
      pushLog(`R = ${i}`)
    }
  }
  // dedup 关不再允许点击格子移动指针，指针由写入/跳过动作自动推进
}

function moveSum(dir: 'left' | 'right') {
  if (props.levelId !== 'sum' || won.value) return
  if (left.value >= right.value) {
    fail.value = true
    msg.value = 'L 必须严格小于 R，请先正确放置指针'
    return
  }
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
  if (left.value >= right.value && !won.value) {
    fail.value = true
    msg.value = 'L 与 R 已交叉，本组无解，请重置后重新放置指针'
  }
}

// dedup 关：用户判断「不同」时点写入
function dedupWrite() {
  if (props.levelId !== 'dedup' || won.value) return
  moveCount.value++
  if (right.value >= nums.value.length) {
    fail.value = true
    msg.value = '已扫描完，没有可比的 right 元素'
    return
  }
  if (nums.value[right.value] === nums.value[writePos.value]) {
    fail.value = true
    msg.value = `nums[right]=${nums.value[right.value]} 与 nums[write]=${nums.value[writePos.value]} 相同，应点「跳过」而非写入`
    pushLog('错误：相同值却点了写入')
    return
  }
  writePos.value++
  nums.value[writePos.value] = nums.value[right.value]!
  msg.value = `写入新值 ${nums.value[writePos.value]}，write=${writePos.value}`
  pushLog(`写入 nums[${writePos.value}]=${nums.value[writePos.value]}`)
  right.value++
  fail.value = false
  checkDedupWin()
}

// dedup 关：用户判断「相同」时点跳过
function dedupSkip() {
  if (props.levelId !== 'dedup' || won.value) return
  moveCount.value++
  if (right.value >= nums.value.length) {
    fail.value = true
    msg.value = '已扫描完，没有可比的 right 元素'
    return
  }
  if (nums.value[right.value] !== nums.value[writePos.value]) {
    fail.value = true
    msg.value = `nums[right]=${nums.value[right.value]} 与 nums[write]=${nums.value[writePos.value]} 不同，应点「写入」而非跳过`
    pushLog('错误：不同值却点了跳过')
    return
  }
  right.value++
  msg.value = `跳过重复元素，right=${right.value}`
  pushLog('跳过重复')
  fail.value = false
  checkDedupWin()
}

function checkDedupWin() {
  if (right.value >= nums.value.length) {
    const result = nums.value.slice(0, writePos.value + 1)
    if (JSON.stringify(result) !== JSON.stringify(dedupTarget.value.arr)) {
      fail.value = true
      msg.value = `去重结果 [${result.join(', ')}] 不正确，应为 [${dedupTarget.value.arr.join(', ')}]`
      pushLog('结果校验失败')
      return
    }
    won.value = true
    msg.value = `去重完成！结果 [${result.join(', ')}]`
    pushLog('通关')
    emit('cleared')
  }
}

function cycleStep(kind: 'slow' | 'fast') {
  if (props.levelId !== 'cycle' || won.value) return
  // 强制交替：slow 与 fast 必须轮流前进，模拟 while 循环里一次迭代同时推进
  if (lastCycleKind.value === kind) {
    fail.value = true
    msg.value = kind === 'slow'
      ? '上一步已经移动 slow，现在应移动 fast（两指针需成对推进）'
      : '上一步已经移动 fast，现在应移动 slow（两指针需成对推进）'
    return
  }
  moveCount.value++
  const n = nums.value.length
  // 用下标取模模拟环形结构：环内 fast 每步比 slow 多走一步，必在环内追上 slow
  if (kind === 'slow') slow.value = (slow.value + 1) % n
  else fast.value = (fast.value + 2) % n
  lastCycleKind.value = kind
  msg.value = `${kind} 前进 → slow=${slow.value} fast=${fast.value}`
  fail.value = false
  pushLog(`${kind} 前进 → slow=${slow.value} fast=${fast.value}`)
  // 起点两者同在 0，第一次移动后必不相同；之后相遇即说明存在环
  if (moveCount.value >= 2 && slow.value === fast.value) {
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
  if (id === 'write') dedupWrite()
  if (id === 'skip') dedupSkip()
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
        :clickable="levelId === 'sum'"
        @select="onSelect"
      />
      <p v-if="levelId === 'sum'" class="sum-line">
        当前和 = {{ nums[left] }} + {{ nums[right] }} = {{ nums[left]! + nums[right]! }}
      </p>
      <p v-if="levelId === 'dedup' && dedupCompare" class="dedup-compare">
        比较：nums[write]={{ dedupCompare.writeVal }} vs nums[right]={{ dedupCompare.rightVal }}
      </p>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.sum-line {
  margin: 12px 0 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--game-accent, #3a8a9e);
}
.dedup-compare {
  margin: 12px 0 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--game-accent, #3a8a9e);
}
</style>
