import type { TraceStep, TraceVarSnapshot, TreeGraph, TreeNodeData } from '@/types/codeTrace'
import { isSequenceSnapshot, sequenceItems } from '@/utils/traceProtocol'

export type TreeBuildInference = {
  graph: TreeGraph
  queueLabels: string[]
  hotNodeIds: Set<string>
  /** 当前层序下标对应的节点 id（若可解析） */
  activeNodeId: string | null
}

function parseLevelOrderValues(snap: TraceVarSnapshot | undefined): (number | null)[] {
  if (!snap) return []
  const raw = isSequenceSnapshot(snap) ? sequenceItems(snap) : []
  if (!raw.length && snap.type === 'list' && Array.isArray(snap.value)) {
    return (snap.value as number[]).map((x) => Number(x))
  }
  return raw.map((x) => {
    const t = String(x).trim()
    if (!t || t === 'null' || t === 'NULL' || t === '?') return null
    const n = parseInt(t, 10)
    return Number.isFinite(n) ? n : null
  })
}

function scalarInt(vars: Record<string, TraceVarSnapshot>, names: string[]): number | null {
  for (const n of names) {
    const s = vars[n]
    if (s?.type === 'int' && typeof s.value === 'number') return s.value
  }
  return null
}

/** 层序建树模拟：与常见 while(!q.empty() && idx<n) 模板一致 */
function simulateLevelOrderBuild(
  values: (number | null)[],
  n: number,
  stopIdx: number,
): { graph: TreeGraph; queueLabels: string[]; activeNodeId: string | null } {
  const nodes: Record<string, TreeNodeData> = {}
  let seq = 0
  const mk = (v: number): string => {
    const id = `t${seq++}`
    nodes[id] = { id, val: v, left: null, right: null }
    return id
  }

  if (!values.length || values[0] == null) {
    return { graph: { root: null, nodes }, queueLabels: [], activeNodeId: null }
  }

  const rootId = mk(values[0]!)
  const q: string[] = [rootId]
  let idx = 1
  let activeNodeId: string | null = rootId
  let iter = 0
  const maxIter = Math.max(n, values.length) * 4 + 8

  while (q.length > 0 && idx < n && idx < stopIdx && iter < maxIter) {
    iter++
    const curId = q.shift()!
    activeNodeId = curId
    const cur = nodes[curId]!
    if (idx < n && idx < values.length && values[idx] != null) {
      const leftId = mk(values[idx]!)
      cur.left = leftId
      q.push(leftId)
      idx++
    }
    if (idx < n && idx < values.length && values[idx] != null) {
      const rightId = mk(values[idx]!)
      cur.right = rightId
      q.push(rightId)
      idx++
    }
  }

  const queueLabels = q.map((id) => String(nodes[id]?.val ?? '?'))
  return { graph: { root: rootId, nodes }, queueLabels, activeNodeId }
}

export function detectTreeBuildPattern(vars: Record<string, TraceVarSnapshot>): boolean {
  const hasNodes = vars.nodes != null || vars.NODES != null
  const hasIdx = vars.idx != null || vars.index != null
  const hasQ = vars.q != null || vars.Q != null
  const hasRoot = vars.root != null
  return Boolean(hasNodes && hasIdx && (hasQ || hasRoot))
}

export function buildLevelOrderTreeInference(
  vars: Record<string, TraceVarSnapshot>,
): TreeBuildInference | null {
  if (!detectTreeBuildPattern(vars)) return null

  const nodesSnap = vars.nodes ?? vars.NODES
  const values = parseLevelOrderValues(nodesSnap)
  if (!values.length || values[0] == null) return null

  const nRaw = scalarInt(vars, ['n', 'N'])
  const n =
    nRaw != null && nRaw > 0 && nRaw <= values.length + 4 ? nRaw : values.length
  const idx = scalarInt(vars, ['idx', 'index']) ?? 1
  const stopIdx = Math.max(1, Math.min(idx, n, values.length + 2))

  const { graph, queueLabels, activeNodeId } = simulateLevelOrderBuild(values, n, stopIdx)
  const hot = new Set<string>()
  if (activeNodeId) hot.add(activeNodeId)
  const currRef = vars.curr
  if (currRef?.type === 'tree_node_ref') {
    const ref = currRef.value as { node?: string | null }
    if (ref?.node) hot.add(ref.node)
  }

  return { graph, queueLabels, hotNodeIds: hot, activeNodeId }
}

export function traceHasTreeBuildPattern(steps: TraceStep[]): boolean {
  return steps.some((s) => detectTreeBuildPattern(s.vars))
}
