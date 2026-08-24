<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { RouteLocationRaw } from 'vue-router'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Cpu, Reading, Collection, DataAnalysis, Document, VideoPlay } from '@element-plus/icons-vue'
import codingHeroUrl from '@/assets/home-coding-hero.png'
import HomeCommunityPanel from '@/components/home/HomeCommunityPanel.vue'
import HomeDashboardCharts from '@/components/home/HomeDashboardCharts.vue'
import HomeHitokotoBar from '@/components/home/HomeHitokotoBar.vue'
import HomeStageLearningMap from '@/components/home/HomeStageLearningMap.vue'
import HomeTrainingSection from '@/components/home/HomeTrainingSection.vue'
import AgentWorkbenchView from '@/views/AgentWorkbenchView.vue'
import { fetchCommunity, type CommunityResponse } from '@/api/analytics'
import { fetchProblems, type ProblemListItem } from '@/api/oj'
import { ALGORITHM_MODULES, MODULE_PHASE_LABELS, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { prefetchRoute } from '@/router/prefetch'
import { getApiBaseUrl } from '@/utils/apiBase'
import { getHeatmapCells, getLast7DaySeries, touchTodayVisit } from '@/utils/homeActivityLog'
import {
  buildPlatformStats,
  buildReviewQueue,
  buildSkillRadar,
  formatRecentRelative,
  getRecentForHome,
  pickDailyProblem,
  pickTargetedProblems,
} from '@/utils/homeDashboard'
import { recordModuleVisit } from '@/utils/learningBookmarks'
import { buildLearningOverview } from '@/utils/learningOverview'

const router = useRouter()
const route = useRoute()
const initialOverview = buildLearningOverview()

const activeModule = ref(initialOverview.nextModule?.key ?? ALGORITHM_MODULES[0]?.key ?? 'array')
const healthStatus = ref<'checking' | 'ok' | 'error'>('checking')
const ojReadyCount = ref<number | null>(null)
const ojProblems = ref<ProblemListItem[]>([])
const communityData = ref<CommunityResponse | null>(null)

const ROUTE_TO_MODULE: Record<string, string> = Object.fromEntries(
  Object.entries(MODULE_ROUTE_NAMES).map(([key, name]) => [name as string, key]),
)

function syncActiveFromRoute() {
  const byName = ROUTE_TO_MODULE[route.name as string]
  if (byName) {
    activeModule.value = byName
    return
  }
  if (route.name === 'learning-path' && typeof route.query.module === 'string') {
    activeModule.value = route.query.module
  }
}

watch(() => route.fullPath, syncActiveFromRoute, { immediate: true })

const overview = computed(() => buildLearningOverview())
const selectedModule = computed(
  () => ALGORITHM_MODULES.find((module) => module.key === activeModule.value) ?? ALGORITHM_MODULES[0],
)
const currentModule = computed(() => overview.value.nextModule ?? selectedModule.value ?? null)
const currentProgress = computed(
  () => overview.value.rows.find((row) => row.key === currentModule.value?.key) ?? null,
)
const currentPhaseLabel = computed(() =>
  currentModule.value ? MODULE_PHASE_LABELS[currentModule.value.phase] : '学习路径',
)
const remainingSections = computed(() => {
  const row = currentProgress.value
  if (!row?.totalCount) return null
  return Math.max(0, row.totalCount - row.doneCount)
})
const currentSectionLabel = computed(() => {
  const row = currentProgress.value
  if (!row?.totalCount) return '进入模块后查看章节目录'
  if (row.doneCount >= row.totalCount) return '本模块已完成'
  return `建议继续第 ${row.doneCount + 1} 个小节`
})
const recentVisits = computed(() => getRecentForHome())
const lastVisitLabel = computed(() => {
  const last = recentVisits.value[0]
  return last ? `${last.label} · ${formatRecentRelative(last.visitedAt)}` : '还没有最近学习记录'
})
const activitySeries = computed(() => getLast7DaySeries())
const heatmapCells = computed(() => getHeatmapCells(12))
const activityTotal = computed(() =>
  activitySeries.value.reduce((total, day) => total + day.total, 0),
)
const skillRadar = computed(() => buildSkillRadar(overview.value.rows))
const reviewQueue = computed(() => buildReviewQueue())
const dailyProblem = computed(() => pickDailyProblem(ojProblems.value))
const targetedProblems = computed(() =>
  pickTargetedProblems(overview.value.weakModules, ojProblems.value),
)
const platformStats = computed(() => {
  const base = buildPlatformStats(ojReadyCount.value)
  const stats = communityData.value?.stats
  if (!stats) return base
  return [
    ...base,
    { key: 'students', label: '注册学员', value: stats.student_count, suffix: ' 人' },
    { key: 'week_ac', label: '本周通过', value: stats.week_ac_count, suffix: ' 次' },
    { key: 'week_active', label: '本周活跃', value: stats.week_active_count, suffix: ' 人' },
  ]
})
const acBoard = computed(() => communityData.value?.ac_board ?? [])
const streakBoard = computed(() => communityData.value?.streak_board ?? [])
const serviceStatusLabel = computed(() => {
  if (healthStatus.value === 'checking') return '正在检查学习服务'
  return healthStatus.value === 'ok' ? '学习服务正常' : '当前可使用本地学习记录'
})

const quickActions: Array<{
  key: string
  label: string
  desc: string
  icon: typeof Reading
  route: RouteLocationRaw
  prefetch: string
}> = [
  {
    key: 'path',
    label: '学习路径',
    desc: '查看全部模块与学习顺序',
    icon: Collection,
    route: { name: 'learning-path' },
    prefetch: '/learning-path',
  },
  {
    key: 'oj',
    label: '在线 OJ',
    desc: '进入 Python / C++ 判题练习',
    icon: Cpu,
    route: { name: 'practice-list' },
    prefetch: '/practice',
  },
  {
    key: 'persona',
    label: '学习画像',
    desc: '查看掌握情况与学习建议',
    icon: DataAnalysis,
    route: { name: 'my-learning', query: { tab: 'persona' } },
    prefetch: '/my-learning',
  },
  {
    key: 'resources',
    label: '学习资料',
    desc: '查找讲义、题单与参考资料',
    icon: Document,
    route: { name: 'resources' },
    prefetch: '/resources',
  },
]

function previewModule(key: string) {
  activeModule.value = key
}

function onModuleSelect(key: string) {
  activeModule.value = key
  const module = ALGORITHM_MODULES.find((item) => item.key === key)
  if (module) recordModuleVisit(key, module.label)
  const routeName = MODULE_ROUTE_NAMES[key]
  if (routeName) {
    prefetchRoute(`/learn/${key}`)
    router.push({ name: routeName })
    return
  }
  router.push({ name: 'learning-path', query: { module: key } })
}

function continueLearning() {
  if (currentModule.value) {
    onModuleSelect(currentModule.value.key)
    return
  }
  router.push({ name: 'learning-path' })
}

function goQuick(item: (typeof quickActions)[number]) {
  prefetchRoute(item.prefetch)
  router.push(item.route)
}

function openPractice(slug: string) {
  prefetchRoute(`/practice/${slug}`)
  router.push({ name: 'practice-problem', params: { slug } })
}

onMounted(async () => {
  touchTodayVisit()
  const base = getApiBaseUrl()
  const healthUrl = base ? `${base}/api/health` : '/api/health'

  try {
    const response = await fetch(healthUrl)
    const data = response.ok ? ((await response.json()) as { status?: string }) : null
    healthStatus.value = data?.status === 'ok' ? 'ok' : 'error'
  } catch {
    healthStatus.value = 'error'
  }

  void fetchProblems()
    .then((list) => {
      ojProblems.value = list
      ojReadyCount.value = list.filter((problem) => problem.ready).length
    })
    .catch(() => {
      ojProblems.value = []
      ojReadyCount.value = null
    })

  void fetchCommunity()
    .then((data) => {
      communityData.value = data
    })
    .catch(() => {
      communityData.value = null
    })
})
</script>

<template>
  <div class="home-workspace home-page">
    <HomeHitokotoBar />
    <section class="study-hero" aria-labelledby="continue-title">
      <div class="study-hero__main">
        <div class="study-hero__copy">
          <p class="section-kicker">今日学习重点</p>
          <div class="study-hero__title-row">
            <h1 id="continue-title">{{ currentModule?.label ?? '选择一个学习模块' }}</h1>
            <span class="study-hero__topic" :title="currentPhaseLabel">{{ currentPhaseLabel }}</span>
          </div>
          <p class="study-hero__section">{{ currentSectionLabel }}</p>

          <div class="continue-learning__progress">
            <div>
              <span>基础结构</span>
              <strong>{{ currentProgress?.percent ?? 0 }}%</strong>
            </div>
            <div class="progress-track" aria-label="当前模块进度">
              <i :style="{ width: `${currentProgress?.percent ?? 0}%` }" />
            </div>
          </div>

          <div class="continue-learning__actions">
            <el-button type="primary" @click="continueLearning">
              <el-icon><VideoPlay /></el-icon>
              继续学习
            </el-button>
            <el-button plain @click="router.push({ name: 'practice-list' })">
              <el-icon><Cpu /></el-icon>
              进入题库
            </el-button>
          </div>
        </div>

        <div class="study-hero__visual" aria-hidden="true"><img :src="codingHeroUrl" alt="" /></div>
      </div>

      <aside class="study-hero__status" aria-label="学习状态">
        <div class="status-title">整体进度</div>
        <div class="status-ring">
          <el-progress type="circle" :percentage="overview.overallPercent" :width="72" :stroke-width="8" :show-text="false" />
          <strong>{{ overview.overallPercent }}<small>%</small></strong>
        </div>
        <div class="status-ring__label">
          <strong>已完成 {{ overview.completedModules }} / {{ ALGORITHM_MODULES.length }} 个模块<br />继续加油，稳步提升中！</strong>
        </div>

        <dl class="study-hero__facts">
          <div>
            <dt>上次学习</dt>
            <dd>{{ lastVisitLabel }}</dd>
            <small>{{ serviceStatusLabel }}</small>
          </div>
          <div>
            <dt>当前剩余</dt>
            <dd>{{ remainingSections === null ? '查看章节目录' : `${remainingSections} 个小节` }}</dd>
            <small>{{ reviewQueue.length ? `${reviewQueue.length} 项内容待复习` : '目前没有待复习内容' }}</small>
          </div>
        </dl>
      </aside>
    </section>

    <nav class="home-tools" aria-label="常用学习工具">
      <button
        v-for="item in quickActions"
        :key="item.key"
        type="button"
        @mouseenter="prefetchRoute(item.prefetch)"
        @click="goQuick(item)"
      >
        <span class="home-tools__icon"><el-icon><component :is="item.icon" /></el-icon></span>
        <span>
          <strong>{{ item.label }}</strong>
          <small>{{ item.desc }}</small>
        </span>
        <el-icon class="home-tools__arrow"><ArrowRight /></el-icon>
      </button>
    </nav>

    <HomeStageLearningMap
      :active-key="activeModule"
      :overall-percent="overview.overallPercent"
      @preview="previewModule"
      @open="onModuleSelect"
    />

    <section class="home-section recent-learning" aria-labelledby="recent-learning-title">
      <header class="home-section__head">
        <div>
          <h2 id="recent-learning-title">最近学习</h2>
          <p>
            {{
              activityTotal
                ? `近 7 天学习活跃度为 ${activityTotal} 分，数据来自访问与刷题记录。`
                : '近 7 天还没有学习记录，完成一次学习或练习后这里会显示趋势。'
            }}
          </p>
        </div>
        <span>近 7 天</span>
      </header>
      <HomeDashboardCharts :radar="skillRadar" :series="activitySeries" :heatmap="heatmapCells" />
    </section>

    <section class="home-section intelligent-learning" aria-labelledby="intelligent-learning-title">
      <header class="home-section__head">
        <div>
          <h2 id="intelligent-learning-title">智能化学习</h2>
          <p>围绕当前课程模块生成讲解、练习与拓展资源，生成结果会经过内容校验。</p>
        </div>
      </header>
      <AgentWorkbenchView embedded />
    </section>

    <div class="home-lower">
      <section class="home-section home-training" aria-labelledby="training-title">
        <header class="home-section__head">
          <div>
            <h2 id="training-title">接下来可以做</h2>
            <p>题目、复习与最近访问均来自现有学习记录。</p>
          </div>
          <el-button text type="primary" @click="router.push({ name: 'practice-list' })">
            查看题库
          </el-button>
        </header>
        <HomeTrainingSection
          :daily="dailyProblem"
          :targeted="targetedProblems"
          :review="reviewQueue"
          :recent="recentVisits"
          @open-problem="openPractice"
          @open-module="onModuleSelect"
        />
      </section>

      <aside class="home-section home-community" aria-labelledby="community-title">
        <header class="home-section__head">
          <div>
            <h2 id="community-title">社区动态</h2>
            <p>本周全站学习概况</p>
          </div>
        </header>
        <HomeCommunityPanel
          :stats="platformStats"
          :ac-board="acBoard"
          :streak-board="streakBoard"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.home-workspace {
  width: min(100%, 1536px);
  margin: 0 auto;
  padding: 2px 0 44px;
  color: var(--color-text-primary);
}

.home-tagline {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary, #888);
  margin: 8px 0 4px;
  letter-spacing: 0.02em;
}

.continue-learning {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(420px, 0.8fr);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-bg-surface);
}

