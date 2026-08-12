import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'

/** 从当前步标量中解析 DP 循环下标 */
export function parseDpCursor(step: TraceStep | null): { row: number; col: number } | null {
  if (!step) return null
  const pairs: [string, string][] = [
    ['i', 'j'],
    ['r', 'c'],
    ['row', 'col'],
  ]
  for (const [ri, ci] of pairs) {
    const r = scalarInt(step.vars[ri])
    const c = scalarInt(step.vars[ci])
    if (r !== null && c !== null) return { row: r, col: c }
  }
  return null
}

function scalarInt(snap: TraceVarSnapshot | undefined): number | null {
  if (!snap || snap.type !== 'int' || typeof snap.value !== 'number') return null
  return snap.value
}
