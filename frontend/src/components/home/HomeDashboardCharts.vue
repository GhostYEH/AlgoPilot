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
const totalScore = computed(() => props.series.reduce((sum, day) => sum + day.total, 0))
const activeWeekDays = computed(() => props.series.filter((day) => day.total > 0).length)
const visitTotal = computed(() => props.series.reduce((sum, day) => sum + day.visits, 0))
const solveTotal = computed(() => props.series.reduce((sum, day) => sum + day.solves, 0))
const averageScore = computed(() =>
  activeWeekDays.value ? Math.round(totalScore.value / activeWeekDays.value) : 0,
)

const bestDay = computed(() => {
  if (!hasActivity.value) return null
  return props.series.reduce((best, day) => (day.total > best.total ? day : best), props.series[0])
})

const breakdown = computed(() => {
  const max = Math.max(1, visitTotal.value + solveTotal.value * 2)
  return {
    visits: Math.round((visitTotal.value / max) * 100),
    solves: Math.round(((solveTotal.value * 2) / max) * 100),
  }
})

const lineChart = computed(() => {
  const width = 760
  const height = 238
  const left = 34
  const right = 16
  const top = 20
  const base = height - 32
  const values = props.series.map((day) => day.total)
  const rawMax = Math.max(0, ...values)
  const max = Math.max(4, Math.ceil(rawMax / 4) * 4)
  const step = props.series.length > 1 ? (width - left - right) / (props.series.length - 1) : 0
  const bestIndex = rawMax > 0 ? values.indexOf(rawMax) : -1
  const y = (value: number) => base - (value / max) * (base - top)
  const points = props.series.map((day, index) => ({
    ...day,
    x: left + index * step,
    y: y(day.total),
    isBest: index === bestIndex,
  }))

  return {
    width,
    height,
    base,
    max,
    points,
    guides: [max, Math.round(max / 2), 0].map((value) => ({ value, y: y(value) })),
    line: points.map((point) => `${point.x},${point.y}`).join(' '),
  }
})

const radarPoints = computed(() => {
  const center = 112
  const radius = 72
  const count = Math.max(1, props.radar.length)
  return props.radar.map((axis, index) => {
    const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count
    const valueRadius = radius * Math.min(100, Math.max(0, axis.value)) / 100
    return {
      ...axis,
      x: center + valueRadius * Math.cos(angle),
      y: center + valueRadius * Math.sin(angle),
      axisX: center + radius * Math.cos(angle),
      axisY: center + radius * Math.sin(angle),
      labelX: center + (radius + 22) * Math.cos(angle),
      labelY: center + (radius + 22) * Math.sin(angle),
    }
  })
})

const radarPolygon = computed(() =>
  radarPoints.value.map((point) => `${point.x},${point.y}`).join(' '),
)

const radarGrid = computed(() => {
  const center = 112
  const radius = 72
  const count = Math.max(1, props.radar.length)
  return [0.25, 0.5, 0.75, 1].map((level) =>
    props.radar.map((_, index) => {
      const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count
      return `${center + radius * level * Math.cos(angle)},${center + radius * level * Math.sin(angle)}`
    }).join(' '),
  )
})

const radarMean = computed(() => {
  if (!props.radar.length) return 0
  return Math.round(props.radar.reduce((sum, axis) => sum + axis.value, 0) / props.radar.length)
})

const strongestSkill = computed(() =>
  [...props.radar].sort((a, b) => b.value - a.value)[0] ?? null,
)
const weakestSkill = computed(() =>
  [...props.radar].filter((axis) => axis.value > 0).sort((a, b) => a.value - b.value)[0] ?? null,
)

const heatmapWeeks = computed(() => {
  const weeks: HeatmapCell[][] = []
  for (let index = 0; index < props.heatmap.length; index += 7) {
    weeks.push(props.heatmap.slice(index, index + 7))
  }
  return weeks
})
const activeDays = computed(() => props.heatmap.filter((cell) => cell.level > 0).length)

