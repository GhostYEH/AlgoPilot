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
  { id: 'array-interval', label: '区间与边界', module_key: 'array', keywords: ['区间', '边界'], prerequisites: ['array-traversal'], description: '统一左闭右开区间，减少越界与漏算。' },
  { id: 'linked-list-dummy', label: '虚拟头结点', module_key: 'linked-list', keywords: ['dummy', '哨兵'], prerequisites: ['linked-list-pointer'], description: '使用哨兵节点统一删除和插入的边界处理。' },
  { id: 'linked-list-reverse', label: '链表反转', module_key: 'linked-list', keywords: ['反转', '迭代'], prerequisites: ['linked-list-pointer'], description: '用 pre、cur、next 三指针安全改变链路方向。' },
  { id: 'linked-list-cycle', label: '环与相交', module_key: 'linked-list', keywords: ['快慢指针', '相交'], prerequisites: ['linked-list-pointer'], description: '利用快慢指针判断环、入口与相交。' },
  { id: 'hash-set', label: '集合去重', module_key: 'hash-table', keywords: ['set', '去重'], prerequisites: ['hash-map'], description: '用集合表达“是否出现过”，降低查找复杂度。' },
  { id: 'hash-counting', label: '频次统计', module_key: 'hash-table', keywords: ['计数', '频次'], prerequisites: ['hash-map'], description: '用哈希表记录字符或元素的出现次数。' },
  { id: 'hash-collision', label: '冲突与复杂度', module_key: 'hash-table', keywords: ['冲突', '负载因子'], prerequisites: ['hash-map'], description: '理解冲突处理与均摊 O(1) 的成立条件。' },
  { id: 'string-scan', label: '字符扫描', module_key: 'string', keywords: ['字符串', '遍历'], prerequisites: ['array-traversal'], description: '按字符处理字符串并明确索引边界。' },
  { id: 'string-match', label: '模式匹配', module_key: 'string', keywords: ['匹配', 'KMP'], prerequisites: ['string-scan'], description: '理解前缀表与 KMP 的失配回退过程。' },
  { id: 'string-transform', label: '原地变换', module_key: 'string', keywords: ['反转', '替换'], prerequisites: ['string-scan'], description: '组合双指针完成反转、压缩与局部替换。' },
  { id: 'two-pointers-invariant', label: '循环不变量', module_key: 'two-pointers', keywords: ['不变量', '边界'], prerequisites: ['two-pointers-same'], description: '用不变量解释指针移动条件并证明不会漏解。' },
  { id: 'two-pointers-dedup', label: '排序与去重', module_key: 'two-pointers', keywords: ['去重', '三数之和'], prerequisites: ['two-pointers-opposite'], description: '在有序序列中跳过重复值并保证结果唯一。' },
  { id: 'queue-adt', label: '队列 ADT', module_key: 'stack-queue', keywords: ['队列', 'FIFO'], prerequisites: ['stack-adt'], description: '先进先出，支撑层序遍历与 BFS。' },
  { id: 'stack-expression', label: '表达式与括号', module_key: 'stack-queue', keywords: ['括号', '表达式'], prerequisites: ['stack-adt'], description: '利用栈保存待匹配符号和中间运算状态。' },
  { id: 'deque-pattern', label: '双端队列', module_key: 'stack-queue', keywords: ['deque', '窗口'], prerequisites: ['queue-adt'], description: '在两端 O(1) 操作，支撑滑动窗口与单调队列。' },
  { id: 'sort-merge', label: '归并与分治', module_key: 'sorting', keywords: ['归并', '分治'], prerequisites: ['comparison-sort'], description: '拆分后有序合并，解决逆序对等统计问题。' },
  { id: 'sort-stability', label: '稳定性与选型', module_key: 'sorting', keywords: ['稳定性', '复杂度'], prerequisites: ['comparison-sort'], description: '根据数据规模、稳定性和空间限制选择排序算法。' },
  { id: 'tree-recursion', label: '递归定义', module_key: 'binary-tree', keywords: ['递归', '子问题'], prerequisites: ['tree-traversal'], description: '把整棵树的问题拆成左右子树的同构子问题。' },
  { id: 'tree-level-order', label: '层序遍历', module_key: 'binary-tree', keywords: ['BFS', '层序'], prerequisites: ['tree-traversal'], description: '按层扩展节点并记录每层边界。' },
  { id: 'tree-path', label: '路径与属性', module_key: 'binary-tree', keywords: ['路径', '深度'], prerequisites: ['tree-recursion'], description: '通过返回值或路径状态计算深度与路径。' },
  { id: 'backtrack-choice-tree', label: '决策树建模', module_key: 'backtracking', keywords: ['决策树', '路径'], prerequisites: ['backtrack-dfs'], description: '明确每层选择、可选集合和终止条件。' },
  { id: 'backtrack-pruning', label: '剪枝策略', module_key: 'backtracking', keywords: ['剪枝', '约束'], prerequisites: ['backtrack-choice-tree'], description: '在部分路径已不可能有效时提前停止搜索。' },
  { id: 'backtrack-dedup', label: '排列组合去重', module_key: 'backtracking', keywords: ['去重', 'used'], prerequisites: ['backtrack-choice-tree'], description: '区分树层去重与树枝去重，处理重复元素。' },
  { id: 'greedy-proof', label: '正确性证明', module_key: 'greedy', keywords: ['交换论证', '反证'], prerequisites: ['greedy-choice'], description: '用交换论证或反证法说明局部最优可导向全局最优。' },
  { id: 'greedy-interval', label: '区间贪心', module_key: 'greedy', keywords: ['区间', '排序'], prerequisites: ['greedy-choice'], description: '按端点排序处理不重叠、覆盖与合并问题。' },
  { id: 'greedy-allocation', label: '分配与调度', module_key: 'greedy', keywords: ['分配', '调度'], prerequisites: ['greedy-choice'], description: '根据局部收益或约束顺序完成资源分配。' },
  { id: 'dp-transition', label: '状态转移', module_key: 'dp', keywords: ['转移', '递推'], prerequisites: ['dp-state'], description: '从最后一步或选择集合推导状态间关系。' },
  { id: 'dp-initialization', label: '初始化与顺序', module_key: 'dp', keywords: ['初始化', '遍历顺序'], prerequisites: ['dp-transition'], description: '确定基础状态和保证依赖已计算的遍历顺序。' },
  { id: 'dp-optimization', label: '空间优化', module_key: 'dp', keywords: ['滚动数组', '压缩'], prerequisites: ['dp-initialization'], description: '分析转移依赖，用滚动数组压缩无用维度。' },
  { id: 'monotonic-next-greater', label: '下一个更大元素', module_key: 'monotonic-stack', keywords: ['next greater', '出栈'], prerequisites: ['monotonic-stack'], description: '在元素出栈时确定右侧第一个更大值。' },
  { id: 'monotonic-boundary', label: '左右边界', module_key: 'monotonic-stack', keywords: ['边界', '柱状图'], prerequisites: ['monotonic-stack'], description: '寻找左右最近更小元素以确定贡献区间。' },
  { id: 'monotonic-circular', label: '环形数组处理', module_key: 'monotonic-stack', keywords: ['环形', '取模'], prerequisites: ['monotonic-next-greater'], description: '通过遍历两轮或取模复用单调栈模板。' },
  { id: 'graph-modeling', label: '建图与表示', module_key: 'graph', keywords: ['邻接表', '邻接矩阵'], prerequisites: ['graph-traversal'], description: '把实体与关系抽象成点和边，选择合适的存储方式。' },
  { id: 'graph-topology', label: '拓扑排序', module_key: 'graph', keywords: ['DAG', '入度'], prerequisites: ['graph-traversal'], description: '用入度或 DFS 求有向无环图的依赖顺序。' },
  { id: 'graph-union-find', label: '并查集', module_key: 'graph', keywords: ['并查集', '连通性'], prerequisites: ['graph-modeling'], description: '用路径压缩与按秩合并维护动态连通分量。' },
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
  { id: 'prob-range-sum', label: '区间和查询', slug: 'range-sum-query-immutable', module_key: 'array', concept_ids: ['prefix-sum'], difficulty: 'easy', keywords: ['前缀和'] },
  { id: 'prob-search-insert', label: '搜索插入位置', slug: 'search-insert-position', module_key: 'array', concept_ids: ['binary-search', 'array-interval'], difficulty: 'easy', keywords: ['二分'] },
  { id: 'prob-cycle-list', label: '环形链表 II', slug: 'linked-list-cycle-ii', module_key: 'linked-list', concept_ids: ['linked-list-cycle'], difficulty: 'medium', keywords: ['快慢指针'] },
  { id: 'prob-anagram-count', label: '字母异位词', slug: 'valid-anagram', module_key: 'hash-table', concept_ids: ['hash-counting'], difficulty: 'easy', keywords: ['计数'] },
  { id: 'prob-reverse-words', label: '反转字符串中的单词', slug: 'reverse-words-in-a-string', module_key: 'string', concept_ids: ['string-transform'], difficulty: 'medium', keywords: ['反转'] },
  { id: 'prob-min-window', label: '最小覆盖子串', slug: 'minimum-window-substring', module_key: 'string', concept_ids: ['sliding-window'], difficulty: 'hard', keywords: ['窗口'] },
  { id: 'prob-remove-duplicates', label: '删除有序数组重复项', slug: 'remove-duplicates-from-sorted-array', module_key: 'two-pointers', concept_ids: ['two-pointers-same', 'two-pointers-invariant'], difficulty: 'easy', keywords: ['快慢指针'] },
  { id: 'prob-sliding-max', label: '滑动窗口最大值', slug: 'sliding-window-maximum', module_key: 'stack-queue', concept_ids: ['deque-pattern'], difficulty: 'hard', keywords: ['双端队列'] },
  { id: 'prob-reverse-pairs', label: '数组中的逆序对', slug: 'reverse-pairs', module_key: 'sorting', concept_ids: ['sort-merge'], difficulty: 'hard', keywords: ['归并'] },
  { id: 'prob-level-order', label: '二叉树层序遍历', slug: 'binary-tree-level-order-traversal', module_key: 'binary-tree', concept_ids: ['tree-level-order'], difficulty: 'medium', keywords: ['层序'] },
  { id: 'prob-combinations', label: '组合', slug: 'combinations', module_key: 'backtracking', concept_ids: ['backtrack-choice-tree'], difficulty: 'medium', keywords: ['组合'] },
  { id: 'prob-subsets-ii', label: '子集 II', slug: 'subsets-ii', module_key: 'backtracking', concept_ids: ['backtrack-pruning', 'backtrack-dedup'], difficulty: 'medium', keywords: ['去重'] },
  { id: 'prob-erase-overlap', label: '无重叠区间', slug: 'non-overlapping-intervals', module_key: 'greedy', concept_ids: ['greedy-interval', 'greedy-proof'], difficulty: 'medium', keywords: ['区间'] },
  { id: 'prob-assign-cookies', label: '分发饼干', slug: 'assign-cookies', module_key: 'greedy', concept_ids: ['greedy-allocation'], difficulty: 'easy', keywords: ['分配'] },
  { id: 'prob-largest-rectangle', label: '柱状图中最大矩形', slug: 'largest-rectangle-in-histogram', module_key: 'monotonic-stack', concept_ids: ['monotonic-boundary'], difficulty: 'hard', keywords: ['左右边界'] },
  { id: 'prob-course-schedule', label: '课程表', slug: 'course-schedule', module_key: 'graph', concept_ids: ['graph-modeling', 'graph-topology'], difficulty: 'medium', keywords: ['拓扑排序'] },
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
