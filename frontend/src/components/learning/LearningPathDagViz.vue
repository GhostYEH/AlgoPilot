<script setup lang="ts">
import * as d3 from 'd3'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

export interface DagNodeDatum {
  id: string
  label: string
  /** 画像维度得分 1–10，用于节点着色 */
  score: number
  isRemediation?: boolean
  isNext?: boolean
  rank?: number
}

export interface DagEdgeDatum {
  source: string
  target: string
}

const props = defineProps<{
  nodes: DagNodeDatum[]
  edges: DagEdgeDatum[]
  /** 巩固节点插入时，连到该受挫节点 */
  remediationAnchorId?: string | null
  width?: number
  height?: number
}>()

const svgRef = ref<SVGSVGElement | null>(null)
const animatingRemediation = ref(false)
let remediationTimer: number | undefined
let renderToken = 0

const nodeIds = computed(() => new Set(props.nodes.map((n) => n.id)))

function linkPath(sx: number, sy: number, tx: number, ty: number): string {
  const mx = (sx + tx) / 2
  return `M${sx},${sy} C${mx},${sy} ${mx},${ty} ${tx},${ty}`
}

const layout = computed(() => {
  const ids = nodeIds.value
  const incoming = new Map<string, Set<string>>()
  for (const n of props.nodes) incoming.set(n.id, new Set())
  for (const e of props.edges) {
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
  for (const n of props.nodes) assignLayer(n.id)

  const byLayer = new Map<number, DagNodeDatum[]>()
  for (const n of props.nodes) {
    const l = layer.get(n.id) ?? 0
    if (!byLayer.has(l)) byLayer.set(l, [])
    byLayer.get(l)!.push(n)
  }

  const w = props.width ?? 720
  const h = props.height ?? 280
  const padX = 48
  const padY = 36
  const maxLayer = Math.max(0, ...byLayer.keys())
  const layerW = maxLayer > 0 ? (w - padX * 2) / maxLayer : 0

  const positioned: Array<DagNodeDatum & { x: number; y: number }> = []
  for (const [l, group] of byLayer) {
    const sorted = [...group].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99))
    sorted.forEach((n, i) => {
      const yStep = (h - padY * 2) / Math.max(sorted.length, 1)
      positioned.push({
        ...n,
        x: padX + l * layerW,
        y: padY + i * yStep + yStep / 2,
      })
    })
  }

  const links = props.edges
    .filter((e) => ids.has(e.source) && ids.has(e.target))
    .map((e) => {
      const s = positioned.find((n) => n.id === e.source)
      const t = positioned.find((n) => n.id === e.target)
      if (!s || !t) return null
      return { ...e, sx: s.x, sy: s.y, tx: t.x, ty: t.y }
    })
    .filter(Boolean) as Array<DagEdgeDatum & { sx: number; sy: number; tx: number; ty: number }>

  return { positioned, links, w, h }
})

function scoreColor(score: number): string {
  if (score >= 8) return '#38bdf8'
  if (score >= 6) return '#4ade80'
  if (score >= 4) return '#fbbf24'
  return '#f87171'
}

function scoreFill(score: number): string {
  const alpha = 0.12 + (Math.min(10, Math.max(0, score)) / 10) * 0.35
  return `color-mix(in srgb, ${scoreColor(score)} ${Math.round(alpha * 100)}%, #0f172a)`
}

