<script setup lang="ts">
import * as d3 from 'd3'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

export interface DimensionDatum {
  key: string
  label: string
  score: number
}

const props = defineProps<{
  dimensions: DimensionDatum[]
}>()

const svgRef = ref<SVGSVGElement | null>(null)
let renderToken = 0

function render() {
  const svgEl = svgRef.value
  if (!svgEl) return
  const token = ++renderToken

  const data = props.dimensions
  const size = 280
  const radius = size / 2 - 40
  const n = data.length

  const svg = d3.select(svgEl)
  svg.selectAll('*').remove()
  svg.attr('width', size).attr('height', size)

  const g = svg.append('g').attr('transform', `translate(${size / 2},${size / 2})`)

  if (!n) return

  const angleSlice = (Math.PI * 2) / n
  const rScale = d3.scaleLinear().domain([0, 100]).range([0, radius])

  ;[25, 50, 75, 100].forEach((lvl) => {
    g.append('circle')
      .attr('r', rScale(lvl))
      .attr('fill', 'none')
      .attr('stroke', 'color-mix(in srgb, var(--alp-color-border) 70%, transparent)')
      .attr('stroke-dasharray', '3,3')
  })

  data.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    g.append('line')
      .attr('x1', 0)
      .attr('y1', 0)
      .attr('x2', radius * Math.cos(angle))
      .attr('y2', radius * Math.sin(angle))
      .attr('stroke', 'color-mix(in srgb, var(--alp-color-border) 70%, transparent)')

    g.append('text')
      .attr('x', (radius + 16) * Math.cos(angle))
      .attr('y', (radius + 16) * Math.sin(angle))
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', 'var(--alp-color-muted)')
      .attr('font-size', 10)
      .text(d.label)
  })

  const area = d3
    .areaRadial<{ score: number }>()
    .radius((d) => rScale(d.score))
    .angle((_, i) => i * angleSlice)
    .curve(d3.curveLinearClosed)

  const start = data.map(() => ({ score: 0 }))
  const target = data.map((d) => ({ score: d.score }))

  const path = g
    .append('path')
    .datum(start)
    .attr('fill', 'color-mix(in srgb, #a78bfa 30%, transparent)')
    .attr('stroke', '#a78bfa')
    .attr('stroke-width', 2)
    .attr('d', area)

  path
    .transition()
    .duration(900)
    .ease(d3.easeCubicOut)
    .attrTween('d', () => {
      const interp = d3.interpolate(start, target)
      return (t) => area(interp(t)) ?? ''
    })

  if (token !== renderToken) return
}

watch(
  () => props.dimensions,
  () => void nextTick().then(render),
  { deep: true },
)

onMounted(() => void nextTick().then(render))

onUnmounted(() => {
  renderToken += 1
  const svgEl = svgRef.value
  if (svgEl) d3.select(svgEl).selectAll('*').interrupt()
})
</script>

<template>
  <div class="dimension-radar">
    <svg ref="svgRef" role="img" aria-label="评估维度雷达图" />
  </div>
</template>

<style scoped>
.dimension-radar {
  display: flex;
  justify-content: center;
  margin: 8px 0 16px;
}

.dimension-radar svg {
  display: block;
}
</style>
