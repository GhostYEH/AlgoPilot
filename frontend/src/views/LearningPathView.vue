<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Guide, TrendCharts, Calendar, DataBoard, Compass, Timer } from '@element-plus/icons-vue'
import AlgorithmUniverseGraph from '@/components/learning/AlgorithmUniverseGraph.vue'
import ConceptKnowledgeGraph from '@/components/learning/ConceptKnowledgeGraph.vue'
import PersonaChatPanel from '@/components/persona/PersonaChatPanel.vue'
import RecommendedResourcesPanel from '@/components/learning/RecommendedResourcesPanel.vue'
import PathReplanDiffCard from '@/components/learning/PathReplanDiffCard.vue'
import LearningProgressRing from '@/components/learning/LearningProgressRing.vue'
import LearningSectionDonut from '@/components/learning/LearningSectionDonut.vue'
import LearningModuleBarChart from '@/components/learning/LearningModuleBarChart.vue'
import LearningActivityHeatmap from '@/components/learning/LearningActivityHeatmap.vue'
import LearningEffectivenessCard from '@/components/learning/LearningEffectivenessCard.vue'
import LearningEvaluationPanel from '@/components/learning/LearningEvaluationPanel.vue'
import { ALGORITHM_MODULES } from '@/constants/modules'
import { buildLearningOverview } from '@/utils/learningOverview'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'
import { isLoggedIn } from '@/stores/auth'
import { useLearningActivity } from '@/composables/useLearningActivity'
import type { PersonaProfile } from '@/api/orchestrator'

const route = useRoute()
const router = useRouter()
const { plan, loadPlan, lastReplanDiff, clearReplanDiff } = useLearningPathPlan()
const { activityDays } = useLearningActivity()
const universeKey = ref(0)

const highlightKey = computed(() => {
  const q = route.query.module
  return typeof q === 'string' ? q : undefined
})

const pathHighlightIds = computed(() => plan.value?.ordered_keys ?? [])

const moduleLabel = computed(() => {
  if (!highlightKey.value) return ''
  return ALGORITHM_MODULES.find((m) => m.key === highlightKey.value)?.label ?? highlightKey.value
})

const overview = computed(() => buildLearningOverview())

const availableRows = computed(() => overview.value.rows.filter(r => r.available && r.hasProgressData))

const phaseStats = computed(() => {
  const phases = ['foundation', 'technique', 'tree', 'advanced'] as const
  return phases.map(phase => {
    const rows = overview.value.rows.filter(r => r.phase === phase)
    const done = rows.reduce((s, r) => s + r.doneCount, 0)
    const total = rows.reduce((s, r) => s + r.totalCount, 0)
    return { phase, done, total, percent: total > 0 ? Math.round(done / total * 100) : 0 }
  })
})

async function onProfileReady(_profile: PersonaProfile) {
  await loadPlan()
  universeKey.value += 1
  autoTour.value = true
}

const autoTour = ref(false)
const onboardingSectionRef = ref<HTMLElement | null>(null)

