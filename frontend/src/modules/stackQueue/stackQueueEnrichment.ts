/**
 * 栈与队列各节加厚内容（overview + topicBlocks），合并进 stackQueueCurriculum
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const STACK_QUEUE_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应栈与队列理论基础篇。要点：先弄清「访问顺序约束」再选结构——后进先出用栈，先进先出用队列。本节把 STL 适配器、deque 与后面 232/225/20/239 的实现题串起来；建议结合本节动图理解 push/pop 端。',
    estMinutes: 25,
    topicBlocks: [
      {
        title: '栈（Stack）：LIFO',
        points: [
          '只在栈顶操作：push 压入、pop 弹出、top 查看栈顶。',
          '系统递归调用栈、DFS 非递归、括号匹配、表达式求值、单调栈都依赖栈。',
          'C++ `stack` 是容器适配器，默认底层 `deque`；不能遍历，只能访问栈顶。',
        ],
      },
      {
        title: '队列（Queue）：FIFO',
        points: [
          '队尾入 `push`、队头出 `pop`；BFS、层序遍历、滑动窗口（单调队列）常用。',
          '「用栈实现队列」与「用队列实现栈」是经典互模拟题，理解倒栈/轮转即掌握本质。',
        ],
      },
      {
        title: 'deque 双端队列',
        points: [
          '头尾均可 push/pop；239 滑动窗口最大值用「单调递减 deque 存下标」。',
          '需要两端操作时直接用 deque，不必强行用 stack/queue 适配器。',
        ],
      },
    ],
    extraChecklist: ['能画出示意图说明栈顶、队头队尾', '知道 DFS 可用栈或递归模拟'],
  },
  'queue-by-stacks': {
    overview:
      '力扣 232《用栈实现队列》。常见解法：入队栈 in + 出队栈 out；只有 pop/peek 时若 out 空才把 in 全部倒入 out。关键是「均摊 O(1)」——每个元素最多入出栈各两次。',
    estMinutes: 28,
    topicBlocks: [
      {
        title: '双栈模型',
        points: [
          'push(x)：直接压入 in 栈。',
          'pop()/peek()：若 out 非空，从 out 取；若 out 空，循环 pop in 并 push 到 out，再从 out 取。',
          'in 负责「入队」，out 负责「出队」，顺序由倒栈保证 FIFO。',
        ],
      },
      {
        title: '均摊复杂度分析',
        intro: '面试常问：单次 pop 最坏 O(n) 为何整体均摊 O(1)？',
        points: [
          '每个元素：进 in 一次 → 进 out 一次 → 出 out 一次，常数次数操作。',
          '均摊到每次 push/pop 为 O(1)；amortized 分析要会口述。',
        ],
      },
      {
        title: '实现细节',
        points: [
          'peek 与 pop 共用「确保 out 非空」逻辑，别一个倒栈一个不倒。',
          'empty：in 与 out 皆空；size 可返回 in.size()+out.size()。',
        ],
      },
    ],
    extraPitfalls: ['每次 push 就倒栈——错误，破坏均摊且多余。'],
    summaryPoints: ['232 模板：两个栈 + pop 时才倒栈。'],
  },
  'stack-by-queues': {
    overview:
      '力扣 225《用队列实现栈》。两种写法：单队列轮转（push 后把前 size-1 个元素依次出队再入队）或双队列交换。理解「把新元素旋到队头」即栈顶。',
    estMinutes: 28,
    topicBlocks: [
      {
        title: '单队列轮转法（推荐记忆）',
        points: [
          'push(x)：x 入队后，执行 size-1 次「出队再入队」，使 x 到队头。',
          'pop/top：直接操作队头，O(1)。',
          'push 为 O(n)，其余 O(1)；与 232 对称。',
        ],
      },
      {
        title: '双队列法',
        points: [
          '维护主队列 q1、辅助 q2；push 时元素先入空队列，再把 q1 全部移到 q2，交换 q1/q2 角色。',
          '逻辑等价，代码稍长，面试写一种即可。',
        ],
      },
    ],
    extraChecklist: ['能手写单队列版 push 的轮转循环'],
  },
  'valid-parentheses': {
    overview:
      '力扣 20《有效的括号》——栈的入门题。遇左括号入栈，遇右括号检查栈顶是否匹配；遍历结束栈须空。与 1047 相邻消除同属「栈维护待匹配结构」。',
    estMinutes: 22,
    topicBlocks: [
      {
        title: '匹配流程',
        points: [
          '左括号 `( [ {`：push 对应右括号或左括号本身（两种写法）。',
          '右括号：栈空 → false；栈顶不匹配 → false；否则 pop。',
          '字符串结束：return stack.empty()。',
        ],
      },
      {
        title: '代码技巧',
        points: [
          "用 hash map 存「)」→「(」等配对，遇右括号查表，代码更短。",
          '也可奇数位剪枝：长度为奇数必 false。',
        ],
      },
      {
        title: '拓展',
        points: [
          '32 最长有效括号、301 删除无效括号属于进阶；20 是模板。',
          'DFS 括号生成（22）是回溯，不是纯栈题。',
        ],
      },
    ],
    extraPitfalls: ['只判断栈非空就 return true，忘记最后必须栈空。'],
  },
  'remove-adjacent': {
    overview:
      '力扣 1047《删除字符串中的所有相邻重复项》。栈顶与当前字符相同则 pop，否则 push；最终栈内拼接即答案。与消消乐一致，也可双指针原地（若允许改输入）。',
    estMinutes: 25,
    topicBlocks: [
      {
        title: '栈模拟消除',
        points: [
          '遍历每个字符 c：若栈非空且 stack.top()==c，则 pop；否则 push(c)。',
          '栈中字符从底到顶即结果（无相邻重复）。',
          '时间 O(n)，空间 O(n)。',
        ],
      },
      {
        title: '与 20 的对比',
        points: [
          '20 是「配对消除」；1047 是「相同相邻消除」，可连续多轮在一次遍历完成。',
          '1209 移掉 K 位数字、402 去零类似贪心+栈，可学完再刷。',
        ],
      },
    ],
    summaryPoints: ['相邻相同 → 看栈顶决定 pop 还是 push。'],
  },
  'eval-rpn': {
    overview:
      '力扣 150《逆波兰表达式求值》。数字入栈；遇运算符弹出两个操作数，注意顺序：先弹 b 再弹 a，计算 a op b 再入栈。最后栈中唯一元素即答案。',
    estMinutes: 28,
    topicBlocks: [
      {
        title: '处理流程',
        points: [
          'token 为数字：push(stoll(token))。',
          'token 为运算符：b=pop(); a=pop(); push(a+b) 等。',
          '除法向零截断：C++ 用 a/b 整数除法；注意负数除法实现差异。',
        ],
      },
      {
        title: '易错点',
        points: [
          '减法、除法顺序：第二个弹出的是右操作数。',
          '表达式合法时栈最后恰剩一个数；中间栈大小至少为 2 才能运算。',
        ],
      },
      {
        title: '拓展',
        points: [
          '224 基本计算器、227 含乘除——栈 + 预处理；150 是无括号 RPN 基础。',
        ],
      },
    ],
    extraPitfalls: ['pop 顺序反了导致减法和除法结果错误。'],
  },
  'sliding-window-max': {
    overview:
      '力扣 239《滑动窗口最大值》——单调队列经典题。deque 存下标，保持对应值单调递减；队头为当前窗口最大值下标。要点：存下标而非值，才能判断元素是否滑出窗口。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '单调递减 deque',
        points: [
          '入队前：从队尾 while 队尾对应值 ≤ nums[i]，pop_back（淘汰不可能成为最大值的）。',
          'push_back(i)；若队头下标 ≤ i-k，pop_front（过期）。',
          '当 i ≥ k-1，ans 记录 nums[deque.front()]。',
        ],
      },
      {
        title: '复杂度',
        points: [
          '每个下标最多入队、出队各一次，总 O(n)。',
          '暴力 O(nk) 会超时；堆 O(n log k) 可过但不如单调队列优雅。',
        ],
      },
      {
        title: '与单调栈区别',
        points: [
          '单调栈：通常求「下一个更大/更小」；单调队列：窗口最值。',
          '239 是队列篇最难一题，务必手写三遍。',
        ],
      },
    ],
    extraPitfalls: ['deque 存值导致窗口左移时无法判断是否过期。', '忘记 i>=k-1 才开始记录答案。'],
    extraChecklist: ['能口述为何每个元素最多进出 deque 一次'],
  },
  'top-k-frequent': {
    overview:
      '力扣 347《前 K 个高频元素》。先哈希计数，再用大小为 k 的小顶堆维护 Top K；或桶排序 O(n)（频次作下标）。堆解法通用，桶排序在频次范围不大时更快。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: '哈希 + 小顶堆',
        points: [
          'unordered_map 统计 nums[i] 频次。',
          'priority_queue 维护 (频次, 数值)，堆顶是 k 个里频次最小的。',
          '若 size>k 则 pop；最后堆中即为答案。复杂度 O(n log k)。',
        ],
      },
      {
        title: '桶排序',
        points: [
          'bucket[i] 存放频次为 i 的所有数；i 从大到小收集直到满 k 个。',
          '频次最大不超过 n，桶数组长度 O(n)。',
          '面试两种都会加分；先写堆更稳。',
        ],
      },
      {
        title: '相关题',
        points: [
          '215 数组第 K 大：快选或堆；347 多一步计数。',
          '692 前 K 高频单词：堆元素为字符串，比较规则更复杂。',
        ],
      },
    ],
    summaryPoints: ['计数 → 小顶堆维护 Top K，或桶排序按频次倒扫。'],
  },
  summary: {
    overview:
      '栈与队列篇复盘：实现互模拟（232/225）打基础；栈处理括号、消除、表达式；队列扩展单调 deque（239）与堆/桶（347）。建议按章节顺序刷完再对照下表查漏补缺。',
    estMinutes: 15,
    topicBlocks: [
      {
        title: '题型地图',
        points: [
          '实现：232 双栈队列、225 队列栈——面试手写高频。',
          '栈应用：20 括号、1047 消除、150 RPN。',
          '进阶：239 单调队列（必掌握）、347  Top K。',
        ],
      },
      {
        title: '学习建议',
        points: [
          '每题先想「需要 LIFO 还是 FIFO」，再选结构。',
          '239 与单调栈篇的 739 对比：一个窗口最值，一个下一个更大。',
          '栈与递归思维互通，写不出递归时可尝试显式栈。',
        ],
      },
    ],
    extraChecklist: ['独立写出 232、20、239 核心循环'],
  },
}

export function applyStackQueueEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, STACK_QUEUE_ENRICHMENT)
}
