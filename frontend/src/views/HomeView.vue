<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Fold,
  Expand,
  ChatDotRound,
  Reading,
  Cpu,
  Trophy,
  ArrowRight,
  Timer,
  Connection,
} from '@element-plus/icons-vue'
import AlgorithmLearningMap from '@/components/learning/AlgorithmLearningMap.vue'
import ModuleGameEntry from '@/components/learning/ModuleGameEntry.vue'
import HomeAnnounceBar from '@/components/home/HomeAnnounceBar.vue'
import HomeDashboardCharts from '@/components/home/HomeDashboardCharts.vue'
import HomeCommunityPanel from '@/components/home/HomeCommunityPanel.vue'
import HomeTrainingSection from '@/components/home/HomeTrainingSection.vue'
import HomeStageLearningMap from '@/components/home/HomeStageLearningMap.vue'
import HomeSortDemo from '@/components/home/HomeSortDemo.vue'
import { ALGORITHM_MODULES, MODULE_PHASE_LABELS, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { getApiBaseUrl } from '@/utils/apiBase'
import { buildLearningOverview } from '@/utils/learningOverview'
import { prefetchRoute } from '@/router/prefetch'
import { fetchProblems, type ProblemListItem } from '@/api/oj'
import { fetchCommunity, type CommunityResponse } from '@/api/analytics'
import { touchTodayVisit, getLast7DaySeries, getHeatmapCells } from '@/utils/homeActivityLog'
import {
  buildSkillRadar,
  buildPlatformStats,
  buildReviewQueue,
  enrichResources,
  getRecentForHome,
  pickDailyProblem,
  pickTargetedProblems,
} from '@/utils/homeDashboard'
import { recordModuleVisit } from '@/utils/learningBookmarks'
import RecommendedResourcesPanel from '@/components/learning/RecommendedResourcesPanel.vue'
import { isLoggedIn } from '@/stores/auth'
import heroLayerSrc from '@/assets/hero.png'
// GSAP entrance animations
import { useStaggerIn, useFadeSlideIn, useScrollReveal, initGsapDefaults, useHeroEntrance, useCardStagger } from '@/composables/useGsapAnimations'

// GSAP animation refs
const heroRef = ref<HTMLElement | null>(null)
const statsRef = ref<HTMLElement | null>(null)
const phasesRef = ref<HTMLElement | null>(null)
const quickActionsRef = ref<HTMLElement | null>(null)
const trainingRef = ref<HTMLElement | null>(null)
const analyticsRef = ref<HTMLElement | null>(null)
const resourcesRef = ref<HTMLElement | null>(null)
const vizRef = ref<HTMLElement | null>(null)

// GSAP - visible entrance animations (run on mount)
initGsapDefaults()
useFadeSlideIn(heroRef, { y: 30, duration: 0.9, ease: 'power3.out' })
useStaggerIn(statsRef, '.stat-card', { stagger: 0.12, y: 20, duration: 0.6 })
useScrollReveal(phasesRef, { y: 30, duration: 0.7, stagger: 0.08, start: 'top 82%' })
useScrollReveal(quickActionsRef, { y: 24, duration: 0.6, stagger: 0.07, start: 'top 83%' })
useScrollReveal(trainingRef, { y: 28, duration: 0.6, start: 'top 82%' })
useScrollReveal(analyticsRef, { y: 24, duration: 0.5, stagger: 0.06, start: 'top 83%' })
useScrollReveal(resourcesRef, { y: 24, duration: 0.5, stagger: 0.06, start: 'top 84%' })
useScrollReveal(vizRef, { y: 24, duration: 0.5, start: 'top 85%' })
// Visible entrance: hero children stagger in sequence
useHeroEntrance(heroRef, { delay: 0.15, duration: 0.6 })
useCardStagger(quickActionsRef, '.quick-action-card', { stagger: 0.1, y: 25, duration: 0.5 })


const router = useRouter()
const route = useRoute()

const asideCollapsed = ref(false)

const activeModule = ref<string>(ALGORITHM_MODULES[0]?.key ?? 'array')

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

const progressSummary = computed(() => ({
  overallPercent: overview.value.overallPercent,
  strong: overview.value.strongModules.map((m) => m.label),
  weak: overview.value.weakModules.map((m) => m.label),
  tracked: overview.value.trackedModules,
  completed: overview.value.completedModules,
}))

const phaseGroups = computed(() =>
  (Object.keys(MODULE_PHASE_LABELS) as Array<keyof typeof MODULE_PHASE_LABELS>).map((phase) => ({
    phase,
    label: MODULE_PHASE_LABELS[phase],
    modules: ALGORITHM_MODULES.filter((m) => m.phase === phase),
  })),
)

const selectedModule = computed(
  () => ALGORITHM_MODULES.find((m) => m.key === activeModule.value) ?? ALGORITHM_MODULES[0],
)

const selectedPhaseLabel = computed(() => {
  const phase = selectedModule.value?.phase
  return phase ? MODULE_PHASE_LABELS[phase] : '学习路径'
})

const selectedModuleProgress = computed(() =>
  selectedModule.value ? progressFor(selectedModule.value.key) : 0,
)

const serviceStatusLabel = computed(() => {
  if (healthStatus.value === 'checking') return '服务检测中'
  return healthStatus.value === 'ok' ? '学习服务正常' : '离线模式可用'
})

function progressFor(key: string) {
  return overview.value.rows.find((row) => row.key === key)?.percent ?? 0
}

const hasRealProgress = computed(() => overview.value.trackedModules > 0)

const quickActions = [
  {
    key: 'path',
    label: '学习路径',
    desc: '按阶段规划模块顺序',
    icon: Reading,
    route: { name: 'learning-path' as const },
    prefetch: '/learning-path',
  },
  {
    key: 'oj',
    label: '在线 OJ',
    desc: 'Python / C++ 判题练习',
    icon: Cpu,
    route: { name: 'practice-list' as const },
    prefetch: '/practice',
  },
  {
    key: 'persona',
    label: '学习画像',
    desc: '对话式个性化起点',
    icon: ChatDotRound,
    route: { name: 'my-learning' as const, query: { tab: 'persona' } },
    prefetch: '/my-learning',
  },
]

function onModuleSelect(key: string) {
  activeModule.value = key
  const mod = ALGORITHM_MODULES.find((m) => m.key === key)
  if (mod) recordModuleVisit(key, mod.label)
  const routeName = MODULE_ROUTE_NAMES[key]
  if (routeName) {
    const learnPath = `/learn/${key}`
    prefetchRoute(learnPath)
    router.push({ name: routeName })
    return
  }
  router.push({
    name: 'learning-path',
    query: { module: key },
  })
}

function previewModule(key: string) {
  activeModule.value = key
}

function continueLearning() {
  const next = overview.value.nextModule
  if (!next) {
    router.push({ name: 'learning-path' })
    return
  }
  onModuleSelect(next.key)
}

function goQuick(route: (typeof quickActions)[number]['route'], prefetch?: string) {
  if (prefetch) prefetchRoute(prefetch)
  router.push(route)
}

const healthStatus = ref<'checking' | 'ok' | 'error'>('checking')
const ojReadyCount = ref<number | null>(null)
const ojProblems = ref<ProblemListItem[]>([])
const communityData = ref<CommunityResponse | null>(null)

const skillRadar = computed(() => buildSkillRadar(overview.value.rows))
const activitySeries = computed(() => getLast7DaySeries())
const heatmapCells = computed(() => getHeatmapCells(12))
const platformStats = computed(() => {
  const base = buildPlatformStats(ojReadyCount.value)
  const c = communityData.value
  if (!c || !c.stats) return base
  return [
    ...base,
    { key: 'students', label: '注册学员', value: c.stats.student_count, suffix: ' 人' },
    { key: 'resources', label: '生成资源', value: c.stats.resource_count, suffix: ' 条' },
    { key: 'week_ac', label: '本周 AC', value: c.stats.week_ac_count, suffix: ' 次' },
    { key: 'week_active', label: '本周活跃', value: c.stats.week_active_count, suffix: ' 人' },
  ]
})
const acBoard = computed(() => communityData.value?.ac_board ?? [])
const streakBoard = computed(() => communityData.value?.streak_board ?? [])
const dailyProblem = computed(() => pickDailyProblem(ojProblems.value))
const targetedProblems = computed(() =>
  pickTargetedProblems(overview.value.weakModules, ojProblems.value),
)
const reviewQueue = computed(() => buildReviewQueue())
const recentVisits = computed(() => getRecentForHome())

const recommendedRaw = [
  {
    id: '1',
    title: '动态规划入门讲解',
    module: '动态规划',
    desc: '从记忆化搜索到状态转移，配合经典例题拆解思路。',
  },
  {
    id: '2',
    title: '双指针高频题单',
    module: '双指针法',
    desc: '覆盖有序数组、链表判环等模板，适合赛前冲刺。',
  },
  {
    id: '3',
    title: '单调栈专题精讲',
    module: '单调栈',
    desc: '下一个更大元素、柱状图等经典模型的统一框架。',
  },
  {
    id: '4',
    title: '二叉树递归与迭代',
    module: '二叉树',
    desc: '统一遍历框架，帮助你快速识别子问题结构。',
  },
]

const recommended = computed(() => enrichResources(recommendedRaw))

function openPractice(slug: string) {
  prefetchRoute(`/practice/${slug}`)
  router.push({ name: 'practice-problem', params: { slug } })
}

onMounted(async () => {
  touchTodayVisit()
  const base = getApiBaseUrl()
  const healthUrl = base ? `${base}/api/health` : '/api/health'
  try {
    const res = await fetch(healthUrl)
    if (!res.ok) {
      healthStatus.value = 'error'
    } else {
      const data = (await res.json()) as { status?: string }
      healthStatus.value = data?.status === 'ok' ? 'ok' : 'error'
    }
  } catch {
    healthStatus.value = 'error'
  }

  void fetchProblems()
    .then((list) => {
      ojProblems.value = list
      ojReadyCount.value = list.filter((p) => p.ready).length
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
  <div class="dashboard-home">
    <header class="dashboard-welcome">
      <div class="dashboard-welcome-copy">
        <p class="dashboard-eyebrow">学习总览</p>
        <h1>{{ overview.nextModule ? `继续学习：${overview.nextModule?.label}` : '今天想学点什么？' }}</h1>
        <p>{{ hasRealProgress ? `已学习 ${progressSummary.tracked} 个模块，保持现在的节奏。` : '从基础模块开始，完成第一节学习。' }}</p>
        <div class="dashboard-context" aria-label="当前学习状态">
          <span>
            <i class="dashboard-status-dot" :class="`is-${healthStatus}`" />
            {{ serviceStatusLabel }}
          </span>
          <span>已追踪 {{ progressSummary.tracked }} 个模块</span>
          <span>待复习 {{ reviewQueue.length }} 项</span>
        </div>
      </div>
      <div class="dashboard-welcome-side">
        <div class="dashboard-focus-summary">
          <div class="dashboard-focus-head">
            <span><el-icon><Timer /></el-icon> 今日焦点</span>
            <b>{{ selectedModuleProgress }}%</b>
          </div>
          <strong>{{ selectedModule?.label ?? '选择学习模块' }}</strong>
          <small>{{ selectedPhaseLabel }} · 建议专注 20 分钟</small>
          <div class="dashboard-focus-track" aria-hidden="true">
            <i :style="{ width: `${selectedModuleProgress}%` }" />
          </div>
        </div>
        <div class="dashboard-welcome-actions">
          <el-button type="primary" :icon="ArrowRight" @click="continueLearning">继续学习</el-button>
          <el-button :icon="Cpu" @click="router.push({ name: 'practice-list' })">进入题库</el-button>
        </div>
      </div>
    </header>

    <nav class="dashboard-shortcuts" aria-label="常用功能">
      <button v-for="item in quickActions" :key="item.key" type="button" @mouseenter="prefetchRoute(item.prefetch)" @click="goQuick(item.route, item.prefetch)">
        <el-icon><component :is="item.icon" /></el-icon>
        <span><strong>{{ item.label }}</strong><small>{{ item.desc }}</small></span>
        <el-icon class="dashboard-shortcut-arrow"><ArrowRight /></el-icon>
      </button>
      <button type="button" @click="router.push({ name: 'resources' })">
        <el-icon><Reading /></el-icon>
        <span><strong>学习资料</strong><small>讲义、题单与参考资料</small></span>
        <el-icon class="dashboard-shortcut-arrow"><ArrowRight /></el-icon>
      </button>
    </nav>

    <HomeStageLearningMap
      :active-key="activeModule"
      :overall-percent="progressSummary.overallPercent"
      @preview="previewModule"
      @open="onModuleSelect"
    />

    <div class="dashboard-columns">
      <main class="dashboard-primary">
        <section class="dashboard-panel dashboard-analytics">
          <div class="dashboard-panel-head"><div><h2>数据可视化与进度反馈</h2><p>最近学习情况与知识点掌握度</p></div><span class="dashboard-updated">本地实时更新</span></div>
          <HomeDashboardCharts :radar="skillRadar" :series="activitySeries" :heatmap="heatmapCells" />
        </section>
        <section class="dashboard-panel dashboard-training">
          <div class="dashboard-panel-head"><div><h2>每日训练推荐</h2><p>从一题开始，复习薄弱知识点</p></div><el-button text type="primary" @click="router.push({ name: 'practice-list' })">查看题库</el-button></div>
          <HomeTrainingSection :daily="dailyProblem" :targeted="targetedProblems" :review="reviewQueue" :recent="recentVisits" @open-problem="openPractice" @open-module="onModuleSelect" />
        </section>
        <section class="dashboard-panel dashboard-progress-panel">
          <div class="dashboard-panel-head"><div><h2>学习进度概览</h2><p>按阶段查看各模块完成情况</p></div><strong class="dashboard-percent">{{ progressSummary.overallPercent }}%</strong></div>
          <div class="dashboard-progress-track"><i :style="{ width: `${progressSummary.overallPercent}%` }" /></div>
          <div class="dashboard-selected-module" aria-live="polite">
            <div class="dashboard-selected-copy">
              <span>当前章节</span>
              <strong>{{ selectedModule?.label }}</strong>
              <small>{{ selectedModule?.available ? '课程内容已开放' : '已加入学习路径，内容持续完善中' }}</small>
            </div>
            <div class="dashboard-selected-progress">
              <div><span>章节进度</span><strong>{{ selectedModule ? progressFor(selectedModule.key) : 0 }}%</strong></div>
              <div class="dashboard-selected-track"><i :style="{ width: `${selectedModule ? progressFor(selectedModule.key) : 0}%` }" /></div>
            </div>
            <el-button type="primary" plain :icon="ArrowRight" :disabled="!selectedModule" @click="selectedModule && onModuleSelect(selectedModule.key)">打开章节</el-button>
          </div>
          <div class="dashboard-module-groups">
            <div v-for="group in phaseGroups" :key="group.phase" class="dashboard-module-group">
              <span>{{ group.label }}</span>
              <div><button v-for="module in group.modules" :key="module.key" type="button" :class="{ done: progressFor(module.key) === 100, active: activeModule === module.key }" :aria-pressed="activeModule === module.key" @mouseenter="activeModule = module.key" @focus="activeModule = module.key" @click="activeModule = module.key">{{ module.label }} <small>{{ progressFor(module.key) }}%</small></button></div>
            </div>
          </div>
        </section>
      </main>

      <aside class="dashboard-secondary">
        <section class="dashboard-panel dashboard-community">
          <div class="dashboard-panel-head"><div><h2>社区与全站数据</h2><p>本周学习动态</p></div></div>
          <HomeCommunityPanel :stats="platformStats" :ac-board="acBoard" :streak-board="streakBoard" />
        </section>
        <section class="dashboard-panel dashboard-resources">
          <div class="dashboard-panel-head"><div><h2>推荐资源</h2><p>与你当前进度相关</p></div><el-button text type="primary" size="small" @click="router.push({ name: 'resources' })">更多</el-button></div>
          <RecommendedResourcesPanel v-if="isLoggedIn" :limit="5" />
          <div v-else class="dashboard-resource-list"><button v-for="item in recommended.slice(0, 4)" :key="item.id" type="button" @click="router.push({ name: 'resources', query: { highlight: item.id } })"><span>{{ item.title }}</span><small>{{ item.module }}</small></button></div>
        </section>
        <section class="dashboard-panel dashboard-continue">
          <div class="dashboard-panel-head"><div><h2>继续学习</h2><p>回到最近访问的内容</p></div></div>
          <button v-if="overview.nextModule" type="button" class="dashboard-continue-item" @click="continueLearning"><span><strong>{{ overview.nextModule?.label }}</strong><small>接着上次的位置继续</small></span><el-icon><ArrowRight /></el-icon></button>
          <button type="button" class="dashboard-continue-item" @click="router.push({ name: 'practice-list' })"><span><strong>在线 OJ</strong><small>{{ ojReadyCount == null ? '打开题库' : `${ojReadyCount} 道题可练` }}</small></span><el-icon><ArrowRight /></el-icon></button>
        </section>
      </aside>
    </div>
  </div>
  <div v-if="false" class="home-page">
    <section ref="heroRef" class="home-hero">
      <div class="hero-copy">
        <p class="hero-kicker">今天从这里开始</p>
        <h1 class="hero-title">{{ overview.nextModule ? `继续学习 ${overview.nextModule?.label}` : '选择一个模块开始学习' }}</h1>
        <p class="hero-desc">
          {{ hasRealProgress ? `当前总进度 ${progressSummary.overallPercent}%，已完成 ${progressSummary.completed} 个模块。` : '按推荐顺序学习，也可以直接进入题库练习。' }}
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" :icon="ArrowRight" @click="continueLearning">
            {{ overview.nextModule ? '继续上次学习' : '查看学习路径' }}
          </el-button>
          <el-button
            size="large"
            plain
            :icon="Cpu"
            @mouseenter="prefetchRoute('/practice')"
            @click="router.push({ name: 'practice-list' })"
          >
            去做题
          </el-button>
        </div>
      </div>

      <div class="hero-visual" aria-hidden="true">
        <img :src="heroLayerSrc" alt="" class="hero-layer-img" />
        <div class="hero-visual-panel hero-visual-panel--top">
          <span>Trace</span>
          <strong>step_07</strong>
        </div>
        <div class="hero-visual-panel hero-visual-panel--bottom">
          <span>学习记录</span>
          <strong>今日进度</strong>
        </div>
      </div>

      <div ref="statsRef" class="hero-stats">
        <div class="stat-card">
          <el-icon :size="20"><Trophy /></el-icon>
          <div>
            <strong>{{ progressSummary.overallPercent }}%</strong>
            <span>平均章节进度</span>
          </div>
        </div>
        <div class="stat-card">
          <el-icon :size="20"><Timer /></el-icon>
          <div>
            <strong>{{ progressSummary.completed }}/{{ progressSummary.tracked || '—' }}</strong>
            <span>已学完模块</span>
          </div>
        </div>
        <div class="stat-card">
          <el-icon :size="20"><Connection /></el-icon>
          <div>
            <strong v-if="healthStatus === 'checking'">…</strong>
            <strong v-else-if="healthStatus === 'ok'">在线</strong>
            <strong v-else>离线</strong>
            <span>判题服务</span>
          </div>
        </div>
        <div v-if="ojReadyCount != null" class="stat-card accent">
          <el-icon :size="20"><Cpu /></el-icon>
          <div>
            <strong>{{ ojReadyCount }}</strong>
            <span>可判题数量</span>
          </div>
        </div>
      </div>
    </section>

    <section class="map-command">
      <div class="map-board">
        <div class="map-board-head">
          <div>
            <p class="section-kicker">学习路径</p>
            <h2>按阶段掌握核心算法</h2>
          </div>
          <div class="map-legend">
            <span><i class="legend-dot done" /> 已完成</span>
            <span><i class="legend-dot active" /> 当前聚焦</span>
            <span><i class="legend-dot idle" /> 待学习</span>
          </div>
        </div>

        <div ref="phasesRef" class="phase-lanes">
          <section v-for="group in phaseGroups" :key="group.phase" class="phase-lane">
            <div class="phase-head">
              <span>{{ group.label }}</span>
              <small>{{ group.modules.length }} 个模块</small>
            </div>
            <div class="module-track">
              <button
                v-for="(module, index) in group.modules"
                :key="module.key"
                type="button"
                class="module-node"
                :class="{
                  active: activeModule === module.key,
                  done: progressFor(module.key) === 100,
                  progress: progressFor(module.key) > 0 && progressFor(module.key) < 100,
                  locked: !module.available,
                }"
                :style="{ '--node-accent': module.accent }"
                @mouseenter="activeModule = module.key"
                @focus="activeModule = module.key"
                @click="onModuleSelect(module.key)"
              >
                <span class="module-index">{{ String(index + 1).padStart(2, '0') }}</span>
                <span class="module-name">{{ module.label }}</span>
                <span class="module-progress">{{ progressFor(module.key) }}%</span>
              </button>
            </div>
          </section>
        </div>
      </div>

      <aside class="map-inspector">
        <div class="inspector-card selected-module">
          <span class="inspector-label">当前模块</span>
          <h3>{{ selectedModule?.label }}</h3>
          <el-progress
            :percentage="selectedModule ? progressFor(selectedModule.key) : 0"
            :stroke-width="8"
          />
          <p>
            {{ selectedModule?.available ? '课程内容已接入，可直接进入学习页。' : '模块已纳入知识体系，后续可扩展完整学习页。' }}
          </p>
          <el-button type="primary" plain :icon="ArrowRight" @click="selectedModule && onModuleSelect(selectedModule.key)">
            打开模块
          </el-button>
        </div>

        <div class="inspector-card compact-map">
          <div class="compact-head">
            <span class="inspector-label">全部模块</span>
            <el-button
              :icon="asideCollapsed ? Expand : Fold"
              circle
              size="small"
              text
              bg
              @click="asideCollapsed = !asideCollapsed"
            />
          </div>
          <el-scrollbar max-height="300px">
            <AlgorithmLearningMap
              :collapsed="asideCollapsed"
              :active-key="activeModule"
              @select="onModuleSelect"
            />
          </el-scrollbar>
        </div>
      </aside>
    </section>

    <div class="home-toolbar">
      <div class="toolbar-left">
        <el-tag type="info" effect="dark" round size="small">快捷入口</el-tag>
        <span class="toolbar-hint">悬停预加载页面，点击即可跳转</span>
      </div>
      <div class="toolbar-right">
        <span class="health-label">后端联调</span>
        <el-tag v-if="healthStatus === 'checking'" type="info" size="small">检测中</el-tag>
        <el-tag v-else-if="healthStatus === 'ok'" type="success" size="small">/api/health 正常</el-tag>
        <el-tag v-else type="danger" size="small">不可用</el-tag>
      </div>
    </div>

    <main class="home-main">
      <HomeAnnounceBar />

      <el-row :gutter="14" ref="quickActionsRef" class="quick-row">
        <el-col v-for="item in quickActions" :key="item.key" :xs="24" :sm="8">
          <button
            type="button"
            class="quick-card"
            @mouseenter="prefetchRoute(item.prefetch)"
            @click="goQuick(item.route, item.prefetch)"
          >
            <el-icon class="quick-icon" :size="22">
              <component :is="item.icon" />
            </el-icon>
            <div class="quick-text">
              <span class="quick-label">{{ item.label }}</span>
              <span class="quick-desc">{{ item.desc }}</span>
            </div>
            <el-icon class="quick-arrow"><ArrowRight /></el-icon>
          </button>
        </el-col>
      </el-row>

      <el-row :gutter="16" ref="analyticsRef" class="analytics-row">
        <el-col :xs="24" :lg="14" :xl="15">
          <el-card class="hover-card analytics-card" shadow="hover">
            <template #header>
              <span class="card-header-title">数据可视化与进度反馈</span>
            </template>
            <HomeDashboardCharts
              :radar="skillRadar"
              :series="activitySeries"
              :heatmap="heatmapCells"
            />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="10" :xl="9">
          <el-card class="hover-card analytics-card community-card" shadow="hover">
            <template #header>
              <span class="card-header-title">社区氛围与全站数据</span>
            </template>
            <HomeCommunityPanel
              :stats="platformStats"
              :ac-board="acBoard"
              :streak-board="streakBoard"
            />
          </el-card>
        </el-col>
      </el-row>

      <section ref="trainingRef" class="training-section">
        <div class="section-head">
          <div class="section-head-left">
            <h2 class="section-title">每日训练与复习</h2>
            <span class="section-hint">基于学习进度与薄弱项推荐</span>
          </div>
          <div class="section-head-right">
            <el-button
              text
              type="primary"
              :icon="Cpu"
              @mouseenter="prefetchRoute('/practice')"
              @click="router.push({ name: 'practice-list' })"
            >
              进入题库
            </el-button>
          </div>
        </div>
        <HomeTrainingSection
          :daily="dailyProblem"
          :targeted="targetedProblems"
          :review="reviewQueue"
          :recent="recentVisits"
          @open-problem="openPractice"
          @open-module="onModuleSelect"
        />
      </section>

      <el-row :gutter="20" class="home-top-row" ref="resourcesRef">
        <el-col :xs="24" :md="10" :lg="8" :xl="6" class="home-stretch-col">
          <el-card class="hover-card persona-card" shadow="hover">
            <div class="card-kicker">个性化起点</div>
            <h2 class="card-title">开启个性化学习</h2>
            <p class="card-desc">
              通过对话构建 6 维学习画像，并由多智能体生成个性化资源与学习路径。
            </p>
            <el-button
              type="primary"
              :icon="ChatDotRound"
              @mouseenter="prefetchRoute('/my-learning')"
              @click="goQuick({ name: 'my-learning', query: { tab: 'persona' } }, '/my-learning')"
            >
              进入画像对话
            </el-button>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="14" :lg="8" :xl="6" class="home-stretch-col">
          <el-card class="hover-card" shadow="hover">
            <template #header>
              <div class="card-header-row">
                <span class="card-header-title">学习进度概览</span>
                <el-tag v-if="hasRealProgress" size="small" type="success" effect="light">
                  本地进度
                </el-tag>
                <el-tag v-else size="small" type="info" effect="light">尚未开始</el-tag>
              </div>
            </template>
            <div class="progress-head">
              <span>总进度</span>
              <strong>{{ progressSummary.overallPercent }}%</strong>
            </div>
            <el-progress
              :percentage="progressSummary.overallPercent"
              :stroke-width="10"
              striped
              striped-flow
            />
            <div class="tag-groups">
              <div v-if="progressSummary.strong.length">
                <div class="tag-label">掌握较好</div>
                <el-tag
                  v-for="t in progressSummary.strong"
                  :key="t"
                  class="mini-tag"
                  type="success"
                  effect="plain"
                >
                  {{ t }}
                </el-tag>
              </div>
              <div v-if="progressSummary.weak.length">
                <div class="tag-label">建议加强</div>
                <el-tag
                  v-for="t in progressSummary.weak"
                  :key="t"
                  class="mini-tag"
                  type="warning"
                  effect="plain"
                >
                  {{ t }}
                </el-tag>
              </div>
              <p v-if="!hasRealProgress" class="empty-progress-hint">
                完成任意模块章节后，此处将自动汇总强弱项。
              </p>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="12" :lg="8" :xl="6" class="home-stretch-col">
          <ModuleGameEntry module-key="array" variant="detective-only" />
        </el-col>

        <el-col :xs="24" :md="12" :lg="8" :xl="6" class="home-stretch-col">
          <el-card class="hover-card tall-card" shadow="hover">
            <template #header>
              <div class="card-header-row">
                <span class="card-header-title">推荐资源</span>
                <el-button
                  text
                  type="primary"
                  size="small"
                  @mouseenter="prefetchRoute('/resources')"
                  @click="router.push({ name: 'resources' })"
                >
                  进入资源库
                </el-button>
              </div>
            </template>
            <RecommendedResourcesPanel v-if="isLoggedIn" :limit="5" />
            <el-scrollbar v-else max-height="360px">
              <div
                v-for="item in recommended"
                :key="item.id"
                class="resource-item resource-item--rich"
                role="button"
                tabindex="0"
                @click="router.push({ name: 'resources', query: { highlight: item.id } })"
                @keydown.enter.prevent="
                  router.push({ name: 'resources', query: { highlight: item.id } })
                "
              >
                <div class="resource-cover" :style="{ background: item.cover }" />
                <div class="resource-body">
                  <div class="resource-title-row">
                    <span class="resource-title">{{ item.title }}</span>
                    <el-tag size="small" type="info" effect="plain">{{ item.module }}</el-tag>
                  </div>
                  <div class="resource-stats">
                    <el-tag size="small" effect="dark" round>{{ item.problemCount }} 题</el-tag>
                    <el-tag size="small" type="success" effect="plain" round>
                      通过率 {{ item.passRate }}%
                    </el-tag>
                    <el-tag
                      v-for="tag in item.tags"
                      :key="tag"
                      size="small"
                      effect="plain"
                      round
                    >
                      {{ tag }}
                    </el-tag>
                  </div>
                  <p class="resource-desc">{{ item.desc }}</p>
                </div>
              </div>
            </el-scrollbar>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="viz-row" ref="vizRef">
        <el-col :xs="24">
          <HomeSortDemo />
        </el-col>
      </el-row>

      <el-row :gutter="16" class="viz-row">
        <el-col :xs="24" :md="12" :lg="8" :xl="6">
          <el-card class="hover-card continue-card" shadow="hover">
            <template #header>
              <span class="card-header-title">继续学习</span>
            </template>
            <p v-if="overview.nextModule" class="continue-lead">
              上次路径建议从
              <strong>{{ overview.nextModule?.label }}</strong>
              继续；也可从下方最近访问快速进入。
            </p>
            <p v-else class="continue-lead">选择上方模块或下方入口开始第一条学习路径。</p>
            <el-button type="primary" :icon="ArrowRight" @click="continueLearning">
              {{ overview.nextModule ? `继续 ${overview.nextModule?.label}` : '打开学习路径' }}
            </el-button>
            <ul v-if="recentVisits.length" class="continue-recent">
              <li v-for="v in recentVisits.slice(0, 4)" :key="v.moduleKey">
                <button type="button" @click="onModuleSelect(v.moduleKey)">
                  {{ v.label }}
                </button>
              </li>
            </ul>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="second-row">
        <el-col :xs="24" :md="12" class="home-stretch-col">
          <el-card shadow="never" class="soft-card actionable" @click="router.push({ name: 'learning-path' })">
            <div class="soft-card-inner">
              <el-icon class="soft-icon" :size="22"><Reading /></el-icon>
              <div>
                <div class="soft-title">学习路径规划</div>
                <div class="soft-desc">
                  按基础结构 → 技巧 → 树与搜索 → 进阶查看模块路线图与章节完成度。
                </div>
              </div>
              <el-icon class="soft-go"><ArrowRight /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="12" class="home-stretch-col">
          <el-card
            shadow="never"
            class="soft-card actionable"
            @mouseenter="prefetchRoute('/practice')"
            @click="router.push({ name: 'practice-list' })"
          >
            <div class="soft-card-inner">
              <el-icon class="soft-icon" :size="22"><Cpu /></el-icon>
              <div>
                <div class="soft-title">在线 OJ 题库</div>
                <div class="soft-desc">
                  与课程题单同步，支持样例运行与提交；后端在线时可 Python / C++ 判题。
                </div>
              </div>
              <el-icon class="soft-go"><ArrowRight /></el-icon>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </main>
  </div>
</template>

<style scoped>
.home-page {
  --home-page-gutter: clamp(16px, 2.2vw, 40px);
  --home-page-max: 1760px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: min(var(--home-page-max), calc(100vw - (var(--home-page-gutter) * 2)));
  max-width: none;
  margin: 0 auto;
  padding-bottom: 48px;
}

.map-command {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(304px, 356px);
  gap: 16px;
  align-items: stretch;
}

.map-board,
.map-inspector .inspector-card,
.home-main {
  border-radius: var(--alp-radius-lg);
  border: 1px solid var(--alp-color-border-strong);
  background:
    rgba(255, 255, 255, 0.025),
    var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
}

.map-board {
  min-width: 0;
  padding: 18px 18px 20px;
  overflow: hidden;
}

.map-board-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.section-kicker {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--alp-color-accent);
}

.map-board-head h2 {
  margin: 0;
  font-size: 21px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.map-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--alp-color-muted);
  font-size: 12px;
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 4px;
  border-radius: 50%;
  background: #64748b;
}

.legend-dot.done {
  background: var(--alp-color-success);
}

.legend-dot.active {
  background: var(--alp-color-primary);
  box-shadow: 0 0 0 3px rgba(var(--alp-color-primary-rgb), 0.14);
}

.phase-lanes {
  display: grid;
  gap: 12px;
}

.phase-lane {
  display: grid;
  grid-template-columns: 126px minmax(0, 1fr);
  gap: 12px;
  align-items: stretch;
}

.phase-head {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
  padding: 14px 13px;
  border-radius: var(--alp-radius-card);
  background:
    rgba(var(--alp-color-primary-rgb), 0.1),
    var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.phase-head span {
  font-weight: 700;
  color: var(--alp-color-text);
}

.phase-head small {
  color: var(--alp-color-muted);
  font-size: 11px;
  font-family: ui-monospace, Consolas, monospace;
}

.module-track {
  position: relative;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
  gap: 8px;
  padding: 10px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-main-panel);
  background-size: auto;
  border: 1px solid rgba(var(--alp-color-primary-rgb), 0.1);
}

.module-node {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 8px;
  min-height: 54px;
  padding: 10px 12px;
  border-radius: 7px;
  border: 1px solid color-mix(in srgb, var(--node-accent) 28%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-bg-surface) 88%, transparent);
  color: var(--alp-color-text);
  cursor: pointer;
  text-align: left;
  transition:
    transform var(--alp-transition-smooth),
    box-shadow var(--alp-transition-smooth),
    border-color var(--alp-transition-fast),
    filter var(--alp-transition-fast);
}

.module-node:hover,
.module-node:focus-visible,
.module-node.active {
  transform: translateY(-2px);
  border-color: var(--node-accent);
  box-shadow:
    inset 3px 0 0 var(--node-accent),
    var(--alp-shadow-card-hover);
  outline: none;
  filter: brightness(1.06);
}

.module-node.locked {
  opacity: 0.55;
  border-style: dashed;
}

.module-node.done {
  border-color: rgba(52, 211, 153, 0.5);
  background:
    rgba(74, 138, 94, 0.12),
    color-mix(in srgb, var(--alp-bg-surface) 90%, transparent);
}

.module-index,
.module-progress {
  font-family: 'Cascadia Code', ui-monospace, Consolas, monospace;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.module-name {
  min-width: 0;
  font-weight: 700;
  font-size: 13.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-progress {
  color: var(--node-accent);
}

.map-inspector {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.inspector-card {
  padding: 16px;
}

.selected-module h3 {
  margin: 6px 0 12px;
  font-size: 22px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.selected-module p {
  color: var(--alp-color-muted);
  line-height: 1.6;
  font-size: 13px;
}

.inspector-label {
  color: var(--alp-color-accent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.compact-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.compact-map :deep(.learning-map) {
  padding: 0;
}

.home-main {
  padding: 18px;
}

.home-layout {
  --home-sticky-top: calc(var(--alp-header-height, 60px) + var(--alp-layout-padding-y, 20px));
  --home-bottom-gap: calc(var(--alp-layout-padding-y, 20px) + 32px);
  --home-aside-gap: 8px;
  position: relative;
  display: block;
  width: 100%;
  height: calc(100vh - var(--home-sticky-top) - var(--home-bottom-gap));
  max-height: calc(100vh - var(--home-sticky-top) - var(--home-bottom-gap));
  overflow: hidden;
  box-sizing: border-box;
}

.home-hero {
  display: grid;
  grid-template-columns: minmax(360px, 1.1fr) minmax(230px, 0.52fr) minmax(360px, 0.82fr);
  align-items: stretch;
  gap: 16px;
  margin-bottom: 16px;
  padding: 28px;
  border-radius: var(--alp-radius-lg);
  border: 1px solid var(--alp-color-border-strong);
  background:
    rgba(var(--alp-color-primary-rgb), 0.1),
    rgba(255, 255, 255, 0.03),
    var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
  min-width: 0;
  position: relative;
  overflow: hidden;
}

.home-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: transparent;
  background-size: auto;
  mask-image: linear-gradient(90deg, rgba(0, 0, 0, 0.56), transparent 76%);
  pointer-events: none;
}

.hero-copy {
  position: relative;
  z-index: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hero-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--alp-color-accent);
}

.hero-title {
  margin: 0 0 12px;
  font-size: clamp(2.1rem, 4vw, 4rem);
  font-weight: 800;
  line-height: 1.04;
  letter-spacing: 0;
  background: var(--alp-gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  overflow-wrap: anywhere;
  word-break: break-all;
}

.hero-desc {
  margin: 0 0 16px;
  max-width: 56ch;
  font-size: 15px;
  line-height: 1.72;
  color: var(--alp-color-muted);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hero-visual {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  min-height: 214px;
  border-left: 1px solid rgba(var(--alp-color-primary-rgb), 0.12);
  border-right: 1px solid rgba(var(--alp-color-primary-rgb), 0.12);
}

.hero-layer-img {
  width: min(220px, 72%);
  opacity: 0.88;
  filter: saturate(0.85) hue-rotate(76deg) drop-shadow(0 24px 34px rgba(0, 0, 0, 0.38));
}

.hero-visual-panel {
  position: absolute;
  min-width: 128px;
  padding: 8px 10px;
  border-radius: 7px;
  border: 1px solid var(--alp-color-border);
  background: rgba(11, 16, 15, 0.78);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(12px);
}

html:not(.dark) .hero-visual-panel {
  background: rgba(255, 255, 255, 0.82);
}

.hero-visual-panel span,
.hero-visual-panel strong {
  display: block;
  line-height: 1.2;
}

.hero-visual-panel span {
  font-size: 10px;
  color: var(--alp-color-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.hero-visual-panel strong {
  margin-top: 3px;
  font-family: 'Cascadia Code', ui-monospace, Consolas, monospace;
  font-size: 12px;
  color: var(--alp-color-text);
}

.hero-visual-panel--top {
  top: 20px;
  right: 6px;
}

.hero-visual-panel--bottom {
  left: 4px;
  bottom: 22px;
  border-color: rgba(var(--alp-color-accent-rgb), 0.26);
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-items: stretch;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  min-height: 92px;
  padding: 16px;
  border-radius: 8px;
  background:
    rgba(255, 255, 255, 0.035),
    var(--alp-bg-main-panel);
  border: 1px solid var(--alp-color-border);
  transition: border-color var(--alp-transition-fast), box-shadow var(--alp-transition-fast), filter var(--alp-transition-fast);
}

.stat-card:hover {
  border-color: rgba(var(--alp-color-primary-rgb), 0.34);
  transform: translateY(-3px);
  box-shadow: var(--alp-shadow-card-hover);
  filter: brightness(1.06);
}

.stat-card.accent {
  border-color: rgba(var(--alp-color-accent-rgb), 0.34);
  background:
    rgba(var(--alp-color-accent-rgb), 0.12),
    var(--alp-bg-main-panel);
}

.stat-card strong {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--alp-color-text);
  line-height: 1.2;
  letter-spacing: 0;
}

.stat-card span {
  font-size: 11px;
  color: var(--alp-color-muted);
  letter-spacing: 0.02em;
}

.stat-card .el-icon {
  color: var(--alp-color-primary);
  flex-shrink: 0;
}

.home-aside {
  position: fixed;
  z-index: 12;
  top: var(--home-sticky-top);
  left: var(--alp-layout-padding-x, 16px);
  bottom: var(--home-bottom-gap);
  width: var(--home-aside-width, 268px) !important;
  height: auto !important;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  box-shadow: var(--alp-shadow-card);
  overflow: hidden;
  margin-right: 0;
}

.aside-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 10px 6px 14px;
  border-bottom: 1px solid var(--alp-color-border);
}

.aside-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.aside-scroll {
  flex: 1;
  min-height: 0;
}

.aside-scroll :deep(.el-scrollbar) {
  height: 100%;
}

.home-right {
  margin-left: calc(var(--home-aside-width, 268px) + var(--home-aside-gap));
  width: calc(100% - var(--home-aside-width, 268px) - var(--home-aside-gap));
  height: 100%;
  max-height: 100%;
  min-width: 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}

.home-layout :deep(.home-right.el-container) {
  display: block;
}

.home-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  padding: 10px 16px;
  background: var(--alp-bg-toolbar);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  backdrop-filter: blur(8px);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.toolbar-hint {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.health-label {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.home-main {
  padding: 18px;
}

.home-main-surface {
  padding: 18px 18px 20px;
  background: var(--alp-bg-main-panel);
  border: 1px solid var(--alp-color-border);
  border-radius: 14px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.analytics-row {
  margin-bottom: 18px;
}

.analytics-card :deep(.el-card__body) {
  padding-top: 8px;
}

.community-card :deep(.el-card__body) {
  min-height: 320px;
}

.training-section {
  margin-bottom: 18px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--alp-color-border);
}

.section-head-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.section-hint {
  font-size: 12px;
  color: var(--alp-color-muted);
  padding: 2px 8px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--alp-color-primary) 8%, transparent);
}

.viz-row {
  margin-bottom: 18px;
}

.continue-card .continue-lead {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.55;
}

.continue-card .continue-lead strong {
  color: var(--alp-color-primary);
}

.continue-recent {
  list-style: none;
  margin: 14px 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.continue-recent button {
  border: 1px solid var(--alp-color-border);
  background: rgba(15, 23, 42, 0.35);
  color: var(--alp-color-text);
  font-size: 12px;
  padding: 6px 14px;
  border-radius: var(--alp-radius-pill);
  cursor: pointer;
  transition: border-color var(--alp-transition-fast), background var(--alp-transition-fast), filter var(--alp-transition-fast);
}

.continue-recent button:hover {
  border-color: rgba(var(--alp-color-primary-rgb), 0.38);
  background: rgba(var(--alp-color-primary-rgb), 0.07);
  transform: translateY(-2px);
  box-shadow: var(--alp-shadow-btn-hover);
  filter: brightness(1.08);
}

.quick-row {
  margin-bottom: 18px;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  margin-bottom: 12px;
  padding: 16px 18px;
  text-align: left;
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  color: inherit;
  cursor: pointer;
  transition:
    transform var(--alp-transition-smooth),
    border-color var(--alp-transition-fast),
    box-shadow var(--alp-transition-fast),
    filter var(--alp-transition-fast);
}

.quick-card:hover {
  transform: translateY(-3px);
  border-color: rgba(var(--alp-color-primary-rgb), 0.38);
  box-shadow: var(--alp-shadow-card-hover);
  filter: brightness(1.06);
}

.quick-icon {
  color: var(--alp-color-primary);
  flex-shrink: 0;
}

.quick-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.quick-label {
  font-weight: 700;
  font-size: 14px;
  color: var(--alp-color-text);
}

.quick-desc {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.quick-arrow {
  color: var(--alp-color-muted);
  flex-shrink: 0;
}

.home-top-row,
.second-row {
  align-items: stretch;
}

.home-stretch-col {
  display: flex;
  margin-bottom: 0;
}

.home-stretch-col :deep(.el-card),
.home-stretch-col :deep(.alp-game-entry) {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.home-stretch-col :deep(.el-card__body),
.home-stretch-col :deep(.alp-game-panel) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.home-stretch-col :deep(.el-scrollbar) {
  flex: 1;
  min-height: 0;
}

.hover-card {
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  transition:
    transform var(--alp-transition-smooth),
    box-shadow var(--alp-transition-smooth),
    border-color var(--alp-transition-fast),
    filter var(--alp-transition-fast);
}

.hover-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--alp-shadow-card-hover);
  border-color: rgba(var(--alp-color-primary-rgb), 0.3);
  filter: brightness(1.06);
}

.persona-card {
  background: var(--alp-bg-persona);
  border: 1px solid var(--alp-border-persona);
}

.card-kicker {
  font-size: 12px;
  color: var(--alp-color-primary);
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.card-title {
  margin: 6px 0 8px;
  font-size: 20px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.card-desc {
  margin: 0 0 14px;
  color: var(--alp-color-muted);
  line-height: 1.6;
  font-size: 14px;
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-header-title {
  font-weight: 700;
  color: var(--alp-color-text);
  font-size: 14.5px;
}

.progress-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 10px;
  font-size: 13px;
  color: var(--alp-color-muted);
}

.progress-head strong {
  color: var(--alp-color-text);
  font-size: 20px;
  font-weight: 700;
}

.tag-groups {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.tag-label {
  font-size: 12px;
  color: var(--alp-color-muted);
  margin-bottom: 6px;
}

.mini-tag {
  margin: 0 6px 6px 0;
}

.empty-progress-hint {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.tall-card {
  min-height: 100%;
}

/* 首页卡片行：算法侦探卡片与周围 el-card 统一视觉 */
.home-stretch-col :deep(.alp-game-panel) {
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  padding: 16px;
  transition:
    transform var(--alp-transition-smooth),
    box-shadow var(--alp-transition-smooth),
    border-color var(--alp-transition-fast);
}

.home-stretch-col :deep(.alp-game-entry:hover .alp-game-panel) {
  transform: translateY(-3px);
  box-shadow: var(--alp-shadow-card-hover);
  border-color: rgba(var(--alp-color-primary-rgb), 0.3);
}

.resource-item {
  padding: 12px 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: background var(--alp-transition-fast), filter var(--alp-transition-fast);
}

.resource-item--rich {
  display: flex;
  gap: 12px;
  padding: 12px 6px;
}

.resource-cover {
  width: 56px;
  height: 56px;
  border-radius: var(--alp-radius-sm);
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.resource-body {
  flex: 1;
  min-width: 0;
}

.resource-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 6px 0;
}

.resource-item + .resource-item {
  border-top: 1px dashed var(--alp-color-border);
}

.resource-item:hover,
.resource-item:focus-visible {
  background: var(--alp-color-primary-soft);
  transform: translateY(-2px);
  box-shadow: var(--alp-shadow-btn-hover);
  outline: none;
  filter: brightness(1.06);
}

.resource-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.resource-title {
  font-weight: 700;
  font-size: 14px;
  color: var(--alp-color-text);
}

.resource-desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.second-row {
  margin-top: 20px;
}

@media (min-width: 1720px) {
  .home-page {
    gap: 20px;
  }

  .map-command {
    grid-template-columns: minmax(0, 1fr) minmax(340px, 380px);
  }

  .map-board,
  .home-main {
    padding: 20px;
  }

  .phase-lane {
    grid-template-columns: 136px minmax(0, 1fr);
  }

  .module-track {
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  }

  .module-node {
    min-height: 58px;
    padding-inline: 14px;
  }
}

@media (max-width: 1180px) {
  .home-page {
    width: min(100%, calc(100vw - 24px));
  }

  .home-hero {
    grid-template-columns: 1fr;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .map-command {
    grid-template-columns: 1fr;
  }

  .map-inspector {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.soft-card {
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.soft-card.actionable {
  cursor: pointer;
  transition:
    transform var(--alp-transition-smooth),
    border-color var(--alp-transition-fast),
    box-shadow var(--alp-transition-fast),
    filter var(--alp-transition-fast);
}

.soft-card.actionable:hover {
  transform: translateY(-3px);
  border-color: rgba(var(--alp-color-primary-rgb), 0.3);
  box-shadow: var(--alp-shadow-card-hover);
  filter: brightness(1.06);
}

.soft-card-inner {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.soft-icon {
  color: var(--alp-color-primary);
  margin-top: 2px;
  flex-shrink: 0;
}

.soft-go {
  margin-left: auto;
  margin-top: 4px;
  color: var(--alp-color-muted);
  flex-shrink: 0;
  transition: transform var(--alp-transition-fast);
}

.soft-card.actionable:hover .soft-go {
  transform: translateX(3px);
}

.soft-title {
  font-weight: 700;
  margin-bottom: 4px;
  color: var(--alp-color-text);
}

.soft-desc {
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.55;
}

@media (max-width: 768px) {
  .home-layout {
    height: auto;
    max-height: none;
    overflow: visible;
  }

  .home-aside {
    position: static;
    width: 100% !important;
    height: auto !important;
    margin-bottom: 12px;
  }

  .map-inspector {
    grid-template-columns: 1fr;
  }

  .phase-lane {
    grid-template-columns: 1fr;
  }

  .home-right {
    margin-left: 0;
    width: 100%;
    height: auto;
    max-height: none;
    overflow-y: visible;
  }

  .aside-scroll {
    flex: none;
    max-height: 320px;
  }

  .home-hero {
    padding: 16px;
    overflow: hidden;
  }

  .hero-visual {
    min-height: 168px;
    border-left: none;
    border-right: none;
    border-top: 1px solid rgba(var(--alp-color-primary-rgb), 0.12);
    border-bottom: 1px solid rgba(var(--alp-color-primary-rgb), 0.12);
  }

  .hero-layer-img {
    width: min(172px, 58%);
  }

  .hero-visual-panel {
    min-width: 112px;
    padding: 7px 9px;
  }

  .hero-visual-panel--top {
    top: 12px;
    right: 16px;
  }

  .hero-visual-panel--bottom {
    left: 14px;
    bottom: 12px;
  }

  .hero-copy {
    flex: 1 1 100%;
  }

  .hero-title {
    max-width: 100%;
    white-space: normal !important;
    word-break: break-word;
  }

  .hero-actions :deep(.el-button) {
    flex: 1 1 100%;
    margin-left: 0;
  }

  .hero-stats {
    width: 100%;
  }

  .stat-card {
    flex: 1 1 calc(50% - 8px);
    min-width: 0;
    min-height: 76px;
    padding: 12px;
  }

  .stat-card strong {
    font-size: 20px;
  }

  .home-main-surface {
    padding: 14px;
  }

  .home-stretch-col {
    margin-bottom: 12px;
  }

  .home-stretch-col:last-child {
    margin-bottom: 0;
  }
}

  /* Impeccable Design - Enhanced micro-interactions */
  .home-hero {
    position: relative;
    isolation: isolate;
  }

  .home-hero::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: inherit;
    background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(61, 138, 126, 0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  .hero-copy, .hero-visual, .hero-stats {
    position: relative;
    z-index: 1;
  }

  .quick-action-card {
    transition: transform var(--alp-transition-smooth), box-shadow var(--alp-transition-smooth), border-color var(--alp-transition-fast), background var(--alp-transition-fast), filter var(--alp-transition-smooth) !important;
    will-change: transform;
  }

  .quick-action-card:hover {
    transform: translateY(-4px) scale(1.01) !important;
    box-shadow: var(--alp-shadow-card-hover) !important;
    border-color: rgba(var(--alp-color-primary-rgb), 0.25) !important;
  }

  .quick-action-card:active {
    transform: translateY(-1px) scale(0.99) !important;
  }

  .quick-arrow {
    transition: transform var(--alp-transition-fast);
  }

  .quick-action-card:hover .quick-arrow {
    transform: translateX(4px);
  }

  .module-node {
    transition: transform var(--alp-transition-smooth), box-shadow var(--alp-transition-smooth), border-color var(--alp-transition-fast), background var(--alp-transition-fast), filter var(--alp-transition-smooth);
    will-change: transform;
    cursor: pointer;
  }

  .module-node:hover {
    transform: translateY(-3px) scale(1.02);
    z-index: 2;
  }

  .module-node:active {
    transform: translateY(-1px) scale(0.98);
  }

  .stat-card {
    transition: transform var(--alp-transition-smooth), box-shadow var(--alp-transition-smooth), border-color var(--alp-transition-fast), background var(--alp-transition-fast);
    will-change: transform;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--alp-shadow-card-hover);
    border-color: rgba(var(--alp-color-primary-rgb), 0.2);
  }

  .card-header-title {
    position: relative;
    display: inline-block;
  }

  .card-header-title::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 28px;
    height: 2px;
    background: var(--alp-color-primary);
    border-radius: 2px;
    opacity: 0.5;
  }

  @keyframes alp-pulse-soft {
    0%, 100% { box-shadow: 0 0 0 0 rgba(var(--alp-color-primary-rgb), 0); }
    50% { box-shadow: 0 0 0 4px rgba(var(--alp-color-primary-rgb), 0.06); }
  }

  .hero-visual-panel {
    animation: alp-pulse-soft 3s ease-in-out infinite;
  }

  .hero-visual-panel--bottom {
    animation-delay: 1.5s;
  }

  @media (prefers-reduced-motion: reduce) {
    .quick-action-card, .module-node, .stat-card, .hero-visual-panel {
      transition-duration: 0.01ms !important;
      animation-duration: 0.01ms !important;
      transform: none !important;
    }
    .quick-arrow { transform: none !important; }
  }

/* Impeccable Product UI — layout & visual hierarchy overrides */

/* Hero: cleaner spacing, less visual noise */
.home-hero {
  padding: 28px 28px 20px !important;
}

.home-hero::before {
  content: none !important;
}

.hero-copy, .hero-visual, .hero-stats {
  position: static;
  z-index: auto;
}

.hero-title {
  font-size: 28px !important;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.25;
  margin-bottom: 8px;
}

.hero-kicker {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--alp-color-muted);
  margin-bottom: 4px;
}

.hero-desc {
  font-size: 14px;
  color: var(--alp-color-text-secondary);
  line-height: 1.55;
  max-width: 520px;
}

.hero-actions {
  margin-top: 16px;
  gap: 10px;
}

/* Stats cards: compact, readable */
.stat-card {
  padding: 14px 16px !important;
  min-height: auto !important;
}

.stat-card strong {
  font-size: 20px !important;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.stat-card span {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--alp-color-muted);
}

.hero-stats {
  gap: 10px;
}

/* Section headers: consistent rhythm */
.section-kicker {
  display: none;
}

.map-board-head h2 {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 0;
}

.map-board-head {
  margin-bottom: 20px;
}

.phase-head {
  margin-bottom: 8px;
}

.phase-head span {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--alp-color-text);
}

.phase-head small {
  font-size: 11px;
  color: var(--alp-color-muted);
}

/* Module nodes: touch-friendly, readable */
.module-node {
  padding: 8px 12px !important;
  min-height: auto !important;
}

.module-index {
  font-size: 11px;
  font-weight: 600;
}

.module-name {
  font-size: 13px;
  font-weight: 500;
}

.module-progress {
  font-size: 11px;
}

/* Quick action cards: clean, compact */
.quick-action-card {
  padding: 16px 18px !important;
  transition: border-color 0.2s ease, background 0.2s ease !important;
}

.quick-action-card:hover {
  transform: none !important;
  border-color: var(--alp-color-border-strong) !important;
}

.quick-label {
  font-size: 14px;
  font-weight: 600;
}

.quick-desc {
  font-size: 12px;
  color: var(--alp-color-muted);
}

/* Map inspector */
.inspector-card {
  padding: 16px;
}

.inspector-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--alp-color-muted);
}

/* Training section */
.section-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.section-hint {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.section-head {
  margin-bottom: 16px;
}

/* Soft cards */
.soft-card {
  padding: 16px 18px;
}

.soft-title {
  font-size: 14px;
  font-weight: 600;
}

.soft-desc {
  font-size: 12px;
  line-height: 1.5;
}

/* Toolbar */
.home-toolbar {
  padding: 8px 12px;
  font-size: 12px;
}

.toolbar-hint {
  font-size: 11px;
  color: var(--alp-color-muted);
}

/* Continue card */
.continue-lead {
  font-size: 13px;
  line-height: 1.5;
  color: var(--alp-color-text-secondary);
  margin-bottom: 14px;
}

.continue-recent button {
  font-size: 12px;
  padding: 4px 0;
}

/* Resource items */
.resource-title {
  font-size: 13px;
}

.resource-desc {
  font-size: 12px;
}

/* Card headers */
.card-header-title {
  font-size: 14px;
  font-weight: 600;
  position: static;
}

.card-header-title::after {
  content: none;
}

/* Hero visual panel: smaller, less distracting */
.hero-visual-panel {
  padding: 8px 10px;
  font-size: 11px;
  animation: none;
}

.hero-visual-panel strong {
  font-size: 13px;
}

/* Visual panels: less decorative */
.hero-visual-panel--top,
.hero-visual-panel--bottom {
  animation: none;
}

/* Remove the ::before pseudo on hero that Impeccable banned */
.home-page .soft-card.actionable {
  transition: border-color 0.2s ease, background 0.2s ease;
}

.home-page .soft-card.actionable:hover {
  transform: none;
}

.home-page .soft-card.actionable:active {
  transform: none;
}

/* Consistent section spacing */
.map-command {
  margin-bottom: 0;
}

.home-main {
  padding-top: 12px !important;
}

/* Phase lanes: better vertical rhythm */
.phase-lanes {
  gap: 16px;
}

.phase-lane {
  gap: 8px;
}

.module-track {
  gap: 6px;
}

/* Map legend: compact */
.map-legend {
  font-size: 11px;
  gap: 12px;
}

.map-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 6px;
  height: 6px;
}

/* Analytics cards */
.analytics-card .card-header-title {
  font-size: 14px;
}

/* Persona card */
.persona-card .card-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin-bottom: 8px;
}

.persona-card .card-desc {
  font-size: 13px;
  line-height: 1.5;
  color: var(--alp-color-text-secondary);
  margin-bottom: 16px;
}

.persona-card .card-kicker {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--alp-color-muted);
  margin-bottom: 4px;
}

/* Remove decorative pulse animations */
.hero-visual-panel {
  animation: none !important;
}

/* Quick arrow: clean */
.quick-arrow {
  transition: transform 0.15s ease;
}

/* Card header rows */
.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

/* Resource stats */
.resource-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 6px 0;
}

.resource-stats .el-tag {
  font-size: 11px;
  padding: 0 6px;
  height: 20px;
  line-height: 20px;
}

/* Module node status: cleaner */
.module-node.active {
  border-color: var(--alp-color-primary) !important;
  background: rgba(var(--alp-color-primary-rgb), 0.08) !important;
}

.module-node.done {
  border-color: var(--alp-color-success) !important;
}

.module-node.progress {
  border-color: var(--alp-color-accent) !important;
}

/* Home layout: prevent overflow */
.home-layout {
  height: 100%;
  max-height: 100vh;
}

/* Responsive: mobile cleanup */
@media (max-width: 768px) {
  .home-hero {
    padding: 20px 16px !important;
  }
  
  .hero-title {
    font-size: 22px !important;
  }
  
  .hero-stats {
    grid-template-columns: repeat(2, 1fr) !important;
  }
  
  .section-title,
  .map-board-head h2,
  .persona-card .card-title {
    font-size: 16px;
  }
}
</style>

<style scoped>
.dashboard-home {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 8px 0 56px;
  color: var(--alp-color-text);
}

.dashboard-welcome {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.72fr);
  align-items: center;
  gap: 40px;
  padding: 26px 28px;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px 10px 0 0;
  background: var(--alp-bg-surface-solid);
}

.dashboard-welcome-copy {
  min-width: 0;
}

.dashboard-eyebrow {
  margin: 0 0 5px;
  color: var(--alp-color-primary);
  font-size: 12px;
  font-weight: 700;
}

.dashboard-welcome h1 {
  margin: 0;
  font-size: 25px;
  line-height: 1.35;
  letter-spacing: -0.02em;
}

.dashboard-welcome p:not(.dashboard-eyebrow) {
  margin: 7px 0 0;
  color: var(--alp-color-muted);
  font-size: 13px;
}

.dashboard-context {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 15px;
}

.dashboard-context > span {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 4px 9px;
  color: var(--alp-color-text-secondary);
  font-size: 11px;
  font-weight: 550;
  border-radius: 99px;
  background: var(--alp-bg-surface-muted);
}

.dashboard-status-dot {
  width: 7px;
  height: 7px;
  margin-right: 6px;
  border-radius: 50%;
  background: var(--alp-color-muted);
}

.dashboard-status-dot.is-ok {
  background: var(--alp-color-success);
  box-shadow: 0 0 0 3px rgba(74, 138, 94, 0.12);
}

.dashboard-status-dot.is-error {
  background: var(--alp-color-warning);
  box-shadow: 0 0 0 3px rgba(156, 122, 61, 0.12);
}

.dashboard-welcome-side {
  display: grid;
  gap: 15px;
  min-width: 0;
  padding-left: 28px;
  border-left: 1px solid var(--alp-color-border);
}

.dashboard-focus-summary {
  min-width: 0;
}

.dashboard-focus-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.dashboard-focus-head > span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--alp-color-muted);
  font-size: 11px;
  font-weight: 650;
}

.dashboard-focus-head .el-icon,
.dashboard-focus-head b {
  color: var(--alp-color-primary);
}

.dashboard-focus-head b {
  font-size: 13px;
}

.dashboard-focus-summary > strong {
  display: block;
  overflow: hidden;
  margin-top: 6px;
  font-size: 17px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-focus-summary > small {
  display: block;
  margin-top: 3px;
  color: var(--alp-color-muted);
  font-size: 11px;
}

.dashboard-focus-track {
  height: 5px;
  overflow: hidden;
  margin-top: 10px;
  border-radius: 99px;
  background: var(--alp-bg-soft-block);
}

.dashboard-focus-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--alp-color-primary);
  transition: width 240ms cubic-bezier(0.22, 1, 0.36, 1);
}

.dashboard-welcome-actions {
  display: flex;
  flex: 0 0 auto;
}

.dashboard-welcome-actions :deep(.el-button) {
  min-height: 40px;
  border-radius: 6px;
  font-weight: 650;
}

.dashboard-shortcuts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid var(--alp-color-border);
  border-top: 0;
  background: var(--alp-bg-surface-solid);
}

.dashboard-shortcuts > button {
  display: grid;
  grid-template-columns: 34px 1fr 18px;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 17px 20px;
  color: var(--alp-color-text);
  text-align: left;
  border: 0;
  border-right: 1px solid var(--alp-color-border);
  background: transparent;
  cursor: pointer;
  transition: background-color 160ms ease, color 160ms ease;
}

.dashboard-shortcuts > button:last-child { border-right: 0; }
.dashboard-shortcuts > button:hover { background: var(--alp-bg-surface-muted); }
.dashboard-shortcuts > button > .el-icon:first-child {
  width: 32px;
  height: 32px;
  color: var(--alp-color-primary);
  font-size: 17px;
  border-radius: 8px;
  background: var(--alp-color-primary-soft);
  transition: background-color 160ms ease, transform 160ms cubic-bezier(0.22, 1, 0.36, 1);
}
.dashboard-shortcuts > button:hover > .el-icon:first-child {
  background: rgba(var(--alp-color-primary-rgb), 0.16);
  transform: translateY(-1px);
}
.dashboard-shortcuts span { display: flex; min-width: 0; flex-direction: column; }
.dashboard-shortcuts strong { font-size: 14px; font-weight: 650; }
.dashboard-shortcuts small { overflow: hidden; margin-top: 2px; color: var(--alp-color-muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.dashboard-shortcut-arrow {
  color: var(--alp-color-muted);
  font-size: 13px;
  transition: color 160ms ease, transform 160ms cubic-bezier(0.22, 1, 0.36, 1);
}
.dashboard-shortcuts > button:hover .dashboard-shortcut-arrow {
  color: var(--alp-color-primary);
  transform: translateX(2px);
}

.dashboard-columns {
  display: grid;
  grid-template-columns: minmax(0, 2.15fr) minmax(390px, 0.95fr);
  align-items: start;
  gap: 18px;
  margin-top: 18px;
}

.dashboard-primary,
.dashboard-secondary {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.dashboard-panel {
  min-width: 0;
  padding: 18px 20px 20px;
  border: 1px solid var(--alp-color-border);
  border-radius: 8px;
  background: var(--alp-bg-surface-solid);
}

.dashboard-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 15px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--alp-color-border);
}

.dashboard-panel-head h2 {
  margin: 0;
  font-size: 16px;
  line-height: 1.4;
  letter-spacing: -0.01em;
}

.dashboard-panel-head p {
  margin: 3px 0 0;
  color: var(--alp-color-muted);
  font-size: 11px;
}

.dashboard-updated {
  color: var(--alp-color-primary);
  font-size: 11px;
  white-space: nowrap;
}

.dashboard-analytics { min-height: 420px; }
.dashboard-training { min-height: 360px; }
.dashboard-community { min-height: 420px; }

.dashboard-map-count {
  color: var(--alp-color-muted);
  font-size: 11px;
  white-space: nowrap;
}

.dashboard-map-body {
  min-height: 260px;
  padding: 2px 4px 12px;
}

.dashboard-chapter-map :deep(.algorithm-map) {
  width: 100%;
}

.dashboard-chapter-map :deep(.map-node),
.dashboard-chapter-map :deep(button) {
  cursor: pointer;
}

.dashboard-map-detail {
  margin-top: 4px;
  padding: 16px;
  border: 1px solid rgba(var(--alp-color-primary-rgb), 0.28);
  border-radius: 7px;
  background: rgba(var(--alp-color-primary-rgb), 0.055);
}

.dashboard-map-detail > span {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.dashboard-map-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-top: 3px;
}

.dashboard-map-title strong {
  font-size: 18px;
}

.dashboard-map-title b {
  color: var(--alp-color-primary);
  font-size: 13px;
}

.dashboard-map-progress {
  height: 6px;
  overflow: hidden;
  margin-top: 10px;
  border-radius: 99px;
  background: var(--alp-bg-soft-block);
}

.dashboard-map-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--alp-color-primary);
  transition: width 220ms ease;
}

.dashboard-map-detail p {
  margin: 10px 0 13px;
  color: var(--alp-color-text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.dashboard-map-detail :deep(.el-button) {
  width: 100%;
  border-radius: 6px;
}

.dashboard-percent {
  color: var(--alp-color-primary);
  font-size: 20px;
}

.dashboard-progress-track {
  height: 7px;
  overflow: hidden;
  margin: -2px 0 18px;
  border-radius: 99px;
  background: var(--alp-bg-soft-block);
}

.dashboard-progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--alp-color-primary);
}

.dashboard-selected-module {
  display: grid;
  grid-template-columns: minmax(180px, 0.8fr) minmax(220px, 1.2fr) auto;
  align-items: center;
  gap: 22px;
  margin-bottom: 18px;
  padding: 15px 16px;
  border: 1px solid rgba(var(--alp-color-primary-rgb), 0.28);
  border-radius: 7px;
  background: rgba(var(--alp-color-primary-rgb), 0.055);
}

.dashboard-selected-copy {
  display: grid;
  gap: 2px;
}

.dashboard-selected-copy > span,
.dashboard-selected-progress span {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.dashboard-selected-copy > strong {
  font-size: 17px;
  line-height: 1.45;
}

.dashboard-selected-copy > small {
  color: var(--alp-color-text-secondary);
  font-size: 11px;
}

.dashboard-selected-progress > div:first-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 7px;
}

.dashboard-selected-progress strong {
  color: var(--alp-color-primary);
  font-size: 13px;
}

.dashboard-selected-track {
  height: 6px;
  overflow: hidden;
  border-radius: 99px;
  background: var(--alp-bg-soft-block);
}

.dashboard-selected-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--alp-color-primary);
  transition: width 220ms ease;
}

.dashboard-selected-module :deep(.el-button) {
  border-radius: 6px;
}

.dashboard-module-groups { display: grid; gap: 13px; }
.dashboard-module-group { display: grid; grid-template-columns: 78px 1fr; align-items: start; gap: 12px; }
.dashboard-module-group > span { padding-top: 6px; color: var(--alp-color-muted); font-size: 12px; font-weight: 650; }
.dashboard-module-group > div { display: flex; flex-wrap: wrap; gap: 7px; }
.dashboard-module-group button {
  padding: 5px 9px;
  color: var(--alp-color-text-secondary);
  font: inherit;
  font-size: 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: 5px;
  background: var(--alp-bg-surface-muted);
  cursor: pointer;
}
.dashboard-module-group button:hover,
.dashboard-module-group button.active { color: var(--alp-color-primary); border-color: var(--alp-color-primary); }
.dashboard-module-group button.done { color: #287a52; background: rgba(40, 122, 82, 0.07); }
.dashboard-module-group small { margin-left: 4px; color: var(--alp-color-muted); }

.dashboard-resource-list { display: grid; }
.dashboard-resource-list button {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 2px;
  color: var(--alp-color-text-secondary);
  font: inherit;
  font-size: 13px;
  text-align: left;
  border: 0;
  border-bottom: 1px solid var(--alp-color-border);
  background: transparent;
  cursor: pointer;
}
.dashboard-resource-list button:hover span { color: var(--alp-color-primary); }
.dashboard-resource-list small { color: var(--alp-color-muted); white-space: nowrap; }

.dashboard-continue-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 13px 12px;
  color: var(--alp-color-text);
  text-align: left;
  border: 1px solid var(--alp-color-border);
  border-radius: 6px;
  background: var(--alp-bg-surface-muted);
  cursor: pointer;
}
.dashboard-continue-item + .dashboard-continue-item { margin-top: 8px; }
.dashboard-continue-item:hover { border-color: var(--alp-color-primary); }
.dashboard-continue-item span { display: flex; flex-direction: column; }
.dashboard-continue-item strong { font-size: 13px; }
.dashboard-continue-item small { margin-top: 2px; color: var(--alp-color-muted); font-size: 11px; }
.dashboard-continue-item .el-icon { color: var(--alp-color-primary); }

@media (max-width: 1020px) {
  .dashboard-welcome { grid-template-columns: minmax(0, 1fr) minmax(300px, 0.72fr); gap: 24px; }
  .dashboard-welcome-side { padding-left: 22px; }
  .dashboard-columns { grid-template-columns: 1fr; }
  .dashboard-secondary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dashboard-continue { grid-column: 1 / -1; }
}

@media (max-width: 760px) {
  .dashboard-home { width: 100%; padding-top: 0; }
  .dashboard-welcome { grid-template-columns: 1fr; align-items: flex-start; gap: 20px; padding: 21px 18px; }
  .dashboard-welcome-side { width: 100%; padding: 17px 0 0; border-top: 1px solid var(--alp-color-border); border-left: 0; }
  .dashboard-welcome-actions { width: 100%; }
  .dashboard-welcome-actions :deep(.el-button) { flex: 1; }
  .dashboard-shortcuts { grid-template-columns: 1fr 1fr; }
  .dashboard-shortcuts > button:nth-child(2) { border-right: 0; }
  .dashboard-shortcuts > button:nth-child(-n + 2) { border-bottom: 1px solid var(--alp-color-border); }
  .dashboard-secondary { grid-template-columns: 1fr; }
  .dashboard-continue { grid-column: auto; }
  .dashboard-panel { padding: 16px 14px; }
  .dashboard-module-group { grid-template-columns: 1fr; gap: 4px; }
  .dashboard-selected-module { grid-template-columns: 1fr; gap: 12px; }
  .dashboard-selected-module :deep(.el-button) { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
  .dashboard-focus-track i,
  .dashboard-shortcuts > button,
  .dashboard-shortcuts > button > .el-icon:first-child,
  .dashboard-shortcut-arrow {
    transition: none;
  }
}
</style>

<style scoped>
/* 2026 homepage refresh: compact, task-first product UI */
.home-page {
  max-width: 1480px;
  margin: 0 auto;
  padding: 24px 28px 56px;
}

.home-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(420px, 0.65fr);
  grid-template-areas:
    "copy stats";
  gap: 0;
  min-height: 0;
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
  background: var(--alp-bg-surface-solid);
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.05);
}

