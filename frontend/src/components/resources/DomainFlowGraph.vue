<script setup lang="ts">
import * as d3 from 'd3'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { DomainNarrative, StructureLogic } from '@/utils/domainStructureContent'

const props = defineProps<{
  domain?: DomainNarrative | null
  structure?: StructureLogic | null
}>()

const emit = defineEmits<{
  'step-click': [index: number, label: string]
}>()

interface FlowStep {
  id: string
  label: string
  group: 'domain' | 'structure'
  hint?: string
}

const containerRef = ref<HTMLDivElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)

const steps = computed((): FlowStep[] => {
  const list: FlowStep[] = []
  const d = props.domain
  const s = props.structure

  if (d?.headline) list.push({ id: 'd-head', label: d.headline, group: 'domain', hint: d.mission })
  if (d?.story) {
    const parts = d.story.split(/[。！？\n]/).filter(Boolean).slice(0, 3)
    parts.forEach((p, i) => list.push({ id: `d-${i}`, label: p.slice(0, 28), group: 'domain' }))
  }

  if (s?.algorithm_outline) {
    const lines = s.algorithm_outline.split(/\n|；|;/).filter(Boolean)
    lines.forEach((line, i) => {
      list.push({
        id: `s-${i}`,
        label: line.replace(/^[\d.、\s]+/, '').slice(0, 32),
        group: 'structure',
      })
    })
  } else if (s?.step_hints?.length) {
    s.step_hints.forEach((h, i) => {
      list.push({ id: `h-${i}`, label: h.slice(0, 32), group: 'structure', hint: h })
    })
  } else if (s?.abstract_model) {
    list.push({
      id: 's-model',
      label: '抽象模型',
      group: 'structure',
      hint: s.abstract_model.slice(0, 80),
    })
  }

  return list.slice(0, 10)
})

function renderFlow() {
  const svgEl = svgRef.value
  const container = containerRef.value
  if (!svgEl || !container || !steps.value.length) return

  const width = container.clientWidth
  const height = Math.max(120, 72 + steps.value.length * 8)
  const svg = d3.select(svgEl)
  svg.selectAll('*').remove()
  svg.attr('width', width).attr('height', height).attr('viewBox', `0 0 ${width} ${height}`)

  const padX = 48
  const gap = Math.min(140, (width - padX * 2) / Math.max(steps.value.length - 1, 1))
  const cy = height / 2
  const g = svg.append('g')

  steps.value.forEach((step, i) => {
    const x = padX + i * gap
    const color = step.group === 'domain' ? 'var(--alp-color-accent)' : 'var(--alp-color-primary)'

    if (i > 0) {
      g.append('line')
        .attr('x1', padX + (i - 1) * gap + 20)
        .attr('y1', cy)
        .attr('x2', x - 20)
        .attr('y2', cy)
        .attr('stroke', 'rgba(148,163,184,0.45)')
        .attr('stroke-width', 2)
        .attr('marker-end', 'url(#domain-flow-arrow)')
    }

    const node = g
      .append('g')
      .attr('class', 'flow-node')
      .attr('transform', `translate(${x},${cy})`)
      .style('cursor', 'pointer')
      .on('click', () => emit('step-click', i, step.label))

    node
      .append('circle')
      .attr('r', 18)
      .attr('fill', `color-mix(in srgb, ${color} 25%, #0f172a)`)
      .attr('stroke', color)
      .attr('stroke-width', 2)

    node
      .append('text')
      .attr('y', 34)
      .attr('text-anchor', 'middle')
      .attr('fill', '#cbd5e1')
      .attr('font-size', 10)
      .text(step.label.length > 12 ? step.label.slice(0, 11) + '…' : step.label)
  })

  svg
    .append('defs')
    .append('marker')
    .attr('id', 'domain-flow-arrow')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 8)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', 'rgba(148,163,184,0.6)')
}

watch(steps, () => void nextTick().then(renderFlow), { deep: true })

onMounted(() => {
  void nextTick().then(renderFlow)
  window.addEventListener('resize', renderFlow)
})

onUnmounted(() => {
  window.removeEventListener('resize', renderFlow)
})
</script>

<template>
  <div v-if="steps.length" ref="containerRef" class="domain-flow">
    <div class="domain-flow-head">
      <span class="flow-tag">Domain Flow</span>
      <span class="flow-hint">点击步骤可联动 Trace / 旁白（若已接入）</span>
    </div>
    <svg ref="svgRef" class="domain-flow-svg" role="img" aria-label="业务与算法步骤流图" />
  </div>
</template>

<style scoped>
.domain-flow {
  margin-top: 12px;
  padding: 12px;
  border-radius: 12px;
  border: 1px dashed color-mix(in srgb, var(--alp-color-primary) 35%, var(--alp-color-border));
  background: color-mix(in srgb, #0f172a 6%, var(--alp-bg-soft-block));
  overflow-x: auto;
}

.domain-flow-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.flow-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-accent) 20%, transparent);
  color: #c4b5fd;
}

.flow-hint {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.domain-flow-svg {
  display: block;
  min-width: 100%;
}

.flow-node:hover circle {
  filter: drop-shadow(0 0 6px rgba(74, 126, 148, 0.5));
}
</style>
