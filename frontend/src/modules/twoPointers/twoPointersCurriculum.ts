/**
 * 双指针学习模块 — 知识结构
 * 与双指针篇章节顺序一致。
 * 正文为平台侧要点串联；完整题解、动图与多语言实现学习资料以平台讲解与正版资料为准。
 */

import type { LearnSection } from '@/modules/shared/learningTypes'
import { applyTwoPointersEnrichment } from './twoPointersEnrichment'

export type DifficultyLabel = LearnSection['difficulty']
export type PracticeLink = NonNullable<LearnSection['main']>

export type TwoPointerKind = 'fast-slow' | 'opposite' | 'sorted-lr' | 'mixed'

export interface TwoPointersSection extends LearnSection {
  /** 本节主要双指针形态，便于侧栏与总结对照 */
  pointerKind?: TwoPointerKind
}

/** 三种双指针形态速查（对应 总结篇） */
export const TWO_POINTER_PATTERN_GUIDE: {
  pattern: string
  when: string
  move: string
  examples: string
}[] = [
  {
    pattern: '快慢指针（同向）',
    when: '原地筛选、覆盖写入；链表判环、求倒数第 k 个的前驱。',
    move: '快指针探路，慢指针落位或保持间距；一个 for 完成两层扫描。',
    examples: '27、283；19、141/142。',
  },
  {
    pattern: '相向指针（对撞）',
    when: '有序数组两端决策；对称交换；不要求保序的覆盖删除。',
    move: 'left 从首、right 从尾向中间逼近，按比较结果移动一侧。',
    examples: '344、977；27 相向版；15/18 的内层。',
  },
  {
    pattern: '排序 + 左右指针',
    when: '在同一数组上找不重复 k 元组且和为定值；需配合去重剪枝。',
    move: '外层固定若干元素，内层 left/right 收拢；找到答案后再去重收缩。',
    examples: '15、18；可推广到 N 数之和 O(n^(k-1))。',
  },
]

/** 哈希 vs 双指针：本节 454 与 15/18、1 与 15 的对照 */
export const HASH_VS_TWO_POINTERS_COMPARE: {
  dimension: string
  hashSide: string
  twoPointerSide: string
}[] = [
  {
    dimension: '两数之和（返回下标）',
    hashSide: 'map 存「值→下标」，一遍 O(n)。',
    twoPointerSide: '先排序会打乱下标，不适用；若只要求数值可用排序+对撞。',
  },
  {
    dimension: '三数 / 四数之和（同数组、不重复元组）',
    hashSide: '放进 vector 再去重，费时易超时，剪枝弱。',
    twoPointerSide: '排序 + 双指针为主流；去重与剪枝可控，面试更稳。',
  },
  {
    dimension: '四数相加 II（四个独立数组）',
    hashSide: '枚举 AB 和入 map，再扫 CD 查 target-sum，推荐。',
    twoPointerSide: '无「同数组去重」负担，不必强行双指针。',
  },
]

export const TWO_POINTERS_CURRICULUM_INTRO =
  '双指针不是某一种数据结构专属的技巧：数组上可原地覆盖或两端夹逼，字符串上常配合从后往前填充，链表上是快慢相遇或对齐长度，有序数组上则是排序后 left/right 收拢。本篇按双指针 顺序串起 9 道经典题与总结，建议每节先明确「快/慢、左/右各代表什么」，再结合本节动图手敲一遍。'

