<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Clock,
  Collection,
  DataLine,
  StarFilled,
  TrendCharts,
  Trophy,
  Calendar,
  Aim,
  Timer,
  Compass,
} from '@element-plus/icons-vue'
import { MODULE_PATH_HINTS } from '@/constants/modulePathHints'
import { buildLearningOverview, phaseLabel } from '@/utils/learningOverview'
import {
  loadFavoriteKeys,
  loadRecentVisits,
  toggleFavorite,
  type RecentVisit,
} from '@/utils/learningBookmarks'
import { useModuleNavigation } from '@/composables/useModuleNavigation'
import { isLoggedIn, getUser } from '@/stores/auth'
import { buildGameLearningOverview } from '@/utils/gameLearningOverview'
import { applyRemoteProgressPayload } from '@/utils/learningStorage'
import { fetchRecentEvents, type LearningEventRecord } from '@/api/events'
import PersonaChatPanel from '@/components/persona/PersonaChatPanel.vue'
import RecommendedResourcesPanel from '@/components/learning/RecommendedResourcesPanel.vue'
import { buildActivityDays, type ActivityDay, type ActivitySource } from '@/utils/learningActivity'
import LearningSectionDonut from '@/components/learning/LearningSectionDonut.vue'
import LearningModuleBarChart from '@/components/learning/LearningModuleBarChart.vue'
import LearningModuleRadar from '@/components/learning/LearningModuleRadar.vue'
import LearningActivityHeatmap from '@/components/learning/LearningActivityHeatmap.vue'
import LearningPulseChart from '@/components/learning/LearningPulseChart.vue'
import LearningEvaluationPanel from '@/components/learning/LearningEvaluationPanel.vue'
import MasteryEvaluationCard from '@/components/learning/MasteryEvaluationCard.vue'
import LearningEffectivenessCard from '@/components/learning/LearningEffectivenessCard.vue'

const route = useRoute()
const router = useRouter()
const { goModule } = useModuleNavigation()

const activeTab = ref(
  typeof route.query.tab === 'string' ? route.query.tab : 'overview',
)

const progressRevision = ref(0)
const overview = computed(() => {
  void progressRevision.value
  return buildLearningOverview()
})
const gameRevision = ref(0)
const dbEvents = ref<LearningEventRecord[]>([])
const dbActivityReady = ref(false)
const activityLoading = ref(false)
const activityRange = ref<7 | 30 | 90>(30)
const activityRanges = [7, 30, 90] as const
const gameOverview = computed(() => {
  void gameRevision.value
  return buildGameLearningOverview()
})
const favRevision = ref(0)

onMounted(async () => {
  if (!isLoggedIn.value) return
  activityLoading.value = true
  const [progressResult, eventsResult] = await Promise.allSettled([
    import('@/api/learning').then(({ fetchLearningProgress }) => fetchLearningProgress()),
    fetchRecentEvents({ limit: 100 }),
  ])
  if (progressResult.status === 'fulfilled') {
    applyRemoteProgressPayload((progressResult.value.payload || {}) as Record<string, unknown>)
    progressRevision.value++
    gameRevision.value++
  }
  if (eventsResult.status === 'fulfilled') {
    dbEvents.value = eventsResult.value.items
    dbActivityReady.value = true
  }
  activityLoading.value = false
})

const favoriteRows = computed(() => {
  void favRevision.value
  const keys = new Set(loadFavoriteKeys())
  return overview.value.rows.filter((r) => keys.has(r.key) && r.available)
})

const recentVisits = computed(() => loadRecentVisits())

const inProgressRows = computed(() =>
  overview.value.inProgressModules.length > 0
    ? overview.value.inProgressModules.slice(0, 10)
    : overview.value.rows.filter((r) => r.available && r.percent === 0 && r.hasProgressData).slice(0, 10),
)

const totalSectionsDone = computed(() =>
  overview.value.rows.reduce((acc, r) => acc + r.doneCount, 0),
)

const totalSections = computed(() =>
  overview.value.rows.reduce((acc, r) => acc + r.totalCount, 0),
)

const activityDays = computed(() => {
  const source: ActivitySource = {
    visitTimestamps: dbActivityReady.value ? [] : recentVisits.value.map((v) => v.visitedAt),
    gameClearTimestamps: gameOverview.value.recentHistory.map((r) => r.clearedAt),
    eventTimestamps: dbActivityReady.value
      ? dbEvents.value.map((event) => Date.parse(event.created_at)).filter(Number.isFinite)
      : [],
  }
  return buildActivityDays(source, 12)
})

const pulseDays = computed(() => activityDays.value.slice(-activityRange.value))

const pulseSummary = computed(() => {
  const days = pulseDays.value
  const activeDays = days.filter((day) => day.count > 0)
  const total = days.reduce((sum, day) => sum + day.count, 0)
  const peak = days.reduce<ActivityDay | null>(
    (best, day) => (!best || day.count > best.count ? day : best),
    null,
  )
  return {
    total,
    activeDays: activeDays.length,
    peakLabel: peak ? `${peak.count} 次 · ${formatActivityDate(peak.date)}` : '暂无记录',
  }
})

