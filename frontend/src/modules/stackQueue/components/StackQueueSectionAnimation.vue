<script setup lang="ts">
import { computed, ref, toRef, watch } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

function maxStepForSection(id: string) {
  const m: Record<string, number> = {
    theory: 0,
    'queue-by-stacks': 4,
    'stack-by-queues': 3,
    'valid-parentheses': 4,
    'remove-adjacent': 4,
    'eval-rpn': 4,
    'sliding-window-max': 4,
    'top-k-frequent': 3,
    summary: 3,
  }
  return m[id] ?? 3
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } = useSteppedAnimation({
  sectionId: sectionIdRef,
  maxStepForSection,
})

/** 理论基础：栈 / 队列 / deque 三套独立分步动画 */
const theoryStackId = ref('sq-theory-stack')
const theoryQueueId = ref('sq-theory-queue')
const theoryDequeId = ref('sq-theory-deque')

const stackTheory = useSteppedAnimation({
  sectionId: theoryStackId,
  maxStepForSection: () => 3,
  stepMs: 850,
})
const queueTheory = useSteppedAnimation({
  sectionId: theoryQueueId,
  maxStepForSection: () => 2,
  stepMs: 950,
})
const dequeTheory = useSteppedAnimation({
  sectionId: theoryDequeId,
  maxStepForSection: () => 1,
  stepMs: 1100,
})

const STACK_HINTS = [
  'push 1 压入栈顶',
  'push 2，新元素总在栈顶',
  'push 3 后栈顶为 3',
  'pop 弹出 3：后进先出 (LIFO)',
]
const QUEUE_HINTS = [
  '队尾 push、队头在左',
  '队头 pop 出 1，剩余前移 (FIFO)',
  '队尾继续 push 新元素',
]
const DEQUE_HINTS = ['头尾两端均可 push / pop', '左端 pop 或右端 push 示意']

watch(
  () => props.sectionId,
  (id) => {
    if (id !== 'theory') return
    stackTheory.resetAnim()
    queueTheory.resetAnim()
    dequeTheory.resetAnim()
  },
)

const caption = computed(() => {
  const m: Record<string, string> = {
    theory: '栈 LIFO · 队列 FIFO · deque 两端操作',
    'queue-by-stacks': '232：入队栈 in · 出队时倒入 out 栈',
    'stack-by-queues': '225：单队列轮转使新元素到队头',
    'valid-parentheses': '20：左括号入栈，右括号与栈顶匹配',
    'remove-adjacent': '1047：相同字符栈顶则消除',
    'eval-rpn': '150：数字入栈，运算符弹出两数再入栈',
    'sliding-window-max': '239：单调递减 deque 存下标',
    'top-k-frequent': '347：频次统计 + 小顶堆',
    summary: '栈与队列篇：实现 · 括号 · 单调队列',
  }
  return m[props.sectionId] ?? '栈与队列示意'
})

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'queue-by-stacks') {
    return ['push 直接压入 in 栈', 'pop 时若 out 空，把 in 全部倒入 out', '从 out 栈顶弹出队头', '均摊 O(1)：每个元素最多倒腾两次', ''][i] ?? ''
  }
  if (s === 'valid-parentheses') {
    return [
      '读 ( → 左括号入栈',
      '读 [ → 入栈，栈内 (、[',
      '读 ] → 与栈顶 [ 匹配并 pop',
      '读 ) → 与栈顶 ( 匹配并 pop',
      '遍历结束：栈须为空',
    ][i] ?? ''
  }
  if (s === 'sliding-window-max') {
    return [
      '窗口 [1,3,-1]：deque 存下标 1（值 3 最大）',
      '加入下标 3（-3）：队尾弹出值 ≤ -3 的下标',
      '窗口右移：队头下标 1 过期，从队头弹出',
      '加入 5：清空队尾较小值，队头下标 4 → 窗口最大值 5',
      '',
    ][i] ?? ''
  }
  if (s === 'eval-rpn') {
    return [
      '读 2：数字直接入栈',
      '读 1：再入栈，栈顶为 1',
      '读 +：弹出 1、2，计算 2+1=3 再入栈',
      '读 3 入栈；读 *：弹出 3、3，得 9',
      '遍历结束，栈中唯一元素即答案',
    ][i] ?? ''
  }
  if (s === 'remove-adjacent') {
    return [
      '读 a：栈空，直接 push',
      '再读 a：与栈顶相同，pop 消除这一对',
      '读 b：push 入栈',
      '栈中拼接得结果 "b"',
      '',
    ][i] ?? ''
  }
  if (s === 'stack-by-queues') {
    return [
      'push(1)：新元素从队尾入队',
      'push(2)：先入队 [1,2]',
      '轮转：队头 1 出队并回到队尾 → [2,1]',
      '队头即栈顶（top），pop 从队头出',
      '',
    ][i] ?? ''
  }
  if (s === 'top-k-frequent') {
    return [
      '遍历 nums，map 统计各元素频次',
      '维护大小 k=2 的小顶堆（按频次）',
      '堆中保留频次最高的 k 个 → [1, 2]',
      '',
    ][i] ?? ''
  }
  if (s === 'summary') {
    return [
      '实现互模拟：232 双栈队列 · 225 单队列轮转栈',
      '栈经典：20 括号 · 1047 相邻消除 · 150 表达式',
      '进阶：239 单调队列 · 347 频次 + 小顶堆',
      '',
    ][i] ?? ''
  }
  return ['观察数据进出方向', '对照题目选择结构', '模拟一遍 push/pop', ''][i] ?? ''
})

/** 225：单队列模拟栈 */
const STACK_BY_Q_FRAMES = [
  { cells: ['1'], pushVal: '1', rotateVal: '', op: 'push' as const },
  { cells: ['1', '2'], pushVal: '2', rotateVal: '', op: 'push' as const },
  { cells: ['2', '1'], pushVal: '', rotateVal: '1', op: 'rotate' as const },
  { cells: ['2', '1'], pushVal: '', rotateVal: '', op: 'top' as const },
]

const stackByQFrame = computed(() => {
  if (props.sectionId !== 'stack-by-queues') return null
  return STACK_BY_Q_FRAMES[Math.min(step.value, STACK_BY_Q_FRAMES.length - 1)] ?? null
})

