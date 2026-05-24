/** 哈希表学习模块 — 知识结构 */

import type { LearnTopicBlock } from '@/modules/shared/learningTypes'
import { mergeEnrichment } from '@/modules/shared/sectionEnrichment'
import { HASH_TABLE_ENRICHMENT } from './hashTableEnrichment'

export interface PracticeLink {
  id: number
  title: string
  slug: string
}

/** 章节类型：用于侧栏标签与学习节奏提示 */
export type HashSectionKind = 'theory' | 'practice' | 'two-pointers' | 'summary'

export interface HashTableSection {
  id: string
  /** 侧栏与进度条展示的短标题 */
  menuLabel: string
  /** 正文大标题（与 章节名一致） */
  title: string
  kind: HashSectionKind
  /** 一句话目标，显示在卡片副标题 */
  goal: string
  points: string[]
  overview?: string
  topicBlocks?: LearnTopicBlock[]
  main?: PracticeLink
  related?: PracticeLink[]
  /** 复杂度或实现提示（可选） */
  complexity?: string
}

function applyHashTableSectionEnrichment(sections: HashTableSection[]): HashTableSection[] {
  const merged = mergeEnrichment(
    sections.map((s) => ({
      id: s.id,
      title: s.title,
      subtitle: s.goal,
      difficulty: '基础' as const,
      estMinutes: 25,
      keywords: [] as string[],
      points: s.points,
      overview: s.overview,
      topicBlocks: s.topicBlocks,
    })),
    HASH_TABLE_ENRICHMENT,
  )
  return sections.map((s, i) => ({
    ...s,
    overview: merged[i]?.overview ?? s.overview,
    topicBlocks: merged[i]?.topicBlocks ?? s.topicBlocks,
    points: merged[i]?.points ?? s.points,
  }))
}

/** C++/Java 系容器选型速查（「常见的三种哈希结构」主线） */
export const HASH_STRUCTURE_GUIDE: {
  structure: string
  scene: string
  pros: string
  examples: string
}[] = [
  {
    structure: '定长数组作计数表',
    scene: 'key 值域小且连续（如 26 个小写字母、0–1000 内整数），可直接当下标用。',
    pros: '实现简单、常数小；不依赖哈希函数开销。',
    examples: '242、383；数据范围收紧后的 349。',
  },
  {
    structure: '哈希集合 unordered_set / HashSet',
    scene: '只需判断「是否出现过」、要去重，且 key 分散或范围很大。',
    pros: '均摊 O(1) 查询/插入；无需预知值域上界。',
    examples: '349（通用做法）、202（记录出现过的和）。',
  },
  {
    structure: '哈希映射 unordered_map / HashMap',
    scene: '除了「是否存在」，还要存「另一个属性」：下标、出现次数、前缀和等。',
    pros: 'key→value 一体；适合两数之和、四数相加 II 这类「配对信息」问题。',
    examples: '1（值→下标）、454（和→次数）。',
  },
]

/** 易混题对照：需注意 454 与 15/18 模板差异 */
export const HASH_VS_TWOPOINTERS_COMPARE: {
  dimension: string
  fourSumIi: string
  threeOrFourSum: string
}[] = [
  {
    dimension: '数据形态',
    fourSumIi: '四个独立数组，下标各自组合。',
    threeOrFourSum: '同一数组中选不重复元组。',
  },
  {
    dimension: '去重',
    fourSumIi: '无需对「四元组」去重。',
    threeOrFourSum: '必须去重，双指针写法更稳。',
  },
  {
    dimension: '主流解法',
    fourSumIi: '枚举 AB 和 → map；再枚举 CD 查相反数。',
    threeOrFourSum: '排序 + 双指针（推荐）。',
  },
]

export const HASH_TABLE_CURRICULUM_INTRO =
  '哈希表的核心用途是「快速判断某元素是否出现在集合里」：用额外空间换查询时间。本章按顺序：先建立数组 / 集合 / 映射三种载体的直觉，再掌握经典哈希题，最后对照 15、18 理解「何时不用哈希」。'