const eventTypeStats = computed(() => {
  const labels: Record<string, string> = {
    section_done: '完成小节',
    resource_complete: '完成资源',
    quiz_complete: '完成测验',
    oj_submit_success: 'OJ 通过',
    oj_submit_fail: 'OJ 未通过',
    trace_diagnosis: 'Trace 诊断',
    evaluation_struggle: '评估反馈',
  }
  const counts = new Map<string, number>()
  for (const event of dbEvents.value) {
    const key = event.event_type || 'other'
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  const total = [...counts.values()].reduce((sum, value) => sum + value, 0)
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([key, count]) => ({
      key,
      label: labels[key] ?? '其他学习事件',
      count,
      percent: total > 0 ? Math.round((count / total) * 100) : 0,
    }))
})

const activitySourceLabel = computed(() => {
  if (!isLoggedIn.value) return '本地学习记录'
  if (dbActivityReady.value) return '账号数据库事件'
  return '正在连接账号数据'
})

const phaseStats = computed(() => {
  const phases = ['foundation', 'technique', 'tree', 'advanced'] as const
  return phases.map(phase => {
    const rows = overview.value.rows.filter(r => r.phase === phase)
    const done = rows.reduce((s, r) => s + r.doneCount, 0)
    const total = rows.reduce((s, r) => s + r.totalCount, 0)
    return { phase, label: phaseLabel(phase), done, total, percent: total > 0 ? Math.round(done / total * 100) : 0 }
  })
})

const weeklyActivity = computed(() => {
  const days = activityDays.value
  const recent7 = days.slice(-7)
  const total = recent7.reduce((s, d) => s + d.count, 0)
  return { total, days: recent7.length }
})

const recentVisitGroups = computed(() => {
  const todayStart = new Date(new Date().toISOString().slice(0, 10)).getTime()
  const yesterdayStart = todayStart - 86400_000
  const groups: { label: string; items: RecentVisit[] }[] = [
    { label: '今天', items: [] },
    { label: '昨天', items: [] },
    { label: '更早', items: [] },
  ]
  for (const v of recentVisits.value) {
    if (v.visitedAt >= todayStart) {
      groups[0].items.push(v)
    } else if (v.visitedAt >= yesterdayStart) {
      groups[1].items.push(v)
    } else {
      groups[2].items.push(v)
    }
  }
  return groups.filter((g) => g.items.length > 0)
})

function onToggleFavorite(key: string) {
  toggleFavorite(key)
  favRevision.value += 1
}

