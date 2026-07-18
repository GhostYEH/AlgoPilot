<script setup lang="ts">
import { computed } from 'vue'
import type { RadarAxis } from '@/utils/homeDashboard'
import type { DaySeriesPoint, HeatmapCell } from '@/utils/homeActivityLog'

const props = defineProps<{
  radar: RadarAxis[]
  series: DaySeriesPoint[]
  heatmap: HeatmapCell[]
}>()

const hasActivity = computed(() => props.series.some((day) => day.total > 0))
const lineChart = computed(() => {
  const width = 560
  const height = 150
  const xPadding = 18
  const yPadding = 18
  const max = Math.max(1, ...props.series.map((day) => day.total))
  const step = props.series.length > 1
    ? (width - xPadding * 2) / (props.series.length - 1)
    : 0
  const points = props.series.map((day, index) => ({
    ...day,
    x: xPadding + index * step,
    y: height - yPadding - (day.total / max) * (height - yPadding * 2),
  }))
  return {
    width,
    height,
    max,
    points,
    line: points.map((point) => `${point.x},${point.y}`).join(' '),
  }
})

const radarPoints = computed(() => {
  const center = 90
  const radius = 58
  const count = Math.max(1, props.radar.length)
  return props.radar.map((axis, index) => {
    const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count
    const valueRadius = radius * Math.min(100, Math.max(0, axis.value)) / 100
    return {
      ...axis,
      x: center + valueRadius * Math.cos(angle),
      y: center + valueRadius * Math.sin(angle),
      labelX: center + (radius + 18) * Math.cos(angle),
      labelY: center + (radius + 18) * Math.sin(angle),
    }
  })
})
const radarPolygon = computed(() =>
  radarPoints.value.map((point) => `${point.x},${point.y}`).join(' '),
)
const radarGrid = computed(() => {
  const center = 90
  const count = Math.max(1, props.radar.length)
  return [0.5, 1].map((level) =>
    props.radar.map((_, index) => {
      const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count
      return `${center + 58 * level * Math.cos(angle)},${center + 58 * level * Math.sin(angle)}`
    }).join(' '),
  )
})

const heatmapWeeks = computed(() => {
  const weeks: HeatmapCell[][] = []
  for (let index = 0; index < props.heatmap.length; index += 7) {
    weeks.push(props.heatmap.slice(index, index + 7))
  }
  return weeks
})
const activeDays = computed(() => props.heatmap.filter((cell) => cell.level > 0).length)

// 热力图统计：当前连续学习天数、最长连续、本周活跃天数
const heatmapStats = computed(() => {
  const cells = props.heatmap
  if (cells.length === 0) return { currentStreak: 0, maxStreak: 0, weekActive: 0, totalActive: 0 }

  // 从最后一天（今天）往前数连续活跃天数
  let currentStreak = 0
  for (let i = cells.length - 1; i >= 0; i--) {
    if (cells[i].level > 0) currentStreak++
    else break
  }

  // 最长连续活跃天数
  let maxStreak = 0
  let run = 0
  for (const cell of cells) {
    if (cell.level > 0) {
      run++
      if (run > maxStreak) maxStreak = run
    } else {
      run = 0
    }
  }

  // 本周活跃天数（最后 7 天）
  const lastWeek = cells.slice(-7)
  const weekActive = lastWeek.filter((cell) => cell.level > 0).length

  return {
    currentStreak,
    maxStreak,
    weekActive,
    totalActive: activeDays.value,
  }
})

function heatmapLabel(cell: HeatmapCell) {
  const date = new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
  }).format(new Date(`${cell.date}T00:00:00`))
  return `${date}，学习强度 ${cell.level}/4`
}
</script>

