<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('monotonic-barrier', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const heights = ref<number[]>([])
const stack = ref<number[]>([])
const result = ref<number[]>([])
const processed = ref(0)
const msg = ref('')
const won = ref(false)
const fail = ref(false)

watch(() => props.levelId, reset, { immediate: true })

function reset() {
  heights.value = props.levelId === 'rect' ? [2, 1, 5, 6, 2, 3] : [73, 74, 71, 69, 76, 73, 72]
  stack.value = []
  result.value = heights.value.map(() => 0)
  processed.value = 0
  msg.value =
    props.levelId === 'temp'
      ? '点击下一根柱子入栈；栈顶更高时先点栈顶弹出结算，再入栈'
      : '维护递增栈：当前柱比栈顶矮时先点栈顶弹出，再点当前柱入栈'
  won.value = false
  fail.value = false
  clearLog('地震挡板启动')
}

const stackTop = computed(() => stack.value[stack.value.length - 1])

const stepIndex = computed(() => {
  if (won.value) return heights.value.length
  return Math.min(processed.value, heights.value.length - 1)
})

const stateValues = computed(() => ({
  processed: `${processed.value} / ${heights.value.length}`,
  stack: stack.value.length
    ? `下标 ${stackTop.value} (高 ${heights.value[stackTop.value!]})`
    : '空',
}))

function onBarClick(i: number) {
  if (won.value || i !== processed.value) {
    if (i !== processed.value) {
      fail.value = true
      msg.value = `请按从左到右顺序处理，当前应处理第 ${processed.value} 根`
    }
    return
  }
  fail.value = false

  if (props.levelId === 'temp') {
    while (stack.value.length && heights.value[stackTop.value!]! >= heights.value[i]!) {
      fail.value = true
      msg.value = '栈顶高度 ≥ 当前柱，应先点栈顶弹出！'
      return
    }
  } else {
    while (stack.value.length && heights.value[stackTop.value!]! > heights.value[i]!) {
      fail.value = true
      msg.value = '栈顶比当前柱高，应先弹出栈顶！'
      return
    }
  }

  stack.value.push(i)
  processed.value++
  msg.value = `柱 ${i}（${heights.value[i]}）入栈。栈：[${stack.value.map((x) => heights.value[x]).join(', ')}]`
  pushLog(`柱 ${i} 入栈`)
  if (processed.value >= heights.value.length) finish()
}

function onStackTopClick() {
  if (won.value || stack.value.length === 0) return
  const j = stack.value.pop()!
  if (props.levelId === 'temp') {
    const i = processed.value
    result.value[j] = i - j
    msg.value = `弹出下标 ${j}，等待天数 = ${result.value[j]}`
    pushLog(`弹出 ${j}，等待 ${result.value[j]} 天`)
  } else {
    msg.value = `弹出柱 ${j}，准备让更矮的柱入栈`
    pushLog(`弹出柱 ${j}`)
  }
  fail.value = false
  if (processed.value >= heights.value.length && stack.value.length === 0) finish()
}

function finish() {
  while (props.levelId === 'temp' && stack.value.length) {
    const j = stack.value.pop()!
    result.value[j] = processed.value - j
  }
  won.value = true
  msg.value =
    props.levelId === 'temp'
      ? `每日温度结果：[${result.value.join(',')}]`
      : '单调栈扫描完成，可计算矩形面积'
  pushLog('扫描完成')
  emit('cleared')
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
    :step-total="heights.length"
    :state-values="stateValues"
    :action-log="actionLog"
    @reset="reset"
  >
    <div class="workbench">
      <div class="workbench-head">
        <span class="workbench-title">温度 / 柱高</span>
        <code class="workbench-snap">进度 {{ processed }}/{{ heights.length }}</code>
      </div>
      <div class="bars">
        <button
          v-for="(h, i) in heights"
          :key="i"
          type="button"
          class="bar-wrap"
          :class="{
            'is-next': i === processed && !won,
            'is-done': i < processed,
          }"
          @click="onBarClick(i)"
        >
          <div class="bar" :style="{ height: `${h * (levelId === 'rect' ? 18 : 2)}px` }" />
          <span class="bar-val">{{ h }}</span>
          <span v-if="levelId === 'temp' && result[i]" class="wait">{{ result[i] }}天</span>
        </button>
      </div>
      <div class="stack-zone">
        <span class="stack-label">单调栈（点栈顶弹出）</span>
        <div class="stack-pile">
          <button
            v-for="(idx, si) in stack"
            :key="`${idx}-${si}`"
            type="button"
            class="stack-item"
            :class="{ 'is-top': si === stack.length - 1 }"
            @click="si === stack.length - 1 ? onStackTopClick() : undefined"
          >
            {{ heights[idx] }}
            <small>(i={{ idx }})</small>
          </button>
          <span v-if="!stack.length" class="empty">空栈 — 点击左侧下一根柱入栈</span>
        </div>
      </div>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.bars {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  min-height: 160px;
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 10px;
  background: color-mix(in srgb, #0f172a 40%, transparent);
}
.bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px;
  border: 2px solid transparent;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
}
.bar-wrap.is-next {
  border-color: #38bdf8;
}
.bar-wrap.is-done {
  opacity: 0.55;
}
.bar {
  width: 36px;
  background: linear-gradient(180deg, #38bdf8, #6366f1);
  border-radius: 4px 4px 0 0;
}
.bar-val {
  font-size: 11px;
  margin-top: 4px;
  color: var(--alp-color-muted);
}
.wait {
  font-size: 10px;
  color: #86efac;
}
.stack-zone {
  padding: 14px;
  border-radius: 10px;
  border: 1px dashed var(--alp-color-border);
}
.stack-label {
  display: block;
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-bottom: 8px;
}
.stack-pile {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 48px;
}
.stack-item {
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-weight: 700;
  cursor: pointer;
}
.stack-item.is-top {
  border-color: #fbbf24;
  box-shadow: 0 0 0 2px color-mix(in srgb, #fbbf24 35%, transparent);
}
.stack-item small {
  display: block;
  font-size: 9px;
  font-weight: 400;
  color: var(--alp-color-muted);
}
.empty {
  font-size: 12px;
  color: var(--alp-color-muted);
}
</style>
