<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import {
  Calendar,
  Clock,
  Collection,
  Cpu,
  DataAnalysis,
  Edit,
  List,
  Memo,
  Search,
  TrendCharts,
  User,
  View,
  Warning,
} from '@element-plus/icons-vue'
import type {
  StudentDetailResponse,
  StudentProfileDimensionStat,
} from '@/api/teacherDashboard'

const props = defineProps<{
  modelValue: boolean
  detail: StudentDetailResponse | null
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

// ============== 动画状态：抽屉打开后依次触发各模块动画 ==============
const animReady = ref(false)
const animTimers: number[] = []

function clearAnimTimers() {
  animTimers.forEach((t) => window.clearTimeout(t))
  animTimers.length = 0
}

function scheduleAnim() {
  clearAnimTimers()
  animReady.value = false
  // 等抽屉过渡结束后再触发，避免视觉冲突
  const baseDelay = 280
  animTimers.push(
    window.setTimeout(() => {
      animReady.value = true
    }, baseDelay),
  )
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      scheduleAnim()
    } else {
      clearAnimTimers()
      animReady.value = false
    }
  },
)

watch(
  () => props.detail,
  () => {
    if (props.modelValue) {
      nextTick(() => scheduleAnim())
    }
  },
)

onBeforeUnmount(() => clearAnimTimers())

// ============== 数字滚动动画 ==============
const animatedMastery = ref(0)
const animatedProgress = ref(0)
const animatedOjSubs = ref(0)
const animatedOjAc = ref(0)
const animatedResources = ref(0)
const animatedCompleteness = ref(0)
const animatedStreak = ref(0)

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}

function animateNumber(
  target: number,
  setter: (v: number) => void,
  duration = 900,
  isFloat = false,
) {
  const start = 0
  const startTime = performance.now()
  function tick(now: number) {
    const elapsed = now - startTime
    const progress = Math.min(1, elapsed / duration)
    const v = start + (target - start) * easeOutCubic(progress)
    setter(isFloat ? Math.round(v * 10) / 10 : Math.round(v))
    if (progress < 1) {
      requestAnimationFrame(tick)
    } else {
      setter(target)
    }
  }
  requestAnimationFrame(tick)
}

watch(
  () => props.detail,
  (d) => {
    if (!d || !props.modelValue) return
    // 延迟启动数字滚动，让淡入动画先开始
    animTimers.push(
      window.setTimeout(() => {
        animateNumber(d.mastery_score, (v) => (animatedMastery.value = v), 1000, true)
        animateNumber(d.progress_percent, (v) => (animatedProgress.value = v), 1000, true)
        animateNumber(d.oj_submissions, (v) => (animatedOjSubs.value = v), 800)
        animateNumber(d.oj_accepted, (v) => (animatedOjAc.value = v), 800)
        animateNumber(d.resource_count, (v) => (animatedResources.value = v), 800)
        animateNumber(d.profile_completeness, (v) => (animatedCompleteness.value = v), 1200, true)
        animateNumber(d.learning_streak_days, (v) => (animatedStreak.value = v), 700)
      }, 320),
    )
  },
)

// ============== 工具函数 ==============
function masteryColor(score: number): string {
  if (score >= 80) return '#6aa878'
  if (score >= 50) return '#9c7a3d'
  return '#9e6470'
}

