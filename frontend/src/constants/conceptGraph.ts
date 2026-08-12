/**
 * 算法概念级知识图谱（与 backend/knowledge_base/concept_graph.json 同步）
 */

export type ConceptNodeKind = 'module' | 'concept' | 'problem'

export interface ConceptCatalogItem {
  id: string
  label: string
  module_key: string
  keywords: string[]
  prerequisites: string[]
  description?: string
}

export interface ProblemCatalogItem {
  id: string
  label: string
  slug: string
  module_key: string
  concept_ids: string[]
  difficulty: 'easy' | 'medium' | 'hard'
  keywords: string[]
}

export interface PatternEdge {
  source: string
  target: string
  label?: string
}

export interface ConceptGraphNode {
  id: string
  label: string
  kind: ConceptNodeKind
  moduleKey: string
  accent: string
  slug?: string
  difficulty?: string
  description?: string
  prerequisites: string[]
  mastery: number
  radius: number
}

export interface ConceptGraphEdge {
  source: string
  target: string
  label?: string
}

export interface GraphValidationIssue {
  type: 'orphan' | 'missing_prerequisite' | 'dangling_edge'
  nodeId: string
  message: string
}

const CONCEPTS: ConceptCatalogItem[] = [
  { id: 'array-traversal', label: '数组遍历', module_key: 'array', keywords: ['遍历', '下标'], prerequisites: [], description: '按索引访问与遍历数组元素。' },
  { id: 'prefix-sum', label: '前缀和', module_key: 'array', keywords: ['前缀和', '区间和'], prerequisites: ['array-traversal'], description: '预处理区间和，O(1) 查询。' },
  { id: 'binary-search', label: '二分查找', module_key: 'array', keywords: ['二分', '有序'], prerequisites: ['array-traversal'], description: '有序数组 O(log n) 定位。' },
  { id: 'sliding-window', label: '滑动窗口', module_key: 'string', keywords: ['滑动窗口', '子串'], prerequisites: ['two-pointers-same'], description: '可变窗口统计连续子串性质。' },
  { id: 'two-pointers-same', label: '同向双指针', module_key: 'two-pointers', keywords: ['同向', '快慢指针'], prerequisites: ['array-traversal'], description: '同向移动，去重与窗口。' },
  { id: 'two-pointers-opposite', label: '相向双指针', module_key: 'two-pointers', keywords: ['相向', '对撞'], prerequisites: ['array-traversal', 'binary-search'], description: '左右夹逼求和对。' },
  { id: 'linked-list-pointer', label: '链表指针', module_key: 'linked-list', keywords: ['链表', '反转'], prerequisites: [], description: '虚拟头结点与快慢指针。' },
  { id: 'hash-map', label: '哈希映射', module_key: 'hash-table', keywords: ['哈希', '两数之和'], prerequisites: [], description: 'O(1) 查找与计数。' },
  { id: 'stack-adt', label: '栈 ADT', module_key: 'stack-queue', keywords: ['栈', 'LIFO'], prerequisites: [], description: '后进先出，括号匹配基础。' },
  { id: 'monotonic-stack', label: '单调栈', module_key: 'monotonic-stack', keywords: ['单调栈', 'next greater'], prerequisites: ['stack-adt'], description: 'O(n) 邻域极值。' },
  { id: 'tree-traversal', label: '树遍历', module_key: 'binary-tree', keywords: ['dfs', 'bfs', '层序'], prerequisites: ['stack-adt'], description: '递归与迭代遍历。' },
  { id: 'bst', label: '二叉搜索树', module_key: 'binary-tree', keywords: ['bst'], prerequisites: ['tree-traversal', 'binary-search'], description: '有序性 O(log n) 操作。' },
  { id: 'backtrack-dfs', label: '回溯 DFS', module_key: 'backtracking', keywords: ['回溯', '剪枝'], prerequisites: ['tree-traversal'], description: '选择-探索-撤销。' },
  { id: 'greedy-choice', label: '贪心选择', module_key: 'greedy', keywords: ['贪心'], prerequisites: ['array-traversal'], description: '局部最优 + 正确性证明。' },
  { id: 'dp-state', label: 'DP 状态', module_key: 'dp', keywords: ['动态规划', '状态转移'], prerequisites: ['array-traversal'], description: '定义状态与转移方程。' },
  { id: 'dp-knapsack', label: '背包 DP', module_key: 'dp', keywords: ['背包', 'knapsack'], prerequisites: ['dp-state'], description: '01/完全背包模型。' },
  { id: 'comparison-sort', label: '比较排序', module_key: 'sorting', keywords: ['快排', '归并', '比较排序'], prerequisites: ['array-traversal'], description: '基于比较的排序：快排、归并、堆排，O(n log n) 下界。' },
  { id: 'sort-partition', label: '分区与划分', module_key: 'sorting', keywords: ['partition', 'topk'], prerequisites: ['comparison-sort'], description: '快排分区与 Top-K 选择。' },
  { id: 'graph-traversal', label: '图遍历 BFS/DFS', module_key: 'graph', keywords: ['bfs', 'dfs', '连通分量'], prerequisites: ['tree-traversal'], description: '邻接表/矩阵的 BFS 与 DFS 遍历。' },
  { id: 'shortest-path', label: '最短路径', module_key: 'graph', keywords: ['dijkstra', 'bfs 01', '最短路'], prerequisites: ['graph-traversal'], description: 'Dijkstra 与 01-BFS 求加权最短路。' },
]