.continue-learning__main {
  padding: 30px 32px 28px;
  border-right: 1px solid var(--color-border);
}

.section-kicker {
  margin: 0 0 6px;
  color: var(--color-brand);
  font-size: 12px;
  font-weight: 700;
}

.continue-learning h1 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: clamp(24px, 2.4vw, 32px);
  line-height: 1.25;
  letter-spacing: -0.025em;
}

.continue-learning__section {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.continue-learning__progress {
  max-width: 560px;
  margin-top: 24px;
}

.continue-learning__progress > div:first-child {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.continue-learning__progress strong {
  color: var(--color-brand);
  font-variant-numeric: tabular-nums;
}

.progress-track {
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--color-bg-subtle);
}

.progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-brand);
  transition: width 220ms ease;
}

.continue-learning__actions {
  display: flex;
  gap: 8px;
  margin-top: 24px;
}

.continue-learning__actions :deep(.el-button) {
  min-height: 40px;
  margin: 0;
  border-radius: var(--radius-sm);
}

.continue-learning__facts {
  display: grid;
  grid-template-rows: repeat(3, 1fr);
  margin: 0;
  padding: 0 28px;
}

.continue-learning__facts > div {
  display: grid;
  grid-template-columns: 104px minmax(0, 1fr);
  align-content: center;
  gap: 3px 16px;
  padding: 18px 0;
  border-bottom: 1px solid var(--color-border);
}

