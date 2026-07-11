<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('canteen-stack-queue', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const stack = ref<number[]>([])
const queue = ref<number[]>([])
const inStack = ref<number[]>([])
const outStack = ref<number[]>([])
const inbound = ref<number[]>([])
const parenStack = ref<string[]>([])
const stream = ref<string[]>([])
const parenCursor = ref(0)
const target = ref<number[]>([])
const output = ref<number[]>([])
const msg = ref('')
const won = ref(false)
const lives = ref(3)
const score = ref(0)
const shakeKey = ref(0)
const dualPoured = ref(false)

/** deque 关：窗口 [1,3,-1] 当前下标 3 入窗，选 deque 中应弹出的队尾下标 */
const dequeNums = [1, 3, -1, 3, 5]
const dequeWindowStart = ref(0)
const dequeIdxInDeque = ref<number[]>([])
const dequeStep = ref(0)

const nextExpected = computed(() => target.value[output.value.length])

const targetSlots = computed(() =>
  target.value.map((v, i) => ({
    v,
    filled: output.value[i] === v,
    current: !won.value && i === output.value.length,
  })),
)

watch(() => props.levelId, init, { immediate: true })

function shake() {
  shakeKey.value++
}

function loseLife(text: string) {
  lives.value--
  msg.value = text
  shake()
  if (lives.value <= 0) {
    msg.value = '生命值耗尽，点击重置再来'
  }
}

function addScore(n = 10) {
  score.value += n
}

function init() {
  stack.value = []
  queue.value = []
  inStack.value = []
  outStack.value = []
  inbound.value = []
  parenStack.value = []
  parenCursor.value = 0
  output.value = []
  msg.value = ''
  won.value = false
  lives.value = 3
  score.value = 0
  dualPoured.value = false
  dequeStep.value = 0
  dequeWindowStart.value = 0
  dequeIdxInDeque.value = []

  clearLog('食堂出餐口开门营业')

  switch (props.levelId) {
    case 'stack':
      target.value = [3, 2, 1]
      inbound.value = [1, 2, 3]
      msg.value = '先把餐盘入栈，再按目标顺序从栈顶出餐（只能点栈顶！）'
      break
    case 'queue':
      target.value = [1, 2, 3]
      inbound.value = [1, 2, 3]
      msg.value = '从右侧入队，从左侧队头出餐（只能点队头！）'
      break
    case 'dual-stack':
      target.value = [1, 2]
      inbound.value = []
      inStack.value = [1, 2]
      msg.value = 'out 空时先点「倒入 out」，再点 out 栈顶出餐'
      break
    case 'paren':
      target.value = []
      stream.value = '()[]{}'.split('')
      parenCursor.value = 0
      msg.value = '按顺序点击传送带上的括号，由栈来匹配'
      break
    case 'deque':
      target.value = []
      dequeStep.value = 0
      dequeWindowStart.value = 0
      dequeIdxInDeque.value = [1]
      msg.value = '窗口 [1,3,-1]：点击 deque 中应弹出的队尾（值 ≤ 新来的 -1）'
      break
    default:
      msg.value = `未知关卡：${props.levelId}`
  }
}

function checkWin() {
  if (JSON.stringify(output.value) !== JSON.stringify(target.value)) return
  won.value = true
  msg.value = '订单完成，通关！'
  emit('cleared')
}

// —— 栈关：入栈 / 仅栈顶可出餐 ——
function pushToStack() {
  if (won.value || lives.value <= 0) return
  if (!inbound.value.length) {
    msg.value = '待入栈区已空'
    return
  }
  stack.value.push(inbound.value.shift()!)
  addScore(5)
  pushLog(`入栈 ${stack.value[stack.value.length - 1]}`)
  msg.value = `已入栈。栈内自下而上：${stack.value.join(' → ')}`
}

function clickStackPlate(stackIndex: number) {
  if (won.value || lives.value <= 0) return
  const top = stack.value.length - 1
  if (stackIndex !== top) {
    loseLife('只能从栈顶出餐！')
    return
  }
  const expect = nextExpected.value
  if (expect === undefined) {
    loseLife('已经出够了')
    return
  }
  const v = stack.value[top]!
  if (v !== expect) {
    // 不消费餐盘，仅提示顺序错误，避免污染 output 导致本关永久不可通关
    loseLife(`顺序错了：该出 ${expect}，栈顶是 ${v}`)
    return
  }
  stack.value.pop()
  output.value.push(v)
  addScore(15)
  pushLog(`栈顶出餐 ${v}`)
  msg.value = `正确出餐 ${v}！`
  checkWin()
}

// —— 队列关：右侧入队 / 仅队头可出 ——
function enqueue() {
  if (won.value || lives.value <= 0) return
  if (!inbound.value.length) {
    msg.value = '没有待入队餐盘'
    return
  }
  queue.value.push(inbound.value.shift()!)
  addScore(5)
  msg.value = '已从右侧入队'
}

function clickQueuePlate(index: number) {
  if (won.value || lives.value <= 0) return
  if (index !== 0) {
    loseLife('只能从队头（最左侧）出餐！')
    return
  }
  const expect = nextExpected.value
  const v = queue.value[0]!
  if (v !== expect) {
    // 不消费餐盘，仅提示顺序错误，避免污染 output 导致本关永久不可通关
    loseLife(`顺序错了：该出 ${expect}，队头是 ${v}`)
    return
  }
  queue.value.shift()
  output.value.push(v)
  addScore(15)
  msg.value = `队头出餐 ${v} ✓`
  checkWin()
}

// —— 双栈 ——
function pourInToOut() {
  if (won.value || lives.value <= 0) return
  if (outStack.value.length) {
    loseLife('out 里还有盘子，不必倒入')
    return
  }
  if (!inStack.value.length) {
    msg.value = 'in 已空'
    return
  }
  while (inStack.value.length) outStack.value.push(inStack.value.pop()!)
  dualPoured.value = true
  addScore(10)
  msg.value = '已倒入 out，点击 out 栈顶出餐'
}

function clickOutStackTop() {
  if (won.value || lives.value <= 0) return
  if (!outStack.value.length) {
    if (inStack.value.length) {
      msg.value = 'out 为空，请先「倒入 out」'
    } else {
      msg.value = 'out 为空'
    }
    return
  }
  const v = outStack.value[outStack.value.length - 1]!
  const expect = nextExpected.value
  if (v !== expect) {
    // 不消费餐盘，仅提示顺序错误，避免污染 output 导致本关永久不可通关
    loseLife(`应对 ${expect}，栈顶是 ${v}`)
    return
  }
  outStack.value.pop()
  output.value.push(v)
  addScore(15)
  dualPoured.value = false
  msg.value = `出餐 ${v} ✓`
  checkWin()
}

// —— 括号：点击当前字符 ——
function clickParenAt(i: number) {
  if (won.value || lives.value <= 0) return
  if (i !== parenCursor.value) {
    loseLife('请按从左到右顺序点击括号')
    return
  }
  const ch = stream.value[i]!
  parenCursor.value++
  if ('([{'.includes(ch)) {
    parenStack.value.push(ch)
    addScore(5)
    msg.value = `左括号 ${ch} 入栈`
  } else {
    const map: Record<string, string> = { ')': '(', ']': '[', '}': '{' }
    const top = parenStack.value[parenStack.value.length - 1]
    if (top !== map[ch]) {
      // 不弹出栈顶，避免破坏匹配栈状态
      loseLife(`栈顶与 ${ch} 不匹配`)
      parenCursor.value--
      return
    }
    parenStack.value.pop()
    addScore(10)
    msg.value = `匹配 ${ch}，栈：${parenStack.value.join('') || '空'}`
  }
  if (parenCursor.value >= stream.value.length && parenStack.value.length === 0) {
    won.value = true
    msg.value = '括号全部匹配！'
    emit('cleared')
  }
}

// —— deque：点击要弹出的队尾下标 ——
const dequeWindow = computed(() => {
  const s = dequeWindowStart.value
  return dequeNums.slice(s, s + 3)
})

function clickDequePop(idxInWindow: number) {
  if (won.value || lives.value <= 0 || props.levelId !== 'deque') return
  const globalIdx = dequeWindowStart.value + idxInWindow
  if (dequeStep.value === 0) {
    // 新元素下标 3 值 -1，应弹出 <= -1 的队尾
    if (globalIdx !== 1) {
      loseLife('应弹出值 ≤ -1 的队尾下标（本步弹下标 1）')
      return
    }
    dequeIdxInDeque.value = [3]
    dequeWindowStart.value = 1
    dequeStep.value = 1
    addScore(20)
    msg.value = '正确！窗口右移，deque 现为 [3]'
    return
  }
  if (dequeStep.value >= 1) {
    won.value = true
    msg.value = '窗口最大值 5，通关！'
    emit('cleared')
  }
}

function advanceDeque() {
  if (dequeStep.value === 1) {
    dequeIdxInDeque.value = [4]
    dequeWindowStart.value = 2
    addScore(15)
    msg.value = '队头过期弹出，加入下标 4（值 5）'
    dequeStep.value = 2
  }
}

const canPour = computed(
  () => props.levelId === 'dual-stack' && !outStack.value.length && inStack.value.length > 0,
)

const stepIndex = computed(() => {
  if (won.value) return shellMeta.value?.stepCount ? shellMeta.value.stepCount - 1 : 2
  if (props.levelId === 'paren') return Math.min(parenCursor.value, 5)
  if (props.levelId === 'deque') return dequeStep.value
  return Math.min(output.value.length, 2)
})

const stateValues = computed(() => ({
  lives: `${lives.value} ❤️`,
  score: String(score.value),
  cursor: props.levelId === 'paren' ? String(parenCursor.value) : '—',
  stack: props.levelId === 'paren' ? String(parenStack.value.length) : '—',
  window: props.levelId === 'deque' ? dequeWindow.value.join(', ') : '—',
}))

const hintText = computed(() => msg.value || '按规则出餐')
const isFail = computed(() => lives.value <= 0 && !won.value)
</script>

<template>
  <GamePlayShell
    v-if="shellMeta"
    :meta="shellMeta"
    :hint="hintText"
    :fail="isFail"
    :won="won"
    :step-index="stepIndex"
    :state-values="stateValues"
    :action-log="actionLog"
    @reset="init"
  >
  <div class="canteen-game" :class="{ 'is-shake': shakeKey % 2 === 1 }" :key="'shake-' + shakeKey">
    <div class="hud hud--inline">
      <div class="hud-item">
        <span class="hud-label">生命</span>
        <span class="hearts">{{ '❤️'.repeat(lives) }}{{ '🖤'.repeat(Math.max(0, 3 - lives)) }}</span>
      </div>
      <div class="hud-item">
        <span class="hud-label">得分</span>
        <strong>{{ score }}</strong>
      </div>
      <el-button v-if="!won && lives <= 0" type="warning" size="small" @click="init">重置本关</el-button>
    </div>

    <div v-if="target.length" class="order-ticket">
      <span class="order-label">顾客订单</span>
      <div class="order-slots">
        <span
          v-for="(slot, i) in targetSlots"
          :key="i"
          class="order-plate"
          :class="{ 'is-done': slot.filled, 'is-next': slot.current }"
        >{{ slot.v }}</span>
      </div>
    </div>

    <!-- 栈关 -->
    <div v-if="levelId === 'stack'" class="canteen-board">
      <div class="board-col">
        <span class="col-title">待入栈（点击餐盘入栈）</span>
        <div class="conveyor">
          <button
            v-for="(x, i) in inbound"
            :key="'in' + i"
            type="button"
            class="plate plate--clickable"
            :disabled="won || lives <= 0"
            @click="pushToStack"
          >
            {{ x }}
          </button>
          <span v-if="!inbound.length" class="plate-empty">已取完</span>
        </div>
      </div>
      <div class="board-col">
        <span class="col-title">出餐栈（仅栈顶可点）</span>
        <div class="plate-stack">
          <button
            v-for="(x, i) in stack"
            :key="'s' + i"
            type="button"
            class="plate plate--clickable"
            :class="{
              'is-top': i === stack.length - 1,
              'is-locked': i !== stack.length - 1,
            }"
            :disabled="won || lives <= 0"
            @click="clickStackPlate(i)"
          >
            {{ x }}
            <span v-if="i === stack.length - 1" class="plate-tag">栈顶</span>
          </button>
          <span v-if="!stack.length" class="plate-empty">栈空</span>
        </div>
      </div>
      <div class="board-col">
        <span class="col-title">出餐口</span>
        <div class="output-row">
          <span v-for="(x, i) in output" :key="i" class="plate plate--out">{{ x }}</span>
          <span v-if="!output.length" class="plate-empty">空</span>
        </div>
      </div>
    </div>

    <!-- 队列关 -->
    <div v-else-if="levelId === 'queue'" class="canteen-board">
      <div class="board-col">
        <span class="col-title">待入队（点击从右侧入队）</span>
        <div class="conveyor">
          <button
            v-for="(x, i) in inbound"
            :key="i"
            type="button"
            class="plate plate--clickable"
            :disabled="won || lives <= 0"
            @click="enqueue"
          >
            {{ x }} →
          </button>
        </div>
      </div>
      <div class="board-col board-col--wide">
        <span class="col-title">队列（仅队头可点）</span>
        <div class="conveyor queue-line">
          <button
            v-for="(x, i) in queue"
            :key="i"
            type="button"
            class="plate plate--clickable"
            :class="{ 'is-head': i === 0, 'is-locked': i !== 0 }"
            :disabled="won || lives <= 0"
            @click="clickQueuePlate(i)"
          >
            {{ x }}
            <small v-if="i === 0">队头</small>
          </button>
          <span v-if="!queue.length" class="plate-empty">队列空</span>
        </div>
      </div>
      <div class="board-col">
        <span class="col-title">出餐口</span>
        <div class="output-row">
          <span v-for="(x, i) in output" :key="i" class="plate plate--out">{{ x }}</span>
        </div>
      </div>
    </div>

    <!-- 双栈 -->
    <div v-else-if="levelId === 'dual-stack'" class="canteen-board canteen-board--triple">
      <div class="board-col">
        <span class="col-title">入队栈 in</span>
        <div class="plate-stack plate-stack--short">
          <span v-for="(x, i) in inStack" :key="i" class="plate">{{ x }}</span>
          <span v-if="!inStack.length" class="plate-empty">空</span>
        </div>
        <button
          type="button"
          class="action-chip"
          :class="{ 'is-ready': canPour }"
          :disabled="!canPour || won || lives <= 0"
          @click="pourInToOut"
        >
          倒入 out
        </button>
      </div>
      <div class="board-col">
        <span class="col-title">出队栈 out（点栈顶）</span>
        <div class="plate-stack plate-stack--short">
          <button
            v-for="(x, i) in outStack"
            :key="i"
            type="button"
            class="plate plate--clickable"
            :class="{ 'is-top': i === outStack.length - 1 }"
            :disabled="won || lives <= 0"
            @click="clickOutStackTop"
          >
            {{ x }}
          </button>
          <span v-if="!outStack.length" class="plate-empty">空</span>
        </div>
      </div>
      <div class="board-col">
        <span class="col-title">出餐口</span>
        <div class="output-row">
          <span v-for="(x, i) in output" :key="i" class="plate plate--out">{{ x }}</span>
        </div>
      </div>
    </div>

    <!-- 括号 -->
    <div v-else-if="levelId === 'paren'" class="canteen-board paren-board">
      <div class="board-col board-col--wide">
        <span class="col-title">点击当前高亮括号</span>
        <div class="conveyor paren-belt">
          <button
            v-for="(c, i) in stream"
            :key="i"
            type="button"
            class="plate plate--char plate--clickable"
            :class="{
              'is-done': i < parenCursor,
              'is-current': i === parenCursor,
              'is-locked': i > parenCursor,
            }"
            :disabled="won || lives <= 0 || i !== parenCursor"
            @click="clickParenAt(i)"
          >
            {{ c }}
          </button>
        </div>
        <div class="match-stack-viz">
          <span class="col-title">匹配栈</span>
          <div class="stack-chars">
            <span v-for="(c, i) in parenStack" :key="i" class="plate plate--char">{{ c }}</span>
            <span v-if="!parenStack.length" class="plate-empty">空</span>
          </div>
        </div>
      </div>
    </div>

    <!-- deque -->
    <div v-else-if="levelId === 'deque'" class="canteen-board deque-board">
      <span class="col-title">数组下标与值（窗口宽度 3）</span>
      <div class="deque-array">
        <div
          v-for="(n, i) in dequeNums"
          :key="i"
          class="deque-bar-wrap"
          :class="{ 'in-window': i >= dequeWindowStart && i < dequeWindowStart + 3 }"
        >
          <div class="deque-bar" :style="{ height: `${Math.max(12, (n + 3) * 14)}px` }" />
          <span class="deque-idx">{{ i }}</span>
          <span class="deque-val">{{ n }}</span>
        </div>
      </div>
      <p class="deque-caption">deque 存下标：{{ dequeIdxInDeque.join(', ') || '空' }}</p>
      <p class="deque-caption">当前窗口值：{{ dequeWindow.join(', ') }}</p>
      <div v-if="dequeStep === 0" class="deque-actions">
        <span class="hint">新元素进入窗口：下标 3 值为 -1，谁该从 deque 队尾弹出？</span>
        <button
          v-for="(n, wi) in dequeWindow"
          :key="wi"
          type="button"
          class="plate plate--clickable"
          @click="clickDequePop(wi)"
        >
          弹下标 {{ dequeWindowStart + wi }}（{{ n }}）
        </button>
      </div>
      <div v-else class="deque-actions">
        <button type="button" class="action-chip" @click="advanceDeque">队头过期，加入下标 4</button>
        <button type="button" class="action-chip" @click="clickDequePop(0)">确认窗口最大值 5</button>
      </div>
    </div>

  </div>
  </GamePlayShell>
