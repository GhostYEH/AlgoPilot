import { defineAsyncComponent, type Component } from 'vue'

export type GameDifficultyStars = 1 | 2 | 3

export interface GameLevelMeta {
  id: string
  title: string
  goal: string
}

export interface ModuleGameMeta {
  id: string
  moduleKey: string
  title: string
  tagline: string
  stars: GameDifficultyStars
  levels: GameLevelMeta[]
  loadComponent: () => Promise<Component>
}

export const MODULE_GAME_MAP: Record<string, string> = {
  array: 'binary-search',
  'linked-list': 'linked-list-repair',
  'hash-table': 'hash-locker',
  string: 'palindrome',
  'two-pointers': 'two-pointers-race',
  'stack-queue': 'canteen-stack-queue',
  'monotonic-stack': 'monotonic-barrier',
  'binary-tree': 'tree-cave',
  backtracking: 'backtrack-room',
  greedy: 'greedy-courier',
  dp: 'knapsack-lite',
  graph: 'graph-explorer',
}

export const ALGO_DETECTIVE_GAME_ID = 'algo-detective'

const GAME_LOADERS: Record<string, () => Promise<Component>> = {
  'binary-search': () => import('./components/BinarySearchGame.vue'),
  'linked-list-repair': () => import('./components/LinkedListRepairGame.vue'),
  'hash-locker': () => import('./components/HashLockerGame.vue'),
  palindrome: () => import('./components/PalindromeGame.vue'),
  'two-pointers-race': () => import('./components/TwoPointersRaceGame.vue'),
  'canteen-stack-queue': () => import('./components/CanteenStackQueueGame.vue'),
  'monotonic-barrier': () => import('./components/MonotonicBarrierGame.vue'),
  'tree-cave': () => import('./components/TreeCaveGame.vue'),
  'backtrack-room': () => import('./components/BacktrackRoomGame.vue'),
  'greedy-courier': () => import('./components/GreedyCourierGame.vue'),
  'knapsack-lite': () => import('./components/KnapsackLiteGame.vue'),
  'graph-explorer': () => import('./components/GraphExplorerGame.vue'),
  'algo-detective': () => import('./components/AlgoDetectiveGame.vue'),
}