function formatVisitTime(ts: number) {
  const d = new Date(ts)
  const now = Date.now()
  const diff = now - ts
  if (diff < 60_000) return '刚刚'
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function openRecent(visit: RecentVisit) {
  goModule(visit.moduleKey)
}

function onTabChange(name: string | number) {
  activeTab.value = String(name)
  router.replace({ query: { ...route.query, tab: String(name) } })
}

function getModuleHint(key: string) {
  return MODULE_PATH_HINTS[key]
}

function formatActivityDate(dateKey: string) {
  const date = new Date(`${dateKey}T00:00:00`)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
</script>

<template>
  <el-card shadow="never" class="page-card">
    <el-page-header title="我的学习" @back="router.push({ name: 'home' })" />
    <el-divider />

    <header class="page-hero">
      <div class="hero-main">
        <h2 class="hero-title">
          <el-icon class="hero-icon"><Compass /></el-icon>
          学习数据中心
        </h2>
        <p class="hero-desc">
          汇总学习进度、小游戏闯关与收藏。登录后小节进度与游戏记录会同步至云端数据库。
        </p>
      </div>
      <div class="hero-stats">
        <div class="stat-mini">
          <span class="stat-mini-value">{{ overview.overallPercent }}%</span>
          <span class="stat-mini-label">总进度</span>
        </div>
        <div class="stat-mini">
          <span class="stat-mini-value">{{ overview.completedModules }}</span>
          <span class="stat-mini-label">已完成</span>
        </div>
        <div class="stat-mini">
          <span class="stat-mini-value">{{ totalSectionsDone }}</span>
          <span class="stat-mini-label">小节</span>
        </div>
        <div class="stat-mini">
          <span class="stat-mini-value">{{ favoriteRows.length }}</span>
          <span class="stat-mini-label">收藏</span>
        </div>
      </div>
    </header>

    <template v-if="!isLoggedIn">
      <el-alert
        title="登录后可云端保存学习进度"
        type="info"
        show-icon
        :closable="false"
        class="alert-block"
      />
      <div class="actions">
        <el-button
          type="primary"
          @click="router.push({ name: 'login', query: { redirect: route.fullPath } })"
        >
          登录
        </el-button>
        <el-button @click="router.push({ name: 'register' })">注册</el-button>
      </div>
    </template>

    <div v-else class="user-info-bar">
      <div class="user-info-left">
        <el-avatar :size="36" class="user-avatar">{{ getUser()?.username?.slice(0, 1).toUpperCase() || '学' }}</el-avatar>
        <div class="user-info-text">
          <span class="user-info-name">{{ getUser()?.username }}</span>
          <span class="user-info-meta">{{ totalSectionsDone }} / {{ totalSections }} 小节已完成</span>
        </div>
      </div>
      <el-button type="primary" text size="small" @click="router.push({ name: 'learning-path' })">
        <el-icon><Compass /></el-icon>
        继续学习
      </el-button>
    </div>

    <el-tabs v-model="activeTab" class="learn-tabs" @tab-change="onTabChange">
      <el-tab-pane label="学习概览" name="overview">
        <section class="dashboard-section">
          <div class="overview-dashboard-head">
            <div>
              <span class="dashboard-kicker">学习脉搏</span>
              <h2>把学习痕迹变成下一步</h2>
              <p>用活动趋势、阶段结构和模块掌握度，快速找到今天最值得投入的地方。</p>
            </div>
            <div class="range-switch" role="group" aria-label="活动时间范围">
              <button
                v-for="range in activityRanges"
                :key="range"
                type="button"
                :class="{ 'is-active': activityRange === range }"
                @click="activityRange = range"
              >
                {{ range }} 天
              </button>
            </div>
          </div>

          <div class="dashboard-bento">
            <section class="viz-panel viz-panel--pulse">
              <div class="viz-panel-head">
                <div>
                  <h3>学习活动趋势</h3>
                  <p>按天聚合账号事件，看看你的节奏有没有连续起来。</p>
                </div>
                <span class="source-chip" :class="{ 'is-loading': activityLoading }">
                  {{ activitySourceLabel }}
                </span>
              </div>
              <div class="pulse-legend">
                <span><i class="legend-line" />学习活动</span>
                <span>{{ activityRange }} 天 · {{ pulseSummary.activeDays }} 天有记录</span>
              </div>
              <LearningPulseChart :days="activityDays" :range="activityRange" />
              <div class="pulse-summary">
                <div>
                  <strong>{{ pulseSummary.total }}</strong>
                  <span>活动次数</span>
                </div>
                <div>
                  <strong>{{ pulseSummary.activeDays }}</strong>
                  <span>活跃天数</span>
                </div>
                <div>
                  <strong>{{ pulseSummary.peakLabel }}</strong>
                  <span>单日峰值</span>
                </div>
              </div>
            </section>

            <section class="viz-panel viz-panel--next">
              <div class="viz-panel-head">
                <div>
                  <h3>下一步建议</h3>
                  <p>从当前进度继续，不需要重新找入口。</p>
                </div>
                <el-icon><Compass /></el-icon>
              </div>
              <template v-if="overview.nextModule">
                <div class="next-module-phase">{{ phaseLabel(overview.nextModule.phase) }}</div>
                <h4 class="next-module-name">{{ overview.nextModule.label }}</h4>
                <p class="next-module-hint">
                  {{ getModuleHint(overview.nextModule.key)?.summary ?? '继续完成下一个小节，保持学习节奏。' }}
                </p>
                <div class="next-module-progress">
                  <div><span>模块进度</span><strong>{{ overview.rows.find((r) => r.key === overview.nextModule?.key)?.percent ?? 0 }}%</strong></div>
                  <div class="thin-progress"><i :style="{ width: `${overview.rows.find((r) => r.key === overview.nextModule?.key)?.percent ?? 0}%` }" /></div>
                </div>
                <el-button type="primary" size="small" @click="goModule(overview.nextModule.key)">继续学习</el-button>
              </template>
              <el-empty v-else description="完成一个模块后，这里会给出下一步" :image-size="64" />
            </section>

            <section class="viz-panel viz-panel--phase">
              <div class="viz-panel-head">
                <div>
                  <h3>阶段结构</h3>
                  <p>完成的小节落在哪个阶段。</p>
                </div>
                <el-icon><TrendCharts /></el-icon>
              </div>
              <LearningSectionDonut :rows="overview.rows" />
              <div class="phase-list">
                <div v-for="ps in phaseStats" :key="ps.phase" class="phase-row">
                  <span>{{ ps.label }}</span>
                  <strong>{{ ps.percent }}%</strong>
                </div>
              </div>
            </section>

            <section class="viz-panel viz-panel--heatmap">
              <div class="viz-panel-head">
                <div>
                  <h3>学习节奏</h3>
                  <p>颜色越深，代表当天留下的学习事件越多。</p>
                </div>
                <el-icon><Calendar /></el-icon>
              </div>
              <LearningActivityHeatmap :days="activityDays" :weeks="12" />
              <div class="viz-panel-foot">近 7 天 {{ weeklyActivity.total }} 次活动</div>
            </section>

            <section class="viz-panel viz-panel--radar">
              <div class="viz-panel-head">
                <div>
                  <h3>模块掌握轮廓</h3>
                  <p>用形状看出优势与需要补强的模块。</p>
                </div>
                <el-icon><DataLine /></el-icon>
              </div>
              <LearningModuleRadar :rows="overview.rows" :max-items="6" />
            </section>

            <section class="viz-panel viz-panel--mix">
              <div class="viz-panel-head">
                <div>
                  <h3>账号行为构成</h3>
                  <p>数据库最近事件按类型汇总。</p>
                </div>
                <el-icon><DataLine /></el-icon>
              </div>
              <div v-if="eventTypeStats.length" class="event-mix-list">
                <div v-for="item in eventTypeStats" :key="item.key" class="event-mix-row">
                  <div><span>{{ item.label }}</span><strong>{{ item.count }}</strong></div>
                  <div class="event-mix-track"><i :style="{ width: `${item.percent}%` }" /></div>
                </div>
              </div>
              <div v-else class="event-mix-empty">
                登录并完成一次小节、测验或 OJ 练习后，这里会开始记录你的学习行为。
              </div>
            </section>
          </div>

          <section class="viz-panel viz-panel--bars">
            <div class="viz-panel-head">
              <div>
                <h3>模块进度对比</h3>
                <p>点击任意模块，直接回到对应的学习内容。</p>
              </div>
              <el-button type="primary" text size="small" @click="router.push({ name: 'learning-path' })">查看学习路径</el-button>
            </div>
            <LearningModuleBarChart :rows="overview.rows" :max-items="8" @select="goModule" />
          </section>
        </section>

        <section class="modules-section">
          <div class="section-header">
            <h3 class="section-title">
              <el-icon><Timer /></el-icon>
              进行中的模块
            </h3>
            <el-tag size="small" effect="plain">{{ inProgressRows.length }} 个</el-tag>
          </div>

          <div v-if="inProgressRows.length" class="module-grid-5x2">
            <div
              v-for="row in inProgressRows"
              :key="row.key"
              class="module-card-compact"
              role="button"
              tabindex="0"
              @click="goModule(row.key)"
              @keydown.enter.prevent="goModule(row.key)"
            >
              <div class="card-header">
                <span class="card-name" :style="{ color: row.accent }">{{ row.label }}</span>
                <el-tag size="small" effect="plain">{{ phaseLabel(row.phase) }}</el-tag>
              </div>
              <div class="card-progress">
                <el-progress
                  :percentage="row.percent"
                  :stroke-width="6"
                  :show-text="false"
                  :color="row.accent"
                />
                <span class="card-pct">{{ row.percent }}%</span>
              </div>
              <div class="card-meta-row">
                <span class="card-meta-item">
                  <el-icon><Collection /></el-icon>
                  {{ row.doneCount }}/{{ row.totalCount }} 节
                </span>
                <span class="card-meta-item" v-if="getModuleHint(row.key)?.estHours">
                  <el-icon><Clock /></el-icon>
                  {{ getModuleHint(row.key)?.estHours }}h
                </span>
              </div>
              <ul v-if="getModuleHint(row.key)?.goals?.length" class="card-goals">
                <li v-for="(g, i) in getModuleHint(row.key)?.goals.slice(0, 2)" :key="i">{{ g }}</li>
              </ul>
              <div class="card-actions">
                <el-button type="primary" size="small" plain>
                  {{ row.percent > 0 ? '继续' : '开始' }}
                </el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无进行中的模块" :image-size="80">
            <el-button type="primary" size="small" @click="router.push({ name: 'learning-path' })">
              开始学习
            </el-button>
          </el-empty>
        </section>

        <section class="strength-section">
          <div class="strength-grid">
            <div class="strength-card">
              <div class="strength-head">
                <el-icon class="strength-icon strength-icon--success"><TrendCharts /></el-icon>
                <span class="strength-title">掌握较好</span>
              </div>
              <div class="strength-body">
                <template v-if="overview.strongModules.length">
                  <el-tag
                    v-for="r in overview.strongModules"
                    :key="r.key"
                    type="success"
                    effect="plain"
                    size="small"
                    class="strength-tag"
                    @click="goModule(r.key)"
                  >
                    {{ r.label }} {{ r.percent }}%
                  </el-tag>
                </template>
                <span v-else class="strength-empty">继续学习以积累掌握模块</span>
              </div>
            </div>
            <div class="strength-card">
              <div class="strength-head">
                <el-icon class="strength-icon strength-icon--warning"><Aim /></el-icon>
                <span class="strength-title">建议加强</span>
              </div>
              <div class="strength-body">
                <template v-if="overview.weakModules.length">
                  <el-tag
                    v-for="r in overview.weakModules"
                    :key="r.key"
                    type="warning"
                    effect="plain"
                    size="small"
                    class="strength-tag"
                    @click="goModule(r.key)"
                  >
                    {{ r.label }} {{ r.percent }}%
                  </el-tag>
                </template>
                <span v-else class="strength-empty">暂无薄弱项，保持节奏即可</span>
              </div>
            </div>
          </div>
        </section>

        <section class="all-modules-section">
          <div class="section-header">
            <h3 class="section-title">
              <el-icon><Collection /></el-icon>
              全部模块
            </h3>
            <el-tag size="small" effect="plain">共 {{ overview.rows.length }} 个</el-tag>
          </div>
          <div class="module-list-compact">
            <div
              v-for="row in overview.rows"
              :key="row.key"
              class="module-row"
              role="button"
              tabindex="0"
              @click="goModule(row.key)"
              @keydown.enter.prevent="goModule(row.key)"
            >
              <div class="module-row-left">
                <span class="module-row-dot" :style="{ background: row.accent }" />
                <span class="module-row-name">{{ row.label }}</span>
                <el-tag size="small" effect="plain" type="info">{{ phaseLabel(row.phase) }}</el-tag>
              </div>
              <div class="module-row-right">
                <el-progress
                  v-if="row.hasProgressData"
                  :percentage="row.percent"
                  :stroke-width="4"
                  :show-text="false"
                  style="width: 60px"
                  :color="row.accent"
                />
                <span class="module-row-pct" v-if="row.hasProgressData">{{ row.percent }}%</span>
                <span v-else class="module-row-muted">{{ row.available ? '未开始' : '规划中' }}</span>
              </div>
            </div>
          </div>
        </section>

        <RecommendedResourcesPanel v-if="isLoggedIn" class="overview-rec" />
      </el-tab-pane>

      <el-tab-pane label="效果评估" name="evaluation">
        <div class="eval-layout">
          <div class="eval-left">
            <MasteryEvaluationCard />
          </div>
          <div class="eval-right">
            <LearningEvaluationPanel />
            <LearningEffectivenessCard v-if="isLoggedIn" />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="收藏" name="favorites">
        <div v-if="favoriteRows.length" class="fav-grid">
          <div
            v-for="row in favoriteRows"
            :key="row.key"
            class="fav-card"
          >
            <div class="fav-card-top">
              <span class="fav-card-dot" :style="{ background: row.accent }" />
              <span class="fav-card-name" :style="{ color: row.accent }">{{ row.label }}</span>
              <el-tag size="small" effect="plain" type="info">{{ phaseLabel(row.phase) }}</el-tag>
              <el-button
                text
                size="small"
                :icon="StarFilled"
                class="fav-unstar-btn"
                @click.stop="onToggleFavorite(row.key)"
              />
            </div>
            <p class="fav-card-desc">
              {{ MODULE_PATH_HINTS[row.key]?.summary ?? '算法学习模块' }}
            </p>
            <div class="fav-card-progress" v-if="row.hasProgressData">
              <el-progress
                :percentage="row.percent"
                :stroke-width="6"
                :show-text="false"
                :color="row.accent"
              />
              <span class="fav-card-pct">{{ row.percent }}%</span>
            </div>
            <div class="fav-card-meta" v-if="row.hasProgressData">
              <span class="fav-card-meta-item">
                <el-icon><Collection /></el-icon>
                {{ row.doneCount }}/{{ row.totalCount }} 节
              </span>
            </div>
            <el-button type="primary" size="small" plain class="fav-card-action" @click="goModule(row.key)">进入学习</el-button>
          </div>
        </div>
        <el-empty v-else description="暂无收藏，在学习路径页可收藏模块" :image-size="80">
          <el-button type="primary" size="small" @click="router.push({ name: 'learning-path' })">去收藏</el-button>
        </el-empty>
      </el-tab-pane>

      <el-tab-pane label="小游戏" name="games">
        <div class="game-stats-row">
          <div class="game-stat-card">
            <el-icon class="game-stat-icon game-stat-icon--trophy"><Trophy /></el-icon>
            <div class="game-stat-info">
              <strong class="game-stat-value">{{ gameOverview.totalLevelsCleared }}</strong>
              <span class="game-stat-label">已通关卡</span>
            </div>
          </div>
          <div class="game-stat-card">
            <el-icon class="game-stat-icon game-stat-icon--percent"><TrendCharts /></el-icon>
            <div class="game-stat-info">
              <strong class="game-stat-value">{{ gameOverview.overallPercent }}%</strong>
              <span class="game-stat-label">总完成度</span>
            </div>
          </div>
          <div class="game-stat-card">
            <el-icon class="game-stat-icon game-stat-icon--unlock"><DataLine /></el-icon>
            <div class="game-stat-info">
              <strong class="game-stat-value">{{ gameOverview.rows.filter(r => r.cleared > 0).length }}</strong>
              <span class="game-stat-label">已解锁游戏</span>
            </div>
          </div>
        </div>

        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Trophy /></el-icon>
            各模块闯关进度
          </h3>
        </div>

        <div v-if="gameOverview.rows.some((r) => r.cleared > 0)" class="game-grid">
          <div
            v-for="row in gameOverview.rows.filter((r) => r.cleared > 0)"
            :key="row.gameId"
            class="game-card"
          >
            <div class="game-card-head">
              <span class="game-card-title">{{ row.title }}</span>
              <el-tag size="small" type="success" effect="plain">{{ row.cleared }}/{{ row.total }}</el-tag>
            </div>
            <el-progress :percentage="row.percent" :stroke-width="6" :show-text="false" color="#6aa878" />
            <div class="game-card-meta">
              <span>{{ row.moduleLabel }}</span>
            </div>
            <el-button
              type="primary"
              size="small"
              plain
              @click="router.push({ name: 'module-game-play', params: { gameId: row.gameId }, query: { from: 'my-learning' } })"
            >
              进入游戏
            </el-button>
          </div>
        </div>
        <el-empty v-else description="尚未通关任何小游戏" :image-size="80">
          <el-button type="primary" size="small" @click="router.push({ name: 'home' })">去学习</el-button>
        </el-empty>

        <div class="section-header">
          <h3 class="section-title">通关记录</h3>
        </div>

        <div v-if="gameOverview.recentHistory.length" class="history-list-compact">
          <div
            v-for="rec in gameOverview.recentHistory.slice(0, 10)"
            :key="`${rec.gameId}-${rec.levelId}-${rec.clearedAt}`"
            class="history-row"
          >
            <div class="history-row-left">
              <span class="history-row-title">{{ rec.gameTitle }} · {{ rec.levelTitle }}</span>
              <el-tag size="small" effect="plain">{{ rec.moduleKey === '_global' ? '毕业挑战' : rec.moduleKey }}</el-tag>
            </div>
            <span class="history-row-time">{{ formatVisitTime(rec.clearedAt) }}</span>
          </div>
        </div>
        <el-empty v-else description="通关后会显示在这里" :image-size="60" />
      </el-tab-pane>

      <el-tab-pane label="最近学习" name="history">
        <div v-if="recentVisits.length" class="recent-groups">
          <div
            v-for="group in recentVisitGroups"
            :key="group.label"
            class="recent-group"
          >
            <div class="recent-group-label">{{ group.label }}</div>
            <div class="recent-group-list">
              <div
                v-for="visit in group.items"
                :key="`${visit.moduleKey}-${visit.visitedAt}`"
                class="recent-item"
                role="button"
                tabindex="0"
                @click="openRecent(visit)"
                @keydown.enter.prevent="openRecent(visit)"
              >
                <div class="recent-item-left">
                  <span class="recent-item-dot" />
                  <span class="recent-item-title">{{ visit.label }}</span>
                </div>
                <div class="recent-item-right">
                  <span class="recent-item-time">{{ formatVisitTime(visit.visitedAt) }}</span>
                  <el-button text type="primary" size="small">继续</el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无访问记录" :image-size="80">
          <el-button type="primary" size="small" @click="router.push({ name: 'learning-path' })">开始学习</el-button>
        </el-empty>
      </el-tab-pane>

      <el-tab-pane label="学习画像" name="persona">
        <el-alert
          v-if="!isLoggedIn"
          type="warning"
          show-icon
          :closable="false"
        >
          登录后可使用流式画像对话
          <el-button type="primary" link @click="router.push({ name: 'login' })">去登录</el-button>
        </el-alert>
        <div v-if="isLoggedIn" class="persona-layout">
          <div class="persona-left">
            <PersonaChatPanel />
          </div>
          <div class="persona-right">
            <div class="persona-viz">
              <div class="persona-viz-head">
                <h3 class="section-title">模块掌握概览</h3>
                <el-tag size="small" effect="plain">雷达图</el-tag>
              </div>
              <LearningModuleRadar :rows="overview.rows" />
            </div>
            <div v-if="overview.weakModules.length" class="persona-hints">
              <span class="hints-label">建议优先加强：</span>
              <div class="hints-tags">
                <el-tag
                  v-for="r in overview.weakModules.slice(0, 3)"
                  :key="r.key"
                  type="warning"
                  effect="plain"
                  size="small"
                >
                  {{ r.label }}
                </el-tag>
              </div>
            </div>
            <div v-if="overview.strongModules.length" class="persona-hints persona-hints--success">
              <span class="hints-label">掌握较好：</span>
              <div class="hints-tags">
                <el-tag
                  v-for="r in overview.strongModules.slice(0, 3)"
                  :key="r.key"
                  type="success"
                  effect="plain"
                  size="small"
                >
                  {{ r.label }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<style scoped>
.page-card {
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
}

.page-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: color-mix(in srgb, var(--alp-color-primary) 8%, var(--alp-bg-soft-block));
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 25%, var(--alp-color-border));
}

.hero-main {
  flex: 1;
  min-width: 0;
}

.hero-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.hero-icon {
  color: var(--alp-color-primary);
  font-size: 20px;
}

.hero-desc {
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 13px;
  line-height: 1.5;
}

.hero-stats {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.stat-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  min-width: 60px;
}

.stat-mini-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--alp-color-primary);
  font-variant-numeric: tabular-nums;
}