const HASH_TABLE_SECTIONS_RAW: HashTableSection[] = [
  {
    id: 'theory',
    menuLabel: '1 理论基础',
    title: '1. 哈希表理论基础',
    kind: 'theory',
    goal: '搞清何时用哈希、用什么容器承载，以及碰撞在刷题语境下的直觉。',
    points: [
      '哈希表根据关键码直接访问数据；数组可视为最简单的哈希表（下标即 key）。',
      '典型场景：需要 O(1) 判断「是否出现过」——朴素枚举是 O(n)，哈希查找均摊 O(1)。',
      '哈希函数：把任意 key 映射为表索引；若索引越界，常配合取模落在表长范围内。',
      '哈希碰撞：多个 key 落到同一索引；常见处理为拉链法（链表挂桶）与线性探测法（向后找空位）；线性探测一般要求表长大于数据量。',
      '刷题三件套：定长数组、set（集合）、map（映射）。C++ 的 unordered_*、Java 的 HashMap/HashSet 等底层为哈希时，增删查均摊 O(1)；有序树实现（如 std::map）则是 O(log n)，题中不需要有序时优先无序哈希表。',
      '空间代价：用额外结构存访问痕迹，本质是空间换时间；值域可控且连续时，小数组往往比通用 map 更省常数。',
    ],
    complexity: '平均 O(1) 查询与插入；最坏因碰撞退化，面试写题通常按均摊理解即可。',
  },
  {
    id: 'valid-anagram',
    menuLabel: '2 有效的字母异位词',
    title: '2. 有效的字母异位词',
    kind: 'practice',
    goal: '掌握「小写字母 → 长度 26 计数数组」这一最朴素的哈希形态。',
    points: [
      '暴力：两层循环配合标记，约 O(n²)；字母异位词本质是「 multiset 相等」。',
      '题目限定小写英文字母：开 int[26]，先对 s 做 ++，再对 t 做 --，全零则 true。',
      '映射规则：不记绝对 ASCII，用 s[i] - \'a\' 得到 0…25 的相对下标即可。',
      '若字符种类多、跨度极大（如任意 Unicode），再改用 map 或 sort 对比。',
    ],
    main: { id: 242, title: '有效的字母异位词', slug: 'valid-anagram' },
    related: [
      { id: 383, title: '赎金信', slug: 'ransom-note' },
      { id: 49, title: '字母异位词分组', slug: 'group-anagrams' },
    ],
    complexity: '时间 O(n)，空间 O(1)（26 为常数）。',
  },
  {
    id: 'intersection',
    menuLabel: '3 两个数组的交集',
    title: '3. 两个数组的交集',
    kind: 'practice',
    goal: '学会在「值域未知」时用集合完成存在性判断与结果去重。',
    points: [
      '输出要求每个值唯一、顺序不限 → 用集合表达「是否出现」最自然。',
      '值域未事先收紧时，不宜开「以元素值为下标」的巨大数组；unordered_set 更合适。',
      '常见流程：把一个数组放入 set，遍历另一个数组，命中则插入结果 set，最后转回数组。',
      '补充说明：力扣加强数据范围后，若元素落在有界小区间（如 0–1000），也可用定长数组标记是否出现，时空常为 O(m+n)。',
      '拓展思考：unordered_set 比数组多哈希计算与节点开销；能数组时不必盲目 set。',
    ],
    main: { id: 349, title: '两个数组的交集', slug: 'intersection-of-two-arrays' },
    related: [{ id: 350, title: '两个数组的交集 II', slug: 'intersection-of-two-arrays-ii' }],
    complexity: '典型 O(m+n) 时间与 O(m+n) 辅助空间（结果集规模相关）。',
  },
  {
    id: 'happy-number',
    menuLabel: '4 快乐数',
    title: '4. 快乐数',
    kind: 'practice',
    goal: '把「可能无限循环」转译为「和是否重复出现」，练习 set 判环。',
    points: [
      '快乐数定义：反复替换为各位数字平方和，最终到 1 为真；否则可能永远循环不到 1。',
      '关键句：循环过程中 sum 会重复 → 一旦重复即可判 false，这是哈希法的直接动机。',
      '实现：unordered_set 记录出现过的 sum；每次算新 sum，为 1 返回 true，已见过返回 false。',
      '辅助函数 getSum(n)：while(n){ sum+=(n%10)^2; n/=10; }，注意整数运算不要写错幂次。',
    ],
    main: { id: 202, title: '快乐数', slug: 'happy-number' },
    complexity: '时间与空间约为 O(log n) 量级（与数位迭代及出现过的和的规模相关，常见写法如此归纳）。',
  },
  {
    id: 'two-sum',
    menuLabel: '5 两数之和',
    title: '5. 两数之和',
    kind: 'practice',
    goal: '第一次系统使用 map：既要「存在」又要「另一个属性——下标」。',
    points: [
      '暴力两重循环 O(n²)；优化目标是「遍历到 x 时，O(1) 知道 target-x 是否在之前出现过」。',
      '数组哈希受值域与稀疏性限制；set 只能存一个 key，无法同时放下标。',
      'unordered_map：key 为「已经遍历过的元素值」，value 为其下标；当前 nums[i] 查找 complement = target - nums[i]。',
      '遍历顺序：先查 map 再插入当前值，避免同一元素用两次（除非题目允许）。',
      '自检四问自检：为何哈希、为何 map、map 存什么、key/value 各是什么——能口述才算过关。',
    ],
    main: { id: 1, title: '两数之和', slug: 'two-sum' },
    related: [{ id: 167, title: '两数之和 II - 输入有序数组', slug: 'two-sum-ii-input-array-is-sorted' }],
    complexity: '时间 O(n)，空间 O(n)。',
  },
  {
    id: 'four-sum-ii',
    menuLabel: '6 四数相加 II',
    title: '6. 四数相加 II',
    kind: 'practice',
    goal: '用 map 统计「两数之和」的出现次数，体会与 15/18 的本质差别。',
    points: [
      '四组独立数组：只要下标组合使和为 0 即计数，不必对四元组去重，和单数组四数之和完全不同。',
      '步骤：枚举 A、B，将 a+b 作为 key 记入 map，value 为出现次数；再枚举 C、D，查 -(c+d) 是否在 map，累加对应次数。',
      '与 15/18 对比：后者在同一数组上选不重复元组，用哈希做去重很难写且不讨好；推荐双指针 + 排序。',
      '若把本题升级为「单数组四元组不重复」，难度接近 18，需要另一套模板。',
    ],
    main: { id: 454, title: '四数相加 II', slug: '4sum-ii' },
    complexity: '时间 O(n²)，最坏空间 O(n²)（不同 a+b 个数）。',
  },
  {
    id: 'ransom-note',
    menuLabel: '7 赎金信',
    title: '7. 赎金信',
    kind: 'practice',
    goal: '巩固「计数数组」相对 map 在常数与实现上的优势。',
    points: [
      '题意：ransomNote 能否由 magazine 中字符拼出，每个杂志字符最多用一次；均为小写字母。',
      '先统计 magazine 各字符频次，再遍历 ransom 做减法，任一位置 <0 即失败。',
      '与 242 区别：242 判断双向 multiset 是否一致；383 只要求「magazine 是否覆盖 ransom」。',
      '注意：map 也能过，但在小字母表上数组更简单、常数更小；不要「万物 map」。',
    ],
    main: { id: 383, title: '赎金信', slug: 'ransom-note' },
    complexity: '时间 O(m+n)，空间 O(1)（26）。',
  },
  {
    id: 'three-sum',
    menuLabel: '8 三数之和',
    title: '8. 三数之和',
    kind: 'two-pointers',
    goal: '理解「不重复三元组」下去重的难点，掌握排序 + 双指针主解。',
    points: [
      '目标：a+b+c=0 的所有不重复三元组；暴力 O(n³) 且去重难写。',
      '哈希思路：两层枚举 + 第三数在集合里查，理论上可到 O(n²)，但去重极易超时或漏判，面试不友好。',
      '推荐：排序后固定 i，left=i+1，right=n-1，根据和与 0 比较移动指针；找到一组解后，左右指针都要跳过重复值。',
      'a 的去重：比较 nums[i] 与 nums[i-1]（与前一个比较），避免误杀合法重复如 [-1,-1,2]。',
      '思考题：若两数之和要求返回原下标，则不能用「先排序再双指针」，因为下标会被打乱。',
    ],
    main: { id: 15, title: '三数之和', slug: '3sum' },
    related: [{ id: 18, title: '四数之和', slug: '4sum' }],
    complexity: '双指针主解时间 O(n²)，空间 O(1)（不含输出）。',
  },
  {
    id: 'four-sum',
    menuLabel: '9 四数之和',
    title: '9. 四数之和',
    kind: 'two-pointers',
    goal: '在 15 题模板上套第二层循环，并处理一般 target 与溢出、剪枝。',
    points: [
      '两层 for 固定 k、i，内层 left/right 双指针，使四数和等于 target；整体 O(n³)。',
      '剪枝陷阱：不能简单 if(nums[k]>target) break，因 target 可能为负；可结合符号的更稳妥剪枝。',
      '比较四数和与 target 时用 long 或等价类型，避免 int 溢出。',
      'k、i、left、right 四层去重逻辑与 15 题一脉相承，建议对着「排序 + 双指针」模板默写。',
      '与 454 再次对照：本题同数组、要去重；454 四数组、计数即可。',
    ],
    main: { id: 18, title: '四数之和', slug: '4sum' },
    complexity: '时间 O(n³)，空间 O(1)（不含输出）。',
  },
  {
    id: 'summary',
    menuLabel: '10 总结篇',
    title: '10. 哈希表总结篇',
    kind: 'summary',
    goal: '把「何时数组 / set / map」与「454 vs 15/18」收束成可复述的面试话术。',
    points: [
      '一句话：遇到「是否出现过」「是否在某集合里」优先考虑哈希；接受额外空间。',
      '数组哈希：值域小且连续；典型 242、383，及范围收紧后的 349。',
      'set：值域大或未知、只要 key、要自动去重；典型 349、202。',
      'map：需要 key 关联 value（下标、次数、前缀等）；典型 1、454。',
      '454 与 15/18：前者四独立数组 + map 计数；后者单数组不重复元组 + 排序双指针——模板不要混用。',
      '刷题后自检：能否向面试官解释「为何不用数组/set」以及「map 里 key、value 各代表什么」。',
    ],
  },
]

export const HASH_TABLE_SECTIONS = applyHashTableSectionEnrichment(HASH_TABLE_SECTIONS_RAW)

export function leetcodeCnUrl(slug: string) {
  return `https://leetcode.cn/problems/${slug}/`
}

export const HASH_SECTION_IDS = HASH_TABLE_SECTIONS.map((s) => s.id)