onMounted(async () => {
  if (isLoggedIn.value) {
    await loadPlan()
  }
  if (route.query.onboarding === '1') {
    await nextTick()
    onboardingSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
})
</script>

<template>
  <el-card shadow="never" class="page-card">
    <el-page-header title="学习路径" @back="router.push({ name: 'home' })" />
    <el-divider />

    <header class="page-hero">
      <div class="hero-main">
        <h2 class="hero-title">
          <el-icon class="hero-icon"><Compass /></el-icon>
          智能学习路径
        </h2>
        <p class="hero-desc">
          <strong>ProfilerAgent + PlannerAgent</strong>：登录后完成破冰访谈，系统将抽取六维画像并在<strong>算法知识宇宙</strong>中生成可探索的 DAG 星图。
          <template v-if="highlightKey">
            当前聚焦：<el-tag type="primary" effect="plain" size="small">{{ moduleLabel }}</el-tag>
          </template>
        </p>
      </div>
      <div class="hero-stats">
        <div class="stat-mini">
          <span class="stat-mini-value">{{ overview.overallPercent }}%</span>
          <span class="stat-mini-label">总进度</span>
        </div>
        <div class="stat-mini">
          <span class="stat-mini-value">{{ overview.trackedModules }}</span>
          <span class="stat-mini-label">已跟踪</span>
        </div>
        <div class="stat-mini">
          <span class="stat-mini-value">{{ overview.completedModules }}</span>
          <span class="stat-mini-label">已完成</span>
        </div>
      </div>
    </header>

    <section class="dashboard-grid">
      <div class="dash-card dash-card--progress">
        <div class="dash-head">
          <el-icon><DataBoard /></el-icon>
          <span>学习进度总览</span>
        </div>
        <div class="dash-body dash-body--centered">
          <LearningProgressRing
            :percent="overview.overallPercent"
            :size="120"
            label="总进度"
            :sublabel="`${overview.completedModules}/${overview.trackedModules} 模块`"
          />
        </div>
        <div class="dash-foot">
          <span>已完成 {{ overview.completedModules }} 个模块</span>
        </div>
      </div>

      <div class="dash-card dash-card--donut">
        <div class="dash-head">
          <el-icon><TrendCharts /></el-icon>
          <span>阶段分布</span>
        </div>
        <div class="dash-body dash-body--centered">
          <LearningSectionDonut :rows="overview.rows" />
        </div>
        <div class="dash-foot">
          <template v-for="ps in phaseStats" :key="ps.phase">
            <span v-if="ps.total > 0">{{ ps.phase }}: {{ ps.done }}/{{ ps.total }}</span>
          </template>
        </div>
      </div>

      <div class="dash-card dash-card--bars">
        <div class="dash-head">
          <el-icon><Guide /></el-icon>
          <span>模块进度</span>
        </div>
        <div class="dash-body">
          <LearningModuleBarChart :rows="availableRows" :max-items="6" />
        </div>
      </div>

      <div class="dash-card dash-card--heatmap">
        <div class="dash-head">
          <el-icon><Calendar /></el-icon>
          <span>学习活跃度</span>
        </div>
        <div class="dash-body">
          <LearningActivityHeatmap :days="activityDays" :weeks="10" />
        </div>
        <div class="dash-foot">
          <span>近 10 周学习轨迹</span>
        </div>
      </div>
    </section>

    <section
      v-if="isLoggedIn"
      ref="onboardingSectionRef"
      id="onboarding"
      class="onboarding-section"
      :class="{ 'onboarding-section--highlight': route.query.onboarding === '1' }"
    >
      <div class="onboarding-head">
        <h3 class="section-title">
          <el-icon><Timer /></el-icon>
          新生破冰访谈 · 六维画像
        </h3>
        <el-tag type="success" effect="plain" size="small">画像驱动</el-tag>
      </div>
      <PersonaChatPanel @profile-ready="onProfileReady" />
    </section>

    <el-row :gutter="16" class="tip-row">
      <el-col :xs="24" :md="12">
        <div class="tip-card">
          <el-icon class="tip-icon"><Guide /></el-icon>
          <div>
            <div class="tip-title">阶段目标</div>
            <p class="tip-desc">从基础结构到进阶算法，循序渐进掌握面试核心知识体系。</p>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="tip-card">
          <el-icon class="tip-icon"><TrendCharts /></el-icon>
          <div>
            <div class="tip-title">进度同步</div>
            <p class="tip-desc">
              已跟踪 {{ overview.trackedModules }} 个模块，总进度 {{ overview.overallPercent }}%。登录后可将进度同步至云端。
            </p>
          </div>
        </div>
      </el-col>
    </el-row>

    <PathReplanDiffCard
      v-if="isLoggedIn && lastReplanDiff"
      :diff="lastReplanDiff"
      @dismiss="clearReplanDiff"
    />

    <section class="analytics-section" v-if="isLoggedIn">
      <div class="analytics-grid">
        <LearningEvaluationPanel class="analytics-panel" />
        <LearningEffectivenessCard class="analytics-panel" />
      </div>
    </section>

    <section class="path-explorer-grid">
      <div class="universe-panel">
        <div class="panel-heading">
          <div>
            <h3 class="section-title">算法知识宇宙</h3>
            <p class="muted section-desc">
              以数据结构、算法范式、练习任务三层构建竞赛式学习星图，支持滚轮缩放、拖拽与路径自动巡航。
            </p>
          </div>
          <el-tag effect="plain" type="success">DAG 路径引擎</el-tag>
        </div>
        <AlgorithmUniverseGraph
          :key="`${universeKey}-${highlightKey ?? 'default'}`"
          :highlight-key="highlightKey"
          :auto-start-tour="autoTour"
        />
      </div>

      <aside class="concept-side-panel">
        <div class="panel-heading panel-heading--compact">
          <div>
            <h3 class="section-title">概念依赖图谱 · 可交互探索</h3>
            <p class="muted section-desc">
              基于 <code>concept_graph.json</code> 的先修关系与题目关联，点击节点跳转到模块或 OJ 练习。
            </p>
          </div>
        </div>
        <ConceptKnowledgeGraph
          :module-key="highlightKey"
          :highlight-path-ids="pathHighlightIds"
          height="520px"
        />
        <RecommendedResourcesPanel
          v-if="isLoggedIn"
          :module-key="highlightKey ?? plan?.next_module_key ?? ''"
          title="路径关联推荐资源"
        />
      </aside>
    </section>
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
  margin-bottom: 20px;
  padding: 16px 18px;
  border-radius: var(--alp-radius-card);
  background: linear-gradient(135deg, color-mix(in srgb, var(--alp-color-primary) 8%, var(--alp-bg-soft-block)), var(--alp-bg-soft-block));
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
  margin: 0 0 8px;
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
  line-height: 1.6;
}

