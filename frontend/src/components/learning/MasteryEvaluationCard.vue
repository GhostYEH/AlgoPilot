<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts } from '@element-plus/icons-vue'
import {
  fetchMasteryReport,
  recalculateMastery,
  MASTERY_LEVEL_LABELS,
  MASTERY_TREND_LABELS,
  CONFIDENCE_LEVEL_LABELS,
  type MasteryOverview,
  type MasteryReport,
} from '@/api/mastery'
import { buildLearningOverview } from '@/utils/learningOverview'
import { isLoggedIn } from '@/stores/auth'

const loading = ref(false)
const loadFailed = ref(false)
const overview = ref<MasteryOverview | null>(null)

const levelTagType = computed(() => {
  const level = overview.value?.overall_level ?? 'beginner'
  if (level === 'advanced') return 'success'
  if (level === 'competent') return 'primary'
  if (level === 'improving') return 'warning'
  return 'danger'
})

const topChapters = computed(() => {
  const list = overview.value?.chapters ?? []
  return [...list].sort((a, b) => a.mastery_score - b.mastery_score).slice(0, 6)
})

const primaryReport = computed<MasteryReport | null>(
  () => overview.value?.report ?? overview.value?.chapters?.[0] ?? null,
)

const trendTagType = computed(() => {
  const trend = primaryReport.value?.mastery_trend ?? 'stable'
  if (trend === 'rising') return 'success'
  if (trend === 'falling') return 'danger'
  return 'info'
})

const confidenceTagType = computed(() => {
  const level = primaryReport.value?.confidence_level ?? 'low'
  if (level === 'high') return 'success'
  if (level === 'medium') return 'warning'
  return 'info'
})

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