.stat-mini-label {
  font-size: 10px;
  color: var(--alp-color-muted);
}

.user-info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  margin-bottom: 16px;
}

.user-info-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  background: var(--alp-color-primary-soft);
  color: var(--alp-color-primary);
  font-size: 14px;
}

.user-info-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--alp-color-text);
}

.user-info-meta {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.alert-block {
  margin-bottom: 12px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.learn-tabs {
  margin-top: 4px;
}

/* ===== 学习概览 ===== */
.dashboard-section {
  margin-bottom: 20px;
}

@media (max-width: 600px) {
  .page-hero {
    flex-direction: column;
  }

  .hero-stats {
    width: 100%;
    justify-content: space-between;
  }
}

/* ===== 学习脉搏重排 ===== */
.overview-dashboard-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin: 6px 0 14px;
}

.dashboard-kicker {
  display: block;
  margin-bottom: 5px;
  color: var(--alp-color-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.overview-dashboard-head h2 {
  margin: 0;
  color: var(--alp-color-text);
  font-size: clamp(20px, 2vw, 28px);
  font-weight: 780;
  letter-spacing: -0.035em;
}

.overview-dashboard-head p {
  max-width: 560px;
  margin: 6px 0 0;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.55;
}

.range-switch {
  display: inline-flex;
  flex-shrink: 0;
  padding: 3px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-pill);
  background: var(--alp-bg-soft-block);
}

.range-switch button {
  padding: 6px 10px;
  border: 0;
  border-radius: var(--alp-radius-pill);
  background: transparent;
  color: var(--alp-color-muted);
  font-size: 11px;
  cursor: pointer;
  transition: color 160ms ease, background-color 160ms ease, transform 160ms ease;
}

.range-switch button:hover,
.range-switch button:focus-visible {
  color: var(--alp-color-primary);
  outline: none;
}

.range-switch button.is-active {
  color: var(--alp-color-primary);
  background: var(--alp-bg-surface);
  box-shadow: 0 2px 7px rgba(var(--alp-color-primary-rgb), 0.1);
}

.dashboard-bento {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(250px, 0.82fr) minmax(230px, 0.76fr);
  gap: 12px;
}

.viz-panel {
  min-width: 0;
  padding: 16px 18px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
}

.viz-panel--pulse {
  grid-column: span 2;
  padding: 18px 20px 14px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--alp-color-primary) 8%, var(--alp-bg-soft-block)), var(--alp-bg-soft-block) 55%),
    var(--alp-bg-soft-block);
}