/** 1047：aab → b */
const ADJ_INPUT = ['a', 'a', 'b'] as const
const ADJ_STACK_FRAMES: string[][] = [['a'], [], ['b'], ['b']]

const adjScanIndex = computed(() => {
  if (props.sectionId !== 'remove-adjacent') return 0
  return Math.min(step.value, ADJ_INPUT.length)
})

const adjStackCells = computed(() => {
  if (props.sectionId !== 'remove-adjacent') return []
  return ADJ_STACK_FRAMES[Math.min(step.value, ADJ_STACK_FRAMES.length - 1)] ?? []
})

const adjEliminate = computed(
  () => props.sectionId === 'remove-adjacent' && step.value === 1,
)

/** 150：逆波兰 2 1 + 3 * */
const RPN_TOKENS = ['2', '1', '+', '3', '*'] as const
const RPN_STACK_FRAMES: string[][] = [['2'], ['2', '1'], ['3'], ['3', '3'], ['9']]
const RPN_POP_PAIR: ([string, string] | null)[] = [null, null, ['1', '2'], null, ['3', '3']]

const rpnScanIndex = computed(() => {
  if (props.sectionId !== 'eval-rpn') return 0
  const map = [0, 1, 2, 3, 4, 4]
  return map[Math.min(step.value, map.length - 1)] ?? 0
})

const rpnStackCells = computed(() => {
  if (props.sectionId !== 'eval-rpn') return []
  return RPN_STACK_FRAMES[Math.min(step.value, RPN_STACK_FRAMES.length - 1)] ?? []
})

const rpnPopPair = computed(() => {
  if (props.sectionId !== 'eval-rpn') return null
  return RPN_POP_PAIR[Math.min(step.value, RPN_POP_PAIR.length - 1)] ?? null
})

const rpnIsOp = computed(
  () => props.sectionId === 'eval-rpn' && step.value === 2,
)

/** 239：滑动窗口最大值 k=3 */
const SW_NUMS = [
  { v: '1', i: 0 },
  { v: '3', i: 1 },
  { v: '-1', i: 2 },
  { v: '-3', i: 3 },
  { v: '5', i: 4 },
] as const

const swFrame = computed(() => {
  if (props.sectionId !== 'sliding-window-max') return null
  const s = step.value
  const frames = [
    { win: [0, 1, 2], deque: [1], max: '3', popBack: [] as number[], popFront: -1 },
    { win: [1, 2, 3], deque: [1, 2, 3], max: '3', popBack: [] as number[], popFront: -1 },
    { win: [2, 3, 4], deque: [4], max: '5', popBack: [2, 3], popFront: 1 },
    { win: [2, 3, 4], deque: [4], max: '5', popBack: [], popFront: -1 },
  ]
  return frames[Math.min(s, frames.length - 1)] ?? frames[0]
})

/** 347：前 K 高频 k=2 */
const FREQ_ITEMS = [
  { k: '1', f: 3 },
  { k: '2', f: 2 },
  { k: '3', f: 1 },
] as const

const topKFrame = computed(() => {
  if (props.sectionId !== 'top-k-frequent') return null
  const s = step.value
  return {
    mapHot: s >= 0,
    heapCells: s >= 1 ? ['2×2', '1×3'] : [] as string[],
    heapHot: s >= 1,
    result: s >= 2 ? ['1', '2'] : [] as string[],
  }
})

const SUMMARY_GROUPS = [
  { title: '实现互模拟', tags: ['232 双栈', '225 轮转'], color: 'blue' as const },
  { title: '栈应用', tags: ['20 括号', '1047 消除', '150 RPN'], color: 'cyan' as const },
  { title: '队列 · 堆', tags: ['239 单调队列', '347 Top-K'], color: 'violet' as const },
]

const inStack = computed(() => {
  if (props.sectionId !== 'queue-by-stacks') return []
  const frames = [['1', '2'], ['1', '2', '3'], [], ['3', '2'], ['2']]
  return frames[Math.min(step.value, frames.length - 1)] ?? []
})
const outStack = computed(() => {
  if (props.sectionId !== 'queue-by-stacks') return []
  const frames = [[], [], ['1', '2'], ['1', '2'], ['1']]
  return frames[Math.min(step.value, frames.length - 1)] ?? []
})

function stackCellsForStep(s: number) {
  const frames = [['1'], ['1', '2'], ['1', '2', '3'], ['1', '2']]
  return frames[Math.min(s, frames.length - 1)] ?? []
}

function stackPopForStep(s: number) {
  return s === 3 ? '3' : ''
}

function queueCellsForStep(s: number) {
  const frames = [['1', '2', '3'], ['2', '3'], ['2', '3', '4']]
  return frames[Math.min(s, frames.length - 1)] ?? []
}

function queuePopForStep(s: number) {
  return s === 1
}

const stackStep = computed(() => stackTheory.step.value)
const queueStep = computed(() => queueTheory.step.value)
const dequeStep = computed(() => dequeTheory.step.value)

const theoryStackCells = computed(() =>
  props.sectionId === 'theory' ? stackCellsForStep(stackStep.value) : [],
)
const theoryStackPop = computed(() =>
  props.sectionId === 'theory' ? stackPopForStep(stackStep.value) : '',
)
const theoryQueueCells = computed(() =>
  props.sectionId === 'theory' ? queueCellsForStep(queueStep.value) : [],
)
const theoryQueuePop = computed(() =>
  props.sectionId === 'theory' ? queuePopForStep(queueStep.value) : false,
)
const theoryDequeCells = computed(() => ['A', 'B', 'C'])
const theoryDequeHotEnds = computed(() => dequeStep.value === 1)

const PAREN_INPUT = ['(', '[', ']', ')'] as const
const PAREN_STACK_FRAMES: string[][] = [['('], ['(', '['], ['('], [], []]

const parenScanIndex = computed(() => {
  if (props.sectionId !== 'valid-parentheses') return 0
  if (step.value >= 4) return PAREN_INPUT.length
  return step.value
})

const parenStackCells = computed(() => {
  if (props.sectionId !== 'valid-parentheses') return []
  return PAREN_STACK_FRAMES[Math.min(step.value, PAREN_STACK_FRAMES.length - 1)] ?? []
})

const parenOpLabel = computed(() => {
  if (props.sectionId !== 'valid-parentheses') return ''
  if (step.value <= 1) return 'push ↑'
  if (step.value <= 3) return 'pop ↓'
  return '完成 ✓'
})

