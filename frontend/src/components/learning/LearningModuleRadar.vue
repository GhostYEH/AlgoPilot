<script setup lang="ts">
import * as d3 from 'd3'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { ModuleProgressRow } from '@/utils/learningOverview'

const props = withDefaults(
  defineProps<{
    rows: ModuleProgressRow[]
    maxItems?: number
  }>(),
  { maxItems: 8 },
)

const svgRef = ref<SVGSVGElement | null>(null)
let renderToken = 0

const chartRows = computed(() =>
  props.rows
    .filter((r) => r.available && r.hasProgressData)
    .sort((a, b) => b.percent - a.percent)
    .slice(0, props.maxItems),
)

function render() {
  const svgEl = svgRef.value
  if (!svgEl) return
  const token = ++renderToken

  const data = chartRows.value
  const size = 260
  const radius = size / 2 - 36
  const n = data.length

  const svg = d3.select(svgEl)
  svg.selectAll('*').remove()
  svg.attr('width', size).attr('height', size)

  const g = svg.append('g').attr('transform', `translate(${size / 2},${size / 2})`)

  if (!n) {
    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--alp-color-muted)')
      .attr('font-size', 12)
      .text('暂无模块进度')
    return
  }

  const angleSlice = (Math.PI * 2) / n
  const rScale = d3.scaleLinear().domain([0, 100]).range([0, radius])

  const levels = [25, 50, 75, 100]
  g.selectAll('.grid-line')
    .data(levels)
    .enter()
    .append('circle')
    .attr('class', 'grid-line')
    .attr('r', (d) => rScale(d))
    .attr('fill', 'none')
    .attr('stroke', 'color-mix(in srgb, var(--alp-color-border) 70%, transparent)')
    .attr('stroke-dasharray', '3,3')

  const axis = g.append('g').attr('class', 'axis')
  data.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    axis
      .append('line')
      .attr('x1', 0)
      .attr('y1', 0)
      .attr('x2', radius * Math.cos(angle))
      .attr('y2', radius * Math.sin(angle))
      .attr('stroke', 'color-mix(in srgb, var(--alp-color-border) 70%, transparent)')

    axis
      .append('text')
      .attr('x', (radius + 14) * Math.cos(angle))
      .attr('y', (radius + 14) * Math.sin(angle))
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', 'var(--alp-color-muted)')
      .attr('font-size', 10)
      .text(d.label.length > 4 ? d.label.slice(0, 4) : d.label)
  })

  const area = d3
    .areaRadial<{ percent: number }>()
    .radius((d) => rScale(d.percent))
    .angle((_, i) => i * angleSlice)
    .curve(d3.curveLinearClosed)

  const pathData = data.map(() => ({ percent: 0 }))
  const areaPath = g
    .append('path')
    .datum(pathData)
    .attr('fill', 'color-mix(in srgb, var(--alp-color-primary) 25%, transparent)')
    .attr('stroke', 'var(--alp-color-primary)')
    .attr('stroke-width', 2)
    .attr('d', area)

  areaPath
    .transition()
    .duration(900)
    .ease(d3.easeCubicOut)
    .attrTween('d', () => {
      const target = data.map((d) => ({ percent: d.percent }))
      const interp = d3.interpolate(
        pathData,
        target,
      )
      return (t) => area(interp(t)) ?? ''
    })

  g.selectAll('.dot')
    .data(data)
    .enter()
    .append('circle')
    .attr('class', 'dot')
    .attr('r', 0)
    .attr('fill', (d) => d.accent)
    .attr('cx', (_, i) => rScale(0) * Math.cos(angleSlice * i - Math.PI / 2))
    .attr('cy', (_, i) => rScale(0) * Math.sin(angleSlice * i - Math.PI / 2))
    .transition()
    .duration(900)
    .delay((_, i) => i * 80)
    .attr('r', 4)
    .attr('cx', (d, i) => rScale(d.percent) * Math.cos(angleSlice * i - Math.PI / 2))
    .attr('cy', (d, i) => rScale(d.percent) * Math.sin(angleSlice * i - Math.PI / 2))

  if (token !== renderToken) return
}

watch(chartRows, () => void nextTick().then(render), { deep: true })

onMounted(() => void nextTick().then(render))

onUnmounted(() => {
  renderToken += 1
  const svgEl = svgRef.value
  if (svgEl) d3.select(svgEl).selectAll('*').interrupt()
})
</script>

<template>
  <div class="module-radar">
    <svg ref="svgRef" role="img" aria-label="模块掌握雷达图" />
  </div>
</template>

<style scoped>
.module-radar {
  display: flex;
  justify-content: center;
}

.module-radar svg {
  display: block;
}
</style>
