<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Guide, TrendCharts } from '@element-plus/icons-vue'
import LearningPathRoadmap from '@/components/learning/LearningPathRoadmap.vue'
import RecommendedResourcesPanel from '@/components/learning/RecommendedResourcesPanel.vue'
import { ALGORITHM_MODULES } from '@/constants/modules'
import { buildLearningOverview } from '@/utils/learningOverview'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'
import { isLoggedIn } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const { plan } = useLearningPathPlan()

const highlightKey = computed(() => {
  const q = route.query.module
  return typeof q === 'string' ? q : undefined
})

const moduleLabel = computed(() => {
  if (!highlightKey.value) return ''
  return ALGORITHM_MODULES.find((m) => m.key === highlightKey.value)?.label ?? highlightKey.value
})

const overview = computed(() => buildLearningOverview())
</script>

<template>
  <el-card shadow="never" class="page-card">
    <el-page-header title="学习路径" @back="router.push({ name: 'home' })" />
    <el-divider />

    <p class="muted">
      <strong>学习路径 Agent</strong> 根据你的学习画像与各模块完成度自动重排推荐顺序；登录后可一键规划或重新规划。
      <template v-if="highlightKey">
        当前聚焦：<el-tag type="primary" effect="plain">{{ moduleLabel }}</el-tag>
      </template>
    </p>

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

    <LearningPathRoadmap :key="highlightKey ?? 'default'" :highlight-key="highlightKey" />

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

</style>