const TWO_POINTERS_SECTIONS_RAW: TwoPointersSection[] = [
  {
    id: 'theory',
    title: '0. 双指针法怎么学',
    subtitle: '先分清三种形态与适用场景，再进具体题型。',
    difficulty: '入门',
    estMinutes: 20,
    keywords: ['快慢', '相向', '排序+左右', 'O(n)', '循环不变量'],
    points: [
      '核心收益：常常把 O(n²) 的双重循环压成 O(n)，或在 O(n²) 框架下获得更小常数与更强剪枝（如 15/18）。',
      '快慢（同向）：快指针负责「探路 / 找新数组元素」，慢指针指向「下一个写入位置」——27 题的经典定义。',
      '相向（对撞）：left、right 从两端向中间，适合有序和、平方、对称反转；若允许打乱相对顺序，27 也可用相向减少搬移。',
      '排序 + 左右：外层枚举固定元素，内层 left/right 根据与 target 的大小关系移动；三数之和、四数之和的模板。',
      '链表双指针：间距刻画「倒数」、快慢判环、对齐长度找相交；与数组双指针「语义」相同，实现落在 next 上。',
      '书写习惯：写清每个指针的循环不变量；避免在 for 下随意 erase 导致 O(n²)（在字符串去空格处强调）。',
    ],
    pitfalls: [
      '不区分「比较 val」与「比较结点地址」：相交、环入口题必须是指针同一引用。',
      '三数之和去重时比较 nums[i] 与 nums[i+1]，会漏掉 [-1,-1,2] 这类合法三元组。',
    ],
    checklist: [
      '能用自己的话说明快慢、相向、排序+左右三种写法各解决哪类问题。',
      '能解释为何「填充类字符串题」常从后往前双指针写才是 O(n)。',
    ],
    complexityHint: '单指针扫描 O(n)；相向/快慢同层循环 O(n)；三数之和 O(n²)，四数之和 O(n³)。',
  },
  {
    id: 'remove-element',
    title: '1. 移除元素',
    subtitle: '快慢覆盖是数组双指针第一课；相向版在允许乱序时减少交换次数。',
    difficulty: '基础',
    pointerKind: 'fast-slow',
    estMinutes: 40,
    keywords: ['27', '快慢指针', '相向', '原地', '覆盖'],
    points: [
      '题意：原地删除等于 val 的元素，返回新长度；超出新长度的尾部元素无需关心。',
      '数组不能真删，只能覆盖；暴力两层 for 搬移是 O(n²)，面试应优先双指针 O(n)。',
      '快慢写法：fast 扫描全表，若 nums[fast]!=val 则 nums[slow++]=nums[fast]；保持相对顺序不变。',
      '相向写法：left 找等于 val，right 找不等于 val，交换覆盖；会改变相对顺序，但移动元素更少（相向写法代码）。',
      '相关套路：26 去重、283 移动零、844 含退格比较、977 有序平方——都可归入双指针族。',
    ],
    pitfalls: [
      '慢指针含义不清：它是「下一个写入下标」，返回时即新长度。',
      '相向写法循环条件 left<=right 与最后 return left 的边界要手画一遍。',
    ],
    checklist: [
      '能手写快慢版并说明时间 O(n)、空间 O(1)。',
      '能对比「保序」与「最少移动」两种写法的取舍。',
    ],
    complexityHint: '快慢 / 相向均为 O(n) 时间、O(1) 额外空间。',
    main: { id: 27, title: '移除元素', slug: 'remove-element' },
    related: [
      { id: 26, title: '删除有序数组中的重复项', slug: 'remove-duplicates-from-sorted-array' },
      { id: 283, title: '移动零', slug: 'move-zeroes' },
      { id: 844, title: '比较含退格的字符串', slug: 'backspace-string-compare' },
      { id: 977, title: '有序数组的平方', slug: 'squares-of-a-sorted-array' },
    ],
  },
  {
    id: 'reverse-string',
    title: '2. 反转字符串',
    subtitle: '相向指针交换对称位置；理解原理比背 reverse 库函数更重要。',
    difficulty: '基础',
    pointerKind: 'opposite',
    estMinutes: 25,
    keywords: ['344', '相向', 'swap', '原地'],
    points: [
      '题意：原地反转字符数组，O(1) 额外空间；字符串在内存中连续，类似数组。',
      '定义 i=0、j=n-1，向中间移动并交换 s[i]、s[j]，直到 i>=j。',
      '关于库函数的原则：关键步骤若一行库函数搞定，面试不宜依赖；swap 作为辅助且你理解实现时可用。',
      '与 206 反转链表对照：链表改 next，字符串改下标交换，难度更低，是双指针入门。',
    ],
    pitfalls: [
      '循环条件写成 i<j 与 i<=j 在奇偶长度上的差异要统一一种写法。',
      'Java 字符串不可变，力扣 344 给的是 char[]，勿与 String 混淆。',
    ],
    checklist: [
      '能不用库函数手写交换；能口述 O(n) 时间、O(1) 空间。',
    ],
    complexityHint: '时间 O(n)，空间 O(1)。',
    main: { id: 344, title: '反转字符串', slug: 'reverse-string' },
  },
  {
    id: 'replace-space',
    title: '3. 替换空格（剑指 Offer 05）',
    subtitle: '先扩容再从后往前填：填充类问题的双指针模板。',
    difficulty: '基础',
    pointerKind: 'opposite',
    estMinutes: 35,
    keywords: ['剑指05', '从后往前', '扩容', '%20'],
    points: [
      '若允许辅助空间，题很简单；极致做法：统计空格数 → resize 到 oldSize+2*count → 双指针从尾部填充。',
      'i 指向新串末尾，j 指向旧串末尾；非空格则 s[i--]=s[j--]，空格则依次写入 \'0\'、\'2\'、\'%\' 并 i-=2。',
      '从前向后填每次插入都要后移后续字符，整体 O(n²)；从后向前每个字符只写一次，O(n)。',
      '至此：到本节已完成多道双指针题（27、15、18、206、142、344 等），说明技巧跨结构通用。',
    ],
    pitfalls: [
      '未先扩容就写，或 i、j 初值不是 newSize-1 / oldSize-1。',
      'C++ resize 后 string 可写；Java 需 StringBuilder 或 char 数组思维。',
    ],
    checklist: [
      '能解释「为何填充类常从后往前」并套用到 151 去空格。',
    ],
    complexityHint: '时间 O(n)，空间 O(1)（不计扩容占用的原地额外槽位）。',
    main: { id: 5, title: '替换空格（剑指 Offer 05）', slug: 'replace-space-lcof' },
  },
  {
    id: 'reverse-words',
    title: '4. 翻转字符串里的单词',
    subtitle: '去冗余空格 O(n) + 整体反转 + 逐词反转；综合字符串双指针。',
    difficulty: '进阶',
    pointerKind: 'mixed',
    estMinutes: 55,
    keywords: ['151', '快慢去空格', '整体反转', '单词反转'],
    points: [
      '要求 O(1) 空间则必须在原串操作：先压缩空格，再 reverse 全串，再对每个单词 reverse 区间。',
      '去空格：快慢指针类似 27——遇非空格写入，单词间手动补一个空格；勿在 for 里 erase，否则 O(n²)。',
      '整体反转后单词内字符也反了，再对每个 [start, end] 区间做一次相向交换即可复原单词。',
      '示例："the sky is blue" → 去空格 → 全串反转 → 逐词反转 → "blue is sky the"。',
    ],
    pitfalls: [
      '用 split+新串 虽能 AC 但不符合 O(1) 空间题意。',
      '单词边界：在 i==size 或 s[i]==\' \' 时反转 [start, i-1]。',
    ],
    checklist: [
      '能手写 removeExtraSpaces 的精简版（精简版二）并接双段 reverse。',
    ],
    complexityHint: '时间 O(n)，空间 O(1)（语言允许原地修改时）。',
    main: { id: 151, title: '反转字符串中的单词', slug: 'reverse-words-in-a-string' },
  },
  {
    id: 'reverse-list',
    title: '5. 反转链表',
    subtitle: '双指针改 next：pre/cur/temp 三指针迭代是现场手写高频。',
    difficulty: '基础',
    pointerKind: 'fast-slow',
    estMinutes: 45,
    keywords: ['206', 'pre', 'cur', '递归', 'O(1)'],
    points: [
      '不新建链表，只改 next 指向；pre 初 null，cur 从 head 出发，每轮保存 cur.next 再 cur->next=pre，然后 pre、cur 右移。',
      '递归与双指针本质相同：子问题 reverseList(head->next)，再把 head 接到新尾后面。',
      '拓展：虚结点+头插、栈弹出再接——帮助理解，面试优先迭代 O(1) 空间。',
    ],
    pitfalls: [
      '未保存 cur->next 就改写 next，丢链。',
      '返回 pre 而非 cur（循环结束时 cur 为 null）。',
    ],
    checklist: [
      '能在白纸上一遍写出迭代版；能说明与 344 反转的异同。',
    ],
    complexityHint: '迭代 O(n) 时间 O(1) 空间；递归 O(n) 栈空间。',
    main: { id: 206, title: '反转链表', slug: 'reverse-linked-list' },
  },
  {
    id: 'remove-nth-from-end',
    title: '6. 删除链表的倒数第 N 个节点',
    subtitle: '快指针先走 n+1 步，再与慢指针同速；配合 dummy 一趟删除。',
    difficulty: '基础',
    pointerKind: 'fast-slow',
    estMinutes: 40,
    keywords: ['19', 'dummy', 'n+1', '一趟'],
    points: [
      '删除倒数第 n 个 = 让 slow 停在待删结点的前驱；故 fast 从 dummy 先走 n+1 步。',
      '然后 fast、slow 同步前进直到 fast==null，执行 slow->next = slow->next->next。',
      '进阶要求一趟扫描；不用 dummy 则要单独处理删头。',
    ],
    pitfalls: [
      '快指针只走 n 步会导致 slow 指向待删结点本身而非前驱。',
      'while 未判断 fast->next 就访问 fast->next->next。',
    ],
    checklist: [
      '能手画 n=表长（删头）与 n=1（删尾）两种情形。',
    ],
    complexityHint: 'O(n) 时间，O(1) 空间。',
    main: { id: 19, title: '删除链表的倒数第 N 个结点', slug: 'remove-nth-node-from-end-of-list' },
  },
  {
    id: 'intersection',
    title: '7. 面试题 02.07 · 链表相交',
    subtitle: '对齐长度后同速前进；或交替拼接两链消去长度差。',
    difficulty: '基础',
    pointerKind: 'fast-slow',
    estMinutes: 35,
    keywords: ['160', '长度差', '指针相等'],
    points: [
      '相交指结点引用相同，不是 val 相等；从相交点起两链尾部完全共用。',
      '求 lenA、lenB，长链 cur 先走 |lenA-lenB| 步，再与短链头同步后移，第一次相等即交点。',
      '写法二：A 走完接 headB，B 走完接 headA，两指针同速，相遇即交点（无交则同抵 null）。',
    ],
    pitfalls: [
      '交换长度与头指针时弄混 curA/curB。',
    ],
    checklist: [
      '能口述 O(m+n) 时间与 O(1) 空间的一种实现。',
    ],
    complexityHint: '时间 O(m+n)，空间 O(1)。',
    main: { id: 160, title: '相交链表', slug: 'intersection-of-two-linked-lists' },
  },
  {
    id: 'cycle',
    title: '8. 环形链表 II',
    subtitle: '快慢相遇判环；头指针与相遇点同速走，相遇处为入口。',
    difficulty: '进阶',
    pointerKind: 'fast-slow',
    estMinutes: 55,
    keywords: ['142', '141', '入口', 'x+y'],
    points: [
      'fast 每次两步、slow 一步；有环必在环上相遇，无环则 fast 先到 null。',
      '设头到入口 x，入口到相遇 y，相遇回到入口 z；相遇时 2(x+y)=x+y+n(y+z)，化简得 x=(n-1)(y+z)+z，n=1 时 x=z。',
      '相遇后 index1 从相遇点、index2 从 head 同速走，再相遇即环入口；n>1 只是多绕圈，入口不变。',
      '141 只判是否有环；142 要返回入口结点。',
    ],
    pitfalls: [
      'while 条件须 fast && fast->next，否则空指针。',
      '误以为 slow 第一次相遇路程是 x+多圈而不敢用 x+y 等式（补充证明可读）。',
    ],
    checklist: [
      '能手写 detectCycle 并口述 x=z 的直觉（走一圈路程对齐）。',
    ],
    complexityHint: '时间 O(n)，空间 O(1)。',
    main: { id: 142, title: '环形链表 II', slug: 'linked-list-cycle-ii' },
    related: [{ id: 141, title: '环形链表', slug: 'linked-list-cycle' }],
  },
  {
    id: 'three-sum',
    title: '9. 三数之和',
    subtitle: '排序 + 固定 i + left/right；去重细节决定能否 AC。',
    difficulty: '进阶',
    pointerKind: 'sorted-lr',
    estMinutes: 60,
    keywords: ['15', '排序', '去重', '剪枝'],
    points: [
      '哈希可做但去重难、剪枝弱；面试推荐 sort 后 i 固定，left=i+1、right=n-1 收拢。',
      '和>0 则 right--；和<0 则 left++；等于 0 则收录并同时收缩 left/right，且跳过重复 left/right。',
      '去重 a：比较 nums[i] 与 nums[i-1]（i>0），勿与 nums[i+1] 比，否则漏 [-1,-1,2]。',
      '去重 b/c 放在找到答案之后；和>0 时 nums[i]>0 可直接 break。',
      '思考题：两数之和若返回下标不能排序双指针；若返回数值则可以。',
    ],
    pitfalls: [
      '在 while 开头对 left/right 去重可能导致 right<=left 漏解 0,0,0。',
      '提前对 right 去重并不减少比较次数，通常可省略。',
    ],
    checklist: [
      '能默写主框架并解释三处去重为何这样写。',
    ],
    complexityHint: '时间 O(n²)，空间 O(1)（不计输出）。',
    main: { id: 15, title: '三数之和', slug: '3sum' },
  },
  {
    id: 'four-sum',
    title: '10. 四数之和',
    subtitle: '在三数之和外再套一层 k；剪枝勿照搬「nums[i]>0」到任意 target。',
    difficulty: '进阶',
    pointerKind: 'sorted-lr',
    estMinutes: 50,
    keywords: ['18', '四层去重', '溢出', '剪枝'],
    points: [
      '两层 for 固定 k、i，内层 left/right，和与 target 比较；整体 O(n³)。',
      '不能因 nums[k]>target 就 break（如全负数 target=-10）；可用 nums[k]>target && nums[k]>=0 等条件。',
      '二级剪枝：nums[k]+nums[i]>target 且二者同号时可 break 内层 i 循环。',
      '找到答案后对 left、right 做与 15 题相同的去重收缩；注意 long 防溢出。',
      'N 数之和：继续外层 for + 最内层双指针，复杂度 O(n^(N-1))。',
    ],
    pitfalls: [
      '与 454 四数相加 II 混淆：后者四数组 + 哈希，无同数组去重问题。',
    ],
    checklist: [
      '能说明 18 与 15 模板差异仅在多一层枚举与剪枝条件。',
    ],
    complexityHint: '时间 O(n³)，空间 O(1)（不计输出）。',
    main: { id: 18, title: '四数之和', slug: '4sum' },
  },
  {
    id: 'summary',
    title: '11. 双指针总结篇',
    subtitle: '按数组 / 字符串 / 链表 / N 数之和四条线复盘全书九题。',
    difficulty: '入门',
    estMinutes: 30,
    keywords: ['复盘', '九题', '降复杂度', '模板'],
    points: [
      '数组：27 快慢/相向覆盖；不要用 for+erase O(n²)。',
      '字符串：344 相向交换；剑指05/151 从后往前或快慢压缩+区间反转；填充与去空格都怕 erase。',
      '链表：206 改 next；19 间距快慢；160 对齐；142 快慢+入口二次相遇——链表题常「必用」双指针。',
      'N 数之和：15/18 排序+双指针优于哈希去重；454 仍用哈希。',
      '本章九题：27、15、18、206、19、160、142、344 + 字符串系列；掌握后同类题多为变体。',
      '练习建议：每类挑一题限时手写，再结合本节视频与动图补直觉。',
    ],
    pitfalls: [
      '动画需上  查看；本站提供结构梳理与示意动画。',
    ],
    checklist: [
      '能按「快慢 / 相向 / 排序+左右」各举 2 道题名。',
      '能说明双指针将哪类暴力从 O(n²) 降到 O(n) 或 O(n²) 可剪枝。',
    ],
    complexityHint: '多数题为 O(n) 或 O(n²)/O(n³) 配合排序；额外空间多为 O(1)。',
  },
]

export function leetcodeCnUrl(slug: string) {
  return `https://leetcode.cn/problems/${slug}/`
}

export const TWO_POINTERS_SECTIONS = applyTwoPointersEnrichment(TWO_POINTERS_SECTIONS_RAW)

export const TWO_POINTERS_SECTION_COUNT = TWO_POINTERS_SECTIONS.length
