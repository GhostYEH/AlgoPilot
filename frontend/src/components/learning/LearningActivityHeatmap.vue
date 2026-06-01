<script setup lang="ts">
import * as d3 from 'd3'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
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

const cellSize = computed(() => 16)
const gapSize = computed(() => 4)
const labelWidth = computed(() => 32)
const fontSize = computed(() => 11)
const titleSize = computed(() => 12)

function localDayOfWeek(dateKey: string): number {
  const [y, m, d] = dateKey.split('-').map(Number)
  return new Date(y, m - 1, d).getDay()
}

function formatDateLabel(dateKey: string): string {
  const [y, m, d] = dateKey.split('-').map(Number)
  const date = new Date(y, m - 1, d)
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${y}年${m}月${d}日 ${weekdays[date.getDay()]}`
}

function buildTooltipText(d: ActivityDay): string {
  const dateLabel = formatDateLabel(d.date)
  if (d.count === 0) {
    return `${dateLabel}\n暂无学习活动`
  }
  const parts: string[] = [dateLabel]
  parts.push(`学习活动: ${d.count} 次`)
  if (d.visitCount > 0) {
    parts.push(`访问模块: ${d.visitCount} 次`)
  }
  if (d.gameCount > 0) {
    parts.push(`通关关卡: ${d.gameCount} 题`)
  }
  return parts.join('\n')
}

function render() {
  const svgEl = svgRef.value
  if (!svgEl) return
  const token = ++renderToken

  const data = props.days
  const cell = cellSize.value
  const gap = gapSize.value
  const labelW = labelWidth.value
  const weeks = props.weeks
  const cols = weeks
  const rows = 7

  const width = labelW + cols * (cell + gap) + 12
  const height = rows * (cell + gap) + 28

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
  const g = svg.append('g').attr('transform', `translate(${labelW}, 20)`)

  dayLabels.forEach((lbl, i) => {
    if (i % 2 === 0) {
      svg
        .append('text')
        .attr('x', 0)
        .attr('y', 20 + i * (cell + gap) + cell / 2)
        .attr('dy', '0.35em')
        .attr('fill', 'var(--alp-color-muted)')
        .attr('font-size', fontSize.value)
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
      .attr('rx', 3)
      .attr('fill', color(d.count))
      .attr('class', 'heatmap-cell')
      .attr('data-date', d.date)
      .attr('data-count', d.count)
      .attr('data-game', d.gameCount)
      .attr('data-visit', d.visitCount)
      .append('title')
      .text(buildTooltipText(d))
  })

  svg
    .append('text')
    .attr('x', labelW)
    .attr('y', 12)
    .attr('fill', 'var(--alp-color-muted)')
    .attr('font-size', titleSize.value)
    .text(`近 ${weeks} 周学习活跃度`)

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
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
}

.activity-heatmap svg {
  display: block;
}

.heatmap-cell {
  cursor: pointer;
  transition: filter 0.15s ease;
}

.heatmap-cell:hover {
  filter: brightness(1.15);
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.legend-cell {
  width: 14px;
  height: 14px;
  border-radius: 3px;
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