.continue-learning__facts > div:last-child {
  border-bottom: 0;
}

.continue-learning__facts dt {
  grid-row: 1 / 3;
  align-self: center;
  color: var(--color-text-muted);
  font-size: 12px;
}

.continue-learning__facts dd {
  overflow: hidden;
  margin: 0;
  color: var(--color-text-primary);
  font-size: 15px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.continue-learning__facts small {
  color: var(--color-text-muted);
  font-size: 11px;
}

.home-tools {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 12px;
  border-block: 1px solid var(--color-border);
}

.home-tools button {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 15px 18px;
  color: var(--color-text-primary);
  text-align: left;
  border: 0;
  border-right: 1px solid var(--color-border);
  background: transparent;
  cursor: pointer;
  transition: background-color 160ms ease, color 160ms ease;
}

.home-tools button:last-child {
  border-right: 0;
}

.home-tools button:hover {
  color: var(--color-brand);
  background: var(--color-bg-subtle);
}

.home-tools button > .el-icon:first-child {
  color: var(--color-text-muted);
  font-size: 16px;
}

.home-tools span {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.home-tools strong {
  font-size: 13px;
  font-weight: 650;
}

.home-tools small {
  overflow: hidden;
  margin-top: 2px;
  color: var(--color-text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-tools__arrow {
  color: var(--color-text-muted);
  font-size: 12px;
  transition: transform 160ms ease;
}

.home-tools button:hover .home-tools__arrow {
  transform: translateX(3px);
}

.home-section {
  min-width: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-surface);
}

.recent-learning {
  margin-top: 28px;
  padding: 22px 24px 24px;
}

.home-section__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.home-section__head h2 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
  line-height: 1.4;
}

.home-section__head p {
  margin: 4px 0 0;
  color: var(--color-text-muted);
  font-size: 12px;
}

.home-section__head > span {
  color: var(--color-text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.home-lower {
  display: grid;
  grid-template-columns: minmax(0, 1.75fr) minmax(320px, 0.75fr);
  align-items: start;
  gap: 18px;
  margin-top: 18px;
}

.home-training,
.home-community {
  padding: 20px 22px 22px;
}

@media (max-width: 1080px) {
  .continue-learning {
    grid-template-columns: 1fr;
  }

  .continue-learning__main {
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .continue-learning__facts {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-template-rows: none;
    padding: 0;
  }

  .continue-learning__facts > div {
    grid-template-columns: 1fr;
    padding: 18px 20px;
    border-right: 1px solid var(--color-border);
    border-bottom: 0;
  }

  .continue-learning__facts > div:last-child {
    border-right: 0;
  }

  .continue-learning__facts dt {
    grid-row: auto;
  }

  .home-lower {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .home-workspace {
    padding-bottom: 28px;
  }

  .continue-learning__main {
    padding: 23px 18px 22px;
  }

  .continue-learning__facts {
    grid-template-columns: 1fr;
  }

  .continue-learning__facts > div {
    grid-template-columns: 96px minmax(0, 1fr);
    padding: 15px 18px;
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .continue-learning__facts dt {
    grid-row: 1 / 3;
  }

  .continue-learning__actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .home-tools {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .home-tools button:nth-child(2) {
    border-right: 0;
  }

  .home-tools button:nth-child(-n + 2) {
    border-bottom: 1px solid var(--color-border);
  }

  .recent-learning,
  .home-training,
  .home-community {
    padding: 18px 15px;
  }
}

@media (max-width: 420px) {
  .continue-learning__actions {
    grid-template-columns: 1fr;
  }

  .home-tools button {
    grid-template-columns: 20px minmax(0, 1fr) 14px;
    padding: 14px 12px;
  }

  .home-tools small {
    white-space: normal;
  }
}

/* Reference-inspired student home: quiet surfaces, one strong learning focus. */
.home-page { padding-top: 4px; }
.study-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.62fr) minmax(420px, 0.98fr);
  min-height: 278px;
  overflow: hidden;
  border: 1px solid #dceceb;
  border-radius: 20px;
  background: linear-gradient(112deg, #fff 0%, #fbfefe 56%, #eff9f8 100%);
  box-shadow: 0 10px 28px rgba(28, 89, 90, 0.06), 0 2px 6px rgba(28, 89, 90, 0.035);
}
.study-hero__main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(250px, 0.82fr);
  align-items: center;
  min-width: 0;
  padding: 24px 28px 22px 32px;
}
.study-hero__copy { position: relative; z-index: 1; min-width: 0; }
.study-hero .section-kicker { margin-bottom: 10px; color: var(--color-brand); font-size: 13px; letter-spacing: 0.08em; }
.study-hero__title-row { display: flex; align-items: center; gap: 12px; min-width: 0; }
.study-hero h1 { margin: 0; color: #102c31; font-size: clamp(30px, 3.1vw, 40px); font-weight: 800; letter-spacing: -0.05em; line-height: 1.12; }
.study-hero__topic { flex: 0 0 auto; display: grid; width: 28px; height: 28px; padding: 0; place-items: center; color: var(--color-brand); font-size: 0; font-weight: 700; border: 1px solid #b9dedb; border-radius: 10px; background: rgba(234, 246, 245, 0.72); }
.study-hero__topic::before { content: '⌘'; font-size: 15px; }
.study-hero__section { margin: 10px 0 0; color: var(--color-text-secondary); font-size: 15px; font-weight: 600; }
.study-hero__advice { max-width: 31em; margin: 8px 0 0; color: var(--color-text-muted); font-size: 13px; line-height: 1.65; }
.study-hero .continue-learning__progress { max-width: 480px; margin-top: 22px; }
.study-hero .continue-learning__progress > div:first-child { margin-bottom: 9px; color: var(--color-text-muted); font-size: 12px; }
.study-hero .continue-learning__progress strong { color: var(--color-brand); font-size: 13px; }
.study-hero .progress-track { height: 8px; background: #e4efee; }
.study-hero .progress-track i { background: var(--color-brand); box-shadow: 0 0 0 1px rgba(15, 133, 136, 0.04), 0 2px 7px rgba(15, 133, 136, 0.18); animation: home-progress-in 700ms var(--alp-ease-out-expo, ease-out) both; }
.study-hero .continue-learning__actions { gap: 10px; margin-top: 22px; }
.study-hero .continue-learning__actions :deep(.el-button) { min-width: 152px; min-height: 44px; padding-inline: 17px; font-size: 15px; border-radius: 6px; transition: transform 200ms ease, box-shadow 200ms ease, background-color 200ms ease; }
.study-hero .continue-learning__actions :deep(.el-button:hover) { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(15, 133, 136, 0.14); }
.study-hero__visual { display: grid; min-height: 228px; place-items: center; overflow: hidden; }
.study-hero__visual img { width: min(100%, 340px); height: 254px; object-fit: contain; filter: drop-shadow(0 12px 12px rgba(15, 133, 136, .08)); }
.study-hero__status { display: grid; grid-template-columns: 78px 76px minmax(0, 1fr); align-content: center; gap: 10px 12px; min-width: 0; padding: 22px 32px 20px 30px; border-left: 1px solid rgba(196, 224, 222, 0.92); background: rgba(255, 255, 255, 0.54); }
.status-title { display: flex; align-items: center; color: var(--color-text-muted); font-size: 12px; font-weight: 650; }
.status-ring { position: relative; display: grid; width: 72px; height: 72px; place-items: center; }
.status-ring :deep(.el-progress-circle__track) { stroke: #e6eeee; }
.status-ring :deep(.el-progress-circle__path) { stroke: var(--color-brand); transition: stroke-dasharray 700ms var(--alp-ease-out-expo, ease-out); }
.status-ring strong { position: absolute; color: #233d42; font-size: 17px; font-weight: 760; }
.status-ring strong small { margin-left: 1px; color: var(--color-text-muted); font-size: 12px; }
.status-ring__label { display: flex; min-width: 0; flex-direction: column; justify-content: center; gap: 7px; }
.status-ring__label span, .study-hero__facts dt { color: var(--color-text-muted); font-size: 12px; }
.status-ring__label strong { color: var(--color-brand); font-size: 12px; line-height: 1.7; }
.study-hero__facts { grid-column: 1 / -1; margin: 3px 0 0; padding: 9px 0 0; border-top: 1px solid rgba(196, 224, 222, 0.85); }
.study-hero__facts > div { display: grid; grid-template-columns: 90px minmax(0, 1fr); gap: 3px 12px; padding: 10px 0; border-bottom: 1px solid rgba(221, 235, 234, 0.9); }
.study-hero__facts > div:last-child { border-bottom: 0; }
.study-hero__facts dd { overflow: hidden; margin: 0; color: #294147; font-size: 14px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.study-hero__facts dd small { color: var(--color-text-muted); font-size: 11px; font-weight: 500; }
.study-hero__facts small { grid-column: 2; color: var(--color-text-muted); font-size: 11px; }
.home-tools { gap: 14px; margin-top: 16px; border: 0; }
.home-tools button { grid-template-columns: 48px minmax(0, 1fr) 18px; gap: 12px; min-height: 82px; padding: 14px 18px; border: 1px solid var(--color-border); border-radius: 12px; background: var(--color-bg-surface); box-shadow: 0 4px 14px rgba(28, 89, 90, 0.035); transition: transform 220ms ease, border-color 220ms ease, box-shadow 220ms ease; }
.home-tools button:last-child, .home-tools button:nth-child(2) { border-right: 1px solid var(--color-border); }
.home-tools button:hover { color: var(--color-text-primary); border-color: #b7d9d7; background: var(--color-bg-surface); box-shadow: 0 10px 22px rgba(28, 89, 90, 0.08); transform: translateY(-3px); }
.home-tools__icon { display: grid; width: 46px; height: 46px; place-items: center; color: var(--color-brand); border: 1px solid #c7e4e1; border-radius: 14px; background: #eef9f7; transition: transform 220ms ease, background-color 220ms ease; }
.home-tools button:nth-child(1) .home-tools__icon { color: #4fa56a; background: #eff9e9; }
.home-tools button:nth-child(2) .home-tools__icon { color: #258bc3; background: #eaf6fd; }
.home-tools button:nth-child(3) .home-tools__icon { color: #168d8b; background: #e9f8f5; }
.home-tools button:nth-child(4) .home-tools__icon { color: #22a598; background: #e7f8f4; }
.home-tools button:hover .home-tools__icon { background: #e0f4f1; transform: translateX(3px); }
.home-tools button > span:nth-child(2) { display: flex; min-width: 0; flex-direction: column; gap: 4px; }
.home-tools strong { font-size: 14px; }
.home-tools small { color: var(--color-text-muted); font-size: 11px; }
.home-tools__arrow { transition: transform 220ms ease, color 220ms ease; }
.home-tools button:hover .home-tools__arrow { color: var(--color-brand); transform: translateX(4px); }
.learning-map, .home-section { border-radius: 14px; box-shadow: 0 6px 18px rgba(28, 89, 90, 0.035); }
.learning-map { margin-top: 18px; }
.learning-map__head { padding: 22px 26px 18px; }
.learning-map__head h2, .home-section__head h2 { font-size: 20px; font-weight: 750; }
.recent-learning { margin-top: 18px; }
@keyframes home-progress-in { from { transform: translateX(-12px) scaleX(0.86); transform-origin: left; } to { transform: translateX(0) scaleX(1); transform-origin: left; } }
@keyframes home-card-float { 0%, 100% { transform: rotate(-5deg) translateY(0); } 50% { transform: rotate(-5deg) translateY(-5px); } }
@keyframes home-orb-float { 0%, 100% { transform: translateY(0); opacity: 0.75; } 50% { transform: translateY(-6px); opacity: 1; } }
@media (max-width: 880px) {
  .study-hero { grid-template-columns: 1fr; }
  .study-hero__status { grid-template-columns: 108px minmax(0, 1fr); border-top: 1px solid rgba(196, 224, 222, 0.92); border-left: 0; }
  .study-hero__facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
  .study-hero__facts > div { display: block; padding: 0 18px 0 0; border-right: 1px solid rgba(221, 235, 234, 0.9); border-bottom: 0; }
  .study-hero__facts > div:last-child { padding-right: 0; border-right: 0; }
  .study-hero__facts dd { margin-top: 6px; }
  .study-hero__facts small { display: block; margin-top: 3px; }
}
@media (max-width: 760px) {
  .home-page { padding-bottom: 28px; }
  .study-hero__main { grid-template-columns: 1fr; padding: 24px 20px 18px; }
  .study-hero__visual { min-height: 190px; margin-top: 12px; }
  .study-hero__status { padding: 22px 20px 24px; }
  .home-tools { gap: 10px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-tools button:nth-child(2), .home-tools button:last-child { border-right: 1px solid var(--color-border); }
  .home-tools button { grid-template-columns: 36px minmax(0, 1fr) 14px; min-height: 74px; padding: 13px 12px; }
  .home-tools__icon { width: 34px; height: 34px; border-radius: 10px; }
  .study-hero__facts { grid-template-columns: 1fr; gap: 0; }
  .study-hero__facts > div, .study-hero__facts > div:last-child { padding: 10px 0; border-right: 0; border-bottom: 1px solid rgba(221, 235, 234, 0.9); }
  .study-hero__facts > div:last-child { border-bottom: 0; }
  .study-hero__facts dd { margin-top: 3px; }
  .recent-learning, .home-training, .home-community { padding: 18px 15px; }
}
@media (max-width: 420px) {
  .study-hero__title-row { display: block; }
  .study-hero__topic { display: inline-block; margin-top: 9px; }
  .study-hero .continue-learning__actions { display: grid; grid-template-columns: 1fr; }
  .home-tools { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .progress-track i,
  .home-tools button,
  .home-tools__arrow,
  .home-tools__icon,
  .study-hero__code-card,
  .study-hero__orb,
  .study-hero .continue-learning__actions :deep(.el-button) {
    transition: none;
    animation: none;
  }
}
</style>
