<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Aim,
  Collection,
  Cpu,
  DataAnalysis,
  Document,
  Reading,
  RefreshRight,
  TrendCharts,
  User,
  Warning,
} from '@element-plus/icons-vue'

import {
  fetchTeacherDashboardSummary,
  type TeacherDashboardSummary,
} from '@/api/teacherDashboard'

const router = useRouter()
const loading = ref(false)
const loadError = ref('')
const summary = ref<TeacherDashboardSummary | null>(null)

const overview = computed(() => summary.value?.overview)
const maxWeakCount = computed(() =>
  Math.max(...(summary.value?.weak_knowledge_points.map((item) => item.error_count) ?? []), 1),
)
const maxErrorCount = computed(() =>
  Math.max(...(summary.value?.error_types.map((item) => item.count) ?? []), 1),
)

function barWidth(value: number, max: number) {
  return `${Math.max(4, Math.round((value / max) * 100))}%`
}

function formatGeneratedAt(value?: string) {
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

async function loadDashboard() {
  loading.value = true
  loadError.value = ''
  try {
    summary.value = await fetchTeacherDashboardSummary()
  } catch {
    loadError.value = '教学数据暂时无法加载，请确认后端服务已启动后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <main class="teacher-dashboard">
    <section class="dashboard-hero">
      <div class="hero-copy">
        <div class="hero-kicker">
          <el-icon><DataAnalysis /></el-icon>
          AlgoPilot 教学辅助
        </div>
        <h1>教师教学看板</h1>
        <p>
          汇总班级画像、学习进度、Evaluation、OJ 与资源记录，
          将学生侧学习证据转化为可执行的课堂教学建议。
        </p>
        <div class="hero-meta">
          <el-tag v-if="summary?.is_demo" type="warning" effect="dark">比赛演示数据</el-tag>
          <span>数据更新时间：{{ formatGeneratedAt(summary?.generated_at) }}</span>
          <span>课程：数据结构与算法</span>
        </div>
      </div>
      <div class="hero-actions">
        <el-button :loading="loading" :icon="RefreshRight" @click="loadDashboard">
          刷新数据
        </el-button>
        <el-button type="primary" plain @click="router.push({ name: 'a3-demo' })">
          返回比赛演示
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

    <div v-if="loading && !summary" class="loading-card">
      <el-skeleton :rows="10" animated />
    </div>

    <template v-else-if="summary">
      <p class="data-note">
        <el-icon><Aim /></el-icon>
        {{ summary.data_note }}
      </p>

      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <span class="section-eyebrow">CLASS OVERVIEW</span>
            <h2>班级学习概览</h2>
          </div>
          <span class="section-caption">一屏掌握教学落地关键指标</span>
        </div>

        <div class="metric-grid">
          <article class="metric-card metric-card--blue">
            <div class="metric-icon"><el-icon><User /></el-icon></div>
            <div>
              <strong>{{ overview?.student_count ?? 0 }}</strong>
              <span>学生数</span>
            </div>
          </article>
          <article class="metric-card metric-card--purple">
            <div class="metric-icon"><el-icon><Document /></el-icon></div>
            <div>
              <strong>{{ overview?.profile_count ?? 0 }}</strong>
              <span>已生成画像数</span>
            </div>
          </article>
          <article class="metric-card metric-card--green">
            <div class="metric-icon"><el-icon><TrendCharts /></el-icon></div>
            <div>
              <strong>{{ (overview?.average_mastery ?? 0).toFixed(1) }}%</strong>
              <span>平均掌握度</span>
            </div>
          </article>
          <article class="metric-card metric-card--orange">
            <div class="metric-icon"><el-icon><Collection /></el-icon></div>
            <div>
              <strong>{{ overview?.resource_count ?? 0 }}</strong>
              <span>资源生成数量</span>
            </div>
          </article>
          <article class="metric-card metric-card--cyan">
            <div class="metric-icon"><el-icon><Cpu /></el-icon></div>
            <div>
              <strong>{{ overview?.oj_submission_count ?? 0 }}</strong>
              <span>OJ 提交次数</span>
            </div>
          </article>
        </div>
      </section>

      <section class="analysis-grid">
        <article class="panel-card">
          <div class="panel-heading">
            <div>
              <span class="section-eyebrow">WEAK POINTS</span>
              <h2>高频薄弱知识点</h2>
            </div>
            <el-icon class="panel-icon panel-icon--danger"><Warning /></el-icon>
          </div>
          <div v-if="summary.weak_knowledge_points.length" class="ranking-list">
            <div
              v-for="(item, index) in summary.weak_knowledge_points"
              :key="item.module_key"
              class="ranking-item"
            >
              <span class="ranking-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="ranking-content">
                <div class="ranking-label">
                  <strong>{{ item.module_label }}</strong>
                  <span>{{ item.affected_students }} 名学生受影响</span>
                </div>
                <div class="bar-track">
                  <div
                    class="bar-fill bar-fill--danger"
                    :style="{ width: barWidth(item.error_count, maxWeakCount) }"
                  />
                </div>
              </div>
              <strong class="ranking-value">{{ item.error_count }}</strong>
            </div>
          </div>
          <el-empty v-else description="暂无薄弱点记录" :image-size="72" />
        </article>

        <article class="panel-card">
          <div class="panel-heading">
            <div>
              <span class="section-eyebrow">ERROR PATTERNS</span>
              <h2>高频错误类型</h2>
            </div>
            <el-icon class="panel-icon"><DataAnalysis /></el-icon>
          </div>
          <div class="error-list">
            <div v-for="item in summary.error_types" :key="item.error_type" class="error-item">
              <div class="error-label">
                <strong>{{ item.label }}</strong>
                <span>{{ item.percentage.toFixed(1) }}%</span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: barWidth(item.count, maxErrorCount) }"
                />
              </div>
              <span class="error-count">{{ item.count }} 次</span>
            </div>
          </div>
        </article>
      </section>

      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <span class="section-eyebrow">TEACHING ACTIONS</span>
            <h2>推荐教师补讲内容</h2>
          </div>
          <span class="section-caption">由班级共性薄弱点自动生成 3 条建议</span>
        </div>
        <div class="suggestion-grid">
          <article
            v-for="(item, index) in summary.teaching_suggestions"
            :key="item.title"
            class="suggestion-card"
          >
            <span class="suggestion-number">0{{ index + 1 }}</span>
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.reason }}</p>
              <div class="suggestion-focus">
                <el-icon><Reading /></el-icon>
                <span>{{ item.focus }}</span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <span class="section-eyebrow">AFTER-CLASS PACKS</span>
            <h2>推荐课后巩固包</h2>
          </div>
          <span class="section-caption">模块、资源与 OJ 题目形成教学闭环</span>
        </div>
        <div class="pack-grid">
          <article
            v-for="pack in summary.reinforcement_packs"
            :key="pack.module_key"
            class="pack-card"
          >
            <div class="pack-header">
              <span class="pack-module">{{ pack.module_label }}</span>
              <el-tag size="small" effect="plain">{{ pack.module_key }}</el-tag>
            </div>
            <div class="pack-block">
              <span class="pack-label">推荐资源类型</span>
              <div class="tag-row">
                <el-tag
                  v-for="resourceType in pack.resource_types"
                  :key="resourceType"
                  type="success"
                  effect="plain"
                >
                  {{ resourceType }}
                </el-tag>
              </div>
            </div>
            <div class="pack-block">
              <span class="pack-label">推荐 OJ 题目</span>
              <div class="problem-list">
                <router-link
                  v-for="problem in pack.oj_problems"
                  :key="problem.slug"
                  :to="{ name: 'practice-problem', params: { slug: problem.slug } }"
                >
                  <el-icon><Cpu /></el-icon>
                  {{ problem.title }}
                </router-link>
              </div>
            </div>
          </article>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.teacher-dashboard {
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
    radial-gradient(circle at 82% 18%, rgba(56, 189, 248, 0.2), transparent 28%),
    linear-gradient(135deg, rgba(14, 116, 144, 0.22), rgba(79, 70, 229, 0.14)),
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
  border: 1px solid rgba(56, 189, 248, 0.16);
  border-radius: 50%;
  box-shadow: 0 0 0 34px rgba(56, 189, 248, 0.04), 0 0 0 70px rgba(129, 140, 248, 0.03);
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
.panel-card,
.suggestion-card,
.pack-card {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
}

.loading-card {
  padding: 24px;
}

.data-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 14px 0 0;
  color: var(--alp-color-muted);
  font-size: 12px;
}

