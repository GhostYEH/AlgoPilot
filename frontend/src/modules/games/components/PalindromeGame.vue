<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('palindrome', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const str = 'A man, a plan, a canal: Panama'
const chars = computed(() => str.split(''))
const filtered = computed(() =>
  chars.value.map((c) => (/[a-zA-Z0-9]/.test(c) ? c.toLowerCase() : null)),
)
const validIndices = computed(() => {
  const idx: number[] = []
  filtered.value.forEach((c, i) => {
    if (c) idx.push(i)
  })
  return idx
})

const leftPtr = ref(0)
const rightPtr = ref(0)
const msg = ref('')
const won = ref(false)
const fail = ref(false)

const kmpPattern = 'ababa'.split('')
const kmpUser = ref<number[]>([0])
const kmpStep = ref(1)

const kmpOptions = [
  { label: '[0,0,1,1,2]', correct: false },
  { label: '[0,1,0,1,2]', correct: false },
  { label: '[0,0,1,2,3]', correct: true },
  { label: '[0,1,2,3,4]', correct: false },
]

watch(
  () => props.levelId,
  () => {
    leftPtr.value = 0
    rightPtr.value = validIndices.value.length - 1
    kmpUser.value = [0]
    kmpStep.value = 1
    msg.value =
      props.levelId === 'palindrome'
        ? '直接点击左右指针对应的字符（跳过的符号不可点）'
        : '为 ababa 逐格填写 next：点击下方候选数字填入当前位'
    won.value = false
    fail.value = false
    clearLog('关卡开始')
  },
  { immediate: true },
)

const leftCharIdx = computed(() => validIndices.value[leftPtr.value])
const rightCharIdx = computed(() => validIndices.value[rightPtr.value])

const stepIndex = computed(() => {
  if (props.levelId === 'palindrome') {
    if (won.value) return 4
    return Math.min(leftPtr.value, 4)
  }
  if (won.value) return 4
  return Math.min(kmpStep.value, 4)
})

const stateValues = computed(() => {
  if (props.levelId === 'palindrome') {
    return {
      L: `第 ${leftPtr.value + 1} 个有效字符`,
      R: `第 ${rightPtr.value + 1} 个有效字符`,
    }
  }
  return { step: `next[${kmpStep.value}]` }
})

function onCharClick(i: number) {
  if (props.levelId !== 'palindrome' || won.value) return
  if (i !== leftCharIdx.value && i !== rightCharIdx.value) {
    fail.value = true
    msg.value = '只能点击当前 L 或 R 指向的有效字符'
    return
  }
  if (leftPtr.value >= rightPtr.value) {
    won.value = true
    msg.value = '回文验证通过！'
    pushLog('回文验证通过')
    emit('cleared')
    return
  }
  const a = filtered.value[i]
  const b = filtered.value[rightCharIdx.value!]
  if (a !== b) {
    fail.value = true
    msg.value = `不匹配：${chars.value[i]} vs ${chars.value[rightCharIdx.value!]}`
    pushLog(`不匹配 ${a} vs ${b}`)
    return
  }
  leftPtr.value++
  rightPtr.value--
  fail.value = false
  msg.value = `匹配「${a}」，L/R 向中间移动`
  pushLog(`匹配「${a}」`)
  if (leftPtr.value >= rightPtr.value) {
    won.value = true
    pushLog('通关')
    emit('cleared')
  }
}

function fillKmp(n: number) {
  if (props.levelId !== 'kmp-next' || won.value) return
  const correct = [0, 0, 1, 2, 3][kmpStep.value]
  if (n !== correct) {
    fail.value = true
    msg.value = `next[${kmpStep.value}] 应为 ${correct}，想想最长相等前后缀`
    pushLog(`填写错误：${n}`)
    return
  }
  kmpUser.value.push(n)
  kmpStep.value++
  fail.value = false
  msg.value = `next[${kmpStep.value - 1}]=${n} 正确`
  pushLog(`next[${kmpStep.value - 1}]=${n}`)
  if (kmpUser.value.length >= kmpPattern.length) {
    won.value = true
    msg.value = 'next 数组 [0,0,1,2,3] 完成！'
    pushLog('next 数组完成')
    emit('cleared')
  } else {
    msg.value = `请填写 next[${kmpStep.value}]`
  }
}

function pickKmpOption(i: number) {
  if (kmpOptions[i]?.correct) {
    won.value = true
    msg.value = '整条 next 数组正确！'
    pushLog('一次选对整条 next')
    emit('cleared')
  } else {
    fail.value = true
    msg.value = '整条不对，建议用逐格填空模式'
    pushLog('整条选项错误')
  }
}

function doReset() {
  leftPtr.value = 0
  rightPtr.value = validIndices.value.length - 1
  kmpUser.value = [0]
  kmpStep.value = 1
  won.value = false
  fail.value = false
  msg.value =
    props.levelId === 'palindrome'
      ? '直接点击左右指针对应的字符（跳过的符号不可点）'
      : '为 ababa 逐格填写 next'
  clearLog('已重置')
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
    @reset="doReset"
  >
    <div v-if="levelId === 'palindrome'" class="workbench">
      <div class="workbench-head">
        <span class="workbench-title">字符夹逼</span>
        <code class="workbench-snap">{{ str }}</code>
      </div>
      <div class="char-row">
        <button
          v-for="(c, i) in chars"
          :key="i"
          type="button"
          class="char-cell"
          :class="{
            'is-skip': !filtered[i],
            'is-l': i === leftCharIdx && leftPtr <= rightPtr,
            'is-r': i === rightCharIdx && leftPtr <= rightPtr,
            'is-done': validIndices.indexOf(i) < leftPtr || validIndices.indexOf(i) > rightPtr,
          }"
          :disabled="!filtered[i] || won"
          @click="onCharClick(i)"
        >
          {{ c }}
        </button>
      </div>
      <p class="ptr-meta">L → 第 {{ leftPtr + 1 }} 个有效字符 · R → 第 {{ rightPtr + 1 }} 个</p>
    </div>

    <div v-else class="workbench">
      <div class="workbench-head">
        <span class="workbench-title">模式串 ababa</span>
      </div>
      <div class="kmp-row">
        <span v-for="(ch, i) in kmpPattern" :key="i" class="kmp-ch">{{ ch }}</span>
      </div>
      <div class="kmp-next-row">
        <span
          v-for="(_, i) in kmpPattern"
          :key="'n' + i"
          class="kmp-next-cell"
          :class="{ 'is-current': i === kmpStep && !won }"
        >
          {{ kmpUser[i] ?? '?' }}
        </span>
      </div>
      <p class="sub">点击数字填入 next[{{ kmpStep }}]：</p>
      <div class="kmp-btns">
        <el-button v-for="n in [0, 1, 2, 3]" :key="n" @click="fillKmp(n)">{{ n }}</el-button>
      </div>
      <p class="sub">或一次选对整条：</p>
      <div class="kmp-btns">
        <el-button v-for="(opt, i) in kmpOptions" :key="i" size="small" @click="pickKmpOption(i)">
          {{ opt.label }}
        </el-button>
      </div>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.char-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 10px;
}
.char-cell {
  min-width: 28px;
  padding: 8px 6px;
  border-radius: 6px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-size: 14px;
  cursor: pointer;
}
.char-cell.is-skip {
  opacity: 0.35;
  cursor: not-allowed;
}
.char-cell.is-l {
  border-color: #22d3ee;
  box-shadow: 0 0 0 2px color-mix(in srgb, #22d3ee 30%, transparent);
}
.char-cell.is-r {
  border-color: #f472b6;
  box-shadow: 0 0 0 2px color-mix(in srgb, #f472b6 30%, transparent);
}
.char-cell.is-done {
  opacity: 0.5;
}
.ptr-meta {
  font-size: 12px;
  color: var(--alp-color-muted);
  margin: 0;
}
.kmp-row,
.kmp-next-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.kmp-ch,
.kmp-next-cell {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  font-weight: 600;
}
.kmp-next-cell.is-current {
  border-color: #fbbf24;
  background: color-mix(in srgb, #fbbf24 15%, transparent);
}
.sub {
  font-size: 12px;
  color: var(--alp-color-muted);
  margin: 8px 0 4px;
}
.kmp-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
