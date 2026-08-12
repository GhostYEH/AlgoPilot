import type { GuideTableBlock } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { applyGreedyEnrichment } from './greedyEnrichment'

export { leetcodeCnUrl } from '@/modules/shared/learningTypes'

export const GREEDY_INTRO =
  '贪心在每一步做当前看起来最优的选择，期望全局最优。关键是证明「局部最优 → 全局最优」。本篇覆盖分发饼干、无重叠区间、用最少数箭、跳跃游戏、加油站环等经典题。'

const base = (s: LearnSection): LearnSection => s

const GREEDY_SECTIONS_RAW: LearnSection[] = [
  base({
    id: 'theory',
    title: '1. 贪心算法理论基础',
    subtitle: '局部最优 · 排序 · 证明直觉',
    difficulty: '入门',
    estMinutes: 20,
    keywords: ['贪心'],
    points: [
      '贪心无通用模板，常先排序再双指针或单次扫描。',
      '区间题：按起点或终点排序，决定贪心维度（最早结束 vs 最晚开始）。',
      '无法证明时考虑 DP；能举反例则贪心不成立。',
    ],
  }),
  base({
    id: 'assign-cookies',
    title: '2. 分发饼干（455）',
    subtitle: '排序后小胃口配小饼干',
    difficulty: '入门',
    estMinutes: 15,
    keywords: ['455'],
    points: [
      'g、s 升序；双指针：若 s[j]>=g[i] 则满足 i++，j 始终前进。',
      '用大饼干满足小胃口是浪费，故尽量用小够用的饼干。',
    ],
    main: { id: 455, title: '分发饼干', slug: 'assign-cookies' },
  }),
  base({
    id: 'non-overlapping-intervals',
    title: '3. 无重叠区间（435）',
    subtitle: '按右端点排序 · 保留最多区间',
    difficulty: '基础',
    estMinutes: 25,
    keywords: ['435', '区间'],
    points: [
      '按 end 升序；选 end 最小的不相交区间。',
      '若下一区间 start < 当前 end，重叠，移除（计数+1）。',
      '等价于「最多保留多少个」= n - 移除数。',
    ],
    main: { id: 435, title: '无重叠区间', slug: 'non-overlapping-intervals' },
    related: [{ id: 452, title: '用最少数量的箭引爆气球', slug: 'minimum-number-of-arrows-to-burst-balloons' }],
  }),
  base({
    id: 'jump-game',
    title: '4. 跳跃游戏（55 / 45）',
    subtitle: '维护最远可达 · 最少步数',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['55', '45'],
    points: [
      '55：遍历时 maxReach = max(maxReach, i+nums[i])，若 i>maxReach 则失败。',
      '45：在 [curEnd, farthest] 内每步 end++，到达 curEnd 时 steps++ 并更新 curEnd=farthest。',
    ],
    main: { id: 55, title: '跳跃游戏', slug: 'jump-game' },
    related: [{ id: 45, title: '跳跃游戏 II', slug: 'jump-game-ii' }],
  }),
  base({
    id: 'gas-station',
    title: '5. 加油站（134）',
    subtitle: '总油量 < 总耗则无解 · 累计亏空则换起点',
    difficulty: '进阶',
    estMinutes: 30,
    keywords: ['134', '环'],
    points: [
      '若 sum(gas) < sum(cost) 返回 -1。',
      'curSum 从 0 累加 gas[i]-cost[i]；若 curSum<0，起点设为 i+1，curSum 清零。',
      '唯一解时该起点必能走完全程。',
    ],
    main: { id: 134, title: '加油站', slug: 'gas-station' },
  }),
  base({
    id: 'stock-greedy',
    title: '6. 股票贪心（121 / 122）',
    subtitle: '只卖一次 vs 可多次交易',
    difficulty: '基础',
    estMinutes: 25,
    keywords: ['121', '122'],
    points: [
      '121：维护最低价，每日更新 maxProfit = max(max, price-low)。',
      '122：累加所有上涨日差价（等价于抓住每一段上升）。',
    ],
    related: [
      { id: 121, title: '买卖股票的最佳时机', slug: 'best-time-to-buy-and-sell-stock' },
      { id: 122, title: '买卖股票的最佳时机 II', slug: 'best-time-to-buy-and-sell-stock-ii' },
    ],
  }),
  base({
    id: 'summary',
    title: '7. 贪心篇总结',
    subtitle: '排序 · 区间 · 覆盖 · 环',
    difficulty: '入门',
    estMinutes: 10,
    keywords: ['总结'],
    points: [
      '区间类：想清楚按左还是按右排序，以及贪心保留策略。',
      '覆盖/可达：维护 farthest 或 curEnd。',
      '环上起点：134 的亏空重置技巧要记牢。',
    ],
  }),
]

export const GREEDY_SECTIONS = applyGreedyEnrichment(GREEDY_SECTIONS_RAW)

export const GREEDY_COUNT = GREEDY_SECTIONS.length

export const GREEDY_EXTRA: GuideTableBlock[] = [
  {
    sectionId: 'summary',
    title: '贪心 vs 动态规划',
    columns: [
      { prop: 'aspect', label: '维度', width: 100 },
      { prop: 'greedy', label: '贪心', minWidth: 180 },
      { prop: 'dp', label: '动态规划', minWidth: 180 },
    ],
    data: [
      { aspect: '决策', greedy: '每步一个局部最优，不可回退', dp: '枚举状态，保留子问题最优' },
      { aspect: '证明', greedy: '需证明贪心选择性质', dp: '状态转移方程即正确性' },
      { aspect: '适用', greedy: '区间调度、覆盖、部分最优化', dp: '最值依赖全局结构、有重叠子问题' },
    ],
  },
]
