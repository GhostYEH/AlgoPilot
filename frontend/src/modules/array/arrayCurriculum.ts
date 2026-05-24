/**
 * 数组学习模块 — 知识结构
 * 与数组篇章节顺序对齐，便于同学延伸阅读与动图。
 * 正文为平台侧归纳，完整题解与动图学习资料以平台讲解与正版资料为准。
 */

import type { LearnSection } from '@/modules/shared/learningTypes'
import { applyArrayEnrichment } from './arrayEnrichment'

export type ArraySection = LearnSection
export type DifficultyLabel = LearnSection['difficulty']
export type PracticeLink = NonNullable<LearnSection['main']>

export const ARRAY_CURRICULUM_INTRO =
  '数组是面试最高频的基础结构之一：思路往往直白，真正区分度在「边界、指针、循环不变量」与代码实现细节。建议按下方顺序学习，每节配合主刷题在编辑器里手写一遍。'

const ARRAY_SECTIONS_RAW: ArraySection[] = [
  {
    id: 'theory',
    title: '1. 数组理论基础',
    subtitle: '先建立内存模型，再谈「删除」「插入」究竟在干什么。',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['连续内存', '随机访问', '覆盖', '二维数组'],
    points: [
      '元素在内存中连续存放，可通过下标 O(1) 随机访问；这是多数「下标技巧」的基础。',
      '静态数组语境下，「删除 / 插入」本质是搬移覆盖，尾部可能残留旧值——很多 bug 来自「逻辑长度」与物理容量未区分。',
      '二维数组在不同语言里布局不同：C++ 可一整块连续；Java 常见「行连续、行间指针」模型。面试时要能用自己的主语言解释清楚。',
      '复杂度直觉：在中间插入/删除最坏需移动约一半元素，平均仍与长度线性相关。',
    ],
    pitfalls: [
      '把 vector / ArrayList 当成「数学数组」：它们是容器，扩容、迭代器失效等语义与裸数组不同。',
      '写双重循环访问二维数组时混淆行列下标，或把 `m×n` 与 `n×m` 传反。',
    ],
    checklist: [
      '能画出「删除中间元素」时剩余元素如何左移的示意图。',
      '能说出你所用语言里二维数组在内存中的大致布局。',
    ],
    complexityHint: '访问 O(1)；尾部插入均摊 O(1)（动态数组扩容时偶发 O(n)）；中间插入/删除 O(n)。',
  },
  {
    id: 'binary-search',
    title: '2. 二分查找',
    subtitle: '区间定义一旦选定，循环里所有边界都要服从同一套「不变量」。',
    difficulty: '基础',
    estMinutes: 45,
    keywords: ['有序', '折半', '循环不变量', '边界'],
    points: [
      '典型前提：有序、且能根据中点值决定丢弃左半或右半；含重复元素时「返回哪个下标」需看题意。',
      '两大写法来自两种区间：[L,R] 闭闭 → `while (L<=R)`，`mid` 偏大则 `R=mid-1`；[L,R) 左闭右开 → `while (L<R)`，`R=mid`。',
      '中点写作 `L + (R-L)/2` 避免 `L+R` 溢出；二分也可推广到「答案单调」的最值问题（如最小满足条件）。',
      '写完后用长度为 0、1、2 的数组各测一遍，比盯着大样例更有效。',
    ],
    pitfalls: [
      '混用两种区间定义：同一题里一会儿 `<=` 一会儿 `<`，或 `R=mid` 与 `R=mid-1` 写反。',
      '死循环：`L=mid` 且 `mid` 计算未向上取整时，区间可能不缩小。',
    ],
    checklist: [
      '能手写 [L,R] 与 [L,R) 两套模板并解释每一行对应的几何意义。',
      '看到「有序 + 判定某侧可丢」能想到二分，而不是只会套「找 target」。',
    ],
    complexityHint: '每次缩小约一半区间 → O(log n) 次比较；空间 O(1)。',
    main: { id: 704, title: '二分查找', slug: 'binary-search' },
    related: [
      { id: 35, title: '搜索插入位置', slug: 'search-insert-position' },
      { id: 34, title: '排序数组中查找首尾位置', slug: 'find-first-and-last-position-of-element-in-sorted-array' },
      { id: 69, title: 'x 的平方根', slug: 'sqrtx' },
      { id: 367, title: '有效的完全平方数', slug: 'valid-perfect-square' },
    ],
  },
  {
    id: 'remove-element',
    title: '3. 移除元素',
    subtitle: '快慢指针：用一次扫描完成「筛选 + 紧凑写入」。',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['原地', '快慢指针', '相向指针', 'O(n)'],
    points: [
      '暴力双层循环每次发现目标就整体左移，最坏 O(n²)；面试常要求优化到 O(n)。',
      '快慢指针：快指针遍历读源，慢指针指向下一个「应保留元素」的写入位；条件通常是「快指针指向的值不等于 val」。',
      '若题目允许打乱相对顺序，可用「相向双指针」：左找该删、右找可搬，减少搬移次数（仍要注意边界与计数）。',
      '返回值是「新长度」时，别忘了调用方只能信任前 newLength 个位置。',
    ],
    pitfalls: [
      '循环变量在删除后未回退或越界，导致漏删连续目标值。',
      '快慢指针语义没定义清楚：先写注释「慢指针表示什么」再写代码。',
    ],
    checklist: [
      '能解释为什么单次遍历足够：每个元素最多被快指针访问一次、被慢指针写入一次。',
      '能手写 27，并口头对比「保序」与「不保序」两种策略差异。',
    ],
    complexityHint: '快慢指针一次遍历 O(n)，额外 O(1) 空间。',
    main: { id: 27, title: '移除元素', slug: 'remove-element' },
    related: [
      { id: 26, title: '删除有序数组重复项', slug: 'remove-duplicates-from-sorted-array' },
      { id: 283, title: '移动零', slug: 'move-zeroes' },
      { id: 844, title: '比较含退格的字符串', slug: 'backspace-string-compare' },
    ],
  },
  {
    id: 'sorted-squares',
    title: '4. 有序数组的平方',
    subtitle: '利用「单调性在两端」：最大值只来自最左或最右。',
    difficulty: '基础',
    estMinutes: 25,
    keywords: ['非递减', '双指针', '从大到小填结果'],
    points: [
      '原数组按绝对值看，平方后最大值只可能出现在两端，不可能在中间「突然最大」。',
      '双指针 i=0、j=n-1，比较 `nums[i]²` 与 `nums[j]²`，较大者写入结果数组末尾，指针内移。',
      '「先平方再 sort」是 O(n log n) 对照组，帮助理解双指针 O(n) 的收益。',
      '注意负数与 0：左端负数平方后可能很大，不要凭直觉只盯右端。',
    ],
    pitfalls: [
      '结果数组方向写反：应从 `n-1` 往前填，否则破坏「从大到小」的填充顺序。',
    ],
    checklist: [
      '能手画「两端谁平方更大」的决策树，覆盖全负、全正、有零三种形状。',
    ],
    complexityHint: '双指针 O(n)；暴力平方 + 排序 O(n log n)。',
    main: { id: 977, title: '有序数组的平方', slug: 'squares-of-a-sorted-array' },
  },
  {
    id: 'min-subarray',
    title: '5. 长度最小的子数组（滑动窗口）',
    subtitle: '用「右扩左收」把平方暴力压成线性均摊。',
    difficulty: '进阶',
    estMinutes: 50,
    keywords: ['滑动窗口', '前缀和直觉', '正整数', '最短'],
    points: [
      '暴力枚举所有子区间 O(n²)；滑动窗口用右指针扩展累加，一旦满足条件就用左指针收缩求最短。',
      '本题常见前提是元素为正：和随窗口单调增，左指针收缩才安全；若含负数需换思路（如前缀和 + 单调队列/哈希）。',
      '复杂度直觉：每个元素最多被右指针纳入一次、被左指针弹出一次 → 均摊 O(n)。',
      '实现细节：`while` 收缩还是 `if` 一次，取决于「求最短」还是「求恰好」。',
    ],
    pitfalls: [
      '把 `for` 里套 `while` 一律当成 O(n²)：要看指针是否单调移动。',
      '忘记更新答案在收缩前还是后，导致漏掉「刚好等于边界」的窗口。',
    ],
    checklist: [
      '能口述「窗口内统计量是什么、何时扩、何时缩」。',
      '能手写 209，并用小例子走一遍左右指针移动顺序。',
    ],
    complexityHint: '正数数组 + 滑动窗口 O(n)；暴力 O(n²)。',
    main: { id: 209, title: '长度最小的子数组', slug: 'minimum-size-subarray-sum' },
    related: [
      { id: 904, title: '水果成篮', slug: 'fruit-into-baskets' },
      { id: 76, title: '最小覆盖子串', slug: 'minimum-window-substring' },
    ],
  },
  {
    id: 'spiral',
    title: '6. 螺旋矩阵 II',
    subtitle: '模拟题的灵魂：统一转角规则，少写特殊分支。',
    difficulty: '基础',
    estMinutes: 45,
    keywords: ['模拟', '顺时针', '左闭右开', 'offset'],
    points: [
      '按圈模拟：上→右→下→左；每一圈缩小边界（`start`、`offset` 控制）。',
      '坚持「每条边同一种开闭区间」例如左闭右开，拐角不重复填，能显著减少 off-by-one。',
      'n 为奇数时中心单独赋值；n 为 1 时整圈循环可能为 0，注意别漏中心。',
      '可先在纸上标号再走代码，比直接写四重循环更稳。',
    ],
    pitfalls: [
      '四条边循环长度不一致：某一向少写或多写一格导致整体错位。',
      '内层循环变量复用导致起始行列在下一圈未正确递增。',
    ],
    checklist: [
      '能手画 n=4 与 n=5 的填充顺序，并标出每一圈的起止下标。',
    ],
    complexityHint: '填 n² 个格子 → 时间 O(n²)，空间 O(1) 额外（不计结果矩阵）。',
    main: { id: 59, title: '螺旋矩阵 II', slug: 'spiral-matrix-ii' },
    related: [{ id: 54, title: '螺旋矩阵', slug: 'spiral-matrix' }],
  },
  {
    id: 'summary',
    title: '7. 数组篇小结',
    subtitle: '把「题型」收束成几条可迁移的思想线。',
    difficulty: '入门',
    estMinutes: 20,
    keywords: ['复盘', '迁移', '面试'],
    points: [
      '二分：本质是分治在有序结构上的特例，核心是区间与不变量，不是背模板。',
      '双指针：同向（快慢）擅长原地筛选；相向擅长两端决策（如平方、两数之和类）。',
      '滑动窗口：双指针 + 窗口统计量，适合「连续子数组 / 子串」最值或可行性判定。',
      '模拟：代码量比想法长，用统一边界规则换更少的 if-else。',
      '下一篇链表起，指针语义会更绕，建议把数组里的「下标不变量」迁移成「指针不变量」。',
    ],
    checklist: [
      '能用自己的话给同学讲一遍：二分两种区间、快慢指针、滑动窗口三问。',
      '从本节主刷题里各挑一题，限时 15 分钟内独立 AC。',
    ],
    complexityHint: '数组篇整体以 O(n) 与 O(log n) 为主干，面试追问时常回到「为何不能再优」。',
  },
]

export function leetcodeCnUrl(slug: string) {
  return `https://leetcode.cn/problems/${slug}/`
}

export const ARRAY_SECTIONS = applyArrayEnrichment(ARRAY_SECTIONS_RAW)

export const ARRAY_SECTION_COUNT = ARRAY_SECTIONS.length