const parenOpIsPop = computed(
  () => props.sectionId === 'valid-parentheses' && step.value >= 2 && step.value <= 3,
)
</script>

<template>
  <div v-if="sectionId === 'theory'" class="sq-theory-trio" role="img" :aria-label="caption">
    <p class="sq-theory-trio-hint">三种结构独立演示 · 可分别暂停或步进</p>

    <div class="sq-theory-grid">
      <article class="sq-theory-card sq-theory-card--stack">
        <header class="sq-theory-card-head">
          <span class="struct-tag">栈 · LIFO</span>
          <span class="struct-badge">后进先出</span>
        </header>
        <div class="viz-stage sq-viz-stage viz-stage--stack">
          <div class="stack-well stack-well--horizontal" aria-hidden="true">
            <div class="stack-axis-h">
              <span class="well-cap well-cap--left">栈底</span>
              <span class="stack-axis-arrow" aria-hidden="true">→</span>
              <span class="well-cap well-cap--right">栈顶</span>
            </div>
            <div class="stack-well-body stack-well-body--horizontal alp-hstack-body alp-hslots-3">
              <span
                v-for="(v, i) in theoryStackCells"
                :key="'st' + v + i"
                class="viz-cell"
                :class="{ 'viz-cell--hot': i === theoryStackCells.length - 1 }"
              >{{ v }}</span>
              <span v-if="theoryStackPop" class="viz-cell viz-cell--float stack-float-pop">{{ theoryStackPop }}</span>
            </div>
          </div>
          <span
            class="op-badge learn-viz-op"
            :class="stackStep < 3 ? 'op-badge--push learn-viz-op--push-h' : 'op-badge--pop learn-viz-op--pop-h'"
          >
            {{ stackStep < 3 ? 'push →' : 'pop ←' }}
          </span>
        </div>
        <footer class="sq-card-foot">
          <p class="sq-mini-hint" aria-live="polite">{{ STACK_HINTS[stackStep] }}</p>
          <div class="sq-mini-toolbar" role="group" aria-label="栈动画控制">
            <el-button size="small" round @click="stackTheory.togglePlay">
              {{ stackTheory.playing ? '暂停' : '播放' }}
            </el-button>
            <el-button size="small" round @click="stackTheory.manualNext">下一步</el-button>
          </div>
        </footer>
      </article>

      <article class="sq-theory-card sq-theory-card--queue">
        <header class="sq-theory-card-head">
          <span class="struct-tag struct-tag--queue">队列 · FIFO</span>
          <span class="struct-badge struct-badge--queue">先进先出</span>
        </header>
        <div class="viz-stage sq-viz-stage viz-stage--queue">
          <div class="queue-well">
            <div class="queue-axis">
              <div class="queue-axis-labels">
                <span class="axis-tag axis-tag--front">队头 pop</span>
                <span class="axis-tag axis-tag--back">队尾 push</span>
              </div>
              <span class="queue-axis-arrow" aria-hidden="true">→</span>
            </div>
            <div class="queue-lane-wrap" :class="{ 'queue-lane-wrap--pop': theoryQueuePop }">
              <div class="queue-lane">
                <span
                v-for="(v, i) in theoryQueueCells"
                :key="'q' + v + i"
                class="viz-cell"
                :class="{
                  'viz-cell--hot': i === 0,
                  'viz-cell--dim': theoryQueuePop && i === 0,
                  'viz-cell--link': i < theoryQueueCells.length - 1,
                }"
              >{{ v }}</span>
              </div>
              <span v-if="theoryQueuePop" class="viz-cell viz-cell--ghost queue-ghost">1</span>
            </div>
          </div>
        </div>
        <footer class="sq-card-foot">
          <p class="sq-mini-hint" aria-live="polite">{{ QUEUE_HINTS[queueStep] }}</p>
          <div class="sq-mini-toolbar" role="group" aria-label="队列动画控制">
            <el-button size="small" round @click="queueTheory.togglePlay">
              {{ queueTheory.playing ? '暂停' : '播放' }}
            </el-button>
            <el-button size="small" round @click="queueTheory.manualNext">下一步</el-button>
          </div>
        </footer>
      </article>

      <article class="sq-theory-card sq-theory-card--deque">
        <header class="sq-theory-card-head">
          <span class="struct-tag struct-tag--deque">deque · 双端</span>
          <span class="struct-badge struct-badge--deque">头尾皆可</span>
        </header>
        <div class="viz-stage sq-viz-stage viz-stage--deque">
          <div class="deque-well" :class="{ 'deque-well--active': theoryDequeHotEnds }">
            <div class="deque-port deque-port--left">
              <span class="port-label">左端</span>
              <span class="port-ops">入/出</span>
            </div>
            <div class="deque-lane">
              <span
                v-for="(v, i) in theoryDequeCells"
                :key="'d' + v"
                class="viz-cell"
                :class="{
                  'viz-cell--hot': i === 0 || i === theoryDequeCells.length - 1,
                  'viz-cell--link': i < theoryDequeCells.length - 1,
                }"
              >{{ v }}</span>
            </div>
            <div class="deque-port deque-port--right">
              <span class="port-label">右端</span>
              <span class="port-ops">入/出</span>
            </div>
          </div>
        </div>
        <footer class="sq-card-foot">
          <p class="sq-mini-hint" aria-live="polite">{{ DEQUE_HINTS[dequeStep] }}</p>
          <div class="sq-mini-toolbar" role="group" aria-label="双端队列动画控制">
            <el-button size="small" round @click="dequeTheory.togglePlay">
              {{ dequeTheory.playing ? '暂停' : '播放' }}
            </el-button>
            <el-button size="small" round @click="dequeTheory.manualNext">下一步</el-button>
          </div>
        </footer>
      </article>
    </div>
  </div>

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
    <div v-if="sectionId === 'queue-by-stacks'" class="learn-viz-grid learn-viz-grid--2">
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag">入队栈 in</span>
          <span class="learn-viz-badge">push</span>
        </header>
        <div class="learn-viz-stage">
          <div class="learn-stack-well learn-stack-well--horizontal">
            <div class="learn-stack-axis-h">
              <span class="learn-well-cap learn-well-cap--left">栈底</span>
              <span class="learn-stack-axis-arrow" aria-hidden="true">→</span>
              <span class="learn-well-cap learn-well-cap--right">栈顶</span>
            </div>
            <div class="learn-stack-body learn-stack-body--horizontal alp-hstack-body alp-hslots-4">
              <span
                v-for="(v, i) in inStack"
                :key="'in' + v + i"
                class="learn-viz-cell"
                :class="{ 'learn-viz-cell--hot': step === 0 && i === inStack.length - 1 }"
              >{{ v }}</span>
            </div>
          </div>
          <span v-if="step === 0 && inStack.length" class="learn-viz-op learn-viz-op--push">push</span>
        </div>
      </article>

      <span class="learn-viz-transfer" aria-hidden="true">⇄</span>

      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag learn-viz-tag--green">出队栈 out</span>
          <span class="learn-viz-badge learn-viz-badge--green">pop</span>
        </header>
        <div class="learn-viz-stage">
          <div class="learn-stack-well learn-stack-well--green learn-stack-well--horizontal">
            <div class="learn-stack-axis-h">
              <span class="learn-well-cap learn-well-cap--left">栈底</span>
              <span class="learn-stack-axis-arrow" aria-hidden="true">→</span>
              <span class="learn-well-cap learn-well-cap--right">栈顶</span>
            </div>
            <div class="learn-stack-body learn-stack-body--horizontal alp-hstack-body alp-hslots-4">
              <span
                v-for="(v, i) in outStack"
                :key="'out' + v + i"
                class="learn-viz-cell learn-viz-cell--hot"
              >{{ v }}</span>
            </div>
          </div>
          <span v-if="step >= 2 && outStack.length" class="learn-viz-op learn-viz-op--pop">pop</span>
        </div>
      </article>
    </div>

    <div v-else-if="sectionId === 'valid-parentheses'" class="learn-viz-panel sq-paren-viz">
      <div class="sq-paren-scan">
        <span class="sq-paren-scan-label">输入 s</span>
        <div class="sq-paren-chars" aria-label="括号字符串">
          <span
            v-for="(ch, i) in PAREN_INPUT"
            :key="i"
            class="learn-viz-cell sq-paren-char"
            :class="{
              'learn-viz-cell--hot': i === parenScanIndex && step < 4,
              'learn-viz-cell--dim': i < parenScanIndex || step >= 4,
            }"
          >{{ ch }}</span>
        </div>
        <span v-if="parenScanIndex < PAREN_INPUT.length" class="sq-paren-cursor" aria-hidden="true">▲</span>
      </div>

      <span class="sq-paren-flow" aria-hidden="true">↓</span>

      <div class="sq-paren-stack-wrap">
        <span class="sq-paren-stack-label">栈</span>
        <div class="learn-stack-well sq-paren-stack">
          <div class="learn-well-cap learn-well-cap--top">栈顶 ▲</div>
          <div class="learn-stack-body alp-vstack-body alp-vslots-4">
            <span
              v-for="(v, i) in parenStackCells"
              :key="'p' + v + i"
              class="learn-viz-cell"
              :class="{
                'learn-viz-cell--hot': i === parenStackCells.length - 1 && step < 4,
                'learn-viz-cell--dim': parenOpIsPop && i === parenStackCells.length - 1,
              }"
            >{{ v }}</span>
          </div>
          <div class="learn-well-cap learn-well-cap--bottom">栈底</div>
        </div>
        <span
          class="learn-viz-op sq-paren-op"
          :class="parenOpIsPop ? 'learn-viz-op--pop' : 'learn-viz-op--push'"
        >{{ parenOpLabel }}</span>
      </div>
    </div>

    <!-- 225 用队列实现栈 -->
    <div v-else-if="sectionId === 'stack-by-queues' && stackByQFrame" class="learn-viz-panel sq-sbq-viz">
      <div class="sq-sbq-op-row">
        <span
          class="learn-viz-op"
          :class="{
            'learn-viz-op--push': stackByQFrame.op === 'push',
            'learn-viz-op--pop': stackByQFrame.op === 'top',
          }"
        >
          {{ stackByQFrame.op === 'push' ? 'push' : stackByQFrame.op === 'rotate' ? '轮转' : '栈顶' }}
        </span>
        <span v-if="stackByQFrame.pushVal" class="sq-sbq-incoming">
          入队 <strong>{{ stackByQFrame.pushVal }}</strong>
        </span>
      </div>
      <div class="learn-queue-well sq-sbq-queue">
        <div class="sq-queue-axis">
          <span class="sq-axis-tag sq-axis-tag--front">队头 = 栈顶 pop</span>
          <span class="sq-queue-axis-arrow" aria-hidden="true">→</span>
          <span class="sq-axis-tag sq-axis-tag--back">队尾 push</span>
        </div>
        <div
          class="sq-queue-lane-wrap"
          :class="{ 'sq-queue-lane-wrap--rotate': !!stackByQFrame.rotateVal }"
        >
          <div class="sq-queue-lane">
            <span
              v-for="(v, i) in stackByQFrame.cells"
              :key="'sq' + v + i"
              class="learn-viz-cell"
              :class="{
                'learn-viz-cell--stack-top': i === 0 && stackByQFrame.op === 'top',
                'learn-viz-cell--push-new': i === stackByQFrame.cells.length - 1 && stackByQFrame.op === 'push',
                'learn-viz-cell--dim': !!stackByQFrame.rotateVal && i === 0,
                'learn-viz-cell--link': i < stackByQFrame.cells.length - 1,
              }"
            >{{ v }}</span>
          </div>
          <span
            v-if="stackByQFrame.rotateVal"
            class="learn-viz-cell learn-viz-cell--ghost sq-sbq-rotate-ghost"
          >{{ stackByQFrame.rotateVal }}</span>
        </div>
        <p v-if="stackByQFrame.rotateVal" class="sq-sbq-rotate-hint" aria-hidden="true">
          队头出队 → 队尾入队（重复 size−1 次）
        </p>
      </div>
    </div>

    <!-- 1047 删除相邻重复 -->
    <div v-else-if="sectionId === 'remove-adjacent'" class="learn-viz-panel sq-adj-viz">
      <div class="sq-paren-scan">
        <span class="sq-paren-scan-label">输入 s = "aab"</span>
        <div class="sq-paren-chars">
          <span
            v-for="(ch, i) in ADJ_INPUT"
            :key="i"
            class="learn-viz-cell sq-paren-char"
            :class="{
              'learn-viz-cell--hot': i === adjScanIndex && step < 4,
              'learn-viz-cell--dim': i < adjScanIndex,
              'learn-viz-cell--ghost': adjEliminate && i === 1,
            }"
          >{{ ch }}</span>
        </div>
        <span v-if="adjScanIndex < ADJ_INPUT.length && step < 4" class="sq-paren-cursor" aria-hidden="true">▲</span>
      </div>
      <span class="sq-paren-flow" aria-hidden="true">↓</span>
      <div class="sq-paren-stack-wrap">
        <span class="sq-paren-stack-label">字符栈</span>
        <div class="learn-stack-well sq-paren-stack">
          <div class="learn-well-cap learn-well-cap--top">栈顶 ▲</div>
          <div class="learn-stack-body alp-vstack-body alp-vslots-4">
            <span
              v-for="(v, i) in adjStackCells"
              :key="'adj' + v + i"
              class="learn-viz-cell"
              :class="{
                'learn-viz-cell--hot': i === adjStackCells.length - 1 && !adjEliminate,
                'learn-viz-cell--dim': adjEliminate && i === adjStackCells.length - 1,
              }"
            >{{ v }}</span>
          </div>
          <div class="learn-well-cap learn-well-cap--bottom">栈底</div>
        </div>
        <span v-if="adjEliminate" class="learn-viz-op learn-viz-op--pop sq-adj-pop">相同 → pop</span>
        <p v-if="step >= 3" class="sq-adj-result">结果：<strong>b</strong></p>
      </div>
    </div>

    <!-- 150 逆波兰表达式 -->
    <div v-else-if="sectionId === 'eval-rpn'" class="learn-viz-panel sq-rpn-viz">
      <div class="sq-paren-scan">
        <span class="sq-paren-scan-label">tokens</span>
        <div class="sq-paren-chars">
          <span
            v-for="(tok, i) in RPN_TOKENS"
            :key="i"
            class="learn-viz-cell sq-paren-char"
            :class="{
              'learn-viz-cell--hot': i === rpnScanIndex,
              'learn-viz-cell--dim': i < rpnScanIndex,
            }"
          >{{ tok }}</span>
        </div>
        <span v-if="rpnScanIndex < RPN_TOKENS.length" class="sq-paren-cursor" aria-hidden="true">▲</span>
      </div>
      <span class="sq-paren-flow" aria-hidden="true">↓</span>
      <div class="sq-rpn-main">
        <div class="sq-paren-stack-wrap">
          <span class="sq-paren-stack-label">数字栈</span>
          <div class="learn-stack-well sq-paren-stack">
            <div class="learn-well-cap learn-well-cap--top">栈顶 ▲</div>
            <div class="learn-stack-body alp-vstack-body alp-vslots-5">
              <span
                v-for="(v, i) in rpnStackCells"
                :key="'rpn' + v + i"
                class="learn-viz-cell"
                :class="{ 'learn-viz-cell--hot': i === rpnStackCells.length - 1 }"
              >{{ v }}</span>
            </div>
            <div class="learn-well-cap learn-well-cap--bottom">栈底</div>
          </div>
        </div>
        <div v-if="rpnPopPair" class="sq-rpn-calc">
          <span class="learn-viz-op learn-viz-op--pop">pop</span>
          <span class="learn-viz-cell learn-viz-cell--dim">{{ rpnPopPair[1] }}</span>
          <span class="learn-viz-cell learn-viz-cell--dim">{{ rpnPopPair[0] }}</span>
          <span class="learn-viz-arrow" aria-hidden="true">→</span>
          <span class="learn-viz-cell learn-viz-cell--hot">{{ step === 2 ? '3' : '9' }}</span>
          <span class="learn-viz-op learn-viz-op--push">push</span>
        </div>
        <span v-else-if="rpnIsOp" class="learn-viz-op sq-rpn-op-badge">运算符 +</span>
      </div>
    </div>

    <!-- 239 滑动窗口最大值 -->
    <div v-else-if="sectionId === 'sliding-window-max' && swFrame" class="learn-viz-panel sq-sw-viz">
      <header class="sq-sw-head">
        <span class="learn-viz-tag learn-viz-tag--violet">单调递减 deque</span>
        <span class="sq-sw-k-badge">k = 3</span>
      </header>
      <div class="sq-sw-array">
        <span
          v-for="n in SW_NUMS"
          :key="n.i"
          class="learn-viz-cell sq-sw-cell"
          :class="{
            'learn-viz-cell--hot': swFrame.win.includes(n.i),
            'learn-viz-cell--dim': !swFrame.win.includes(n.i) && step >= 2,
          }"
        >
          <span class="sq-sw-val">{{ n.v }}</span>
          <span class="sq-sw-idx">i={{ n.i }}</span>
        </span>
      </div>
      <div class="sq-sw-deque-wrap">
        <span class="sq-sw-deque-label">deque（存下标）</span>
        <div class="deque-well sq-sw-deque" :class="{ 'deque-well--active': step >= 1 }">
          <div class="deque-port deque-port--left">
            <span class="port-label">队头</span>
            <span class="port-ops">max</span>
          </div>
          <div class="deque-lane">
            <span
              v-for="idx in swFrame.deque"
              :key="'dq' + idx"
              class="learn-viz-cell"
              :class="{
                'learn-viz-cell--hot': idx === swFrame.deque[0],
                'learn-viz-cell--dim': swFrame.popBack.includes(idx),
              }"
            >
              {{ idx }}
            </span>
          </div>
          <div class="deque-port deque-port--right">
            <span class="port-label">队尾</span>
            <span class="port-ops">入队</span>
          </div>
        </div>
        <p v-if="swFrame.popBack.length" class="sq-sw-note sq-sw-note--warn">
          队尾弹出 ≤ 当前值的旧下标：{{ swFrame.popBack.join(', ') }}
        </p>
        <p v-if="swFrame.popFront >= 0" class="sq-sw-note sq-sw-note--warn">
          队头下标 {{ swFrame.popFront }} 已滑出窗口 → pop_front
        </p>
      </div>
      <div class="sq-sw-max">
        <span class="sq-sw-max-label">当前窗口最大值</span>
        <span class="learn-viz-cell learn-viz-cell--hot sq-sw-max-val">{{ swFrame.max }}</span>
      </div>
    </div>

    <!-- 347 前 K 高频 -->
    <div v-else-if="sectionId === 'top-k-frequent' && topKFrame" class="learn-viz-grid learn-viz-grid--2 sq-topk-viz">
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag">频次 map</span>
          <span class="learn-viz-badge">统计</span>
        </header>
        <div class="learn-viz-stage sq-topk-map-stage">
          <div class="sq-topk-freq-list">
            <div
              v-for="item in FREQ_ITEMS"
              :key="item.k"
              class="sq-topk-freq-row"
              :class="{ 'sq-topk-freq-row--hot': topKFrame.mapHot }"
            >
              <span class="learn-viz-cell" :class="{ 'learn-viz-cell--hot': topKFrame.mapHot }">{{ item.k }}</span>
              <span class="sq-topk-bar" :style="{ width: 16 + item.f * 22 + 'px' }" />
              <span class="sq-topk-cnt">×{{ item.f }}</span>
            </div>
          </div>
        </div>
      </article>
      <span class="learn-viz-transfer" aria-hidden="true">→</span>
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag learn-viz-tag--violet">小顶堆 k=2</span>
          <span class="sq-sw-k-badge sq-sw-k-badge--violet">Top-K</span>
        </header>
        <div class="learn-viz-stage sq-topk-heap-stage">
          <div v-if="topKFrame.heapCells.length" class="sq-topk-heap">
            <span
              v-for="(c, i) in topKFrame.heapCells"
              :key="c"
              class="learn-viz-cell"
              :class="{ 'learn-viz-cell--hot': topKFrame.heapHot && i === 1 }"
            >{{ c }}</span>
            <span class="sq-topk-heap-cap">堆顶（频次最小）</span>
          </div>
          <div v-if="topKFrame.result.length" class="sq-topk-result">
            <span class="sq-topk-result-label">答案</span>
            <span v-for="r in topKFrame.result" :key="r" class="learn-viz-pill sq-topk-pill-hot">{{ r }}</span>
          </div>
          <p v-else class="sq-topk-placeholder">遍历 map 维护大小为 k 的堆</p>
        </div>
      </article>
    </div>

    <div v-else-if="sectionId === 'summary'" class="learn-viz-panel sq-summary-viz">
      <div class="sq-summary-grid">
        <article
          v-for="(g, gi) in SUMMARY_GROUPS"
          :key="g.title"
          class="sq-summary-card"
          :class="[
            `sq-summary-card--${g.color}`,
            { 'sq-summary-card--active': step === gi || step >= SUMMARY_GROUPS.length },
          ]"
        >
          <h4 class="sq-summary-title">{{ g.title }}</h4>
          <div class="sq-summary-tags">
            <span
              v-for="t in g.tags"
              :key="t"
              class="learn-viz-pill"
              :class="{ 'learn-viz-pill--hot': step === gi }"
            >{{ t }}</span>
          </div>
        </article>
      </div>
    </div>
  </SteppedAnimShell>