function formatDate(value: string): string {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function formatRelative(value: string): string {
  if (!value) return '暂无活跃'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  const now = Date.now()
  const diff = now - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} 天前`
  return formatDate(value)
}

function verdictTagType(
  verdict: string,
): 'success' | 'warning' | 'primary' | 'info' | 'danger' {
  switch (verdict) {
    case 'AC':
      return 'success'
    case 'WA':
      return 'warning'
    case 'TLE':
      return 'warning'
    case 'RE':
      return 'danger'
    case 'CE':
      return 'info'
    default:
      return 'info'
  }
}

// ============== 计算属性：图表数据 ==============
const totalOjVerdict = computed(() => {
  if (!props.detail) return 0
  return props.detail.oj_verdict_breakdown.reduce((sum, v) => sum + v.count, 0)
})

const ojAcRate = computed(() => {
  if (!props.detail || props.detail.oj_submissions === 0) return 0
  return Math.round((props.detail.oj_accepted / props.detail.oj_submissions) * 1000) / 10
})

// 综合学习完成度（环形图）：mastery(40%) + progress(30%) + oj_ac_rate(20%) + profile_completeness(10%)
const overallCompleteness = computed(() => {
  if (!props.detail) return 0
  const mastery = props.detail.mastery_score
  const progress = props.detail.progress_percent
  const acRate = props.detail.oj_submissions > 0 ? ojAcRate.value : 30
  const profileComp = props.detail.profile_completeness
  return Math.round((mastery * 0.4 + progress * 0.3 + acRate * 0.2 + profileComp * 0.1) * 10) / 10
})

// 环形进度 SVG 计算
const ringRadius = 52
const ringCircumference = 2 * Math.PI * ringRadius

const ringStrokeDashoffset = computed(() => {
  const pct = Math.max(0, Math.min(100, overallCompleteness.value))
  // 动画：从满偏移到目标偏移
  const targetOffset = ringCircumference * (1 - pct / 100)
  return animReady.value ? targetOffset : ringCircumference
})

// 雷达图计算
const radarPoints = computed(() => {
  if (!props.detail || !props.detail.dimension_stats.length) return []
  const cx = 120
  const cy = 120
  const maxR = 72
  const n = props.detail.dimension_stats.length
  const scale = animReady.value ? 1 : 0.08
  return props.detail.dimension_stats.map((dim: StudentProfileDimensionStat, i: number) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2
    const pct = (dim.score / 10) * 100
    const r = (pct / 100) * maxR * scale
    return {
      key: dim.key,
      label: dim.label,
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
      lx: cx + (maxR + 22) * Math.cos(angle),
      ly: cy + (maxR + 22) * Math.sin(angle),
      score: dim.score,
      text: dim.text,
      confidence: dim.confidence,
    }
  })
})

const radarPolygon = computed(() =>
  radarPoints.value.map((p) => `${p.x},${p.y}`).join(' '),
)

const radarGridLevels = [0.25, 0.5, 0.75, 1]

function radarGridPolygon(level: number): string {
  const dimensions = props.detail?.dimension_stats ?? []
  if (!dimensions.length) return ''
  return dimensions
    .map((_, index) => {
      const angle = (Math.PI * 2 * index) / dimensions.length - Math.PI / 2
      const radius = 72 * level
      return `${120 + radius * Math.cos(angle)},${120 + radius * Math.sin(angle)}`
    })
    .join(' ')
}

// 错误类型饼图（SVG）
const errorPieSegments = computed(() => {
  if (!props.detail || !props.detail.error_type_breakdown.length) return []
  const total = props.detail.error_type_breakdown.reduce((s, e) => s + e.count, 0)
  if (total === 0) return []
  const colors = ['#9e6470', '#9c7a3d', '#7a6e9e', '#5b8da8', '#6aa878']
  let cumAngle = -Math.PI / 2
  return props.detail.error_type_breakdown.map((e, i) => {
    const ratio = e.count / total
    const targetAngle = cumAngle + ratio * Math.PI * 2
    // 动画：使用 animReady 控制角度展开
    const animatedRatio = animReady.value ? ratio : 0
    const animatedEnd = cumAngle + animatedRatio * Math.PI * 2
    const cx = 70
    const cy = 70
    const r = 50
    const x1 = cx + r * Math.cos(cumAngle)
    const y1 = cy + r * Math.sin(cumAngle)
    const x2 = cx + r * Math.cos(animatedEnd)
    const y2 = cy + r * Math.sin(animatedEnd)
    const largeArc = animatedRatio > 0.5 ? 1 : 0
    const path = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`
    const seg = {
      key: e.error_type,
      label: e.label,
      count: e.count,
      percent: Math.round(ratio * 1000) / 10,
      color: colors[i % colors.length],
      path,
    }
    cumAngle = targetAngle
    return seg
  })
})

// 资源类型分布（横向条形图，归一化）
const resourceBars = computed(() => {
  if (!props.detail || !props.detail.resource_type_breakdown.length) return []
  const max = Math.max(...props.detail.resource_type_breakdown.map((r) => r.count), 1)
  return props.detail.resource_type_breakdown.map((r, i) => ({
    ...r,
    width: animReady.value ? (r.count / max) * 100 : 0,
    color: ['#3d8a7e', '#9c7a3d', '#5b8da8', '#6aa878', '#7a6e9e', '#9e6470'][i % 6],
  }))
})

// verdict 横向条形图（归一化）
const verdictBars = computed(() => {
  if (!props.detail) return []
  const max = Math.max(...props.detail.oj_verdict_breakdown.map((v) => v.count), 1)
  return props.detail.oj_verdict_breakdown.map((v) => ({
    ...v,
    width: animReady.value ? (v.count / max) * 100 : 0,
    percent: totalOjVerdict.value > 0
      ? Math.round((v.count / totalOjVerdict.value) * 1000) / 10
      : 0,
  }))
})

