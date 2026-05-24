import type { GuideTableBlock } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { applyStackQueueEnrichment } from './stackQueueEnrichment'

export { leetcodeCnUrl } from '@/modules/shared/learningTypes'

export const STACK_QUEUE_INTRO =
  '栈与队列是限制访问顺序的线性结构：栈后进先出（LIFO），队列先进先出（FIFO）。本篇用「两个栈模拟队列」「两个队列模拟栈」打通实现；再以有效括号、相邻删除、逆波兰、滑动窗口最大值、前 K 高频串联经典题型。'

const base = (s: Omit<LearnSection, never>): LearnSection => s

const STACK_QUEUE_SECTIONS_RAW: LearnSection[] = [
  base({
    id: 'theory',
    title: '1. 栈与队列理论基础',
    subtitle: 'LIFO / FIFO · 适配器 · 何时用哪种结构',
    difficulty: '入门',
    estMinutes: 15,
    keywords: ['栈', '队列', 'deque'],
    points: [
      '栈：只在栈顶 push/pop，适合括号匹配、DFS、表达式求值、单调栈。',
      '队列：队尾入、队头出；BFS、滑动窗口、层序遍历常用。',
      'C++ 中 stack / queue 是容器适配器，默认底层 deque；需要两端操作时直接用 deque。',
      '「用栈实现队列」：入队栈 + 出队栈，出队时若出队栈空则把入队栈全部倒入。',
    ],
    checklist: ['能口述栈与队列的 push/pop 端', '知道 BFS 用队列、DFS 用栈（或递归栈）'],
  }),
  base({
    id: 'queue-by-stacks',
    title: '2. 用栈实现队列（232）',
    subtitle: '双栈倒腾 · 均摊 O(1)',
    difficulty: '基础',
    estMinutes: 20,
    keywords: ['232', '双栈'],
    points: [
      'push：直接压入 in 栈。',
      'pop/peek：若 out 为空，把 in 栈元素依次弹出并压入 out，再从 out 弹出。',
      '均摊分析：每个元素最多入栈出栈各两次，均摊 O(1)。',
    ],
    pitfalls: ['只在 pop 时倒栈会导致最坏 O(n)；peek 与 pop 逻辑要一致。'],
    main: { id: 232, title: '用栈实现队列', slug: 'implement-queue-using-stacks' },
  }),
  base({
    id: 'stack-by-queues',
    title: '3. 用队列实现栈（225）',
    subtitle: '单队列轮转 · 或双队列',
    difficulty: '基础',
    estMinutes: 20,
    keywords: ['225', '队列'],
    points: [
      '单队列法：push 时把新元素入队后，把前面 size-1 个元素依次 dequeue 再 enqueue，使新元素到队头。',
      '双队列法：push 到空队列，再把另一队列元素全部移过来，交换角色。',
    ],
    main: { id: 225, title: '用队列实现栈', slug: 'implement-stack-using-queues' },
  }),
  base({
    id: 'valid-parentheses',
    title: '4. 有效的括号（20）',
    subtitle: '栈匹配 · 三种括号',
    difficulty: '入门',
    estMinutes: 15,
    keywords: ['20', '栈'],
    points: [
      '遇左括号入栈；遇右括号若栈空或栈顶不匹配则 false。',
      '遍历结束栈必须为空。',
      '可用 map 存右→左对应关系，代码更短。',
    ],
    main: { id: 20, title: '有效的括号', slug: 'valid-parentheses' },
    related: [{ id: 1047, title: '删除字符串中的所有相邻重复项', slug: 'remove-all-adjacent-duplicates-in-string' }],
  }),
  base({
    id: 'remove-adjacent',
    title: '5. 删除相邻重复项（1047）',
    subtitle: '栈模拟消除 · 也可双指针原地',
    difficulty: '基础',
    estMinutes: 18,
    keywords: ['1047', '栈'],
    points: [
      '栈顶与当前字符相同则 pop，否则 push。',
      '最终栈中字符拼接即为结果。',
      '与消消乐类似，连续段一次性消掉。',
    ],
    main: { id: 1047, title: '删除字符串中的所有相邻重复项', slug: 'remove-all-adjacent-duplicates-in-string' },
  }),
  base({
    id: 'eval-rpn',
    title: '6. 逆波兰表达式（150）',
    subtitle: '遇运算符弹出两数计算再入栈',
    difficulty: '基础',
    estMinutes: 20,
    keywords: ['150', '栈'],
    points: [
      '数字入栈；运算符弹出 b、a，计算 a op b 再入栈（注意顺序）。',
      '最后栈中应剩一个数。',
      '用 long 或检查溢出视题目要求而定。',
    ],
    main: { id: 150, title: '逆波兰表达式求值', slug: 'evaluate-reverse-polish-notation' },
  }),
  base({
    id: 'sliding-window-max',
    title: '7. 滑动窗口最大值（239）',
    subtitle: '单调递减双端队列 · 存下标',
    difficulty: '进阶',
    estMinutes: 35,
    keywords: ['239', '单调队列'],
    points: [
      'deque 存下标，队头对应当前窗口最大值。',
      '新元素入队前，从队尾弹出所有值 ≤ 当前值的元素下标。',
      '队头下标超出窗口左边界则 pop_front。',
      '每个下标最多入队出队各一次，O(n)。',
    ],
    pitfalls: ['存值而非下标会导致窗口收缩时无法判断是否过期。'],
    main: { id: 239, title: '滑动窗口最大值', slug: 'sliding-window-maximum' },
  }),
  base({
    id: 'top-k-frequent',
    title: '8. 前 K 个高频元素（347）',
    subtitle: '哈希计数 + 小顶堆 / 桶排序',
    difficulty: '进阶',
    estMinutes: 30,
    keywords: ['347', '堆', '桶'],
    points: [
      'map 统计频次；维护大小为 k 的小顶堆，堆顶是 k 个里频次最小的。',
      '桶排序：下标为频次，桶内放该频次所有数，从高桶往下取 k 个。',
      '堆解法 O(n log k)，桶排序 O(n) 当频次范围可控时。',
    ],
    main: { id: 347, title: '前 K 个高频元素', slug: 'top-k-frequent-elements' },
  }),
  base({
    id: 'summary',
    title: '9. 栈与队列篇总结',
    subtitle: '实现互模拟 · 括号 · 单调队列 · 堆',
    difficulty: '入门',
    estMinutes: 10,
    keywords: ['总结'],
    points: [
      '实现题：232/225 理解倒栈与轮转；面试常手写。',
      '栈：20 括号、1047 消除、150 表达式。',
      '队列扩展：239 单调队列是难点；347 结合堆或桶。',
    ],
    checklist: ['能独立写出 232 与 20', '能解释 239 为何 deque 存下标'],
  }),
]

export const STACK_QUEUE_SECTIONS = applyStackQueueEnrichment(STACK_QUEUE_SECTIONS_RAW)

export const STACK_QUEUE_COUNT = STACK_QUEUE_SECTIONS.length

export const STACK_QUEUE_EXTRA: GuideTableBlock[] = [
  {
    sectionId: 'theory',
    title: '栈 vs 队列速查',
    hint: '与 开篇对照：先判断访问顺序约束，再选结构。',
    columns: [
      { prop: 'structure', label: '结构', width: 80 },
      { prop: 'order', label: '顺序', width: 100 },
      { prop: 'ops', label: '核心操作', minWidth: 140 },
      { prop: 'typical', label: '典型题', minWidth: 160 },
    ],
    data: [
      { structure: '栈', order: 'LIFO', ops: 'push / pop 栈顶', typical: '20 括号、150 表达式、DFS' },
      { structure: '队列', order: 'FIFO', ops: 'push 尾 / pop 头', typical: 'BFS、232 实现、层序' },
      { structure: 'deque', order: '两端', ops: '头尾 push/pop', typical: '239 滑动窗口最大值' },
    ],
  },
]
