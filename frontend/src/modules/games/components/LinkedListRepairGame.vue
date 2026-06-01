<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GameLinkedListBoard from '@/modules/games/shared/GameLinkedListBoard.vue'
import GameToolPalette from '@/modules/games/shared/GameToolPalette.vue'
import type { GameTool } from '@/modules/games/shared/GameToolPalette.vue'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const values = ref<number[]>([1, 2, 3, 4, 5])
const pre = ref<number | null>(null)
const cur = ref<number | null>(null)
const slow = ref<number | null>(null)
const fast = ref<number | null>(null)
const activeTool = ref<string>('cur')
const stepIndex = ref(0)
const msg = ref('')
const won = ref(false)
const fail = ref(false)
const actionLog = ref<string[]>([])

interface Step {
  hint: string
  tool: string
  /** 点节点时期望下标；null 表示 pre 为 null */
  expectNode: number | null
  actionLabel?: string
}

const LEVEL_STEPS: Record<string, Step[]> = {
  reverse: [
    { hint: '① 选中「移动 cur」，点击头结点 0', tool: 'cur', expectNode: 0 },
    { hint: '② 选中「移动 pre」，确认 pre = null（点 null 区）', tool: 'pre', expectNode: null },
    { hint: '③ 执行一次「反转一步」', tool: 'reverse-step', expectNode: -1 },
    { hint: '④ 再执行「反转一步」', tool: 'reverse-step', expectNode: -1 },
    { hint: '⑤ 再执行「反转一步」', tool: 'reverse-step', expectNode: -1 },
    { hint: '⑥ 再执行「反转一步」', tool: 'reverse-step', expectNode: -1 },
    { hint: '⑦ 最后执行「反转一步」完成反转', tool: 'reverse-step', expectNode: -1 },
  ],
  delete: [
    { hint: '① 移动 dummy 指针到虚拟头（点 dummy）', tool: 'dummy', expectNode: -2 },
    { hint: '② 移动 cur 到结点 0', tool: 'cur', expectNode: 0 },
    { hint: '③ 移动 cur 到结点 1', tool: 'cur', expectNode: 1 },
    { hint: '④ 移动 cur 到值为 3 的结点（下标 2）', tool: 'cur', expectNode: 2 },
    { hint: '⑤ 执行「跳过 cur」删除结点 3', tool: 'skip', expectNode: -1 },
  ],
  cycle: [
    { hint: '① 移动 slow 到头结点 0', tool: 'slow', expectNode: 0 },
    { hint: '② 移动 fast 到头结点 0', tool: 'fast', expectNode: 0 },
    { hint: '③ 执行「slow 走一步」', tool: 'slow-step', expectNode: -1 },
    { hint: '④ 执行「fast 走两步」', tool: 'fast-step', expectNode: -1 },
    { hint: '⑤ 再 slow 走一步', tool: 'slow-step', expectNode: -1 },
    { hint: '⑥ 再 fast 走两步 —— 观察是否相遇', tool: 'fast-step', expectNode: -1 },
  ],
}

const LEVEL_META: Record<
  string,
  {
    badge: string
    lc: string
    concept: string
    invariant: string
    codeLines: { text: string; hl?: number[] }[]
    pointers: { key: string; label: string; color: string }[]
  }
