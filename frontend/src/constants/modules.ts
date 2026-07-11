/**
 * 算法学习模块定义（侧边栏 / 路由 query 等共用）
 * 后续可与后端「知识图谱 / 多智能体资源生成」模块 id 对齐
 */
export type ModulePhase = 'foundation' | 'technique' | 'tree' | 'advanced'

export interface AlgorithmModuleItem {
  /** 路由或接口使用的稳定 key */
  key: string
  /** 中文展示名 */
  label: string
  /** 学习路径阶段（用于地图分组标题） */
  phase: ModulePhase
  /** 是否已有完整学习页（否则走 learning-path 占位） */
  available: boolean
  /** 节点主题色（地图节点描边 / 光晕） */
  accent: string
}

export const MODULE_PHASE_LABELS: Record<ModulePhase, string> = {
  foundation: '基础结构',
  technique: '解题技巧',
  tree: '树与搜索',
  advanced: '进阶算法',
}

export const ALGORITHM_MODULES: AlgorithmModuleItem[] = [
  { key: 'array', label: '数组', phase: 'foundation', available: true, accent: '#3a8a9e' },
  { key: 'linked-list', label: '链表', phase: 'foundation', available: true, accent: '#3a8a9e' },
  { key: 'hash-table', label: '哈希表', phase: 'foundation', available: true, accent: '#3d8a7e' },
  { key: 'string', label: '字符串', phase: 'foundation', available: true, accent: '#34d399' },
  { key: 'two-pointers', label: '双指针法', phase: 'technique', available: true, accent: '#7a6e9e' },
  { key: 'stack-queue', label: '栈与队列', phase: 'technique', available: true, accent: '#6b7a9e' },
  { key: 'sorting', label: '排序算法', phase: 'technique', available: true, accent: '#2e6b78' },
  { key: 'binary-tree', label: '二叉树', phase: 'tree', available: true, accent: '#9e6e88' },
  { key: 'backtracking', label: '回溯算法', phase: 'tree', available: true, accent: '#9e6470' },
  { key: 'greedy', label: '贪心算法', phase: 'advanced', available: true, accent: '#9c8540' },
  { key: 'dp', label: '动态规划', phase: 'advanced', available: true, accent: '#9e6e4a' },
  { key: 'monotonic-stack', label: '单调栈', phase: 'advanced', available: true, accent: '#7a6e8e' },
  { key: 'graph', label: '图论', phase: 'advanced', available: true, accent: '#9e5a5a' },
]

/** 具名学习路由（与 HomeView / 地图点击逻辑一致） */
export const MODULE_ROUTE_NAMES: Partial<Record<string, string>> = {
  array: 'learn-array',
  'linked-list': 'learn-linked-list',
  'hash-table': 'learn-hash-table',
  string: 'learn-string',
  'two-pointers': 'learn-two-pointers',
  'stack-queue': 'learn-stack-queue',
  sorting: 'learn-sorting',
  'binary-tree': 'learn-binary-tree',
  backtracking: 'learn-backtracking',
  greedy: 'learn-greedy',
  dp: 'learn-dp',
  'monotonic-stack': 'learn-monotonic-stack',
  graph: 'learn-graph',
}
