/** 字符串学习模块 — 知识结构 */

import type { LearnSection } from '@/modules/shared/learningTypes'
import { leetcodeCnUrl } from '@/modules/shared/learningTypes'
import { applyStringEnrichment } from './stringEnrichment'

export { leetcodeCnUrl }

export type DifficultyLabel = LearnSection['difficulty']
/** 剑指系列题可用 `badge` 代替「力扣题号」展示 */
export interface StringPracticeLink extends NonNullable<LearnSection['main']> {
  badge?: string
}

export interface StringSection extends LearnSection {
  main?: StringPracticeLink
  related?: StringPracticeLink[]
}

export const STRING_CURRICULUM_INTRO =
  '字符串题常围绕「原地修改、双指针、分段反转、模式匹配」展开。建议顺序：344 → 541 → 剑指 05 → 151 → 剑指 58-II → 28（KMP）→ 459 → 总结；打基础时别只调库函数而不懂原理。KMP 请配合示意动画手算前缀表。每节先画例子再走模板，并对照视频讲解补齐直觉。'

const STRING_SECTIONS_RAW: StringSection[] = [
  {
    id: 'theory',
    title: '1. 关于字符串，你该了解这些！',
    subtitle: '字符序列在内存中的表示、语言可变性，以及「库函数能不能用」的面试原则。',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['可变性', 'char[]', '\\0', '库函数原则', '双指针'],
    points: [
      '字符串是有限字符序列，可视为字符数组；C/C++ 中 C 风格串用 `\\0` 标记结束，循环常写 `a[i] != \'\\0\'`；C++ `string` 用 `size()` 判断长度，不依赖结束符。',
      '`vector<char>` 与 `string` 在基本读写上相近，但 `string` 提供 `+`、查找等接口，刷题与工程里处理文本更常用 `string`。',
      'C++ `string`、C `char[]` 通常可原地修改；Java `String` 不可变，力扣「原地」题常先 `toCharArray()` 或 `StringBuilder`；Python `str` 不可变，需在新缓冲或题目放宽的 O(n) 辅助空间上操作。',
      '开篇强调：打基础时不要太迷恋库函数。若题目关键步骤靠一行 `reverse` / `split` 就能过，面试不建议直接用；若只是辅助且你清楚其时间复杂度（如 `erase` 单次 O(n)），可酌情使用。',
      '力扣要求「O(1) 额外空间」时，优先考虑左右对称双指针、或「先扩容再从后往前写」——与数组篇 27（移除元素）、合并类题目同一思想族。',
      '空格语义、大小写、Unicode：面试多数按 ASCII 单字节处理；遇 emoji / 组合字符再单独读题。',
    ],
    pitfalls: [
      '把 `s[s.length()]` 当成合法下标；`left < right` 与 `left <= right` 混用导致多交换或死循环。',
      'Java 中 `s[i]` 不存在，需 `charAt(i)` 或 `toCharArray()`。',
      '在循环里反复 `erase` 去空格：单次 erase 为 O(n)，套 for 后整体 O(n²)，短测例可能 AC 但面试会被追问复杂度。',
    ],
    checklist: [
      '能说明本机主力语言里字符串可变与否及常见写法。',
      '能复述「关键步骤能否用库函数」的两条原则（ 总结篇）。',
    ],
    complexityHint: '单字符访问 O(1)；整串扫描 O(n)；是否可原地取决于语言与题面。',
  },
  {
    id: 'reverse-string',
    title: '2. 反转字符串',
    subtitle: '与 206 反转链表同族：左右双指针对称交换；字符串因连续存储通常更简单。',
    difficulty: '基础',
    estMinutes: 20,
    keywords: ['344', '双指针', '对称交换', '库函数原则'],
    points: [
      '题意：原地反转 `char[]`，O(1) 额外空间；与链表反转一样用双指针，但下标访问 O(1)，无需改指针域。',
      '令 `left = 0`，`right = n - 1`，`while (left < right)` 交换 `s[left]`、`s[right]` 后 `left++`、`right--`。',
      '提示：可用 `swap` 库函数（你已知交换原理且非题目核心）；不建议直接 `reverse` 整段——那等于把考点交给库函数。',
      '与 206 对照记忆：链表用 `prev/cur/next`，字符串用下标向中间收拢。',
    ],
    pitfalls: ['只反转一半区间；`right` 初值写成 `n` 而非 `n-1`。'],
    checklist: ['能手写循环不变量：每次交换后，外侧已确定最终位置的字符区间向中间扩展。'],
    complexityHint: '时间 O(n)，指针 O(1) 额外空间。',
    codeSketch: `void reverseRange(char[] s, int L, int R) {
  while (L < R) {
    char t = s[L]; s[L] = s[R]; s[R] = t;
    L++; R--;
  }
}
// 整串反转：reverseRange(s, 0, s.length - 1);`,
    main: { id: 344, title: '反转字符串', slug: 'reverse-string' },
    related: [{ id: 345, title: '反转字符串中的元音字母', slug: 'reverse-vowels-of-a-string' }],
  },
  {
    id: 'reverse-string-ii',
    title: '3. 反转字符串 II',
    subtitle: '固定步长 2k 分段：每段前 k 个反转；for 表达式写 `i += 2k` 比额外计数器更清晰。',
    difficulty: '基础',
    estMinutes: 35,
    keywords: ['541', '分段', '区间反转', 'i += 2k'],
    points: [
      '规则：从起点每 `2k` 个字符为一组，反转每组前 `k` 个；剩余 ≥k 则只反前 k；剩余 <k 则整段反转。',
      '外层 `for (int i = 0; i < n; i += 2 * k)` 直接跳到每组起点，不必再套计数器统计 2k。',
      '内层对闭区间 `[i, min(i + k - 1, n - 1)]` 调用区间反转（与 344 相同双指针）。',
      '两种写法等价：① `if (i + k <= n) reverse(i, i+k-1) else reverse(i, n-1)`；② 先 `reverse(i, i+k-1)` 再 `i += 2k`（注意边界）。',
      '区间反转函数建议左闭右闭 `[start, end]`，与后续 151、58-II 共用一套工具函数。',
    ],
    pitfalls: [
      '内层右端点误用 `i + 2k - 1`；`i + k` 与 `n` 比较时用 `<=` 还是 `<` 与区间定义不一致。',
    ],
    checklist: ['能手画 n 不是 2k 整数倍时最后一组的两种情形。'],
    complexityHint: '每字符参与反转常数次，总体 O(n)。',
    codeSketch: `for (int i = 0; i < n; i += 2 * k) {
  int end = Math.min(i + k - 1, n - 1);
  reverseRange(s, i, end);
}`,
    main: { id: 541, title: '反转字符串 II', slug: 'reverse-string-ii' },
    related: [{ id: 345, title: '反转字符串中的元音字母', slug: 'reverse-vowels-of-a-string' }],
  },
  {
    id: 'replace-space',
    title: '4. 替换空格（剑指 Offer 05）',
    subtitle: '先扩容再双指针从后往前填，避免覆盖未读字符——数组「填充类」通用套路。',
    difficulty: '基础',
    estMinutes: 40,
    keywords: ['扩容', '从后往前', '双指针', 'O(n)'],
    points: [
      '每个空格变 `%20` 多 2 个字符：先统计 `spaceCount`，新长度 `oldSize + 2 * spaceCount`（`resize` / 预留容量）。',
      '双指针：`i` 指向新串末尾，`j` 指向旧串末尾；`j` 非空格则 `s[i--]=s[j--]`；是空格则依次写入 `0`、`2`、`%` 并 `i -= 3`。',
      '从前向后填会把尚未处理的字符顶走 → 等价于反复后移，最坏 O(n²)；从后向前每个位置只写一次 → O(n)。',
      '串联：至此双指针题已涵盖 27、15、18、206、142、344 等，本题与「移除元素」快慢指针、合并从尾写入同族。',
    ],
    pitfalls: [
      '新长度写成 `+ 3 * spaceCount` 或漏乘 2；`i/j` 初值未指向扩容量后的最后一个有效下标。',
      '写入 `%20` 时顺序错误（应先写 `%` 对应的最右字符还是最左，要与从后往前一致）。',
    ],
    checklist: ['能口述为何必须从后往前，并举一个从前填会覆盖的反例。'],
    complexityHint: '线性扫描 + 线性写入；在原 char 数组上为 O(n) 时间、O(1) 额外空间。',
    codeSketch: `// 1) 统计空格并 resize
// 2) for (i = newSize-1, j = oldSize-1; j < i; )
//    非空格: s[i--] = s[j--];
//    空格: s[i--]='0'; s[i--]='2'; s[i--]='%';`,
    main: {
      id: 0,
      title: '替换空格',
      slug: 'ti-huan-kong-ge-lcof',
      badge: '剑指 Offer 05',
    },
    related: [
      { id: 27, title: '移除元素', slug: 'remove-element' },
      { id: 844, title: '比较含退格的字符串', slug: 'backspace-string-compare' },
    ],
  },
  {
    id: 'reverse-words',
    title: '5. 反转字符串中的单词',
    subtitle: 'O(1) 额外空间：去冗余空格 → 整体反转 → 逐单词反转；勿用 split 堆新串。',
    difficulty: '基础',
    estMinutes: 50,
    keywords: ['151', 'trim', '整体+局部反转', 'erase O(n²)'],
    points: [
      '题意：单词内字符顺序不变，单词顺序反转；首尾与单词间只保留一个空格。',
      '三步：① 快慢指针压缩空格（思想同 27.移除元素，慢指针写、快指针读）；② `reverse(0, n-1)`；③ 扫描空格边界，对每个单词 `reverse(start, end)`。',
      '示例：`"the sky is blue"` → 去空格 → 整体反得 `"eulb si yks eht"` → 分词反回 `"blue is sky the"`。',
      '提示：用 `split` + 新 `string` 拼接是 O(n) 时间但 O(n) 空间且失去练习价值；`erase` 去空格在 for 里套 erase 为 O(n²)。',
      'C++ `istringstream` 可帮助理解题意，面试仍推荐掌握原地双指针 + 区间反转模板。',
    ],
    pitfalls: [
      '只做一次整体反转导致单词内也被反转；忘记第二步按单词再反转。',
      '多空格、首尾空格、全空格、单单词未测；`reverse` 区间写成左闭右开与闭闭混用。',
    ],
    checklist: ['能手画三步前后下标；能说明为何 erase 去空格是 O(n²)。'],
    complexityHint: '压缩 + 两次反转扫描均为 O(n)；原地 O(1) 额外空间（语言允许改 char 数组时）。',
    codeSketch: `removeExtraSpaces(s);
reverse(s, 0, s.length - 1);
for (int i = 0, start = 0; i <= s.length; i++) {
  if (i == s.length || s[i] == ' ') {
    reverse(s, start, i - 1);
    start = i + 1;
  }
}`,
    main: { id: 151, title: '反转字符串中的单词', slug: 'reverse-words-in-a-string' },
    related: [{ id: 186, title: '反转字符串中的单词 II', slug: 'reverse-words-in-a-string-ii' }],
  },
  {
    id: 'left-rotate',
    title: '6. 左旋转字符串（剑指 Offer 58 - II）',
    subtitle: '先局部反转再整体反转，与 151「先整体再局部」互为镜像；等同 189 轮转数组。',
    difficulty: '基础',
    estMinutes: 30,
    keywords: ['旋转', '三次反转', 'substr 对比'],
    points: [
      '题意：把前 `n` 个字符移到尾部，如 `"abcdefg", n=2` → `"cdefgab"`；题目要求不申请额外空间，在本串操作。',
      '三步（令 k = n）：`reverse(0, k-1)` → `reverse(k, end)` → `reverse(0, end)`；与 189.轮转数组完全一致。',
      '与 151 对照：151 是「先整体后局部」调单词序；左旋是「先局部后整体」搬左段——反转技巧的可逆组合。',
      '提示：`substr` 拼接时间 O(n) 但空间 O(n)；三反转空间 O(1)（可原地改 char 数组时），面试更推崇后者。',
    ],
    pitfalls: ['用循环左移一位重复 n 次 → O(n²)；题面 `k` 与数组长度 `n` 变量名混淆。'],
    checklist: ['能背诵三个反转区间的端点；能对比 substr 与三反转的时空复杂度。'],
    complexityHint: '三次线性扫描 O(n)；O(1) 额外空间（原地 char 数组）。',
    codeSketch: `int k = n;
reverse(s, 0, k - 1);
reverse(s, k, s.length - 1);
reverse(s, 0, s.length - 1);`,
    main: {
      id: 0,
      title: '左旋转字符串',
      slug: 'zuo-xuan-zhuan-zi-fu-chuan-lcof',
      badge: '剑指 Offer 58 - II',
    },
    related: [{ id: 189, title: '轮转数组', slug: 'rotate-array' }],
  },
  {
    id: 'kmp',
    title: '7. 找出字符串中第一个匹配项的下标（KMP）',
    subtitle: '前缀表（最长相等前后缀）+ next 数组；失配时主串 i 不回退。',
    difficulty: '进阶',
    estMinutes: 90,
    keywords: ['28', 'next', '前缀表', 'aabaaf'],
    points: [
      '暴力：主串失配时 `i` 回退，重复比较已匹配部分 → O(n×m)。KMP 利用已匹配信息，只移动模式串下标。',
      '前缀表含义：下标 i 之前（含 i）子串中，最长相等前后缀的长度。前缀不含最后一个字符，后缀不含第一个字符；更准确说法是「最长相等前后缀」而非含糊的「公共前后缀」。',
      '手算示例 `aabaaf`（不减一版本前缀表）：`0,1,0,1,2,0`。在文本 `aabaabaafa` 中末位失配时，看前一位置前缀表值 2，模式串跳到与已匹配前缀对齐处继续比。',
      'next 实现常两种：① 前缀表整体减一、j 初值 -1，失配 `j = next[j]`，比较 `s[i]` 与 `s[j+1]`；② 不减一，失配 `j = next[j-1]`。全程固定一套，勿混用公式。',
      '构造 next：双指针 i（后缀末）、j（前缀末）；`while (j>=0 && s[i]!=s[j+1]) j=next[j]`；相等则 `j++`；`next[i]=j`。',
      '匹配：空模式串返回 0（与 C `strstr` / Java `indexOf` 一致）；`j == m-1`（或 `j==m` 视写法）时命中，返回 `i - m + 1`。',
      '复杂度：构造 O(m) + 匹配 O(n) → 总 O(n+m)；空间 O(m) 存 next。建议结合本节动画逐步暂停理解，勿死记模板。',
    ],
    pitfalls: [
      'next 下标含义与「减一 / 不减一」版本混用；把 next[i] 当成「含当前字符的最长前后缀」却按另一套回退。',
      '构造 next 时 i 从 0 还是从 1 开始与所选版本不一致。',
    ],
    checklist: [
      '能手算 `aabaaf` 前缀表前几项并解释失配时为何跳到 b。',
      '能说明主串指针为何单调不减 → 整体线性时间。',
    ],
    complexityHint: '预处理 O(m)，匹配 O(n)；空间 O(m)。',
    codeSketch: `// 前缀表「不减一」构造（力扣常见写法）
next[0] = 0;
for (int i = 1, j = 0; i < m; i++) {
  while (j > 0 && needle[i] != needle[j]) j = next[j - 1];
  if (needle[i] == needle[j]) j++;
  next[i] = j;
}`,
    main: {
      id: 28,
      title: '找出字符串中第一个匹配项的下标',
      slug: 'find-the-index-of-the-first-occurrence-in-a-string',
    },
    related: [
      { id: 1392, title: '最长快乐前缀', slug: 'longest-happy-prefix' },
      { id: 214, title: '最短回文串', slug: 'shortest-palindrome' },
    ],
  },
  {
    id: 'repeated-substring',
    title: '8. 重复的子字符串',
    subtitle: '移动匹配（s+s 掐头去尾）或 KMP：len % 周期长度 == 0 且存在非平凡前后缀。',
    difficulty: '进阶',
    estMinutes: 45,
    keywords: ['459', 's+s', '周期', 'next'],
    points: [
      '暴力：枚举子串长度至 n/2，判断能否铺满 → O(n²)；建议理解后上更高效写法。',
      '移动匹配：若 `s` 由子串重复构成，则 `s+s` 掐头去尾后仍包含 `s`（中间拼接处会出现完整 s）；实现可用 KMP 找子串，勿忽略 `find` 的复杂度。',
      'KMP（不减一）：`len = s.length`，若 `next[len-1] > 0` 且 `len % (len - next[len-1]) == 0` 则为重复串；`len - next[len-1]` 即最小周期长度。',
      'KMP（减一版本，代码）：需 `next[len-1] != -1` 且 `len % (len - (next[len-1] + 1)) == 0`；与上一式等价但勿混用 next 定义。',
      '直觉：重复串的最长相等前后缀（不含整串）对应的最小重复单元；`ababab` 最小单元 `ab`。',
    ],
    pitfalls: [
      '只做 `len % k == 0` 未结合 next，可能误判；`s+s` 忘记掐头去尾会在原串位置误匹配。',
      '对 `aba` 等无重复结构，next 条件应排除。',
    ],
    checklist: [
      '能写出 s+s 掐头去尾的判断逻辑并说明为何有效。',
      '能分别写出两种 next 定义下的判定式且不混用。',
    ],
    complexityHint: 'KMP 解法 O(n)；s+s 需 O(n) 辅助构造新串。',
    codeSketch: `// 移动匹配思路
String t = s + s;
t = t.substring(1, t.length() - 1);
return t.contains(s);

// KMP（不减一）
// period = len - next[len-1];
// return next[len-1] > 0 && len % period == 0;`,
    main: { id: 459, title: '重复的子字符串', slug: 'repeated-substring-pattern' },
  },
  {
    id: 'summary',
    title: '9. 字符串总结篇',
    subtitle: '收束 ：库函数原则、双指针、反转族、KMP 两类经典题。',
    difficulty: '入门',
    estMinutes: 25,
    keywords: ['复盘', '双指针', '反转', 'KMP'],
    points: [
      '库函数：关键步骤能一行库函数解决 → 不建议；辅助步骤且懂复杂度 → 可考虑。警惕 `erase`、`split`、`reverse` 滥用。',
      '双指针：344 对称交换；剑指 05 / 151 去空格与填充（先扩再从后填）；27 移除思想在 151 压缩空格中复现。',
      '反转族：整串（344）→ 分段 2k（541）→ 单词序（151：整体+局部）→ 左旋（58-II：局部+整体）；for 里 `i += 2k` 处理规律分段。',
      'KMP 两类题：① 匹配问题 28；② 重复子串 459。核心都是前缀表 / next；彻底理解比背模板重要。',
      '字符串题想法常简单、实现易错；复杂题考验代码掌控力。建议 151 与 28 至少各手写一遍并口述不变量。',
    ],
    pitfalls: ['KMP 仅背代码，答不出 next[i] 含义与失配跳转原因。'],
    checklist: [
      '能列出四个主套路并各举一题号。',
      '能说明 151 与 58-II 在反转顺序上的对称关系。',
    ],
    complexityHint: '本篇以 O(n) 扫描为主；KMP 为 O(n+m)。',
    related: [
      { id: 796, title: '旋转字符串', slug: 'rotate-string' },
      { id: 415, title: '字符串相加', slug: 'add-strings' },
      { id: 58, title: '最后一个单词的长度', slug: 'length-of-last-word' },
    ],
  },
]

export const STRING_SECTIONS = applyStringEnrichment(STRING_SECTIONS_RAW)

export const STRING_SECTION_COUNT = STRING_SECTIONS.length