export const ALL_GAMES: ModuleGameMeta[] = [
  {
    id: 'binary-search',
    moduleKey: 'array',
    title: '夹逼寻宝',
    tagline: '有序数组上拖动左右指针，练习二分不变量',
    stars: 1,
    levels: [
      { id: 'find', title: '找目标', goal: '在 [2,5,8,12,16,23,38,56,72,91] 中找到 23' },
      { id: 'lower', title: '第一个 ≥ x', goal: '找第一个 ≥ 15 的下标（lower_bound）' },
      { id: 'rotated', title: '旋转最小值', goal: '在旋转有序数组 [4,5,6,7,0,1,2] 找最小值下标' },
    ],
    loadComponent: GAME_LOADERS['binary-search'],
  },
  {
    id: 'linked-list-repair',
    moduleKey: 'linked-list',
    title: '断链修理工',
    tagline: '选择工具并点击结点/执行操作，分步完成反转、删除与判环',
    stars: 2,
    levels: [
      { id: 'reverse', title: '反转链表', goal: '用 pre/cur 工具分步完成原地反转' },
      { id: 'delete', title: '删除结点', goal: '删除值为 3 的结点（虚拟头结点法）' },
      { id: 'cycle', title: '龟兔赛跑', goal: '快慢指针相遇时判断是否有环' },
    ],
    loadComponent: GAME_LOADERS['linked-list-repair'],
  },
  {
    id: 'hash-locker',
    moduleKey: 'hash-table',
    title: '快递柜取件',
    tagline: '计算桶号、处理冲突、体验 rehash',
    stars: 2,
    levels: [
      { id: 'basic', title: '入桶', goal: 'key % 7 放入对应桶' },
      { id: 'chain', title: '拉链法', goal: '冲突时在同一桶尾部链接' },
      { id: 'rehash', title: 'Boss：扩容', goal: '表满后触发 rehash 到更大容量' },
    ],
    loadComponent: GAME_LOADERS['hash-locker'],
  },
  {
    id: 'palindrome',
    moduleKey: 'string',
    title: '回文消消乐',
    tagline: '双指针夹逼或补全 KMP next 数组',
    stars: 1,
    levels: [
      { id: 'palindrome', title: '验证回文', goal: '左右指针向中间移动，跳过非字母数字' },
      { id: 'kmp-next', title: 'next 填空', goal: '为模式 ababa 选择正确的 next 数组一项' },
    ],
    loadComponent: GAME_LOADERS.palindrome,
  },
  {
    id: 'two-pointers-race',
    moduleKey: 'two-pointers',
    title: '双指针赛跑',
    tagline: '控制 left/right 或 slow/fast，理解不漏解',
    stars: 1,
    levels: [
      { id: 'dedup', title: '有序去重', goal: 'left 指向下一个不重复位置' },
      { id: 'sum', title: '三数之和', goal: '固定 i，left/right 向目标和靠拢' },
      { id: 'cycle', title: '环检测', goal: 'fast 走 2 步、slow 走 1 步直到相遇' },
    ],
    loadComponent: GAME_LOADERS['two-pointers-race'],
  },
  {
    id: 'canteen-stack-queue',
    moduleKey: 'stack-queue',
    title: '食堂出餐口',
    tagline: '栈 LIFO、队列 FIFO、双栈与括号、单调 deque',
    stars: 2,
    levels: [
      { id: 'stack', title: '栈关', goal: '点击餐盘入栈，再只点栈顶出餐，完成订单 [3,2,1]' },
      { id: 'queue', title: '队列关', goal: '点击入队，只点队头出餐，完成订单 [1,2,3]' },
      { id: 'dual-stack', title: '232 双栈', goal: '先倒入 out，再点 out 栈顶按序出餐' },
      { id: 'paren', title: '括号接龙', goal: '按顺序点击括号，由栈匹配 ()[]{}' },
      { id: 'deque', title: '239 窗口', goal: '在滑动窗口中选对 deque 队尾弹出时机' },
    ],
    loadComponent: GAME_LOADERS['canteen-stack-queue'],
  },
  {
    id: 'monotonic-barrier',
    moduleKey: 'monotonic-stack',
    title: '地震挡板',
    tagline: '单调栈维护「第一个更大」挡板高度',
    stars: 2,
    levels: [
      { id: 'temp', title: '每日温度', goal: '为每天找到之后第一个更高温度的天数差' },
      { id: 'rect', title: '最大矩形', goal: '向左右扩展，栈维护递增柱高' },
    ],
    loadComponent: GAME_LOADERS['monotonic-barrier'],
  },
  {
    id: 'tree-cave',
    moduleKey: 'binary-tree',
    title: '树洞探险',
    tagline: '遍历顺序、BST 中序、根到叶路径和',
    stars: 2,
    levels: [
      { id: 'traverse', title: '遍历关', goal: '按前序访问 A→B→D→C' },
      { id: 'bst', title: 'BST 关', goal: '中序必须严格递增' },
      { id: 'path', title: '路径和', goal: '选一条根到叶路径和为 22' },
    ],
    loadComponent: GAME_LOADERS['tree-cave'],
  },
  {
    id: 'backtrack-room',
    moduleKey: 'backtracking',
    title: '密室排列',
    tagline: '放皇后、判冲突、撤销回溯',
    stars: 2,
    levels: [
      { id: 'n4', title: '4 皇后', goal: '在 4×4 棋盘放 4 个皇后互不攻击' },
      { id: 'perm', title: '全排列', goal: '用 1,2,3 排出所有排列（点选顺序）' },
    ],
    loadComponent: GAME_LOADERS['backtrack-room'],
  },
  {
    id: 'greedy-courier',
    moduleKey: 'greedy',
    title: '贪心快递员',
    tagline: '跳跃游戏与区间调度',
    stars: 2,
    levels: [
      { id: 'jump', title: '跳跃游戏', goal: '每次跳到当前能覆盖的最远位置' },
      { id: 'interval', title: '会议室', goal: '选最多不重叠区间' },
    ],
    loadComponent: GAME_LOADERS['greedy-courier'],
  },
  {
    id: 'knapsack-lite',
    moduleKey: 'dp',
    title: '背包小偷 Lite',
    tagline: '0/1 背包填表，理解状态转移',
    stars: 3,
    levels: [
      { id: 'knapsack', title: '0/1 背包', goal: '容量 7 时选物品使价值最大' },
      { id: 'rob', title: '打家劫舍', goal: '相邻不能选，求最大金额' },
      { id: 'stairs', title: '爬楼梯', goal: '一维滚动：到第 n 阶的方法数' },
    ],
    loadComponent: GAME_LOADERS['knapsack-lite'],
  },
  {
    id: 'graph-explorer',
    moduleKey: 'graph',
    title: '图岛探路员',
    tagline: '在邻接表、BFS 队列与 DFS 回溯之间切换，练习图论核心操作',
    stars: 2,
    levels: [
      { id: 'representation', title: '建图关', goal: '把边集转换成无向图邻接表' },
      { id: 'bfs', title: '最短层序', goal: '用队列按层访问，找到 S 到 F 的最短步数' },
      { id: 'dfs', title: '深搜回溯', goal: '沿一条路径递归探索，遇到死路正确回退' },
    ],
    loadComponent: GAME_LOADERS['graph-explorer'],
  },
  {
    id: ALGO_DETECTIVE_GAME_ID,
    moduleKey: '_global',
    title: '算法侦探',
    tagline: '找出错误操作序列中的那一步',
    stars: 1,
    levels: [
      { id: 'dfs-queue', title: '结构误用', goal: '指出用队列做 DFS 的错误步骤' },
      { id: 'bst-inorder', title: 'BST 验证', goal: '找出破坏中序递增的操作' },
      { id: 'dp-order', title: 'DP 填表', goal: '找出先填 dp[i+1] 再填 dp[i] 的错误' },
    ],
    loadComponent: GAME_LOADERS['algo-detective'],
  },
]