async function loadReport(recalc = false) {
  if (!isLoggedIn.value) return
  loading.value = true
  loadFailed.value = false
  try {
    if (recalc) {
      const r = await recalculateMastery(buildPayload())
      overview.value = r.overview
      ElMessage.success('掌握度已重新计算')
    } else {
      overview.value = await fetchMasteryReport()
    }
  } catch {
    loadFailed.value = true
    ElMessage.warning('掌握度报告加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (isLoggedIn.value) void loadReport()
})

defineExpose({ reload: () => loadReport(true) })
</script>

<template>
  <el-card v-loading="loading" shadow="never" class="mastery-card">
    <div class="mastery-head">
      <el-icon><TrendCharts /></el-icon>
      <span>MasteryAgent · 学习效果掌握度评估</span>
      <el-button size="small" :loading="loading" @click="loadReport(true)">重新计算</el-button>
    </div>

    <el-empty
      v-if="!isLoggedIn && !loading"
      description="登录后生成可解释掌握度报告"
    />
    <el-empty v-else-if="loadFailed && !overview" description="报告加载失败">
      <el-button type="primary" plain size="small" @click="loadReport()">重试</el-button>
    </el-empty>
    <el-empty v-else-if="!overview && !loading" description="暂无掌握度数据，点击重新计算" />

    <template v-else-if="overview">
      <div class="score-row">
        <div class="score-main">
          <span class="label">总掌握度</span>
          <strong class="score">{{ overview.overall_score }}</strong>
          <el-tag :type="levelTagType" size="small">
            {{ MASTERY_LEVEL_LABELS[overview.overall_level] }}
          </el-tag>
        </div>
        <p v-if="primaryReport?.path_adjustment_suggestion" class="path-hint">
          {{ primaryReport.path_adjustment_suggestion }}
        </p>
      </div>

      <div v-if="primaryReport" class="bkt-lite-row">
        <div class="bkt-lite-item">
          <span class="bkt-label">掌握概率</span>
          <strong class="bkt-prob">{{ (primaryReport.mastery_probability * 100).toFixed(0) }}%</strong>
        </div>
        <div class="bkt-lite-item">
          <span class="bkt-label">趋势</span>
          <el-tag :type="trendTagType" size="small">
            {{ MASTERY_TREND_LABELS[primaryReport.mastery_trend] }}
          </el-tag>
        </div>
        <div class="bkt-lite-item">
          <span class="bkt-label">置信度</span>
          <el-tag :type="confidenceTagType" size="small">
            {{ CONFIDENCE_LEVEL_LABELS[primaryReport.confidence_level] }}
          </el-tag>
        </div>
      </div>

      <p v-if="primaryReport?.probability_explanation" class="prob-explanation">
        {{ primaryReport.probability_explanation }}
      </p>

      <div v-if="topChapters.length" class="section">
        <h4>章节掌握度</h4>
        <div class="chapter-grid">
          <div v-for="ch in topChapters" :key="ch.chapter_id" class="chapter-tile">
            <div class="ch-title">{{ ch.chapter_title || ch.chapter_id }}</div>
            <el-progress
              :percentage="ch.mastery_score"
              :stroke-width="8"
              :status="ch.mastery_score >= 60 ? 'success' : ch.mastery_score < 40 ? 'exception' : undefined"
            />
            <span class="ch-level">{{ MASTERY_LEVEL_LABELS[ch.mastery_level] }}</span>
          </div>
        </div>
      </div>

      <div v-if="primaryReport?.weak_skills?.length" class="section">
        <h4>薄弱技能</h4>
        <el-space wrap>
          <el-tag v-for="s in primaryReport.weak_skills" :key="s" type="danger" effect="plain">
            {{ s }}
          </el-tag>
        </el-space>
      </div>

      <div v-if="primaryReport?.component_scores?.length" class="section">
        <h4>为什么这样评估</h4>
        <ul class="evidence-list">
          <li v-for="c in primaryReport.component_scores" :key="c.key">
            <strong>{{ c.label }}</strong> {{ c.score.toFixed(0) }} 分（权重 {{ Math.round(c.weight * 100) }}%）
            <span class="muted">— {{ c.note }}</span>
          </li>
        </ul>
      </div>

      <div v-else-if="primaryReport?.evidence?.length" class="section">
        <h4>为什么这样评估</h4>
        <ul class="evidence-list">
          <li v-for="(e, i) in primaryReport.evidence.slice(0, 6)" :key="i">{{ e.detail }}</li>
        </ul>
      </div>

      <div v-if="primaryReport?.recommended_actions?.length" class="section">
        <h4>下一步建议</h4>
        <ul class="action-list">
          <li v-for="(a, i) in primaryReport.recommended_actions" :key="i">{{ a }}</li>
        </ul>
      </div>

      <div v-if="primaryReport?.recommended_resources?.length" class="section">
        <h4>推荐资源</h4>
        <el-space wrap>
          <el-tag
            v-for="(r, i) in primaryReport.recommended_resources"
            :key="i"
            type="info"
            effect="plain"
          >
            {{ r.resource_type }} · {{ r.topic }}
          </el-tag>
        </el-space>
      </div>
    </template>
  </el-card>
</template>

<style scoped>
.mastery-card {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  margin-bottom: 16px;
}

.mastery-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
}

.mastery-head .el-button {
  margin-left: auto;
}

.score-row {
  margin-bottom: 16px;
}

.score-main {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.score-main .label {
  font-size: 14px;
  color: var(--alp-color-muted);
}

.score-main .score {
  font-size: 32px;
  color: var(--alp-color-primary);
}

.path-hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.bkt-lite-row {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 10px;
  padding: 10px 12px;
  background: var(--alp-bg-soft-block);
  border-radius: 8px;
}

.bkt-lite-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.bkt-label {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.bkt-prob {
  font-size: 18px;
  color: var(--alp-color-primary);
}

.prob-explanation {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.6;
}

.section {
  margin-bottom: 14px;
}

.section h4 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
}

.chapter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.chapter-tile {
  padding: 10px;
  background: var(--alp-bg-soft-block);
  border-radius: 8px;
}

.ch-title {
  font-size: 12px;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ch-level {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.evidence-list,
.action-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}

.muted {
  color: var(--alp-color-muted);
}
</style>
