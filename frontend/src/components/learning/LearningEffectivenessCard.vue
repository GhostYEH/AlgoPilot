<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { Download, DataLine, TrendCharts } from '@element-plus/icons-vue'
import { fetchEffectiveness, getEffectivenessCsvUrl, type EffectivenessResponse } from '@/api/analytics'
import { isLoggedIn } from '@/stores/auth'

const loading = ref(false)
const data = ref<EffectivenessResponse | null>(null)

const totalDelta = computed(() => (data.value?.rows || []).reduce((s, r) => s + r.mastery_delta, 0))
const totalTraceCount = computed(() => (data.value?.rows || []).reduce((s, r) => s + r.trace_diagnosis_count, 0))
const totalResourceDone = computed(() => (data.value?.rows || []).reduce((s, r) => s + r.resource_completion_count, 0))
const overallAcceptRate = computed(() => {
  const rows = data.value?.rows || []
  const attempts = rows.reduce((s, r) => s + r.oj_attempts, 0)
  const failures = rows.reduce((s, r) => s + r.oj_failures, 0)
  if (attempts === 0) return 0
  return Math.round(((attempts - failures) / attempts) * 100)
})

onMounted(async () => {
  if (!isLoggedIn.value) return
  loading.value = true
  try {
    data.value = await fetchEffectiveness()
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
})

function handleExportCsv() {
  const url = getEffectivenessCsvUrl()
  const token = localStorage.getItem('access_token')
  const a = document.createElement('a')
  a.href = url
  if (token) {
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((blob) => {
        const objUrl = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = objUrl
        link.download = 'effectiveness_export.csv'
        link.click()
        URL.revokeObjectURL(objUrl)
      })
      .catch(() => {
        window.open(url, '_blank')
      })
    return
  }
  a.download = 'effectiveness_export.csv'
  a.click()
}

function deltaColor(delta: number): string {
  if (delta > 0) return 'var(--el-color-success)'
  if (delta < 0) return 'var(--el-color-danger)'
  return 'var(--alp-color-muted)'
}

function deltaLabel(delta: number): string {
  if (delta > 0) return `+${delta}`
  return `${delta}`
}
</script>

<template>
  <div class="effectiveness-card">
    <div class="card-header">
      <h3 class="section-title">学习效果证据</h3>
      <el-button
        type="primary"
        size="small"
        :icon="Download"
        :disabled="!data || data.rows.length === 0"
        @click="handleExportCsv"
      >
        导出 CSV
      </el-button>
    </div>

    <el-skeleton :loading="loading" animated :rows="3">
      <template v-if="data">
        <el-alert
          v-if="data.partial"
          type="info"
          show-icon
          :closable="false"
          class="partial-alert"
        >
          部分数据暂缺（{{ data.missing_fields.join('、') }}），统计结果可能不完整
        </el-alert>

        <el-empty
          v-if="data.rows.length === 0"
          description="暂无学习行为记录，完成章节学习与 OJ 练习后即可生成效果证据"
        />

        <template v-else>
          <el-row :gutter="12" class="stat-row">
            <el-col :xs="12" :sm="6">
              <div class="stat-tile">
                <el-icon class="stat-icon"><TrendCharts /></el-icon>
                <strong :style="{ color: deltaColor(totalDelta) }">{{ deltaLabel(totalDelta) }}</strong>
                <span>掌握度变化</span>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="stat-tile">
                <el-icon class="stat-icon"><DataLine /></el-icon>
                <strong>{{ overallAcceptRate }}%</strong>
                <span>OJ 通过率</span>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="stat-tile">
                <strong>{{ totalTraceCount }}</strong>
                <span>Trace 诊断次数</span>
              </div>
            </el-col>
            <el-col :xs="12" :sm="6">
              <div class="stat-tile">
                <strong>{{ totalResourceDone }}</strong>
                <span>资源完成数</span>
              </div>
            </el-col>
          </el-row>

          <el-table :data="data.rows" stripe size="small" class="effect-table">
            <el-table-column prop="chapter_id" label="章节" min-width="140" />
            <el-table-column prop="skill_id" label="技能" min-width="120" />
            <el-table-column label="掌握度变化" min-width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: deltaColor(row.mastery_delta), fontWeight: 600 }">
                  {{ deltaLabel(row.mastery_delta) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="oj_attempts" label="OJ 提交" width="90" align="center" />
            <el-table-column prop="oj_failures" label="OJ 失败" width="90" align="center" />
            <el-table-column prop="trace_diagnosis_count" label="诊断次数" width="90" align="center" />
            <el-table-column prop="resource_completion_count" label="资源完成" width="90" align="center" />
            <el-table-column prop="improvement_summary" label="效果摘要" min-width="200" show-overflow-tooltip />
          </el-table>
        </template>
      </template>
    </el-skeleton>
  </div>
</template>

<style scoped>
.effectiveness-card {
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.section-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.partial-alert {
  margin-bottom: 12px;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  text-align: center;
}

.stat-icon {
  font-size: 18px;
  color: var(--alp-color-primary);
}

.stat-tile strong {
  font-size: 20px;
  color: var(--alp-color-text);
}

.stat-tile span {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.effect-table {
  width: 100%;
}
</style>