.viz-panel--next {
  display: flex;
  flex-direction: column;
}

.viz-panel--heatmap {
  grid-column: span 2;
}

.viz-panel--bars {
  grid-column: 1 / -1;
  margin-top: 12px;
  background: var(--alp-bg-surface);
}

.viz-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.viz-panel-head h3 {
  margin: 0;
  color: var(--alp-color-text);
  font-size: 14px;
  font-weight: 700;
}

.viz-panel-head p {
  margin: 4px 0 0;
  color: var(--alp-color-muted);
  font-size: 11px;
  line-height: 1.45;
}

.viz-panel-head > .el-icon {
  flex-shrink: 0;
  color: var(--alp-color-primary);
  font-size: 17px;
}

.source-chip {
  flex-shrink: 0;
  padding: 4px 7px;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 28%, var(--alp-color-border));
  border-radius: var(--alp-radius-pill);
  color: var(--alp-color-primary);
  font-size: 10px;
  line-height: 1;
}

.source-chip.is-loading {
  color: var(--alp-color-muted);
  border-color: var(--alp-color-border);
}

.pulse-legend {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  color: var(--alp-color-muted);
  font-size: 10px;
}

.pulse-legend > span:first-child {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--alp-color-text-secondary);
}

.legend-line {
  display: inline-block;
  width: 18px;
  height: 3px;
  border-radius: var(--alp-radius-pill);
  background: var(--alp-color-primary);
}

