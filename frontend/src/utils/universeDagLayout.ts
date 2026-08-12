/**
 * DAG 分层自动布局（与 LearningPathDagViz / 后端 prerequisites 边一致）
 * 避免力导向图初始堆叠在 (0,0)。
 */

export interface LayoutNode {
  id: string
  rank?: number
  radius?: number
}

export interface LayoutEdge {
  source: string
  target: string
}

export interface LayoutPosition {
  x: number
  y: number
}

export function layoutUniverseDag(
  nodes: LayoutNode[],
  edges: LayoutEdge[],
  width: number,
  height: number,
): Map<string, LayoutPosition> {
  const positions = new Map<string, LayoutPosition>()
  if (!nodes.length) return positions

  const ids = new Set(nodes.map((n) => n.id))
  const incoming = new Map<string, Set<string>>()
  for (const n of nodes) incoming.set(n.id, new Set())
  for (const e of edges) {
    if (!ids.has(e.source) || !ids.has(e.target)) continue
    incoming.get(e.target)!.add(e.source)
  }

  const layer = new Map<string, number>()
  const visiting = new Set<string>()

  const assignLayer = (id: string): number => {
    if (!ids.has(id)) return 0
    if (layer.has(id)) return layer.get(id)!
    if (visiting.has(id)) return 0
    visiting.add(id)
    const deps = [...(incoming.get(id) ?? [])]
    const l = deps.length ? Math.max(...deps.map(assignLayer)) + 1 : 0
    visiting.delete(id)
    layer.set(id, l)
    return l
  }
  for (const n of nodes) assignLayer(n.id)

  const byLayer = new Map<number, LayoutNode[]>()
  for (const n of nodes) {
    const l = layer.get(n.id) ?? 0
    if (!byLayer.has(l)) byLayer.set(l, [])
    byLayer.get(l)!.push(n)
  }

  const padX = Math.max(56, width * 0.06)
  const padY = Math.max(48, height * 0.08)
  const maxLayer = Math.max(0, ...byLayer.keys())
  const innerW = Math.max(200, width - padX * 2)
  const innerH = Math.max(200, height - padY * 2)
  const layerW = maxLayer > 0 ? innerW / maxLayer : innerW / 2

  for (const [l, group] of byLayer) {
    const sorted = [...group].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99))
    const yStep = innerH / Math.max(sorted.length, 1)
    sorted.forEach((n, i) => {
      positions.set(n.id, {
        x: padX + l * layerW + (maxLayer === 0 ? innerW / 2 : 0),
        y: padY + i * yStep + yStep / 2,
      })
    })
  }

  // 无边或单层时改为环形散布，防止重叠
  if (edges.length === 0 && nodes.length > 1) {
    const cx = width / 2
    const cy = height / 2
    const r = Math.min(innerW, innerH) * 0.36
    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * Math.PI * 2 - Math.PI / 2
      positions.set(n.id, {
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      })
    })
  }

  return positions
}