// 模块掌握度（条形图带动画）
const moduleBars = computed(() => {
  if (!props.detail) return []
  return props.detail.module_progress.map((m) => ({
    ...m,
    width: animReady.value ? m.mastery_score : 0,
    color: masteryColor(m.mastery_score),
  }))
})

// ============== 折叠面板 ==============
const expandedSections = ref<Record<string, boolean>>({
  profile: true,
  radar: true,
  ring: true,
  oj: true,
  modules: true,
  errors: true,
  resources: true,
  timeline: true,
  submissions: true,
})

function toggleSection(key: string) {
  expandedSections.value[key] = !expandedSections.value[key]
}

// ============== 时间线图标映射 ==============
const timelineIconMap: Record<string, unknown> = {
  edit: Edit,
  warning: Warning,
  search: Search,
  view: View,
  check: TrendCharts,
  user: User,
  collection: Collection,
  memo: Memo,
}

function getTimelineIcon(icon: string) {
  return timelineIconMap[icon] || Memo
}
</script>

<template>
  <el-drawer
    v-model="visible"
    size="640px"
    :title="detail ? `${detail.username} 的学情详情` : '学情详情'"
    direction="rtl"
    class="student-detail-drawer"
  >
    <div v-if="loading" class="drawer-loading">
      <el-skeleton :rows="10" animated />
    </div>
    <div v-else-if="detail" class="detail-content" :class="{ 'anim-ready': animReady }">
      <!-- 学生信息头部 -->
      <section class="detail-hero fade-in" style="--delay: 0ms">
        <div class="hero-avatar">
          {{ detail.username.slice(0, 1).toUpperCase() }}
        </div>
        <div class="hero-meta">
          <h3>{{ detail.username }}</h3>
          <div class="hero-tags">
            <el-tag size="small" effect="plain" type="info">
              <el-icon><Calendar /></el-icon>
              注册 {{ formatDate(detail.created_at) }}
            </el-tag>
            <el-tag size="small" effect="plain" type="info">
              <el-icon><Clock /></el-icon>
              {{ formatRelative(detail.last_active) }}
            </el-tag>
            <el-tag size="small" effect="plain" :type="animatedStreak >= 7 ? 'success' : 'warning'">
              <el-icon><TrendCharts /></el-icon>
              连续学习 {{ animatedStreak }} 天
            </el-tag>
          </div>
          <div class="completeness-note">
            <el-icon><DataAnalysis /></el-icon>
            <span>{{ detail.data_completeness_note }}</span>
          </div>
        </div>
      </section>

      <!-- 综合学习完成度 环形图 -->
      <section class="detail-block fade-in" style="--delay: 80ms">
        <header class="block-header" @click="toggleSection('ring')">
          <h4><el-icon><TrendCharts /></el-icon>综合学习完成度</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.ring }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.ring" class="ring-block">
          <div class="ring-wrap">
            <svg viewBox="0 0 140 140" class="ring-svg">
              <circle
                cx="70"
                cy="70"
                :r="ringRadius"
                fill="none"
                stroke="rgba(145,161,154,0.16)"
                stroke-width="10"
              />
              <circle
                cx="70"
                cy="70"
                :r="ringRadius"
                fill="none"
                :stroke="overallCompleteness >= 50 ? '#6aa878' : '#9c7a3d'"
                stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="ringCircumference"
                :stroke-dashoffset="ringStrokeDashoffset"
                transform="rotate(-90 70 70)"
                class="ring-progress"
              />
            </svg>
            <div class="ring-center">
              <strong>{{ animatedCompleteness.toFixed(1) }}<span>%</span></strong>
              <span class="ring-label">综合完成度</span>
            </div>
          </div>
          <ul class="ring-breakdown">
            <li>
              <span class="dot" style="background: #3d8a7e"></span>
              掌握度 {{ detail.mastery_score.toFixed(1) }}%
            </li>
            <li>
              <span class="dot" style="background: #9c7a3d"></span>
              学习进度 {{ detail.progress_percent.toFixed(1) }}%
            </li>
            <li>
              <span class="dot" style="background: #6aa878"></span>
              OJ AC 率 {{ ojAcRate }}%
            </li>
            <li>
              <span class="dot" style="background: #7a6e9e"></span>
              画像完成 {{ detail.profile_completeness.toFixed(1) }}%
            </li>
          </ul>
        </div>
      </section>

      <!-- 5 个核心指标卡 -->
      <section class="detail-metric-row fade-in" style="--delay: 140ms">
        <div class="detail-metric">
          <strong :style="{ color: masteryColor(detail.mastery_score) }">
            {{ animatedMastery.toFixed(1) }}<span class="unit">%</span>
          </strong>
          <span>掌握度</span>
        </div>
        <div class="detail-metric">
          <strong>{{ animatedProgress.toFixed(1) }}<span class="unit">%</span></strong>
          <span>学习进度</span>
        </div>
        <div class="detail-metric">
          <strong>{{ animatedOjSubs }}</strong>
          <span>OJ 提交</span>
        </div>
        <div class="detail-metric">
          <strong>{{ animatedOjAc }}</strong>
          <span>OJ AC</span>
        </div>
        <div class="detail-metric">
          <strong>{{ animatedResources }}</strong>
          <span>资源数</span>
        </div>
      </section>

      <!-- 学习画像摘要 + 六维雷达图 -->
      <section class="detail-block fade-in" style="--delay: 220ms">
        <header class="block-header" @click="toggleSection('radar')">
          <h4><el-icon><User /></el-icon>学习画像六维</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.radar }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.radar" class="radar-block">
          <div class="radar-wrap">
            <svg viewBox="0 0 240 240" class="radar-svg" aria-label="学习画像六维雷达图">
              <g v-for="lv in radarGridLevels" :key="lv">
                <polygon
                  :points="radarGridPolygon(lv)"
                  fill="none"
                  stroke="rgba(145,161,154,0.25)"
                  stroke-width="1"
                />
              </g>
              <line
                v-for="(p, i) in radarPoints"
                :key="'axis-' + i"
                x1="120"
                y1="120"
                :x2="p.lx"
                :y2="p.ly"
                stroke="rgba(145,161,154,0.2)"
              />
              <polygon
                :points="radarPolygon"
                class="radar-fill"
                fill="rgba(61,138,126,0.25)"
                stroke="#3d8a7e"
                stroke-width="2"
              />
              <circle
                v-for="p in radarPoints"
                :key="p.key"
                :cx="p.x"
                :cy="p.y"
                r="3"
                fill="#3d8a7e"
              />
              <text
                v-for="p in radarPoints"
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
              <li v-for="p in radarPoints" :key="'leg-' + p.key" class="legend-item">
                <div class="legend-head">
                  <span>{{ p.label }}</span>
                  <strong>{{ p.score }}<span class="unit">/10</span></strong>
                </div>
                <p class="legend-text" :class="{ inferred: p.confidence === 'inferred' }">
                  {{ p.text }}
                </p>
                <el-tag
                  v-if="p.confidence === 'inferred'"
                  size="small"
                  type="warning"
                  effect="plain"
                >
                  推断
                </el-tag>
              </li>
            </ul>
          </div>
          <p v-if="detail.profile_summary" class="profile-summary-text">
            {{ detail.profile_summary }}
          </p>
        </div>
      </section>

      <!-- 薄弱模块 -->
      <section v-if="detail.weak_modules.length" class="detail-block fade-in" style="--delay: 280ms">
        <header class="block-header" @click="toggleSection('profile')">
          <h4><el-icon><Warning /></el-icon>薄弱模块</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.profile }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.profile" class="tag-row">
          <el-tag
            v-for="mod in detail.weak_modules"
            :key="mod"
            type="danger"
            effect="plain"
            size="large"
          >
            {{ mod }}
          </el-tag>
        </div>
      </section>

      <!-- OJ verdict 分布 -->
      <section class="detail-block fade-in" style="--delay: 340ms">
        <header class="block-header" @click="toggleSection('oj')">
          <h4><el-icon><Cpu /></el-icon>OJ 提交结果分布</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.oj }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.oj" class="verdict-block">
          <div v-if="totalOjVerdict === 0" class="empty-tip">
            <el-empty :image-size="60" description="该学生暂无 OJ 提交记录" />
          </div>
          <div v-else class="verdict-bars">
            <div
              v-for="(bar, idx) in verdictBars"
              :key="bar.verdict"
              class="verdict-bar-row"
              :style="{ '--bar-color': bar.color, '--bar-delay': `${idx * 60}ms` }"
            >
              <div class="bar-label">
                <span class="dot" :style="{ background: bar.color }"></span>
                <span>{{ bar.label }}</span>
                <strong>{{ bar.count }} 次</strong>
                <span class="percent">({{ bar.percent }}%)</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: `${bar.width}%`, background: bar.color }" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 分模块掌握度 -->
      <section v-if="detail.module_progress.length" class="detail-block fade-in" style="--delay: 400ms">
        <header class="block-header" @click="toggleSection('modules')">
          <h4><el-icon><List /></el-icon>分模块掌握度</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.modules }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.modules" class="module-progress-list">
          <div
            v-for="(mod, idx) in moduleBars"
            :key="mod.module_key"
            class="module-progress-item"
            :style="{ '--bar-color': mod.color, '--bar-delay': `${idx * 70}ms` }"
          >
            <span class="module-label">{{ mod.module_label }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: `${mod.width}%`, background: mod.color }"
              />
            </div>
            <span class="module-score" :style="{ color: mod.color }">
              {{ mod.mastery_score.toFixed(1) }}%
            </span>
          </div>
        </div>
      </section>

      <!-- 错误类型分布 饼图 -->
      <section v-if="detail.error_type_breakdown.length" class="detail-block fade-in" style="--delay: 460ms">
        <header class="block-header" @click="toggleSection('errors')">
          <h4><el-icon><Warning /></el-icon>错误类型分布</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.errors }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.errors" class="error-pie-block">
          <div v-if="errorPieSegments.length === 0" class="empty-tip">
            <el-empty :image-size="60" description="暂无错误记录" />
          </div>
          <div v-else class="pie-wrap">
            <svg viewBox="0 0 140 140" class="pie-svg">
              <path
                v-for="(seg, idx) in errorPieSegments"
                :key="seg.key"
                :d="seg.path"
                :fill="seg.color"
                :style="{ '--seg-delay': `${idx * 100}ms` }"
                class="pie-segment"
              >
                <title>{{ seg.label }}: {{ seg.count }} 次 ({{ seg.percent }}%)</title>
              </path>
            </svg>
            <ul class="pie-legend">
              <li v-for="seg in errorPieSegments" :key="seg.key">
                <span class="dot" :style="{ background: seg.color }"></span>
                <span class="legend-label">{{ seg.label }}</span>
                <strong>{{ seg.count }} 次</strong>
                <span class="percent">({{ seg.percent }}%)</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- 资源类型分布 -->
      <section v-if="detail.resource_type_breakdown.length" class="detail-block fade-in" style="--delay: 520ms">
        <header class="block-header" @click="toggleSection('resources')">
          <h4><el-icon><Collection /></el-icon>资源类型分布</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.resources }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.resources" class="resource-bars">
          <div
            v-for="(bar, idx) in resourceBars"
            :key="bar.resource_type"
            class="verdict-bar-row"
            :style="{ '--bar-color': bar.color, '--bar-delay': `${idx * 60}ms` }"
          >
            <div class="bar-label">
              <span class="dot" :style="{ background: bar.color }"></span>
              <span>{{ bar.label }}</span>
              <strong>{{ bar.count }} 个</strong>
            </div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${bar.width}%`, background: bar.color }" />
            </div>
          </div>
        </div>
      </section>

      <!-- 技能掌握度 -->
      <section v-if="detail.skill_mastery.length" class="detail-block fade-in" style="--delay: 560ms">
        <header class="block-header">
          <h4><el-icon><DataAnalysis /></el-icon>技能掌握度</h4>
        </header>
        <div class="skill-list">
          <div
            v-for="(skill, idx) in detail.skill_mastery"
            :key="skill.skill_id"
            class="skill-item"
            :style="{ '--bar-color': masteryColor(skill.mastery_score), '--bar-delay': `${idx * 60}ms` }"
          >
            <div class="skill-head">
              <span>{{ skill.skill_label }}</span>
              <strong :style="{ color: masteryColor(skill.mastery_score) }">
                {{ skill.mastery_score.toFixed(1) }}%
              </strong>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{
                  width: animReady ? `${skill.mastery_score}%` : '0%',
                  background: masteryColor(skill.mastery_score),
                }"
              />
            </div>
            <span class="sample-count">{{ skill.sample_count }} 条样本</span>
          </div>
        </div>
      </section>

      <!-- 学习活跃时间线 -->
      <section v-if="detail.activity_timeline.length" class="detail-block fade-in" style="--delay: 620ms">
        <header class="block-header" @click="toggleSection('timeline')">
          <h4><el-icon><Clock /></el-icon>学习活跃时间线</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.timeline }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.timeline" class="timeline-list">
          <div
            v-for="(item, idx) in detail.activity_timeline"
            :key="idx"
            class="timeline-item"
            :style="{ '--item-delay': `${idx * 80}ms` }"
          >
            <div class="timeline-dot">
              <el-icon><component :is="getTimelineIcon(item.icon)" /></el-icon>
            </div>
            <div class="timeline-body">
              <div class="timeline-head">
                <strong>{{ item.label }}</strong>
                <span class="timeline-time">{{ formatRelative(item.created_at) }}</span>
              </div>
              <p class="timeline-desc">{{ item.description }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 最近 OJ 提交列表 -->
      <section v-if="detail.oj_recent_submissions.length" class="detail-block fade-in" style="--delay: 680ms">
        <header class="block-header" @click="toggleSection('submissions')">
          <h4><el-icon><Cpu /></el-icon>最近 OJ 提交</h4>
          <el-icon class="collapse-icon" :class="{ collapsed: !expandedSections.submissions }"><View /></el-icon>
        </header>
        <div v-show="expandedSections.submissions" class="submission-list">
          <div
            v-for="(sub, idx) in detail.oj_recent_submissions"
            :key="idx"
            class="submission-item"
          >
            <div class="submission-head">
              <el-tag :type="verdictTagType(sub.verdict)" size="small" effect="dark">
                {{ sub.verdict }}
              </el-tag>
              <span class="submission-title">{{ sub.problem_title }}</span>
              <span class="submission-time">{{ formatRelative(sub.created_at) }}</span>
            </div>
            <div class="submission-meta">
              <span>{{ sub.language }}</span>
              <span>通过 {{ sub.passed }}/{{ sub.total }}</span>
              <span v-if="sub.runtime_ms">均 {{ sub.runtime_ms }}ms</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 最近学习记忆 -->
      <section v-if="detail.recent_memories.length" class="detail-block fade-in" style="--delay: 740ms">
        <header class="block-header">
          <h4><el-icon><Memo /></el-icon>最近学习记录</h4>
        </header>
        <div class="memory-list">
          <div
            v-for="(mem, index) in detail.recent_memories"
            :key="index"
            class="memory-item"
          >
            <div class="memory-header">
              <el-tag size="small" effect="plain">{{ String(mem.event_type || '事件') }}</el-tag>
              <span class="text-muted">{{ formatDate(String(mem.created_at || '')) }}</span>
            </div>
            <p v-if="mem.observed_error_pattern" class="memory-text">
              错误模式：{{ mem.observed_error_pattern }}
            </p>
            <p v-if="mem.trace_summary" class="memory-text text-muted">
              {{ mem.trace_summary }}
            </p>
          </div>
        </div>
      </section>

      <el-empty
        v-if="
          !detail.profile_summary &&
          !detail.recent_memories.length &&
          !detail.module_progress.length &&
          !detail.dimension_stats.length
        "
        description="该学生暂无详细学习记录"
        :image-size="80"
      />
    </div>
  </el-drawer>
</template>

<style scoped>
.student-detail-drawer :deep(.el-drawer__body) {
  padding: 16px 20px 32px;
}

.drawer-loading {
  padding: 16px;
}

.detail-content {
  padding: 0 4px;
}

/* 依次淡入动画 */
.fade-in {
  opacity: 0;
  transform: translateY(12px);
  transition:
    opacity 0.55s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0ms),
    transform 0.55s cubic-bezier(0.22, 1, 0.36, 1) var(--delay, 0ms);
}

.anim-ready .fade-in {
  opacity: 1;
  transform: translateY(0);
}

/* 学生信息头部 */
.detail-hero {
  display: flex;
  gap: 14px;
  padding: 16px;
  margin-bottom: 18px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-lg);
  background:
    linear-gradient(135deg, rgba(61, 138, 126, 0.08), rgba(156, 122, 61, 0.06)),
    var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-sm);
}

.hero-avatar {
  display: grid;
  width: 56px;
  height: 56px;
  flex: 0 0 56px;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, #3d8a7e, #2e6b62);
  color: #fff;
  font-size: 22px;
  font-weight: 600;
  box-shadow: 0 6px 16px rgba(61, 138, 126, 0.32);
}

.hero-meta {
  flex: 1;
  min-width: 0;
}

.hero-meta h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.hero-tags .el-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.completeness-note {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.5;
}

/* 区块头 */
.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--alp-color-border);
  cursor: pointer;
  transition: color var(--alp-duration-fast);
}

.block-header:hover {
  color: var(--alp-color-primary);
}

.block-header h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.collapse-icon {
  transition: transform var(--alp-duration-normal);
  color: var(--alp-color-muted);
  font-size: 14px;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

/* 指标卡 */
.detail-metric-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-bottom: 18px;
  padding: 14px 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-lg);
  background: var(--alp-bg-surface);
}

.detail-metric {
  text-align: center;
  transition: transform var(--alp-duration-fast);
}

.detail-metric:hover {
  transform: translateY(-2px);
}

.detail-metric strong {
  display: block;
  font-size: 19px;
  font-variant-numeric: tabular-nums;
  color: var(--alp-color-text);
}

.detail-metric .unit {
  font-size: 12px;
  margin-left: 1px;
}

.detail-metric span {
  display: block;
  margin-top: 4px;
  color: var(--alp-color-muted);
  font-size: 11px;
}

/* 详情区块 */
.detail-block {
  margin-bottom: 20px;
  padding: 14px 16px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-lg);
  background: var(--alp-bg-surface);
  transition: border-color var(--alp-duration-fast), box-shadow var(--alp-duration-fast);
}

.detail-block:hover {
  border-color: color-mix(in srgb, var(--alp-color-primary) 38%, var(--alp-color-border));
  box-shadow: var(--alp-shadow-sm);
}

/* 综合完成度环形图 */
.ring-block {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.ring-wrap {
  position: relative;
  width: 140px;
  height: 140px;
  flex-shrink: 0;
}

.ring-svg {
  width: 100%;
  height: 100%;
}

.ring-progress {
  transition: stroke-dashoffset 1.4s cubic-bezier(0.22, 1, 0.36, 1);
  filter: drop-shadow(0 0 6px rgba(61, 138, 126, 0.32));
}

.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.ring-center strong {
  font-size: 22px;
  font-variant-numeric: tabular-nums;
  color: var(--alp-color-text);
}

.ring-center strong span {
  font-size: 12px;
  margin-left: 1px;
}

.ring-label {
  margin-top: 2px;
  color: var(--alp-color-muted);
  font-size: 11px;
}

.ring-breakdown {
  flex: 1;
  min-width: 180px;
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.ring-breakdown li {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--alp-color-text-secondary);
}

.ring-breakdown .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* 雷达图 */
.radar-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radar-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: center;
}

.radar-svg {
  width: 240px;
  height: 240px;
  flex-shrink: 0;
}

.anim-ready .radar-fill {
  transition: all 1s cubic-bezier(0.34, 1.2, 0.64, 1);
}

.axis-label {
  font-size: 10px;
  fill: var(--alp-color-muted);
}

.radar-legend {
  flex: 1;
  min-width: 220px;
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}

.legend-item {
  padding: 8px 10px;
  border-radius: var(--alp-radius-sm);
  background: var(--alp-bg-soft-block);
  transition: background var(--alp-duration-fast);
}

.legend-item:hover {
  background: var(--alp-bg-nav-hover);
}

.legend-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 12px;
}

.legend-head strong {
  color: var(--alp-color-primary);
  font-variant-numeric: tabular-nums;
}

.legend-head .unit {
  font-size: 10px;
  color: var(--alp-color-muted);
}

.legend-text {
  margin: 0 0 4px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--alp-color-text-secondary);
}

.legend-text.inferred {
  font-style: italic;
  color: var(--alp-color-muted);
}

.profile-summary-text {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--alp-radius-sm);
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-text-secondary);
  font-size: 12px;
  line-height: 1.7;
}

/* 标签行 */
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 条形图通用 */
.bar-track {
  flex: 1;
  min-width: 40px;
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-muted) 14%, transparent);
}

.bar-fill {
  height: 100%;
  border-radius: inherit;
  background: #3d8a7e;
  transition: width 0.9s cubic-bezier(0.22, 1, 0.36, 1) var(--bar-delay, 0ms);
}

/* OJ verdict 分布 */
.verdict-block {
  min-height: 40px;
}

.empty-tip {
  display: flex;
  justify-content: center;
}

.verdict-bars,
.resource-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.verdict-bar-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bar-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--alp-color-text-secondary);
}

.bar-label .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.bar-label strong {
  margin-left: auto;
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.bar-label .percent {
  color: var(--alp-color-muted);
  font-size: 11px;
}

/* 模块进度 */
.module-progress-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.module-progress-item {
  display: grid;
  grid-template-columns: 76px 1fr 50px;
  align-items: center;
  gap: 10px;
}

.module-label {
  font-size: 12px;
  color: var(--alp-color-text-secondary);
}

.module-score {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

/* 错误类型饼图 */
.pie-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.pie-svg {
  width: 140px;
  height: 140px;
  flex-shrink: 0;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.08));
}

.pie-segment {
  transition: opacity var(--alp-duration-normal);
  transform-origin: 70px 70px;
  animation: pie-fade-in 0.6s cubic-bezier(0.22, 1, 0.36, 1) var(--seg-delay, 0ms) both;
}

.pie-segment:hover {
  opacity: 0.78;
  transform: scale(1.04);
}

@keyframes pie-fade-in {
  from {
    opacity: 0;
    transform: scale(0.6);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.pie-legend {
  flex: 1;
  min-width: 160px;
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pie-legend li {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--alp-color-text-secondary);
}

.pie-legend .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.pie-legend .legend-label {
  flex: 1;
}

.pie-legend strong {
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.pie-legend .percent {
  color: var(--alp-color-muted);
  font-size: 11px;
}

/* 技能列表 */
.skill-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skill-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skill-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--alp-color-text-secondary);
}

.skill-head strong {
  font-variant-numeric: tabular-nums;
}

.sample-count {
  font-size: 10px;
  color: var(--alp-color-muted);
}

/* 时间线 */
.timeline-list {
  position: relative;
  padding-left: 8px;
}

.timeline-list::before {
  content: '';
  position: absolute;
  left: 16px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: linear-gradient(
    to bottom,
    rgba(61, 138, 126, 0.4),
    rgba(156, 122, 61, 0.2),
    transparent
  );
}

.timeline-item {
  position: relative;
  display: flex;
  gap: 12px;
  padding: 6px 0 12px 28px;
  opacity: 0;
  transform: translateX(-12px);
  transition:
    opacity 0.5s cubic-bezier(0.22, 1, 0.36, 1) var(--item-delay, 0ms),
    transform 0.5s cubic-bezier(0.22, 1, 0.36, 1) var(--item-delay, 0ms);
}

.anim-ready .timeline-item {
  opacity: 1;
  transform: translateX(0);
}

.timeline-dot {
  position: absolute;
  left: 8px;
  top: 6px;
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--alp-bg-surface-solid);
  border: 2px solid var(--alp-color-primary);
  color: var(--alp-color-primary);
  font-size: 9px;
  box-shadow: 0 0 0 3px rgba(61, 138, 126, 0.12);
  transition: transform var(--alp-duration-normal);
}

.timeline-item:hover .timeline-dot {
  transform: scale(1.2);
}

.timeline-body {
  flex: 1;
  min-width: 0;
  padding: 8px 12px;
  border-radius: var(--alp-radius-sm);
  background: var(--alp-bg-soft-block);
  transition: background var(--alp-duration-fast);
}

.timeline-item:hover .timeline-body {
  background: var(--alp-bg-nav-hover);
}

.timeline-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.timeline-head strong {
  font-size: 12px;
  font-weight: 600;
}

.timeline-time {
  color: var(--alp-color-muted);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.timeline-desc {
  margin: 0;
  color: var(--alp-color-text-secondary);
  font-size: 11px;
  line-height: 1.5;
  word-break: break-word;
}

/* OJ 提交列表 */
.submission-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.submission-item {
  padding: 8px 10px;
  border-radius: var(--alp-radius-sm);
  background: var(--alp-bg-soft-block);
  transition: background var(--alp-duration-fast), transform var(--alp-duration-fast);
}

.submission-item:hover {
  background: var(--alp-bg-nav-hover);
  transform: translateX(2px);
}

.submission-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.submission-title {
  flex: 1;
  font-size: 12px;
  color: var(--alp-color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.submission-time {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.submission-meta {
  display: flex;
  gap: 12px;
  color: var(--alp-color-muted);
  font-size: 11px;
}

/* 学习记录 */
.memory-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.memory-item {
  padding: 10px 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-sm);
  background: var(--alp-bg-surface);
}

.memory-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.memory-text {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.6;
}

.text-muted {
  color: var(--alp-color-muted);
  font-size: 12px;
}

@media (max-width: 760px) {
  .detail-metric-row {
    grid-template-columns: repeat(3, 1fr);
  }

  .ring-breakdown {
    grid-template-columns: 1fr;
  }

  .radar-wrap {
    flex-direction: column;
  }

  .radar-legend {
    max-height: none;
  }
}
</style>