.pulse-summary {
  display: grid;
  grid-template-columns: 0.85fr 0.85fr 1.3fr;
  gap: 10px;
  margin-top: 2px;
  padding-top: 10px;
  border-top: 1px dashed var(--alp-color-border);
}

.pulse-summary div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.pulse-summary strong {
  overflow: hidden;
  color: var(--alp-color-text);
  font-size: 15px;
  font-variant-numeric: tabular-nums;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pulse-summary span,
.viz-panel-foot {
  color: var(--alp-color-muted);
  font-size: 10px;
}

.next-module-phase {
  margin-top: auto;
  color: var(--alp-color-primary);
  font-size: 11px;
  font-weight: 700;
}

.next-module-name {
  margin: 8px 0 0;
  color: var(--alp-color-text);
  font-size: 22px;
  letter-spacing: -0.04em;
}

.next-module-hint {
  min-height: 38px;
  margin: 8px 0 18px;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.55;
}

.next-module-progress {
  margin-bottom: 14px;
}

.next-module-progress > div:first-child {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  color: var(--alp-color-muted);
  font-size: 10px;
}

.next-module-progress strong {
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.thin-progress,
.event-mix-track {
  height: 5px;
  overflow: hidden;
  border-radius: var(--alp-radius-pill);
  background: color-mix(in srgb, var(--alp-color-border) 75%, transparent);
}

.thin-progress i,
.event-mix-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--alp-color-primary);
  transition: width 400ms ease;
}

