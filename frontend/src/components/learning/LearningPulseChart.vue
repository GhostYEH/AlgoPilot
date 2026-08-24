<script setup lang="ts">
import * as d3 from 'd3'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { ActivityDay } from '@/utils/learningActivity'

const props = withDefaults(
  defineProps<{
    days: ActivityDay[]
    range?: 7 | 30 | 90
  }>(),
  { range: 30 },
)

const containerRef = ref<HTMLElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)
let resizeObs: ResizeObserver | undefined
let renderToken = 0

const chartDays = computed(() => props.days.slice(-props.range))

function dateLabel(dateKey: string): string {
  const date = new Date(`${dateKey}T00:00:00`)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function tooltipText(day: ActivityDay): string {
  const parts = [`${dateLabel(day.date)} 学习活动 ${day.count} 次`]
  if (day.eventCount > 0) parts.push(`账号事件 ${day.eventCount} 次`)
  if (day.visitCount > 0) parts.push(`模块访问 ${day.visitCount} 次`)
  if (day.gameCount > 0) parts.push(`闯关 ${day.gameCount} 次`)
  return parts.join('\n')
}

function render() {
  const svgEl = svgRef.value
  if (!svgEl) return
  const token = ++renderToken
  const data = chartDays.value
  const width = containerRef.value?.clientWidth || 520
  const height = width < 460 ? 188 : 214
  const margin = { top: 14, right: 14, bottom: 28, left: 28 }
  const innerW = Math.max(1, width - margin.left - margin.right)
  const innerH = height - margin.top - margin.bottom
  const svg = d3.select(svgEl)
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  svg.selectAll('*').remove()
  svg.attr('viewBox', `0 0 ${width} ${height}`).attr('width', width).attr('height', height)

  if (!data.length) {
    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--alp-color-muted)')
      .attr('font-size', 12)
      .text('完成一次学习后，这里会出现你的活动曲线')
    return
  }

  const maxCount = Math.max(2, d3.max(data, (d) => d.count) ?? 0)
  const x = d3.scalePoint<number>().domain(data.map((_, i) => i)).range([0, innerW]).padding(0.2)
  const y = d3.scaleLinear().domain([0, maxCount]).nice(3).range([innerH, 0])
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const yTicks = y.ticks(3)
  g.selectAll('.grid')
    .data(yTicks)
    .enter()
    .append('line')
    .attr('class', 'grid')
    .attr('x1', 0)
    .attr('x2', innerW)
    .attr('y1', (d) => y(d))
    .attr('y2', (d) => y(d))
    .attr('stroke', 'var(--alp-color-border)')
    .attr('stroke-dasharray', '2 4')
    .attr('opacity', 0.7)

  g.selectAll('.tick-label')
    .data(yTicks)
    .enter()
    .append('text')
    .attr('class', 'tick-label')
    .attr('x', -8)
    .attr('y', (d) => y(d))
    .attr('text-anchor', 'end')
    .attr('dy', '0.35em')
    .attr('fill', 'var(--alp-color-muted)')
    .attr('font-size', 10)
    .text((d) => d)

  const area = d3
    .area<ActivityDay>()
    .x((_, i) => x(i) ?? 0)
    .y0(innerH)
    .y1((d) => y(d.count))
    .curve(d3.curveMonotoneX)
  const line = d3
    .line<ActivityDay>()
    .x((_, i) => x(i) ?? 0)
    .y((d) => y(d.count))
    .curve(d3.curveMonotoneX)

  const areaPath = g
    .append('path')
    .datum(data)
    .attr('d', area)
    .attr('fill', 'var(--alp-color-primary)')
    .attr('opacity', 0.12)

  const linePath = g
    .append('path')
    .datum(data)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', 'var(--alp-color-primary)')
    .attr('stroke-width', 2.5)
    .attr('stroke-linecap', 'round')
    .attr('stroke-linejoin', 'round')

  const points = g
    .selectAll('.point')
    .data(data)
    .enter()
    .append('circle')
    .attr('class', 'point')
    .attr('cx', (_, i) => x(i) ?? 0)
    .attr('cy', (d) => y(d.count))
    .attr('r', (d) => (d.count > 0 ? 3.5 : 2.5))
    .attr('fill', 'var(--alp-bg-surface)')
    .attr('stroke', 'var(--alp-color-primary)')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')

  points.append('title').text(tooltipText)

  const labelStep = Math.max(1, Math.ceil(data.length / (width < 460 ? 4 : 7)))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % labelStep === 0 || i === data.length - 1))
    .enter()
    .append('text')
    .attr('class', 'x-label')
    .attr('x', (d) => x(data.indexOf(d)) ?? 0)
    .attr('y', innerH + 20)
    .attr('text-anchor', 'middle')
    .attr('fill', 'var(--alp-color-muted)')
    .attr('font-size', 10)
    .text((d) => dateLabel(d.date))

  if (!reduceMotion) {
    const totalLength = (linePath.node() as SVGPathElement | null)?.getTotalLength?.() ?? 0
    linePath
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(700)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
    areaPath.attr('opacity', 0).transition().duration(450).attr('opacity', 0.12)
    points.attr('opacity', 0).transition().duration(450).delay((_, i) => i * 8).attr('opacity', 1)
  }

  if (token !== renderToken) return
}

watch(() => [props.days, props.range], () => void nextTick().then(render), { deep: true })

onMounted(() => {
  void nextTick().then(render)
  if (containerRef.value) {
    resizeObs = new ResizeObserver(() => render())
    resizeObs.observe(containerRef.value)
  }
})

onUnmounted(() => {
  renderToken += 1
  resizeObs?.disconnect()
  if (svgRef.value) d3.select(svgRef.value).selectAll('*').interrupt()
})
</script>

<template>
  <div ref="containerRef" class="learning-pulse-chart">
    <svg ref="svgRef" role="img" aria-label="学习活动趋势图" />
  </div>
</template>

<style scoped>
.learning-pulse-chart {
  width: 100%;
  min-width: 0;
}

.learning-pulse-chart svg {
  display: block;
  width: 100%;
  overflow: visible;
}
</style>
