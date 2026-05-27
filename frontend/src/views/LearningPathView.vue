<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Guide, TrendCharts } from '@element-plus/icons-vue'
import AlgorithmUniverseGraph from '@/components/learning/AlgorithmUniverseGraph.vue'
import ConceptKnowledgeGraph from '@/components/learning/ConceptKnowledgeGraph.vue'
import PersonaChatPanel from '@/components/persona/PersonaChatPanel.vue'
import RecommendedResourcesPanel from '@/components/learning/RecommendedResourcesPanel.vue'
import { ALGORITHM_MODULES } from '@/constants/modules'
import { buildLearningOverview } from '@/utils/learningOverview'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'
import { isLoggedIn } from '@/stores/auth'
import type { PersonaProfile } from '@/api/orchestrator'

const route = useRoute()
const router = useRouter()
const { plan, loadPlan } = useLearningPathPlan()
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

async function onProfileReady(_profile: PersonaProfile) {
  await loadPlan()
  universeKey.value += 1
  autoTour.value = true
}

const autoTour = ref(false)
const onboardingSectionRef = ref<HTMLElement | null>(null)

onMounted(async () => {
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

    <p class="muted">
      <strong>ProfilerAgent + PlannerAgent</strong>：登录后先完成破冰访谈，系统将抽取六维画像并在<strong>算法知识宇宙</strong>中生成可探索的 DAG 星图——滚轮缩放、拖拽漫游，单击节点进入微观资源层。
      <template v-if="highlightKey">
        当前聚焦：<el-tag type="primary" effect="plain">{{ moduleLabel }}</el-tag>
      </template>
    </p>

    <section
      v-if="isLoggedIn"
      ref="onboardingSectionRef"
      id="onboarding"
      class="onboarding-section"
      :class="{ 'onboarding-section--highlight': route.query.onboarding === '1' }"
    >
      <h3 class="section-title">新生破冰访谈 · 六维画像</h3>
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

    <section class="universe-section">
      <AlgorithmUniverseGraph
        :key="`${universeKey}-${highlightKey ?? 'default'}`"
        :highlight-key="highlightKey"
        :auto-start-tour="autoTour"
      />
    </section>

    <section class="concept-graph-section">
      <h3 class="section-title">概念依赖图谱 · 可交互探索</h3>
      <p class="muted section-desc">
        基于 <code>concept_graph.json</code> 的先修关系与题目关联；滚轮缩放、拖拽平移，点击节点跳转模块或 OJ 练习。
      </p>
      <ConceptKnowledgeGraph
        :module-key="highlightKey"
        :highlight-path-ids="pathHighlightIds"
        height="440px"
      />
    </section>

    <RecommendedResourcesPanel
      v-if="isLoggedIn"
      :module-key="highlightKey ?? plan?.next_module_key ?? ''"
      title="路径关联推荐资源"
    />
  </el-card>
</template>

<style scoped>
.page-card {
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
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
}

.onboarding-section--highlight {
  padding: 16px;
  border-radius: var(--alp-radius-card);
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 45%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-primary) 5%, var(--alp-bg-surface));
  animation: onboarding-glow 2.4s ease-in-out infinite;
}

@keyframes onboarding-glow {
  0%,
  100% {
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--alp-color-primary) 15%, transparent);
  }
  50% {
    box-shadow: 0 0 24px 2px color-mix(in srgb, var(--alp-color-primary) 22%, transparent);
  }
}

.section-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.universe-section {
  margin: 0 -4px 8px;
}

@media (min-width: 960px) {
  .universe-section {
    margin-left: -12px;
    margin-right: -12px;
  }
}

</style>
