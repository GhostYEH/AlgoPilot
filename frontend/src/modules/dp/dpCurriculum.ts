import type { GuideTableBlock } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { applyDpEnrichment } from './dpEnrichment'

export { leetcodeCnUrl } from '@/modules/shared/learningTypes'

export const DP_INTRO =
  '动态规划将大问题拆成重叠子问题，用表格保存子问题最优解避免重复计算。本篇按「五部曲」建立思维：定义 dp → 递推 → 初始化 → 遍历顺序 → 举例推导；再练爬楼梯、背包、零钱、最长上升子序列等核心模型。'

const base = (s: LearnSection): LearnSection => s

const DP_SECTIONS_RAW: LearnSection[] = [
  base({
    id: 'theory',
    title: '1. 动态规划理论基础',
    subtitle: '重叠子问题 · 最优子结构',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['DP'],
    points: [
      '适用：最优子结构 + 重叠子问题；纯递归会超时则用 DP。',
      '一维 dp[i]、二维 dp[i][j]、滚动数组降空间。',
      '先想「最后一步是什么」，再写转移。',
    ],
  }),
  base({
    id: 'five-steps',
    title: '2. 动态规划五部曲',
    subtitle: '定义 · 递推 · 初始化 · 顺序 · 验证',
    difficulty: '入门',
    estMinutes: 20,
    keywords: ['五部曲'],
    points: [
      '① dp 数组及下标含义 ② 递推公式 ③ 初始化 ④ 遍历顺序 ⑤ 打印 dp 表验证样例。',
      '背包类注意遍历顺序：01 背包物品外层容量逆序；完全背包容量正序。',
    ],
  }),
  base({
    id: 'climbing-stairs',
    title: '3. 爬楼梯（70）',
    subtitle: '斐波那契 · dp[i]=dp[i-1]+dp[i-2]',
    difficulty: '入门',
    estMinutes: 15,
    keywords: ['70'],
    points: [
      'dp[i] 表示到第 i 阶的方法数；dp[0]=1, dp[1]=1。',
      '可滚动为两个变量 O(1) 空间。',
    ],
    main: { id: 70, title: '爬楼梯', slug: 'climbing-stairs' },
    related: [{ id: 509, title: '斐波那契数', slug: 'fibonacci-number' }],
  }),
  base({
    id: 'knapsack-01',
    title: '4. 01 背包',
    subtitle: '每件物品选一次 · 容量逆序',
    difficulty: '进阶',
    estMinutes: 45,
    keywords: ['416', '背包'],
    points: [
      'dp[j] = 容量 j 能否恰好装满（或最大价值）。',
      'for 物品 for j from W down to weight：dp[j] |= dp[j-weight]。',
      '416 分割等和子集：sum/2 能否由 nums 组成。',
    ],
    related: [{ id: 416, title: '分割等和子集', slug: 'partition-equal-subset-sum' }],
  }),
  base({
    id: 'unbounded-knapsack',
    title: '5. 完全背包',
    subtitle: '物品可重复 · 容量正序',
    difficulty: '进阶',
    estMinutes: 40,
    keywords: ['完全背包', '322'],
    points: [
      '与 01 背包区别：内层 j 从 weight 到 W 正序遍历。',
      '322 零钱兑换：dp[j]=min(dp[j], dp[j-coin]+1)，初始化 INF。',
      '518 零钱兑换 II：求组合数，注意遍历顺序（物品在外为组合，容量在外为排列）。',
    ],
    related: [
      { id: 322, title: '零钱兑换', slug: 'coin-change' },
      { id: 518, title: '零钱兑换 II', slug: 'coin-change-ii' },
    ],
  }),
  base({
    id: 'coin-change',
    title: '6. 零钱兑换（322）',
    subtitle: '最少硬币数 · 完全背包最值',
    difficulty: '基础',
    estMinutes: 25,
    keywords: ['322'],
    points: [
      'dp[0]=0，其余 dp[i]=INF；无法凑出返回 -1。',
      '外层物品、内层金额正序：每种硬币可用无限次。',
    ],
    main: { id: 322, title: '零钱兑换', slug: 'coin-change' },
  }),
  base({
    id: 'lis',
    title: '7. 最长递增子序列（300）',
    subtitle: 'dp[i] 或 patience 二分',
    difficulty: '进阶',
    estMinutes: 35,
    keywords: ['300', 'LIS'],
    points: [
      'O(n²)：dp[i]=以 nums[i] 结尾的 LIS 长度，内层 j<i 且 nums[j]<nums[i]。',
      'O(n log n)：tails 数组维护各长度最小末尾，二分找插入位置。',
    ],
    main: { id: 300, title: '最长递增子序列', slug: 'longest-increasing-subsequence' },
  }),
  base({
    id: 'summary',
    title: '8. 动态规划篇总结',
    subtitle: '线性 · 背包 · 子序列 · 区间 DP',
    difficulty: '入门',
    estMinutes: 15,
    keywords: ['总结'],
    points: [
      '线性 DP：70、打家劫舍、删除字符串等，想清楚 dp[i] 含义。',
      '背包家族：01 / 完全 / 多重，牢记遍历方向。',
      '子序列类：300、1143、1035 等，注意 i、j 双指针式 DP。',
    ],
  }),
]

export const DP_SECTIONS = applyDpEnrichment(DP_SECTIONS_RAW)

export const DP_COUNT = DP_SECTIONS.length

export const DP_EXTRA: GuideTableBlock[] = [
  {
    sectionId: 'five-steps',
    title: '动态规划五部曲',
    columns: [
      { prop: 'no', label: '步', width: 48 },
      { prop: 'content', label: '内容', minWidth: 260 },
    ],
    data: [
      { no: '1', content: '确定 dp 数组及下标的含义' },
      { no: '2', content: '根据含义写出递推公式' },
      { no: '3', content: '初始化边界' },
      { no: '4', content: '确定遍历顺序（尤其背包）' },
      { no: '5', content: '举例推导 dp 表，对照输出' },
    ],
  },
]
