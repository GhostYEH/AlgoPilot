import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'
import { mergeTraceVarsForViz } from '@/utils/traceHashLookup'
import {
  isSequenceSnapshot,
  listLikeValues,
  sequenceItems,
  sequenceViewHint,
} from '@/utils/traceProtocol'

export type MonotonicQueueScene = {
  nums: string[]
  queueName: string
  queueIndices: number[]
  windowSize: number | null
  activeIndex: number | null
  windowStart: number | null
  windowEnd: number | null
  maxInWindow: string | null
}

const QUEUE_NAMES = new Set([
  'q',
  'dq',
  'deque',
  'queue',
  'monotonic_queue',
  'mq',
  'candq',
])

const NUMS_NAMES = ['nums', 'nums1', 'arr', 'array', 'numbers', 'a']

function scalarInt(vars: Record<string, TraceVarSnapshot>, names: string[]): number | null {
  for (const n of names) {
    const s = vars[n]
    if (s?.type === 'int' && typeof s.value === 'number') return s.value
  }
  return null
}

function listValues(snap: TraceVarSnapshot | undefined): string[] {
  return listLikeValues(snap)
}

export function isQueueVarName(name: string): boolean {
  const low = name.toLowerCase()
  return QUEUE_NAMES.has(low) || low.endsWith('_queue') || low.endsWith('deque')
}

export function parseQueueIndices(
  snap: TraceVarSnapshot | undefined,
  varName = '',
): number[] {
  if (!snap) return []
  if (isSequenceSnapshot(snap)) {
    const hint = sequenceViewHint(snap)
    if (
      hint === 'queue' ||
      hint === 'deque' ||
      hint === 'priority_queue' ||
      isQueueVarName(varName)
    ) {
      return sequenceItems(snap)
        .map((x) => parseInt(x, 10))
        .filter((n) => Number.isFinite(n))
    }
  }
  if (snap.type === 'queue' && Array.isArray(snap.value)) {
    return (snap.value as number[])
      .map((x) => (typeof x === 'number' ? x : parseInt(String(x), 10)))
      .filter((n) => Number.isFinite(n))
  }
  if (snap.type === 'list' && Array.isArray(snap.value)) {
    return (snap.value as number[]).map((x) => Number(x))
  }
  if (typeof snap.value === 'string') {
    const text = snap.value
    const py = text.match(/deque\(\[([^\]]*)\]/i)
    if (py) {
      return py[1]
        .split(',')
        .map((s) => parseInt(s.trim(), 10))
        .filter((n) => Number.isFinite(n))
    }
    const gdb = text.match(/deque[^=]*=\s*\{([^}]*)\}/i)
    if (gdb) {
      return gdb[1]
        .split(',')
        .map((s) => parseInt(s.trim(), 10))
        .filter((n) => Number.isFinite(n))
    }
  }
  return []
}

function looksLikePointerIndices(indices: number[]): boolean {
  return indices.some((x) => !Number.isFinite(x) || Math.abs(x) > 50_000)
}

function traceHasQueueVar(steps: TraceStep[]): boolean {
  return steps.some((s) =>
    Object.entries(s.vars).some(([name, snap]) => {
      if (!isQueueVarName(name)) return false
      if (sequenceViewHint(snap) === 'tree_build_queue') return false
      const indices = parseQueueIndices(snap, name)
      if (indices.length && looksLikePointerIndices(indices)) return false
      return true
    }),
  )
}

export function buildMonotonicQueueScene(
  step: TraceStep | null,
  mergedVars: Record<string, TraceVarSnapshot>,
  steps: TraceStep[] = [],
): MonotonicQueueScene | null {
  if (!step) return null
  if (!traceHasQueueVar(steps)) return null

  let nums: string[] = []
  for (const n of NUMS_NAMES) {
    const vals = listValues(mergedVars[n])
    if (vals.length) {
      nums = vals
      break
    }
  }
  if (!nums.length) {
    for (const [, snap] of Object.entries(mergedVars)) {
      if (snap.type === 'list' && Array.isArray(snap.value) && (snap.value as number[]).length >= 2) {
        nums = (snap.value as number[]).map(String)
        break
      }
    }
  }

  let queueName = 'q'
  let queueIndices: number[] = []
  for (const [name, snap] of Object.entries(mergedVars)) {
    if (!isQueueVarName(name)) continue
    const parsed = parseQueueIndices(snap, name)
    if (parsed.length || snap.type === 'queue' || (isSequenceSnapshot(snap) && sequenceViewHint(snap) !== 'vector')) {
      queueIndices = parsed
      queueName = name
      break
    }
  }

  if (!nums.length) return null
  if (looksLikePointerIndices(queueIndices)) return null
  if (sequenceViewHint(mergedVars[queueName] ?? { type: 'none', value: null }) === 'tree_build_queue') {
    return null
  }

  const windowSize = scalarInt(mergedVars, ['k', 'window', 'window_size', 'size'])
  const activeIndex = scalarInt(mergedVars, ['i', 'j', 'right', 'r', 'idx', 'index'])

  let windowStart: number | null = null
  let windowEnd: number | null = null
  if (activeIndex != null && windowSize != null && windowSize > 0) {
    windowEnd = activeIndex
    windowStart = Math.max(0, activeIndex - windowSize + 1)
  }

  let maxInWindow: string | null = null
  if (queueIndices.length && nums.length) {
    const front = queueIndices[0]
    if (front >= 0 && front < nums.length) maxInWindow = nums[front]!
  }

  return {
    nums,
    queueName,
    queueIndices,
    windowSize,
    activeIndex,
    windowStart,
    windowEnd,
    maxInWindow,
  }
}

export function detectQueueFromTrace(steps: TraceStep[], frame: number): boolean {
  if (!traceHasQueueVar(steps)) return false
  const merged = mergeTraceVarsForViz(steps, frame)
  return buildMonotonicQueueScene(steps[frame] ?? null, merged, steps) != null
}
