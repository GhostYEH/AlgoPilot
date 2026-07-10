<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

interface Case {
  steps: string[]
  wrongIndex: number
  explain: string
}

const CASES: Record<string, Case> = {
  'dfs-queue': {
    steps: [
      '1. 将起点入队',
      '2. while 队列非空：出队 u',
      '3. 标记 u 已访问',
      '4. 将所有未访问邻居入队',
      '5. 用队列实现 DFS 深度优先',
    ],
    wrongIndex: 4,
    explain: 'DFS 应使用栈（或递归），BFS 才用队列。',
  },
  'bst-inorder': {
    steps: [
      '1. 中序遍历左子树',
      '2. 访问根（记录值）',
      '3. 若当前值 < 上一值则合法',
      '4. 中序遍历右子树',
    ],
    wrongIndex: 2,
    explain: 'BST 应检查当前值 > 上一值（严格递增）。',
  },
  'dp-order': {
    steps: [
      '1. 初始化 dp[0][*]',
      '2. for i from 1 to n',
      '3.   for w from 0 to W',
      '4.     dp[i][w] = max(不选, 选)',
      '5. 先算 dp[i+1][w] 再算 dp[i][w]',
    ],
    wrongIndex: 4,
    explain: '0/1 背包应依赖 dp[i-1]，不能先填 i+1。',
  },
}

const shellMeta = computed(() => getGameShellMeta('algo-detective', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const c = computed(() => CASES[props.levelId] ?? CASES['dfs-queue'])
const flagged = ref<number[]>([])
const msg = ref('')
const won = ref(false)
const fail = ref(false)

watch(
  () => props.levelId,
  () => {
    flagged.value = []
    msg.value = '点击你认为有问题的步骤（可多选），选满后点「提交判断」'
    won.value = false
    fail.value = false
    clearLog('算法侦探：审查步骤序列')
  },
  { immediate: true },
)

const stepIndex = computed(() => (won.value ? 1 : flagged.value.length > 0 ? 1 : 0))

const stateValues = computed(() => ({
  flag: flagged.value.length ? flagged.value.map((x) => x + 1).join(', ') : '无',
}))

function toggle(i: number) {
  if (won.value) return
  const idx = flagged.value.indexOf(i)
  if (idx >= 0) flagged.value.splice(idx, 1)
  else flagged.value.push(i)
  fail.value = false
  msg.value = `已标记：${flagged.value.map((x) => x + 1).join(', ') || '无'}`
  pushLog(`标记步骤 ${i + 1}`)
}

function submit() {
  if (won.value) return
  if (flagged.value.length !== 1) {
    fail.value = true
    msg.value = '请只标记 1 个错误步骤'
    pushLog('提交：标记数量不对')
    return
  }
  if (flagged.value[0] === c.value.wrongIndex) {
    won.value = true
    msg.value = c.value.explain
    pushLog('找对 bug！')
    emit('cleared')
  } else {
    fail.value = true
    msg.value = '标记的步骤其实没问题，再想想～'
    pushLog('提交错误')
  }
}

function doReset() {
  flagged.value = []
  msg.value = '点击你认为有问题的步骤，选满后点「提交判断」'
  won.value = false
  fail.value = false
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
    <div class="workbench">
      <div class="workbench-head">
        <span class="workbench-title">可疑操作序列</span>
        <code class="workbench-snap">找出 1 处错误</code>
      </div>
      <ol class="steps">
        <li
          v-for="(s, i) in c.steps"
          :key="i"
          class="step"
          :class="{
            'is-flagged': flagged.includes(i),
            'is-right': won && i === c.wrongIndex,
            'is-wrong-step': won && i !== c.wrongIndex,
          }"
          @click="toggle(i)"
        >
          <span class="flag">{{ flagged.includes(i) ? '🚩' : '○' }}</span>
          <span class="step-text">{{ s }}</span>
        </li>
      </ol>
    </div>
    <template #actions>
      <el-button type="primary" size="large" @click="submit">提交判断</el-button>
      <el-button size="large" @click="doReset">清空标记</el-button>
    </template>
  </GamePlayShell>
</template>

<style scoped>
.steps {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 2px solid var(--alp-color-border);
  cursor: pointer;
  font-size: 14px;
  line-height: 1.5;
  transition: border-color 0.12s, background 0.12s, transform 0.12s;
}
.step:hover {
  border-color: #22d3ee;
  transform: translateX(4px);
}
.step.is-flagged {
  border-color: #fbbf24;
  background: color-mix(in srgb, #fbbf24 12%, transparent);
}
.step.is-right {
  border-color: #22c55e;
  background: color-mix(in srgb, #22c55e 14%, transparent);
}
.step.is-wrong-step {
  opacity: 0.5;
}
.flag {
  flex-shrink: 0;
  font-size: 18px;
}
.step-text {
  flex: 1;
}
</style>
