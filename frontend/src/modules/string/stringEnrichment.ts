/**
 * 字符串各节加厚内容（overview + topicBlocks），合并进 stringCurriculum
 * 字符串模块 enrichment
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const STRING_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应《关于字符串，你该了解这些！》。要点：字符串题常考「能否原地、能否用库函数、双指针从哪端写」。本节建立语言差异（C++/Java/Python 可变性）与 O(1) 空间下的通用思路，再进入 344 等具体题。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '字符串在内存与语言中的差异',
        points: [
          'C 风格 `char[]` 以 `\\0` 结束；C++ `string` 用 `size()`，刷题更常用 `string` 或 `vector<char>`。',
          'C++ `string`、C 数组通常可原地改；Java `String` 不可变，力扣原地题先 `toCharArray()`；Python `str` 不可变，需新缓冲或题目允许的辅助空间。',
          '力扣「O(1) 额外空间」在可改 char 数组上 = 下标双指针或先扩容再从后往前写，与数组篇移除/合并同族。',
          '空格、大小写：面试默认 ASCII；Unicode/emoji 题需单独读题。',
        ],
      },
      {
        title: '库函数原则（开篇必记）',
        points: [
          '打基础阶段：若题目核心一步靠 `reverse` / `split` / `erase` 一行搞定，面试不建议直接交卷——你应能讲清原理与复杂度。',
          '辅助步骤且你明确其代价（如单次 `erase` O(n)）时，可酌情使用；但 for 里反复 `erase` 去空格 → 整体 O(n²)，短测例可能 AC，面试会被追问。',
          '字符串题「想法简单、实现易错」：先画下标再走模板，比死记 API 更稳。',
        ],
      },
    ],
    extraPitfalls: ['把 `s[s.length()]` 当合法下标；`left < right` 与 `left <= right` 混用导致多交换。'],
    extraChecklist: ['能说明本语言字符串可变与否；能复述库函数两条原则。'],
  },
  'reverse-string': {
    overview:
      '344 反转字符串：与 206 反转链表同族，用左右相向双指针对称交换。字符串连续存储、下标 O(1)，是双指针与反转族的入门题；理解 swap 比背 `reverse` 更重要。',
    estMinutes: 25,
    topicBlocks: [
      {
        title: '标准模板与循环不变量',
        points: [
          '`left = 0`，`right = n - 1`，`while (left < right)` 交换后 `left++`、`right--`。',
          '不变量：每次循环后，区间 `[0, left)` 与 `(right, n-1]` 中的字符已处于最终位置。',
          '提示：可用 `swap`（你已知交换原理）；不建议直接 `reverse` 整段——考点被库函数替代。',
          '与 206 对照：链表改 `next`，字符串改下标交换，难度更低。',
        ],
      },
      {
        title: '拓展与相关题',
        points: [
          '345 只反转元音：相向指针跳过非元音再交换，模板相同。',
          '区间反转 `reverseRange(s, L, R)` 建议左闭右闭，供 541、151、58-II 复用。',
          '复杂度：时间 O(n)，指针 O(1) 额外空间。',
        ],
      },
    ],
    extraPitfalls: ['`right` 初值写成 `n` 而非 `n-1`；只反转一半区间。'],
  },
  'reverse-string-ii': {
    overview:
      '541 反转字符串 II：按步长 `2k` 分段，每段只反前 `k` 个（不足则反到段尾）。外层 `for (i += 2k)` 直接跳组起点，内层调用与 344 相同的区间反转。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '规则与 for 写法',
        points: [
          '从起点每 `2k` 字符为一组：若本组长度 ≥ `k`，反转 `[i, i+k-1]`；若剩余 < `k`，反转 `[i, n-1]`。',
          '统一写法：`for (int i = 0; i < n; i += 2 * k)`，`end = min(i + k - 1, n - 1)`，再 `reverseRange(s, i, end)`。',
          '两种等价分支：`if (i + k <= n) reverse(i, i+k-1) else reverse(i, n-1)`；理解一种即可。',
          '不要在内层误用 `i + 2k - 1` 作为反转右端点。',
        ],
      },
      {
        title: '手画边界与工具函数',
        points: [
          '当 `n` 不是 `2k` 整数倍时，最后一组可能「不足 k 整段反」或「不足 2k 只反一段」。',
          '抽离 `reverseRange(start, end)` 左闭右闭，与后续 151、左旋共用，减少边界 bug。',
          '每字符参与反转常数次，总体 O(n)。',
        ],
      },
    ],
    extraPitfalls: ['`i + k` 与 `n` 比较时用 `<=` 还是 `<` 必须与区间定义一致。'],
  },
  'replace-space': {
    overview:
      '剑指 Offer 05 替换空格：每个空格变 `%20` 多 2 字符。先统计空格并扩容，再双指针从后往前填——「填充类」通用套路，与 27 移除元素、数组合并从尾写入同族。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: '为何必须从后往前',
        points: [
          '新长度 = `oldSize + 2 * spaceCount`（每个空格 +2，不是 +3）。',
          '`i` 指向新串末尾，`j` 指向旧串末尾；非空格 `s[i--]=s[j--]`；空格依次写 `0`、`2`、`%` 后 `i -= 3`。',
          '从前向后填会把尚未处理的字符顶走，等价反复后移 → O(n²)；从后向前每位只写一次 → O(n)。',
          '能举反例：若从前填，未读字符被覆盖，无法恢复。',
        ],
      },
      {
        title: '与双指针篇的串联',
        points: [
          '提示：到本节已完成 27、15、18、206、142、344 等多道双指针题，说明技巧跨数组/字符串/链表。',
          'C++ `resize` 后可写；Java 常用 `StringBuilder` 或 char 数组思维。',
          '写入 `%20` 的顺序必须与「从后往前」一致，先写最右字符 `0`。',
        ],
      },
    ],
    extraPitfalls: ['新长度写成 `+ 3 * spaceCount`；`i/j` 初值未指向扩容量后的最后有效下标。'],
  },
  'reverse-words': {
    overview:
      '151 反转字符串中的单词：O(1) 额外空间 = 快慢压缩冗余空格 → 整体反转 → 逐单词区间反转。勿用 `split`+新串（失去练习价值）；勿 for 里 `erase`（O(n²)）。',
    estMinutes: 55,
    topicBlocks: [
      {
        title: '三步模板（必背顺序）',
        points: [
          '① `removeExtraSpaces`：快慢指针思想同 27，慢指针写、快指针读，单词间只留一个空格，去掉首尾空格。',
          '② `reverse(0, n-1)` 整串反转，此时单词内字符也被反转。',
          '③ 扫描空格边界，对每个单词 `reverse(start, end)`，单词内顺序恢复，单词顺序已反。',
          '示例：`"the sky is blue"` → 压缩 → 全反 → 分词反 → `"blue is sky the"`。',
        ],
      },
      {
        title: '实现细节与复杂度',
        points: [
          '在 `i == n` 或 `s[i] == \' \'` 时反转 `[start, i-1]`，再 `start = i + 1`。',
          'C++ `istringstream` 可帮助理解题意，面试仍推荐原地双指针 + 区间反转。',
          '压缩 + 两次反转扫描均为 O(n)；语言允许改 char 数组时为 O(1) 额外空间。',
          '只做一次整体反转会导致单词内也被反转且未调序——必做第三步。',
        ],
      },
    ],
    extraPitfalls: ['多空格、首尾空格、全空格、单单词未测；区间左闭右开与左闭右闭混用。'],
  },
  'left-rotate': {
    overview:
      '剑指 Offer 58-II 左旋转字符串：把前 `n` 个字符移到尾部。三步反转 `reverse(0,k-1)` → `reverse(k,end)` → `reverse(0,end)`，与 189 轮转数组完全一致；与 151「先整体后局部」互为镜像。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: '三次反转区间',
        points: [
          '题意：`"abcdefg", n=2` → `"cdefgab"`；题目要求不申请额外空间，在本串操作。',
          '令 `k = n`：`reverse(0, k-1)` 反左段；`reverse(k, len-1)` 反右段；`reverse(0, len-1)` 反整串。',
          '与 151 对照：151 先整体再局部调单词序；左旋先局部再整体搬左段——反转技巧的可逆组合。',
          '循环左移一位重复 n 次 → O(n²)，面试应拒绝。',
        ],
      },
      {
        title: 'substr 对比',
        points: [
          '`substr` 拼接时间 O(n) 但空间 O(n)；三反转在可原地 char 数组时空间 O(1)，面试更推崇后者。',
          '能背诵三个反转区间的端点；注意题面 `k` 与数组长度 `n` 变量名勿混淆。',
          '796 旋转字符串等变体可回到「反转 / KMP / 双倍串」思路选型。',
        ],
      },
    ],
  },
  kmp: {
    overview:
      '28 实现 strStr（KMP）：前缀表（最长相等前后缀）+ next 数组，失配时主串 `i` 不回退。建议配合手算示例手算 `aabaaf`，勿死记模板；「减一 / 不减一」两套公式全程固定一套。',
    estMinutes: 95,
    topicBlocks: [
      {
        title: '前缀表含义与手算',
        points: [
          '暴力：主串失配 `i` 回退，重复比较 → O(n×m)。KMP 利用已匹配信息，只移动模式串下标。',
          '前缀表 `next[i]`（不减一常见写法）：下标 i 之前子串中，最长相等前后缀的长度；前缀不含末字符、后缀不含首字符的严格定义以你选用的版本为准。',
          '手算 `aabaaf`：`0,1,0,1,2,0`。文本 `aabaabaafa` 末位失配时，看前一位置值 2，模式串跳到与已匹配前缀对齐处。',
          '空模式串返回 0；命中时返回 `i - m + 1`（写法随 j 定义略变）。',
        ],
      },
      {
        title: '构造 next 与匹配（固定一套写法）',
        points: [
          '不减一构造：`next[0]=0`；`for i=1,j=0`：`while (j>0 && needle[i]!=needle[j]) j=next[j-1]`；相等则 `j++`；`next[i]=j`。',
          '减一版本：前缀表整体减一、`j` 初值 -1，失配 `j=next[j]`，比较 `s[i]` 与 `s[j+1]`——与上式等价但勿混用回退公式。',
          '主串指针单调不减 → 构造 O(m) + 匹配 O(n) = O(n+m)；空间 O(m)。',
          '彻底理解比背代码重要：能答出失配时为何跳到 `next[j-1]` 对应的前缀位置。',
        ],
      },
    ],
    extraPitfalls: ['next 下标含义与减一/不减一版本混用；构造时 i 从 0 还是从 1 与所选版本不一致。'],
    extraChecklist: ['能手算 `aabaaf` 前几项并解释失配跳转；能说明主串 i 为何线性。'],
  },
  'repeated-substring': {
    overview:
      '459 重复的子字符串：暴力枚举子串长度 O(n²)；推荐移动匹配（`s+s` 掐头去尾）或 KMP 用 `next[len-1]` 判周期。核心直觉：重复串的最长相等前后缀对应最小重复单元。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: '移动匹配（s+s 掐头去尾）',
        points: [
          '若 `s` 由子串重复构成，则 `s+s` 去掉首尾各一字符后，中间仍包含完整 `s`。',
          '实现：`t = (s+s).substring(1, 2*len-1)`，再判断 `t` 是否包含 `s`；注意构造辅助串的 O(n) 空间。',
          '勿忘记「掐头去尾」，否则会在原串起始位置误匹配。',
          '理解后可与 KMP 解法对照，面试能说清两种思路的时空权衡。',
        ],
      },
      {
        title: 'KMP 判周期（两种 next 定义）',
        points: [
          '不减一：若 `next[len-1] > 0` 且 `len % (len - next[len-1]) == 0` → 重复串；`len - next[len-1]` 为最小周期长度。',
          '减一版本：`next[len-1] != -1` 且 `len % (len - (next[len-1]+1)) == 0`；与上式等价但勿混用 next 定义。',
          '直觉：`ababab` 最小单元 `ab`；对 `aba` 等无重复结构，条件应排除。',
          '只做 `len % k == 0` 未结合 next 可能误判。',
        ],
      },
    ],
  },
  summary: {
    overview:
      '字符串篇总结：库函数原则、双指针、反转族、KMP 两类经典题。建议 151 与 28 各手写一遍并口述不变量；结合本节《字符串总结》查漏补缺。',
    estMinutes: 30,
    topicBlocks: [
      {
        title: '四条主线复盘',
        points: [
          '库函数：关键步骤一行库函数能过 → 不建议；辅助且懂复杂度 → 可考虑。警惕 `erase`、`split`、`reverse` 滥用。',
          '双指针：344 对称交换；剑指 05 / 151 去空格与从后填；27 移除思想在 151 压缩空格中复现。',
          '反转族：344 整串 → 541 分段 2k → 151（整体+局部）→ 58-II（局部+整体）；`for` 里 `i += 2k` 处理规律分段。',
          'KMP：① 匹配 28；② 重复子串 459。核心都是前缀表 / next。',
        ],
      },
      {
        title: '学习顺序与自测',
        points: [
          '推荐顺序：344 → 541 → 剑指 05 → 151 → 58-II → 28 → 459 → 总结；KMP 配合示意动画暂停手算。',
          '字符串题想法常简单、实现易错；复杂题考验代码掌控力。',
          '能说明 151 与 58-II 在反转顺序上的对称关系；能各举一题说明「从后往前」为何 O(n)。',
        ],
      },
    ],
    summaryPoints: ['复盘时先画下标再写代码，比死记 API 更稳。'],
  },
}

export function applyStringEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, STRING_ENRICHMENT)
}