</template>

<style scoped>
/* 顶部三列动画区：轻外壳，正文在下方 LearnSectionBody */
.sq-theory-trio {
  width: 100%;
  margin: 0;
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.sq-theory-trio-hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--alp-color-muted);
  text-align: center;
  line-height: 1.5;
}

.sq-theory-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: stretch;
  gap: 14px;
  width: 100%;
}

@media (max-width: 960px) {
  .sq-theory-grid {
    grid-template-columns: 1fr;
    max-width: 420px;
    margin: 0 auto;
  }
}

.sq-theory-card {
  --sq-cell: 40px;
  --sq-cell-gap: 10px;
  --alp-vc: var(--sq-cell);
  --alp-vg: var(--sq-cell-gap);
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 14px 12px 12px;
  border-radius: 12px;
  background: var(--alp-bg-code-ish, rgba(15, 23, 42, 0.55));
  border: 1px solid var(--alp-color-border);
  overflow: hidden;
}

.sq-theory-card-head {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 8px;
  margin-bottom: 10px;
}

/* 三列统一演示区高度，底部说明与按钮对齐 */
.sq-viz-stage {
  position: relative;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 248px;
  height: 248px;
  max-height: 248px;
  padding: 4px 2px;
  box-sizing: border-box;
  overflow: hidden;
}