> = {
  reverse: {
    badge: '三指针迭代',
    lc: 'LeetCode 206',
    concept: '原地反转：每次把 cur.next 改指向 pre，再整体右移 pre/cur。务必先保存后继再改链。',
    invariant: '循环不变量：已遍历段已反转并挂在 pre 后；cur 指向待处理首结点。',
    codeLines: [
      { text: 'ListNode* pre = nullptr;', hl: [1] },
      { text: 'ListNode* cur = head;', hl: [1] },
      { text: 'while (cur != nullptr) {', hl: [3, 4, 5, 6, 7] },
      { text: '  ListNode* next = cur->next;', hl: [3, 4, 5, 6, 7] },
      { text: '  cur->next = pre;      // 反转', hl: [3, 4, 5, 6, 7] },
      { text: '  pre = cur;', hl: [3, 4, 5, 6, 7] },
      { text: '  cur = next;', hl: [3, 4, 5, 6, 7] },
      { text: '}', hl: [3, 4, 5, 6, 7] },
      { text: 'return pre;  // 新头', hl: [7] },
    ],
    pointers: [
      { key: 'pre', label: 'pre', color: '#38bdf8' },
      { key: 'cur', label: 'cur', color: '#f472b6' },
    ],
  },
  delete: {
    badge: '虚拟头结点',
    lc: 'LeetCode 203',
    concept: '删除指定值：dummy 简化删头；cur 停在待删结点前驱，skip 即 cur.next = cur.next.next。',
    invariant: 'dummy.next 始终为真实头；cur 为「待删结点的前驱」。',
    codeLines: [
      { text: 'ListNode dummy(0);', hl: [0] },
      { text: 'dummy.next = head;', hl: [0] },
      { text: 'ListNode* cur = &dummy;', hl: [0, 1, 2, 3] },
      { text: 'while (cur->next) {', hl: [3, 4] },
      { text: '  if (cur->next->val == val)', hl: [4] },
      { text: '    cur->next = cur->next->next;', hl: [4] },
      { text: '  else cur = cur->next;', hl: [1, 2, 3] },
      { text: '}', hl: [4] },
      { text: 'return dummy.next;', hl: [4] },
    ],
    pointers: [
      { key: 'dummy', label: 'dummy', color: '#94a3b8' },
      { key: 'cur', label: 'cur', color: '#f472b6' },
    ],
  },
  cycle: {
    badge: '快慢指针',
    lc: 'LeetCode 141',
    concept: '龟兔赛跑：slow 每次 +1，fast 每次 +2；若有环必相遇，无环则 fast 先到 null。',
    invariant: '相遇时 slow 进入环内；fast 比 slow 多走的步数可被环长整除。',
    codeLines: [
      { text: 'ListNode* slow = head;', hl: [0, 1] },
      { text: 'ListNode* fast = head;', hl: [0, 1] },
      { text: 'while (fast && fast->next) {', hl: [2, 3, 4, 5] },
      { text: '  slow = slow->next;', hl: [2, 4] },
      { text: '  fast = fast->next->next;', hl: [3, 5] },
      { text: '  if (slow == fast) return true;', hl: [5] },
      { text: '}', hl: [5] },
      { text: 'return false;', hl: [5] },
    ],
    pointers: [
      { key: 'slow', label: 'slow', color: '#a78bfa' },
      { key: 'fast', label: 'fast', color: '#f97316' },
    ],
  },
}

const steps = computed(() => LEVEL_STEPS[props.levelId] ?? LEVEL_STEPS.reverse)
const currentStep = computed(() => steps.value[stepIndex.value])
const meta = computed(() => LEVEL_META[props.levelId] ?? LEVEL_META.reverse)
const rules = computed(() => {
  if (props.levelId === 'reverse') {
    return [
      '必须先让 cur 指向待处理结点，pre 明确为 null 或已反转链头。',
      '每次“反转一步”都要遵守：保存 next、改 cur.next、移动 pre/cur。',
      '不能跳过中间结点；全部结点处理完且 cur 为 null 才算通关。',
    ]
  }
  if (props.levelId === 'delete') {
    return [
      '先放置 dummy，再让 cur 停在待删结点的前驱位置。',
      '只能用“跳过 cur”完成删除，不能直接点击目标结点抹除。',
      '删除后链表必须保持剩余结点原有顺序。',
    ]
  }
  return [
    'slow 每轮只能走一步，fast 每轮只能走两步。',
    '按 slow/fast 的交替步骤操作，不能直接拖到相遇点。',
    '只有在两指针真实相遇时才能判定有环。',
  ]
})

