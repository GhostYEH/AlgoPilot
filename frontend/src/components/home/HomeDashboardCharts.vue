<script setup lang="ts">
import { computed, ref } from 'vue'
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

const selectedHeatmapDate = ref<string | null>(null)

const heatmapSummary = computed(() => {
  const cells = props.heatmap
  const activeDays = cells.filter((cell) => cell.level > 0).length
  let currentStreak = 0
  let longestStreak = 0
  let runningStreak = 0

  for (const cell of cells) {
    if (cell.level > 0) {
      runningStreak += 1
      longestStreak = Math.max(longestStreak, runningStreak)
    } else {
      runningStreak = 0
    }
  }

  for (let index = cells.length - 1; index >= 0; index -= 1) {
    if (cells[index]?.level === 0) break
    currentStreak += 1
  }

  return {
    activeDays,
    currentStreak,
    longestStreak,
    activeRate: cells.length ? Math.round((activeDays / cells.length) * 100) : 0,
  }
})

const focusedHeatmapCell = computed(() => {
  if (selectedHeatmapDate.value) {
    const selected = props.heatmap.find((cell) => cell.date === selectedHeatmapDate.value)
    if (selected) return selected
  }

  return [...props.heatmap].reverse().find((cell) => cell.level > 0)
    ?? props.heatmap.at(-1)
    ?? null
})

const heatLevelLabels = ['未打卡', '轻量学习', '稳定学习', '高效学习', '深度学习'] as const

function formatHeatmapDate(date: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  }).format(new Date(`${date}T00:00:00`))
}

function heatmapCellLabel(cell: HeatmapCell) {
  return `${formatHeatmapDate(cell.date)}，${heatLevelLabels[cell.level]}`
}
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
        <div>
          <span class="chart-title">学习打卡热力</span>
          <span class="heatmap-caption">颜色越深，表示当天投入越充分</span>
        </div>
        <span class="chart-sub">近 12 周 · {{ heatmapSummary.activeRate }}% 打卡率</span>
      </div>

      <div class="heatmap-overview" aria-label="学习打卡概览">
        <span><strong>{{ heatmapSummary.currentStreak }}</strong> 连续天</span>
        <span><strong>{{ heatmapSummary.activeDays }}</strong> 活跃日</span>
        <span><strong>{{ heatmapSummary.longestStreak }}</strong> 最长连续</span>
      </div>

      <div class="heatmap-content">
        <div class="heatmap-visual">
          <div class="heatmap" role="group" aria-label="近 12 周学习热力图">
            <div v-for="(week, wi) in heatmapWeeks" :key="wi" class="heatmap-week">
              <button
                v-for="cell in week"
                :key="cell.date"
                type="button"
                class="heatmap-cell"
                :class="{ selected: focusedHeatmapCell?.date === cell.date }"
                :data-level="cell.level"
                :title="heatmapCellLabel(cell)"
                :aria-label="heatmapCellLabel(cell)"
                :aria-pressed="focusedHeatmapCell?.date === cell.date"
                @click="selectedHeatmapDate = cell.date"
              />
            </div>
          </div>
          <div class="heatmap-legend" aria-label="热力强度图例">
            <span>少</span>
            <span class="heatmap-cell" data-level="0" />
            <span class="heatmap-cell" data-level="1" />
            <span class="heatmap-cell" data-level="2" />
            <span class="heatmap-cell" data-level="3" />
            <span class="heatmap-cell" data-level="4" />
            <span>多</span>
          </div>
        </div>

        <div v-if="focusedHeatmapCell" class="heatmap-detail" aria-live="polite">
          <span>{{ formatHeatmapDate(focusedHeatmapCell.date) }}</span>
          <strong>{{ heatLevelLabels[focusedHeatmapCell.level] }}</strong>
          <small>
            {{ focusedHeatmapCell.level > 0 ? `学习强度 ${focusedHeatmapCell.level}/4，继续保持这个节奏。` : '当天还没有学习记录，完成一次访问或刷题即可点亮。' }}
          </small>
        </div>
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

.chart-head > div {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
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
  gap: 4px;
  overflow-x: auto;
  padding: 3px 3px 6px;
}

.heatmap-week {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.heatmap-cell {
  flex: 0 0 auto;
  width: 14px;
  height: 14px;
  padding: 0;
  border: 1px solid var(--alp-color-border);
  border-radius: 3px;
  background: var(--alp-bg-soft-block);
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

.heatmap-caption {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.heatmap-overview {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin: 2px 0 14px;
  color: var(--alp-color-muted);
  font-size: 11px;
}

.heatmap-overview > span {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
}

.heatmap-overview strong {
  color: var(--alp-color-text);
  font-size: 17px;
  line-height: 1;
}

.heatmap-content {
  display: grid;
  grid-template-columns: minmax(245px, auto) minmax(180px, 1fr);
  align-items: center;
  gap: 24px;
}

.heatmap-visual {
  min-width: 0;
}

button.heatmap-cell {
  appearance: none;
  cursor: pointer;
  transition: transform 150ms cubic-bezier(0.22, 1, 0.36, 1), border-color 150ms ease;
}

button.heatmap-cell:hover {
  z-index: 1;
  border-color: var(--alp-color-primary);
  transform: scale(1.28);
}

button.heatmap-cell.selected {
  border-color: var(--alp-color-text);
  box-shadow: 0 0 0 2px var(--alp-bg-surface-solid), 0 0 0 3px var(--alp-color-primary);
}

.heatmap-detail {
  display: grid;
  gap: 3px;
  min-width: 0;
  padding-left: 20px;
  border-left: 1px solid var(--alp-color-border);
}

.heatmap-detail > span {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.heatmap-detail > strong {
  color: var(--alp-color-primary);
  font-size: 15px;
}

.heatmap-detail > small {
  max-width: 38ch;
  color: var(--alp-color-text-secondary);
  font-size: 11px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .chart-head,
  .chart-head > div {
    align-items: flex-start;
    flex-direction: column;
  }

  .chart-head > div {
    gap: 2px;
  }

  .heatmap-content {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .heatmap-detail {
    padding: 12px 0 0;
    border-top: 1px solid var(--alp-color-border);
    border-left: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  button.heatmap-cell {
    transition: none;
  }

  button.heatmap-cell:hover {
    transform: none;
  }
}
</style>
