<script setup lang="ts">
import * as d3 from 'd3'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { ActivityDay } from '@/utils/learningActivity'

const props = withDefaults(
  defineProps<{
    days: ActivityDay[]
    weeks?: number
  }>(),
  { weeks: 12 },
)

const svgRef = ref<SVGSVGElement | null>(null)
let renderToken = 0

function localDayOfWeek(dateKey: string): number {
  const [y, m, d] = dateKey.split('-').map(Number)
  return new Date(y, m - 1, d).getDay()
}

function render() {
  const svgEl = svgRef.value
  if (!svgEl) return
  const token = ++renderToken

  const data = props.days
  const cell = 13
  const gap = 3
  const labelW = 28
  const weeks = props.weeks
  const cols = weeks
  const rows = 7

  const width = labelW + cols * (cell + gap) + 8
  const height = rows * (cell + gap) + 24

  const svg = d3.select(svgEl)
  svg.selectAll('*').remove()
  svg.attr('width', width).attr('height', height)

  const maxCount = Math.max(1, ...data.map((d) => d.count))
  const color = d3
    .scaleLinear<string>()
    .domain([0, 1, maxCount])
    .range([
      'color-mix(in srgb, var(--alp-color-border) 60%, transparent)',
      'color-mix(in srgb, var(--alp-color-primary) 35%, transparent)',
      'var(--alp-color-primary)',
    ])
    .clamp(true)

  const dayLabels = ['日', '一', '二', '三', '四', '五', '六']
  const g = svg.append('g').attr('transform', `translate(${labelW}, 16)`)

  dayLabels.forEach((lbl, i) => {
    if (i % 2 === 0) {
      svg
        .append('text')
        .attr('x', 0)
        .attr('y', 16 + i * (cell + gap) + cell / 2)
        .attr('dy', '0.35em')
        .attr('fill', 'var(--alp-color-muted)')
        .attr('font-size', 9)
        .text(lbl)
    }
  })

  data.forEach((d, idx) => {
    const col = Math.floor(idx / 7)
    const row = localDayOfWeek(d.date)
    if (col >= cols) return

    g.append('rect')
      .attr('x', col * (cell + gap))
      .attr('y', row * (cell + gap))
      .attr('width', cell)
      .attr('height', cell)
      .attr('rx', 2)
      .attr('fill', color(d.count))
      .append('title')
      .text(`${d.date}: ${d.count} 次学习活动`)
  })

  svg
    .append('text')
    .attr('x', labelW)
    .attr('y', 10)
    .attr('fill', 'var(--alp-color-muted)')
    .attr('font-size', 10)
    .text('近 12 周学习活跃度')

  if (token !== renderToken) return
}

watch(
  () => [props.days, props.weeks],
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
  <div class="activity-heatmap">
    <svg ref="svgRef" role="img" aria-label="学习活跃度热力图" />
    <div class="heatmap-legend">
      <span>少</span>
      <i v-for="n in 4" :key="n" class="legend-cell" :class="`legend-cell--${n}`" />
      <span>多</span>
    </div>
  </div>
</template>

<style scoped>
.activity-heatmap {
  overflow-x: auto;
  padding: 4px 0;
}

.activity-heatmap svg {
  display: block;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 10px;
  color: var(--alp-color-muted);
}

.legend-cell {
  width: 11px;
  height: 11px;
  border-radius: 2px;
}

.legend-cell--1 {
  background: color-mix(in srgb, var(--alp-color-border) 60%, transparent);
}
.legend-cell--2 {
  background: color-mix(in srgb, var(--alp-color-primary) 25%, transparent);
}
.legend-cell--3 {
  background: color-mix(in srgb, var(--alp-color-primary) 55%, transparent);
}
.legend-cell--4 {
  background: var(--alp-color-primary);
}
</style>