const pointers = computed(() => {
  const p: Record<string, number | null> = {}
  if (props.levelId === 'delete') p.dummy = -1
  if (pre.value !== null) p.pre = pre.value
  if (cur.value !== null) p.cur = cur.value
  if (slow.value !== null) p.slow = slow.value
  if (fast.value !== null) p.fast = fast.value
  return p
})

const tools = computed<GameTool[]>(() => {
  if (props.levelId === 'reverse') {
    return [
      { id: 'pre', label: '移动 pre', hint: '将 pre 指到某结点或 null' },
      { id: 'cur', label: '移动 cur', hint: 'cur 指向当前待反转结点' },
      { id: 'reverse-step', label: '反转一步', hint: '执行一轮 pre/cur 右移并改 next' },
    ]
  }
  if (props.levelId === 'delete') {
    return [
      { id: 'dummy', label: 'dummy', hint: '虚拟头，简化删头结点' },
      { id: 'cur', label: '移动 cur', hint: '前驱指针，停在待删结点前' },
      { id: 'skip', label: '跳过 cur', hint: 'cur->next = cur->next->next' },
    ]
  }
  return [
    { id: 'slow', label: '移动 slow', hint: '龟，每次走一步' },
    { id: 'fast', label: '移动 fast', hint: '兔，每次走两步' },
    { id: 'slow-step', label: 'slow +1', hint: 'slow = slow->next' },
    { id: 'fast-step', label: 'fast +2', hint: 'fast = fast->next->next' },
  ]
})

const removedIndex = ref<number | null>(null)

const progressPercent = computed(() =>
  won.value ? 100 : Math.round((stepIndex.value / steps.value.length) * 100),
)

const codeHighlightSteps = computed(() => {
  if (props.levelId === 'reverse') {
    if (stepIndex.value <= 0) return [1]
    if (stepIndex.value === 1) return [0, 1]
    if (stepIndex.value < steps.value.length) return [3, 4, 5, 6]
    return [7]
  }
  if (props.levelId === 'delete') {
    if (stepIndex.value <= 0) return [0, 1]
    if (stepIndex.value < 4) return [2, 6]
    return [4, 5]
  }
  if (stepIndex.value <= 1) return [0, 1]
  if (stepIndex.value < steps.value.length - 1) return [2, 3, 4]
  return [5]
})

function ptrDisplay(key: string): string {
  const p = pointers.value
  const v = p[key]
  if (v === undefined) return '—'
  if (v === -1) return 'dummy'
  if (v === null) return 'null'
  const val = values.value[v]
  return val !== undefined ? `下标 ${v} (值 ${val})` : `下标 ${v}`
}

function pushLog(text: string) {
  const t = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  actionLog.value = [`[${t}] ${text}`, ...actionLog.value].slice(0, 8)
}

function reset() {
  if (props.levelId === 'delete') values.value = [1, 2, 3, 4]
  else if (props.levelId === 'cycle') values.value = [1, 2, 3, 4, 2]
  else values.value = [1, 2, 3, 4, 5]
  pre.value = null
  cur.value = null
  slow.value = null
  fast.value = null
  activeTool.value = tools.value[0]?.id ?? 'cur'
  stepIndex.value = 0
  msg.value = steps.value[0]?.hint ?? ''
  won.value = false
  fail.value = false
  removedIndex.value = null
  actionLog.value = []
  pushLog('关卡已重置，按步骤提示操作')
}

watch(() => props.levelId, reset, { immediate: true })

function advance() {
  stepIndex.value++
  if (stepIndex.value >= steps.value.length) {
    if (props.levelId === 'reverse') values.value = [5, 4, 3, 2, 1]
    if (props.levelId === 'delete') values.value = [1, 2, 4]
    won.value = true
    msg.value =
      props.levelId === 'reverse'
        ? '链表反转完成！head 指向原尾结点。'
        : props.levelId === 'delete'
          ? '结点 3 已删除，前驱成功跳过。'
          : '快慢指针相遇 → 链表有环！'
    pushLog('关卡通过')
    emit('cleared')
    return
  }
  msg.value = currentStep.value?.hint ?? ''
  activeTool.value = currentStep.value?.tool ?? activeTool.value
}