.sq-viz-float {
  position: absolute;
  top: 6px;
  left: 50%;
  z-index: 3;
  transform: translateX(-50%);
  pointer-events: none;
}

.struct-tag {
  font-size: 15px;
  font-weight: 700;
  color: var(--alp-color-primary, #38bdf8);
  letter-spacing: 0.02em;
}

.struct-tag--queue {
  color: #4ade80;
}

.struct-tag--deque {
  color: #c4b5fd;
}

.struct-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 35%, transparent);
}

.struct-badge--queue {
  color: #4ade80;
  background: color-mix(in srgb, #4ade80 12%, transparent);
  border-color: color-mix(in srgb, #4ade80 35%, transparent);
}

.struct-badge--deque {
  color: #c4b5fd;
  background: color-mix(in srgb, #a78bfa 12%, transparent);
  border-color: color-mix(in srgb, #a78bfa 35%, transparent);
}

.viz-stage {
  gap: 8px;
}

.viz-cell {
  display: inline-grid;
  place-items: center;
  min-width: var(--sq-cell, 40px);
  height: var(--sq-cell, 40px);
  padding: 0 8px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--alp-color-text);
  background: var(--alp-bg-surface-solid);
  border: 2px solid var(--alp-color-border);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.28);
}

.viz-cell--hot {
  border-color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 20%, var(--alp-bg-surface-solid));
  transform: scale(1.06);
}

.viz-cell--dim {
  opacity: 0.35;
  transform: scale(0.94);
}

.viz-cell--float {
  border-color: #f87171;
  background: color-mix(in srgb, #f87171 18%, var(--alp-bg-surface-solid));
}

.viz-cell--ghost {
  border-color: #f87171;
  background: color-mix(in srgb, #f87171 12%, transparent);
  opacity: 0.5;
  text-decoration: line-through;
}

.viz-cell--link::after {
  content: '→';
  position: absolute;
  right: calc(var(--sq-cell-gap, 10px) * -0.9);
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.viz-cell--link {
  position: relative;
  margin-right: var(--sq-cell-gap, 10px);
}

/* 栈容器 */
.stack-well {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 108px;
  padding: 0 10px 10px;
  border-radius: 14px;
  border: 2px solid color-mix(in srgb, var(--alp-color-primary) 45%, var(--alp-color-border));
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--alp-color-primary) 8%, transparent),
    var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.6))
  );
  box-shadow: inset 0 2px 12px rgba(0, 0, 0, 0.25);
}

