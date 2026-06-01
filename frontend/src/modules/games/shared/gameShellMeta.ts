/** 各游戏关卡侧栏：伪代码、要点、页脚 */

export interface GameCodeLine {
  text: string
  /** 在哪些步骤索引下高亮（0-based stepIndex） */
  activeAtSteps?: number[]
}

export interface GameLevelShellMeta {
  badge: string
  lc: string
  concept: string
  invariant: string
  rules?: string[]
  codeLines: GameCodeLine[]
  stateKeys: { key: string; label: string; color: string }[]
  footer: [string, string]
  stepCount?: number
}

export const GAME_SHELL_META: Record<string, Record<string, GameLevelShellMeta>> = {
  'binary-search': {
    find: {
      badge: '二分查找',
      lc: 'LeetCode 704',
      concept: '有序数组上维护 [L,R]，每次取 mid 与 target 比较后收缩一半区间。',
      invariant: '答案（若存在）始终在 [L,R] 内；L≤R 时 mid 有意义。',
      codeLines: [
        { text: 'int L = 0, R = n - 1;', activeAtSteps: [0] },
        { text: 'while (L <= R) {', activeAtSteps: [0, 1, 2] },
        { text: '  int mid = L + (R - L) / 2;', activeAtSteps: [1, 2] },
        { text: '  if (nums[mid] == target) return mid;', activeAtSteps: [1, 2] },
        { text: '  if (nums[mid] < target) L = mid + 1;', activeAtSteps: [1, 2] },
        { text: '  else R = mid - 1;', activeAtSteps: [1, 2] },
        { text: '}', activeAtSteps: [2] },
        { text: 'return -1;', activeAtSteps: [2] },
      ],
      stateKeys: [
        { key: 'L', label: 'L', color: '#38bdf8' },
        { key: 'R', label: 'R', color: '#f472b6' },
        { key: 'M', label: 'mid', color: '#fbbf24' },
      ],
      footer: ['夹逼口诀：小了 L 右移，大了 R 左移', '数组篇 · 二分模板'],
      stepCount: 3,
    },
    lower: {
      badge: 'lower_bound',
      lc: 'LeetCode 35',
      concept: '找第一个 ≥ target 的位置：nums[mid] < target 则 L=mid+1，否则 R=mid。',
      invariant: '答案区间始终在 [L,R]；结束时 L 即为插入/第一个 ≥ 位置。',
      codeLines: [
        { text: 'while (L < R) {', activeAtSteps: [0, 1, 2] },
        { text: '  int mid = L + (R - L) / 2;', activeAtSteps: [0, 1, 2] },
        { text: '  if (nums[mid] < target) L = mid + 1;', activeAtSteps: [0, 1, 2] },
        { text: '  else R = mid;', activeAtSteps: [0, 1, 2] },
        { text: '}', activeAtSteps: [2] },
        { text: 'return L;', activeAtSteps: [2] },
      ],
      stateKeys: [
        { key: 'L', label: 'L', color: '#38bdf8' },
        { key: 'R', label: 'R', color: '#f472b6' },
      ],
      footer: ['与 upper_bound 对称记忆', '数组篇 · 二分边界'],
      stepCount: 3,
    },
    rotated: {
      badge: '旋转数组',
      lc: 'LeetCode 153',
      concept: '旋转有序：比较 mid 与 R，判断最小值在哪一半，收缩区间。',
      invariant: '最小值在 [L,R] 内；nums[mid]>nums[R] 则最小值在右半。',
      codeLines: [
        { text: 'while (L < R) {', activeAtSteps: [0, 1, 2] },
        { text: '  int mid = L + (R - L) / 2;', activeAtSteps: [0, 1, 2] },
        { text: '  if (nums[mid] > nums[R]) L = mid + 1;', activeAtSteps: [0, 1, 2] },
        { text: '  else R = mid;', activeAtSteps: [0, 1, 2] },
        { text: '}', activeAtSteps: [2] },
        { text: 'return L;', activeAtSteps: [2] },
      ],
      stateKeys: [
        { key: 'L', label: 'L', color: '#38bdf8' },
        { key: 'R', label: 'R', color: '#f472b6' },
      ],
      footer: ['先判哪一半有序，再二分', '数组篇 · 旋转二分'],
      stepCount: 3,
    },
  },
  'hash-locker': {
    basic: {
      badge: '取模散列',
      lc: '哈希表基础',
      concept: 'key % 桶数 决定桶下标；无冲突时直接放入桶内。',
      invariant: '同一 key 永远映射到同一桶（负载因子低时均摊 O(1)）。',
      codeLines: [
        { text: 'int bucket = key % capacity;', activeAtSteps: [0, 1, 2, 3] },
        { text: 'table[bucket].insert(key);', activeAtSteps: [0, 1, 2, 3] },
      ],
      stateKeys: [
        { key: 'mod', label: '桶数', color: '#38bdf8' },
        { key: 'key', label: '当前 key', color: '#f472b6' },
      ],
      footer: ['取模前确保 capacity 为正', '哈希表篇 · 入桶'],
      stepCount: 4,
    },
    chain: {
      badge: '拉链法',
      lc: '冲突处理',
      concept: '同桶冲突时在链表尾部追加，查找沿链扫描。',
      invariant: '桶内元素 key 互异；插入总在链尾。',
      codeLines: [
        { text: 'int b = key % capacity;', activeAtSteps: [0, 1, 2, 3] },
        { text: 'if (bucket[b] occupied)', activeAtSteps: [1, 2, 3] },
        { text: '  chain_push_back(b, key);', activeAtSteps: [1, 2, 3] },
        { text: 'else bucket[b] = key;', activeAtSteps: [0] },
      ],
      stateKeys: [
        { key: 'mod', label: '桶数', color: '#38bdf8' },
        { key: 'key', label: '当前 key', color: '#f472b6' },
      ],
      footer: ['开放寻址是另一种冲突策略', '哈希表篇 · 拉链'],
      stepCount: 4,
    },
    rehash: {
      badge: 'rehash 扩容',
      lc: '动态扩容',
      concept: '负载过高时桶数翻倍，所有 key 按新容量重新取模入桶。',
      invariant: 'rehash 后映射关系改变，必须全表重散列。',
      codeLines: [
        { text: 'if (size >= capacity * load_factor)', activeAtSteps: [0] },
        { text: '  capacity *= 2;', activeAtSteps: [0] },
        { text: '  rehash_all_keys();', activeAtSteps: [1, 2, 3, 4, 5, 6] },
      ],
      stateKeys: [
        { key: 'phase', label: '阶段', color: '#a78bfa' },
        { key: 'key', label: '当前 key', color: '#f472b6' },
      ],
      footer: ['均摊 O(1) 来自偶尔扩容', '哈希表篇 · rehash'],
      stepCount: 6,
    },
  },
  palindrome: {
    palindrome: {
      badge: '相向双指针',
      lc: 'LeetCode 125',
      concept: '左右指针向中间移动，跳过无效字符后比较是否相等。',
      invariant: '已检查区间外的字符满足回文对称。',
      codeLines: [
        { text: 'while (L < R) {', activeAtSteps: [0, 1, 2, 3, 4] },
        { text: '  skip non-alnum at L, R;', activeAtSteps: [0, 1, 2, 3, 4] },
        { text: '  if (s[L] != s[R]) return false;', activeAtSteps: [0, 1, 2, 3, 4] },
        { text: '  L++; R--;', activeAtSteps: [0, 1, 2, 3, 4] },
        { text: '}', activeAtSteps: [4] },
        { text: 'return true;', activeAtSteps: [4] },
      ],
      stateKeys: [
        { key: 'L', label: 'L', color: '#38bdf8' },
        { key: 'R', label: 'R', color: '#f472b6' },
      ],
      footer: ['跳过规则先写清再比较', '字符串篇 · 回文'],
      stepCount: 5,
    },
    'kmp-next': {
      badge: 'KMP next',
      lc: 'LeetCode 28',
      concept: 'next[i] = 最长相等前后缀长度；失配时 j = next[j-1]。',
      invariant: 'next 数组只依赖模式串自身，与文本无关。',
      codeLines: [
        { text: 'next[0] = 0;', activeAtSteps: [0] },
        { text: 'for (i = 1; i < m; i++) {', activeAtSteps: [1, 2, 3, 4] },
        { text: '  j = next[i-1];', activeAtSteps: [1, 2, 3, 4] },
        { text: '  while (j>0 && p[i]!=p[j]) j=next[j-1];', activeAtSteps: [1, 2, 3, 4] },
        { text: '  if (p[i]==p[j]) j++;', activeAtSteps: [1, 2, 3, 4] },
        { text: '  next[i] = j;', activeAtSteps: [1, 2, 3, 4] },
      ],
      stateKeys: [{ key: 'step', label: '填写位', color: '#fbbf24' }],
      footer: ['ababa → [0,0,1,2,3]', '字符串篇 · KMP'],
      stepCount: 5,
    },
  },
  'two-pointers-race': {
    dedup: {
      badge: '快慢写读',
      lc: 'LeetCode 26',
      concept: 'right 扫描，write 指向下一个写入位置；不等则写入并 write++。',
      invariant: '[0,write] 为去重后的有序前缀。',
      codeLines: [
        { text: 'int write = 0, right = 1;', activeAtSteps: [0, 1, 2] },
        { text: 'while (right < n) {', activeAtSteps: [0, 1, 2] },
        { text: '  if (nums[right]!=nums[write])', activeAtSteps: [0, 1, 2] },
        { text: '    nums[++write]=nums[right];', activeAtSteps: [0, 1, 2] },
        { text: '  right++;', activeAtSteps: [0, 1, 2] },
        { text: '}', activeAtSteps: [2] },
      ],
      stateKeys: [
        { key: 'L', label: 'write', color: '#38bdf8' },
        { key: 'R', label: 'right', color: '#f472b6' },
        { key: 'w', label: 'write', color: '#a78bfa' },
      ],
      footer: ['有序才能 O(n) 去重', '双指针篇 · 快慢'],
      stepCount: 3,
    },
    sum: {
      badge: '相向指针',
      lc: 'LeetCode 15',
      concept: '固定 i，L/R 向目标和收缩：和太小 L++，和太大 R--。',
      invariant: '已固定的 i 左侧组合已枚举完毕。',
      codeLines: [
        { text: 'sort(nums);', activeAtSteps: [0] },
        { text: 'for (i...) { L=i+1; R=n-1;', activeAtSteps: [0, 1, 2] },
        { text: '  while (L<R) {', activeAtSteps: [0, 1, 2] },
        { text: '    if (sum==0) record;', activeAtSteps: [1, 2] },
        { text: '    else if (sum<0) L++;', activeAtSteps: [0, 1, 2] },
        { text: '    else R--;', activeAtSteps: [0, 1, 2] },
        { text: '  }', activeAtSteps: [2] },
      ],
      stateKeys: [
        { key: 'L', label: 'L', color: '#38bdf8' },
        { key: 'R', label: 'R', color: '#f472b6' },
      ],
      footer: ['去重：跳过相同 i/L/R', '双指针篇 · 三数之和'],
      stepCount: 3,
    },
    cycle: {
      badge: '快慢指针',
      lc: 'LeetCode 141',
      concept: 'slow 走 1 步，fast 走 2 步；相遇则有环。',
      invariant: '若有环，fast 必在环内追上 slow。',
      codeLines: [
        { text: 'slow = fast = head;', activeAtSteps: [0] },
        { text: 'while (fast && fast->next) {', activeAtSteps: [0, 1, 2] },
        { text: '  slow = slow->next;', activeAtSteps: [0, 1, 2] },
        { text: '  fast = fast->next->next;', activeAtSteps: [0, 1, 2] },
        { text: '  if (slow==fast) return true;', activeAtSteps: [2] },
        { text: '}', activeAtSteps: [2] },
      ],
      stateKeys: [
        { key: 'slow', label: 'slow', color: '#a78bfa' },
        { key: 'fast', label: 'fast', color: '#f97316' },
      ],
      footer: ['数组版用下标模拟指针', '双指针篇 · 判环'],
      stepCount: 3,
    },
  },
  'greedy-courier': {
    jump: {
      badge: '贪心跳跃',
      lc: 'LeetCode 55',
      concept: '维护最远可达下标；每步更新 maxReach，maxReach 到末尾即可达。',
      invariant: '当前位置 i 可达当且仅当 i ≤ maxReach。',
      codeLines: [
        { text: 'int maxReach = 0;', activeAtSteps: [0, 1, 2] },
        { text: 'for (i = 0; i < n; i++) {', activeAtSteps: [0, 1, 2] },
        { text: '  if (i > maxReach) return false;', activeAtSteps: [0, 1, 2] },
        { text: '  maxReach = max(maxReach, i+nums[i]);', activeAtSteps: [0, 1, 2] },
        { text: '}', activeAtSteps: [2] },
      ],
      stateKeys: [
        { key: 'pos', label: '当前位置', color: '#38bdf8' },
        { key: 'reach', label: '最远可达', color: '#fbbf24' },
      ],
      footer: ['能到 i 才能从 i 跳', '贪心篇 · 跳跃'],
      stepCount: 3,
    },
    interval: {
      badge: '区间贪心',
      lc: 'LeetCode 435',
      concept: '按结束时间排序，每次选结束最早的且不与已选重叠的区间。',
      invariant: '已选区间按 end 递增，下一个选 start ≥ 上一 end。',
      codeLines: [
        { text: 'sort by end;', activeAtSteps: [0, 1, 2] },
        { text: 'pick interval with min end;', activeAtSteps: [0, 1, 2] },
        { text: 'next must have start >= last_end;', activeAtSteps: [0, 1, 2] },
      ],
      stateKeys: [{ key: 'picked', label: '已选', color: '#22c55e' }],
      footer: ['活动选择：结束越早越优', '贪心篇 · 区间'],
      stepCount: 3,
    },
  },
  'knapsack-lite': {
    knapsack: {
      badge: '0/1 背包',
      lc: 'LeetCode 416',
      concept: '每件物品选或不选；在容量限制下最大化价值。',
      invariant: 'dp[w] = 容量 w 时的最大价值（滚动数组可优化空间）。',
      codeLines: [
        { text: 'for (item i)', activeAtSteps: [0, 1, 2] },
        { text: '  for (w from W downto w_i)', activeAtSteps: [0, 1, 2] },
        { text: '    dp[w] = max(dp[w], dp[w-wi]+vi);', activeAtSteps: [0, 1, 2] },
      ],
      stateKeys: [
        { key: 'w', label: '已用容量', color: '#38bdf8' },
        { key: 'v', label: '总价值', color: '#fbbf24' },
      ],
      footer: ['逆序枚举 w 保证每件只用一次', 'DP 篇 · 背包'],
      stepCount: 3,
    },
    rob: {
      badge: '线性 DP',
      lc: 'LeetCode 198',
      concept: '偷第 i 家则 i-1 不能偷；dp[i]=max(dp[i-1], dp[i-2]+nums[i])。',
      invariant: 'dp[i] 为前 i 家的最大金额。',
      codeLines: [
        { text: 'dp[i] = max(dp[i-1], dp[i-2]+a[i]);', activeAtSteps: [0, 1, 2, 3, 4] },
      ],
      stateKeys: [{ key: 'sum', label: '当前金额', color: '#22c55e' }],
      footer: ['相邻约束 → 只依赖前两个状态', 'DP 篇 · 打家劫舍'],
      stepCount: 5,
    },
    stairs: {
      badge: '一维滚动',
      lc: 'LeetCode 70',
      concept: '到第 i 阶 = 从 i-1 迈 1 步 + 从 i-2 迈 2 步。',
      invariant: 'dp[i]=dp[i-1]+dp[i-2]，可用两个变量滚动。',
      codeLines: [
        { text: 'dp[0]=1; dp[1]=1;', activeAtSteps: [0, 1] },
        { text: 'for (i=2..n) dp[i]=dp[i-1]+dp[i-2];', activeAtSteps: [2, 3, 4, 5] },
      ],
      stateKeys: [{ key: 'i', label: '填写下标', color: '#fbbf24' }],
      footer: ['斐波那契本质', 'DP 篇 · 爬楼梯'],
      stepCount: 6,
    },
  },
  'backtrack-room': {
    n4: {
      badge: 'N 皇后',
      lc: 'LeetCode 51',
      concept: '逐行放皇后，列/对角冲突则剪枝；放满 n 个即解。',
      invariant: '每行恰一皇后；已放皇后互不攻击。',
      codeLines: [
        { text: 'void dfs(int row) {', activeAtSteps: [0, 1, 2, 3] },
        { text: '  if (row==n) record;', activeAtSteps: [3] },
        { text: '  for (col) if (!attack) {', activeAtSteps: [0, 1, 2] },
        { text: '    place; dfs(row+1); remove;', activeAtSteps: [0, 1, 2] },
        { text: '  }', activeAtSteps: [0, 1, 2] },
        { text: '}', activeAtSteps: [3] },
      ],
      stateKeys: [{ key: 'queens', label: '已放皇后', color: '#f472b6' }],
      footer: ['冲突检测：同行列对角', '回溯篇 · N 皇后'],
      stepCount: 4,
    },
    perm: {
      badge: '全排列',
      lc: 'LeetCode 46',
      concept: 'used 标记已选数字；每层选一个未用数，到底则收集排列。',
      invariant: 'path 长度为 k 时前 k 位已固定且互异。',
      codeLines: [
        { text: 'void dfs(path) {', activeAtSteps: [0, 1, 2] },
        { text: '  if (path.size()==n) output;', activeAtSteps: [2] },
        { text: '  for (x not used) { used[x]=1; dfs; used[x]=0; }', activeAtSteps: [0, 1] },
      ],
      stateKeys: [{ key: 'perm', label: '当前路径', color: '#a78bfa' }],
      footer: ['撤销：used 与 path 同步回溯', '回溯篇 · 排列'],
      stepCount: 3,
    },
  },
  'tree-cave': {
    traverse: {
      badge: '前序遍历',
      lc: 'LeetCode 144',
      concept: '根 → 左 → 右；递归或栈实现。',
      invariant: '访问根在访问其子树之前。',
      codeLines: [
        { text: 'visit(root);', activeAtSteps: [0, 1, 2, 3] },
        { text: 'preorder(root->left);', activeAtSteps: [0, 1, 2, 3] },
        { text: 'preorder(root->right);', activeAtSteps: [0, 1, 2, 3] },
      ],
      stateKeys: [{ key: 'order', label: '已访问', color: '#38bdf8' }],
      footer: ['口诀：根左右', '二叉树篇 · 前序'],
      stepCount: 4,
    },
    bst: {
      badge: 'BST 中序',
      lc: 'LeetCode 98',
      concept: '中序遍历 BST 得到严格递增序列，用于验证或找第 k 小。',
      invariant: '当前值必须大于上一访问值。',
      codeLines: [
        { text: 'inorder(left);', activeAtSteps: [0, 1, 2, 3, 4, 5, 6] },
        { text: 'if (val <= prev) invalid;', activeAtSteps: [0, 1, 2, 3, 4, 5, 6] },
        { text: 'prev = val; visit(root);', activeAtSteps: [0, 1, 2, 3, 4, 5, 6] },
        { text: 'inorder(right);', activeAtSteps: [0, 1, 2, 3, 4, 5, 6] },
      ],
      stateKeys: [{ key: 'order', label: '中序序列', color: '#22c55e' }],
      footer: ['口诀：左根右', '二叉树篇 · BST'],
      stepCount: 7,
    },
    path: {
      badge: '根到叶路径',
      lc: 'LeetCode 112',
      concept: 'DFS 维护路径和；到叶且和等于 target 则找到解。',
      invariant: '路径和 = 根到当前结点 val 之和。',
      codeLines: [
        { text: 'dfs(node, sum) {', activeAtSteps: [0, 1, 2, 3] },
        { text: '  sum += node->val;', activeAtSteps: [0, 1, 2, 3] },
        { text: '  if (leaf && sum==target) return true;', activeAtSteps: [2, 3] },
        { text: '  return dfs(L)||dfs(R);', activeAtSteps: [0, 1, 2, 3] },
      ],
      stateKeys: [
        { key: 'path', label: '路径和', color: '#fbbf24' },
        { key: 'sum', label: '当前和', color: '#38bdf8' },
      ],
      footer: ['回溯时减去结点值', '二叉树篇 · 路径和'],
      stepCount: 4,
    },
  },
  'monotonic-barrier': {
    temp: {
      badge: '单调栈',
      lc: 'LeetCode 739',
      concept: '栈存下标，当前温度更高时弹出并计算等待天数。',
      invariant: '栈内下标对应温度严格递减。',
      codeLines: [
        { text: 'for (i in days) {', activeAtSteps: [0, 1, 2, 3, 4, 5, 6] },
        { text: '  while (stack && T[i]>T[top])', activeAtSteps: [0, 1, 2, 3, 4, 5, 6] },
        { text: '    ans[pop] = i - pop;', activeAtSteps: [0, 1, 2, 3, 4, 5, 6] },
        { text: '  push(i);', activeAtSteps: [0, 1, 2, 3, 4, 5, 6] },
        { text: '}', activeAtSteps: [6] },
      ],
      stateKeys: [
        { key: 'processed', label: '进度', color: '#38bdf8' },
        { key: 'stack', label: '栈顶', color: '#fbbf24' },
      ],
      footer: ['弹栈时机：遇到更高温度', '单调栈篇 · 每日温度'],
      stepCount: 7,
    },
    rect: {
      badge: '柱状图',
      lc: 'LeetCode 84',
      concept: '递增栈；当前柱更矮时弹出，以弹出柱为高算矩形宽。',
      invariant: '栈内柱高单调递增，弹出时确定右边界。',
      codeLines: [
        { text: 'for (i) {', activeAtSteps: [0, 1, 2, 3, 4, 5] },
        { text: '  while (h[i] < h[stack.top]) pop;', activeAtSteps: [0, 1, 2, 3, 4, 5] },
        { text: '  push(i);', activeAtSteps: [0, 1, 2, 3, 4, 5] },
        { text: '}', activeAtSteps: [5] },
      ],
      stateKeys: [
        { key: 'processed', label: '进度', color: '#38bdf8' },
        { key: 'stack', label: '栈', color: '#a78bfa' },
      ],
      footer: ['宽度由左右第一个更矮柱决定', '单调栈篇 · 矩形'],
      stepCount: 6,
    },
  },
  'canteen-stack-queue': {
    stack: {
      badge: '栈 LIFO',
      lc: 'LeetCode 225',
      concept: '后进先出：只能 push 到栈顶，pop 也只能从栈顶取。',
      invariant: '栈顶 = 最后入栈元素；出餐顺序由栈决定。',
      codeLines: [
        { text: 'push(x);  // 入栈', activeAtSteps: [0, 1, 2] },
        { text: 'x = pop();  // 仅栈顶', activeAtSteps: [0, 1, 2] },
      ],
      stateKeys: [
        { key: 'lives', label: '生命', color: '#ef4444' },
        { key: 'score', label: '得分', color: '#fbbf24' },
      ],
      footer: ['订单错序扣生命', '栈队列篇 · 栈'],
      stepCount: 3,
    },
    queue: {
      badge: '队列 FIFO',
      lc: 'LeetCode 622',
      concept: '先进先出：队尾入队，队头出队。',
      invariant: '队头 = 最早入队元素。',
      codeLines: [
        { text: 'enqueue(x);', activeAtSteps: [0, 1, 2] },
        { text: 'x = dequeue();  // 队头', activeAtSteps: [0, 1, 2] },
      ],
      stateKeys: [
        { key: 'lives', label: '生命', color: '#ef4444' },
        { key: 'score', label: '得分', color: '#fbbf24' },
      ],
      footer: ['只能从队头出餐', '栈队列篇 · 队列'],
      stepCount: 3,
    },
    'dual-stack': {
      badge: '双栈队列',
      lc: 'LeetCode 232',
      concept: 'in 栈倒入 out 后，out 栈顶相当于队头；均摊 O(1)。',
      invariant: 'out 空时才需要把 in 全部倒入 out。',
      codeLines: [
        { text: 'if (out.empty()) pour(in→out);', activeAtSteps: [0, 1] },
        { text: 'return out.pop();', activeAtSteps: [0, 1, 2] },
      ],
      stateKeys: [
        { key: 'lives', label: '生命', color: '#ef4444' },
        { key: 'score', label: '得分', color: '#fbbf24' },
      ],
      footer: ['先倒入再出队', '栈队列篇 · 232'],
      stepCount: 2,
    },
    paren: {
      badge: '括号匹配',
      lc: 'LeetCode 20',
      concept: '左括号入栈；右括号与栈顶匹配则弹栈。',
      invariant: '栈中仅存未匹配的左括号。',
      codeLines: [
        { text: 'if (open) stack.push(c);', activeAtSteps: [0, 1, 2, 3, 4, 5] },
        { text: 'else if (match(stack.top,c)) pop;', activeAtSteps: [0, 1, 2, 3, 4, 5] },
      ],
      stateKeys: [
        { key: 'cursor', label: '扫描位置', color: '#38bdf8' },
        { key: 'stack', label: '栈深', color: '#a78bfa' },
      ],
      footer: ['三种括号成对匹配', '栈队列篇 · 有效括号'],
      stepCount: 6,
    },
    deque: {
      badge: '单调 deque',
      lc: 'LeetCode 239',
      concept: '队尾维护递减下标；窗口右移时弹出过期队头。',
      invariant: 'deque 存下标且对应值单调递减。',
      codeLines: [
        { text: 'while (back val <= new) pop_back;', activeAtSteps: [0, 1] },
        { text: 'push_back(i);', activeAtSteps: [0, 1] },
        { text: 'if (front expired) pop_front;', activeAtSteps: [1, 2] },
      ],
      stateKeys: [{ key: 'window', label: '窗口', color: '#fbbf24' }],
      footer: ['队头即窗口最大值下标', '栈队列篇 · 滑动窗口'],
      stepCount: 2,
    },
  },
  'graph-explorer': {
    representation: {
      badge: '邻接表建图',
      lc: '图论基础',
      concept: '边集转邻接表时，无向边 (u,v) 需要同时写入 adj[u] 和 adj[v]。',
      invariant: '每处理一条无向边，两个端点的邻接表都必须同步更新。',
      rules: [
        '按当前提示处理边集中的一条边。',
        '无向边必须先补 from→to，再补 to→from，缺任一方向都不能过关。',
        '重复写入或写错端点会触发失败提示，本关要求邻接表完整且无重复。',
      ],
      codeLines: [
        { text: 'for ([u, v] of edges) {', activeAtSteps: [0, 1, 2, 3, 4, 5] },
        { text: '  adj[u].push(v);', activeAtSteps: [0, 2, 4] },
        { text: '  adj[v].push(u);', activeAtSteps: [1, 3, 5] },
        { text: '}', activeAtSteps: [5] },
      ],
      stateKeys: [
        { key: 'edge', label: '当前边', color: '#38bdf8' },
        { key: 'done', label: '已补方向', color: '#22c55e' },
      ],
      footer: ['建图先确认有向/无向', '图论篇 · 表示法'],
      stepCount: 6,
    },
    bfs: {
      badge: 'BFS 层序',
      lc: '最短路基础',
      concept: '无权图最短步数由 BFS 保证：队列先进先出，先访问的层距离更短。',
      invariant: '队列中结点按距离非递减排列；首次访问即得到最短距离。',
      rules: [
        '每轮只能展开队头结点，不能跳过队列前面的结点。',
        '点击队头的未访问邻居完成入队和距离更新。',
        '队头所有邻居处理完后，点击“弹出队头”进入下一轮。',
      ],
      codeLines: [
        { text: 'queue.push(start); dist[start]=0;', activeAtSteps: [0] },
        { text: 'while (!queue.empty()) {', activeAtSteps: [0, 1, 2, 3, 4, 5] },
        { text: '  u = queue.front();', activeAtSteps: [0, 1, 2, 3, 4, 5] },
        { text: '  for (v in adj[u]) if (!seen[v])', activeAtSteps: [0, 1, 2, 3, 4] },
        { text: '    seen[v]=true; dist[v]=dist[u]+1; push(v);', activeAtSteps: [0, 1, 2, 3, 4] },
        { text: '  queue.pop();', activeAtSteps: [1, 3, 5] },
        { text: '}', activeAtSteps: [5] },
      ],
      stateKeys: [
        { key: 'queue', label: '队列', color: '#38bdf8' },
        { key: 'dist', label: '目标距离', color: '#fbbf24' },
      ],
      footer: ['无权最短路：BFS 第一次到达', '图论篇 · BFS'],
      stepCount: 6,
    },
    dfs: {
      badge: 'DFS 回溯',
      lc: '递归搜索',
      concept: 'DFS 沿一条路径深入，遇到死路后回退到上一个分叉点继续尝试。',
      invariant: 'path 表示递归栈；栈顶是当前正在探索的结点。',
      rules: [
        '只能从当前栈顶选择相邻且未访问的结点继续深入。',
        '本关会先探索 S→B→D 死路，必须逐层回退到 S。',
        '回退后再走 S→A→C→F，找到 F 才能通关。',
      ],
      codeLines: [
        { text: 'path.push(u); seen[u]=true;', activeAtSteps: [0, 1, 2, 3] },
        { text: 'if (u == target) return true;', activeAtSteps: [3] },
        { text: 'for (v in adj[u]) if (!seen[v]) dfs(v);', activeAtSteps: [0, 1, 2] },
        { text: 'path.pop();  // backtrack', activeAtSteps: [4] },
      ],
      stateKeys: [
        { key: 'path', label: '递归栈', color: '#a78bfa' },
        { key: 'seen', label: '已访问', color: '#22c55e' },
      ],
      footer: ['DFS 关键是进入与回退成对', '图论篇 · DFS'],
      stepCount: 7,
    },
  },
  'algo-detective': {
    'dfs-queue': {
      badge: '结构侦探',
      lc: 'BFS vs DFS',
      concept: 'BFS 用队列先进先出；DFS 用栈或递归后进先出。',
      invariant: '选对容器才能保持正确的访问顺序。',
      codeLines: [
        { text: 'BFS: queue.push(start);', activeAtSteps: [0, 1] },
        { text: 'DFS: stack.push(start) / recurse;', activeAtSteps: [0, 1] },
      ],
      stateKeys: [{ key: 'flag', label: '已标记', color: '#ef4444' }],
      footer: ['第 5 步混用了队列做 DFS', '综合 · 容器选择'],
      stepCount: 2,
    },
    'bst-inorder': {
      badge: 'BST 验证',
      lc: 'LeetCode 98',
      concept: '中序必须严格递增；应比较 curr > prev。',
      invariant: 'BST 中序 = 有序数组。',
      codeLines: [
        { text: 'if (curr > prev) ok;', activeAtSteps: [0, 1] },
        { text: 'wrong: if (curr < prev)', activeAtSteps: [0, 1] },
      ],
      stateKeys: [{ key: 'flag', label: '已标记', color: '#ef4444' }],
      footer: ['第 3 步比较方向反了', '综合 · BST'],
      stepCount: 2,
    },
    'dp-order': {
      badge: 'DP 填表',
      lc: '0/1 背包',
      concept: 'dp[i][w] 依赖 dp[i-1][*]，不能先算 i+1 再算 i。',
      invariant: '外层物品、内层容量，内层 w 逆序。',
      codeLines: [
        { text: 'dp[i][w] from dp[i-1][...]', activeAtSteps: [0, 1] },
        { text: 'wrong: dp[i+1] before dp[i]', activeAtSteps: [0, 1] },
      ],
      stateKeys: [{ key: 'flag', label: '已标记', color: '#ef4444' }],
      footer: ['第 5 步填表顺序错误', '综合 · DP'],
      stepCount: 2,
    },
  },
}

