/**
 * 链表学习模块 — 知识结构
 * 与链表篇目录顺序一致，便于延伸阅读与动图。
 * 正文为平台侧要点串联；完整题解、示意图与多语言实现学习资料以平台讲解与正版资料为准。
 */

import type { LearnSection } from '@/modules/shared/learningTypes'
import { applyLinkedListEnrichment } from './linkedListEnrichment'

export type LinkedListSection = LearnSection
export type DifficultyLabel = LearnSection['difficulty']
export type PracticeLink = NonNullable<LearnSection['main']>

export const LINKED_LIST_CURRICULUM_INTRO =
  '链表与数组相反：结点分散在内存中，通过指针串联，插入删除在已知前驱时多为 O(1)，但失去随机访问；面试高频集中在虚拟头结点、反转、快慢指针、相交与环形等套路的统一写法。建议每节先画图再写码，再结合本节题解查漏补缺。动画与多语言实现请配合平台讲解；ACM 模式可配合练习。'

const LINKED_LIST_SECTIONS_RAW: LinkedListSection[] = [
  {
    id: 'theory',
    title: '1. 关于链表，你该了解这些！',
    subtitle: '先分清「结点 / 指针 / 内存模型」，再谈增删与复杂度。',
    difficulty: '入门',
    estMinutes: 30,
    keywords: ['单链表', '双链表', '循环链表', '非连续存储', 'ListNode', '数组对比'],
    points: [
      '单链表：数据域 + 一个 next；双链表多一个 prev，可 O(1) 找前驱；循环链表首尾相接，经典应用如约瑟夫环。',
      '链表的结点在内存中不必连续，由指针链接；分配方式取决于语言与运行时的堆管理。',
      '删除：让前驱的 next 跳过目标结点即可；C/C++ 需注意释放被删结点，Java/Python 等依赖 GC。',
      '增删「当前结点」本身可 O(1)，但若要先找到前驱或第 k 个结点，查找仍是 O(n)；与数组的随机访问 O(1) 形成对照。',
      '面试常要求手写 ListNode：构造函数初始化 val/next；力扣默认给出结点类，容易忽略定义细节。',
      'Java 可用内部类 `class ListNode { int val; ListNode next; }`；Python 常用 `class ListNode: def __init__(self, val=0, next=None)`。',
      '刷题中「虚拟头结点 dummy」可把头结点与其他结点统一到同一套删除/插入逻辑，减少分支。',
    ],
    pitfalls: [
      '把「结点值相等」当成「链表相交」：相交题比较的是结点引用（地址），不是 val。',
      '混淆头结点与第一个数据结点：不同资料用语不一，读题时注意「head 是否就是第一个存值的结点」。',
    ],
    checklist: [
      '能口述单链、双链、循环链在「找前驱、删结点」上的能力差异。',
      '能对比数组与链表在访问、插入删除、缓存友好性上的典型取舍。',
    ],
    complexityHint: '按位访问 O(n)；已知前驱时插入/删除 O(1)；额外指针空间 O(1)（不计结点本身）。',
  },
  {
    id: 'remove-elements',
    title: '2. 移除链表元素',
    subtitle: '头结点也可能被删：「原链删除」与「dummy 统一删除」两条路径都要会。',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['虚拟头结点', '头删', '遍历', '203'],
    points: [
      '题意：删除链表中值等于给定 val 的全部结点。',
      '不用 dummy：删非头结点靠前驱改 next；删头需 while（不是 if）连续移动 head，直到头不再是目标值。',
      '使用 dummy：dummy.next = head，令 cur 从 dummy 起扫描；若 cur.next 为目标则 cur.next = cur.next.next，否则 cur 前进。',
      '与数组「快慢指针覆盖」不同，链表删结点只改指针，无需元素搬移。',
      'C++ 在力扣上即使不 delete 也可能 AC，但工程与面试习惯上仍建议释放被摘除结点，避免泄漏与坏习惯。',
    ],
    pitfalls: [
      '删头时只用一次 if，漏删连续多个等于 val 的头结点。',
      '改 next 前未暂存后继指针，导致丢链；C++ 删除后仍将裸指针当有效引用使用。',
    ],
    checklist: [
      '能手写 dummy 版本与「先处理头再遍历」版本，并说明 return 时取 dummy.next。',
    ],
    complexityHint: '单次遍历 O(n)，O(1) 额外空间。',
    main: { id: 203, title: '移除链表元素', slug: 'remove-linked-list-elements' },
    related: [
      { id: 237, title: '删除链表中的节点', slug: 'delete-node-in-a-linked-list' },
      { id: 876, title: '链表的中间结点', slug: 'middle-of-the-linked-list' },
    ],
  },
  {
    id: 'design-list',
    title: '3. 设计链表',
    subtitle: '一题覆盖增删查五类接口，是巩固「找前驱 + 改链」的最好练习题。',
    difficulty: '基础',
    estMinutes: 60,
    keywords: ['707', 'dummy', 'size', 'index 合法性', '头插尾插'],
    points: [
      '需实现 get、addAtHead、addAtTail、addAtIndex、deleteAtIndex；建议自建结点类型并维护 _size 与虚拟头结点。',
      'get(index)：index 从 0 计，非法返回 -1；单链表需从第一个真实结点走 index 步，时间 O(index)。',
      'addAtIndex：index 等于表长等价于尾插；大于表长不插入；小于 0 按头插处理（与力扣题意一致）。',
      '删除与插入都要先定位到「第 index 个结点的前驱」，再改链；注意 delete 后 C++ 中指针置空避免野指针。',
    ],
    pitfalls: [
      'while(index--) 与 --index 混用导致死循环或少走步。',
      '未同步维护 _size，或边界仍用真实头结点导致头尾特判混乱。',
    ],
    checklist: [
      '能不看模板口述五个接口的边界：空表、单结点、删头删尾、index 越界。',
    ],
    complexityHint: '含 index 的操作为 O(index)；头插尾插在维护尾指针时可优化，题解常用 O(n) 找尾。',
    main: { id: 707, title: '设计链表', slug: 'design-linked-list' },
  },
  {
    id: 'reverse',
    title: '4. 反转链表',
    subtitle: '先吃透「三指针迭代」，再对照递归与「头插 / 栈」思路加深理解。',
    difficulty: '基础',
    estMinutes: 50,
    keywords: ['206', 'prev/cur/next', '递归', '头插法', 'O(1) 空间'],
    points: [
      '题意：原地反转整表，不要靠新建一条链浪费结点（思路是改 next 方向）。',
      '迭代：pre 初值为 null，cur 从 head 出发；每次保存 cur.next，再让 cur.next 指向 pre，然后 pre、cur 同步右移。',
      '递归：子问题 reverseList(head.next) 返回新头，当前层把 head.next.next 指回 head，head.next 置 null；栈深度 O(n)。',
      '拓展思路（对照 ）：虚结点 + 头插模拟反转、或栈依次弹出再接——帮助理解「反转 = 反复调整 next 指向」。',
    ],
    pitfalls: [
      '未保存 cur.next 就改写 cur.next，导致无法走到原后继。',
      '只背代码不理解移动顺序：面试一变体（反转区间、K 个一组）就容易写断。',
    ],
    checklist: [
      '能手画三指针每轮前后链接关系，并说明返回值为新的头（原尾）。',
      '能对比迭代 O(1) 空间与递归 O(n) 栈空间的取舍。',
    ],
    complexityHint: '迭代时间 O(n)、空间 O(1)；递归时间 O(n)、空间 O(n)。',
    main: { id: 206, title: '反转链表', slug: 'reverse-linked-list' },
    related: [
      { id: 92, title: '反转链表 II', slug: 'reverse-linked-list-ii' },
      { id: 25, title: 'K 个一组翻转链表', slug: 'reverse-nodes-in-k-group' },
      { id: 234, title: '回文链表', slug: 'palindrome-linked-list' },
    ],
  },
  {
    id: 'swap-pairs',
    title: '5. 两两交换链表中的节点',
    subtitle: '必须交换结点本身而非只换 val；dummy + 画图定「三步改链」顺序。',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['24', '模拟', '多指针', '虚拟头结点'],
    points: [
      '题意：两两反转相邻结点；结点数为奇时末尾单独留下即可。',
      '强烈建议画图：用 dummy 作为上一对之前驱，循环条件常写 cur.next 与 cur.next.next 均存在。',
      '典型三步：记录临时结点保存第三段头，再依次调整两条 next，最后 cur 前进两个「交换对」的长度。',
      '易错是指针覆盖顺序错误或对「移动 cur 到哪」理解反了，导致死循环或丢结点。',
    ],
    pitfalls: [
      '只交换 val 未改指针，不符合题意。',
      '未备份 third 结点就改写前两个的 next，后续无法接回链尾。',
    ],
    checklist: [
      '能手画长度为 2、3、4 的链各走一轮循环，确认返回 dummy.next。',
    ],
    complexityHint: '遍历一遍 O(n)，O(1) 额外空间。',
    main: { id: 24, title: '两两交换链表中的节点', slug: 'swap-nodes-in-pairs' },
  },
  {
    id: 'remove-nth-from-end',
    title: '6. 删除链表的倒数第 N 个节点',
    subtitle: '快慢指针间距刻画「倒数」；配合 dummy 一趟删掉头结点情形。',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['19', '快慢指针', 'n+1 步', '一趟扫描'],
    points: [
      '题意：删除倒数第 n 个结点并返回头；进阶要求一趟扫描。',
      '快慢同从 dummy 出发：快指针先走 n+1 步，再与慢指针同步前移，直到快指针到达 null（越过尾结点）。',
      '此时慢指针恰落在「待删结点的前驱」上，执行 slow.next = slow.next.next 即可。',
      '「先 n+1 再一起走」是为了让 slow 停在待删前驱；若快指针只先走 n 步，则 slow 会指向待删结点本身，不利于单链表删除。',
    ],
    pitfalls: [
      '快指针先走步数与是否使用 dummy 不统一，删头时出错。',
      'while 条件未判 fast.next，在访问 fast.next.next 时空指针异常。',
    ],
    checklist: [
      '能解释为何是 n+1 步而不是 n 步（目标是让 slow 停在待删的前一个结点）。',
      '能手画 n 等于表长（删头）与 n 为 1（删尾）两种边界。',
    ],
    complexityHint: '单次遍历 O(n)，O(1) 额外空间。',
    main: { id: 19, title: '删除链表的倒数第 N 个结点', slug: 'remove-nth-node-from-end-of-list' },
  },
  {
    id: 'intersection',
    title: '7. 面试题 02.07. 链表相交',
    subtitle: '与力扣 160 为同一题意；对齐长度后同速前进，或「A 走完走 B」消去长度差；判的是指针同一引用。',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['160', '面试题 02.07', '长度差', '双指针'],
    points: [
      '题意数据保证无环；若相交，则从某一结点起两链尾部完全共用同一段（地址相同）。',
      '求长度差：长链指针先走 gap 步，再与短链头同步后移，第一次相等即为交点；无交则最终同抵 null。',
      '另一经典写法：A 指针走到末尾后接 headB，B 同理接 headA，第二次相遇等价于消去长度差（需理解无交时双 null）。',
      '剑指 Offer 版与 160 题意相同，可在力扣检索「面试题 02.07」对照提交与讨论。',
    ],
    pitfalls: [
      '比较 val 或把相交误解为「形状交叉」的图示误解题意。',
      'swap 两链头指针时弄混 len 与 cur 的对应关系。',
    ],
    checklist: [
      '能手写「算长度 + 对齐」与「交替拼接」两种思路之一，并说明时间复杂度 O(n+m)。',
    ],
    complexityHint: '时间 O(n+m)，空间 O(1)。',
    main: { id: 160, title: '相交链表', slug: 'intersection-of-two-linked-lists' },
  },
  {
    id: 'cycle',
    title: '8. 环形链表 II',
    subtitle: '快慢相遇判环；再用「头指针与相遇指针同速」找入口，背后是环形上的路程等式。',
    difficulty: '进阶',
    estMinutes: 55,
    keywords: ['142', '141', '快慢指针', '入口', 'x=(n-1)(y+z)+z'],
    points: [
      '子问题一：fast 每次两步、slow 一步，若有环必在环上某处相遇；无环则 fast 先到 null。',
      '相对速度上 fast 对 slow 每次靠近一个结点，故不会「跨过」而不相遇。',
      '子问题二：设头到入口为 x，入口到相遇为 y，相遇回到入口为 z；相遇时 2(x+y)=x+y+n(y+z)，化简得 x=(n-1)(y+z)+z。',
      '当 n=1 时 x=z：从头与从相遇点各放一指针同步走一步，相遇点即为环入口；n>1 时只是在环上多绕圈，相遇仍在入口。',
    ],
    pitfalls: [
      'while 条件未同时检查 fast 与 fast.next，访问 fast.next.next 时崩溃。',
      '把 slow 第一次相遇走过的路程误写成「多绕了未知圈数」而推翻 x+y 等式；资料中有专门补充证明可读。',
    ],
    checklist: [
      '能手写 detectCycle：相遇后拆双指针找入口，并口述为何需要第二次遍历。',
      '能区分 141（判环）与 142（返回入口）的返回值差异。',
    ],
    complexityHint: '时间 O(n)：相遇前指针总步数小于链表长度，相遇后双指针再走亦小于一轮；空间 O(1)。',
    main: { id: 142, title: '环形链表 II', slug: 'linked-list-cycle-ii' },
    related: [{ id: 141, title: '环形链表', slug: 'linked-list-cycle' }],
  },
  {
    id: 'summary',
    title: '9. 链表总结篇',
    subtitle: '把题型收束为几条可迁移的「指针不变量」与套路线。',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['复盘', 'dummy', '反转', '双指针', '相交', '环形'],
    points: [
      '理论基础：种类、存储方式、增删查与数组的性能对照（总结图可对照记忆）。',
      '虚拟头结点：解决「头没有前驱」导致的分支，贯穿移除元素、设计链表、倒数第 N、两两交换等题。',
      '反转链表：先迭代再递归，理解指针翻转过程比背模板重要；复杂题多为「反转一段 + 拼回原链」。',
      '双指针：倒数第 N（间距）、相交（对齐或交替）、环形（快慢 + 入口二次相遇）。',
      '链表题本质是「指针操作」：动手画图、写清每个指针代表的语义，再写代码。',
      '进阶可衔接：复制带随机指针的链表、排序链表、合并 K 个升序链表等，多在「多指针 / 分治 / 堆」上扩展。',
    ],
    pitfalls: [
      '资料中部分动图离线无法播放，复盘时建议打开同题文章对照示意图。',
    ],
    checklist: [
      '能不看笔记列出链表篇五个核心套路：dummy、基础操作、反转、倒数删除、相交与环。',
      '从主刷题中各选一题，限时内独立 AC 并口述指针移动顺序。',
    ],
    complexityHint: '链表篇主复杂度多为 O(n) 遍历与 O(1) 额外空间；递归反转等为 O(n) 栈空间。',
  },
]

export function leetcodeCnUrl(slug: string) {
  return `https://leetcode.cn/problems/${slug}/`
}

export const LINKED_LIST_SECTIONS = applyLinkedListEnrichment(LINKED_LIST_SECTIONS_RAW)

export const LINKED_LIST_SECTION_COUNT = LINKED_LIST_SECTIONS.length
