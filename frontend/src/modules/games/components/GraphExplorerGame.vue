<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('graph-explorer', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const nodes = ['S', 'A', 'B', 'C', 'D', 'F']
const edges: Array<[string, string]> = [
  ['S', 'A'],
  ['S', 'B'],
  ['A', 'C'],
]
const graph: Record<string, string[]> = {
  S: ['B', 'A'],
  A: ['C'],
  B: ['D'],
  C: ['F'],
  D: [],
  F: [],
}
const dfsScript: Array<{ kind: 'move' | 'backtrack'; node?: string }> = [
  { kind: 'move', node: 'B' },
  { kind: 'move', node: 'D' },
  { kind: 'backtrack' },
  { kind: 'backtrack' },
  { kind: 'move', node: 'A' },
  { kind: 'move', node: 'C' },
  { kind: 'move', node: 'F' },
]

const edgeStep = ref(0)
const adjacency = ref<Record<string, string[]>>({})
const bfsQueue = ref<string[]>([])
const bfsSeen = ref<Set<string>>(new Set())
const bfsDist = ref<Record<string, number>>({})
const bfsExpected = ref<string[]>([])
const dfsPath = ref<string[]>([])
const dfsSeen = ref<Set<string>>(new Set())
const dfsActionIndex = ref(0)
const msg = ref('')
const won = ref(false)
const fail = ref(false)

const currentEdge = computed(() => edges[Math.floor(edgeStep.value / 2)])
const currentDirection = computed(() => {
  const edge = currentEdge.value
  if (!edge) return undefined
  return edgeStep.value % 2 === 0
    ? { from: edge[0], to: edge[1] }
    : { from: edge[1], to: edge[0] }
})

const bfsHead = computed(() => bfsQueue.value[0])
const bfsNextNeighbor = computed(() => bfsExpected.value[0])
const dfsCurrent = computed(() => dfsPath.value[dfsPath.value.length - 1] ?? 'S')

const stepIndex = computed(() => {
  if (won.value) return (shellMeta.value?.stepCount ?? 1) - 1
  if (props.levelId === 'representation') return edgeStep.value
  if (props.levelId === 'bfs') return Math.min(bfsSeen.value.size, 5)
  return Math.min(dfsActionIndex.value, 6)
})

const stateValues = computed(() => {
  if (props.levelId === 'representation') {
    return {
      edge: currentEdge.value?.join('-') ?? '完成',
      done: `${edgeStep.value}/${edges.length * 2}`,
    }
  }
  if (props.levelId === 'bfs') {
    return {
      queue: bfsQueue.value.join('→') || '空',
      dist: bfsDist.value.F == null ? '未到达' : String(bfsDist.value.F),
    }
  }
  return {
    path: dfsPath.value.join('→'),
    seen: Array.from(dfsSeen.value).join(','),
  }
})

const hintText = computed(() => {
  if (msg.value) return msg.value
  if (props.levelId === 'representation' && currentDirection.value) {
    return `处理无向边 ${currentEdge.value?.join('-')}：请补 ${currentDirection.value.from} → ${currentDirection.value.to}`
  }
  if (props.levelId === 'bfs') return `展开队头 ${bfsHead.value}，按邻接顺序处理未访问邻居`
  return `当前递归栈顶 ${dfsCurrent.value}，选择下一步或回退`
})

function init() {
  edgeStep.value = 0
  adjacency.value = Object.fromEntries(nodes.map((n) => [n, []]))
  bfsQueue.value = ['S']
  bfsSeen.value = new Set(['S'])
  bfsDist.value = { S: 0 }
  bfsExpected.value = ['A', 'B']
  dfsPath.value = ['S']
  dfsSeen.value = new Set(['S'])
  dfsActionIndex.value = 0
  msg.value = ''
  won.value = false
  fail.value = false
  clearLog('图论关卡开始')
}

watch(() => props.levelId, init, { immediate: true })

function finish(text: string) {
  won.value = true
  fail.value = false
  msg.value = text
  pushLog('关卡通过')
  emit('cleared')
}

function addAdjacency(from: string, to: string) {
  if (props.levelId !== 'representation' || won.value) return
  const expected = currentDirection.value
  if (!expected || from !== expected.from || to !== expected.to) {
    fail.value = true
    msg.value = `本步应补 ${expected?.from ?? '-'} → ${expected?.to ?? '-'}`
    return
  }
  const bucket = adjacency.value[from] ?? []
  if (bucket.includes(to)) {
    fail.value = true
    msg.value = `${from} 的邻接表里已经有 ${to}`
    return
  }
  adjacency.value = {
    ...adjacency.value,
    [from]: [...bucket, to],
  }
  edgeStep.value++
  fail.value = false
  msg.value = `已补 ${from} → ${to}`
  pushLog(`adj[${from}].push(${to})`)
  if (edgeStep.value >= edges.length * 2) {
    finish('邻接表建图完成：每条无向边都补齐了两个方向。')
  }
}

function enqueueNeighbor(node: string) {
  if (props.levelId !== 'bfs' || won.value) return
  const head = bfsHead.value
  if (!head) return
  if (node !== bfsNextNeighbor.value) {
    fail.value = true
    msg.value = `应先访问队头 ${head} 的下一个未访问邻居 ${bfsNextNeighbor.value}`
    return
  }
  bfsSeen.value = new Set([...bfsSeen.value, node])
  bfsDist.value = { ...bfsDist.value, [node]: (bfsDist.value[head] ?? 0) + 1 }
  bfsQueue.value = [...bfsQueue.value, node]
  bfsExpected.value = bfsExpected.value.slice(1)
  fail.value = false
  msg.value = `${node} 入队，dist=${bfsDist.value[node]}`
  pushLog(`访问 ${node}，入队`)
  if (node === 'F') finish('首次到达 F，BFS 得到最短距离 3。')
}

function popBfsHead() {
  if (props.levelId !== 'bfs' || won.value) return
  if (bfsExpected.value.length) {
    fail.value = true
    msg.value = `队头 ${bfsHead.value} 还有邻居没处理`
    return
  }
  const popped = bfsQueue.value.shift()
  const next = bfsHead.value
  if (next === 'A') bfsExpected.value = ['C']
  else if (next === 'B') bfsExpected.value = ['D']
  else if (next === 'C') bfsExpected.value = ['F']
  else bfsExpected.value = []
  fail.value = false
  msg.value = `弹出 ${popped}，继续展开 ${next ?? '空队列'}`
  pushLog(`queue.pop() -> ${popped}`)
}

function dfsMove(node: string) {
  if (props.levelId !== 'dfs' || won.value) return
  const current = dfsCurrent.value
  const expected = dfsScript[dfsActionIndex.value]
  if (expected?.kind !== 'move') {
    fail.value = true
    msg.value = '当前分支已经到头，请先点击“回退栈顶”。'
    return
  }
  if (!graph[current]?.includes(node)) {
    fail.value = true
    msg.value = `${node} 不是 ${current} 的相邻结点`
    return
  }
  if (dfsSeen.value.has(node)) {
    fail.value = true
    msg.value = `${node} 已访问，DFS 不能重复入栈`
    return
  }
  if (node !== expected.node) {
    fail.value = true
    msg.value = expected.node === 'B'
      ? '按邻接顺序先探索 B 分支，才能看到回溯过程。'
      : `本步应进入 ${expected.node}`
    return
  }
  dfsPath.value = [...dfsPath.value, node]
  dfsSeen.value = new Set([...dfsSeen.value, node])
  dfsActionIndex.value++
  fail.value = false
  msg.value = `${node} 入栈，继续深入`
  pushLog(`dfs(${node})`)
  if (node === 'F') finish('先回退死路，再找到目标路径 S→A→C→F。')
}

function dfsBacktrack() {
  if (props.levelId !== 'dfs' || won.value) return
  const expected = dfsScript[dfsActionIndex.value]
  if (expected?.kind !== 'backtrack') {
    fail.value = true
    msg.value = `当前还应继续深入 ${expected?.node ?? ''}`
    return
  }
  if (dfsPath.value.length <= 1) {
    fail.value = true
    msg.value = '起点不能回退'
    return
  }
  const popped = dfsPath.value[dfsPath.value.length - 1]
  dfsPath.value = dfsPath.value.slice(0, -1)
  dfsActionIndex.value++
  fail.value = false
  msg.value = `回退 ${popped}，当前栈顶 ${dfsCurrent.value}`
  pushLog(`path.pop() -> ${popped}`)
}
</script>

<template>
  <GamePlayShell
    v-if="shellMeta"
    :meta="shellMeta"
    :hint="hintText"
    :fail="fail"
    :won="won"
    :step-index="stepIndex"
    :state-values="stateValues"
    :action-log="actionLog"
    @reset="init"
  >
    <div class="workbench graph-game">
      <template v-if="levelId === 'representation'">
        <div class="workbench-head">
          <span class="workbench-title">边集转邻接表</span>
          <code class="workbench-snap">{{ edges.map((e) => e.join('-')).join(', ') }}</code>
        </div>
        <div class="adj-grid">
          <div v-for="node in nodes" :key="node" class="adj-row">
            <strong>{{ node }}</strong>
            <span>{{ adjacency[node]?.join(', ') || '空' }}</span>
          </div>
        </div>
        <div v-if="currentDirection" class="choice-row">
          <button
            v-for="node in nodes.filter((n) => n !== currentDirection?.from)"
            :key="node"
            type="button"
            class="choice-btn"
            :disabled="won"
            @click="addAdjacency(currentDirection.from, node)"
          >
            写入 {{ currentDirection.from }} → {{ node }}
          </button>
        </div>
      </template>

      <template v-else-if="levelId === 'bfs'">
        <div class="workbench-head">
          <span class="workbench-title">BFS 队列</span>
          <code class="workbench-snap">queue: {{ bfsQueue.join(' -> ') }}</code>
        </div>
        <div class="graph-node-grid">
          <button
            v-for="node in nodes"
            :key="node"
            type="button"
            class="graph-node"
            :class="{ seen: bfsSeen.has(node), head: node === bfsHead }"
            :disabled="won || bfsSeen.has(node)"
            @click="enqueueNeighbor(node)"
          >
            {{ node }}
            <small v-if="bfsDist[node] != null">d={{ bfsDist[node] }}</small>
          </button>
        </div>
        <el-button type="primary" :disabled="won" @click="popBfsHead">弹出队头</el-button>
      </template>

      <template v-else>
        <div class="workbench-head">
          <span class="workbench-title">DFS 递归栈</span>
          <code class="workbench-snap">{{ dfsPath.join(' -> ') }}</code>
        </div>
        <div class="graph-node-grid">
          <button
            v-for="node in nodes"
            :key="node"
            type="button"
            class="graph-node"
            :class="{ seen: dfsSeen.has(node), head: node === dfsCurrent }"
            :disabled="won || dfsSeen.has(node)"
            @click="dfsMove(node)"
          >
            {{ node }}
          </button>
        </div>
        <el-button :disabled="won" @click="dfsBacktrack">回退栈顶</el-button>
      </template>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.graph-game {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.adj-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}

.adj-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  background: var(--alp-bg-soft-block);
}

.adj-row strong {
  color: var(--game-accent, #3a8a9e);
}

.adj-row span {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.choice-row,
.graph-node-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.choice-btn,
.graph-node {
  padding: 10px 14px;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-text);
  cursor: pointer;
  font-weight: 600;
  transition:
    border-color 0.12s,
    background 0.12s,
    transform 0.12s;
}

.choice-btn:hover:not(:disabled),
.graph-node:hover:not(:disabled) {
  border-color: var(--game-accent, #3a8a9e);
  background: color-mix(in srgb, var(--game-accent, #3a8a9e) 14%, transparent);
  transform: translateY(-1px);
}

.graph-node {
  min-width: 64px;
  min-height: 58px;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.graph-node small {
  margin-top: 4px;
  font-size: 10px;
  color: var(--alp-color-muted);
}

.graph-node.seen {
  border-color: color-mix(in srgb, #4a8a5e 45%, transparent);
  background: color-mix(in srgb, #4a8a5e 12%, transparent);
}

.graph-node.head {
  outline: 2px solid var(--game-accent, #3a8a9e);
  outline-offset: 2px;
}
</style>
