<script setup lang="ts">
import { computed } from 'vue'
import type { RadarAxis } from '@/utils/homeDashboard'
import type { DaySeriesPoint, HeatmapCell } from '@/utils/homeActivityLog'

const props = defineProps<{
  radar: RadarAxis[]
  series: DaySeriesPoint[]
  heatmap: HeatmapCell[]
}>()

const radarPoints = computed(() => {
  const n = props.radar.length
  const cx = 100
  const cy = 100
  const maxR = 72
  const angle0 = -Math.PI / 2
  return props.radar.map((axis, i) => {
    const angle = angle0 + (i * 2 * Math.PI) / n
    const r = (Math.min(100, Math.max(0, axis.value)) / 100) * maxR
    return {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
      labelX: cx + (maxR + 14) * Math.cos(angle),
      labelY: cy + (maxR + 14) * Math.sin(angle),
      label: axis.label,
      value: axis.value,
    }
  })
})

const radarPolygon = computed(() =>
  radarPoints.value.map((p) => `${p.x},${p.y}`).join(' '),
)

const gridPolygons = computed(() => {
  const levels = [0.25, 0.5, 0.75, 1]
  const n = props.radar.length
  const cx = 100
  const cy = 100
  const maxR = 72
  const angle0 = -Math.PI / 2
  return levels.map((lv) => {
    const pts = Array.from({ length: n }, (_, i) => {
      const angle = angle0 + (i * 2 * Math.PI) / n
      const r = maxR * lv
      return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`
    })
    return pts.join(' ')
  })
})

const lineChart = computed(() => {
  const w = 280
  const h = 88
  const pad = 8
  const max = Math.max(1, ...props.series.map((s) => s.total))
  const step = props.series.length > 1 ? (w - pad * 2) / (props.series.length - 1) : 0
  const points = props.series.map((s, i) => {
    const x = pad + i * step
    const y = h - pad - (s.total / max) * (h - pad * 2)
    return { x, y, ...s }
  })
  const line = points.map((p) => `${p.x},${p.y}`).join(' ')
  const area =
    `${pad},${h - pad} ` +
    line +
    ` ${w - pad},${h - pad}`
  return { w, h, points, line, area, max }
})

const heatmapWeeks = computed(() => {
  const cells = props.heatmap
  const weeks: HeatmapCell[][] = []
  for (let i = 0; i < cells.length; i += 7) {
    weeks.push(cells.slice(i, i + 7))
  }
  return weeks
})
</script>

<template>
  <div class="charts-grid">
    <div class="chart-block">
      <div class="chart-head">
        <span class="chart-title">能力雷达</span>
        <span class="chart-sub">各知识维度章节进度</span>
      </div>
      <svg class="radar-svg" viewBox="0 0 200 200" aria-label="能力雷达图">
        <polygon
          v-for="(poly, idx) in gridPolygons"
          :key="idx"
          :points="poly"
          fill="none"
          stroke="rgba(148, 163, 184, 0.2)"
          stroke-width="1"
        />
        <polygon
          :points="radarPolygon"
          fill="rgba(61, 138, 126, 0.22)"
          stroke="rgba(61, 138, 126, 0.85)"
          stroke-width="2"
        />
        <g v-for="(p, i) in radarPoints" :key="i">
          <circle :cx="p.x" :cy="p.y" r="3" fill="#3d8a7e" />
          <text
            :x="p.labelX"
            :y="p.labelY"
            text-anchor="middle"
            dominant-baseline="middle"
            class="radar-label"
          >
            {{ p.label }}
          </text>
        </g>
      </svg>
      <div class="radar-legend">
        <span v-for="p in radarPoints" :key="p.label" class="radar-legend-item">
          {{ p.label }} <strong>{{ p.value }}%</strong>
        </span>
      </div>
    </div>

    <div class="chart-block">
      <div class="chart-head">
        <span class="chart-title">近 7 日学习</span>
        <span class="chart-sub">访问 + 刷题加权</span>
      </div>
      <svg
        class="line-svg"
        :viewBox="`0 0 ${lineChart.w} ${lineChart.h}`"
        preserveAspectRatio="none"
        aria-label="近7日折线图"
      >
        <defs>
          <linearGradient id="homeLineFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="rgba(61, 138, 126, 0.35)" />
            <stop offset="100%" stop-color="rgba(61, 138, 126, 0)" />
          </linearGradient>
        </defs>
        <polygon :points="lineChart.area" fill="url(#homeLineFill)" />
        <polyline
          :points="lineChart.line"
          fill="none"
          stroke="#3d8a7e"
          stroke-width="2.5"
          stroke-linejoin="round"
        />
        <circle
          v-for="(p, i) in lineChart.points"
          :key="i"
          :cx="p.x"
          :cy="p.y"
          r="3.5"
          fill="#3d8a7e"
          stroke="#e0f2fe"
          stroke-width="1"
        />
      </svg>
      <div class="line-labels">
        <span v-for="s in series" :key="s.date">{{ s.label }}</span>
      </div>
    </div>

    <div class="chart-block heatmap-block">
      <div class="chart-head">
        <span class="chart-title">学习打卡热力</span>
        <span class="chart-sub">近 12 周</span>
      </div>
      <div class="heatmap" role="img" aria-label="学习热力图">
        <div v-for="(week, wi) in heatmapWeeks" :key="wi" class="heatmap-week">
          <span
            v-for="cell in week"
            :key="cell.date"
            class="heatmap-cell"
            :data-level="cell.level"
            :title="cell.date"
          />
        </div>
      </div>
      <div class="heatmap-legend">
        <span>少</span>
        <span class="heatmap-cell" data-level="0" />
        <span class="heatmap-cell" data-level="1" />
        <span class="heatmap-cell" data-level="2" />
        <span class="heatmap-cell" data-level="3" />
        <span class="heatmap-cell" data-level="4" />
        <span>多</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.chart-block {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: rgba(15, 23, 42, 0.35);
}

.heatmap-block {
  grid-column: 1 / -1;
}

.chart-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.chart-sub {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.radar-svg {
  width: 100%;
  max-width: 220px;
  margin: 0 auto;
  display: block;
}

.radar-label {
  font-size: 9px;
  fill: var(--alp-color-muted);
}

.radar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-top: 8px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.radar-legend strong {
  color: var(--alp-color-primary);
  margin-left: 2px;
}

.line-svg {
  width: 100%;
  height: 88px;
  display: block;
}

.line-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 10px;
  color: var(--alp-color-muted);
}

.heatmap {
  display: flex;
  gap: 3px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.heatmap-week {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.heatmap-cell {
  width: 11px;
  height: 11px;
  border-radius: 2px;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(51, 65, 85, 0.6);
}

.heatmap-cell[data-level='1'] {
  background: rgba(var(--alp-color-primary-rgb), 0.25);
}
.heatmap-cell[data-level='2'] {
  background: rgba(var(--alp-color-primary-rgb), 0.45);
}
.heatmap-cell[data-level='3'] {
  background: rgba(var(--alp-color-primary-rgb), 0.65);
}
.heatmap-cell[data-level='4'] {
  background: rgba(var(--alp-color-primary-rgb), 0.9);
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 10px;
  color: var(--alp-color-muted);
}

@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