.data-note .el-icon {
  color: var(--alp-color-primary);
}

.dashboard-section {
  margin-top: 28px;
}

.section-heading,
.panel-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.section-heading h2,
.panel-heading h2 {
  margin: 4px 0 0;
  font-size: 20px;
}

.section-caption {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
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
}

.metric-card--blue { --metric-color: #38bdf8; }
.metric-card--purple { --metric-color: #a78bfa; }
.metric-card--green { --metric-color: #4ade80; }
.metric-card--orange { --metric-color: #f59e0b; }
.metric-card--cyan { --metric-color: #22d3ee; }

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

.analysis-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 14px;
  margin-top: 28px;
}

.panel-card {
  min-width: 0;
  padding: 20px;
}

.panel-icon {
  color: var(--alp-color-primary);
  font-size: 24px;
}

.panel-icon--danger {
  color: #fb7185;
}

.ranking-list,
.error-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ranking-item {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) 32px;
  align-items: center;
  gap: 10px;
}

.ranking-index {
  color: var(--alp-color-muted);
  font-size: 12px;
  font-weight: 700;
}

.ranking-label,
.error-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 7px;
  font-size: 13px;
}

.ranking-label span,
.error-label span {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.bar-track {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-muted) 14%, transparent);
}

.bar-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #38bdf8, #818cf8);
  transition: width 0.5s ease;
}

