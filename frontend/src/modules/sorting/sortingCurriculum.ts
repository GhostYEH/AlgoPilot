import type { GuideTableBlock } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'

export const SORTING_INTRO =
  '排序算法专题是数组、双指针、分治、堆与贪心之间的关键桥梁。本章对齐课程 ch08-sorting，从稳定性、原地性和复杂度比较出发，系统掌握基础排序、归并排序、快速排序、堆排序，并通过 OJ 与 Trace 观察合并、分区和堆化过程。'

export const SORTING_SECTIONS: LearnSection[] = [
  {
    id: 'concepts',
    title: '1. 排序问题与评价指标',
    subtitle: '稳定性 · 原地性 · 时空复杂度',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['排序', '稳定性', '原地排序', 'ch08-sorting'],
    overview:
      '排序不仅要求输出有序序列，还要根据数据规模、重复元素、内存限制和后续任务选择合适算法。',
    points: [
      '稳定排序保持相等关键字元素的原相对次序，适合多关键字分层排序。',
      '原地排序通常只使用 O(1) 额外数组空间；递归栈需要单独说明。',
      '比较排序在一般模型下存在 Ω(n log n) 下界，计数排序依赖有限键域。',
      '工程选型需同时考虑最好、平均、最坏时间以及缓存友好性。',
    ],
    checklist: ['能解释稳定性', '能区分原地与额外空间', '能读懂排序复杂度表'],
  },
  {
    id: 'basic',
    title: '2. 冒泡、选择与插入排序',
    subtitle: '循环不变式 · 近乎有序数据',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['冒泡排序', '选择排序', '插入排序'],
    points: [
      '冒泡排序通过相邻交换让最大值逐轮到达后缀，可用未交换标记提前结束。',
      '选择排序每轮选最小值放到区间起点，交换次数少但通常不稳定。',
      '插入排序维护有序前缀，对小规模或近乎有序数据表现良好。',
    ],
    pitfalls: ['内外层边界多循环一位', '插入时覆盖了待插入值', '误认为选择排序稳定'],
    codeSketch: `for i in range(1, len(a)):
    key = a[i]
    j = i - 1
    while j >= 0 and a[j] > key:
        a[j + 1] = a[j]
        j -= 1
    a[j + 1] = key`,
    main: { id: 0, title: '基础排序输出', slug: 'sorting-basic-output' },
  },
  {
    id: 'merge',
    title: '3. 归并排序与逆序对',
    subtitle: '分治 · 双指针合并',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['归并排序', 'merge sort', '逆序对'],
    points: [
      '递归排序左右半区，再用双指针在线性时间内合并。',
      '右侧元素先于左侧剩余元素写入时，可累计逆序对数量。',
      '时间始终 O(n log n)，通常需要 O(n) 辅助数组，且可以稳定。',
    ],
    pitfalls: ['半开区间与闭区间混用', '漏拷贝剩余元素', '逆序对计数使用 32 位整数'],
    main: { id: 0, title: '逆序对统计', slug: 'sorting-inversion-count' },
  },
  {
    id: 'quick',
    title: '4. 快速排序与快速选择',
    subtitle: 'pivot · 分区 · TopK',
    difficulty: '进阶',
    estMinutes: 40,
    keywords: ['快速排序', 'quickselect', 'TopK'],
    points: [
      '分区后 pivot 到达最终位置，递归处理两侧区间。',
      '随机 pivot 或三数取中可降低有序输入导致的退化风险。',
      '快速选择只进入目标下标所在一侧，平均 O(n) 求第 k 大。',
    ],
    pitfalls: ['递归区间仍包含 pivot', '第 k 大目标下标换算错误', '重复值导致指针不移动'],
    main: { id: 0, title: '第 K 大元素', slug: 'sorting-kth-largest' },
  },
  {
    id: 'heap',
    title: '5. 堆排序',
    subtitle: '建堆 · 下沉 · 有效区间',
    difficulty: '进阶',
    estMinutes: 35,
    keywords: ['堆排序', 'heap sort', 'sift down'],
    points: [
      '自底向上从最后一个非叶结点开始下沉，可在 O(n) 内建最大堆。',
      '交换堆顶与有效区间末尾，再缩小堆并恢复堆性质。',
      '堆排序最坏 O(n log n)、额外空间 O(1)，通常不稳定。',
    ],
    pitfalls: ['孩子下标越界', '把数组总长当作当前堆长', '交换后忘记重新下沉'],
  },
  {
    id: 'trace',
    title: '6. Trace 可视化与常见错误',
    subtitle: '合并区间 · pivot · 堆化',
    difficulty: '基础',
    estMinutes: 20,
    keywords: ['Trace', '变量轨迹', '错误诊断'],
    points: [
      '归并 Trace 观察 left/mid/right、i/j 和临时数组写入。',
      '快速选择 Trace 观察 pivot、分区边界与目标下标。',
      '堆排序 Trace 观察 parent/child、heapSize 和交换位置。',
      '基础排序 Trace 可验证“已排序前缀”或“已就位后缀”不变式。',
    ],
  },
  {
    id: 'practice',
    title: '7. OJ 分层实操',
    subtitle: '基础输出 → 逆序对 → TopK',
    difficulty: '进阶',
    estMinutes: 45,
    keywords: ['OJ', '逆序对', 'TopK'],
    points: [
      '基础排序输出：验证输入输出、重复值和负数处理。',
      '逆序对统计：验证归并写回与 64 位计数。',
      '第 K 大元素：比较排序、堆和快速选择三种方案。',
    ],
    main: { id: 0, title: '基础排序输出', slug: 'sorting-basic-output' },
    related: [
      { id: 0, title: '逆序对统计', slug: 'sorting-inversion-count' },
      { id: 0, title: '第 K 大元素', slug: 'sorting-kth-largest' },
    ],
  },
]

export const SORTING_COUNT = SORTING_SECTIONS.length

export const SORTING_EXTRA: GuideTableBlock[] = [
  {
    sectionId: 'concepts',
    title: '常见排序算法对比',
    columns: [
      { prop: 'algorithm', label: '算法', width: 100 },
      { prop: 'time', label: '平均/最坏时间', minWidth: 150 },
      { prop: 'space', label: '额外空间', width: 100 },
      { prop: 'stable', label: '稳定', width: 80 },
    ],
    data: [
      { algorithm: '插入排序', time: 'O(n²) / O(n²)', space: 'O(1)', stable: '是' },
      { algorithm: '归并排序', time: 'O(n log n)', space: 'O(n)', stable: '是' },
      { algorithm: '快速排序', time: 'O(n log n) / O(n²)', space: '平均 O(log n)', stable: '否' },
      { algorithm: '堆排序', time: 'O(n log n)', space: 'O(1)', stable: '否' },
    ],
  },
]