.home-hero::before,
.home-hero::after,
.hero-visual {
  display: none !important;
}

.hero-copy {
  grid-area: copy;
  max-width: none;
  padding: 34px 38px 30px;
  border-right: 1px solid var(--alp-color-border);
}

.hero-kicker {
  margin: 0 0 8px;
  color: var(--alp-color-primary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: none;
}

.hero-title {
  max-width: none;
  margin: 0;
  color: var(--alp-color-text);
  font-size: 30px;
  font-weight: 720;
  line-height: 1.3;
  letter-spacing: -0.025em;
}

.hero-desc {
  max-width: 62ch;
  margin: 10px 0 0;
  color: var(--alp-color-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.hero-actions {
  margin-top: 22px;
}

.hero-actions :deep(.el-button) {
  min-height: 42px;
  border-radius: 7px;
  font-weight: 650;
}

.hero-stats {
  grid-area: stats;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-content: stretch;
  gap: 0;
  width: auto;
  margin: 0;
  padding: 0;
  border: 0;
}

.stat-card,
.stat-card.accent {
  min-width: 0;
  padding: 24px;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.stat-card:nth-child(odd) { border-right: 1px solid var(--alp-color-border); }
.stat-card:nth-child(-n + 2) { border-bottom: 1px solid var(--alp-color-border); }
.stat-card:hover { transform: none; background: var(--alp-bg-surface-muted); box-shadow: none; }
.stat-card .el-icon { color: var(--alp-color-primary); }
.stat-card strong { color: var(--alp-color-text); font-size: 22px; }
.stat-card span { color: var(--alp-color-muted); font-size: 12px; }

.map-command {
  margin-top: 18px;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
  background: var(--alp-bg-surface-solid);
  box-shadow: none;
}

.map-board-head h2 {
  font-size: 19px;
  letter-spacing: -0.01em;
}

.section-kicker {
  color: var(--alp-color-primary);
  font-size: 12px;
  letter-spacing: 0;
  text-transform: none;
}

.module-node {
  border-radius: 7px;
  box-shadow: none;
}

.home-toolbar {
  margin: 14px 0 0;
  border: 1px solid var(--alp-color-border);
  border-radius: 8px;
  background: var(--alp-bg-surface-muted);
  box-shadow: none;
}

.quick-row { margin-top: 14px; }
.quick-card {
  min-height: 76px;
  border-radius: 9px;
  background: var(--alp-bg-surface-solid);
  box-shadow: none;
}
.quick-card:hover { transform: none; border-color: var(--alp-color-primary); box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05); }

@media (max-width: 1080px) {
  .home-hero {
    grid-template-columns: 1fr;
    grid-template-areas: "copy" "stats";
  }
  .hero-copy { border-right: 0; border-bottom: 1px solid var(--alp-color-border); }
}

@media (max-width: 720px) {
  .home-page { padding: 14px 12px 40px; }
  .hero-copy { padding: 24px 20px; }
  .hero-title { font-size: 24px; }
  .hero-actions { display: grid; gap: 10px; }
  .hero-actions :deep(.el-button) { width: 100%; margin: 0; }
  .hero-stats { grid-template-columns: 1fr 1fr; }
  .stat-card, .stat-card.accent { padding: 18px 16px; }
}
</style>

<style>
/* 首页：禁止 document 滚动，确保仅 .home-right 内滚动 */
html:has(.home-layout),
body:has(.home-layout) {
  overflow: hidden;
  height: 100%;
}

@media (max-width: 768px) {
  html:has(.home-layout),
  body:has(.home-layout) {
    overflow: auto;
    height: auto;
  }
}
</style>
