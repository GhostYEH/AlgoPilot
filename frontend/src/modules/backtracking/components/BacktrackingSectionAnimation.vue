<script setup lang="ts">
import { computed, toRef } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

function maxStepForSection(id: string) {
  const m: Record<string, number> = {
    theory: 4,
    combinations: 3,
    permutations: 3,
    subsets: 3,
    'n-queens': 3,
    sudoku: 3,
    'palindrome-partition': 3,
    summary: 3,
  }
  return m[id] ?? 3
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

const caption = computed(() => {
  const m: Record<string, string> = {
    theory: '回溯：选择 → 递归 → 撤销（决策树 DFS）',
    combinations: '77：start 递增，组合不重复',
    permutations: '46：used 标记已选元素',
    subsets: '78：每个节点都可收集',
    'n-queens': '51：按行放皇后，检测列与对角线',
    sudoku: '37：空格试填 1..9，冲突则回溯',
    'palindrome-partition': '131：切分位置 + 回文判断',
    summary: '组合 · 排列 · 子集 · 棋盘',
  }
  return m[props.sectionId] ?? '回溯示意'
})

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'theory') {
    return [
      '① 从根节点出发，path 为空，面对当前层「选择列表」',
      '② 做选择：将候选加入 path，递归进入下一层（纵向）',
      '③ 满足结束条件：收集答案；未满足则继续 for 横向扩展',
      '④ 回溯：pop 撤销选择，同层尝试下一个候选（剪枝可跳过无效枝）',
      '',
    ][Math.min(i, 4)] ?? ''
  }
  if (s === 'combinations') {
    return ['选 1，path=[1]', '选 2，path=[1,2] 收集', '回溯 pop，选 3', ''][i] ?? ''
  }
  if (s === 'permutations') {
    return ['选 1 used', '选 2 used', '选 3 收集 [1,2,3]', '回溯撤销 used', ''][i] ?? ''
  }
  if (s === 'subsets') {
    return ['[] 收集', '选 1 收集 [1]', '选 2 收集 [1,2]', ''][i] ?? ''
  }
  if (s === 'n-queens') {
    return ['第 1 行放皇后', '第 2 行放皇后', '列/对角冲突则回溯', ''][i] ?? ''
  }
  if (s === 'sudoku') {
    return ['找空格 (i,j)', '试填合法数字 1..9', '无解则回溯上一格', '全部填满即得解', ''][i] ?? ''
  }
  if (s === 'palindrome-partition') {
    return ['从 start 尝试切分点', '子串回文则加入 path', '递归切分剩余部分', ''][i] ?? ''
  }
  if (s === 'summary') {
    return ['组合 77：start 递增', '排列 46：used 数组', '子集 78：每个节点收集', '棋盘 51/37：约束剪枝', ''][i] ?? ''
  }
  return ''
})

const pathCells = computed(() => {
  if (props.sectionId === 'combinations') {
    return [['1'], ['1', '2'], ['1', '2', '3'], ['1', '3']][step.value] ?? []
  }
  if (props.sectionId === 'permutations') {
    return [['1'], ['1', '2'], ['1', '2', '3'], []][step.value] ?? []
  }
  if (props.sectionId === 'subsets') {
    return [[], ['1'], ['1', '2'], ['2']][step.value] ?? []
  }
  return []
})

/** 理论课：决策树层级高亮 */
const theoryDepth = computed(() => Math.min(step.value, 4))

const summaryTags = ['77 组合', '46 排列', '78 子集', '51 皇后']
</script>

<template>
  <SteppedAnimShell
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
    <!-- 理论基础：决策树 DFS -->
    <div v-if="sectionId === 'theory'" class="panel tree-panel alp-vslots-5">
      <div class="tree-col">
        <span class="cell" :class="{ hot: theoryDepth >= 0, dim: theoryDepth < 0 }">根</span>
        <span v-if="theoryDepth >= 1" class="tree-link">↓ 选</span>
        <span v-if="theoryDepth >= 1" class="cell" :class="{ hot: theoryDepth >= 1 }">1</span>
        <span v-if="theoryDepth >= 2" class="tree-link">↓ 递归</span>
        <span v-if="theoryDepth >= 2" class="cell" :class="{ hot: theoryDepth >= 2 }">2</span>
        <span v-if="theoryDepth >= 3" class="tree-link collect">✓ 收集</span>
        <span v-if="theoryDepth >= 4" class="tree-link back">↩ 回溯 pop</span>
      </div>
      <div class="tree-col side">
        <span class="cell dim">2</span>
        <span class="cell dim">3</span>
        <span class="hint-label">同层其他分支</span>
      </div>
    </div>

    <div v-else-if="pathCells.length" class="panel">
      <span class="pill">path</span>
      <span v-for="(v, i) in pathCells" :key="i" class="cell hot">{{ v }}</span>
      <span v-if="step >= 1" class="arrow">↩</span>
    </div>

    <div v-else-if="sectionId === 'n-queens'" class="panel board">
      <span
        v-for="i in 4"
        :key="i"
        class="cell"
        :class="{ hot: step >= i - 1 }"
      >{{ step >= i - 1 ? '♛' : '·' }}</span>
    </div>

    <div v-else-if="sectionId === 'sudoku'" class="panel sudoku">
      <span
        v-for="(n, i) in ['5', '3', '·', '·', '7', '·', '·', '·', '·']"
        :key="i"
        class="cell sudoku-cell"
        :class="{ hot: step >= 1 && n !== '·', dim: n === '·' && step < 2 }"
      >{{ step >= 2 && n === '·' && i === 2 ? '4' : n }}</span>
    </div>

    <div v-else-if="sectionId === 'palindrome-partition'" class="panel">
      <span
        v-for="(ch, i) in ['a', 'a', 'b']"
        :key="i"
        class="cell"
        :class="{ hot: step >= 0 && i < (step >= 1 ? 2 : 1) }"
      >{{ ch }}</span>
      <span v-if="step >= 1" class="cut">|</span>
      <span v-if="step >= 2" class="cell hot">b</span>
    </div>

    <div v-else-if="sectionId === 'summary'" class="panel">
      <span
        v-for="(tag, i) in summaryTags"
        :key="tag"
        class="pill"
        :class="{ hot: step === i, dim: step !== i }"
      >{{ tag }}</span>
    </div>
  </SteppedAnimShell>
</template>

<style scoped>
.tree-panel {
  align-items: flex-start;
  gap: 24px;
  min-height: 120px;
}
.tree-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.tree-col.side {
  padding-top: 28px;
  opacity: 0.85;
}
.tree-link {
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-primary, #2563eb);
}
.tree-link.collect {
  color: #22c55e;
}
.tree-link.back {
  color: #f59e0b;
}
.hint-label {
  font-size: 10px;
  color: var(--alp-color-muted);
  margin-top: 8px;
}
.board .cell {
  min-width: 36px;
}
.sudoku {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  max-width: 120px;
}
.sudoku-cell {
  min-width: 28px;
  height: 28px;
}
.cut {
  font-weight: 700;
  color: var(--alp-color-primary);
  padding: 0 4px;
}
.pill.dim {
  opacity: 0.4;
}
.pill.hot {
  border: 2px solid var(--alp-color-primary, #2563eb);
}
</style>