function checkTool(tool: string) {
  if (!currentStep.value || won.value) return false
  if (currentStep.value.tool !== tool) {
    fail.value = true
    msg.value = `当前步骤应使用「${tools.value.find((t) => t.id === currentStep.value?.tool)?.label ?? currentStep.value.tool}」`
    return false
  }
  return true
}

function onSelectNode(i: number) {
  if (won.value || !currentStep.value) return
  const st = currentStep.value
  if (st.expectNode === -1 || st.expectNode === -2) {
    fail.value = true
    msg.value = '本步请使用操作按钮，而非点击结点'
    return
  }
  if (!checkTool(activeTool.value)) return

  if (st.expectNode === null) {
    if (activeTool.value === 'pre') {
      pre.value = null
      fail.value = false
      pushLog('pre ← null')
      advance()
    } else {
      fail.value = true
      msg.value = '请点击「移动 pre」后确认 pre 为 null'
    }
    return
  }

  if (st.expectNode === -2 && activeTool.value === 'dummy') {
    fail.value = false
    pushLog('dummy 就位（虚拟头）')
    advance()
    return
  }

  if (i !== st.expectNode) {
    fail.value = true
    msg.value = `应选中下标 ${st.expectNode} 的结点`
    return
  }

  if (activeTool.value === 'pre') {
    pre.value = i
    pushLog(`pre ← 下标 ${i}`)
  } else if (activeTool.value === 'cur') {
    cur.value = i
    pushLog(`cur ← 下标 ${i}`)
  } else if (activeTool.value === 'slow') {
    slow.value = i
    pushLog(`slow ← 下标 ${i}`)
  } else if (activeTool.value === 'fast') {
    fast.value = i
    pushLog(`fast ← 下标 ${i}`)
  }
  fail.value = false
  advance()
}

function onNullClick() {
  if (won.value || !currentStep.value) return
  if (currentStep.value.expectNode !== null) return
  if (!checkTool('pre')) return
  pre.value = null
  fail.value = false
  pushLog('pre ← null（点击 null 区确认）')
  advance()
}

function onDummyClick() {
  if (won.value || !currentStep.value) return
  if (!checkTool('dummy')) return
  fail.value = false
  pushLog('dummy 就位')
  advance()
}

function reverseOneStep() {
  if (!checkTool('reverse-step')) return
  if (cur.value === null) {
    fail.value = true
    msg.value = '请先让 cur 指向当前结点'
    return
  }
  const c = cur.value
  pre.value = c
  cur.value = c + 1 < values.value.length ? c + 1 : null
  pushLog(`反转一步：pre←${c}，cur${cur.value === null ? '→null' : `→${cur.value}`}`)
  if (cur.value === null) values.value = [...values.value].reverse()
  fail.value = false
  advance()
}

function skipCur() {
  if (!checkTool('skip')) return
  if (cur.value !== 2) {
    fail.value = true
    msg.value = 'cur 应停在要删除结点的前驱（下标 2）'
    return
  }
  removedIndex.value = 3
  values.value = [1, 2, 4]
  pushLog('cur->next = cur->next->next，删除值为 3 的结点')
  fail.value = false
  advance()
}

function slowStep() {
  if (!checkTool('slow-step')) return
  slow.value = slow.value === null ? 0 : Math.min(slow.value + 1, values.value.length - 1)
  pushLog(`slow 前进一步 → 下标 ${slow.value}`)
  fail.value = false
  advance()
}

function fastStep() {
  if (!checkTool('fast-step')) return
  if (fast.value === null) fast.value = 0
  else fast.value = Math.min(fast.value + 2, values.value.length - 1)
  pushLog(`fast 前进两步 → 下标 ${fast.value}`)
  if (slow.value !== null && fast.value === slow.value && stepIndex.value >= steps.value.length - 1) {
    fail.value = false
    advance()
    return
  }
  if (stepIndex.value >= steps.value.length - 1 && slow.value === fast.value) {
    fail.value = false
    advance()
    return
  }
  fail.value = false
  advance()
}

