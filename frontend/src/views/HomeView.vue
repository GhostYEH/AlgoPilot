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
  if (!c) return base
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
const activityFeed = computed(() => communityData.value?.feed ?? [])
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
  <div class="home-page">
    <section class="home-hero">
      <div class="hero-copy">
        <p class="hero-kicker">AlgoPilot · 智能算法学习</p>
        <h1 class="hero-title">算法学习驾驶舱</h1>
        <p class="hero-desc">
          用阶段化学习地图串起讲义、OJ、Trace 动画、游戏化练习与多智能体资源生成，形成完整教学闭环。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" :icon="ArrowRight" @click="continueLearning">
            {{ overview.nextModule ? `继续：${overview.nextModule.label}` : '开始学习路径' }}
          </el-button>
          <el-button
            size="large"
            plain
            :icon="Cpu"
            @mouseenter="prefetchRoute('/practice')"
            @click="router.push({ name: 'practice-list' })"
          >
            进入在线 OJ
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
          <span>Agent Loop</span>
          <strong>verify → adapt</strong>
        </div>
      </div>

      <div class="hero-stats">
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
            <p class="section-kicker">Course Knowledge Map</p>
            <h2>阶段星轨学习地图</h2>
          </div>
          <div class="map-legend">
            <span><i class="legend-dot done" /> 已完成</span>
            <span><i class="legend-dot active" /> 当前聚焦</span>
            <span><i class="legend-dot idle" /> 待学习</span>
          </div>
        </div>

        <div class="phase-lanes">
          <section v-for="group in phaseGroups" :key="group.phase" class="phase-lane">
            <div class="phase-head">
              <span>{{ group.label }}</span>
              <small>{{ group.modules.length }} modules</small>
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
            <span class="inspector-label">纵向路径索引</span>
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

      <el-row :gutter="14" class="quick-row">
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

      <el-row :gutter="16" class="analytics-row">
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
              :feed="activityFeed"
            />
          </el-card>
        </el-col>
      </el-row>

      <section class="training-section">
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

      <el-row :gutter="20" class="home-top-row">
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

      <el-row :gutter="16" class="viz-row">
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
              <strong>{{ overview.nextModule.label }}</strong>
              继续；也可从下方最近访问快速进入。
            </p>
            <p v-else class="continue-lead">选择上方模块或下方入口开始第一条学习路径。</p>
            <el-button type="primary" :icon="ArrowRight" @click="continueLearning">
              {{ overview.nextModule ? `继续 ${overview.nextModule.label}` : '打开学习路径' }}
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
