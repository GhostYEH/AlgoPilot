import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'
import { mergeTraceVarsForViz } from '@/utils/traceHashLookup'
import { listLikeValues } from '@/utils/traceProtocol'

export type SlidingWindowScene = {
  nums: string[]
  target: number | null
  left: number | null
  right: number | null
  sum: number | null
  minLen: number | null
  shrinking: boolean
}

const LEFT_NAMES = ['left', 'l', 'start', 'lo']
const RIGHT_NAMES = ['right', 'r', 'end', 'hi']
const SUM_NAMES = ['sum', 'total', 'window_sum', 'cur_sum']
const MIN_LEN_NAMES = ['min_len', 'minLen', 'ans', 'res', 'answer']

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

export function buildSlidingWindowScene(
  step: TraceStep | null,
  mergedVars: Record<string, TraceVarSnapshot>,
): SlidingWindowScene | null {
  if (!step) return null

  let nums: string[] = []
  for (const n of ['nums', 'arr', 'array', 'numbers']) {
    const v = listValues(mergedVars[n])
    if (v.length) {
      nums = v
      break
    }
  }
  if (!nums.length) {
    for (const [, snap] of Object.entries(mergedVars)) {
      const v = listValues(snap)
      if (v.length >= 2) {
        nums = v
        break
      }
    }
  }

  const left = scalarInt(mergedVars, LEFT_NAMES)
  const right = scalarInt(mergedVars, RIGHT_NAMES)
  const sum = scalarInt(mergedVars, SUM_NAMES)
  const minLen = scalarInt(mergedVars, MIN_LEN_NAMES)
  const target = scalarInt(mergedVars, ['target', 'goal'])

  if (!nums.length) return null
  if (left == null && right == null && sum == null) return null

  const shrinking =
    target != null && sum != null && sum >= target && step.changed.some((c) =>
      LEFT_NAMES.includes(c),
    )

  return {
    nums,
    target,
    left: left ?? 0,
    right: right ?? left ?? 0,
    sum,
    minLen,
    shrinking,
  }
}

export function detectSlidingWindowFromTrace(
  steps: TraceStep[],
  frame: number,
): boolean {
  const merged = mergeTraceVarsForViz(steps, frame)
  return (
    buildSlidingWindowScene(steps[frame] ?? null, merged) != null &&
    (merged.left != null || merged.right != null || steps.some((s) => 'left' in s.vars))
  )
}