const GAME_BY_ID = Object.fromEntries(ALL_GAMES.map((g) => [g.id, g]))

const SECTION_GAME_LEVEL_MAP: Record<string, Record<string, string>> = {
  array: {
    theory: 'find',
    'binary-search': 'lower',
    'remove-element': 'find',
    'sorted-squares': 'lower',
    'min-subarray': 'lower',
    spiral: 'rotated',
    summary: 'rotated',
  },
  'linked-list': {
    theory: 'reverse',
    'remove-elements': 'delete',
    'design-list': 'reverse',
    reverse: 'reverse',
    'swap-pairs': 'reverse',
    'remove-nth-from-end': 'delete',
    intersection: 'cycle',
    cycle: 'cycle',
    summary: 'cycle',
  },
  'hash-table': {
    theory: 'basic',
    'valid-anagram': 'basic',
    intersection: 'chain',
    'happy-number': 'chain',
    'two-sum': 'chain',
    'four-sum-ii': 'chain',
    'ransom-note': 'basic',
    'three-sum': 'chain',
    'four-sum': 'rehash',
    summary: 'rehash',
  },
  string: {
    theory: 'palindrome',
    'reverse-string': 'palindrome',
    'reverse-string-ii': 'palindrome',
    'replace-space': 'palindrome',
    'reverse-words': 'palindrome',
    'left-rotate': 'palindrome',
    kmp: 'kmp-next',
    'repeated-substring': 'kmp-next',
    summary: 'kmp-next',
  },
  'two-pointers': {
    theory: 'dedup',
    'remove-element': 'dedup',
    'reverse-string': 'sum',
    'replace-space': 'dedup',
    'reverse-words': 'dedup',
    'reverse-list': 'cycle',
    'remove-nth-from-end': 'cycle',
    intersection: 'cycle',
    cycle: 'cycle',
    'three-sum': 'sum',
    'four-sum': 'sum',
    summary: 'sum',
  },
  'stack-queue': {
    theory: 'stack',
    'queue-by-stacks': 'dual-stack',
    'stack-by-queues': 'queue',
    'valid-parentheses': 'paren',
    'remove-adjacent': 'stack',
    'eval-rpn': 'stack',
    'sliding-window-max': 'deque',
    'top-k-frequent': 'queue',
    summary: 'deque',
  },
  'monotonic-stack': {
    theory: 'temp',
    'daily-temperatures': 'temp',
    'next-greater': 'temp',
    'largest-rectangle': 'rect',
    'trapping-rain': 'rect',
    summary: 'rect',
  },
  'binary-tree': {
    theory: 'traverse',
    'traversal-recursive': 'traverse',
    'traversal-iterative': 'traverse',
    'unified-traversal': 'traverse',
    'level-order': 'traverse',
    'invert-tree': 'traverse',
    'checkpoint-1': 'traverse',
    'symmetric-tree': 'traverse',
    'max-depth': 'path',
    'min-depth': 'path',
    'count-nodes': 'path',
    'balanced-tree': 'path',
    'all-paths': 'path',
    'checkpoint-2': 'path',
    'sum-left-leaves': 'path',
    'find-bottom-left': 'path',
    'path-sum': 'path',
    'build-tree-in-post': 'traverse',
    'maximum-binary-tree': 'traverse',
    'checkpoint-3': 'traverse',
    'merge-trees': 'traverse',
    'bst-search': 'bst',
    'validate-bst': 'bst',
    'bst-min-diff': 'bst',
    'bst-modes': 'bst',
    'lowest-common-ancestor': 'path',
    'checkpoint-4': 'bst',
    'bst-lca': 'bst',
    'bst-insert': 'bst',
    'bst-delete': 'bst',
    'bst-trim': 'bst',
    'sorted-array-to-bst': 'bst',
    'bst-to-greater-sum': 'bst',
    summary: 'bst',
  },
  backtracking: {
    theory: 'n4',
    combinations: 'perm',
    permutations: 'perm',
    subsets: 'perm',
    'n-queens': 'n4',
    sudoku: 'n4',
    'palindrome-partition': 'perm',
    summary: 'n4',
  },
  greedy: {
    theory: 'jump',
    'assign-cookies': 'jump',
    'non-overlapping-intervals': 'interval',
    'jump-game': 'jump',
    'gas-station': 'jump',
    'stock-greedy': 'interval',
    summary: 'interval',
  },
  dp: {
    theory: 'stairs',
    'five-steps': 'stairs',
    'climbing-stairs': 'stairs',
    'knapsack-01': 'knapsack',
    'unbounded-knapsack': 'knapsack',
    'coin-change': 'knapsack',
    lis: 'rob',
    summary: 'rob',
  },
  graph: {
    theory: 'representation',
    representation: 'representation',
    bfs: 'bfs',
    dfs: 'dfs',
    pitfalls: 'dfs',
    practice: 'bfs',
    summary: 'dfs',
  },
}

