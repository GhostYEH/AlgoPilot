import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'
import { associativeEntries, isAssociativeSnapshot, listLikeValues } from '@/utils/traceProtocol'
import { isQueueVarName } from '@/utils/traceQueue'
import { isStackVarName } from '@/utils/traceStack'

function isGarbageStr(val: unknown): boolean {
  if (typeof val !== 'string') return false
  if (/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(val)) return true
  if (/\\0\d{2,3}/.test(val) && val.length > 8) return true
  return false
}

function snapOkForMerge(snap: TraceVarSnapshot): boolean {
  if (snap.type === 'str' && isGarbageStr(snap.value)) return false
  return true
}

export type MapEntry = { key: string; value: string }

export type HashLookupScene = {
  nums: string[]
  target: number | null
  mapEntries: MapEntry[]
  mapName: string
  activeIndex: number | null
  complement: number | null
  lookupKey: string | null
  found: boolean
  result: number[]
}

const MAP_NAMES = new Set([
  'num_map',
  'map',
  'seen',
  'hash',
  'freq',
  'm',
  'table',
  'dict',
  'count',
])

const NUMS_NAMES = new Set(['nums', 'nums1', 'nums2', 'arr', 'array', 'numbers'])

export function parseMapEntries(snap: TraceVarSnapshot): MapEntry[] {
  if (isAssociativeSnapshot(snap)) {
    return associativeEntries(snap).map((e) => ({
      key: e.key,
      value: e.value ?? '',
    }))
  }
  if (snap.type === 'dict' && snap.value && typeof snap.value === 'object') {
    const v = snap.value as Record<string, unknown>
    if (Array.isArray(v.entries)) {
      return (v.entries as { key?: unknown; value?: unknown }[]).map((e) => ({
        key: String(e.key ?? ''),
        value: String(e.value ?? ''),
      }))
    }
    const out: MapEntry[] = []
    for (const [k, val] of Object.entries(v)) {
      if (k.startsWith('_')) continue
      out.push({ key: k, value: String(val) })
    }
    return out
  }
  if (snap.type === 'other' && typeof snap.value === 'string') {
    const text = snap.value
    const inner = text.match(/\{(.+)\}/)?.[1]
    if (inner) {
      const out: MapEntry[] = []
      for (const m of inner.matchAll(/\[(-?\d+)\]\s*=\s*(-?\d+)/g)) {
        out.push({ key: m[1], value: m[2] })
      }
      if (out.length) return out
    }
    const cnt = text.match(/unordered_map[^(]*（(\d+)\s*项）/) || text.match(/with (\d+) elements/)
    if (cnt && Number(cnt[1]) === 0) return []
  }
  return []
}

function listValues(snap: TraceVarSnapshot): string[] {
  return listLikeValues(snap)
}

function scalarInt(vars: Record<string, TraceVarSnapshot>, names: string[]): number | null {
  for (const n of names) {
    const s = vars[n]
    if (s?.type === 'int' && typeof s.value === 'number') return s.value
  }
  return null
}

/** 合并历史步中的数组/字典，避免早期步只显示单个标量 */
export function mergeTraceVarsForViz(
  steps: TraceStep[],
  frame: number,
): Record<string, TraceVarSnapshot> {
  const merged: Record<string, TraceVarSnapshot> = { ...steps[frame]?.vars }
  for (let i = frame; i >= 0; i--) {
    const v = steps[i]?.vars
    if (!v) continue
    for (const [name, snap] of Object.entries(v)) {
      if (name in merged) continue
      if (
        snap.type === 'list' ||
        snap.type === 'sequence' ||
        snap.type === 'dict' ||
        snap.type === 'associative' ||
        snap.type === 'queue' ||
        snap.type === 'str' ||
        snap.type === 'int' ||
        snap.type === 'float' ||
        snap.type === 'bool' ||
        (snap.type === 'other' && typeof snap.value === 'string') ||
        (snap.type === 'other' && MAP_NAMES.has(name)) ||
        snap.type === 'stack' ||
        isQueueVarName(name) ||
        isStackVarName(name)
      ) {
        if (!snapOkForMerge(snap)) continue
        merged[name] = snap
      }
    }
  }
  return merged
}

export function inferMapEntriesFromTrace(
  steps: TraceStep[],
  frame: number,
  nums: string[],
): MapEntry[] {
  const acc = new Map<string, string>()

  for (let f = 0; f <= frame; f++) {
    const st = steps[f]
    if (!st) continue

    const snap = st.vars.num_map ?? st.vars.map ?? st.vars.seen
    if (snap) {
      const parsed = parseMapEntries(snap)
      if (parsed.length) {
        acc.clear()
        for (const e of parsed) acc.set(e.key, e.value)
      }
    }

    if (st.changed.some((c) => MAP_NAMES.has(c) || c.endsWith('_map'))) {
      const iVal = st.vars.i ?? st.vars.idx
      const i =
        iVal?.type === 'int' && typeof iVal.value === 'number' ? iVal.value : null
      if (i != null && i >= 0 && i < nums.length) {
        acc.set(String(nums[i]), String(i))
      }
    }
  }

  return [...acc.entries()].map(([key, value]) => ({ key, value }))
}

function hasHashMapVariable(vars: Record<string, TraceVarSnapshot>): boolean {
  for (const [name, snap] of Object.entries(vars)) {
    if (!MAP_NAMES.has(name) && !name.endsWith('_map')) continue
    if (snap.type === 'dict' || snap.type === 'associative') return true
    const text = String(snap.value ?? '')
    if (snap.type === 'other' && /unordered_map|^\s*map/i.test(text)) return true
  }
  return false
}

function traceUsesHashMap(steps: TraceStep[], frame: number): boolean {
  for (let f = 0; f <= frame; f++) {
    if (hasHashMapVariable(steps[f]?.vars ?? {})) return true
  }
  return false
}

export function buildHashLookupScene(
  step: TraceStep | null,
  mergedVars: Record<string, TraceVarSnapshot>,
  steps: TraceStep[] = [],
  frame = 0,
): HashLookupScene | null {
  if (!step) return null

  let nums: string[] = []
  for (const n of NUMS_NAMES) {
    const s = mergedVars[n]
    if (s) {
      const vals = listValues(s)
      if (vals.length) {
        nums = vals
        break
      }
    }
  }
  if (!nums.length) {
    for (const [, snap] of Object.entries(mergedVars)) {
      if (snap.type === 'list' && Array.isArray(snap.value) && (snap.value as number[]).length) {
        nums = (snap.value as number[]).map(String)
        break
      }
    }
  }

  let mapEntries: MapEntry[] = []
  let mapName = 'map'
  for (const [name, snap] of Object.entries(mergedVars)) {
    if (!MAP_NAMES.has(name) && !name.endsWith('_map') && snap.type !== 'dict') continue
    const entries = parseMapEntries(snap)
    if (entries.length || snap.type === 'dict' || String(snap.value).includes('unordered_map')) {
      mapEntries = entries
      mapName = name
      break
    }
  }

  if (nums.length) {
    mapEntries = inferMapEntriesFromTrace(steps, frame, nums)
    if (!mapName && mapEntries.length) mapName = 'num_map'
  }

  const complement = scalarInt(mergedVars, ['complement', 'need', 'diff', 'rest'])

  if (Object.keys(mergedVars).some((n) => isQueueVarName(n) || isStackVarName(n))) return null

  const target = scalarInt(mergedVars, ['target', 'tgt'])
  const activeIndex = scalarInt(mergedVars, ['i', 'idx', 'index'])
  const usesHash = traceUsesHashMap(steps, frame)
  const isTwoSumLike =
    target != null && nums.length > 0 && (usesHash || complement != null)

  if (!usesHash && !isTwoSumLike) return null
  if (!nums.length && !usesHash) return null

  if (!nums.length && !mapEntries.length && target == null) return null

  const lookupKey = complement != null ? String(complement) : null

  const found =
    mapEntries.some((e) => lookupKey != null && e.key === lookupKey) &&
    (step.changed.includes(mapName) ||
      step.changed.includes('complement') ||
      step.line >= 27)

  let result: number[] = []
  if (found && activeIndex != null && lookupKey != null) {
    const hit = mapEntries.find((e) => e.key === lookupKey)
    if (hit) result = [Number(hit.value), activeIndex]
  }

  return {
    nums,
    target,
    mapEntries,
    mapName,
    activeIndex,
    complement,
    lookupKey,
    found,
    result,
  }
}