.bar-fill--danger {
  background: linear-gradient(90deg, #fb7185, #f59e0b);
}

.ranking-value,
.error-count {
  color: var(--alp-color-text);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.error-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 54px;
  column-gap: 12px;
}

.error-item .error-label,
.error-item .bar-track {
  grid-column: 1;
}

.error-count {
  grid-column: 2;
  grid-row: 1 / span 2;
  align-self: center;
}

.suggestion-grid,
.pack-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.suggestion-card {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 14px;
  padding: 20px;
}

.suggestion-number {
  color: color-mix(in srgb, var(--alp-color-primary) 70%, var(--alp-color-muted));
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
}

.suggestion-card h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

.suggestion-card p {
  min-height: 44px;
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.7;
}

.suggestion-focus {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--alp-color-border);
  color: var(--alp-color-text);
  font-size: 12px;
  line-height: 1.6;
}

.suggestion-focus .el-icon {
  flex: 0 0 auto;
  margin-top: 3px;
  color: var(--alp-color-primary);
}

.pack-card {
  padding: 20px;
}

.pack-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.pack-module {
  font-size: 19px;
  font-weight: 700;
}

.pack-block + .pack-block {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--alp-color-border);
}

.pack-label {
  display: block;
  margin-bottom: 9px;
  color: var(--alp-color-muted);
  font-size: 11px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.problem-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.problem-list a {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--alp-color-primary);
  font-size: 13px;
  text-decoration: none;
}

.problem-list a:hover {
  text-decoration: underline;
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .suggestion-grid,
  .pack-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .dashboard-hero,
  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-actions {
    flex-wrap: wrap;
  }

  .metric-grid,
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
</style>