<template>
  <div class="learning-charts">
    <section class="learning-charts__trend">
      <header>
        <div>
          <h3>近 7 天学习活跃度</h3>
          <p>访问记 1 分，完成题目记 2 分</p>
        </div>
        <strong v-if="hasActivity">{{ series.reduce((sum, day) => sum + day.total, 0) }} 分</strong>
      </header>

      <div v-if="hasActivity" class="trend-chart">
        <div class="trend-chart__axis">
          <span>{{ lineChart.max }}</span>
          <span>0</span>
        </div>
        <svg
          :viewBox="`0 0 ${lineChart.width} ${lineChart.height}`"
          preserveAspectRatio="none"
          aria-label="近 7 天学习活跃度折线图"
        >
          <line
            x1="18"
            :x2="lineChart.width - 18"
            :y1="lineChart.height - 18"
            :y2="lineChart.height - 18"
            class="trend-chart__base"
          />
          <polyline :points="lineChart.line" class="trend-chart__line" />
          <circle
            v-for="point in lineChart.points"
            :key="point.date"
            :cx="point.x"
            :cy="point.y"
            r="3.5"
            class="trend-chart__point"
          />
        </svg>
        <div class="trend-chart__labels">
          <span v-for="day in series" :key="day.date">{{ day.label }}</span>
        </div>
      </div>
      <div v-else class="learning-charts__empty">
        还没有近 7 天学习记录，完成一次学习或练习后这里会显示趋势。
      </div>
    </section>

    <section class="learning-charts__radar">
      <header>
        <div>
          <h3>能力变化</h3>
          <p>按已有章节完成度汇总</p>
        </div>
      </header>
      <svg viewBox="0 0 180 180" aria-label="能力维度雷达图">
        <polygon
          v-for="(polygon, index) in radarGrid"
          :key="index"
          :points="polygon"
          class="radar-grid"
        />
        <polygon :points="radarPolygon" class="radar-value" />
        <g v-for="point in radarPoints" :key="point.key">
          <circle :cx="point.x" :cy="point.y" r="2.5" class="radar-point" />
          <text
            :x="point.labelX"
            :y="point.labelY"
            text-anchor="middle"
            dominant-baseline="middle"
          >
            {{ point.label }}
          </text>
        </g>
      </svg>
    </section>

    <section class="learning-charts__heatmap">
      <header>
        <div>
          <h3>近 12 周学习记录</h3>
          <p>{{ activeDays ? `${activeDays} 个活跃日，颜色越深表示当天学习更集中。` : '还没有可显示的学习记录。' }}</p>
        </div>
      </header>
      <div class="heatmap-row">
        <div class="heatmap" aria-label="近 12 周学习热力图">
          <div v-for="(week, index) in heatmapWeeks" :key="index">
            <span
              v-for="cell in week"
              :key="cell.date"
              :data-level="cell.level"
              :title="heatmapLabel(cell)"
            />
          </div>
        </div>
        <div class="heatmap-stats">
          <div class="heatmap-stats__item">
            <strong>{{ heatmapStats.currentStreak }}</strong>
            <span>连续学习</span>
          </div>
          <div class="heatmap-stats__item">
            <strong>{{ heatmapStats.maxStreak }}</strong>
            <span>最长连续</span>
          </div>
          <div class="heatmap-stats__item">
            <strong>{{ heatmapStats.weekActive }}<small>/7</small></strong>
            <span>本周活跃</span>
          </div>
          <div class="heatmap-stats__item">
            <strong>{{ heatmapStats.totalActive }}</strong>
            <span>总活跃日</span>
          </div>
        </div>
        <div class="heatmap-legend">
          <span>少</span>
          <i v-for="level in [0, 1, 2, 3, 4]" :key="level" :data-level="level" />
          <span>多</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.learning-charts {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(240px, 0.7fr);
  border-top: 1px solid var(--color-border);
}

.learning-charts section {
  min-width: 0;
}

.learning-charts__trend {
  padding: 18px 24px 4px 0;
  border-right: 1px solid var(--color-border);
}

.learning-charts__radar {
  padding: 18px 0 4px 24px;
}

.learning-charts__heatmap {
  grid-column: 1 / -1;
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid var(--color-border);
}

.learning-charts header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.learning-charts h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 13px;
}

.learning-charts header p {
  margin: 3px 0 0;
  color: var(--color-text-muted);
  font-size: 10px;
}

