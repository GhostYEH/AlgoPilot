import type { TraceVarSnapshot } from '@/types/codeTrace'

export type SequenceViewHint =
  | 'vector'
  | 'deque'
  | 'stack'
  | 'queue'
  | 'priority_queue'
  | 'tree_build_queue'

export type AssociativeViewHint = 'map' | 'set' | 'unordered_map' | 'unordered_set'

export type AssociativeEntry = { key: string; value: string | null }

export type SequenceVarItem = {
  name: string
  snap: TraceVarSnapshot
  viewHint: SequenceViewHint
  items: string[]
}

export type AssociativeVarItem = {
  name: string
  snap: TraceVarSnapshot
  viewHint: AssociativeViewHint
  entries: AssociativeEntry[]
}

export function isSequenceSnapshot(snap: TraceVarSnapshot): boolean {
  if (snap.type === 'sequence') return true
  return snap.type === 'list' || snap.type === 'stack' || snap.type === 'queue'
}

export function isAssociativeSnapshot(snap: TraceVarSnapshot): boolean {
  if (snap.type === 'associative') return true
  return snap.type === 'dict'
}

export function sequenceViewHint(snap: TraceVarSnapshot): SequenceViewHint {
  const hint = (snap as TraceVarSnapshot & { view_hint?: string }).view_hint
  if (
    hint === 'vector' ||
    hint === 'deque' ||
    hint === 'stack' ||
    hint === 'queue' ||
    hint === 'priority_queue' ||
    hint === 'tree_build_queue'
  ) {
    return hint
  }
  if (snap.type === 'stack') return 'stack'
  if (snap.type === 'queue') return 'queue'
  return 'vector'
}

export function associativeViewHint(snap: TraceVarSnapshot): AssociativeViewHint {
  const hint = (snap as TraceVarSnapshot & { view_hint?: string }).view_hint
  if (
    hint === 'map' ||
    hint === 'set' ||
    hint === 'unordered_map' ||
    hint === 'unordered_set'
  ) {
    return hint
  }
  return 'map'
}

export function sequenceItems(snap: TraceVarSnapshot | undefined): string[] {
  if (!snap) return []
  const raw = snap.value
  if (!Array.isArray(raw)) return []
  return raw.map((x) => String(x))
}

/** 一维数组类变量（vector / list / deque 作 nums 等） */
export function listLikeValues(snap: TraceVarSnapshot | undefined): string[] {
  if (!snap) return []
  if (isSequenceSnapshot(snap)) {
    const hint = sequenceViewHint(snap)
    if (hint === 'stack' || hint === 'queue' || hint === 'priority_queue' || hint === 'tree_build_queue') {
      return []
    }
    return sequenceItems(snap)
  }
  if (snap.type === 'list' && Array.isArray(snap.value)) {
    return (snap.value as number[]).map((x) => String(x))
  }
  return []
}

export function associativeEntries(snap: TraceVarSnapshot): AssociativeEntry[] {
  const raw = snap.value
  if (Array.isArray(raw)) {
    return (raw as { key?: unknown; value?: unknown }[]).map((e) => ({
      key: String(e.key ?? ''),
      value: e.value == null ? null : String(e.value),
    }))
  }
  if (raw && typeof raw === 'object' && Array.isArray((raw as { entries?: unknown }).entries)) {
    return ((raw as { entries: { key?: unknown; value?: unknown }[] }).entries).map((e) => ({
      key: String(e.key ?? ''),
      value: e.value == null ? null : String(e.value),
    }))
  }
  return []
}

export function diffSequenceItems(prev: string[], curr: string[]): { added: number[]; removed: number[] } {
  const added: number[] = []
  const removed: number[] = []
  const maxLen = Math.max(prev.length, curr.length)
  for (let i = 0; i < maxLen; i++) {
    if (prev[i] !== curr[i]) {
      if (i >= prev.length) added.push(i)
      else if (i >= curr.length) removed.push(i)
      else {
        added.push(i)
        removed.push(i)
      }
    }
  }
  if (curr.length > prev.length) {
    for (let i = prev.length; i < curr.length; i++) added.push(i)
  }
  if (prev.length > curr.length) {
    for (let i = curr.length; i < prev.length; i++) removed.push(i)
  }
  return { added, removed }
}
