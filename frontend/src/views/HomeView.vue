<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { RouteLocationRaw } from 'vue-router'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRight, Calendar, Collection, Cpu, DataAnalysis, Document,
  Refresh, Timer, Trophy, VideoPlay,
} from '@element-plus/icons-vue'
import codingHeroUrl from '@/assets/home-coding-hero.png'
import HomeAiPipeline from '@/components/home/HomeAiPipeline.vue'
import HomeCommunityPanel from '@/components/home/HomeCommunityPanel.vue'
import HomeDashboardCharts from '@/components/home/HomeDashboardCharts.vue'
import HomeHitokotoBar from '@/components/home/HomeHitokotoBar.vue'
import HomeStageLearningMap from '@/components/home/HomeStageLearningMap.vue'
import HomeTrainingSection from '@/components/home/HomeTrainingSection.vue'
import { fetchCommunity, type CommunityResponse } from '@/api/analytics'
import { fetchProblems, type ProblemListItem } from '@/api/oj'
import { ALGORITHM_MODULES, MODULE_PHASE_LABELS, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { prefetchRoute } from '@/router/prefetch'
import { getUser } from '@/stores/auth'
import { getApiBaseUrl } from '@/utils/apiBase'
import { getHeatmapCells, getLast7DaySeries, touchTodayVisit } from '@/utils/homeActivityLog'
import {
  buildPlatformStats, buildReviewQueue, buildSkillRadar, formatRecentRelative,
  getRecentForHome, pickDailyProblem, pickTargetedProblems, type TrainingProblem,
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
const recommendationOffset = ref(0)

const ROUTE_TO_MODULE: Record<string, string> = Object.fromEntries(
  Object.entries(MODULE_ROUTE_NAMES).map(([key, name]) => [name as string, key]),
)

function syncActiveFromRoute() {
  const byName = ROUTE_TO_MODULE[route.name as string]
  if (byName) return void (activeModule.value = byName)
  if (route.name === 'learning-path' && typeof route.query.module === 'string') activeModule.value = route.query.module
}
watch(() => route.fullPath, syncActiveFromRoute, { immediate: true })

const overview = computed(() => buildLearningOverview())
const selectedModule = computed(() => ALGORITHM_MODULES.find((module) => module.key === activeModule.value) ?? ALGORITHM_MODULES[0])
const currentModule = computed(() => overview.value.nextModule ?? selectedModule.value ?? null)
const currentProgress = computed(() => overview.value.rows.find((row) => row.key === currentModule.value?.key) ?? null)
const currentPhaseLabel = computed(() => currentModule.value ? MODULE_PHASE_LABELS[currentModule.value.phase] : '学习路径')
const currentSectionLabel = computed(() => {
  const row = currentProgress.value
  if (!row?.totalCount) return '进入模块后查看章节目录'
  if (row.doneCount >= row.totalCount) return '本模块已完成，可以继续下一站'
  return `建议继续第 ${row.doneCount + 1} 个小节`
})
const completedSections = computed(() => overview.value.rows.reduce((total, row) => total + row.doneCount, 0))
const totalSections = computed(() => overview.value.rows.reduce((total, row) => total + row.totalCount, 0))
const recentVisits = computed(() => getRecentForHome())
const lastVisitLabel = computed(() => recentVisits.value[0] ? `${recentVisits.value[0].label} · ${formatRecentRelative(recentVisits.value[0].visitedAt)}` : '还没有最近学习记录')
const activitySeries = computed(() => getLast7DaySeries())
const heatmapCells = computed(() => getHeatmapCells(12))
const activityTotal = computed(() => activitySeries.value.reduce((total, day) => total + day.total, 0))
const activeDays = computed(() => activitySeries.value.filter((day) => day.total > 0).length)
const todayActivity = computed(() => activitySeries.value.at(-1)?.total ?? 0)
const skillRadar = computed(() => buildSkillRadar(overview.value.rows))
const reviewQueue = computed(() => buildReviewQueue())
const dailyProblem = computed(() => pickDailyProblem(ojProblems.value))
const targetedProblems = computed(() => pickTargetedProblems(overview.value.weakModules, ojProblems.value))
const platformStats = computed(() => {
  const base = buildPlatformStats(ojReadyCount.value)
  const stats = communityData.value?.stats
  return stats ? [
    ...base,
    { key: 'students', label: '注册学员', value: stats.student_count, suffix: ' 人' },
    { key: 'week_ac', label: '本周通过', value: stats.week_ac_count, suffix: ' 次' },
    { key: 'week_active', label: '本周活跃', value: stats.week_active_count, suffix: ' 人' },
  ] : base
})
const acBoard = computed(() => communityData.value?.ac_board ?? [])
const streakBoard = computed(() => communityData.value?.streak_board ?? [])
const username = computed(() => getUser()?.username || '学习者')
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '上午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const quickActions: Array<{ key: string; label: string; desc: string; icon: typeof Collection; route: RouteLocationRaw; prefetch: string }> = [
  { key: 'path', label: '学习路径', desc: '查看全部模块与学习顺序', icon: Collection, route: { name: 'learning-path' }, prefetch: '/learning-path' },
  { key: 'oj', label: '在线 OJ', desc: '进入 Python / C++ 判题练习', icon: Cpu, route: { name: 'practice-list' }, prefetch: '/practice' },
  { key: 'persona', label: '学习画像', desc: '查看掌握情况与学习建议', icon: DataAnalysis, route: { name: 'my-learning', query: { tab: 'persona' } }, prefetch: '/my-learning' },
  { key: 'resources', label: '学习资料', desc: '查找讲义、题单与参考资料', icon: Document, route: { name: 'resources' }, prefetch: '/resources' },
]

const metrics = computed(() => [
  { key: 'today', label: '今日学习', value: todayActivity.value, suffix: ' 分', note: todayActivity.value ? '今日已有学习记录' : '完成一次学习开始记录', icon: Timer, tone: 'cyan' },
  { key: 'days', label: '近周活跃', value: activeDays.value, suffix: ' 天', note: '近 7 天学习天数', icon: Calendar, tone: 'orange' },
  { key: 'mastery', label: '整体掌握', value: overview.value.overallPercent, suffix: '%', note: '按已学习模块汇总', icon: DataAnalysis, tone: 'teal' },
  { key: 'complete', label: '已完成', value: completedSections.value, suffix: ' 节', note: `共 ${totalSections.value || '—'} 个学习小节`, icon: Collection, tone: 'green' },
  { key: 'problems', label: '可练题目', value: ojReadyCount.value ?? '—', suffix: ' 道', note: healthStatus.value === 'ok' ? '在线 OJ 已同步' : '进入题库查看本地题目', icon: Cpu, tone: 'violet' },
  { key: 'review', label: '待复习', value: reviewQueue.value.length, suffix: ' 项', note: reviewQueue.value.length ? '按学习记录智能整理' : '当前节奏良好', icon: Trophy, tone: 'gold' },
])

type Recommendation =
  | { key: string; title: string; meta: string; kind: 'module'; target: string; tone: string }
  | { key: string; title: string; meta: string; kind: 'problem'; target: string; tone: string }

const recommendations = computed<Recommendation[]>(() => {
  const candidates: Recommendation[] = []
  if (currentModule.value) candidates.push({ key: `module-${currentModule.value.key}`, title: `${currentModule.value.label}核心知识`, meta: `${currentPhaseLabel.value} · 掌握度 ${currentProgress.value?.percent ?? 0}%`, kind: 'module', target: currentModule.value.key, tone: 'green' })
  const problems = [dailyProblem.value, ...targetedProblems.value].filter((item): item is TrainingProblem => Boolean(item))
  for (const problem of problems) {
    if (candidates.some((item) => item.key === `problem-${problem.slug}`)) continue
    candidates.push({ key: `problem-${problem.slug}`, title: problem.title, meta: `${problem.reason || '今日推荐'} · 约 ${problem.etaMin} 分钟`, kind: 'problem', target: problem.slug, tone: candidates.length % 2 ? 'orange' : 'violet' })
  }
  for (const row of overview.value.rows) {
    if (candidates.length >= 6) break
    if (row.key === currentModule.value?.key) continue
    candidates.push({ key: `module-${row.key}`, title: `${row.label}巩固练习`, meta: `${MODULE_PHASE_LABELS[row.phase]} · 掌握度 ${row.percent}%`, kind: 'module', target: row.key, tone: candidates.length % 2 ? 'orange' : 'violet' })
  }
  if (!candidates.length) return []
  return Array.from({ length: Math.min(3, candidates.length) }, (_, index) => candidates[(index + recommendationOffset.value) % candidates.length])
})

function previewModule(key: string) { activeModule.value = key }
function onModuleSelect(key: string) {
  activeModule.value = key
  const module = ALGORITHM_MODULES.find((item) => item.key === key)
  if (module) recordModuleVisit(key, module.label)
  const routeName = MODULE_ROUTE_NAMES[key]
  if (routeName) {
    prefetchRoute(`/learn/${key}`)
    void router.push({ name: routeName })
  } else void router.push({ name: 'learning-path', query: { module: key } })
}
function continueLearning() { currentModule.value ? onModuleSelect(currentModule.value.key) : void router.push({ name: 'learning-path' }) }
function goQuick(item: (typeof quickActions)[number]) { prefetchRoute(item.prefetch); void router.push(item.route) }
function openPractice(slug: string) { prefetchRoute(`/practice/${slug}`); void router.push({ name: 'practice-problem', params: { slug } }) }
function openRecommendation(item: Recommendation) { item.kind === 'problem' ? openPractice(item.target) : onModuleSelect(item.target) }
function rotateRecommendations() { recommendationOffset.value += 3 }

onMounted(async () => {
  touchTodayVisit()
  const base = getApiBaseUrl()
  try {
    const response = await fetch(base ? `${base}/api/health` : '/api/health')
    const data = response.ok ? ((await response.json()) as { status?: string }) : null
    healthStatus.value = data?.status === 'ok' ? 'ok' : 'error'
  } catch { healthStatus.value = 'error' }
  if (healthStatus.value !== 'ok') return
  void fetchProblems().then((list) => { ojProblems.value = list; ojReadyCount.value = list.filter((problem) => problem.ready).length }).catch(() => { ojProblems.value = []; ojReadyCount.value = null })
  void fetchCommunity().then((data) => { communityData.value = data }).catch(() => { communityData.value = null })
})
</script>

<template>
  <div class="home-workspace home-page">
    <section class="home-greeting" aria-label="学习问候">
      <div class="home-greeting__avatar" aria-hidden="true">{{ username.slice(0, 1).toUpperCase() }}</div>
      <div class="home-greeting__copy">
        <div class="home-greeting__headline">
          <h1>{{ greeting }}，{{ username }}</h1>
          <HomeHitokotoBar />
        </div>
        <p>今天是你的第 <strong>{{ Math.max(1, activeDays) }}</strong> 个活跃学习日，继续保持自己的节奏。</p>
      </div>
      <button type="button" @click="router.push({ name: 'my-learning' })">查看学习档案 <el-icon><ArrowRight /></el-icon></button>
    </section>

    <section class="hero-dashboard" aria-labelledby="continue-title">
      <article class="goal-card">
        <header><div><span class="section-kicker">本周学习目标</span><h2 id="continue-title">{{ overview.completedModules }} / {{ ALGORITHM_MODULES.length }} 个模块</h2></div><span>{{ currentModule?.label || '学习路径' }}</span></header>
        <div class="goal-card__progress"><div><span>当前模块完成度</span><strong>{{ currentProgress?.percent ?? 0 }}%</strong></div><div class="progress-track"><i :style="{ width: `${currentProgress?.percent ?? 0}%` }" /></div></div>
        <dl class="goal-card__facts"><div><dt>近周积分</dt><dd>{{ activityTotal }}</dd></div><div><dt>活跃天数</dt><dd>{{ activeDays }} 天</dd></div><div><dt>整体掌握</dt><dd>{{ overview.overallPercent }}%</dd></div></dl>
        <div class="goal-card__actions"><el-button type="primary" @click="continueLearning"><el-icon><VideoPlay /></el-icon>继续学习</el-button><el-button plain @click="router.push({ name: 'practice-list' })"><el-icon><Cpu /></el-icon>进入题库</el-button></div>
      </article>

      <div class="hero-visual"><div class="hero-visual__copy"><span>{{ currentPhaseLabel }}</span><strong>{{ currentModule?.label || '算法学习' }}</strong><small>{{ currentSectionLabel }}</small></div><img :src="codingHeroUrl" alt="青绿色三维代码学习装置" /></div>

      <aside class="recommend-card" aria-label="今日智能推荐">
        <header><div><span class="section-kicker">今日智能推荐</span><p>基于你的学习进度与薄弱点</p></div><span class="ai-label">AI</span></header>
        <div class="recommend-card__list">
          <button v-for="item in recommendations" :key="item.key" type="button" @click="openRecommendation(item)"><span class="recommend-card__mark" :class="`is-${item.tone}`"><el-icon><Collection /></el-icon></span><span><strong>{{ item.title }}</strong><small>{{ item.meta }}</small></span><span class="recommend-card__action">开始学习</span></button>
        </div>
        <button class="recommend-card__refresh" type="button" @click="rotateRecommendations"><el-icon><Refresh /></el-icon>换一批</button>
      </aside>
    </section>

    <nav class="home-tools" aria-label="常用学习工具">
      <button v-for="item in quickActions" :key="item.key" type="button" @mouseenter="prefetchRoute(item.prefetch)" @click="goQuick(item)"><span class="home-tools__icon"><el-icon><component :is="item.icon" /></el-icon></span><span><strong>{{ item.label }}</strong><small>{{ item.desc }}</small></span><el-icon class="home-tools__arrow"><ArrowRight /></el-icon></button>
    </nav>

    <section class="home-metrics" aria-label="学习指标">
      <article v-for="metric in metrics" :key="metric.key" :class="`metric-${metric.tone}`"><div><span>{{ metric.label }}</span><strong>{{ metric.value }}<small>{{ metric.suffix }}</small></strong><p>{{ metric.note }}</p></div><span class="home-metrics__icon"><el-icon><component :is="metric.icon" /></el-icon></span></article>
    </section>

    <HomeStageLearningMap :active-key="activeModule" :overall-percent="overview.overallPercent" @preview="previewModule" @open="onModuleSelect" />

    <section class="home-section recent-learning" aria-labelledby="recent-learning-title">
      <header class="home-section__head"><div><h2 id="recent-learning-title">学习数据总览</h2><p>{{ activityTotal ? `近 7 天累计 ${activityTotal} 学习积分，趋势来自真实访问与刷题记录。` : '完成一次学习或练习后，这里会形成你的趋势与能力画像。' }}</p></div><button type="button" @click="router.push({ name: 'my-learning' })">查看完整档案 <el-icon><ArrowRight /></el-icon></button></header>
      <HomeDashboardCharts :radar="skillRadar" :series="activitySeries" :heatmap="heatmapCells" />
    </section>

    <HomeAiPipeline :module-label="currentModule?.label || '算法学习'" :service-ready="healthStatus === 'ok'" @open-workbench="router.push({ name: 'agent-workbench' })" @open-resources="router.push({ name: 'resources' })" />

    <div class="home-lower">
      <section class="home-section home-training" aria-labelledby="training-title"><header class="home-section__head"><div><h2 id="training-title">接下来可以做</h2><p>根据今天的学习重点，给出可立即执行的下一步。</p></div><button type="button" @click="router.push({ name: 'practice-list' })">查看题库 <el-icon><ArrowRight /></el-icon></button></header><HomeTrainingSection :daily="dailyProblem" :targeted="targetedProblems" :review="reviewQueue" :recent="recentVisits" @open-problem="openPractice" @open-module="onModuleSelect" /></section>
      <aside class="home-section home-community" aria-labelledby="community-title"><header class="home-section__head"><div><h2 id="community-title">社区动态</h2><p>本周全站学习概况</p></div><span>{{ lastVisitLabel }}</span></header><HomeCommunityPanel :stats="platformStats" :ac-board="acBoard" :streak-board="streakBoard" /></aside>
    </div>
  </div>
</template>

<style scoped>
.home-workspace { --color-text-muted: #617477; --color-brand: #0b7477; --color-brand-hover: #09686b; --color-brand-soft: #eaf6f5; --el-color-primary: #0b7477; width: 100%; margin: 0 auto; padding: 4px 0 44px; color: var(--color-text-primary); }
.home-greeting { display: grid; grid-template-columns: 56px minmax(0, 1fr) auto; align-items: center; gap: 16px; padding: 4px 8px 18px; }
.home-greeting__avatar { display: grid; width: 54px; height: 54px; place-items: center; color: #17363c; font-size: 21px; font-weight: 800; border: 1px solid #badbd9; border-radius: 50%; background: rgba(255,255,255,.72); }
.home-greeting__copy { min-width: 0; }
.home-greeting__headline { display: flex; align-items: baseline; gap: 0; min-width: 0; }
.home-greeting h1 { flex: 0 0 auto; margin: 0; color: #102b31; font-size: 25px; font-weight: 780; letter-spacing: -.025em; }
.home-greeting p { margin: 5px 0 0; color: var(--color-text-muted); font-size: 14px; }
.home-greeting p strong { color: var(--color-brand); }
.home-greeting > button, .home-section__head > button { display: inline-flex; align-items: center; gap: 5px; padding: 8px 2px; color: var(--color-brand); font: inherit; font-size: 13px; font-weight: 700; border: 0; background: transparent; cursor: pointer; }
.hero-dashboard { display: grid; grid-template-columns: minmax(280px,.9fr) minmax(300px,.82fr) minmax(310px,.98fr); gap: 16px; min-height: 308px; }
.goal-card, .recommend-card, .home-section, .home-tools, .home-metrics article { border: 1px solid var(--color-border); border-radius: 14px; background: var(--color-bg-surface); box-shadow: 0 8px 26px rgba(27,80,81,.035); }
.goal-card { display: flex; flex-direction: column; padding: 22px 22px 20px; }
.goal-card > header, .recommend-card > header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.section-kicker { color: #18343a; font-size: 15px; font-weight: 760; }
.goal-card > header > span { color: var(--color-text-muted); font-size: 12px; }
.goal-card h2 { margin: 25px 0 0; color: #0f2930; font-size: clamp(24px,2.3vw,31px); letter-spacing: -.035em; }
.goal-card__progress { margin-top: 19px; }
.goal-card__progress > div:first-child { display: flex; justify-content: space-between; margin-bottom: 8px; color: var(--color-text-muted); font-size: 12px; }
.goal-card__progress strong { color: var(--color-brand); font-size: 13px; }
.progress-track { height: 6px; overflow: hidden; border-radius: 99px; background: #e4efee; }
.progress-track i { display: block; height: 100%; border-radius: inherit; background: var(--color-brand); transition: width 420ms ease; }
.goal-card__facts { display: grid; grid-template-columns: repeat(3,1fr); margin: 20px 0 0; padding: 17px 0 0; border-top: 1px solid var(--color-border); }
.goal-card__facts div { padding: 0 12px; border-right: 1px solid var(--color-border); }
.goal-card__facts div:first-child { padding-left: 0; } .goal-card__facts div:last-child { padding-right: 0; border-right: 0; }
.goal-card__facts dt { color: var(--color-text-muted); font-size: 11px; } .goal-card__facts dd { margin: 6px 0 0; color: #18343a; font-size: 17px; font-weight: 760; font-variant-numeric: tabular-nums; }
.goal-card__actions { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: auto; padding-top: 18px; }
.goal-card__actions :deep(.el-button) { width: 100%; min-height: 40px; margin: 0; border-radius: 8px; }
.goal-card__actions :deep(.el-button--primary) { border-color: #0b7477; background: #0b7477; }
.hero-visual { position: relative; display: grid; min-width: 0; place-items: center; overflow: hidden; border-radius: 18px; background: radial-gradient(circle at 50% 45%,rgba(100,220,213,.16),transparent 58%); }
.hero-visual::after { content: ''; position: absolute; inset: auto 8% 20px; height: 28px; border-radius: 50%; background: rgba(58,160,160,.12); filter: blur(16px); }
.hero-visual img { position: relative; z-index: 1; width: min(100%,328px); height: 284px; object-fit: contain; filter: drop-shadow(0 14px 16px rgba(30,126,127,.08)); }
.hero-visual__copy { position: absolute; top: 13px; left: 0; z-index: 2; display: flex; flex-direction: column; max-width: 145px; }
.hero-visual__copy span { color: var(--color-brand); font-size: 11px; font-weight: 750; } .hero-visual__copy strong { margin-top: 3px; color: #14343a; font-size: 18px; } .hero-visual__copy small { margin-top: 4px; color: var(--color-text-muted); font-size: 11px; line-height: 1.5; }
.recommend-card { display: flex; flex-direction: column; padding: 21px 20px 13px; }
.recommend-card header p { margin: 6px 0 0; color: var(--color-text-muted); font-size: 12px; }
.ai-label { padding: 3px 7px; color: #176aa6; font-size: 11px; font-weight: 800; border-radius: 6px; background: #e9f5ff; }
.recommend-card__list { display: grid; margin-top: 12px; }
.recommend-card__list > button { display: grid; grid-template-columns: 34px minmax(0,1fr) auto; align-items: center; gap: 10px; min-height: 58px; padding: 9px 0; color: var(--color-text-primary); text-align: left; border: 0; border-bottom: 1px solid var(--color-border); background: transparent; cursor: pointer; }
.recommend-card__list > button:hover strong { color: var(--color-brand); }
.recommend-card__mark { display: grid; width: 30px; height: 30px; place-items: center; color: var(--color-brand); border: 1px solid #b9d7d4; border-radius: 50%; background: #eff9f7; }
.recommend-card__mark.is-orange { color: #e98a2f; border-color: #f3cfaa; background: #fff7ed; } .recommend-card__mark.is-violet { color: #8264d4; border-color: #d9cff5; background: #f5f1ff; }
.recommend-card__list span:nth-child(2) { display: flex; min-width: 0; flex-direction: column; }
.recommend-card__list strong, .recommend-card__list small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recommend-card__list strong { font-size: 13px; font-weight: 700; transition: color 160ms ease; } .recommend-card__list small { margin-top: 4px; color: var(--color-text-muted); font-size: 11px; }
.recommend-card__action { padding: 6px 9px; color: var(--color-brand); font-size: 11px; font-weight: 700; white-space: nowrap; border: 1px solid #b9deda; border-radius: 99px; }
.recommend-card__refresh { display: inline-flex; align-items: center; align-self: center; gap: 5px; margin-top: auto; padding: 10px 12px 0; color: var(--color-text-muted); font: inherit; font-size: 11px; border: 0; background: transparent; cursor: pointer; }
.recommend-card__refresh:hover { color: var(--color-brand); }
.home-tools { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); margin-top: 16px; overflow: hidden; }
.home-tools button { display: grid; grid-template-columns: 36px minmax(0,1fr) 16px; align-items: center; gap: 10px; min-width: 0; padding: 13px 16px; color: var(--color-text-primary); text-align: left; border: 0; border-right: 1px solid var(--color-border); background: transparent; cursor: pointer; transition: color 160ms ease,background 160ms ease; }
.home-tools button:last-child { border-right: 0; } .home-tools button:hover { color: var(--color-brand); background: var(--color-bg-subtle); }
.home-tools__icon { display: grid; width: 34px; height: 34px; place-items: center; color: var(--color-brand); border: 1px solid #c4e0de; border-radius: 11px; background: #eaf8f6; }
.home-tools button:nth-child(2) .home-tools__icon { color: #228dcc; border-color: #c8e1f0; background: #edf8fc; } .home-tools button:nth-child(3) .home-tools__icon { color: #8366d7; border-color: #ded4f5; background: #f4f0ff; }
.home-tools span:nth-child(2) { display: flex; min-width: 0; flex-direction: column; } .home-tools strong { font-size: 13px; } .home-tools small { overflow: hidden; margin-top: 3px; color: var(--color-text-muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.home-tools__arrow { color: var(--color-text-muted); font-size: 11px; transition: transform 160ms ease; } .home-tools button:hover .home-tools__arrow { transform: translateX(3px); }
.home-metrics { display: grid; grid-template-columns: repeat(6,minmax(0,1fr)); gap: 12px; margin-top: 16px; }
.home-metrics article { display: grid; grid-template-columns: minmax(0,1fr) 40px; align-items: center; gap: 8px; min-height: 88px; padding: 15px; }
.home-metrics article > div { display: flex; min-width: 0; flex-direction: column; } .home-metrics article span:first-child { color: var(--color-text-muted); font-size: 11px; }
.home-metrics article strong { margin-top: 5px; color: #153239; font-size: 22px; line-height: 1; font-variant-numeric: tabular-nums; } .home-metrics article strong small { font-size: 11px; font-weight: 600; }
.home-metrics article p { overflow: hidden; margin: 6px 0 0; color: var(--color-text-muted); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.home-metrics__icon { display: grid; width: 38px; height: 38px; place-items: center; color: var(--color-brand); font-size: 20px; border-radius: 13px; background: #e9f8f5; }
.metric-orange .home-metrics__icon { color: #ef8737; background: #fff2e8; } .metric-violet .home-metrics__icon { color: #8265d4; background: #f1edff; } .metric-gold .home-metrics__icon { color: #d99713; background: #fff7dc; } .metric-green .home-metrics__icon { color: #2ca66d; background: #eaf8ef; }
.home-section { min-width: 0; } .recent-learning { margin-top: 18px; padding: 20px 22px 22px; }
.home-section__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 16px; } .home-section__head h2 { margin: 0; color: #102b31; font-size: 20px; line-height: 1.4; } .home-section__head p { margin: 4px 0 0; color: var(--color-text-muted); font-size: 12px; } .home-section__head > span { overflow: hidden; max-width: 190px; color: var(--color-text-muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.home-lower { display: grid; grid-template-columns: minmax(0,1.75fr) minmax(300px,.72fr); align-items: start; gap: 16px; margin-top: 16px; } .home-training, .home-community { padding: 19px 20px 21px; }
@media (min-width: 1800px) {
  .home-workspace { padding-top: 8px; }
  .home-greeting { grid-template-columns: 64px minmax(0,1fr) auto; gap: 19px; padding: 6px 10px 22px; }
  .home-greeting__avatar { width: 60px; height: 60px; font-size: 23px; }
  .home-greeting h1 { font-size: 28px; }
  .home-greeting p { margin-top: 7px; font-size: 15px; }
  .home-greeting > button, .home-section__head > button { gap: 6px; font-size: 14px; }
  .hero-dashboard { grid-template-columns: minmax(360px,.92fr) minmax(360px,.84fr) minmax(400px,1fr); gap: 20px; min-height: 340px; }
  .goal-card { padding: 26px 27px 23px; }
  .goal-card > header, .recommend-card > header { gap: 18px; }
  .section-kicker { font-size: 16px; }
  .goal-card > header > span { font-size: 13px; }
  .goal-card h2 { margin-top: 27px; font-size: 34px; }
  .goal-card__progress { margin-top: 21px; }
  .goal-card__progress > div:first-child { font-size: 13px; }
  .goal-card__progress strong { font-size: 14px; }
  .progress-track { height: 7px; }
  .goal-card__facts { margin-top: 22px; padding-top: 19px; }
  .goal-card__facts dt { font-size: 12px; }
  .goal-card__facts dd { font-size: 19px; }
  .goal-card__actions { gap: 11px; padding-top: 20px; }
  .goal-card__actions :deep(.el-button) { min-height: 44px; font-size: 14px; }
  .hero-visual img { width: min(100%,370px); height: 318px; }
  .hero-visual__copy { top: 17px; max-width: 170px; }
  .hero-visual__copy span, .hero-visual__copy small { font-size: 12px; }
  .hero-visual__copy strong { font-size: 20px; }
  .recommend-card { padding: 25px 25px 16px; }
  .recommend-card header p { font-size: 13px; }
  .ai-label { padding: 4px 8px; font-size: 12px; }
  .recommend-card__list { margin-top: 14px; }
  .recommend-card__list > button { grid-template-columns: 38px minmax(0,1fr) auto; gap: 12px; min-height: 64px; padding: 10px 0; }
  .recommend-card__mark { width: 34px; height: 34px; font-size: 17px; }
  .recommend-card__list strong { font-size: 14px; }
  .recommend-card__list small, .recommend-card__action, .recommend-card__refresh { font-size: 12px; }
  .recommend-card__action { padding: 7px 11px; }
  .home-tools { margin-top: 20px; }
  .home-tools button { grid-template-columns: 42px minmax(0,1fr) 18px; gap: 12px; padding: 16px 20px; }
  .home-tools__icon { width: 40px; height: 40px; font-size: 19px; }
  .home-tools strong { font-size: 14px; }
  .home-tools small, .home-tools__arrow { font-size: 12px; }
  .home-metrics { gap: 15px; margin-top: 20px; }
  .home-metrics article { grid-template-columns: minmax(0,1fr) 46px; gap: 10px; min-height: 102px; padding: 18px; }
  .home-metrics article span:first-child { font-size: 12px; }
  .home-metrics article strong { font-size: 25px; }
  .home-metrics article strong small { font-size: 12px; }
  .home-metrics article p { margin-top: 7px; font-size: 11px; }
  .home-metrics__icon { width: 44px; height: 44px; font-size: 22px; }
  .recent-learning { margin-top: 22px; padding: 24px 27px 27px; }
  .home-section__head { margin-bottom: 19px; }
  .home-section__head h2 { font-size: 22px; }
  .home-section__head p { font-size: 13px; }
  .home-section__head > span { max-width: 230px; font-size: 12px; }
  .home-lower { gap: 20px; margin-top: 20px; }
  .home-training, .home-community { padding: 23px 25px 25px; }
}
@media (max-width: 1180px) { .hero-dashboard { grid-template-columns: 1fr .9fr; } .recommend-card { grid-column: 1/-1; } .recommend-card__list { grid-template-columns: repeat(3,minmax(0,1fr)); gap: 14px; } .recommend-card__list > button { border-bottom: 0; } .recommend-card__refresh { margin-top: 8px; } .home-metrics { grid-template-columns: repeat(3,minmax(0,1fr)); } .home-lower { grid-template-columns: 1fr; } }
@media (max-width: 820px) { .home-greeting { grid-template-columns: 48px minmax(0,1fr); } .home-greeting__avatar { width: 46px; height: 46px; } .home-greeting > button { display: none; } .hero-dashboard { grid-template-columns: 1fr; } .hero-visual { min-height: 250px; grid-row: 1; } .hero-visual__copy { left: 18px; } .recommend-card { grid-column: auto; } .recommend-card__list { grid-template-columns: 1fr; gap: 0; } .recommend-card__list > button { border-bottom: 1px solid var(--color-border); } .home-tools { grid-template-columns: repeat(2,minmax(0,1fr)); } .home-tools button:nth-child(2) { border-right: 0; } .home-tools button:nth-child(-n+2) { border-bottom: 1px solid var(--color-border); } .home-metrics { grid-template-columns: repeat(2,minmax(0,1fr)); } }
@media (max-width: 520px) { .home-workspace { padding-bottom: 28px; } .home-greeting { padding-inline: 2px; } .home-greeting h1 { font-size: 21px; } .home-greeting p { font-size: 13px; line-height: 1.5; } .goal-card,.recommend-card { padding-inline: 17px; } .goal-card__actions { grid-template-columns: 1fr; } .home-tools { grid-template-columns: 1fr; } .home-tools button,.home-tools button:nth-child(2) { border-right: 0; border-bottom: 1px solid var(--color-border); } .home-tools button:last-child { border-bottom: 0; } .home-metrics { gap: 9px; } .home-metrics article { grid-template-columns: 1fr; min-height: 104px; padding: 13px; } .home-metrics__icon { grid-row: 1; width: 32px; height: 32px; font-size: 16px; } .recent-learning,.home-training,.home-community { padding: 17px 14px; } .home-section__head { gap: 10px; } .home-section__head > button { white-space: nowrap; } }
@media (prefers-reduced-motion: reduce) { .progress-track i,.home-tools__arrow { transition: none; } }
</style>
