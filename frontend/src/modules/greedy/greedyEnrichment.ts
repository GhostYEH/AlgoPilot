/**
 * 贪心各节加厚内容（overview + topicBlocks），合并进 greedyCurriculum
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const GREEDY_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应贪心理论基础篇。贪心每步做局部最优，期望得到全局最优——但必须先证明「贪心选择性质」和「最优子结构」。注意：举不出反例不等于正确，面试要能说明为何局部最优不会错过全局最优。',
    estMinutes: 25,
    topicBlocks: [
      {
        title: '贪心思维步骤',
        points: [
          '① 将问题分解为若干步决策 ② 每步选一个「看起来最好」的选项 ③ 证明该选择安全（可不后悔）。',
          '常配合排序：区间按起点/终点、数组升序、双指针扫描。',
        ],
      },
      {
        title: '与动态规划',
        points: [
          '贪心不保留多种子问题状态，只走一条路；DP 表格保存子问题最优。',
          '若局部最优不能推出全局最优（如 0-1 背包），必须用 DP。',
        ],
      },
      {
        title: '常见题型',
        points: [
          '区间调度：无重叠区间、用最少数箭。',
          '覆盖/可达：跳跃游戏。',
          '环与累积：加油站。',
          '股票、分发饼干：排序 + 双指针或单次扫描。',
        ],
      },
    ],
    extraChecklist: ['遇到区间题先想按左还是按右排序'],
  },
  'assign-cookies': {
    overview:
      '力扣 455《分发饼干》：胃口 g 与饼干 s 均升序排序，小胃口尽量用小饼干满足。双指针：若 s[j]>=g[i] 则 i++，j 始终前进。用大饼干满足小胃口是浪费。',
    estMinutes: 20,
    topicBlocks: [
      {
        title: '双指针贪心',
        points: [
          'sort(g); sort(s); i=0, j=0;',
          'while (i<g.size() && j<s.size()) { if (s[j]>=g[i]) i++; j++; }',
          'return i 为满足的孩子数。',
        ],
      },
      {
        title: '为何贪心正确',
        points: [
          '当前最小未满足胃口 g[i]，用能满足它的最小饼干 s[j] 最省大饼干给后面大胃口。',
          '若用小饼干无法满足，大饼干也无法「节省」给更小胃口（已排序）。',
        ],
      },
    ],
    summaryPoints: ['排序 + 双指针，小对大。'],
  },
  'non-overlapping-intervals': {
    overview:
      '力扣 435《无重叠区间》：等价于最多保留多少个互不重叠区间。按 end 升序，贪心选 end 最小的区间；下一区间 start < 当前 end 则重叠，移除计数+1。452 用最少数箭是类似思路。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '按右端点排序',
        points: [
          'sort(intervals, (a,b)=>a[1]<b[1]);',
          '选第一个区间，end=intervals[0][1]；遍历若 start<end 重叠 count++，否则更新 end。',
          '移除数 = count；最多保留 = n - count。',
        ],
      },
      {
        title: '452 引爆气球',
        points: [
          '区间 [x,y] 视为气球，箭在 x 处可射爆所有 xend 的气球。',
          '同样按右端点排序，贪心在 end 处射箭，逻辑与 435 同源。',
        ],
      },
      {
        title: '排序维度选择',
        points: [
          '「最早结束」留最多区间 → 按 end 升序。',
          '「最少箭」也是尽早结束当前重叠群 → 按 end。',
        ],
      },
    ],
    extraPitfalls: ['按 start 排序会导致贪心策略错误。'],
  },
  'jump-game': {
    overview:
      '力扣 55《跳跃游戏》：维护最远可达 maxReach，遍历时 maxReach=max(maxReach, i+nums[i])；若 i>maxReach 则无法到达。45《跳跃游戏 II》在范围内步数+1，到达边界时更新。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: '55 能否到达',
        points: [
          'maxReach 初始 0；for i: if (i>maxReach) return false; maxReach=max(maxReach, i+nums[i]);',
          'O(n) 一次扫描；不必模拟每一步跳。',
        ],
      },
      {
        title: '45 最少步数',
        points: [
          'curEnd 当前步能到达的最远下标；farthest 扫描中最大可达。',
          'i==curEnd 时 steps++，curEnd=farthest（进入下一层 BFS 层）。',
          '若 curEnd 已>=n-1 可提前结束。',
        ],
      },
      {
        title: '与 BFS 关系',
        points: [
          '45 本质是隐式 BFS 层序，但用贪心 O(1) 空间。',
        ],
      },
    ],
    extraChecklist: ['能口述 45 中 curEnd 与 farthest 含义'],
  },
  'gas-station': {
    overview:
      '力扣 134《加油站》：若总油量 < 总耗则无解。否则存在唯一起点：累计 curSum，若 curSum<0 则起点设为 i+1 并清零 curSum。可用「亏空则前面都不可能作起点」解释。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: '无解判断',
        points: [
          'sum(gas) < sum(cost) → return -1。',
          '总油够则必有解，且解唯一。',
        ],
      },
      {
        title: '起点贪心',
        points: [
          'total=0, cur=0, start=0;',
          'total += gas[i]-cost[i]; cur += gas[i]-cost[i];',
          'if (cur<0) { start=i+1; cur=0; }',
          'return start;',
        ],
      },
      {
        title: '直觉证明',
        points: [
          '从 0 出发到 i 亏空，说明 [0,i] 任一点作起点都会在子区间内亏空。',
          '故起点必在 i+1 之后；总油够时最后 start 可行。',
        ],
      },
    ],
    extraPitfalls: ['只比较总油总耗相等，忘记环上必须一路够油。'],
  },
  'stock-greedy': {
    overview:
      '力扣 121《买卖股票的最佳时机》与 122《II》。121 维护历史最低价，每日更新 maxProfit；122 累加所有上涨区间差价，等价于抓住每一段上升。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '121 一次交易',
        points: [
          'low=INT_MAX; for price: low=min(low,price); profit=max(profit, price-low);',
          '贪心：今天卖的最大利润 = 今天价 - 之前最低买入价。',
        ],
      },
      {
        title: '122 无限次交易',
        points: [
          'if (prices[i]>prices[i-1]) profit += prices[i]-prices[i-1];',
          '只赚上升段，下降不交易；与「峰谷」贪心一致。',
        ],
      },
      {
        title: '与 DP 股票系列',
        points: [
          '123 k 次、188 冷冻期、309 需 DP；121/122 是贪心可解的特例。',
        ],
      },
    ],
    summaryPoints: ['121 最低价；122 累加正差价。'],
  },
  summary: {
    overview:
      '贪心篇复盘：区间按 end、覆盖维护 farthest、环上亏空换起点、股票 121/122。无法证明时换 DP 或尝试反例。',
    estMinutes: 12,
    topicBlocks: [
      {
        title: '题型速记',
        points: [
          '455：排序双指针；435/452：按 end 贪心。',
          '55/45：maxReach 与边界步数；134：总油 + 亏空重置。',
          '121/122：最低价与差价累加。',
        ],
      },
      {
        title: '面试建议',
        points: [
          '先说贪心策略，再口述正确性要点；写不出证明时画小反例验证。',
        ],
      },
    ],
    extraChecklist: ['435 能说明为何按 end 排序'],
  },
}

export function applyGreedyEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, GREEDY_ENRICHMENT)
}
