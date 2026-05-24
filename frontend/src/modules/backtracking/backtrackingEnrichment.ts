/**
 * 回溯各节加厚内容（overview + topicBlocks），合并进 backtrackingCurriculum
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const BACKTRACKING_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应回溯理论基础篇。回溯 = 树形 DFS + 撤销选择；常用「回溯三部曲」：路径、选择列表、结束条件。与暴力枚举的区别在于剪枝与及时回退，避免无效搜索。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '回溯三部曲',
        points: [
          '① 递归函数参数：当前路径 path、起始位置 start、目标 k 等。',
          '② 终止条件：path 长度、和、棋盘填满等 → 收集结果 return。',
          '③ 单层逻辑：for 遍历选择 → 做选择 → 递归 → 撤销选择（pop / used[i]=false）。',
        ],
      },
      {
        title: '与 DFS 的关系',
        points: [
          '回溯在决策树上深度优先；系统栈保存递归现场。',
          '剪枝：排序后同层去重、剩余和不够、棋盘冲突等，大幅减少节点。',
        ],
      },
      {
        title: '常见误区',
        points: [
          '忘记撤销选择导致 path 污染后续分支。',
          '组合与排列混淆：组合用 start 递增，排列用 used 标记。',
        ],
      },
    ],
    extraChecklist: ['能默写通用回溯模板伪代码'],
  },
  combinations: {
    overview:
      '力扣 77《组合》：从 1..n 中选 k 个。用 start 控制只向后选，避免 1,2 与 2,1 重复。path.size()==k 时收集；可剪枝：剩余元素不足填满 k 则 return。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: 'start 递增保证不重复',
        points: [
          'for (i = start; i <= n; i++) { path.push_back(i); backtracking(i+1); path.pop_back(); }',
          '每层从 start 开始，保证元素升序，组合无重复。',
        ],
      },
      {
        title: '剪枝优化',
        points: [
          '若 n - i + 1 < k - path.size()，后面元素不够，直接 break。',
          '216 组合总和 III、39 组合总和：加入 sum 与 target 剪枝。',
        ],
      },
      {
        title: '与排列、子集对比',
        points: [
          '77 只收集长度为 k 的节点；78 子集收集每个节点；46 排列每层可选任意未用元素。',
        ],
      },
    ],
    extraPitfalls: ['for 从 0 开始导致组合重复。'],
    summaryPoints: ['组合题：start 参数 + 到 k 收集。'],
  },
  permutations: {
    overview:
      '力扣 46《全排列》：每层从 nums 中选一个未使用的元素。需要 used[] 标记；path 满 n 时收集。47 含重复元素：排序 + 同层 used 跳过相同值。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: 'used 数组模板',
        points: [
          'for (i=0; i<n; i++) { if (used[i]) continue; used[i]=true; path.push(nums[i]); backtrack(); path.pop(); used[i]=false; }',
          'path.size()==n 时 push 到结果集。',
        ],
      },
      {
        title: '47 去重（树层去重）',
        points: [
          '先排序；if (i>0 && nums[i]==nums[i-1] && !used[i-1]) continue;',
          '含义：同层前一个相同元素未使用时，当前跳过，避免重复排列。',
        ],
      },
      {
        title: '拓展',
        points: [
          '60 排列序号、31 下一个排列属于数学/模拟，与纯回溯模板不同。',
        ],
      },
    ],
    extraPitfalls: ['组合题误用 used；排列题误用 start 导致漏解。'],
  },
  subsets: {
    overview:
      '力扣 78《子集》：每个节点都是合法答案。进入递归前先 push 当前 path；start 递增选后续元素。90 子集 II 需排序 + 树层去重 i>start && nums[i]==nums[i-1]。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '收集所有节点',
        points: [
          'void backtrack(int start) { result.push_back(path); for (...) }',
          '与 77 区别：不等到 size==k，每层都收集。',
        ],
      },
      {
        title: '90 去重',
        points: [
          '排序后：if (i > start && nums[i] == nums[i-1]) continue;',
          '注意是 i>start（树层）而非 used（树枝），与 47 写法类似但条件不同。',
        ],
      },
      {
        title: '子集与组合总和',
        points: [
          '39/40 组合总和：可重复选元素时 start 从 i 而非 i+1 开始。',
        ],
      },
    ],
    summaryPoints: ['子集：先收集再递归；去重看 i 与 start 关系。'],
  },
  'n-queens': {
    overview:
      '力扣 51《N 皇后》：按行递归，每行尝试列 0..n-1。用列集合、主对角 (row-col)、副对角 (row+col) O(1) 判冲突。收集时拷贝棋盘状态到答案。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '按行放皇后',
        points: [
          'void backtrack(int row)：row==n 收集；for col 0..n-1，若 isValid(row,col) 则放置、递归 row+1、撤销。',
          '不必按列递归，按行更自然。',
        ],
      },
      {
        title: '冲突检测',
        points: [
          '三个 unordered_set：col、diag1(row-col)、diag2(row+col)。',
          '或用 bool 数组，空间 O(n)，常数更小。',
        ],
      },
      {
        title: '输出格式',
        points: [
          'path 可用 string(n,\'.\') 改 col 为 \'Q\'；或 vector<string> 棋盘。',
          '52 N 皇后 II 只计数，不收集棋盘。',
        ],
      },
    ],
    extraChecklist: ['能手写 isValid 与回溯主函数'],
  },
  sudoku: {
    overview:
      '力扣 37《解数独》：找空格填 1..9，行/列/3×3 宫格无冲突则递归，无解则回溯 false。建议用 bool[9] 数组记录占用，比每次扫描快。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '搜索顺序',
        points: [
          '线性找下一个 \'.\' 的 (row,col)；或预处理空格列表。',
          '尝试 digit 1..9：若 valid，填入；若 backtrack 返回 true 则成功；否则恢复 \'.\' 继续。',
        ],
      },
      {
        title: '可行性剪枝',
        points: [
          'row[col]、col[col]、box[row/3][col/3] 三个 bool 数组维护占用。',
          '无合法数字时立即 return false，触发上层回溯。',
        ],
      },
      {
        title: '与 N 皇后对比',
        points: [
          '都是棋盘回溯；数独约束更多（九宫格），但每格候选最多 9 个。',
          '唯一解保证存在，找到即可 return true 停止。',
        ],
      },
    ],
    extraPitfalls: ['忘记回溯时恢复 board[i][j]=\'.\'。'],
  },
  'palindrome-partition': {
    overview:
      '力扣 131《分割回文串》：start 为切分起点，i 从 start 到 n-1 尝试子串 [start,i]；若回文则加入 path，递归 i+1，回溯 pop。预处理 dp[i][j] 可 O(1) 判回文。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '切分 + 回溯',
        points: [
          'for (int i = start; i < n; i++) { string sub = s.substr(start, i-start+1); if (!isPalindrome(sub)) continue; path.push_back(sub); backtrack(i+1); path.pop_back(); }',
          'start==n 时收集 path。',
        ],
      },
      {
        title: '回文预处理',
        points: [
          'dp[i][j]：s[i]==s[j] && (j-i<=2 || dp[i+1][j-1])。',
          'i 从 n-1 到 0，j 从 i 到 n-1 填表。',
        ],
      },
      {
        title: '拓展',
        points: [
          '132 分割回文 II 求最少切分次数 → DP，不是纯回溯收集。',
        ],
      },
    ],
    summaryPoints: ['枚举切分终点 i；回文判断可 DP 预处理。'],
  },
  summary: {
    overview:
      '回溯篇总复盘：先背通用模板，再区分组合（start）、排列（used）、子集（每层收集）、棋盘（冲突检测）。去重口诀：排序 + 同层跳过相同元素。',
    estMinutes: 15,
    topicBlocks: [
      {
        title: '题型对照',
        points: [
          '组合/子集：start 递增；子集先收集再递归。',
          '排列：used；47/90 树层去重写法要分清。',
          '棋盘：51 皇后、37 数独——O(1) 冲突检测是关键。',
          '切割：131 枚举切分点 + 回文判断。',
        ],
      },
      {
        title: '练习建议',
        points: [
          '77 → 46 → 78 顺序建立模板感；再攻 51、37。',
          '每题画决策树，标出剪枝位置，比死记代码更有效。',
        ],
      },
    ],
    extraChecklist: ['能区分 77 与 46 的 for 循环差异'],
  },
}

export function applyBacktrackingEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, BACKTRACKING_ENRICHMENT)
}