export function getGameById(id: string): ModuleGameMeta | undefined {
  return GAME_BY_ID[id]
}

const gameComponentCache = new Map<string, Component>()

async function resolveGameModule(mod: unknown): Promise<Component> {
  if (mod && typeof mod === 'object' && 'default' in (mod as object)) {
    return (mod as { default: Component }).default
  }
  return mod as Component
}

/** 缓存的异步组件（勿在 computed 内重复 defineAsyncComponent） */
export function getGameComponent(gameId: string): Component | undefined {
  if (!GAME_BY_ID[gameId]) return undefined
  if (!gameComponentCache.has(gameId)) {
    const meta = GAME_BY_ID[gameId]!
    gameComponentCache.set(
      gameId,
      defineAsyncComponent({
        loader: () => meta.loadComponent().then(resolveGameModule),
        delay: 0,
        timeout: 30_000,
      }),
    )
  }
  return gameComponentCache.get(gameId)
}

export function getModuleGame(moduleKey: string): ModuleGameMeta | undefined {
  const gid = MODULE_GAME_MAP[moduleKey]
  return gid ? GAME_BY_ID[gid] : undefined
}

export function getModuleGameLevelForSection(
  moduleKey: string,
  sectionId?: string,
): GameLevelMeta | undefined {
  const game = getModuleGame(moduleKey)
  if (!game) return undefined
  const mappedLevelId = sectionId ? SECTION_GAME_LEVEL_MAP[moduleKey]?.[sectionId] : undefined
  return game.levels.find((level) => level.id === mappedLevelId) ?? game.levels[0]
}

export function getDetectiveGame(): ModuleGameMeta {
  return GAME_BY_ID[ALGO_DETECTIVE_GAME_ID]!
}
