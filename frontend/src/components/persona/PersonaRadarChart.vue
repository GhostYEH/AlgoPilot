<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  PROFILE_DIMENSION_LABELS,
  type PersonaDimensions,
} from '@/api/orchestrator'

const props = defineProps<{
  dimensions: PersonaDimensions
  /** 后端量化分值 1-10，优先用于雷达图 */
  scores?: Record<string, number>
  animated?: boolean
}>()

const keys = Object.keys(PROFILE_DIMENSION_LABELS) as (keyof PersonaDimensions)[]
const reveal = ref(!props.animated)

onMounted(() => {
  if (!props.animated) return
  requestAnimationFrame(() => {
    reveal.value = true
  })
})

const _PENDING_VALUES = new Set(['待补充', '暂无', '未知'])

const _LOW_MARKERS = ['零基础', '不会', '薄弱', '初学', '入门', '不太', '较差', '很少', '几乎没']
const _HIGH_MARKERS = ['熟练', '扎实', '较强', '独立', '竞赛', 'ACM', '蓝桥', '能写', '较好', '深入']

function scoreFor(key: keyof PersonaDimensions): number {
  const s = props.scores?.[key]
  if (typeof s === 'number' && s >= 1 && s <= 10) {
    return Math.round(s * 10)
  }
  const t = (props.dimensions[key] || '').trim()
  if (!t || _PENDING_VALUES.has(t)) return 40
  let score = 5
  for (const m of _LOW_MARKERS) { if (t.includes(m)) score -= 1 }
  for (const m of _HIGH_MARKERS) { if (t.includes(m)) score += 1 }
  if (t.length > 80) score += 1
  return Math.min(100, Math.max(10, Math.round(score * 10)))
}

const points = computed(() => {
  const n = keys.length
  const cx = 120
  const cy = 120
  const maxR = 72
  const scale = reveal.value ? 1 : 0.08
  return keys.map((key, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2
    const pct = scoreFor(key)
    const r = (pct / 100) * maxR * scale
    return {
      key,
      label: PROFILE_DIMENSION_LABELS[key],
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
      lx: cx + (maxR + 22) * Math.cos(angle),
      ly: cy + (maxR + 22) * Math.sin(angle),
      score: pct,
    }
  })
})

const polygon = computed(() =>
  points.value.map((p) => `${p.x},${p.y}`).join(' '),
)

const gridLevels = [0.25, 0.5, 0.75, 1]
</script>

<template>
  <div class="radar-wrap" :class="{ 'radar-wrap--animated': animated && reveal }">
    <svg viewBox="0 0 240 240" class="radar-svg" aria-label="学习画像六维雷达图">
      <g v-for="lv in gridLevels" :key="lv">
        <polygon
          :points="
            keys
              .map((_, i) => {
                const a = (Math.PI * 2 * i) / keys.length - Math.PI / 2
                const r = 72 * lv
                return `${120 + r * Math.cos(a)},${120 + r * Math.sin(a)}`
              })
              .join(' ')
          "
          fill="none"
          stroke="rgba(148,163,184,0.25)"
          stroke-width="1"
        />
      </g>
      <line
        v-for="(p, i) in points"
        :key="'axis-' + i"
        x1="120"
        y1="120"
        :x2="p.lx"
        :y2="p.ly"
        stroke="rgba(148,163,184,0.2)"
      />
      <polygon
        :points="polygon"
        class="radar-fill"
        fill="rgba(56,189,248,0.25)"
        stroke="#38bdf8"
        stroke-width="2"
      />
      <circle
        v-for="p in points"
        :key="p.key"
        :cx="p.x"
        :cy="p.y"
        r="3"
        fill="#38bdf8"
      />
      <text
        v-for="p in points"
        :key="'lbl-' + p.key"
        :x="p.lx"
        :y="p.ly"
        text-anchor="middle"
        dominant-baseline="middle"
        class="axis-label"
      >
        {{ p.label }}
      </text>
    </svg>
    <ul class="radar-legend">
      <li v-for="p in points" :key="'leg-' + p.key">
        <span>{{ p.label }}</span>
        <strong>{{ p.score }}%</strong>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.radar-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: center;
}

.radar-wrap--animated .radar-fill {
  transition: all 0.9s cubic-bezier(0.34, 1.2, 0.64, 1);
}

.radar-svg {
  width: 220px;
  height: 220px;
  flex-shrink: 0;
}

.axis-label {
  font-size: 9px;
  fill: var(--alp-color-muted);
}

.radar-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 11px;
  min-width: 120px;
}

.radar-legend li {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  color: var(--alp-color-muted);
}

.radar-legend strong {
  color: var(--alp-color-primary);
  font-variant-numeric: tabular-nums;
}
</style>
