<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Timer } from '@element-plus/icons-vue'
import LearningPathCommandCenter from '@/components/learning/LearningPathCommandCenter.vue'
import PersonaChatPanel from '@/components/persona/PersonaChatPanel.vue'
import PathReplanDiffCard from '@/components/learning/PathReplanDiffCard.vue'
import StudyPlanDashboard from '@/components/learning/StudyPlanDashboard.vue'
import LearningEffectivenessCard from '@/components/learning/LearningEffectivenessCard.vue'
import LearningEvaluationPanel from '@/components/learning/LearningEvaluationPanel.vue'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'
import { isLoggedIn } from '@/stores/auth'
import type { PersonaProfile } from '@/api/orchestrator'

const route = useRoute()
const { loadPlan, lastReplanDiff, clearReplanDiff } = useLearningPathPlan()
const universeKey = ref(0)

const highlightKey = computed(() => {
  const q = route.query.module
  return typeof q === 'string' ? q : undefined
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
  <el-card shadow="never" class="page-card learning-page">
    <StudyPlanDashboard />

    <section
      v-if="isLoggedIn"
      ref="onboardingSectionRef"
      id="onboarding"
      class="onboarding-section"
      :class="{ 'onboarding-section--highlight': route.query.onboarding === '1' }"
    >
      <div class="onboarding-head">
        <div class="onboarding-head-main">
          <h3 class="section-title">
            <el-icon><Timer /></el-icon>
            新生破冰访谈 · 六维画像
          </h3>
          <p class="muted section-desc">
            与学习画像 Agent 进行 4 轮破冰对话，系统将自动抽取知识基础、认知风格、代码实操、学习目标、易错偏好、抗挫心理六维画像，驱动个性化学习路径与资源推荐。
          </p>
        </div>
        <el-tag type="success" effect="plain" size="small">画像驱动</el-tag>
      </div>
      <PersonaChatPanel @profile-ready="onProfileReady" />
    </section>

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

    <LearningPathCommandCenter
      :key="`${universeKey}-${highlightKey ?? 'default'}`"
      :highlight-key="highlightKey"
      @replan="universeKey += 1"
    />
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.onboarding-head-main {
  min-width: 0;
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

</style>