function renderGraph() {
  const svgEl = svgRef.value
  if (!svgEl || !props.nodes.length) return
  const token = ++renderToken
  const { positioned, links, w, h } = layout.value

  const svg = d3.select(svgEl)
  svg.selectAll('*').interrupt()
  svg.selectAll('*').remove()
  svg.attr('viewBox', `0 0 ${w} ${h}`)

  const root = svg.append('g')

  type LinkDatum = { key: string; d: string }
  const linkData: LinkDatum[] = links.map((l) => ({
    key: `${l.source}-${l.target}`,
    d: linkPath(l.sx + 36, l.sy, l.tx - 36, l.ty),
  }))

  root
    .append('g')
    .attr('class', 'dag-links')
    .selectAll<SVGPathElement, LinkDatum>('path')
    .data(linkData, (d) => d.key)
    .join('path')
    .attr('class', 'dag-link')
    .attr('fill', 'none')
    .attr('stroke', '#475569')
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', function () {
      const len = (this as SVGPathElement).getTotalLength?.() ?? 200
      return `${len} ${len}`
    })
    .attr('stroke-dashoffset', function () {
      return (this as SVGPathElement).getTotalLength?.() ?? 200
    })
    .attr('d', (d) => d.d)
    .transition()
    .duration(900)
    .ease(d3.easeCubicOut)
    .attr('stroke-dashoffset', 0)

  const nodeG = root
    .append('g')
    .attr('class', 'dag-nodes')
    .selectAll<SVGGElement, (typeof positioned)[0]>('g')
    .data(positioned, (d) => d.id)
    .join('g')
    .attr('class', (d) => {
      let c = 'dag-node'
      if (d.isRemediation) c += ' dag-node--remediation'
      if (d.isNext) c += ' dag-node--next'
      return c
    })
    .attr('transform', (d) => `translate(${d.x},${d.y})`)
    .style('opacity', 0)

  nodeG
    .append('rect')
    .attr('x', -52)
    .attr('y', -22)
    .attr('width', 104)
    .attr('height', 44)
    .attr('rx', 10)
    .attr('fill', (d) => scoreFill(d.score))
    .attr('stroke', (d) => scoreColor(d.score))
    .attr('stroke-width', (d) => (d.isNext ? 2.5 : 1.5))

  nodeG
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('fill', '#e2e8f0')
    .attr('font-size', 11)
    .text((d) => d.label)

  nodeG
    .filter((d) => !!d.isRemediation)
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('y', -30)
    .attr('fill', '#fbbf24')
    .attr('font-size', 9)
    .text('巩固 Remediation')

  nodeG
    .transition()
    .duration(600)
    .delay((_, i) => i * 80)
    .style('opacity', 1)

  if (token !== renderToken) return
}

watch(
  () => [props.nodes, props.edges, props.remediationAnchorId],
  async () => {
    await nextTick()
    renderGraph()
    if (props.remediationAnchorId && props.nodes.some((n) => n.isRemediation)) {
      animatingRemediation.value = true
      if (remediationTimer) window.clearTimeout(remediationTimer)
      remediationTimer = window.setTimeout(() => {
        animatingRemediation.value = false
      }, 1200)
    }
  },
  { deep: true },
)

onMounted(() => void nextTick().then(renderGraph))

onUnmounted(() => {
  renderToken += 1
  if (remediationTimer) window.clearTimeout(remediationTimer)
  const svgEl = svgRef.value
  if (svgEl) d3.select(svgEl).selectAll('*').interrupt()
})
</script>

<template>
  <div class="dag-viz" :class="{ 'dag-viz--remediating': animatingRemediation }">
    <div class="dag-legend">
      <span class="legend-item"><i class="swatch swatch--high" /> 画像强项 (8+)</span>
      <span class="legend-item"><i class="swatch swatch--mid" /> 中等 (4–7)</span>
      <span class="legend-item"><i class="swatch swatch--low" /> 薄弱预警 (&lt;4)</span>
    </div>
    <svg ref="svgRef" class="dag-svg" role="img" aria-label="个性化学习路径 DAG" />
  </div>
</template>

<style scoped>
.dag-viz {
  padding: 12px;
  border-radius: var(--alp-radius-card);
  background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 25%, var(--alp-color-border));
  transition: box-shadow 0.6s ease;
}

.dag-viz--remediating {
  box-shadow: 0 0 40px color-mix(in srgb, #fbbf24 25%, transparent);
  animation: rem-pulse 1.2s ease-out;
}

@keyframes rem-pulse {
  0% {
    transform: scale(1);
  }
  40% {
    transform: scale(1.01);
  }
}

.dag-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
  margin-right: 4px;
  vertical-align: middle;
}

.swatch--high {
  background: #38bdf8;
}
.swatch--mid {
  background: #fbbf24;
}
.swatch--low {
  background: #f87171;
}

.dag-svg {
  width: 100%;
  height: auto;
  min-height: 240px;
  display: block;
}

.dag-svg :deep(.dag-link) {
  transition: stroke 0.4s;
}

.dag-viz--remediating .dag-svg :deep(.dag-node--remediation) {
  animation: node-pop 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes node-pop {
  from {
    transform: scale(0.6);
    opacity: 0;
  }
}
</style>
