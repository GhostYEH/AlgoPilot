<script setup lang="ts">
import * as d3 from 'd3'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    percent: number
    size?: number
    label?: string
    sublabel?: string
  }>(),
  {
    size: 140,
    label: '总进度',
    sublabel: '',
  },
)

const svgRef = ref<SVGSVGElement | null>(null)
let renderToken = 0

function render() {
  const svgEl = svgRef.value
  if (!svgEl) return
  const token = ++renderToken

  const size = props.size
  const stroke = 10
  const radius = (size - stroke) / 2
  const cx = size / 2
  const cy = size / 2

  const svg = d3.select(svgEl)
  svg.selectAll('*').remove()
  svg.attr('width', size).attr('height', size)

  const pct = Math.max(0, Math.min(100, props.percent))

  const arcBg = d3
    .arc<{ endAngle: number }>()
    .innerRadius(radius - stroke / 2)
    .outerRadius(radius + stroke / 2)
    .startAngle(0)
    .cornerRadius(stroke / 2)

  const arcFg = d3
    .arc<{ endAngle: number }>()
    .innerRadius(radius - stroke / 2)
    .outerRadius(radius + stroke / 2)
    .startAngle(0)
    .cornerRadius(stroke / 2)

  const g = svg.append('g').attr('transform', `translate(${cx},${cy})`)

  g.append('path')
    .attr('fill', 'color-mix(in srgb, var(--alp-color-border) 80%, transparent)')
    .attr(
      'd',
      arcBg({ endAngle: Math.PI * 2 }) as string,
    )

  const fg = g
    .append('path')
    .attr('fill', 'var(--alp-color-primary)')
    .attr('d', arcFg({ endAngle: 0 }) as string)

  fg.transition()
    .duration(800)
    .ease(d3.easeCubicOut)
    .attrTween('d', () => {
      const interp = d3.interpolate(0, (pct / 100) * Math.PI * 2)
      return (t) => arcFg({ endAngle: interp(t) }) as string
    })

  if (token !== renderToken) return

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.1em')
    .attr('fill', 'var(--alp-color-text)')
    .attr('font-size', size * 0.22)
    .attr('font-weight', 700)
    .text(`${pct}%`)

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.4em')
    .attr('fill', 'var(--alp-color-muted)')
    .attr('font-size', size * 0.1)
    .text(props.label)

  if (props.sublabel) {
    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '2.6em')
      .attr('fill', 'var(--alp-color-muted)')
      .attr('font-size', size * 0.08)
      .text(props.sublabel)
  }
}

watch(
  () => [props.percent, props.label, props.sublabel, props.size],
  () => void nextTick().then(render),
)

onMounted(() => void nextTick().then(render))

onUnmounted(() => {
  renderToken += 1
  const svgEl = svgRef.value
  if (svgEl) d3.select(svgEl).selectAll('*').interrupt()
})
</script>

<template>
  <div class="progress-ring">
    <svg ref="svgRef" role="img" :aria-label="`${label} ${percent}%`" />
  </div>
</template>

<style scoped>
.progress-ring {
  display: flex;
  justify-content: center;
  align-items: center;
}

.progress-ring svg {
  display: block;
}
</style>