.learning-charts header > strong {
  color: var(--color-text-primary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.trend-chart {
  position: relative;
  margin-top: 15px;
  padding-left: 26px;
}

.trend-chart svg {
  display: block;
  width: 100%;
  height: 150px;
}

.trend-chart__base {
  stroke: var(--color-border);
  stroke-width: 1;
}

.trend-chart__line {
  fill: none;
  stroke: var(--color-brand);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}

.trend-chart__point {
  fill: var(--color-bg-surface);
  stroke: var(--color-brand);
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}

.trend-chart__axis {
  position: absolute;
  inset: 0 auto 18px 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: var(--color-text-muted);
  font-size: 9px;
}

.trend-chart__labels {
  display: flex;
  justify-content: space-between;
  padding-left: 4px;
  color: var(--color-text-muted);
  font-size: 9px;
}

.learning-charts__empty {
  display: flex;
  min-height: 176px;
  align-items: center;
  justify-content: center;
  margin-top: 12px;
  padding: 20px;
  color: var(--color-text-muted);
  font-size: 11px;
  line-height: 1.7;
  text-align: center;
  border-block: 1px solid var(--color-border);
}

.learning-charts__radar svg {
  display: block;
  width: min(100%, 210px);
  margin: 8px auto 0;
}

.radar-grid {
  fill: none;
  stroke: var(--color-border);
  stroke-width: 1;
}

.radar-value {
  fill: color-mix(in srgb, var(--color-brand) 14%, transparent);
  stroke: var(--color-brand);
  stroke-width: 1.5;
}

.radar-point {
  fill: var(--color-brand);
}

.learning-charts__radar text {
  fill: var(--color-text-muted);
  font-size: 8px;
}

.heatmap-row {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 18px;
  margin-top: 13px;
}

.heatmap {
  display: flex;
  gap: 4px;
}

.heatmap-stats {
  display: flex;
  gap: 20px;
  margin-left: auto;
  padding-bottom: 2px;
}

.heatmap-stats__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.heatmap-stats__item strong {
  color: var(--color-text-primary);
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.heatmap-stats__item strong small {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 500;
}

.heatmap-stats__item span {
  color: var(--color-text-muted);
  font-size: 10px;
  white-space: nowrap;
}

.heatmap > div {
  display: grid;
  gap: 4px;
}

.heatmap span,
.heatmap-legend i {
  width: 11px;
  height: 11px;
  border: 1px solid var(--color-border);
  border-radius: 2px;
  background: var(--color-bg-subtle);
}

.heatmap [data-level='1'],
.heatmap-legend [data-level='1'] {
  background: color-mix(in srgb, var(--color-brand) 22%, var(--color-bg-surface));
}

.heatmap [data-level='2'],
.heatmap-legend [data-level='2'] {
  background: color-mix(in srgb, var(--color-brand) 42%, var(--color-bg-surface));
}

.heatmap [data-level='3'],
.heatmap-legend [data-level='3'] {
  background: color-mix(in srgb, var(--color-brand) 66%, var(--color-bg-surface));
}

.heatmap [data-level='4'],
.heatmap-legend [data-level='4'] {
  background: var(--color-brand);
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-muted);
  font-size: 9px;
  white-space: nowrap;
}

.heatmap-legend i {
  display: block;
}

@media (max-width: 820px) {
  .learning-charts {
    grid-template-columns: 1fr;
  }

  .learning-charts__trend {
    padding-right: 0;
    border-right: 0;
  }

  .learning-charts__radar {
    margin-top: 20px;
    padding: 18px 0 0;
    border-top: 1px solid var(--color-border);
  }

  .learning-charts__heatmap {
    grid-column: auto;
  }
}

@media (max-width: 520px) {
  .trend-chart {
    padding-left: 20px;
  }

  .trend-chart svg {
    height: 126px;
  }

  .heatmap-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .heatmap-stats {
    margin-left: 0;
    gap: 16px;
  }

  .heatmap {
    max-width: 100%;
    gap: 3px;
  }

  .heatmap > div {
    gap: 3px;
  }

  .heatmap span {
    width: 10px;
    height: 10px;
  }
}
</style>