const PROBLEMS: ProblemCatalogItem[] = [
  { id: 'prob-two-sum', label: '两数之和', slug: 'two-sum', module_key: 'hash-table', concept_ids: ['hash-map'], difficulty: 'easy', keywords: ['two sum'] },
  { id: 'prob-3sum', label: '三数之和', slug: '3sum', module_key: 'two-pointers', concept_ids: ['two-pointers-opposite'], difficulty: 'medium', keywords: ['3sum'] },
  { id: 'prob-valid-paren', label: '有效的括号', slug: 'valid-parentheses', module_key: 'stack-queue', concept_ids: ['stack-adt'], difficulty: 'easy', keywords: ['括号'] },
  { id: 'prob-daily-temp', label: '每日温度', slug: 'daily-temperatures', module_key: 'monotonic-stack', concept_ids: ['monotonic-stack'], difficulty: 'medium', keywords: ['单调栈'] },
  { id: 'prob-climb', label: '爬楼梯', slug: 'climbing-stairs', module_key: 'dp', concept_ids: ['dp-state'], difficulty: 'easy', keywords: ['dp'] },
  { id: 'prob-coin-change', label: '零钱兑换', slug: 'coin-change', module_key: 'dp', concept_ids: ['dp-state'], difficulty: 'medium', keywords: ['dp'] },
  { id: 'prob-reverse-list', label: '反转链表', slug: 'reverse-linked-list', module_key: 'linked-list', concept_ids: ['linked-list-pointer'], difficulty: 'easy', keywords: ['链表'] },
  { id: 'prob-max-depth', label: '二叉树最大深度', slug: 'maximum-depth-of-binary-tree', module_key: 'binary-tree', concept_ids: ['tree-traversal'], difficulty: 'easy', keywords: ['二叉树'] },
  { id: 'prob-valid-anagram', label: '有效的字母异位词', slug: 'valid-anagram', module_key: 'sorting', concept_ids: ['comparison-sort'], difficulty: 'easy', keywords: ['排序'] },
  { id: 'prob-graph-bfs', label: '图的广度优先遍历', slug: 'graph-bfs-traversal', module_key: 'graph', concept_ids: ['graph-traversal'], difficulty: 'easy', keywords: ['图遍历'] },
]

const PATTERN_EDGES: PatternEdge[] = [
  { source: 'prob-3sum', target: 'two-pointers-opposite', label: 'uses' },
  { source: 'prob-3sum', target: 'binary-search', label: 'requires_sort' },
  { source: 'prob-daily-temp', target: 'monotonic-stack', label: 'uses' },
  { source: 'prob-two-sum', target: 'hash-map', label: 'uses' },
  { source: 'sliding-window', target: 'two-pointers-same', label: 'extends' },
]

import { ALGORITHM_MODULES } from './modules'

const MODULE_ACCENTS = Object.fromEntries(ALGORITHM_MODULES.map((m) => [m.key, m.accent]))

export function getConceptCatalog(): ConceptCatalogItem[] {
  return CONCEPTS
}

export function getProblemCatalog(): ProblemCatalogItem[] {
  return PROBLEMS
}

export function getConceptsForModule(moduleKey: string): ConceptCatalogItem[] {
  return CONCEPTS.filter((c) => c.module_key === moduleKey)
}

export function getProblemsForConcept(conceptId: string): ProblemCatalogItem[] {
  return PROBLEMS.filter((p) => p.concept_ids.includes(conceptId))
}

