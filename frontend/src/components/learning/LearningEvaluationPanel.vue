<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis } from '@element-plus/icons-vue'
import LearningDimensionRadar from '@/components/learning/LearningDimensionRadar.vue'
import { fetchLearningEvaluation, type LearningEvaluation } from '@/api/orchestrator'
import { buildLearningOverview } from '@/utils/learningOverview'
import { isLoggedIn } from '@/stores/auth'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'

const loading = ref(false)
const loadFailed = ref(false)
const report = ref<LearningEvaluation | null>(null)
const { replan } = useLearningPathPlan()

function buildPayload() {
  const o = buildLearningOverview()
  return {
    overall_percent: o.overallPercent,
    modules: o.rows.map((r) => ({
      key: r.key,
      label: r.label,
      phase: r.phase,
      available: r.available,
      percent: r.percent,
      done_count: r.doneCount,
      total_count: r.totalCount,
    })),
  }
}

async function runEvaluation() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    return
  }
  loading.value = true
  loadFailed.value = false
  try {
    report.value = await fetchLearningEvaluation(buildPayload())
  } catch {
    loadFailed.value = true
    ElMessage.warning('评估报告加载失败，请检查登录状态或稍后重试')
  } finally {
    loading.value = false
  }
}

async function applyStrategy() {
  if (!report.value) return
  await replan({
    trigger: 'evaluation',
    triggerLabel: '按评估重排路径',
    evidence: [
      `EvaluationAgent 综合得分 ${report.value.overall_score}`,
      ...(report.value.weak_module_keys?.length
        ? [`薄弱模块：${report.value.weak_module_keys.join('、')}`]
        : []),
      report.value.push_strategy,
      ...report.value.suggestions.slice(0, 2),
    ].filter(Boolean),
  })
  ElMessage.success('已根据评估结果重新规划学习路径')
}

onMounted(() => {
  if (isLoggedIn.value) void runEvaluation()
})
</script>

<template>
  <el-card v-loading="loading" shadow="never" class="eval-card">
    <div class="eval-head">
      <el-icon><DataAnalysis /></el-icon>
      <span>EvaluationAgent · 学习效果评估</span>
      <el-button size="small" :loading="loading" @click="runEvaluation">刷新评估</el-button>
    </div>

    <el-empty v-if="!isLoggedIn && !loading" description="登录后生成多维度评估报告" />
    <el-empty v-else-if="loadFailed && !report" description="评估加载失败">
      <el-button type="primary" plain size="small" @click="runEvaluation">重试</el-button>
    </el-empty>
    <el-empty v-else-if="!report && !loading" description="点击「刷新评估」生成报告" />

    <template v-else-if="report">
      <div class="overall">
        综合得分 <strong>{{ report.overall_score }}</strong>
      </div>
      <p class="narrative">{{ report.narrative }}</p>
      <LearningDimensionRadar v-if="report.dimensions.length" :dimensions="report.dimensions" />
      <el-row :gutter="10" class="dim-row">
        <el-col v-for="d in report.dimensions" :key="d.key" :xs="12" :sm="6">
          <div class="dim-tile">
            <span>{{ d.label }}</span>
            <el-progress :percentage="d.score" :stroke-width="6" />
          </div>
        </el-col>
      </el-row>
      <p class="strategy"><strong>推送策略：</strong>{{ report.push_strategy }}</p>
      <ul v-if="report.suggestions.length" class="suggestions">
        <li v-for="(s, i) in report.suggestions" :key="i">{{ s }}</li>
      </ul>
      <el-button type="primary" plain size="small" @click="applyStrategy">
        按评估重排学习路径
      </el-button>
    </template>
  </el-card>
</template>

<style scoped>
.eval-card {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
}

.eval-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
}

.eval-head .el-button {
  margin-left: auto;
}

.overall {
  font-size: 14px;
  margin-bottom: 8px;
}

.overall strong {
  font-size: 28px;
  color: var(--alp-color-primary);
}

.narrative,
.strategy {
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.6;
}

.dim-row {
  margin: 12px 0;
}

.dim-tile {
  padding: 8px;
  background: var(--alp-bg-soft-block);
  border-radius: 8px;
  margin-bottom: 8px;
  font-size: 12px;
}

.suggestions {
  margin: 8px 0 12px;
  padding-left: 18px;
  font-size: 13px;
}
</style>
