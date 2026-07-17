<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Cpu, DataAnalysis, RefreshRight, TrendCharts, User } from '@element-plus/icons-vue'
import { fetchOjAnalytics, type OjAnalyticsResponse } from '@/api/teacherDashboard'

const router = useRouter()
const loading = ref(false)
const loadError = ref('')
const data = ref<OjAnalyticsResponse | null>(null)

const maxModuleSubmissions = computed(() =>
  Math.max(...(data.value?.per_module.map((m) => m.total_submissions) ?? []), 1),
)

function rateColor(rate: number): string {
  if (rate >= 70) return '#6aa878'
  if (rate >= 40) return '#9c7a3d'
  return '#9e6470'
}

function formatDate(value: string): string {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function barWidth(value: number, max: number): string {
  return `${Math.max(4, Math.round((value / max) * 100))}%`
}

function goToProblem(slug: string) {
  router.push({ name: 'practice-problem', params: { slug } })
}

async function loadData() {
  loading.value = true
  loadError.value = ''
  try {
    data.value = await fetchOjAnalytics()
  } catch {
    loadError.value = 'OJ 学情数据暂时无法加载，请确认后端服务已启动后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <main class="oj-analytics">
    <section class="dashboard-hero">
      <div class="hero-copy">
        <div class="hero-kicker">
          <el-icon><DataAnalysis /></el-icon>
          AlgoPilot OJ 学情
        </div>
        <h1>OJ 提交学情分析</h1>
        <p>
          汇总全班 OJ 提交与通过情况，按题目和模块维度分析通过率与常见错误，
          帮助教师定位需要集中讲解的题目与知识点。
        </p>
        <div class="hero-meta">
          <span>数据更新时间：{{ formatDate(data?.generated_at || '') }}</span>
          <span>课程：数据结构与算法</span>
        </div>
      </div>
      <div class="hero-actions">
        <el-button :loading="loading" :icon="RefreshRight" @click="loadData">
          刷新数据
        </el-button>
      </div>
    </section>

    <el-alert
      v-if="loadError"
      class="load-alert"
      type="error"
      :title="loadError"
      show-icon
      :closable="false"
    />

    <div v-if="loading && !data" class="loading-card">
      <el-skeleton :rows="10" animated />
    </div>

    <template v-else-if="data">
      <section class="dashboard-section">
        <div class="metric-grid">
          <article class="metric-card metric-card--blue">
            <div class="metric-icon"><el-icon><Cpu /></el-icon></div>
            <div>
              <strong>{{ data.total_submissions }}</strong>
              <span>提交总数</span>
            </div>
          </article>
          <article class="metric-card metric-card--green">
            <div class="metric-icon"><el-icon><TrendCharts /></el-icon></div>
            <div>
              <strong>{{ data.accepted }}</strong>
              <span>通过数</span>
            </div>
          </article>
          <article class="metric-card metric-card--orange">
            <div class="metric-icon"><el-icon><TrendCharts /></el-icon></div>
            <div>
              <strong :style="{ color: rateColor(data.acceptance_rate) }">{{ data.acceptance_rate.toFixed(1) }}%</strong>
              <span>通过率</span>
            </div>
          </article>
          <article class="metric-card metric-card--purple">
            <div class="metric-icon"><el-icon><User /></el-icon></div>
            <div>
              <strong>{{ data.active_students }}</strong>
              <span>活跃学生数</span>
            </div>
          </article>
        </div>
      </section>

      <section v-if="data.per_module.length" class="dashboard-section">
        <div class="section-heading">
          <div>
            <span class="section-eyebrow">MODULE STATS</span>
            <h2>分模块通过情况</h2>
          </div>
          <span class="section-caption">按模块聚合提交与通过率</span>
        </div>
        <div class="panel-card">
          <div class="module-list">
            <div
              v-for="mod in data.per_module"
              :key="mod.module_key"
              class="module-item"
            >
              <div class="module-info">
                <strong>{{ mod.module_label }}</strong>
                <span>{{ mod.accepted }}/{{ mod.total_submissions }} 通过</span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: barWidth(mod.total_submissions, maxModuleSubmissions), background: rateColor(mod.acceptance_rate) }"
                />
              </div>
              <strong class="module-rate" :style="{ color: rateColor(mod.acceptance_rate) }">
                {{ mod.acceptance_rate.toFixed(1) }}%
              </strong>
            </div>
          </div>
        </div>
      </section>

      <section v-if="data.per_problem.length" class="dashboard-section">
        <div class="section-heading">
          <div>
            <span class="section-eyebrow">PROBLEM STATS</span>
            <h2>题目通过情况</h2>
          </div>
          <span class="section-caption">点击行可跳转到做题页预览</span>
        </div>
        <div class="table-card">
          <el-table
            :data="data.per_problem"
            stripe
            style="width: 100%"
            row-class-name="problem-row"
            empty-text="暂无题目提交记录"
            @row-click="(row: any) => goToProblem(row.slug)"
          >
            <el-table-column prop="title" label="题目" min-width="180">
              <template #default="{ row }">
                <div class="problem-title-cell">
                  <el-icon class="problem-icon"><Cpu /></el-icon>
                  <span>{{ row.title }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="module_label" label="模块" min-width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" effect="plain">{{ row.module_label || '未分类' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_submissions" label="提交数" min-width="80" align="center" />
            <el-table-column prop="accepted" label="通过数" min-width="80" align="center" />
            <el-table-column label="通过率" min-width="160" align="center">
              <template #default="{ row }">
                <div class="rate-cell">
                  <div class="bar-track">
                    <div
                      class="bar-fill"
                      :style="{ width: `${row.acceptance_rate}%`, background: rateColor(row.acceptance_rate) }"
                    />
                  </div>
                  <span :style="{ color: rateColor(row.acceptance_rate) }">{{ row.acceptance_rate.toFixed(1) }}%</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="常见错误" min-width="200">
              <template #default="{ row }">
                <div v-if="row.common_errors.length" class="error-tags">
                  <el-tag
                    v-for="(err, i) in row.common_errors"
                    :key="i"
                    size="small"
                    type="danger"
                    effect="plain"
                  >
                    {{ err.length > 30 ? err.slice(0, 30) + '...' : err }}
                  </el-tag>
                </div>
                <span v-else class="text-muted">--</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <el-empty
        v-if="!data.per_module.length && !data.per_problem.length"
        description="暂无 OJ 提交记录，学生开始做题后这里会展示分析数据"
        :image-size="100"
      />
    </template>
  </main>
</template>

<style scoped>
.oj-analytics {
  width: min(1440px, 100%);
  margin: 0 auto;
  color: var(--alp-color-text);
}

.dashboard-hero {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 30px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 32%, var(--alp-color-border));
  border-radius: 18px;
  background:
    rgba(58, 138, 158, 0.2),
    rgba(14, 116, 144, 0.22),
    var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
}

.dashboard-hero::after {
  position: absolute;
  right: 8%;
  bottom: -90px;
  width: 260px;
  height: 260px;
  content: '';
  border: 1px solid rgba(34, 211, 238, 0.16);
  border-radius: 50%;
  box-shadow: 0 0 0 34px rgba(34, 211, 238, 0.04), 0 0 0 70px rgba(129, 140, 248, 0.03);
  pointer-events: none;
}

.hero-copy,
.hero-actions {
  position: relative;
  z-index: 1;
}

.hero-copy h1 {
  margin: 8px 0 10px;
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.15;
}

.hero-copy p {
  max-width: 760px;
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 15px;
  line-height: 1.8;
}

.hero-kicker,
.section-eyebrow {
  color: var(--alp-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 7px;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  margin-top: 18px;
  color: var(--alp-color-muted);
  font-size: 12px;
}

.hero-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.load-alert,
.loading-card {
  margin-top: 18px;
}

.loading-card,
.panel-card {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
}

.loading-card {
  padding: 24px;
}

.dashboard-section {
  margin-top: 28px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.section-heading h2 {
  margin: 4px 0 0;
  font-size: 20px;
}

.section-caption {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 13px;
  min-height: 92px;
  padding: 16px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--metric-color) 55%, var(--alp-color-border));
  box-shadow: var(--alp-shadow-card-hover);
}

.metric-card--blue { --metric-color: #3a8a9e; }
.metric-card--green { --metric-color: #6aa878; }
.metric-card--orange { --metric-color: #9c7a3d; }
.metric-card--purple { --metric-color: #7a6e9e; }

.metric-icon {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  place-items: center;
  border-radius: 12px;
  background: color-mix(in srgb, var(--metric-color) 16%, transparent);
  color: var(--metric-color);
  font-size: 20px;
}

.metric-card strong,
.metric-card span {
  display: block;
}

.metric-card strong {
  font-size: 25px;
  font-variant-numeric: tabular-nums;
}

.metric-card span {
  margin-top: 3px;
  color: var(--alp-color-muted);
  font-size: 12px;
}

.panel-card {
  padding: 20px;
}

.module-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.module-item {
  display: grid;
  grid-template-columns: 160px 1fr 60px;
  align-items: center;
  gap: 14px;
}

.module-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.module-info strong {
  font-size: 14px;
}

.module-info span {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.bar-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-muted) 14%, transparent);
}

.bar-fill {
  height: 100%;
  border-radius: inherit;
  background: #3a8a9e;
  transition: width 0.5s ease;
}

.module-rate {
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.table-card {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  overflow: hidden;
}

.problem-title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.problem-icon {
  color: var(--alp-color-primary);
  flex-shrink: 0;
}

.rate-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rate-cell .bar-track {
  flex: 1;
  min-width: 40px;
  height: 8px;
}

.error-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.text-muted {
  color: var(--alp-color-muted);
  font-size: 12px;
}

:deep(.problem-row) {
  cursor: pointer;
  transition: background var(--alp-transition-fast);
}

:deep(.problem-row:hover) {
  background: var(--alp-bg-nav-hover);
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .dashboard-hero,
  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .module-item {
    grid-template-columns: 1fr;
    gap: 6px;
  }
}
</style>