export function validateConceptGraph(): GraphValidationIssue[] {
  const ids = new Set([
    ...CONCEPTS.map((c) => c.id),
    ...PROBLEMS.map((p) => p.id),
  ])
  const issues: GraphValidationIssue[] = []

  for (const c of CONCEPTS) {
    for (const pre of c.prerequisites) {
      if (!ids.has(pre)) {
        issues.push({
          type: 'missing_prerequisite',
          nodeId: c.id,
          message: `「${c.label}」的先修「${pre}」不存在`,
        })
      }
    }
  }

  const hasIncoming = new Set<string>()
  for (const c of CONCEPTS) {
    if (c.prerequisites.length) hasIncoming.add(c.id)
  }
  for (const e of PATTERN_EDGES) {
    hasIncoming.add(e.target)
  }

  for (const c of CONCEPTS) {
    if (
      !c.prerequisites.length &&
      c.module_key !== 'array' &&
      c.module_key !== 'linked-list' &&
      c.module_key !== 'hash-table' &&
      c.module_key !== 'stack-queue' &&
      !hasIncoming.has(c.id)
    ) {
      issues.push({ type: 'orphan', nodeId: c.id, message: `概念「${c.label}」缺少入边，可能孤立` })
    }
  }

  for (const e of PATTERN_EDGES) {
    if (!ids.has(e.source) || !ids.has(e.target)) {
      issues.push({
        type: 'dangling_edge',
        nodeId: e.source,
        message: `模式边 ${e.source} → ${e.target} 端点缺失`,
      })
    }
  }

  return issues
}

export function buildConceptGraphNodes(
  masteryMap: Record<string, number>,
  options?: { moduleKey?: string; includeProblems?: boolean; limit?: number },
): ConceptGraphNode[] {
  const moduleKey = options?.moduleKey
  const includeProblems = options?.includeProblems ?? true
  const limit = options?.limit ?? 999

  let concepts = moduleKey ? CONCEPTS.filter((c) => c.module_key === moduleKey) : CONCEPTS
  concepts = concepts.slice(0, limit)

  const nodes: ConceptGraphNode[] = concepts.map((c) => {
    const mastery = masteryMap[c.id] ?? masteryMap[c.module_key] ?? 0
    return {
      id: c.id,
      label: c.label,
      kind: 'concept',
      moduleKey: c.module_key,
      accent: MODULE_ACCENTS[c.module_key] ?? '#4a7e94',
      description: c.description,
      prerequisites: c.prerequisites,
      mastery,
      radius: Math.max(10, Math.min(24, 12 + mastery / 8)),
    }
  })

  if (includeProblems) {
    let problems = moduleKey ? PROBLEMS.filter((p) => p.module_key === moduleKey) : PROBLEMS
    if (limit < 999) problems = problems.slice(0, Math.max(2, Math.floor(limit / 3)))
    for (const p of problems) {
      const mastery = masteryMap[p.slug] ?? masteryMap[p.id] ?? 0
      nodes.push({
        id: p.id,
        label: p.label,
        kind: 'problem',
        moduleKey: p.module_key,
        accent: MODULE_ACCENTS[p.module_key] ?? '#94a3b8',
        slug: p.slug,
        difficulty: p.difficulty,
        prerequisites: p.concept_ids,
        mastery,
        radius: 8,
      })
    }
  }

  return nodes
}

export function buildConceptGraphEdges(
  nodes: ConceptGraphNode[],
  includePattern = true,
): ConceptGraphEdge[] {
  const ids = new Set(nodes.map((n) => n.id))
  const edges: ConceptGraphEdge[] = []

  for (const n of nodes) {
    if (n.kind === 'concept') {
      for (const pre of n.prerequisites) {
        if (ids.has(pre)) edges.push({ source: pre, target: n.id, label: 'prerequisite' })
      }
    } else if (n.kind === 'problem') {
      for (const pre of n.prerequisites) {
        if (ids.has(pre)) edges.push({ source: pre, target: n.id, label: 'applies' })
      }
    }
  }

  if (includePattern) {
    for (const e of PATTERN_EDGES) {
      if (ids.has(e.source) && ids.has(e.target)) {
        edges.push({ source: e.source, target: e.target, label: e.label })
      }
    }
  }

  return edges
}

export function topoSortConceptIds(nodes: ConceptGraphNode[]): string[] {
  const ids = new Set(nodes.map((n) => n.id))
  const incoming = new Map<string, Set<string>>()
  for (const n of nodes) incoming.set(n.id, new Set())
  for (const n of nodes) {
    for (const pre of n.prerequisites) {
      if (ids.has(pre) && ids.has(n.id)) incoming.get(n.id)!.add(pre)
    }
  }

  const order: string[] = []
  const visited = new Set<string>()

  const visit = (id: string) => {
    if (visited.has(id)) return
    visited.add(id)
    for (const dep of incoming.get(id) ?? []) visit(dep)
    order.push(id)
  }

  for (const n of nodes) visit(n.id)
  return order
}
