import type { GuideTableBlock } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { applyMonotonicStackEnrichment } from './monotonicStackEnrichment'

export { leetcodeCnUrl } from '@/modules/shared/learningTypes'

export const MONOTONIC_STACK_INTRO =
  '单调栈维护栈内元素单调递增或递减，用于在 O(n) 内为每个元素找到「下一个更大/更小」元素。本篇覆盖每日温度、下一个更大元素 I、柱状图最大矩形、接雨水等单调栈篇核心题。'

const base = (s: LearnSection): LearnSection => s

const MONOTONIC_STACK_SECTIONS_RAW: LearnSection[] = [
  base({
    id: 'theory',
    title: '1. 单调栈理论基础',
    subtitle: '递增栈 · 递减栈 · 存下标',
    difficulty: '入门',
    estMinutes: 20,
    keywords: ['单调栈'],
    points: [
      '常见：递增栈找「下一个更大」；递减栈找「下一个更小」。',
      '通常存下标而非值，便于算距离与宽度。',
      '当前元素与栈顶比较，不满足单调性则 pop，被 pop 的下标即得到答案。',
    ],
  }),
  base({
    id: 'daily-temperatures',
    title: '2. 每日温度（739）',
    subtitle: '递增栈 · 等待天数',
    difficulty: '基础',
    estMinutes: 25,
    keywords: ['739'],
    points: [
      '栈存下标；当前 T[i] 大于栈顶对应温度时，ans[stack.top]=i-stack.top，pop。',
      '最后栈内元素无更高温，ans 保持 0。',
    ],
    main: { id: 739, title: '每日温度', slug: 'daily-temperatures' },
  }),
  base({
    id: 'next-greater',
    title: '3. 下一个更大元素 I（496）',
    subtitle: 'nums2 建单调栈 · 映射到 nums1',
    difficulty: '基础',
    estMinutes: 25,
    keywords: ['496'],
    points: [
      '从右向左扫 nums2，维护递减栈（栈顶为候选答案）。',
      '弹栈直到栈顶 > 当前值，栈顶即 next greater；再 push 当前下标。',
      '用 map 记录 nums2 值 → 下一个更大，再扫 nums1 查表。',
    ],
    main: { id: 496, title: '下一个更大元素 I', slug: 'next-greater-element-i' },
    related: [{ id: 503, title: '下一个更大元素 II', slug: 'next-greater-element-ii' }],
  }),
  base({
    id: 'largest-rectangle',
    title: '4. 柱状图中最大的矩形（84）',
    subtitle: '左右第一个更小 · 宽度 = 右-左-1',
    difficulty: '进阶',
    estMinutes: 40,
    keywords: ['84'],
    points: [
      '对每个柱子高度 h，找左、右第一个严格小于 h 的位置。',
      '递增栈：遇到更小高度时，被 pop 的高度 h 的右边界为当前 i，左边界为栈顶+1。',
      '首尾加哨兵 0 可统一处理边界。',
    ],
    main: { id: 84, title: '柱状图中最大的矩形', slug: 'largest-rectangle-in-histogram' },
  }),
  base({
    id: 'trapping-rain',
    title: '5. 接雨水（42）',
    subtitle: '单调栈凹槽 · 或双指针',
    difficulty: '进阶',
    estMinutes: 40,
    keywords: ['42'],
    points: [
      '单调栈：形成凹槽时，栈顶为底，左右为墙，累加 (min(墙)-底)×宽。',
      '双指针：维护 leftMax、rightMax，矮侧决定水位。',
    ],
    main: { id: 42, title: '接雨水', slug: 'trapping-rain-water' },
  }),
  base({
    id: 'summary',
    title: '6. 单调栈篇总结',
    subtitle: '下一个更大 · 矩形 · 雨水',
    difficulty: '入门',
    estMinutes: 10,
    keywords: ['总结'],
    points: [
      '739/496：模板级「下一个更大」，务必手写熟练。',
      '84：pop 时计算以被 pop 高度为高的最大矩形。',
      '42：单调栈按层累加雨水，与 84 栈操作类似但累加方式不同。',
    ],
  }),
]

export const MONOTONIC_STACK_SECTIONS = applyMonotonicStackEnrichment(MONOTONIC_STACK_SECTIONS_RAW)

export const MONOTONIC_STACK_COUNT = MONOTONIC_STACK_SECTIONS.length

export const MONOTONIC_STACK_EXTRA: GuideTableBlock[] = [
  {
    sectionId: 'theory',
    title: '递增栈 vs 递减栈',
    columns: [
      { prop: 'stack', label: '栈类型', width: 100 },
      { prop: 'maintain', label: '维护性质', minWidth: 140 },
      { prop: 'query', label: '求解', minWidth: 160 },
    ],
    data: [
      { stack: '递增栈', maintain: '栈底到栈顶递增', query: '每个元素右边第一个更大（739）' },
      { stack: '递减栈', maintain: '栈底到栈顶递减', query: '下一个更小、或作为「墙」（84/42）' },
    ],
  },
]