function runAction() {
  const t = activeTool.value
  if (t === 'reverse-step') reverseOneStep()
  else if (t === 'skip') skipCur()
  else if (t === 'slow-step') slowStep()
  else if (t === 'fast-step') fastStep()
}

const progressText = computed(
  () => `步骤 ${Math.min(stepIndex.value + 1, steps.value.length)} / ${steps.value.length}`,
)

const listSnapshot = computed(() => {
  const arr = values.value
  if (props.levelId === 'cycle') return `${arr.join(' → ')} ↩`
  return `${arr.join(' → ')} → null`
})

const needsActionBtn = computed(() =>
  ['reverse-step', 'skip', 'slow-step', 'fast-step'].includes(activeTool.value),
)
</script>

<template>
  <div class="ll-game">
    <header class="ll-game__header">
      <div class="ll-game__header-main">
        <span class="ll-badge">{{ meta.badge }}</span>
        <span class="ll-lc">{{ meta.lc }}</span>
        <span class="ll-progress-text">{{ progressText }}</span>
      </div>
      <el-progress
        :percentage="progressPercent"
        :stroke-width="6"
        :show-text="false"
        color="var(--game-accent, #38bdf8)"
        class="ll-progress-bar"
      />
      <div class="ll-step-rail" role="list" aria-label="步骤进度">
        <button
          v-for="(st, i) in steps"
          :key="i"
          type="button"
          class="ll-step-chip"
          :class="{
            'is-done': i < stepIndex || won,
            'is-current': i === stepIndex && !won,
            'is-future': i > stepIndex && !won,
          }"
          disabled
          :title="st.hint"
        >
          <span class="ll-step-chip__num">{{ i + 1 }}</span>
        </button>
      </div>
    </header>

    <div class="ll-game__grid">
      <section class="ll-play">
        <div class="ll-hint-box" :class="{ 'is-fail': fail, 'is-win': won }">
          <span class="ll-hint-box__label">{{ won ? '完成' : fail ? '再试一次' : '当前任务' }}</span>
          <p class="ll-hint-box__text">{{ msg }}</p>
        </div>

        <div class="ll-play__tools">
          <GameToolPalette
            :tools="tools"
            :active-id="activeTool"
            @select="activeTool = $event"
          />
          <div class="ll-quick-actions">
            <button
              v-if="levelId === 'reverse' || levelId === 'delete'"
              type="button"
              class="null-btn"
              @click="levelId === 'reverse' ? onNullClick() : onDummyClick()"
            >
              {{ levelId === 'reverse' ? 'pre → null' : 'dummy → 头前' }}
            </button>
            <el-button size="small" text @click="reset">重置本关</el-button>
          </div>
        </div>

        <div class="ll-board-wrap">
          <div class="ll-board-head">
            <span class="ll-board-head__title">链表工作台</span>
            <code class="ll-board-head__snap">{{ listSnapshot }}</code>
          </div>
          <GameLinkedListBoard
            :values="values"
            :pointers="pointers"
            :highlight-index="cur ?? slow ?? undefined"
            :removed-index="removedIndex"
            :has-cycle="levelId === 'cycle'"
            @select="onSelectNode"
          />
          <p class="ll-board-tip">点击结点移动指针；高亮结点为当前 cur / slow 位置</p>
        </div>

        <div class="alp-game-actions">
          <el-button
            v-if="needsActionBtn"
            type="primary"
            size="large"
            @click="runAction"
          >
            执行当前操作
          </el-button>
          <el-button v-else size="large" disabled>先按提示选中工具并点击结点</el-button>
        </div>

        <p v-if="won" class="alp-game-win">{{ msg }}</p>
      </section>

      <aside class="ll-sidebar">
        <div class="ll-panel ll-panel--code">
          <h3 class="ll-panel__title">伪代码对照</h3>
          <pre class="ll-code"><code><span
              v-for="(line, li) in meta.codeLines"
              :key="li"
              class="ll-code__line"
              :class="{ 'is-active': line.hl?.some((s) => codeHighlightSteps.includes(s)) }"
            >{{ line.text }}
