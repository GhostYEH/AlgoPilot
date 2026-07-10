<script setup lang="ts">
import * as d3 from 'd3'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { phaseLabel } from '@/utils/learningOverview'
import type { ModulePhase } from '@/constants/modules'
import type { ModuleProgressRow } from '@/utils/learningOverview'

const PHASE_ORDER: ModulePhase[] = ['foundation', 'technique', 'tree', 'advanced']

const props = defineProps<{
  rows: ModuleProgressRow[]
}>()

const svgRef = ref<SVGSVGElement | null>(null)
let renderToken = 0

interface PhaseSlice {
  phase: ModulePhase
  label: string
  done: number
  total: number
}

const slices = computed<PhaseSlice[]>(() => {
  const map = new Map<ModulePhase, { done: number; total: number }>()
  for (const r of props.rows) {
    if (!r.available || r.totalCount === 0) continue
    const cur = map.get(r.phase) ?? { done: 0, total: 0 }
    cur.done += r.doneCount
    cur.total += r.totalCount
    map.set(r.phase, cur)
  }
  return [...map.entries()]
    .map(([phase, v]) => ({
      phase,
      label: phaseLabel(phase),
      done: v.done,
      total: v.total,
    }))
    .sort((a, b) => PHASE_ORDER.indexOf(a.phase) - PHASE_ORDER.indexOf(b.phase))
})

const colors = ['#22d3ee', '#a78bfa', '#f472b6', '#f97316']

function render() {
  const svgEl = svgRef.value
  if (!svgEl) return
  const token = ++renderToken

  const data = slices.value
  const width = 220
  const height = 220
  const radius = Math.min(width, height) / 2 - 8
  const inner = radius * 0.58

  const svg = d3.select(svgEl)
  svg.selectAll('*').remove()
  svg.attr('width', width).attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${width / 2},${height / 2})`)

  if (!data.length) {
    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--alp-color-muted)')
      .attr('font-size', 12)
      .text('暂无进度数据')
    return
  }

  const totalDone = data.reduce((a, d) => a + d.done, 0)
  const totalAll = data.reduce((a, d) => a + d.total, 0)

  if (totalDone === 0) {
    g.append('circle')
      .attr('r', radius)
      .attr('fill', 'none')
      .attr('stroke', 'color-mix(in srgb, var(--alp-color-border) 70%, transparent)')
      .attr('stroke-width', 12)
    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.2em')
      .attr('fill', 'var(--alp-color-text)')
      .attr('font-size', 22)
      .attr('font-weight', 700)
      .text('0')
    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.2em')
      .attr('fill', 'var(--alp-color-muted)')
      .attr('font-size', 11)
      .text(`/ ${totalAll} 节`)
    return
  }

  const pie = d3
    .pie<PhaseSlice>()
    .value((d) => d.done)
    .sort(null)
    .padAngle(0.02)

  const arc = d3
    .arc<d3.PieArcDatum<PhaseSlice>>()
    .innerRadius(inner)
    .outerRadius(radius)
    .cornerRadius(4)

  const arcs = g
    .selectAll('.arc')
    .data(pie(data))
    .enter()
    .append('g')
    .attr('class', 'arc')

  arcs
    .append('path')
    .attr('fill', (_, i) => colors[i % colors.length])
    .attr('opacity', 0.85)
    .transition()
    .duration(700)
    .attrTween('d', function (d) {
      const interp = d3.interpolate({ startAngle: 0, endAngle: 0, innerRadius: inner, outerRadius: radius }, d)
      return (t) => arc(interp(t)) ?? ''
    })

  if (token !== renderToken) return

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .attr('fill', 'var(--alp-color-text)')
    .attr('font-size', 22)
    .attr('font-weight', 700)
    .text(String(totalDone))

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .attr('fill', 'var(--alp-color-muted)')
    .attr('font-size', 11)
    .text(`/ ${totalAll} 节`)
}

watch(slices, () => void nextTick().then(render), { deep: true })

onMounted(() => void nextTick().then(render))

onUnmounted(() => {
  renderToken += 1
  const svgEl = svgRef.value
  if (svgEl) d3.select(svgEl).selectAll('*').interrupt()
})
</script>

<template>
  <div class="section-donut">
    <svg ref="svgRef" role="img" aria-label="各阶段小节完成分布" />
    <div v-if="slices.length" class="legend">
      <div v-for="(s, i) in slices" :key="s.phase" class="legend-item">
        <i class="swatch" :style="{ background: colors[i % colors.length] }" />
        <span>{{ s.label }}</span>
        <strong>{{ s.done }}/{{ s.total }}</strong>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-donut {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.legend {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  max-width: 220px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.legend-item strong {
  margin-left: auto;
  color: var(--alp-color-text);
  font-weight: 600;
}

.swatch {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}
</style>
