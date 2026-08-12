/**
 * 单调栈各节加厚内容（overview + topicBlocks），合并进 monotonicStackCurriculum
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const MONOTONIC_STACK_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应单调栈理论基础篇。单调栈在 O(n) 内为每个元素找到「下一个更大/更小」元素。要点：通常存下标而非值，便于算距离与宽度；弹栈时处理被 pop 元素的答案。',
    estMinutes: 25,
    topicBlocks: [
      {
        title: '递增栈 vs 递减栈',
        points: [
          '递增栈（栈底到栈顶递增）：当前元素比栈顶大时 pop，被 pop 的下标找到「下一个更大」。',
          '递减栈：找下一个更小，或作为接雨水/矩形的「墙」。',
        ],
      },
      {
        title: '通用模板',
        points: [
          'for i in 0..n-1: while stack 非空且 不满足单调性: 更新 ans[stack.top]; pop; push(i);',
          '遍历结束再清空栈处理剩余元素（若需要）。',
        ],
      },
      {
        title: '与单调队列',
        points: [
          '239 滑动窗口最大值用单调队列；739 每日温度用单调栈——都是维护单调性淘汰无效元素。',
        ],
      },
    ],
    extraChecklist: ['能说明为何存下标', '能口述 pop 时更新答案的时机'],
  },
  'daily-temperatures': {
    overview:
      '力扣 739《每日温度》：栈存下标，当前 T[i] 大于栈顶对应温度时，ans[stack.top]=i-stack.top 并 pop；最后栈内元素无更高温保持 0。单调栈入门模板题。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '递增栈求下一个更大',
        points: [
          'stack 存下标；T[stack.top()] < T[i] 时：ans[stack.top()]=i-stack.top(); pop;',
          '循环结束后 push(i)。',
          '每个下标最多入栈出栈一次，O(n)。',
        ],
      },
      {
        title: '理解方式',
        points: [
          '栈中维护「等待找到更高温度的天数」；更暖的日子到来时结算等待天数。',
          '与 496 下一更大元素同族，739 是数组自身、496 是映射关系。',
        ],
      },
    ],
    extraPitfalls: ['比较时用 T[stack.top()] 而非 stack.top() 本身当下标值。'],
    summaryPoints: ['739：递增栈 + pop 时写 ans 距离。'],
  },
  'next-greater': {
    overview:
      '力扣 496《下一个更大元素 I》：对 nums2 从右向左扫，维护递减栈（栈顶为候选下一个更大）；弹栈直到栈顶 > 当前值，栈顶即答案，再 push 当前下标。map 记录 nums2 值→结果，扫 nums1 查表。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '从右向左 + 递减栈',
        points: [
          'i 从 n-1 到 0：while (!st.empty() && nums2[st.top()]<=nums2[i]) st.pop();',
          'greater = st.empty() ? -1 : nums2[st.top()]; map[nums2[i]]=greater; st.push(i);',
        ],
      },
      {
        title: '503 循环数组',
        points: [
          '遍历 2n 或翻倍数组；下标 i%n，栈中存模后下标。',
          '单调栈处理环形「下一个更大」。',
        ],
      },
      {
        title: '与 739 对比',
        points: [
          '739 从左向右、递增栈；496 从右向左、递减栈——两种视角等价，选一种记牢。',
        ],
      },
    ],
    extraChecklist: ['能手写 nums2 建 map 再答 nums1'],
  },
  'largest-rectangle': {
    overview:
      '力扣 84《柱状图中最大的矩形》：对每个高度 h，找左右第一个严格小于 h 的位置，宽度=右-左-1。递增栈：遇到更小高度 pop，被 pop 的 h 的右边界为 i，左边界为栈顶+1。首尾加哨兵 0 统一边界。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '左右第一个更小',
        points: [
          'heights 末尾 push 0 触发全部 pop；或遍历结束再清空栈。',
          'pop 出 mid：h=heights[mid]；右边界 i；左边界 stack.empty()?0:stack.top()+1；',
          'area = h * (i - left - 1)。',
        ],
      },
      {
        title: '哨兵技巧',
        points: [
          '首尾 0：保证最后所有柱子被 pop 且计算宽度正确。',
          '也可不哨兵，pop 时分别处理栈空左右边界。',
        ],
      },
      {
        title: '85 最大矩形',
        points: [
          '二维矩阵：每行当作柱状图高度，对每行跑 84，O(rows*cols)。',
        ],
      },
    ],
    extraPitfalls: ['pop 时宽度算错：右边界是当前 i，左边界是栈顶+1。'],
  },
  'trapping-rain': {
    overview:
      '力扣 42《接雨水》：单调栈形成凹槽时，栈顶为底、左右为墙，累加 min(墙高)-底高 × 宽。也可双指针维护 leftMax/rightMax，矮侧决定水位。两种都需掌握。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '单调栈法',
        points: [
          '递增栈存下标；heights[i] > heights[stack.top()] 时形成凹槽：',
          'pop 底 mid；若栈空 break；左墙 stack.top()，右墙 i；',
          'h = min(heights[left], heights[i]) - heights[mid]; w = i - left - 1; ans += h*w。',
        ],
      },
      {
        title: '双指针法',
        points: [
          'leftMax, rightMax；l<r 时矮侧更新 max 并累加可接水量。',
          'O(1) 空间，面试常写；单调栈更贴近 84 思维。',
        ],
      },
      {
        title: '与 84 关系',
        points: [
          '都涉及「左右边界」；42 按层累加体积，84 按柱高算矩形面积。',
          '栈操作类似，累加逻辑不同。',
        ],
      },
    ],
    extraChecklist: ['能写双指针版；能口述栈版凹槽形成条件'],
  },
  summary: {
    overview:
      '单调栈篇复盘：739/496 掌握「下一个更大」；84 pop 算矩形；42 凹槽或双指针。存下标、明确 pop 时更新什么是三本篇核心。',
    estMinutes: 12,
    topicBlocks: [
      {
        title: '题型速记',
        points: [
          '下一个更大：739 递增栈从左扫，496 递减栈从右扫。',
          '矩形：84 pop 时算以被 pop 高度为高的最大面积。',
          '雨水：42 栈凹槽累加或双指针。',
        ],
      },
      {
        title: '练习顺序',
        points: [
          '739 → 496 → 84 → 42；每题手写一遍栈循环。',
          '与栈队列篇 239 对比：栈求「边界」，队列求「窗口最值」。',
        ],
      },
    ],
    extraChecklist: ['739、84 各能独立手写一遍'],
  },
}

export function applyMonotonicStackEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, MONOTONIC_STACK_ENRICHMENT)
}
