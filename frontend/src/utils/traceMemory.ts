import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'

export type MemoryRegion = 'stack' | 'heap' | 'global'

export interface MemorySlot {
  id: string
  name: string
  address: string
  displayValue: string
  region: MemoryRegion
}

const PTR_RE = /^0x[0-9a-f]+$/i

function isRawPointer(snap: TraceVarSnapshot): boolean {
  if (snap.type !== 'other' || typeof snap.value !== 'string') return false
  return PTR_RE.test(snap.value.trim())
}

function inferRegion(address: string): MemoryRegion {
  const hex = address.toLowerCase()
  if (hex.startsWith('0x7f') || hex.startsWith('0x7e')) return 'stack'
  if (hex.startsWith('0x55') || hex.startsWith('0x56') || hex.startsWith('0x5')) return 'heap'
  return 'global'
}

function nodeHeapSlots(step: TraceStep): MemorySlot[] {
  const slots: MemorySlot[] = []
  for (const [name, snap] of Object.entries(step.vars)) {
    if (snap.type !== 'linked_list' && snap.type !== 'tree') continue
    const graph = snap.value as { nodes?: Record<string, { id: string; val: unknown }> }
    if (!graph?.nodes) continue
    for (const node of Object.values(graph.nodes)) {
      slots.push({
        id: `${name}:${node.id}`,
        name: `${name}.${node.id}`,
        address: `heap:${node.id}`,
        displayValue: String(node.val ?? '?'),
        region: 'heap',
      })
    }
  }
  return slots
}

/** 从单步 vars 提取 C++ 指针 / 堆节点内存槽 */
export function extractMemorySlots(step: TraceStep | null): MemorySlot[] {
  if (!step) return []

  const slots: MemorySlot[] = []

  for (const [name, snap] of Object.entries(step.vars)) {
    if (isRawPointer(snap)) {
      const addr = String(snap.value).trim()
      slots.push({
        id: name,
        name,
        address: addr,
        displayValue: addr,
        region: inferRegion(addr),
      })
      continue
    }
    if (snap.type === 'node_ref' && snap.value && typeof snap.value === 'object') {
      const ref = snap.value as { node: string | null }
      slots.push({
        id: name,
        name,
        address: ref.node ? `ref:${ref.node}` : 'nullptr',
        displayValue: ref.node ? `→ ${ref.node}` : 'nullptr',
        region: ref.node ? 'heap' : 'stack',
      })
    }
  }

  slots.push(...nodeHeapSlots(step))

  const order: Record<MemoryRegion, number> = { stack: 0, global: 1, heap: 2 }
  return slots.sort((a, b) => order[a.region] - order[b.region] || a.name.localeCompare(b.name))
}

/** 对比两步，返回发生变化的 slot id 集合 */
export function diffMemorySlotIds(prev: MemorySlot[], curr: MemorySlot[]): Set<string> {
  const hot = new Set<string>()
  const prevMap = new Map(prev.map((s) => [s.id, s]))

  for (const slot of curr) {
    const old = prevMap.get(slot.id)
    if (!old || old.address !== slot.address || old.displayValue !== slot.displayValue) {
      hot.add(slot.id)
    }
  }

  for (const old of prev) {
    if (!curr.some((s) => s.id === old.id)) hot.add(old.id)
  }

  return hot
}

export function hasMemoryLayout(step: TraceStep | null): boolean {
  return extractMemorySlots(step).length > 0
}