.well-cap {
  width: 100%;
  padding: 8px 0;
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  color: var(--alp-color-muted);
}

.well-cap--top {
  color: var(--alp-color-primary);
  border-bottom: 1px dashed var(--alp-color-border);
}

.well-cap--bottom {
  margin-top: 4px;
  border-top: 1px dashed var(--alp-color-border);
}

.stack-well-body {
  width: 100%;
  padding: 10px 0;
}

/* 横向栈：栈底在左、栈顶在右 */
.stack-well--horizontal {
  align-items: stretch;
  max-width: 100%;
  width: 100%;
  padding: 8px 12px 10px;
}

.stack-axis-h {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--alp-color-border);
}

.well-cap--left,
.well-cap--right {
  width: auto;
  padding: 0;
}

.well-cap--right {
  color: var(--alp-color-primary);
}

.stack-axis-arrow {
  flex: 1 1 auto;
  text-align: center;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.stack-well-body--horizontal {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: nowrap;
  gap: var(--sq-cell-gap, 10px);
  width: 100%;
  padding: 6px 4px;
  min-height: var(--sq-cell, 40px);
}

.stack-float-pop {
  position: absolute;
  right: 0;
  top: 50%;
  z-index: 2;
  pointer-events: none;
  transform: translateY(-50%);
}

.sq-theory-card--stack .sq-viz-stage {
  overflow: visible;
}

.op-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 999px;
}

