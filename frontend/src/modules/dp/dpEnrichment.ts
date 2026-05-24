/**
 * 动态规划各节加厚内容（overview + topicBlocks），合并进 dpCurriculum
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const DP_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应动态规划理论基础篇。DP 适用条件：最优子结构 + 重叠子问题。建议：先想「最后一步是什么」再定义状态，不要一上来就写循环。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '何时用 DP',
        points: [
          '求最值、方案数、能否达到：且子问题重复出现（如斐波那契、背包）。',
          '纯 DFS 会超时 → 加备忘录或递推表格。',
        ],
      },
      {
        title: '实现形式',
        points: [
          '一维 dp[i]、二维 dp[i][j]；滚动数组把空间降到 O(1) 或 O(n)。',
          '自顶向下记忆化 vs 自底向上递推，面试常写递推。',
        ],
      },
      {
        title: '与贪心、回溯',
        points: [
          '贪心每步一条路径；回溯枚举所有；DP 保留子问题最优解避免重复计算。',
        ],
      },
    ],
    extraChecklist: ['能说出 dp[i] 含义再写转移'],
  },
  'five-steps': {
    overview:
      '动态规划五部曲：① 定义 dp 及下标含义 ② 递推公式 ③ 初始化 ④ 遍历顺序 ⑤ 举例推导 dp 表。背包类第 ④ 步最关键，错序等于错题。',
    estMinutes: 25,
    topicBlocks: [
      {
        title: '五部曲详解',
        points: [
          '① 含义：dp[i] 代表什么？能否由更小状态得到？',
          '② 递推：dp[i] = f(dp[i-1], dp[i-2], ...)。',
          '③ 初始化：dp[0]、dp[1] 或 dp[0][0] 边界。',
          '④ 顺序：一维从左到右；背包物品外层、容量内层方向固定。',
          '⑤ 验证：手画小样例表格，对照代码输出。',
        ],
      },
      {
        title: '背包遍历口诀',
        points: [
          '01 背包：物品 for 外层，容量 j 从 W 到 weight 逆序（每个物品用一次）。',
          '完全背包：容量 j 从 weight 到 W 正序（物品可重复用）。',
          '组合 vs 排列：518 物品在外为组合，容量在外为排列。',
        ],
      },
    ],
    extraPitfalls: ['没定义清 dp 含义就写循环，调试困难。'],
    summaryPoints: ['五部曲顺序写，背包重点看遍历方向。'],
  },
  'climbing-stairs': {
    overview:
      '力扣 70《爬楼梯》：到第 i 阶的方法数 = 从 i-1 走 1 步 + 从 i-2 走 2 步，即 dp[i]=dp[i-1]+dp[i-2]。与 509 斐波那契同源，可 O(1) 滚动。',
    estMinutes: 20,
    topicBlocks: [
      {
        title: '状态定义',
        points: [
          'dp[i]：到达第 i 阶的方法数；dp[0]=1（虚拟起点）, dp[1]=1。',
          'dp[i]=dp[i-1]+dp[i-2]；答案 dp[n]。',
        ],
      },
      {
        title: '空间优化',
        points: [
          'prev2, prev1 滚动；或递归+记忆化。',
          '746 最小花费爬楼梯：转移改为 min 而非 sum。',
        ],
      },
    ],
    extraChecklist: ['能手画 n=4 的 dp 表'],
  },
  'knapsack-01': {
    overview:
      '01 背包：每件物品最多选一次。一维 dp[j] 表示容量 j 能否达到（或最大价值）。外层物品、内层 j 从 W 到 weight 逆序：dp[j] |= dp[j-weight] 或 dp[j]=max(dp[j], dp[j-w]+v)。416 分割等和子集是经典应用。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '一维 01 背包模板',
        points: [
          'for (item : items) for (j = W; j >= weight; j--) dp[j] = max(dp[j], dp[j-weight]+value);',
          '逆序保证 dp[j-weight] 是「未选当前物品」的状态。',
        ],
      },
      {
        title: '416 分割等和子集',
        points: [
          'sum(nums) 为奇数 → false；target = sum/2。',
          'dp[j] 能否凑出和 j；初始 dp[0]=true。',
          '等价 0-1 背包：每个数选或不选。',
        ],
      },
      {
        title: '474 一和零',
        points: [
          '二维容量 0/1 背包：dp[i][j] 最多 i 个 0、j 个 1 的字符串个数。',
        ],
      },
    ],
    extraPitfalls: ['01 背包用正序遍历导致同一物品用多次。'],
  },
  'unbounded-knapsack': {
    overview:
      '完全背包：每种物品无限个。与 01 唯一区别是内层容量 j 从 weight 到 W 正序。322 最少硬币、518 组合数都属此类，注意求最值与求方案数的遍历顺序差异。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '正序遍历',
        points: [
          'for (coin : coins) for (j = coin; j <= amount; j++)',
          'dp[j] = min(dp[j], dp[j-coin]+1) — 322 最少硬币。',
          '正序允许同一物品在同一轮再次参与更新。',
        ],
      },
      {
        title: '518 零钱兑换 II',
        points: [
          '求组合数：外层物品、内层金额 → 顺序无关，1,2 与 2,1 算一种。',
          '求排列数：外层金额、内层物品 → 377 凑总和。',
        ],
      },
      {
        title: '279 完全平方数',
        points: [
          '物品为平方数 1,4,9,...，完全背包求最少个数。',
        ],
      },
    ],
    extraChecklist: ['能对比 01 与完全背包的内层 for 方向'],
  },
  'coin-change': {
    overview:
      '力扣 322《零钱兑换》：dp[j] 凑出金额 j 的最少硬币数。dp[0]=0，其余初值 INF；无法凑出返回 -1。完全背包最值，外层硬币内层金额正序。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '状态与转移',
        points: [
          'dp[j] = min(dp[j], dp[j-coin]+1)，若 dp[j-coin] 非 INF。',
          '遍历完若 dp[amount]==INF 返回 -1。',
        ],
      },
      {
        title: '与 518 区分',
        points: [
          '322 最少个数；518 组合数 dp[j] += dp[j-coin]。',
          '初始化：322 除 dp[0] 为 INF；518 dp[0]=1。',
        ],
      },
      {
        title: 'BFS 视角',
        points: [
          '也可把金额看作图节点、硬币面值作边权 1 做 BFS；DP 更常考。',
        ],
      },
    ],
    extraPitfalls: ['硬币有 1 时忘记 dp[0]=0 导致全 INF。'],
  },
  lis: {
    overview:
      '力扣 300《最长递增子序列》：O(n²) dp[i]=以 nums[i] 结尾的 LIS 长度，内层 j<i 且 nums[j]<nums[i]。O(n log n) 用 tails 数组维护各长度最小末尾，二分找插入位置（耐心排序）。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: 'O(n²) DP',
        points: [
          'dp[i]=1; for j<i if nums[j]<nums[i] dp[i]=max(dp[i], dp[j]+1);',
          '答案 max(dp)；注意子序列不要求连续。',
        ],
      },
      {
        title: 'O(n log n) 贪心+二分',
        points: [
          'tails[len] 为长度 len+1 的上升子序列的最小末尾。',
          '对每个 x：二分找第一个 >=x 的位置替换，或末尾追加。',
          'tails 长度即 LIS 长度。',
        ],
      },
      {
        title: '拓展',
        points: [
          '1143 最长公共子序列、1035 不相交线 — 二维 DP。',
          '334 递增三元组 — 可维护 min1/min2 或 LIS 长度为 3。',
        ],
      },
    ],
    summaryPoints: ['300：dp[i] 结尾 LIS；进阶用 tails 二分。'],
  },
  summary: {
    overview:
      '动态规划篇复盘：线性（70）→ 背包（01/完全/组合排列）→ 子序列（300）。每题先五部曲再编码；背包遍历顺序是最高频考点。',
    estMinutes: 18,
    topicBlocks: [
      {
        title: '模块地图',
        points: [
          '线性：70、198 打家劫舍、53 最大子数组。',
          '背包：416、322、518、474；牢记逆序/正序。',
          '子序列：300、1143、72 编辑距离。',
          '区间 DP：516、1039 等后续篇章。',
        ],
      },
      {
        title: '刷题建议',
        points: [
          '每道背包题手画 dp 表一行；先 70 再 416 再 322。',
          '面试写不出 O(n log n) 时先写 O(n²) DP 保底。',
        ],
      },
    ],
    extraChecklist: ['01 与完全背包内层 for 方向能脱口而出'],
  },
}

export function applyDpEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, DP_ENRICHMENT)
}
