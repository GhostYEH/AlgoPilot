import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'
import { mergeTraceVarsForViz } from '@/utils/traceHashLookup'
import { isSequenceSnapshot, sequenceItems, sequenceViewHint } from '@/utils/traceProtocol'

export type StackScene = {
  name: string
  items: string[]
  inputString: string | null
  currentChar: string | null
  isValid: boolean | null
}

const STACK_NAMES = new Set([
  'st',
  'stack',
  'stk',
  'paren_stack',
  'char_stack',
  'brackets',
])

export function isStackVarName(name: string): boolean {
  const low = name.toLowerCase()
  return STACK_NAMES.has(low) || low.endsWith('_stack') || low.endsWith('stack')
}

export function parseStackItems(
  snap: TraceVarSnapshot | undefined,
  varName = '',
): string[] {
  if (!snap) return []
  if (isSequenceSnapshot(snap)) {
    if (sequenceViewHint(snap) === 'stack' || isStackVarName(varName)) {
      return sequenceItems(snap)
    }
  }
  if (snap.type === 'stack' && Array.isArray(snap.value)) {
    return (snap.value as (string | number)[]).map((x) => String(x))
  }
  if (snap.type === 'list' && Array.isArray(snap.value) && isStackVarName(varName)) {
    return (snap.value as number[]).map(String)
  }
  if (typeof snap.value === 'string') {
    const text = snap.value.trim()
    const charM = text.match(/^(-?\d+)\s+'((?:\\.|[^'\\])*)'$/)
    if (charM) {
      const code = parseInt(charM[1], 10)
      if (code >= 32 && code <= 126) return [String.fromCharCode(code)]
    }
    const m = text.match(/std::stack[^=]*=\s*\{([^}]*)\}/i)
    if (m) {
      const chars = m[1].match(/'([^'\\]|\\.)'/g)
      if (chars) return chars.map((c) => c.slice(1, -1))
    }
    if (text.includes('std::stack') && text.includes('element')) {
      return []
    }
  }
  return []
}

function traceHasStackVar(steps: TraceStep[]): boolean {
  return steps.some((s) => Object.keys(s.vars).some((n) => isStackVarName(n)))
}

export function buildStackScene(
  step: TraceStep | null,
  mergedVars: Record<string, TraceVarSnapshot>,
  steps: TraceStep[] = [],
): StackScene | null {
  if (!step || !traceHasStackVar(steps)) return null

  let name = 'st'
  let items: string[] = []

  const varNames = new Set([...Object.keys(step.vars), ...Object.keys(mergedVars)])
  for (const n of varNames) {
    if (!isStackVarName(n)) continue
    const snap = step.vars[n] ?? mergedVars[n]
    if (!snap) continue
    name = n
    items = parseStackItems(snap, n)
    break
  }

  const inputSnap = step.vars.s ?? mergedVars.s
  const inputString =
    inputSnap?.type === 'str' && typeof inputSnap.value === 'string'
      ? sanitizeDisplayString(inputSnap.value)
      : null

  const validSnap =
    step.vars.is_valid ?? step.vars.valid ?? step.vars.ok ?? mergedVars.is_valid ?? mergedVars.valid ?? mergedVars.ok
  const isValid =
    validSnap?.type === 'bool' && typeof validSnap.value === 'boolean'
      ? validSnap.value
      : null

  const cSnap = step.vars.c ?? step.vars.ch
  const currentChar =
    cSnap?.type === 'str' && typeof cSnap.value === 'string' && cSnap.value.length === 1
      ? cSnap.value
      : null

  return { name, items, inputString, currentChar, isValid }
}

function sanitizeDisplayString(raw: string): string | null {
  if (!raw) return raw
  if (/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(raw)) return null
  if (/\\0\d{2,3}/.test(raw) && raw.length > 8) return null
  return raw
}

export function detectStackFromTrace(steps: TraceStep[], frame: number): boolean {
  if (!traceHasStackVar(steps)) return false
  const merged = mergeTraceVarsForViz(steps, frame)
  return buildStackScene(steps[frame] ?? null, merged, steps) != null
}
