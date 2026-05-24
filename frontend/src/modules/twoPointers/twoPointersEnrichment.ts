/**
 * 双指针各节加厚内容（overview + topicBlocks），合并进 twoPointersCurriculum
 * 双指针模块 enrichment
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const TWO_POINTERS_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应双指针篇开篇与总结中的「三种形态」。要点：双指针不是某一种结构专属——数组可覆盖或两端夹逼，字符串常从后往前填，链表是快慢或对齐长度，有序数组是排序后 left/right。先弄清每个指针代表什么，再进 27、344 等具体题。',
    estMinutes: 25,
    topicBlocks: [
      {
        title: '三种双指针形态',
        points: [
          '快慢（同向）：快指针探路/找新元素，慢指针指向下一个写入位置——27 经典定义；链表判环、倒数第 n 个也属此类。',
          '相向（对撞）：`left` 从首、`right` 从尾向中间，适合有序和、平方、对称交换；允许乱序时 27 相向版可减少搬移。',
          '排序 + 左右：外层固定元素，内层 `left/right` 根据与 target 比较收拢——15、18 模板；可推广到 N 数之和 O(n^(k-1))。',
        ],
      },
      {
        title: '书写习惯与复杂度直觉',
        points: [
          '每道题写清循环不变量：慢指针是「下一写入下标」还是「待删前驱」要一句话说清。',
          '填充类字符串题从后往前写才是 O(n)；for 里随意 `erase` → O(n²)（在 151 去空格处强调）。',
          '单指针扫描 O(n)；三数之和 O(n²)；四数之和 O(n³)；多数额外空间 O(1)。',
        ],
      },
    ],
    extraChecklist: ['能各用一句话说明快慢、相向、排序+左右适用场景。'],
  },
  'remove-element': {
    overview:
      '27 移除元素：数组不能真删，只能覆盖。快慢保序 O(n)；相向在允许打乱相对顺序时减少交换次数。双指针篇第一课，与 26、283、844、977 同族。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '快慢指针（保序）',
        points: [
          '`fast` 扫描全表，若 `nums[fast] != val` 则 `nums[slow++] = nums[fast]`。',
          '慢指针含义：下一个写入位置；返回值即新长度，尾部元素无需关心。',
          '时间 O(n)，空间 O(1)；相对顺序不变，面试默认写法。',
          '与 26 去重、283 移动零：都是「快找、慢写」同一骨架。',
        ],
      },
      {
        title: '相向指针（最少移动）',
        points: [
          '`left` 找等于 val，`right` 找不等于 val，交换覆盖；会改变相对顺序。',
          '循环 `left <= right`，最后 `return left`（或 left+1，与实现统一一种）。',
          '手画 `left`、`right` 相遇时新数组有效区间；对比「保序」与「最少移动」取舍。',
          '相向写法代码：移动元素更少，适合题面不要求保序时。',
        ],
      },
    ],
    extraPitfalls: ['相向写法循环条件与 return 边界未手画验证。'],
  },
  'reverse-string': {
    overview:
      '344 反转字符串：相向指针交换对称位置，双指针入门题。字符串连续存储类似数组；理解 swap 比依赖 `reverse` 更重要，并与 206 反转链表对照记忆。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '标准模板',
        points: [
          '`i = 0`，`j = n - 1`，向中间移动并交换，直到 `i >= j`（或 `i < j` 统一一种）。',
          '库函数原则：关键步骤若一行 `reverse` 搞定，面试不宜依赖；`swap` 且你理解实现时可用。',
          '时间 O(n)，空间 O(1)；Java 注意力扣给的是 `char[]`，不是不可变 `String`。',
        ],
      },
      {
        title: '与链表反转对照',
        points: [
          '206：三指针 `pre/cur/temp` 改 `next`；344：下标交换，无需保存 `next`。',
          '345 只反转元音：跳过非元音再交换，模板相同。',
          '区间反转函数供字符串篇 541、151 复用。',
        ],
      },
    ],
  },
  'replace-space': {
    overview:
      '剑指 Offer 05 替换空格：统计空格 → 扩容 → 双指针从尾部填充 `%20`。填充类问题的双指针模板；说明技巧在数组、字符串、链表间通用。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '从后往前填（O(n)）',
        points: [
          '新长度 `oldSize + 2 * spaceCount`；`i` 指向新串末尾，`j` 指向旧串末尾。',
          '非空格：`s[i--] = s[j--]`；空格：依次写 `0`、`2`、`%`，`i` 减 3。',
          '从前向后填每次插入都要后移后续字符 → O(n²)；从后向前每位只写一次。',
          '能解释为何必须从后往前，并举覆盖未读字符的反例。',
        ],
      },
      {
        title: '语言差异与串联',
        points: [
          'C++ `resize` 后可写；Java 常用 `StringBuilder` 或 char 数组思维。',
          '提示：到本节已完成 27、15、18、206、142、344 等，双指针是跨结构技巧。',
          '与字符串篇 151 去空格：都怕 for 里 `erase`；填充与压缩都倾向 O(n) 单遍写法。',
        ],
      },
    ],
  },
  'reverse-words': {
    overview:
      '151 反转字符串中的单词：快慢压缩空格 + 整体反转 + 逐词反转。双指针篇综合题；要求 O(1) 空间则必须原地操作，勿 `split`+新串。',
    estMinutes: 60,
    topicBlocks: [
      {
        title: '三步流程',
        points: [
          '① 快慢压缩：遇非空格写入，单词间手动补一个空格，去掉首尾与冗余空格（思想同 27）。',
          '② `reverse(0, n-1)` 整串反转。',
          '③ 在 i == size 或 s[i] 为空格时 reverse(start, i-1)，再 start = i+1。',
          '示例：`"the sky is blue"` → 压缩 → 全反 → 分词反 → `"blue is sky the"`。',
        ],
      },
      {
        title: '常见坑与复杂度',
        points: [
          '`split`+拼接虽能 AC 但 O(n) 空间且不符合 O(1) 题意；`erase` 去空格 O(n²)。',
          '只做一次整体反转会导致单词内也被反转且顺序未调——必做第三步。',
          'C++ 可用 `istringstream` 理解题意，面试仍推荐原地模板。',
          '时间 O(n)，语言允许原地修改时空间 O(1)。',
        ],
      },
    ],
  },
  'reverse-list': {
    overview:
      '206 反转链表：迭代三指针 `pre/cur/temp` 改 `next` 是现场手写高频；递归与迭代本质相同。双指针在链表上的代表题之一。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '迭代三指针',
        points: [
          '`pre = null`，`cur = head`；每轮保存 `cur->next` 到 `temp`，再 `cur->next = pre`，然后 `pre = cur`，`cur = temp`。',
          '循环结束返回 `pre`（`cur` 已为 null），不是 `cur`。',
          '未保存 `cur->next` 就改写 `next` 会丢链——第一行必写 `temp = cur->next`。',
          '时间 O(n)，空间 O(1)。',
        ],
      },
      {
        title: '递归与其它写法',
        points: [
          '递归：`newHead = reverseList(head->next)`，再把 `head` 接到新尾后面。',
          '虚结点+头插、栈弹出：帮助理解，面试优先迭代 O(1) 空间。',
          '与 344：链表改指针域，字符串改下标；难度链表略高但套路固定。',
        ],
      },
    ],
  },
  'remove-nth-from-end': {
    overview:
      '19 删除链表的倒数第 N 个结点：快指针先走 `n+1` 步，再与慢指针同速，让 slow 停在待删结点前驱。配合 dummy 一趟删除，是快慢指针「保持间距」的典型题。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: 'dummy + 快先走 n+1',
        points: [
          '删除倒数第 n 个 = 删除 `slow->next`，故 fast 从 dummy 先走 `n+1` 步（不是 n 步）。',
          '然后 fast、slow 同步直到 `fast == null`，执行 `slow->next = slow->next->next`。',
          '不用 dummy 需单独处理删头；面试推荐 dummy 统一边界。',
          '一趟 O(n)，空间 O(1)。',
        ],
      },
      {
        title: '边界手画',
        points: [
          'n = 表长：删头，验证 dummy 是否生效。',
          'n = 1：删尾，验证 `fast->next` 空指针判断。',
          '`while` 访问 `fast->next->next` 前须保证 `fast` 与 `fast->next` 非空。',
        ],
      },
    ],
  },
  intersection: {
    overview:
      '160 相交链表：相交指结点引用相同（不是 val 相等）。对齐长度后同速前进，或 A 走完接 headB、B 走完接 headA 的巧妙写法，均为 O(m+n) 时间 O(1) 空间。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '对齐长度法',
        points: [
          '求 `lenA`、`lenB`；长链 `cur` 先走 `|lenA - lenB|` 步，再与短链头同步后移。',
          '第一次指针相等即为交点；无交则同抵 `null`。',
          '交换长度与头指针时勿弄混 `curA/curB`。',
          '比较的是结点地址，不是结点值。',
        ],
      },
      {
        title: '交替拼接法',
        points: [
          '指针 A 走完 A 接 headB，B 走完 B 接 headA，同速前进，相遇即交点。',
          '两指针各走 `lenA + lenB` 路程，消去长度差，无需先算长度。',
          '无相交时两者同抵 null；空间 O(1)。',
        ],
      },
    ],
  },
  cycle: {
    overview:
      '142 环形链表 II：快慢相遇判环；相遇后 head 与相遇点同速走，再相遇处为入口。141 只判是否有环。数学推导 `x = (n-1)(y+z) + z`，n=1 时 `x=z` 是核心直觉。',
    estMinutes: 60,
    topicBlocks: [
      {
        title: '快慢判环与入口',
        points: [
          'fast 每次两步、slow 一步；有环必在环上相遇，无环 fast 先到 null。',
          '相遇后 `index1` 从相遇点、`index2` 从 head 同速走，再相遇即环入口。',
          '141：只返回是否有环；142：返回入口结点。',
          '`while` 须 `fast && fast->next`，否则空指针。',
        ],
      },
      {
        title: 'x + y 等式直觉',
        points: [
          '设头到入口 x，入口到相遇 y，相遇回到入口 z；相遇时 `2(x+y) = x + y + n(y+z)`，化简得 `x = (n-1)(y+z) + z`。',
          'n=1 时 x=z：从 head 与从相遇点各走 x，同时到达入口。',
          'n>1 只是多绕圈，入口位置不变；勿误以为 slow 第一次相遇路程必须是 x。',
          '时间 O(n)，空间 O(1)。',
        ],
      },
    ],
  },
  'three-sum': {
    overview:
      '15 三数之和：排序 + 固定 i + left/right。哈希可做但去重难、剪枝弱；面试推荐 sort 后双指针。去重细节（比较 `nums[i]` 与 `nums[i-1]`）决定能否 AC。',
    estMinutes: 65,
    topicBlocks: [
      {
        title: '主框架',
        points: [
          'sort 后 `for i`：`if (i>0 && nums[i]==nums[i-1]) continue`；`left=i+1`，`right=n-1`。',
          '和 > 0 → `right--`；和 < 0 → `left++`；和 == 0 → 收录，`left++` 且 `right--`，并跳过重复 left/right。',
          '和 > 0 时若 `nums[i] > 0` 可直接 break（全正后面更大）。',
          '时间 O(n²)，空间 O(1)（不计输出）。',
        ],
      },
      {
        title: '去重为何这样写',
        points: [
          '去重 a：比较 `nums[i]` 与 `nums[i-1]`，勿与 `nums[i+1]` 比，否则漏 `[-1,-1,2]`。',
          '去重 b/c：放在找到答案之后对 left、right 收缩；在 while 开头对 left/right 去重可能 `right<=left` 漏 `0,0,0`。',
          '两数之和若返回下标不能排序双指针；若只要求数值则可以。',
          '与 454 四数相加 II 区分：后者四数组 + 哈希，无同数组去重负担。',
        ],
      },
    ],
  },
  'four-sum': {
    overview:
      '18 四数之和：在三数之和外再套一层 k；内层仍是 left/right。剪枝勿照搬「nums[i]>0」到任意 target；注意 long 防溢出。与 454 勿混淆。',
    estMinutes: 55,
    topicBlocks: [
      {
        title: '四层枚举模板',
        points: [
          '两层 for 固定 `k`、`i`，内层 `left/right`，和与 `target` 比较；整体 O(n³)。',
          '找到答案后对 left、right 做与 15 题相同的去重收缩。',
          'N 数之和：继续外层 for + 最内层双指针，复杂度 O(n^(N-1))。',
          '能说明 18 与 15 差异仅在多一层枚举与剪枝条件。',
        ],
      },
      {
        title: '剪枝与溢出',
        points: [
          '不能因 `nums[k] > target` 就 break（如全负数 target=-10）；可用 `nums[k]>target && nums[k]>=0` 等条件。',
          '二级剪枝：`nums[k]+nums[i]>target` 且二者同号时可 break 内层 i 循环。',
          '累加用 `long` 防溢出；去重逻辑与 15 一致移植到 k、i 层。',
          '454 四数相加 II：四独立数组 + map，不必强行双指针。',
        ],
      },
    ],
  },
  summary: {
    overview:
      '双指针总结篇：按数组 / 字符串 / 链表 / N 数之和四条线复盘全书九题。掌握三种形态后，同类题多为变体；建议每类限时手写一题，再对照  动图补直觉。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: '四条线复盘',
        points: [
          '数组：27 快慢/相向覆盖；勿 for+erase O(n²)。',
          '字符串：344 相向；剑指05/151 从后往前或快慢压缩+区间反转。',
          '链表：206 改 next；19 间距快慢；160 对齐；142 快慢+入口二次相遇——链表题常必用双指针。',
          'N 数之和：15/18 排序+双指针优于哈希去重；454 仍用哈希。',
        ],
      },
      {
        title: '九题清单与练习建议',
        points: [
          '本章九题：27、15、18、206、19、160、142、344 + 字符串系列（05、151 等）。',
          '能按「快慢 / 相向 / 排序+左右」各举 2 道题名。',
          '能说明双指针将哪类暴力从 O(n²) 降到 O(n) 或 O(n²) 可剪枝。',
          '每节先明确各指针语义，再结合本节视频手敲一遍。',
        ],
      },
    ],
    summaryPoints: ['链表相交、环入口必须比较指针地址，不是 val。'],
  },
}

export function applyTwoPointersEnrichment<T extends LearnSection>(sections: T[]): T[] {
  return mergeEnrichment(sections, TWO_POINTERS_ENRICHMENT)
}