.op-badge--push {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.14);
  border: 1px solid rgba(74, 222, 128, 0.35);
}

.op-badge--pop {
  color: #f87171;
  background: rgba(248, 113, 113, 0.14);
  border: 1px solid rgba(248, 113, 113, 0.35);
}

/* 队列容器 */
.queue-well {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
  width: 100%;
  max-width: 100%;
  padding: 10px 8px;
  border-radius: 14px;
  border: 2px dashed color-mix(in srgb, #4ade80 40%, var(--alp-color-border));
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.5));
  box-sizing: border-box;
}

.queue-axis {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 4px;
  margin-bottom: 10px;
  width: 100%;
}

.queue-axis-labels {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  width: 100%;
}

.queue-axis-arrow {
  display: block;
  text-align: center;
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
  color: var(--alp-color-muted);
  opacity: 0.75;
}

.axis-tag {
  font-weight: 700;
  font-size: 10px;
  line-height: 1.25;
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.axis-tag--front {
  color: #f87171;
  background: rgba(248, 113, 113, 0.12);
}

.axis-tag--back {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.12);
}

.queue-lane-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: var(--sq-cell, 40px);
  padding: 0 4px;
  box-sizing: border-box;
}

.queue-lane {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: nowrap;
  gap: 0;
}

.queue-lane-wrap--pop {
  padding-left: calc(var(--sq-cell, 40px) + var(--sq-cell-gap, 10px));
}

.queue-ghost {
  position: absolute;
  left: 6px;
  top: 50%;
  margin: 0;
  transform: translateY(-50%);
  z-index: 2;
}

/* deque */
.deque-well {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  max-width: 100%;
  padding: 10px 6px;
  box-sizing: border-box;
  border-radius: 14px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid);
  transition:
    border-color 0.35s ease,
    box-shadow 0.35s ease;
}

.deque-well--active {
  border-color: color-mix(in srgb, #a78bfa 55%, transparent);
  box-shadow: 0 0 0 4px color-mix(in srgb, #a78bfa 15%, transparent);
}

.deque-port {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  min-width: 34px;
  max-width: 38px;
  padding: 5px 3px;
  border-radius: 8px;
  background: var(--alp-bg-code-ish);
  border: 1px solid var(--alp-color-border);
}

.deque-well--active .deque-port {
  border-color: color-mix(in srgb, #a78bfa 40%, transparent);
}

.port-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.port-ops {
  font-size: 10px;
  font-weight: 600;
  color: #c4b5fd;
  text-align: center;
  line-height: 1.3;
}

.deque-lane {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1 1 auto;
  min-width: 0;
  flex-wrap: nowrap;
}

.sq-card-foot {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--alp-color-border);
}

.sq-mini-hint {
  margin: 0;
  min-height: 2.6em;
  font-size: 13px;
  line-height: 1.5;
  color: var(--alp-color-text);
  text-align: center;
}

.sq-mini-toolbar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.dual-stack {
  gap: 16px;
}
.stack-col {
  display: flex;
  flex-direction: column-reverse;
  align-items: center;
  gap: 4px;
  min-width: 48px;
}
.stack-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--alp-color-muted);
}
.queue-rot .lbl {
  font-size: 10px;
  font-weight: 700;
  color: var(--alp-color-muted);
}
.freq {
  flex-direction: column;
  gap: 6px;
  align-items: stretch;
}
.freq-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.freq .bar {
  height: 8px;
  background: var(--alp-color-primary, #2563eb);
  border-radius: 4px;
  opacity: 0.5;
}
.freq-row .cell.hot + .bar {
  opacity: 1;
}
.cnt {
  font-size: 10px;
  color: var(--alp-color-muted);
}
.heap {
  font-size: 10px;
  font-weight: 700;
  color: #a78bfa;
  text-align: center;
}
.sum {
  flex-wrap: wrap;
  gap: 8px;
}
.sum .pill.hot {
  border: 2px solid var(--alp-color-primary, #2563eb);
}

/* 有效括号：上输入扫描 + 下纵向栈 */
.sq-paren-viz {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: calc(var(--lv-stage-h, 248px) - 8px);
}

.sq-paren-scan {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.sq-paren-scan-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
  letter-spacing: 0.04em;
}

.sq-paren-chars {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.sq-paren-char {
  min-width: 36px;
}

.sq-paren-cursor {
  font-size: 12px;
  color: var(--alp-color-primary, #38bdf8);
  line-height: 1;
}

.sq-paren-flow {
  font-size: 14px;
  font-weight: 700;
  color: var(--alp-color-muted);
  opacity: 0.7;
}

.sq-paren-stack-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.sq-paren-stack-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.sq-paren-stack {
  width: 100%;
  max-width: 88px;
}

.sq-paren-op {
  font-size: 12px;
  font-weight: 700;
}

/* ---------- 225 / 1047 / 150 / 239 / 347 / 总结 ---------- */
.sq-sbq-viz,
.sq-adj-viz,
.sq-rpn-viz,
.sq-sw-viz {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: calc(var(--lv-stage-h, 248px) - 8px);
}

.sq-sbq-op-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  width: 100%;
}

.sq-sbq-incoming {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.sq-sbq-incoming strong {
  color: #4ade80;
}

.sq-sbq-queue {
  width: 100%;
  max-width: 360px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 2px dashed color-mix(in srgb, #4ade80 40%, var(--alp-color-border));
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.5));
  box-sizing: border-box;
}

.sq-queue-axis {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--alp-color-border);
}

.sq-queue-axis-arrow {
  flex: 1 1 auto;
  text-align: center;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.sq-axis-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.sq-axis-tag--front {
  color: #f87171;
  background: rgba(248, 113, 113, 0.12);
}

.sq-axis-tag--back {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.12);
}

.sq-queue-lane-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: var(--sq-cell, 40px);
  transition: padding-left 0.38s cubic-bezier(0.22, 1, 0.36, 1);
}

.sq-queue-lane-wrap--rotate {
  padding-left: calc(var(--sq-cell, 40px) + var(--sq-cell-gap, 10px));
}

.sq-queue-lane {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: nowrap;
}

.sq-sbq-rotate-ghost {
  position: absolute;
  left: 6px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
}

.sq-sbq-rotate-hint {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--alp-color-muted);
  text-align: center;
}

