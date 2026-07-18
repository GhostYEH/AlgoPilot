<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import TreeNodeView, { type TreeNodeData } from '@/modules/games/shared/TreeNodeView.vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('tree-cave', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const trees: Record<string, TreeNodeData> = {
  traverse: {
    id: 'A',
    label: 'A',
    children: [
      { id: 'B', label: 'B', children: [{ id: 'D', label: 'D' }] },
      { id: 'C', label: 'C' },
    ],
  },
  bst: {
    id: '8',
    label: '8',
    val: 8,
    children: [
      {
        id: '4',
        label: '4',
        val: 4,
        children: [
          { id: '3', label: '3', val: 3 },
          { id: '5', label: '5', val: 5 },
        ],
      },
      {
        id: '13',
        label: '13',
        val: 13,
        children: [
          { id: '11', label: '11', val: 11 },
          { id: '15', label: '15', val: 15 },
        ],
      },
    ],
  },
  path: {
    id: '5',
    label: '5',
    val: 5,
    children: [
      {
        id: '4',
        label: '4',
        val: 4,
        children: [
          {
            id: '11',
            label: '11',
            val: 11,
            children: [{ id: '2', label: '2', val: 2 }],
          },
        ],
      },
    ],
  },
}

const order = ref<string[]>([])
const path = ref<number[]>([])
const pathSum = ref(0)
const msg = ref('')
const won = ref(false)
const fail = ref(false)
const shakeId = ref('')

const expectedTraverse = ['A', 'B', 'D', 'C']
const expectedBstLen = 7

const tree = computed(() => trees[props.levelId] ?? trees.traverse)

watch(
  () => props.levelId,
  () => {
    order.value = []
    path.value = []
    pathSum.value = 0
    won.value = false
    fail.value = false
    msg.value =
      props.levelId === 'traverse'
        ? '前序遍历：根 → 左 → 右，按顺序点击树上结点'
        : props.levelId === 'bst'
          ? '中序遍历 BST：从小到大点击结点'
          : '从根到叶选值，路径和=22；再次点击已选结点可回溯'
    clearLog('树洞探险开始')
  },
  { immediate: true },
)

const stepIndex = computed(() => {
  if (won.value) return shellMeta.value?.stepCount ? shellMeta.value.stepCount - 1 : 3
  if (props.levelId === 'path') return Math.min(path.value.length, 3)
  return Math.min(order.value.length, props.levelId === 'bst' ? 6 : 3)
})

const stateValues = computed(() => {
  if (props.levelId === 'path') {
    return {
      path: path.value.join('→') || '—',
      sum: String(pathSum.value),
    }
  }
  return { order: order.value.join('→') || '—' }
})

function nodeState(id: string) {
  if (props.levelId === 'path') {
    const node = findNode(tree.value, id)
    if (!node?.val) return ''
    return path.value.includes(node.val) ? 'picked' : ''
  }
  return order.value.includes(id) ? 'visited' : ''
}

function findNode(root: TreeNodeData, id: string): TreeNodeData | null {
  if (root.id === id) return root
  for (const c of root.children ?? []) {
    const f = findNode(c, id)
    if (f) return f
  }
  return null
}

function findNodeByVal(root: TreeNodeData, val: number): TreeNodeData | null {
  if (root.val === val) return root
  for (const c of root.children ?? []) {
    const f = findNodeByVal(c, val)
    if (f) return f
  }
  return null
}

function isLeaf(node: TreeNodeData) {
  return !node.children?.length
}

