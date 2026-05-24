import type {
  LinkedListGraph,
  MatrixValue,
  TraceStep,
  TraceVarSnapshot,
  TreeGraph,
} from '@/types/codeTrace'
import {
  associativeEntries,
  associativeViewHint,
  isAssociativeSnapshot,
  isSequenceSnapshot,
  sequenceItems,
  sequenceViewHint,
  type AssociativeVarItem,
  type SequenceVarItem,
} from '@/utils/traceProtocol'

export function isMatrixValue(v: unknown): v is MatrixValue {
  if (!v || typeof v !== 'object') return false
  const m = v as MatrixValue
  return Array.isArray(m.cells) && typeof m.rows === 'number'
}

export function isLinkedListGraph(v: unknown): v is LinkedListGraph {
  if (!v || typeof v !== 'object') return false
  const g = v as LinkedListGraph
  return g.nodes != null && typeof g.nodes === 'object'
}

export function isTreeGraph(v: unknown): v is TreeGraph {
  if (!v || typeof v !== 'object') return false
  const g = v as TreeGraph
  return g.nodes != null && typeof g.nodes === 'object' && 'root' in g
}

/** 矩阵单元格 diff：返回本步相对上一步变化的坐标 */
export function diffMatrixCells(prev: MatrixValue | null, curr: MatrixValue): string[] {
  if (!prev) {
    const out: string[] = []
    curr.cells.forEach((row, r) =>
      row.forEach((_, c) => {
        out.push(`${r},${c}`)
      }),
    )
    return out
  }
  const hot: string[] = []
  const rows = Math.max(prev.rows, curr.rows)
  const cols = Math.max(prev.cols, curr.cols)
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const a = prev.cells[r]?.[c]
      const b = curr.cells[r]?.[c]
      if (a !== b) hot.push(`${r},${c}`)
    }
  }
  return hot
}

export function isMatrixOverflow(snap: TraceVarSnapshot): boolean {
  return snap.type === 'matrix_overflow'
}

export function matrixOverflowMessage(snap: TraceVarSnapshot): string {
  const v = snap.value as { message?: string } | null
  return v?.message ?? '数据规模过大，仅支持小规模用例可视化'
}

export function matrixFromSnapshot(snap: TraceVarSnapshot): MatrixValue | null {
  if (snap.type === 'matrix' && isMatrixValue(snap.value)) return snap.value
  if (snap.type === 'list' && Array.isArray(snap.value)) {
    const flat = snap.value as number[]
    const n = flat.length
    const cols = Math.max(1, Math.ceil(Math.sqrt(n)))
    const rows = Math.ceil(n / cols)
    const cells: (number | string)[][] = []
    let k = 0
    for (let r = 0; r < rows; r++) {
      const row: (number | string)[] = []
      for (let c = 0; c < cols; c++) {
        row.push(k < n ? flat[k]! : '')
        k++
      }
      cells.push(row)
    }
    return { rows, cols, cells }
  }
  return null
}

export function classifyStepVars(step: TraceStep | null) {
  const scalars: { name: string; snap: TraceVarSnapshot }[] = []
  const lists: { name: string; snap: TraceVarSnapshot }[] = []
  const sequences: SequenceVarItem[] = []
  const associatives: AssociativeVarItem[] = []
  const matrices: { name: string; snap: TraceVarSnapshot }[] = []
  const maps: { name: string; snap: TraceVarSnapshot }[] = []
  const linkedLists: { name: string; snap: TraceVarSnapshot }[] = []
  const nodeRefs: { name: string; snap: TraceVarSnapshot }[] = []
  const treeNodeRefs: { name: string; snap: TraceVarSnapshot }[] = []
  const trees: { name: string; snap: TraceVarSnapshot }[] = []

  if (!step) {
    return {
      scalars,
      lists,
      sequences,
      associatives,
      matrices,
      maps,
      linkedLists,
      nodeRefs,
      treeNodeRefs,
      trees,
    }
  }

  for (const [name, snap] of Object.entries(step.vars)) {
    if (isSequenceSnapshot(snap)) {
      sequences.push({
        name,
        snap,
        viewHint: sequenceViewHint(snap),
        items: sequenceItems(snap),
      })
      if (sequenceViewHint(snap) === 'vector' && snap.type === 'list') {
        lists.push({ name, snap })
      }
      continue
    }
    if (isAssociativeSnapshot(snap)) {
      associatives.push({
        name,
        snap,
        viewHint: associativeViewHint(snap),
        entries: associativeEntries(snap),
      })
      maps.push({ name, snap })
      continue
    }

    switch (snap.type) {
      case 'matrix':
      case 'matrix_overflow':
        matrices.push({ name, snap })
        break
      case 'linked_list':
        linkedLists.push({ name, snap })
        break
      case 'node_ref':
        nodeRefs.push({ name, snap })
        break
      case 'tree_node_ref':
        treeNodeRefs.push({ name, snap })
        break
      case 'tree':
        trees.push({ name, snap })
        break
      case 'list':
        lists.push({ name, snap })
        sequences.push({
          name,
          snap,
          viewHint: 'vector',
          items: sequenceItems(snap),
        })
        break
      case 'queue':
      case 'stack':
        sequences.push({
          name,
          snap,
          viewHint: snap.type === 'stack' ? 'stack' : 'queue',
          items: sequenceItems(snap),
        })
        break
      case 'dict':
        maps.push({ name, snap })
        associatives.push({
          name,
          snap,
          viewHint: 'map',
          entries: associativeEntries(snap),
        })
        break
      case 'int':
      case 'float':
      case 'bool':
      case 'str':
      case 'none':
        scalars.push({ name, snap })
        break
      case 'other':
        if (typeof snap.value === 'string') {
          if (/std::(stack|deque|vector|map|unordered_map)/i.test(snap.value)) break
          scalars.push({
            name,
            snap: { type: 'str', value: snap.value },
          })
        }
        break
      default:
        break
    }
  }
  return {
    scalars,
    lists,
    sequences,
    associatives,
    matrices,
    maps,
    linkedLists,
    nodeRefs,
    treeNodeRefs,
    trees,
  }
}

/** 将 int 下标 + node_ref 合并为链表上的悬浮标签 */
export function nodeRefLabels(
  nodeRefs: { name: string; snap: TraceVarSnapshot }[],
): Record<string, string[]> {
  const labels: Record<string, string[]> = {}
  for (const { name, snap } of nodeRefs) {
    if (snap.type !== 'node_ref' || !snap.value || typeof snap.value !== 'object') continue
    const node = (snap.value as { node?: string | null }).node
    if (node) {
      if (!labels[node]) labels[node] = []
      labels[node].push(name)
    }
  }
  return labels
}
