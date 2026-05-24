/**
 * 链表各节加厚内容（overview + topicBlocks），合并进 linkedListCurriculum
 * 
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const LINKED_LIST_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应《关于链表，你该了解这些！》。链表与数组相反：结点分散、指针串联，已知前驱时插入删除 O(1)，但无随机访问。面试高频在虚拟头结点、反转、快慢指针、相交与环形——本节先分清结点/指针/内存模型，再进入实操。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '三种链表与能力差异',
        points: [
          '单链表：数据域 + next；删当前结点需知前驱，查找 O(n)。',
          '双链表：多 prev，可 O(1) 找前驱；空间换操作便利。',
          '循环链表：首尾相接；约瑟夫环等经典模型。',
          '结点在堆上不必连续，由指针链接；与数组连续块、缓存友好性形成对照。',
        ],
      },
      {
        title: 'ListNode 与语言细节',
        points: [
          '面试常手写：C++ struct / Java 内部类 / Python __init__(val, next=None)。',
          '力扣默认给出结点类，但「自己定义」题（707）要会写构造函数。',
          'C/C++ 删除结点应释放内存；Java/Python 依赖 GC，但逻辑上仍要断开引用防环。',
        ],
      },
      {
        title: '虚拟头结点 dummy 的动机',
        points: [
          '真实头结点没有「前驱」，删头、插头需特判；dummy.next=head 后，头与其他结点统一处理。',
          '贯穿 203、707、19、24 等题；return dummy.next 作为新头。',
          '相交题比较的是结点引用（地址），不是 val；形状「交叉」的示意图易误导。',
        ],
      },
    ],
    summaryPoints: ['链表题先画图：每个指针此刻指向谁、代表什么语义。'],
    extraPitfalls: [
      '把 val 相等当成链表相交；相交是同一结点对象。',
      '混淆「头结点」与「第一个数据结点」的不同教材用语。',
    ],
    extraChecklist: [
      '能口述单/双/循环链在找前驱、删结点上的差异。',
      '能对比数组与链表在访问、插入删除、缓存上的取舍。',
    ],
  },
  'remove-elements': {
    overview:
      '对应《移除链表元素》203。头结点也可能被删：「while 处理头」与「dummy 统一删除」两条路径都要会。链表删结点只改指针，无需像数组那样搬移元素。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '不用 dummy：先处理头再遍历',
        points: [
          '删非头：cur 扫描，若 cur->next->val==val 则 cur->next=cur->next->next，否则 cur 前进。',
          '删头：while(head && head->val==val) head=head->next，必须是 while 不是 if，否则连续多个 val 漏删。',
          'C++ 删除后建议将摘除结点指针置空，避免野指针习惯问题。',
        ],
      },
      {
        title: 'dummy 统一版（推荐默写）',
        points: [
          'ListNode* dummy=new ListNode(0); dummy->next=head; ListNode* cur=dummy;',
          '若 cur->next 为目标则 cur->next=cur->next->next（cur 不动，继续检查新 next）；否则 cur=cur->next。',
          'return dummy->next；Java 注意避免成环引用导致 GC 无法回收（面试逻辑仍要断开）。',
        ],
      },
      {
        title: '与数组 27 的对照',
        points: [
          '数组快慢指针是覆盖写；链表是改前驱的 next。',
          '237 删除给定结点：把后继值复制上来再删后继，O(1) 但无法删尾结点。',
          '876 找中间结点：快慢指针，为后续题铺垫。',
        ],
      },
    ],
    extraPitfalls: [
      '删头只用一次 if，漏删连续等于 val 的头结点。',
      '改 next 前未暂存后继，导致丢链。',
    ],
    extraChecklist: ['能手写 dummy 版与无 dummy 版，并说明 return dummy.next。'],
  },
  'design-list': {
    overview:
      '对应《设计链表》707。一题覆盖 get、头插、尾插、按下标插删五类接口，是巩固「找前驱 + 改链 + 维护 size」的最佳练习。建议自建结点类型、虚拟头、_size，减少头尾特判。',
    estMinutes: 70,
    topicBlocks: [
      {
        title: '数据结构与边界',
        points: [
          '成员：dummy 哨兵、_size；结点含 val、next。',
          'get(index)：index<0 或 index>=_size 返回 -1；从 dummy.next 走 index 步。',
          'addAtIndex：index>size 不插；index==size 等价尾插；index<0 按题意处理（力扣按头插）。',
        ],
      },
      {
        title: '插入与删除的统一模式',
        points: [
          '插入 index：先让 cur 从 dummy 走 index 步，停在「第 index 个结点的前驱」，new 结点接 cur->next，再 cur->next=new。',
          'deleteAtIndex：同样走到前驱，cur->next=cur->next->next，_size--，C++ 可 delete 被删结点。',
          'addAtHead / addAtTail 可复用 addAtIndex(0) 与 addAtIndex(size)，或单独优化。',
        ],
      },
      {
        title: '常见实现错误',
        points: [
          'while(index--) 与 --index 混用导致少走或多走一步。',
          '未同步 _size，或 delete 后仍访问已释放结点。',
          '尾插若每次 O(n) 找尾，可维护 tail 指针优化，但面试 O(n) 找尾通常可接受。',
        ],
      },
    ],
    extraPitfalls: ['index 合法性判断与 cur 起步位置不一致。', '插入后忘记 _size++。'],
    extraChecklist: ['能口述五接口在空表、单结点、删头删尾、越界时的行为。'],
  },
  reverse: {
    overview:
      '对应《反转链表》206。先吃透三指针迭代（pre/cur/next），再对照递归与头插法。反转是链表篇核心技能：92 反转区间、25 K 个一组、234 回文都是「反转一段 + 拼回」。',
    estMinutes: 60,
    topicBlocks: [
      {
        title: '迭代三指针（必背）',
        points: [
          'pre=null，cur=head；每轮：tmp=cur->next；cur->next=pre；pre=cur；cur=tmp。',
          '结束 cur==null，新头为 pre；切勿未保存 cur->next 就改 cur->next。',
          '时间 O(n)，空间 O(1)；面试首选。',
        ],
      },
      {
        title: '递归写法',
        points: [
          '子问题 newHead=reverseList(head->next)；head->next->next=head；head->next=null；return newHead。',
          '栈深度 O(n)，空间 O(n)；理解「先反转后面，再把当前结点接到后面」.',
          '与后序遍历类似：先处理子链，再处理当前层连接。',
        ],
      },
      {
        title: '头插法与拓展',
        points: [
          'dummy + 反复头插可模拟反转，帮助理解「反转 = 调整 next 方向」。',
          '92：记录区间前驱，反转 [left,right] 再拼接；25：每 K 个一组反转，注意组间连接。',
          '234：找中点 + 反转后半 + 比较，快慢指针与反转的组合。',
        ],
      },
    ],
    extraPitfalls: [
      '未保存 cur->next 就改写 cur->next，断链。',
      '只背代码不理解顺序，一变体（区间/K 组）就写断。',
    ],
    extraChecklist: [
      '能手画每轮 pre/cur/next 的链接关系。',
      '能对比迭代 O(1) 空间与递归 O(n) 栈的取舍。',
    ],
  },
  'swap-pairs': {
    overview:
      '对应《两两交换链表中的节点》24。必须交换结点指针而非只换 val；dummy + 画图定「三步改链」顺序。奇数个结点时末尾单独留下。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '为何必须改指针',
        points: [
          '题意要求交换结点本身；只交换 val 不符合要求且面试会被追问。',
          '用 dummy 作为「上一对」的前驱，循环条件：cur->next 与 cur->next->next 均存在。',
        ],
      },
      {
        title: '典型三步（先备份再改）',
        points: [
          '设 first=cur->next，second=first->next，third=second->next（备份第三段头）。',
          'cur->next=second；second->next=first；first->next=third。',
          'cur 前进到 first（原第一结点，现位于交换对之后），准备下一对。',
        ],
      },
      {
        title: '调试与边界',
        points: [
          '长度 0/1：直接返回 head；长度 2：交换一次即可。',
          '指针覆盖顺序错误或未备份 third 会导致丢链或死循环。',
          '与 25 K 个一组对比：24 是固定 2，改链模式更简单。',
        ],
      },
    ],
    extraPitfalls: ['只换 val。', '未备份第三结点就改前两个的 next。'],
    extraChecklist: ['能手画长度 2、3、4 的链各走一轮循环，确认 return dummy.next。'],
  },
  'remove-nth-from-end': {
    overview:
      '对应《删除链表的倒数第 N 个结点》19。快慢指针间距刻画「倒数」：快指针先走 n+1 步，再与慢同步，慢停在待删前驱。配合 dummy 一趟处理删头。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '为何是 n+1 步',
        points: [
          '目标：让 slow 停在「待删结点的前驱」，才能 slow->next=slow->next->next。',
          '快指针先走 n+1 步（从 dummy 出发），再 while(fast) 双指针同步，fast 到 null 时 slow 恰在前驱。',
          '若快指针只走 n 步，slow 会指向待删结点本身，单链表无法 O(1) 删「当前」无 prev。',
        ],
      },
      {
        title: '完整模板',
        points: [
          'dummy->next=head；slow=fast=dummy；for 走 n+1 步 fast；while(fast) slow++, fast++。',
          'delete slow->next；return dummy->next。',
          'while 条件要判 fast 非空，避免 fast->next 空指针（若写法不同则统一检查 fast/fast->next）。',
        ],
      },
      {
        title: '边界走查',
        points: [
          'n 等于表长：删的是原 head，dummy 使 slow 仍在删头的前驱。',
          'n=1：删尾结点；单结点表删后返回 null。',
          '与 876 快慢找中间对比：本题是固定间距而非「相遇在中点」。',
        ],
      },
    ],
    extraPitfalls: [
      '快指针步数与是否 dummy 不统一，删头出错。',
      'while 未判 fast->next 就访问 fast->next->next。',
    ],
    extraChecklist: ['能解释 n+1 而非 n。', '能手画 n=表长与 n=1 两种边界。'],
  },
  intersection: {
    overview:
      '对应《链表相交》160 / 面试题 02.07。两链尾部共用同一段（同一结点引用），不是 val 相等或形状交叉。解法：对齐长度后同速前进，或 A 走完接 B、B 走完接 A 消长度差。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '题意与易错图示',
        points: [
          '相交后从某结点起两链完全重合（同一对象），长度差只在相交前。',
          '比较的是指针/引用相等，不是结点值。',
          '无环保证；若有环需另做 142。',
        ],
      },
      {
        title: '长度对齐法',
        points: [
          '分别求 lenA、lenB；长链指针先走 |lenA-lenB| 步。',
          '再与短链头同步后移，第一次指针相等即为交点；都无交则同抵 null。',
          '时间 O(n+m)，空间 O(1)。',
        ],
      },
      {
        title: '交替拼接法',
        points: [
          '指针 A 从 headA 走，到尾接 headB；B 同理接 headA。',
          '两指针各走 lenA+lenB，第二次相遇于交点；无交则同 null。',
          '写法优雅，但需理解「走两遍总长」消去长度差。',
        ],
      },
    ],
    extraPitfalls: ['比较 val。', 'swap 头指针时弄混 len 与 cur 对应关系。'],
    extraChecklist: ['能手写「算长度+对齐」或「交替拼接」之一并分析复杂度。'],
  },
  cycle: {
    overview:
      '对应《环形链表 II》142（141 判环）。快慢指针相遇判环；再令一头指针与相遇点同速走，相遇处为入口。背后等式 x=(n-1)(y+z)+z，推导 有补充证明。',
    estMinutes: 65,
    topicBlocks: [
      {
        title: '141：快慢判环',
        points: [
          'slow 一步、fast 两步；有环必在环内相遇，无环 fast 先到 null。',
          'while 须判 fast 与 fast->next，否则访问 fast->next->next 崩溃。',
          '相对速度每次靠近一步，不会「跨过」slow。',
        ],
      },
      {
        title: '142：找入口',
        points: [
          '相遇后：index1=head，index2=meet，同步每次走一步，再相遇点即入口。',
          '推导：设头到入口 x，入口到相遇 y，相遇回入口 z；2(x+y)=x+y+n(y+z) → x=z（n=1 时最直观）。',
          'n>1 只是在环上多绕圈，第二次相遇仍在入口。',
        ],
      },
      {
        title: '与相交、倒数删除的联系',
        points: [
          '快慢指针家族：876 中点、19 间距、141/142 环、160 对齐。',
          '142 返回入口结点；141 返回 bool。',
          '注意勿把 slow 第一次路程误解为「未知圈数」而推翻 x+y 等式。',
        ],
      },
    ],
    extraPitfalls: [
      'while 未判 fast->next。',
      '相遇后未做第二趟同速双指针找入口。',
    ],
    extraChecklist: [
      '能手写 detectCycle 并口述 x=z 直觉。',
      '能区分 141 与 142 返回值差异。',
    ],
  },
  summary: {
    overview:
      '链表篇总复盘：虚拟头、反转、双指针（倒数/相交/环）三条主线。配合本节动画，把「指针不变量」练到能边画边写。进阶可接复制随机链表、合并 K 链、排序链表。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: '套路地图',
        points: [
          'dummy：203/707/19/24 —— 统一头结点无前驱问题。',
          '反转：206 迭代必会 → 92/25/234 分段反转。',
          '快慢：19 间距 n+1、876 中点、141/142 环。',
          '双链对齐：160 长度差或交替拼接。',
        ],
      },
      {
        title: '学习建议',
        points: [
          '每题先画指针图再写代码；return 时想清楚新头是谁。',
          '主刷题各限时 AC 并口述指针移动。',
          'C++ 注意释放；Java 断开引用；Python 注意成环。',
          '数组篇「下标不变量」迁移为「指针语义不变量」。',
        ],
      },
      {
        title: '本章学习顺序',
        points: [
          '理论 → 203 → 707 → 206 → 24 → 19 → 160 → 142。',
          '相关：237/876/92/25/234/141，按套路归类二刷。',
        ],
      },
    ],
    extraChecklist: [
      '能列出五套路：dummy、设计、反转、倒数删、相交与环。',
      '能对比链表 O(1) 删（知前驱）与数组 O(n) 搬移。',
    ],
  },
}

export function applyLinkedListEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, LINKED_LIST_ENRICHMENT)
}
