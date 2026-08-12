import type { LinkedListGraph, LinkedListNodeData, TraceStep } from '@/types/codeTrace'
import { isLinkedListGraph } from '@/utils/traceViz'

export interface MergedListScene {
  graph: LinkedListGraph
  pointerLabels: Record<string, string[]>
  /** 指针变量名 -> nodeId */
  pointerRefs: { name: string; nodeId: string | null }[]
}

/** 合并当前步所有 linked_list + node_ref 为一张节点表 */
export function mergeLinkedListScene(step: TraceStep | null): MergedListScene | null {
  if (!step) return null
  const nodes: Record<string, LinkedListNodeData> = {}
  let head: string | null = null
  const pointerLabels: Record<string, string[]> = {}
  const pointerRefs: { name: string; nodeId: string | null }[] = []

  for (const [name, snap] of Object.entries(step.vars)) {
    if (snap.type === 'linked_list' && isLinkedListGraph(snap.value)) {
      Object.assign(nodes, snap.value.nodes)
      if (!head) head = snap.value.head
    }
    if (snap.type === 'node_ref' && snap.value && typeof snap.value === 'object') {
      const v = snap.value as { node?: string | null; nodes?: Record<string, LinkedListNodeData> }
      if (v.nodes) Object.assign(nodes, v.nodes)
      const nid = v.node ?? null
      pointerRefs.push({ name, nodeId: nid })
      if (nid) {
        if (!pointerLabels[nid]) pointerLabels[nid] = []
        pointerLabels[nid].push(name)
      }
    }
  }

  if (!Object.keys(nodes).length) return null
  return { graph: { head, nodes }, pointerLabels, pointerRefs }
}

export interface ListDiff {
  hotNodes: Set<string>
  hotEdges: Set<string>
  hotPointers: Set<string>
}

function edgeKey(from: string, to: string | null) {
  return `${from}->${to ?? 'null'}`
}

export function diffLinkedList(
  prev: MergedListScene | null,
  curr: MergedListScene | null,
  changedVars: string[],
): ListDiff {
  const hotNodes = new Set<string>()
  const hotEdges = new Set<string>()
  const hotPointers = new Set<string>()

  if (!curr) return { hotNodes, hotEdges, hotPointers }

  for (const name of changedVars) {
    if (curr.pointerRefs.some((p) => p.name === name)) hotPointers.add(name)
  }

  if (!prev) {
    Object.keys(curr.graph.nodes).forEach((id) => hotNodes.add(id))
    return { hotNodes, hotEdges, hotPointers }
  }

  const allIds = new Set([
    ...Object.keys(prev.graph.nodes),
    ...Object.keys(curr.graph.nodes),
  ])

  for (const id of allIds) {
    const a = prev.graph.nodes[id]
    const b = curr.graph.nodes[id]
    if (!a || !b) {
      hotNodes.add(id)
      continue
    }
    if (a.val !== b.val) hotNodes.add(id)
    if (a.next !== b.next) {
      hotNodes.add(id)
      hotEdges.add(edgeKey(id, b.next))
      hotEdges.add(edgeKey(id, a.next))
    }
  }

  return { hotNodes, hotEdges, hotPointers }
}

export function orderedFromHead(graph: LinkedListGraph): string[] {
  const chain: string[] = []
  const seen = new Set<string>()
  let cur = graph.head
  let guard = 0
  while (cur && !seen.has(cur) && guard < 64) {
    seen.add(cur)
    chain.push(cur)
    cur = graph.nodes[cur]?.next ?? null
    guard++
  }
  return chain
}

/** 未挂在 head 链上的节点（反转过程中已断开的节段） */
export function orphanNodeIds(graph: LinkedListGraph): string[] {
  const onChain = new Set(orderedFromHead(graph))
  return Object.keys(graph.nodes).filter((id) => !onChain.has(id))
}