</span></code></pre>
        </div>

        <div class="ll-panel ll-panel--ptrs">
          <h3 class="ll-panel__title">指针寄存器</h3>
          <ul class="ll-ptr-list">
            <li
              v-for="p in meta.pointers"
              :key="p.key"
              class="ll-ptr-item"
              :style="{ '--ptr-color': p.color }"
            >
              <span class="ll-ptr-item__name">{{ p.label }}</span>
              <span class="ll-ptr-item__val">{{ ptrDisplay(p.key) }}</span>
            </li>
            <li v-if="levelId === 'reverse'" class="ll-ptr-item ll-ptr-item--extra">
              <span class="ll-ptr-item__name">head</span>
              <span class="ll-ptr-item__val">{{ won ? '原尾结点' : '下标 0' }}</span>
            </li>
          </ul>
        </div>

        <div class="ll-panel ll-panel--concept">
          <h3 class="ll-panel__title">游戏规则</h3>
          <ol class="ll-rules">
            <li v-for="rule in rules" :key="rule">{{ rule }}</li>
          </ol>
        </div>

        <div class="ll-panel ll-panel--concept">
          <h3 class="ll-panel__title">算法要点</h3>
          <p class="ll-concept">{{ meta.concept }}</p>
          <p class="ll-invariant">
            <strong>不变量：</strong>{{ meta.invariant }}
          </p>
        </div>

        <div class="ll-panel ll-panel--log">
          <h3 class="ll-panel__title">操作日志</h3>
          <ul v-if="actionLog.length" class="ll-log">
            <li v-for="(entry, i) in actionLog" :key="i">{{ entry }}</li>
          </ul>
          <p v-else class="ll-log-empty">尚无操作记录</p>
        </div>
      </aside>
    </div>

    <footer class="ll-game__footer">
      <span class="ll-footer-item">修链口诀：先保存后继，再改 next，最后移动指针</span>
      <span class="ll-footer-item">对应课程：链表篇 · 反转 / 删除 / 判环</span>
    </footer>
  </div>
</template>