const GAME_TAGS: Record<string, string[]> = {
  'binary-search': ['二分夹逼', '指针可视化', '伪代码对照'],
  'linked-list-repair': ['分步操作', '指针可视化', '伪代码对照'],
  'hash-locker': ['取模入桶', '冲突处理', 'rehash 扩容'],
  'palindrome': ['双指针', 'KMP next', '字符串'],
  'two-pointers-race': ['快慢指针', '相向夹逼', '去重模板'],
  'canteen-stack-queue': ['栈 LIFO', '队列 FIFO', '生命值'],
  'monotonic-barrier': ['单调栈', '弹栈时机', '柱状图'],
  'tree-cave': ['树遍历', 'BST 中序', '路径 DFS'],
  'backtrack-room': ['回溯', '剪枝', '撤销'],
  'greedy-courier': ['贪心', '区间调度', '跳跃覆盖'],
  'knapsack-lite': ['0/1 背包', '线性 DP', '滚动数组'],
  'graph-explorer': ['邻接表', 'BFS 队列', 'DFS 回溯'],
  'algo-detective': ['找 bug', '步骤审查', '概念辨析'],
}

export function getGameShellMeta(gameId: string, levelId: string): GameLevelShellMeta | undefined {
  return GAME_SHELL_META[gameId]?.[levelId]
}

export function getGameTags(gameId: string): string[] {
  return GAME_TAGS[gameId] ?? ['互动闯关', '算法可视化']
}

export function isCodeLineActive(line: GameCodeLine, stepIndex: number): boolean {
  if (!line.activeAtSteps?.length) return false
  return line.activeAtSteps.includes(stepIndex)
}