.hero-stats {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.stat-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  min-width: 72px;
}

.stat-mini-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--alp-color-primary);
  font-variant-numeric: tabular-nums;
}

.stat-mini-label {
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-top: 2px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.dash-card {
  display: flex;
  flex-direction: column;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  min-height: 180px;
}

.dash-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin-bottom: 10px;
}

.dash-head .el-icon {
  color: var(--alp-color-primary);
  font-size: 15px;
}

.dash-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.dash-body--centered {
  align-items: center;
  justify-content: center;
}

.dash-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--alp-color-border);
}

.dash-card--bars .dash-body {
  padding: 0;
}

.dash-card--heatmap .dash-body {
  padding: 4px 0;
  overflow-x: auto;
}

@media (max-width: 1100px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .page-hero {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-stats {
    justify-content: space-between;
  }
}

.muted {
  color: var(--alp-color-muted);
  line-height: 1.6;
  margin-bottom: 16px;
}

.tip-row {
  margin-bottom: 20px;
}

.tip-card {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  height: 100%;
}

.tip-icon {
  font-size: 22px;
  color: var(--alp-color-primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.tip-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--alp-color-text);
  margin-bottom: 4px;
}

.tip-desc {
  margin: 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.55;
}

.onboarding-section {
  margin-bottom: 24px;
  padding: 16px;
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.onboarding-section--highlight {
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 45%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-primary) 5%, var(--alp-bg-surface));
  animation: onboarding-glow 2.4s ease-in-out infinite;
}

@keyframes onboarding-glow {
  0%, 100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--alp-color-primary) 15%, transparent);
  }
  50% {
    box-shadow: 0 0 24px 2px color-mix(in srgb, var(--alp-color-primary) 22%, transparent);
  }
}

.onboarding-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--alp-color-text);
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-title .el-icon {
  color: var(--alp-color-primary);
}

.analytics-section {
  margin-bottom: 20px;
}

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.analytics-panel {
  min-height: 200px;
}

@media (max-width: 900px) {
  .analytics-grid {
    grid-template-columns: 1fr;
  }
}

.path-explorer-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 18px;
  align-items: start;
}

.universe-panel,
.concept-side-panel {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
}

.universe-panel {
  min-width: 0;
  overflow: hidden;
}

.concept-side-panel {
  position: sticky;
  top: calc(var(--alp-header-height, 60px) + 16px);
  max-height: calc(100vh - var(--alp-header-height, 60px) - 32px);
  overflow: auto;
  padding: 14px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px 0;
}

.panel-heading--compact {
  padding: 0;
}

.section-desc {
  margin: 0;
  font-size: 13px;
}

.universe-panel :deep(.algorithm-universe) {
  border: 0;
  border-radius: 0;
}

.concept-side-panel :deep(.concept-graph-card) {
  border-radius: calc(var(--alp-radius-card) - 2px);
}

.concept-side-panel :deep(.recommended-resources-panel) {
  margin-top: 14px;
}

@media (max-width: 1180px) {
  .path-explorer-grid {
    grid-template-columns: 1fr;
  }

  .concept-side-panel {
    position: static;
    max-height: none;
  }
}
</style>