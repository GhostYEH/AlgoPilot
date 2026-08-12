import type { GuideTableBlock } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { applyBacktrackingEnrichment } from './backtrackingEnrichment'

export { leetcodeCnUrl } from '@/modules/shared/learningTypes'

export const BACKTRACKING_INTRO =
  '回溯本质是「带剪枝的暴力搜索」：在决策树上深度优先，每层做选择 → 递归 → 撤销选择。组合、排列、子集、棋盘类（N 皇后、数独）是回溯篇的主线，掌握模板后可快速迁移。'

const base = (s: LearnSection): LearnSection => s

const BACKTRACKING_SECTIONS_RAW: LearnSection[] = [
  base({
    id: 'theory',
    title: '1. 回溯算法理论基础',
    subtitle: '决策树 · 模板 · 与 DFS 的关系',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['回溯', 'DFS'],
    points: [
      '三部曲：① 路径（当前选择）② 选择列表 ③ 结束条件。',
      'for 循环横向遍历选择；递归纵向进入下一层；回溯撤销最后选择。',
      '剪枝：排序后跳过重复、可行性预判（如剩余和不够）。',
    ],
  }),
  base({
    id: 'combinations',
    title: '2. 组合（77）',
    subtitle: '从 n 中选 k · start 控制不重复',
    difficulty: '基础',
    estMinutes: 25,
    keywords: ['77', '组合'],
    points: [
      '递归参数 start：只从 start..n 选，避免 1,2 与 2,1 重复。',
      'path.size() === k 时收集答案。',
      '可剪枝：若剩余元素不足填满 k 则 return。',
    ],
    main: { id: 77, title: '组合', slug: 'combinations' },
  }),
  base({
    id: 'permutations',
    title: '3. 全排列（46）',
    subtitle: 'used 数组 · 每层选未使用元素',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['46', '排列'],
    points: [
      '与组合不同：每层可选任意未用元素，需 used[] 标记。',
      'path 长度等于 nums.length 时收集。',
      '47 含重复：排序 + 同层 used 跳过相同值。',
    ],
    main: { id: 46, title: '全排列', slug: 'permutations' },
    related: [{ id: 47, title: '全排列 II', slug: 'permutations-ii' }],
  }),
  base({
    id: 'subsets',
    title: '4. 子集（78）',
    subtitle: '每个节点都是答案 · 树层去重',
    difficulty: '基础',
    estMinutes: 25,
    keywords: ['78', '子集'],
    points: [
      '进入递归前先 push 当前 path（收集所有节点）。',
      'start 递增保证子集不重复。',
      '90 子集 II：排序 + i>start && nums[i]==nums[i-1] 跳过。',
    ],
    main: { id: 78, title: '子集', slug: 'subsets' },
  }),
  base({
    id: 'n-queens',
    title: '5. N 皇后（51）',
    subtitle: '按行放皇后 · 列与对角线冲突检测',
    difficulty: '进阶',
    estMinutes: 40,
    keywords: ['51', '棋盘'],
    points: [
      'row 递归：每行尝试 col 0..n-1。',
      '用集合或数组记录列、主对角 (row-col)、副对角 (row+col) 占用。',
      '收集棋盘状态时拷贝 path。',
    ],
    main: { id: 51, title: 'N 皇后', slug: 'n-queens' },
  }),
  base({
    id: 'sudoku',
    title: '6. 解数独（37）',
    subtitle: '九宫格约束 · 可行性剪枝',
    difficulty: '进阶',
    estMinutes: 45,
    keywords: ['37', '数独'],
    points: [
      '找下一个空格 (i,j)，尝试 1..9，检查行/列/3×3 是否冲突。',
      '若无合法数字则回溯 false；全部填满返回 true。',
      '可用位运算或 bool[9] 优化冲突检测。',
    ],
    main: { id: 37, title: '解数独', slug: 'sudoku-solver' },
  }),
  base({
    id: 'palindrome-partition',
    title: '7. 分割回文串（131）',
    subtitle: '切分位置 + 回文判断',
    difficulty: '进阶',
    estMinutes: 35,
    keywords: ['131', '回文'],
    points: [
      'start 表示切分起点；i 从 start 到 n-1 尝试子串 [start,i]。',
      '若子串回文则加入 path，递归 i+1，回溯 pop。',
      '预处理 dp[i][j] 是否回文可 O(1) 判断。',
    ],
    main: { id: 131, title: '分割回文串', slug: 'palindrome-partitioning' },
  }),
  base({
    id: 'summary',
    title: '8. 回溯篇总结',
    subtitle: '组合 · 排列 · 子集 · 棋盘',
    difficulty: '入门',
    estMinutes: 12,
    keywords: ['总结'],
    points: [
      '先背通用模板，再区分「start 递增」与「used 标记」。',
      '去重：排序 + 同层跳过相同元素。',
      '棋盘题重点在 O(1) 冲突检测与清晰的回溯条件。',
    ],
  }),
]

export const BACKTRACKING_SECTIONS = applyBacktrackingEnrichment(BACKTRACKING_SECTIONS_RAW)

export const BACKTRACKING_COUNT = BACKTRACKING_SECTIONS.length

export const BACKTRACKING_EXTRA: GuideTableBlock[] = [
  {
    sectionId: 'theory',
    title: '回溯通用模板（伪代码）',
    hint: '与 资料中 给出的三部曲一致。',
    columns: [
      { prop: 'step', label: '步骤', width: 80 },
      { prop: 'action', label: '动作', minWidth: 280 },
    ],
    data: [
      { step: '1', action: 'if 满足结束条件：收集结果；return' },
      { step: '2', action: 'for 选择 in 选择列表：若剪枝则 continue' },
      { step: '3', action: '做选择 → 递归下一层 → 撤销选择（pop / used[i]=false）' },
    ],
  },
]