const heatmapStats = computed(() => {
  const cells = props.heatmap
  if (cells.length === 0) {
    return { currentStreak: 0, maxStreak: 0, weekActive: 0, totalActive: 0 }
  }

  let currentStreak = 0
  for (let index = cells.length - 1; index >= 0; index--) {
    if (cells[index].level > 0) currentStreak++
    else break
  }

  let maxStreak = 0
  let run = 0
  for (const cell of cells) {
    if (cell.level > 0) {
      run++
      maxStreak = Math.max(maxStreak, run)
    } else {
      run = 0
    }
  }

  return {
    currentStreak,
    maxStreak,
    weekActive: cells.slice(-7).filter((cell) => cell.level > 0).length,
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
    <div class="learning-charts__summary" aria-label="最近学习摘要">
      <div class="summary-metric">
        <span>学习积分</span>
        <strong>{{ totalScore }}</strong>
        <small>近 7 天累计</small>
      </div>
      <div class="summary-metric">
        <span>活跃天数</span>
        <strong>{{ activeWeekDays }}<small>/7</small></strong>
        <small>有学习记录的天数</small>
      </div>
      <div class="summary-metric">
        <span>日均投入</span>
        <strong>{{ averageScore }}</strong>
        <small>按活跃日计算</small>
      </div>
      <div class="summary-metric summary-metric--accent">
        <span>本周峰值</span>
        <strong>{{ bestDay?.total ?? 0 }}</strong>
        <small>{{ bestDay ? `${bestDay.label} · ${bestDay.solves} 道题` : '等待第一次学习' }}</small>
      </div>
    </div>

    <section class="learning-charts__trend">
      <header class="chart-header">
        <div>
          <span class="chart-kicker">学习节奏</span>
          <h3>把每一天的投入连起来</h3>
          <p>访问记 1 分，完成题目记 2 分 · 实心点代表当天有刷题</p>
        </div>
        <div class="chart-total">
          <strong>{{ totalScore }}</strong>
          <span>近 7 天积分</span>
        </div>
      </header>

      <div v-if="hasActivity" class="trend-layout">
        <div class="trend-chart">
          <svg
            :viewBox="`0 0 ${lineChart.width} ${lineChart.height}`"
            preserveAspectRatio="none"
            role="img"
            aria-label="近 7 天学习积分折线图"
          >
            <g v-for="guide in lineChart.guides" :key="guide.value">
              <line
                :x1="26"
                :x2="lineChart.width - 10"
                :y1="guide.y"
                :y2="guide.y"
                class="trend-chart__guide"
              />
              <text x="0" :y="guide.y + 3" class="trend-chart__scale">{{ guide.value }}</text>
            </g>
            <line
              v-for="point in lineChart.points"
              :key="`${point.date}-floor`"
              :x1="point.x"
              :x2="point.x"
              :y1="lineChart.base"
              :y2="lineChart.base - 8"
              class="trend-chart__floor"
            />
            <polyline :points="lineChart.line" class="trend-chart__line" />
            <g v-for="point in lineChart.points" :key="point.date">
              <circle
                :cx="point.x"
                :cy="point.y"
                :r="point.isBest ? 5.5 : 4"
                :class="['trend-chart__point', { 'is-solved': point.solves > 0, 'is-best': point.isBest }]"
              >
                <title>{{ point.label }}：{{ point.total }} 分，访问 {{ point.visits }} 次，完成 {{ point.solves }} 题</title>
              </circle>
              <text
                v-if="point.isBest"
                :x="point.x"
                :y="point.y - 14"
                class="trend-chart__value"
              >{{ point.total }}</text>
            </g>
          </svg>
          <div class="trend-chart__labels">
            <span v-for="day in series" :key="day.date">{{ day.label }}</span>
          </div>
          <div class="trend-legend" aria-label="折线图图例">
            <span><i class="trend-legend__dot is-filled" />刷题日</span>
            <span><i class="trend-legend__dot" />仅访问</span>
          </div>
        </div>

        <aside class="trend-insight">
          <span class="trend-insight__label">本周峰值</span>
          <strong>{{ bestDay?.label }} · {{ bestDay?.total }} 分</strong>
          <p>
            {{ bestDay?.solves ? `完成了 ${bestDay.solves} 道题，是这一周最有产出的学习日。` : '这一天保持了稳定访问，可以再加一道练习题。' }}
          </p>
          <div class="trend-breakdown">
            <div>
              <span>访问</span>
              <strong>{{ visitTotal }}</strong>
            </div>
            <div class="trend-breakdown__track"><i :style="{ width: `${breakdown.visits}%` }" /></div>
            <div>
              <span>刷题</span>
              <strong>{{ solveTotal }}</strong>
            </div>
            <div class="trend-breakdown__track is-solved"><i :style="{ width: `${breakdown.solves}%` }" /></div>
          </div>
        </aside>
      </div>
      <div v-else class="learning-charts__empty">
        <strong>你的学习节奏还在等第一笔记录</strong>
        <span>完成一次学习或练习后，这里会把每天的投入连成趋势。</span>
      </div>
    </section>

    <section class="learning-charts__radar">
      <header class="chart-header chart-header--compact">
        <div>
          <span class="chart-kicker">能力轮廓</span>
          <h3>优势与下一步</h3>
          <p>按已有章节完成度汇总</p>
        </div>
        <strong class="radar-score">{{ radarMean }}<small>%</small></strong>
      </header>
      <svg viewBox="0 0 224 224" role="img" aria-label="能力维度雷达图">
        <polygon
          v-for="(polygon, index) in radarGrid"
          :key="index"
          :points="polygon"
          class="radar-grid"
        />
        <line
          v-for="point in radarPoints"
          :key="`${point.key}-axis`"
          x1="112"
          y1="112"
          :x2="point.axisX"
          :y2="point.axisY"
          class="radar-axis"
        />
        <polygon :points="radarPolygon" class="radar-value" />
        <g v-for="point in radarPoints" :key="point.key">
          <circle :cx="point.x" :cy="point.y" r="3.5" class="radar-point" />
          <text
            :x="point.labelX"
            :y="point.labelY"
            text-anchor="middle"
            dominant-baseline="middle"
          >{{ point.label }}</text>
        </g>
      </svg>
      <div v-if="strongestSkill?.value" class="radar-insight">
        <div>
          <span>当前优势</span>
          <strong>{{ strongestSkill.label }} {{ strongestSkill.value }}%</strong>
        </div>
        <div>
          <span>建议补强</span>
          <strong>{{ weakestSkill?.label ?? '继续探索' }}<small>{{ weakestSkill ? ` ${weakestSkill.value}%` : '' }}</small></strong>
        </div>
      </div>
      <div v-else class="radar-empty">完成章节后，能力轮廓会逐步成形。</div>
    </section>

    <section class="learning-charts__heatmap">
      <header class="chart-header">
        <div>
          <span class="chart-kicker">学习连续性</span>
          <h3>让节奏留下痕迹</h3>
          <p>{{ activeDays ? `${activeDays} 个活跃日 · 颜色越深表示当天学习更集中` : '近 12 周还没有可显示的学习记录' }}</p>
        </div>
        <strong class="heatmap-period">近 12 周</strong>
      </header>

      <div class="heatmap-layout">
        <div class="heatmap-calendar">
          <div class="heatmap-grid">
            <div class="heatmap-weekdays" aria-hidden="true">
              <span>一</span><span /><span>三</span><span /><span>五</span><span /><span>日</span>
            </div>
            <div class="heatmap" aria-label="近 12 周每日学习热力图">
              <div v-for="(week, index) in heatmapWeeks" :key="index">
                <span
                  v-for="cell in week"
                  :key="cell.date"
                  :data-level="cell.level"
                  :title="heatmapLabel(cell)"
                />
              </div>
            </div>
          </div>
          <div class="heatmap-legend">
            <span>少</span>
            <i v-for="level in [0, 1, 2, 3, 4]" :key="level" :data-level="level" />
            <span>多</span>
          </div>
        </div>

        <div class="heatmap-stats">
          <div class="heatmap-stats__item heatmap-stats__item--primary">
            <strong>{{ heatmapStats.currentStreak }}</strong>
            <span>当前连续</span>
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
      </div>
    </section>
  </div>
</template>

<style scoped>
.learning-charts {
  display: grid;
  grid-template-columns: minmax(0, 1.75fr) minmax(280px, 0.85fr);
  color: var(--color-text-primary);
  border-top: 1px solid var(--color-border);
}

.learning-charts section,
.learning-charts__summary {
  min-width: 0;
}

.learning-charts__summary {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-bottom: 1px solid var(--color-border);
}

.summary-metric {
  display: grid;
  gap: 4px;
  min-height: 92px;
  padding: 17px 20px 15px;
  border-right: 1px solid var(--color-border);
}

.summary-metric:last-child {
  border-right: 0;
}

.summary-metric > span,
.summary-metric > small {
  color: var(--color-text-muted);
  font-size: 10px;
}

.summary-metric > strong {
  color: var(--color-text-primary);
  font-size: 23px;
  font-weight: 760;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.summary-metric > strong small {
  margin-left: 2px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 600;
}

.summary-metric--accent > strong {
  color: var(--color-brand);
}

.learning-charts__trend {
  padding: 21px 22px 20px 0;
  border-right: 1px solid var(--color-border);
}

.learning-charts__radar {
  padding: 21px 0 20px 22px;
}

.learning-charts__heatmap {
  grid-column: 1 / -1;
  padding: 21px 0 2px;
  border-top: 1px solid var(--color-border);
}

.chart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.chart-header--compact {
  gap: 8px;
}

.chart-kicker {
  display: block;
  margin-bottom: 5px;
  color: var(--color-brand);
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.learning-charts h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 750;
  line-height: 1.35;
  letter-spacing: -0.015em;
}

.learning-charts header p {
  margin: 4px 0 0;
  color: var(--color-text-muted);
  font-size: 10px;
  line-height: 1.55;
}

.chart-total {
  display: grid;
  justify-items: end;
  gap: 3px;
  padding-top: 3px;
}

.chart-total strong,
.radar-score {
  color: var(--color-text-primary);
  font-size: 19px;
  font-weight: 780;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.chart-total span,
.heatmap-period {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 550;
  white-space: nowrap;
}

.trend-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 148px;
  gap: 18px;
  margin-top: 15px;
}

.trend-chart {
  min-width: 0;
}

.trend-chart svg {
  display: block;
  width: 100%;
  height: 190px;
  overflow: visible;
}

.trend-chart__guide {
  stroke: var(--color-border);
  stroke-width: 1;
  stroke-dasharray: 2 4;
  vector-effect: non-scaling-stroke;
}

.trend-chart__scale {
  fill: var(--color-text-muted);
  font-size: 10px;
  font-weight: 600;
  text-anchor: start;
}

.trend-chart__floor {
  stroke: color-mix(in srgb, var(--color-brand) 30%, var(--color-border));
  stroke-width: 2;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
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

.trend-chart__point.is-solved {
  fill: var(--color-brand);
}

.trend-chart__point.is-best {
  stroke-width: 2.5;
}

.trend-chart__value {
  fill: var(--color-brand-dark);
  font-size: 11px;
  font-weight: 800;
  text-anchor: middle;
  paint-order: stroke;
  stroke: var(--color-bg-surface);
  stroke-width: 4px;
  stroke-linejoin: round;
}

.trend-chart__labels {
  display: flex;
  justify-content: space-between;
  padding: 5px 2px 0 25px;
  color: var(--color-text-muted);
  font-size: 9px;
  font-variant-numeric: tabular-nums;
}

.trend-legend {
  display: flex;
  gap: 14px;
  margin: 10px 0 0 25px;
  color: var(--color-text-muted);
  font-size: 9px;
}

.trend-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.trend-legend__dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border: 1.5px solid var(--color-brand);
  border-radius: 50%;
  background: var(--color-bg-surface);
}

.trend-legend__dot.is-filled {
  background: var(--color-brand);
}

.trend-insight {
  align-self: stretch;
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  padding: 15px 0 13px 16px;
  border-left: 1px solid var(--color-border);
}

.trend-insight__label {
  color: var(--color-brand);
  font-size: 10px;
  font-weight: 750;
}

.trend-insight > strong {
  margin-top: 6px;
  color: var(--color-text-primary);
  font-size: 15px;
  font-weight: 750;
  line-height: 1.35;
  font-variant-numeric: tabular-nums;
}

.trend-insight > p {
  margin: 7px 0 17px;
  color: var(--color-text-secondary);
  font-size: 10px;
  line-height: 1.65;
}

.trend-breakdown {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 6px 10px;
  color: var(--color-text-muted);
  font-size: 10px;
}

.trend-breakdown div:not(.trend-breakdown__track) {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  grid-column: 1 / -1;
}

.trend-breakdown strong {
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}

.trend-breakdown__track {
  grid-column: 1 / -1;
  height: 4px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--color-bg-subtle);
}

.trend-breakdown__track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-brand);
}

.trend-breakdown__track.is-solved i {
  background: var(--color-success);
}

.learning-charts__empty {
  display: flex;
  min-height: 190px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 15px;
  padding: 20px;
  color: var(--color-text-muted);
  font-size: 11px;
  line-height: 1.7;
  text-align: center;
  border: 1px dashed var(--color-border-strong);
  border-radius: 10px;
  background: var(--color-bg-subtle);
}

.learning-charts__empty strong {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.learning-charts__radar svg {
  display: block;
  width: min(100%, 238px);
  margin: 13px auto 3px;
  overflow: visible;
}

.radar-grid {
  fill: none;
  stroke: var(--color-border);
  stroke-width: 1;
}

.radar-axis {
  stroke: var(--color-border);
  stroke-width: 0.8;
  stroke-dasharray: 2 3;
}

.radar-value {
  fill: color-mix(in srgb, var(--color-brand) 15%, transparent);
  stroke: var(--color-brand);
  stroke-width: 1.8;
}

.radar-point {
  fill: var(--color-brand);
  stroke: var(--color-bg-surface);
  stroke-width: 1.5;
}

.learning-charts__radar text {
  fill: var(--color-text-muted);
  font-size: 9px;
  font-weight: 600;
}

.radar-score {
  color: var(--color-brand);
}

.radar-score small {
  margin-left: 2px;
  color: var(--color-text-muted);
  font-size: 11px;
}

.radar-insight {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 5px;
  padding-top: 13px;
  border-top: 1px solid var(--color-border);
}

.radar-insight > div {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.radar-insight span,
.radar-insight strong,
.radar-empty {
  font-size: 10px;
}

.radar-insight span {
  color: var(--color-text-muted);
}

.radar-insight strong {
  overflow: hidden;
  color: var(--color-text-primary);
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.radar-insight small {
  color: var(--color-text-muted);
  font-weight: 600;
}

.radar-empty {
  margin-top: 13px;
  padding-top: 13px;
  color: var(--color-text-muted);
  border-top: 1px solid var(--color-border);
}

.heatmap-layout {
  display: flex;
  align-items: flex-end;
  gap: 28px;
  margin-top: 16px;
  padding-bottom: 17px;
}

.heatmap-calendar {
  min-width: 0;
}

.heatmap-grid {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr);
  gap: 8px;
}

.heatmap-weekdays {
  display: grid;
  grid-template-rows: repeat(7, 11px);
  gap: 4px;
  color: var(--color-text-muted);
  font-size: 8px;
  line-height: 11px;
  text-align: center;
}

.heatmap {
  display: flex;
  min-width: 0;
  justify-content: space-between;
  gap: clamp(3px, 0.55vw, 7px);
}

.heatmap > div {
  display: grid;
  flex: 1 1 0;
  grid-template-rows: repeat(7, 11px);
  gap: 4px;
  min-width: 0;
}

.heatmap span,
.heatmap-legend i {
  display: block;
  width: 100%;
  min-width: 6px;
  max-width: 13px;
  height: 11px;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  background: var(--color-bg-subtle);
  transition: transform 150ms ease, border-color 150ms ease;
}

.heatmap span:hover {
  border-color: var(--color-brand);
  transform: scale(1.2);
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
  margin: 11px 0 0 24px;
  color: var(--color-text-muted);
  font-size: 9px;
}

.heatmap-legend i {
  width: 11px;
  min-width: 11px;
}

.heatmap-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(70px, 1fr));
  flex: 0 0 min(47%, 430px);
  gap: 10px;
  padding: 0 4px 0 18px;
  border-left: 1px solid var(--color-border);
}

.heatmap-stats__item {
  display: grid;
  align-content: end;
  gap: 4px;
  min-width: 0;
}

.heatmap-stats__item strong {
  color: var(--color-text-primary);
  font-size: 20px;
  font-weight: 760;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.heatmap-stats__item--primary strong {
  color: var(--color-brand);
}

.heatmap-stats__item strong small {
  margin-left: 2px;
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
}

.heatmap-stats__item span {
  color: var(--color-text-muted);
  font-size: 10px;
  white-space: nowrap;
}

@media (max-width: 920px) {
  .learning-charts {
    grid-template-columns: 1fr;
  }

  .learning-charts__trend {
    padding-right: 0;
    border-right: 0;
  }

  .learning-charts__radar {
    margin-top: 2px;
    padding: 20px 0 0;
    border-top: 1px solid var(--color-border);
  }

  .learning-charts__heatmap {
    grid-column: auto;
  }
}

@media (max-width: 660px) {
  .learning-charts__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-metric:nth-child(2) {
    border-right: 0;
  }

  .summary-metric:nth-child(-n + 2) {
    border-bottom: 1px solid var(--color-border);
  }

  .trend-layout {
    grid-template-columns: 1fr;
  }

  .trend-insight {
    padding: 14px 0 0;
    border-top: 1px solid var(--color-border);
    border-left: 0;
  }

  .trend-insight > p {
    margin-bottom: 12px;
  }

  .heatmap-layout {
    display: grid;
    gap: 18px;
  }

  .heatmap-stats {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    padding: 14px 0 0;
    border-top: 1px solid var(--color-border);
    border-left: 0;
  }
}

@media (max-width: 420px) {
  .learning-charts__summary {
    grid-template-columns: 1fr 1fr;
  }

  .summary-metric {
    padding-inline: 13px;
  }

  .trend-chart svg {
    height: 165px;
  }

  .heatmap {
    gap: 2px;
  }

  .heatmap > div,
  .heatmap-weekdays {
    gap: 3px;
  }

  .heatmap-stats {
    gap: 8px;
  }

  .heatmap-stats__item strong {
    font-size: 17px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .heatmap span {
    transition: none;
  }
}
</style>