:deep(.learn-viz-cell--stack-top),
:deep(.learn-viz-cell--push-new) {
  border-color: var(--alp-color-primary, #38bdf8);
  background: color-mix(in srgb, var(--alp-color-primary) 20%, var(--alp-bg-surface-solid));
  transform: scale(1.06);
}

:deep(.learn-viz-cell--push-new) {
  border-color: #4ade80;
  background: color-mix(in srgb, #4ade80 18%, var(--alp-bg-surface-solid));
}

.sq-adj-viz .sq-adj-pop {
  margin-top: 4px;
}

.sq-adj-result {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--alp-color-text);
}

.sq-adj-result strong {
  color: var(--alp-color-primary);
  font-size: 18px;
}

.sq-rpn-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 14px;
  width: 100%;
}

.sq-rpn-calc {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}

.sq-rpn-op-badge {
  align-self: center;
}

.sq-sw-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.sq-sw-k-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  color: #c4b5fd;
  background: color-mix(in srgb, #a78bfa 12%, transparent);
  border: 1px solid color-mix(in srgb, #a78bfa 35%, transparent);
}

.sq-sw-k-badge--violet {
  color: #c4b5fd;
}

.sq-sw-array {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.sq-sw-cell {
  flex-direction: column;
  gap: 2px;
  min-width: 44px;
  height: auto;
  min-height: var(--sq-cell, 40px);
  padding: 6px 8px 4px;
}

.sq-sw-val {
  font-size: 16px;
  line-height: 1;
}

.sq-sw-idx {
  font-size: 9px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.sq-sw-deque-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.sq-sw-deque-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.sq-sw-deque {
  width: 100%;
  max-width: 280px;
}

.sq-sw-note {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
  text-align: center;
  color: var(--alp-color-muted);
}

.sq-sw-note--warn {
  color: #fbbf24;
}

.sq-sw-max {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  padding-top: 4px;
  border-top: 1px dashed var(--alp-color-border);
  width: 100%;
}

.sq-sw-max-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.sq-sw-max-val {
  min-width: 44px;
  font-size: 18px;
}

.sq-topk-viz {
  width: 100%;
}

.sq-topk-map-stage,
.sq-topk-heap-stage {
  min-height: 180px;
  height: auto;
  max-height: none;
}

.sq-topk-freq-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 200px;
}

.sq-topk-freq-row {
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0.55;
  transition: opacity 0.35s ease;
}

.sq-topk-freq-row--hot {
  opacity: 1;
}

.sq-topk-bar {
  height: 8px;
  border-radius: 4px;
  background: var(--alp-color-primary, #38bdf8);
  transition: width 0.38s cubic-bezier(0.22, 1, 0.36, 1);
}

.sq-topk-cnt {
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-muted);
  min-width: 28px;
}

.sq-topk-heap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.sq-topk-heap-cap {
  font-size: 10px;
  color: #c4b5fd;
  font-weight: 600;
}

.sq-topk-result {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.sq-topk-result-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.sq-topk-pill-hot {
  border: 2px solid var(--alp-color-primary);
  transform: scale(1.05);
}

.sq-topk-placeholder {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  text-align: center;
}

.sq-summary-viz {
  padding: 8px 4px;
}

.sq-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

@media (max-width: 720px) {
  .sq-summary-grid {
    grid-template-columns: 1fr;
    max-width: 320px;
    margin: 0 auto;
  }
}

.sq-summary-card {
  padding: 12px 10px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid);
  opacity: 0.5;
  transition:
    opacity 0.35s ease,
    border-color 0.35s ease,
    box-shadow 0.35s ease;
}

.sq-summary-card--active {
  opacity: 1;
}

.sq-summary-card--blue.sq-summary-card--active {
  border-color: color-mix(in srgb, var(--alp-color-primary) 50%, transparent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--alp-color-primary) 12%, transparent);
}

.sq-summary-card--cyan.sq-summary-card--active {
  border-color: color-mix(in srgb, #4ade80 50%, transparent);
  box-shadow: 0 0 0 3px color-mix(in srgb, #4ade80 12%, transparent);
}

.sq-summary-card--violet.sq-summary-card--active {
  border-color: color-mix(in srgb, #a78bfa 50%, transparent);
  box-shadow: 0 0 0 3px color-mix(in srgb, #a78bfa 12%, transparent);
}

.sq-summary-title {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-text);
  text-align: center;
}

.sq-summary-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
}

:deep(.learn-viz-pill--hot) {
  border-color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 22%, transparent);
  transform: scale(1.05);
}
</style>
