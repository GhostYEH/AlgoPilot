/**
 * 哈希表各节加厚内容（overview + topicBlocks），合并进 hashTableCurriculum
 * 
 */
import type { LearnSection } from '@/modules/shared/learningTypes'
import { mergeEnrichment, type SectionEnrichment } from '@/modules/shared/sectionEnrichment'

export type { SectionEnrichment }

export const HASH_TABLE_ENRICHMENT: Record<string, SectionEnrichment> = {
  theory: {
    overview:
      '对应《哈希表理论基础》。核心用途：用额外空间换 O(1) 均摊的「是否出现过」查询。刷题三件套：定长数组（值域小）、unordered_set（只要 key）、unordered_map（key→value）。理解碰撞与取模，但面试写题通常按均摊 O(1) 即可。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '何时想到哈希',
        points: [
          '需要快速判断某元素是否在集合里：朴素 O(n) 扫描 → 哈希均摊 O(1)。',
          '不仅要「存在」，还要「另一个属性」（下标、次数、配对信息）→ map。',
          '值域小且连续（如 26 字母、0–1000）→ 直接用数组当下标，常数更小。',
        ],
      },
      {
        title: '哈希函数与碰撞（刷题直觉）',
        points: [
          '哈希函数把 key 映射到表索引；越界时常对表长取模。',
          '碰撞：多 key 同索引；拉链法（桶挂链表）、线性探测（向后找空位）。',
          '线性探测要求表长大于数据量；力扣底层容器已封装，重在选型而非手写表。',
        ],
      },
      {
        title: '容器选型（C++/Java 系）',
        points: [
          'unordered_map / HashMap：均摊 O(1)，无序；需要有序用 map/TreeMap 为 O(log n)。',
          'unordered_set / HashSet：去重 + 存在性；不能存「值→下标」这类二元信息。',
          '定长数组：242/383/范围收紧的 349；不要「万物 map」浪费常数。',
        ],
      },
    ],
    summaryPoints: ['空间换时间；先问 key/value 各是什么，再选数组/set/map。'],
    extraPitfalls: [
      '值域巨大仍开「以元素值为下标」的数组导致 MLE。',
      '需要有序却用 unordered_*，或需要 O(1) 查下标却只用 set。',
    ],
    extraChecklist: [
      '能口述三种载体各自典型题号。',
      '能解释碰撞在刷题中为何通常只按均摊理解。',
    ],
  },
  'valid-anagram': {
    overview:
      '对应《有效的字母异位词》242。最朴素的哈希：int[26] 计数。异位词 = 两个 multiset 相等；先对 s 做 ++，再对 t 做 --，全零则 true。暴力 O(n²) 仅作对照。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '计数数组模板',
        points: [
          '限定小写英文：record[26]，映射 s[i]-\'a\' 得 0…25，勿死记绝对 ASCII。',
          '第一遍遍历 s：record[s[i]-\'a\']++；第二遍 t：对应位置 --。',
          '任意位置非零则 false；全零 true。',
        ],
      },
      {
        title: '何时不用 26 数组',
        points: [
          '字符集大或 Unicode：sort 后比较，或 unordered_map 计数。',
          '49 字母异位词分组：把计数数组编码成 key 字符串，或 sort 每个串作 key。',
          '与 383 区别：242 双向一致；383 是 magazine 能否覆盖 ransom（单向减法）。',
        ],
      },
      {
        title: '复杂度与拓展',
        points: [
          '时间 O(n)，空间 O(1)（26 为常数）。',
          '理解「 multiset 相等」有助于迁移到滑动窗口 + 计数（438 等）。',
          '面试可提：sort 解法 O(n log n) 更简单但渐近更差。',
        ],
      },
    ],
    extraPitfalls: ['用 map 也能过，但小字母表上数组更简单，勿盲目 map。'],
    extraChecklist: ['能手写 242 双遍计数。', '能说明 s[i]-\'a\' 的含义。'],
  },
  intersection: {
    overview:
      '对应《两个数组的交集》349。输出元素唯一、顺序不限 → set 表达「是否出现」。值域未知不宜开大数组；力扣加强数据后 0–1000 也可用定长数组标记。与 350 的区别：350 要计数出现次数，用 map 或双指针+排序。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: 'unordered_set 主流程',
        points: [
          '遍历 nums1 放入 set；遍历 nums2，若 set.count(x) 则加入结果 set 并可选 erase 防重复计数。',
          '结果转 vector；时间 O(m+n)，空间 O(m+n)。',
          'unordered_set 比数组多哈希开销；能数组时不必盲目 set。',
        ],
      },
      {
        title: '定长数组变体（值域收紧）',
        points: [
          '若元素在 [0,1000]：bool/ int 表标记 nums1 出现，再扫 nums2 收集。',
          '时空常为 O(m+n)，常数优于通用哈希。',
          '补充说明：数据范围是选题依据，读题先看 constraints。',
        ],
      },
      {
        title: '与 350 对照',
        points: [
          '349：每个值最多出现一次于输出 → set 足够。',
          '350：输出要出现 min(count1,count2) 次 → map 计数或排序双指针。',
          '双数组交集 vs 单数组去重：思路不同，勿混模板。',
        ],
      },
    ],
    extraChecklist: ['能解释为何值域未知时用 set。', '能说出 349 与 350 输出语义差别。'],
  },
  'happy-number': {
    overview:
      '对应《快乐数》202。反复求各位平方和，到 1 则 true，否则可能无限循环。关键：循环中 sum 会重复 → 用 set 记录出现过的和，重复即 false。也可用 Floyd 快慢指针判环，空间 O(1)。',
    estMinutes: 45,
    topicBlocks: [
      {
        title: 'set 判重复',
        points: [
          'getSum(n)：while(n){ sum+=(n%10)*(n%10); n/=10; } 注意是平方不是 n%10^2 优先级坑。',
          'unordered_set 存每次 sum；sum==1 return true；已在 set 中 return false。',
          '否则 sum=getSum(sum) 继续迭代。',
        ],
      },
      {
        title: '为何一定是哈希/set',
        points: [
          '无限循环等价于「和」序列进入环；有限数位和的值域有界，必重复。',
          '这是「可能无限过程」转「是否重复出现」的经典范式。',
          '与 141 链表环类似，只是载体是整数而非指针。',
        ],
      },
      {
        title: '快慢指针 O(1) 空间（拓展）',
        points: [
          'slow=getSum(n)，fast=getSum(getSum(n))；相遇且非 1 则 false；fast==1 则 true。',
          '面试写 set 更直观；追问空间可答 Floyd。',
        ],
      },
    ],
    extraPitfalls: ['getSum 写成 n%10^2（异或）而非平方。', '忘记 sum==1 的终止条件。'],
    extraChecklist: ['能手写 set 版 getSum + 主循环。', '能口述「和会重复」故可判 false。'],
  },
  'two-sum': {
    overview:
      '对应《两数之和》1。第一次系统用 map：遍历到 x 时 O(1) 查 target-x 是否在之前出现过，且要记录下标。先查 map 再插入当前值，避免同一元素用两次。自检四问：为何哈希、为何 map、存什么 key/value。',
    estMinutes: 50,
    topicBlocks: [
      {
        title: 'map 里 key 与 value',
        points: [
          'key：已遍历过的元素值；value：该值的下标。',
          '对 nums[i]，complement=target-nums[i]；若 map 存在 complement，return {map[complement], i}。',
          '然后再 map[nums[i]]=i；顺序不能反，否则 i 被自己匹配。',
        ],
      },
      {
        title: '为何不是 set 或数组',
        points: [
          'set 只能判断存在，无法返回下标。',
          '数组当下标需要值域小且连续；两数和值域可能很大很稀疏。',
          '暴力 O(n²) 对照理解优化目标。',
        ],
      },
      {
        title: '变形 167',
        points: [
          '输入有序：双指针左右夹逼 O(n)，空间 O(1)。',
          '说明「有序 → 双指针；无序要下标 → 哈希」的选型分工。',
          '若题目要求返回下标，排序会破坏原下标，故 1 不能先排序再双指针。',
        ],
      },
    ],
    summaryPoints: ['两数之和四问：为何哈希、为何 map、key 是什么、value 是什么。'],
    extraPitfalls: [
      '先 insert 再 find，同一下标被用两次。',
      '167 与 1 模板混用（有序 vs 要原下标）。',
    ],
    extraChecklist: ['能口述 map 存什么、为何先查后插。', '能对比 1 与 167 解法选型。'],
  },
  'four-sum-ii': {
    overview:
      '对应《四数相加 II》454。四个独立数组，计数下标组合使和为 0，无需对四元组去重。枚举 A、B 记入 map(a+b→次数)，再枚举 C、D 查 -(c+d) 累加。与 15/18 单数组不重复元组完全不同，模板勿混。',
    estMinutes: 55,
    topicBlocks: [
      {
        title: '两阶段哈希计数',
        points: [
          '第一阶段：双重循环 A、B，map[nums1[i]+nums2[j]]++。',
          '第二阶段：双重循环 C、D，若 map 存在 -(nums3[k]+nums4[l])，ans += map[that key]。',
          'key 是和的值，value 是该和出现次数（可能多对 AB 同和）。',
        ],
      },
      {
        title: '与 15/18 的本质差别',
        points: [
          '454：四个独立数组，只要下标组合，不去重四元组。',
          '15/18：同一数组选不重复元组，哈希去重难写，推荐排序+双指针。',
          '若把 454 改成「单数组四元组不重复」，难度接近 18，需另一套模板。',
        ],
      },
      {
        title: '复杂度与实现',
        points: [
          '时间 O(n²)，空间 O(n²)（不同 a+b 个数上界）。',
          '注意用 long 累加答案若和可能溢出（本题通常 int 够）。',
          '面试要能向面试官解释「为何这题不用双指针去重」。',
        ],
      },
    ],
    extraPitfalls: ['把 454 当成 18 做排序四指针。', 'map 只存 0/1 不存出现次数。'],
    extraChecklist: ['能对比 454 与 15 的数据形态与去重要求。'],
  },
  'ransom-note': {
    overview:
      '对应《赎金信》383。magazine 能否覆盖 ransomNote 各字符频次：先统计 magazine，再遍历 ransom 做减法，任一位置 <0 失败。与 242 同属计数数组，但是单向「覆盖」而非双向 multiset 相等。',
    estMinutes: 40,
    topicBlocks: [
      {
        title: '计数数组流程',
        points: [
          'int[26] 或 vector(26)；先对 magazine 各字符 ++。',
          '再对 ransomNote 各字符 --；若某位置 <0 立即 return false。',
          '全部走完 return true；magazine 更长允许多余字符留在表中。',
        ],
      },
      {
        title: '与 242 对比',
        points: [
          '242：s 与 t 双向抵消，全零相等。',
          '383：只需 magazine 频次 ≥ ransom 需求，相当于单向检查。',
          'map 也能 AC，但 26 数组更简单，体现「值域小优先数组」。',
        ],
      },
      {
        title: '边界',
        points: [
          'ransom 长于 magazine 必 false。',
          '空 ransom 通常 true（读题确认）。',
          '仅小写字母，与 242 同一映射规则。',
        ],
      },
    ],
    extraChecklist: ['能手写 383 并说明与 242 语义差别。'],
  },
  'three-sum': {
    overview:
      '对应《三数之和》15。目标：和为 0 的不重复三元组。哈希可做 O(n²) 但去重极易错；推荐排序 + 双指针。固定 i，left=i+1、right=n-1，根据 sum 与 0 比较移动；找到解后左右都要跳过重复值。',
    estMinutes: 60,
    topicBlocks: [
      {
        title: '排序 + 双指针主解',
        points: [
          'sort(nums)；for i：若 nums[i]>0 break；若 i>0 && nums[i]==nums[i-1] continue（去重 a）。',
          'left=i+1, right=n-1；while(left<right)：sum=nums[i]+nums[left]+nums[right]。',
          'sum<0 left++；sum>0 right--；sum==0 收集，然后 left/right 跳过重复值再移动。',
        ],
      },
      {
        title: '去重为何难用哈希',
        points: [
          '两层枚举 + set 查第三数，去重要维护复杂集合，易超时或漏判。',
          '双指针在有序数组上天然可「跳过相同值」。',
          'a 的去重是与 nums[i-1] 比，不是与 nums[i+1]，避免误杀 [-1,-1,2]。',
        ],
      },
      {
        title: '思考题',
        points: [
          '若要求返回原下标的两数之和，不能排序破坏下标 → 用 1 的 map。',
          '18 四数之和：再套一层 for 固定第二个数，内层仍 left/right。',
          '剪枝：i 处 nums[i]>0 可 break；四数和要注意 target 符号与剪枝。',
        ],
      },
    ],
    extraPitfalls: [
      '找到一组解后只移动一侧指针，重复三元组。',
      'a 的去重写成与后一个比较，漏解。',
    ],
    extraChecklist: ['能手写 15 并口述三层去重逻辑。', '能说明为何不用哈希做主解。'],
  },
  'four-sum': {
    overview:
      '对应《四数之和》18。在 15 模板上多一层 for 固定 k，内层 i + left/right。和为 target（不限于 0）。注意 long 防溢出；剪枝不能简单 nums[k]>target（target 可能为负）。与 454 再次对照：同数组要去重，四独立数组用 map。',
    estMinutes: 60,
    topicBlocks: [
      {
        title: '四层结构',
        points: [
          'sort；for k：去重 k；剪枝（结合 target 符号，见题解稳妥写法）。',
          'for i 从 k+1：去重 i；left=i+1, right=n-1，比较四数和与 target。',
          '等于 target 收集；left/right 跳过重复；大于 target right--，小于 left++。',
        ],
      },
      {
        title: '溢出与剪枝',
        points: [
          '四数和用 long sum 或等价，避免 int 溢出。',
          '错误剪枝：if(nums[k]>target) break 在 target 为负时不成立。',
          '可结合 nums[k]+nums[k+1] 等与 target 比较的更安全剪枝。',
        ],
      },
      {
        title: '与 454、15 对照表',
        points: [
          '15：三数、单数组、双指针、去重。',
          '18：四数、单数组、双指针、去重、一般 target。',
          '454：四数组、map 计数、不去重四元组。',
          '面试一句话：看「几个数组」和「要不要去重元组」。',
        ],
      },
    ],
    extraPitfalls: ['剪枝只考虑正 target。', 'k/i/left/right 任一层去重遗漏导致重复答案。'],
    extraChecklist: ['能默写 18 框架并指出与 15 的两处扩展。'],
  },
  summary: {
    overview:
      '哈希表篇总复盘：「是否出现过」→ 优先考虑哈希；数组/set/map 三选一。454 与 15/18 是经典易混，前者四独立数组 + map，后者单数组 + 排序双指针。刷完能向面试官解释 key/value 与为何不选另一种结构。',
    estMinutes: 35,
    topicBlocks: [
      {
        title: '载体选型口诀',
        points: [
          '定长数组：值域小且连续 → 242、383、收紧后的 349。',
          'set：值域大、只要 key、自动去重 → 349、202。',
          'map：key 关联 value（下标、次数、和→频次）→ 1、454。',
          '不需要有序：优先 unordered_*；要有序才 map/set 树实现。',
        ],
      },
      {
        title: '454 vs 15/18（必背对比）',
        points: [
          '454：四数组、计数配对、map 统计 AB 和、无元组去重。',
          '15/18：单数组、不重复元组、排序+双指针、去重靠跳过相同值。',
          '两数之和要下标 → 1 map；有序两数 → 167 双指针。',
        ],
      },
      {
        title: '本章学习顺序',
        points: [
          '理论 → 242 → 349 → 202 → 1 → 454 → 383 → 15 → 18 → 总结。',
          '自检四问：为何哈希、为何该容器、key 是什么、value 是什么。',
          '相关：49/350/167/76，按「计数 / 存在 / 配对 / 双指针」归类二刷。',
        ],
      },
    ],
    extraChecklist: [
      '能不看笔记复述 454 与 15 的三条差别。',
      '能从本章主刷题各举一题说明 map 的 key/value。',
    ],
  },
}

export function applyHashTableEnrichment(sections: LearnSection[]): LearnSection[] {
  return mergeEnrichment(sections, HASH_TABLE_ENRICHMENT)
}