function onNode(node: TreeNodeData) {
  if (won.value) return
  shakeId.value = ''

  if (props.levelId === 'traverse') {
    const next = expectedTraverse[order.value.length]
    if (node.label !== next) {
      fail.value = true
      shakeId.value = node.id
      msg.value = `前序下一步应是 ${next}`
      order.value = []
      pushLog(`顺序错误，重置`)
      return
    }
    order.value.push(node.label)
    fail.value = false
    pushLog(`访问 ${node.label}`)
    if (order.value.length === expectedTraverse.length) {
      won.value = true
      pushLog('前序完成')
      emit('cleared')
    }
    return
  }

  if (props.levelId === 'bst') {
    const v = node.val!
    const last = order.value.length ? Number(order.value[order.value.length - 1]) : -1
    if (v <= last) {
      fail.value = true
      shakeId.value = node.id
      order.value = []
      msg.value = '必须严格递增！'
      pushLog(`破坏递增：${v}`)
      return
    }
    order.value.push(String(v))
    fail.value = false
    pushLog(`中序访问 ${v}`)
    if (order.value.length >= expectedBstLen) {
      won.value = true
      pushLog('BST 中序完成')
      emit('cleared')
    }
    return
  }

  // path 关：从根到叶，必须沿父子关系推进
  const v = node.val!

  // 回溯：点击路径末端的结点
  if (path.value.length > 0 && v === path.value[path.value.length - 1]) {
    path.value.pop()
    pathSum.value -= v
    fail.value = false
    msg.value = `回溯 ${v}，当前和 ${pathSum.value}`
    pushLog(`回溯 ${v}`)
    return
  }

  // 路径为空：必须从根开始
  if (path.value.length === 0) {
    if (node.id !== tree.value.id) {
      fail.value = true
      shakeId.value = node.id
      msg.value = `必须从根结点 ${tree.value.label}（值 ${tree.value.val}）开始，不能直接点 ${node.label}`
      pushLog(`错误：未从根开始，点了 ${node.label}`)
      return
    }
  } else {
    // 路径非空：必须点击当前路径末端结点的子结点
    const lastVal = path.value[path.value.length - 1]
    const lastNode = findNodeByVal(tree.value, lastVal)
    const isChild = lastNode?.children?.some((c) => c.id === node.id) ?? false
    if (!isChild) {
      fail.value = true
      shakeId.value = node.id
      const childHint = lastNode?.children?.map((c) => `${c.label}(值${c.val})`).join(' 或 ') ?? '无'
      msg.value = `${node.label} 不是路径末端 ${lastNode?.label ?? '?'} 的子结点，下一步只能选：${childHint}`
      pushLog(`错误：${node.label} 不是末端子结点`)
      return
    }
  }

  path.value.push(v)
  pathSum.value += v
  pushLog(`路径 +${v}，和=${pathSum.value}`)

  if (pathSum.value > 22) {
    fail.value = true
    msg.value = `路径和 ${pathSum.value} 已超过 22，请点击末端结点回溯`
    pushLog('和超过 22')
    return
  }

  fail.value = false
  if (pathSum.value === 22 && isLeaf(node)) {
    won.value = true
    msg.value = '路径和=22 且到叶子，通关！'
    pushLog('路径和=22，通关')
    emit('cleared')
  } else if (isLeaf(node) && pathSum.value !== 22) {
    fail.value = true
    msg.value = `已到叶子 ${node.label}，但路径和=${pathSum.value} ≠ 22，请点击该叶子回溯重试`
    pushLog(`叶子但和=${pathSum.value}≠22`)
  } else {
    msg.value = `当前路径和 ${pathSum.value}，继续向下选子结点`
  }
}

function doReset() {
  order.value = []
  path.value = []
  pathSum.value = 0
  won.value = false
  fail.value = false
  msg.value =
    props.levelId === 'traverse'
      ? '前序遍历：根 → 左 → 右，按顺序点击树上结点'
      : props.levelId === 'bst'
        ? '中序遍历 BST：从小到大点击结点'
        : '从根到叶选值，路径和=22'
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
    <div class="workbench tree-workbench">
      <div class="workbench-head">
        <span class="workbench-title">二叉树洞穴</span>
        <code v-if="order.length" class="workbench-snap">{{ order.join(' → ') }}</code>
        <code v-else-if="path.length" class="workbench-snap">和 {{ pathSum }}</code>
      </div>
      <div class="tree-canvas">
        <TreeNodeView :node="tree" :node-state="nodeState" :shake-id="shakeId" @pick="onNode" />
      </div>
      <p v-if="levelId === 'traverse'" class="trail-hint">目标前序：A → B → D → C</p>
      <p v-else-if="levelId === 'path'" class="trail-hint">目标路径和：22（须到叶子结点）</p>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.tree-workbench .tree-canvas {
  display: flex;
  justify-content: center;
  padding: 20px 16px;
  overflow-x: auto;
  min-height: 200px;
}
.trail-hint {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  text-align: center;
}
</style>