.phase-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 14px;
  margin-top: 8px;
}

.phase-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: var(--alp-color-muted);
  font-size: 10px;
}

.phase-row strong {
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.event-mix-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 20px;
}

.event-mix-row > div:first-child {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  color: var(--alp-color-muted);
  font-size: 11px;
}

.event-mix-row strong {
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.event-mix-track i {
  background: var(--alp-color-accent);
}

.event-mix-empty {
  margin-top: 26px;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.6;
}

.viz-panel--bars :deep(.module-bars) {
  margin-top: 4px;
}

@media (max-width: 1040px) {
  .dashboard-bento {
    grid-template-columns: minmax(0, 1.2fr) minmax(250px, 0.8fr);
  }

  .viz-panel--pulse,
  .viz-panel--heatmap {
    grid-column: span 2;
  }
}

@media (max-width: 680px) {
  .overview-dashboard-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .dashboard-bento {
    grid-template-columns: 1fr;
  }

  .viz-panel--pulse,
  .viz-panel--heatmap,
  .viz-panel--bars {
    grid-column: span 1;
  }

  .range-switch {
    align-self: stretch;
    justify-content: space-between;
  }

  .range-switch button {
    flex: 1;
  }
}

@media (max-width: 420px) {
  .viz-panel,
  .viz-panel--pulse {
    padding-inline: 13px;
  }

  .pulse-summary {
    gap: 7px;
  }
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.section-title .el-icon {
  color: var(--alp-color-primary);
}

.modules-section {
  margin-bottom: 20px;
}

.module-grid-5x2 {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 1200px) {
  .module-grid-5x2 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .module-grid-5x2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .module-grid-5x2 {
    grid-template-columns: 1fr;
  }
}

.module-card-compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s, filter var(--alp-transition-fast);
}

.module-card-compact:hover,
.module-card-compact:focus-visible {
  transform: translateY(-2px);
  border-color: rgba(34, 211, 238, 0.35);
  box-shadow: var(--alp-shadow-card-hover);
  outline: none;
  filter: brightness(1.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-name {
  font-weight: 600;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-progress .el-progress {
  flex: 1;
  min-width: 0;
}

.card-pct {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.card-meta-row {
  display: flex;
  gap: 12px;
}

.card-meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.card-meta-item .el-icon {
  font-size: 12px;
}

.card-goals {
  margin: 0;
  padding-left: 14px;
  font-size: 11px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.card-goals li {
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  margin-top: auto;
}

.strength-section {
  margin-bottom: 20px;
}

.strength-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.strength-card {
  padding: 12px 14px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.strength-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.strength-icon {
  font-size: 16px;
}

.strength-icon--success {
  color: #6aa878;
}

.strength-icon--warning {
  color: #9c8540;
}

.strength-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.strength-body {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.strength-tag {
  cursor: pointer;
}

.strength-empty {
  font-size: 12px;
  color: var(--alp-color-muted);
}

@media (max-width: 600px) {
  .strength-grid {
    grid-template-columns: 1fr;
  }
}

.all-modules-section {
  margin-bottom: 20px;
}

.module-list-compact {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  padding: 10px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

@media (max-width: 1200px) {
  .module-list-compact {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .module-list-compact {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .module-list-compact {
    grid-template-columns: 1fr;
  }
}

.module-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, transform 0.2s;
}

.module-row:hover,
.module-row:focus-visible {
  background: var(--alp-color-primary-soft);
  border-color: color-mix(in srgb, var(--alp-color-primary) 30%, var(--alp-color-border));
  transform: translateY(-1px);
  outline: none;
}

.module-row-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.module-row-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.module-row-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--alp-color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-row-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.module-row-pct {
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.module-row-muted {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.overview-rec {
  margin-top: 16px;
}

/* ===== 效果评估 ===== */
.eval-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.eval-left {
  min-width: 0;
}

.eval-right {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (max-width: 900px) {
  .eval-layout {
    grid-template-columns: 1fr;
  }
}

/* ===== 收藏 ===== */
.fav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.fav-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s, filter var(--alp-transition-fast);
}

.fav-card:hover {
  transform: translateY(-2px);
  border-color: rgba(34, 211, 238, 0.35);
  box-shadow: var(--alp-shadow-card-hover);
  filter: brightness(1.06);
}

.fav-card-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fav-card-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.fav-card-name {
  font-weight: 600;
  font-size: 14px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fav-unstar-btn {
  margin-left: auto;
  color: #9c8540;
}

.fav-card-desc {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.fav-card-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fav-card-pct {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.fav-card-meta {
  display: flex;
  gap: 12px;
}

.fav-card-meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.fav-card-meta-item .el-icon {
  font-size: 12px;
}

.fav-card-action {
  margin-top: auto;
  align-self: flex-start;
}

/* ===== 小游戏 ===== */
.game-stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.game-stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.game-stat-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.game-stat-icon--trophy {
  color: #9c8540;
}

.game-stat-icon--percent {
  color: var(--alp-color-primary);
}

.game-stat-icon--unlock {
  color: #7a6e9e;
}

.game-stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.game-stat-value {
  font-size: 20px;
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.game-stat-label {
  font-size: 11px;
  color: var(--alp-color-muted);
}

@media (max-width: 600px) {
  .game-stats-row {
    grid-template-columns: 1fr;
  }
}

.game-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.game-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  transition: transform 0.2s, border-color 0.2s, filter var(--alp-transition-fast);
}

.game-card:hover {
  transform: translateY(-2px);
  border-color: rgba(74, 222, 128, 0.35);
  box-shadow: var(--alp-shadow-card-hover);
  filter: brightness(1.06);
}

.game-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.game-card-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--alp-color-text);
}

.game-card-meta {
  font-size: 11px;
  color: var(--alp-color-muted);
}

/* ===== 最近学习 ===== */
.recent-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recent-group-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-muted);
  padding-left: 4px;
  margin-bottom: 6px;
  position: relative;
}

.recent-group-label::before {
  content: '';
  position: absolute;
  left: 0;
  bottom: -2px;
  width: 32px;
  height: 2px;
  border-radius: 1px;
  background: var(--alp-color-primary);
  opacity: 0.4;
}

.recent-group-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.recent-item:hover,
.recent-item:focus-visible {
  background: var(--alp-color-primary-soft);
  border-color: color-mix(in srgb, var(--alp-color-primary) 30%, var(--alp-color-border));
  outline: none;
}

.recent-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.recent-item-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--alp-color-primary);
  flex-shrink: 0;
  opacity: 0.6;
}

.recent-item-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--alp-color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-item-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.recent-item-time {
  font-size: 11px;
  color: var(--alp-color-muted);
}

/* ===== 通关记录（小游戏子区域） ===== */
.history-list-compact {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.history-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition: background 0.2s;
}

.history-row:hover,
.history-row:focus-visible {
  background: var(--alp-color-primary-soft);
  outline: none;
}

.history-row-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.history-row-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--alp-color-text);
}

.history-row-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-row-time {
  font-size: 11px;
  color: var(--alp-color-muted);
}

/* ===== 学习画像 ===== */
.persona-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.persona-left {
  min-width: 0;
}

.persona-right {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (max-width: 900px) {
  .persona-layout {
    grid-template-columns: 1fr;
  }
}

.persona-viz {
  padding: 12px 14px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.persona-viz-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.persona-hints {
  padding: 10px 12px;
  border-radius: var(--alp-radius-card);
  background: color-mix(in srgb, var(--el-color-warning-light-9) 40%, var(--alp-bg-soft-block));
  border: 1px solid color-mix(in srgb, var(--el-color-warning) 20%, var(--alp-color-border));
}

.persona-hints--success {
  background: color-mix(in srgb, var(--el-color-success-light-9) 40%, var(--alp-bg-soft-block));
  border-color: color-mix(in srgb, var(--el-color-success) 20%, var(--alp-color-border));
}

.hints-label {
  font-size: 12px;
  color: var(--alp-color-muted);
  display: block;
  margin-bottom: 6px;
}

.hints-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