</template>

<style scoped>
.canteen-game {
  width: 100%;
}

.canteen-game.is-shake {
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-6px);
  }
  75% {
    transform: translateX(6px);
  }
}

.hud--inline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-bottom: 14px;
  padding: 10px 14px;
  border-radius: 10px;
  background: color-mix(in srgb, #525c8a 8%, var(--alp-bg-soft-block));
  border: 1px solid var(--alp-color-border);
}

.hud {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.hud-label {
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-right: 6px;
}

.hearts {
  font-size: 14px;
  letter-spacing: 2px;
}

.order-ticket {
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: 10px;
  background: color-mix(in srgb, #9c8540 10%, transparent);
  border: 1px solid color-mix(in srgb, #9c8540 35%, transparent);
}

.order-label {
  display: block;
  font-size: 12px;
  color: var(--alp-color-muted);
  margin-bottom: 8px;
}

.order-slots {
  display: flex;
  gap: 10px;
}

.order-plate {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  font-weight: 700;
  border-radius: 8px;
  border: 2px dashed var(--alp-color-border);
  color: var(--alp-color-muted);
}

.order-plate.is-next {
  border-color: #9c8540;
  color: #9c8540;
  box-shadow: 0 0 12px color-mix(in srgb, #9c8540 40%, transparent);
}

.order-plate.is-done {
  border-color: #4a8a5e;
  background: color-mix(in srgb, #4a8a5e 20%, transparent);
  color: #8ab896;
}

.canteen-board {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  min-height: 240px;
  padding: 20px;
  border-radius: 12px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.board-col {
  flex: 1;
  min-width: 150px;
}

.board-col--wide {
  flex: 2;
  min-width: 280px;
}

.col-title {
  display: block;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.plate-stack {
  display: flex;
  flex-direction: column-reverse;
  align-items: center;
  gap: 8px;
  min-height: 160px;
  padding: 12px;
  border-radius: 10px;
  background: color-mix(in srgb, #0f172a 60%, transparent);
  border: 2px solid var(--alp-color-border);
}

.plate-stack--short {
  min-height: 100px;
}

.plate {
  position: relative;
  min-width: 52px;
  padding: 10px 16px;
  border-radius: 10px;
  font-size: 1.15rem;
  font-weight: 700;
  color: #f8fafc;
  background: #525c8a;
  border: 2px solid color-mix(in srgb, #a5b4fc 50%, transparent);
  box-shadow: 0 4px 10px rgba(82, 92, 138, 0.3);
}

button.plate {
  cursor: pointer;
  font-family: inherit;
  transition: transform 0.12s, box-shadow 0.12s, filter var(--alp-transition-fast);
}

button.plate:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: var(--alp-shadow-btn-hover);
  filter: brightness(1.08);
}

button.plate:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.plate.is-top {
  outline: 3px solid #9c8540;
  outline-offset: 2px;
}

.plate.is-locked {
  opacity: 0.45;
  filter: grayscale(0.4);
}

.plate.is-head {
  outline: 3px solid #9c8540;
}

.plate.is-current {
  outline: 3px solid #3a8a9e;
  animation: pulse 1s ease infinite;
}

.plate.is-done {
  opacity: 0.35;
}

@keyframes pulse {
  50% {
    box-shadow: 0 0 16px rgba(58, 138, 158, 0.6);
  }
}

.plate-tag {
  position: absolute;
  top: -6px;
  right: -6px;
  padding: 2px 5px;
  font-size: 9px;
  font-weight: 700;
  border-radius: 4px;
  background: #9c8540;
  color: #1e293b;
}

.plate--out {
  background: #4a8a5e;
}

.plate--char {
  min-width: 44px;
}

.plate-empty {
  font-size: 13px;
  color: var(--alp-color-muted);
}

.conveyor {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  min-height: 72px;
  padding: 12px;
  border-radius: 10px;
  background: color-mix(in srgb, #0f172a 45%, transparent);
}

.queue-line {
  min-height: 64px;
}

.output-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 56px;
  align-items: center;
}

.action-chip {
  margin-top: 10px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-text);
  cursor: pointer;
}

.action-chip.is-ready {
  border-color: #3a8a9e;
  background: color-mix(in srgb, #3a8a9e 15%, transparent);
}

.action-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.match-stack-viz {
  margin-top: 16px;
}

.stack-chars {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.deque-array {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin: 16px 0;
  padding: 16px;
  border-radius: 10px;
  background: color-mix(in srgb, #0f172a 50%, transparent);
}

.deque-bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  opacity: 0.35;
  padding: 4px;
  border-radius: 8px;
}

.deque-bar-wrap.in-window {
  opacity: 1;
  background: color-mix(in srgb, #3a8a9e 12%, transparent);
  outline: 2px solid color-mix(in srgb, #3a8a9e 40%, transparent);
}

.deque-bar {
  width: 28px;
  border-radius: 4px 4px 0 0;
  background: #6b7a9e;
}

.deque-idx,
.deque-val {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.deque-val {
  font-weight: 700;
  color: var(--alp-color-text);
}

.deque-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.deque-actions .hint {
  width: 100%;
  font-size: 13px;
  color: var(--alp-color-muted);
  margin: 0 0 8px;
}

.feedback {
  margin: 0;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.55;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border-left: 3px solid var(--alp-color-primary);
  color: var(--alp-color-text);
}

.feedback.is-win {
  border-left-color: #4a8a5e;
  background: color-mix(in srgb, #4a8a5e 12%, transparent);
  color: #8ab896;
}

.feedback.is-error {
  border-left-color: #9e5a5a;
  color: #fca5a5;
}
</style>
