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

const emit = defineEmits<{
  select: [key: string]
}>()

const containerRef = ref<HTMLElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)
let renderToken = 0
let resizeObs: ResizeObserver | undefined

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
  const width = svgEl.parentElement?.clientWidth || svgEl.clientWidth || 360
  const barH = 22
  const gap = 6
  const margin = { top: 8, right: 36, bottom: 8, left: 72 }
  const height = Math.max(120, data.length * (barH + gap) + margin.top + margin.bottom)

  const svg = d3.select(svgEl)
  svg.selectAll('*').remove()
  svg.attr('width', width).attr('height', height)

  if (!data.length) {
    svg
      .append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--alp-color-muted)')
      .attr('font-size', 12)
      .text('开始学习后显示模块进度')
    return
  }

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)
  const innerW = width - margin.left - margin.right

  const x = d3.scaleLinear().domain([0, 100]).range([0, innerW])
  const y = d3
    .scaleBand()
    .domain(data.map((d) => d.key))
    .range([0, data.length * (barH + gap)])
    .paddingInner(0.35)

  g.selectAll('.label')
    .data(data)
    .enter()
    .append('text')
    .attr('class', 'label')
    .attr('x', -8)
    .attr('y', (d) => (y(d.key) ?? 0) + barH / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('fill', 'var(--alp-color-muted)')
    .attr('font-size', 11)
    .text((d) => d.label)

  const bars = g
    .selectAll('.bar')
    .data(data)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', 0)
    .attr('y', (d) => y(d.key) ?? 0)
    .attr('height', barH)
    .attr('width', 0)
    .attr('rx', 4)
    .attr('fill', (d) => d.accent)
    .attr('opacity', 0.85)
    .style('cursor', 'pointer')
    .on('click', (_, d) => emit('select', d.key))

  bars
    .transition()
    .duration(700)
    .delay((_, i) => i * 60)
    .attr('width', (d) => x(d.percent))

  g.selectAll('.pct')
    .data(data)
    .enter()
    .append('text')
    .attr('class', 'pct')
    .attr('x', (d) => x(d.percent) + 6)
    .attr('y', (d) => (y(d.key) ?? 0) + barH / 2)
    .attr('dy', '0.35em')
    .attr('fill', 'var(--alp-color-text)')
    .attr('font-size', 10)
    .text((d) => `${d.percent}%`)

  if (token !== renderToken) return
}

watch(chartRows, () => void nextTick().then(render), { deep: true })

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
  const svgEl = svgRef.value
  if (svgEl) d3.select(svgEl).selectAll('*').interrupt()
})
</script>

<template>
  <div ref="containerRef" class="module-bars">
    <svg ref="svgRef" role="img" aria-label="各模块掌握进度条形图" />
  </div>
</template>

<style scoped>
.module-bars {
  width: 100%;
}

.module-bars svg {
  display: block;
  width: 100%;
  min-height: 120px;
}
</style>