<style scoped>
.ll-game {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

.ll-game__header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: color-mix(in srgb, var(--game-accent, #38bdf8) 8%, var(--alp-bg-soft-block));
}

.ll-game__header-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.ll-badge {
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--game-accent, #38bdf8);
  background: color-mix(in srgb, var(--game-accent, #38bdf8) 16%, transparent);
  border-radius: 999px;
}

.ll-lc {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.ll-progress-text {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  color: var(--game-accent, #38bdf8);
}

.ll-progress-bar {
  width: 100%;
}

.ll-step-rail {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ll-step-chip {
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  cursor: default;
  transition: border-color 0.15s, background 0.15s;
}

.ll-step-chip__num {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.ll-step-chip.is-done {
  border-color: color-mix(in srgb, #22c55e 50%, transparent);
  background: color-mix(in srgb, #22c55e 14%, transparent);
}

.ll-step-chip.is-done .ll-step-chip__num {
  color: #86efac;
}

.ll-step-chip.is-current {
  border-color: var(--game-accent, #38bdf8);
  background: color-mix(in srgb, var(--game-accent, #38bdf8) 22%, transparent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--game-accent, #38bdf8) 25%, transparent);
}

.ll-step-chip.is-current .ll-step-chip__num {
  color: #7dd3fc;
}

.ll-game__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(260px, 0.85fr);
  gap: 16px;
  align-items: start;
  flex: 1;
}

.ll-play {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.ll-hint-box {
  padding: 12px 14px;
  border-radius: 10px;
  border-left: 4px solid var(--game-accent, #38bdf8);
  background: color-mix(in srgb, var(--game-accent, #38bdf8) 6%, var(--alp-bg-surface-solid, #0f172a));
}

.ll-hint-box.is-fail {
  border-left-color: #ef4444;
  background: color-mix(in srgb, #ef4444 8%, transparent);
}

.ll-hint-box.is-win {
  border-left-color: #22c55e;
  background: color-mix(in srgb, #22c55e 10%, transparent);
}

.ll-hint-box__label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--alp-color-muted);
  margin-bottom: 4px;
}

.ll-hint-box.is-fail .ll-hint-box__label {
  color: #fca5a5;
}

.ll-hint-box__text {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.ll-play__tools {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.ll-play__tools :deep(.tool-palette) {
  margin-bottom: 0;
  flex: 1;
  min-width: 200px;
}

.ll-quick-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.null-btn {
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 8px;
  border: 1px dashed var(--alp-color-border);
  background: transparent;
  color: var(--alp-color-muted);
  cursor: pointer;
  transition: border-color 0.12s, color 0.12s;
}

.null-btn:hover {
  border-color: #38bdf8;
  color: #7dd3fc;
}

.ll-board-wrap {
  padding: 14px;
  border-radius: 12px;
  border: 1px dashed color-mix(in srgb, var(--game-accent, #38bdf8) 35%, var(--alp-color-border));
  background: color-mix(in srgb, var(--game-accent, #38bdf8) 4%, transparent);
}

.ll-board-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.ll-board-head__title {
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.ll-board-head__snap {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 6px;
  background: var(--alp-bg-soft-block);
  color: #7dd3fc;
  font-family: ui-monospace, monospace;
}

.ll-board-wrap :deep(.ll-board) {
  margin-bottom: 8px;
  min-height: 100px;
  justify-content: center;
}

.ll-board-tip {
  margin: 0;
  font-size: 11px;
  color: var(--alp-color-muted);
  text-align: center;
}

.ll-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ll-panel {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.5));
}

.ll-panel__title {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--alp-color-muted);
}

.ll-code {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #0c1222;
  overflow-x: auto;
  font-size: 11px;
  line-height: 1.65;
  font-family: ui-monospace, 'Cascadia Code', monospace;
}

.ll-code__line {
  display: block;
  color: #94a3b8;
  padding: 1px 4px;
  border-radius: 3px;
}

.ll-code__line.is-active {
  color: #e2e8f0;
  background: color-mix(in srgb, var(--game-accent, #38bdf8) 18%, transparent);
}

.ll-ptr-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ll-ptr-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.ll-ptr-item__name {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  background: var(--ptr-color);
  color: #0f172a;
}

.ll-ptr-item__val {
  font-size: 12px;
  font-weight: 500;
  color: var(--alp-color-text);
  text-align: right;
}

.ll-concept {
  margin: 0 0 8px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.ll-rules {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ll-rules li {
  font-size: 12px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.ll-invariant {
  margin: 0;
  font-size: 11px;
  line-height: 1.55;
  color: var(--alp-color-muted);
}

.ll-invariant strong {
  color: var(--game-accent, #38bdf8);
  font-weight: 600;
}

.ll-log {
  margin: 0;
  padding: 0;
  list-style: none;
  max-height: 140px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ll-log li {
  font-size: 11px;
  line-height: 1.45;
  padding: 6px 8px;
  border-radius: 6px;
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-muted);
  font-family: ui-monospace, monospace;
}

.ll-log-empty {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  font-style: italic;
}

.ll-game__footer {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px dashed var(--alp-color-border);
  font-size: 11px;
  color: var(--alp-color-muted);
}

.ll-footer-item::before {
  content: '◆ ';
  color: var(--game-accent, #38bdf8);
  font-size: 8px;
}

@media (max-width: 960px) {
  .ll-game__grid {
    grid-template-columns: 1fr;
  }

  .ll-progress-text {
    margin-left: 0;
  }
}
</style>
