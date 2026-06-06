<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  DataLine,
  TrendCharts,
  Warning,
  User,
  Document,
  Collection,
  Aim,
  Cpu,
  Trophy,
  Bell,
  StarFilled,
  Opportunity,
} from '@element-plus/icons-vue'
import {
  fetchClassOverview,
  fetchWeakPoints,
  fetchResourceStats,
  fetchInterventions,
  type ClassOverviewResponse,
  type WeakPointsResponse,
  type ResourceStatsResponse,
  type InterventionResponse,
} from '@/api/teacherDashboard'

const router = useRouter()
const loading = ref(true)

const overview = ref<ClassOverviewResponse | null>(null)
const weakPoints = ref<WeakPointsResponse | null>(null)
const resourceStats = ref<ResourceStatsResponse | null>(null)
const interventions = ref<InterventionResponse | null>(null)

const isDemo = computed(() =>
  overview.value?.is_demo ||
  weakPoints.value?.is_demo ||
  resourceStats.value?.is_demo ||
  interventions.value?.is_demo,
)

const errorEntries = computed(() => {
  if (!overview.value) return []
  return Object.entries(overview.value.error_type_distribution)
    .sort((a, b) => b[1] - a[1])
})

const maxErrorCount = computed(() => {
  if (!errorEntries.value.length) return 1
  return Math.max(...errorEntries.value.map(([, v]) => v), 1)
})

const resourceBarMax = computed(() => {
  if (!resourceStats.value) return 1
  return Math.max(...resourceStats.value.resource_stats.map(r => r.count), 1)
})

onMounted(async () => {
  loading.value = true
  try {
    const [o, w, r, i] = await Promise.allSettled([
      fetchClassOverview(),
      fetchWeakPoints(),
      fetchResourceStats(),
      fetchInterventions(),
    ])
    if (o.status === 'fulfilled') overview.value = o.value
    if (w.status === 'fulfilled') weakPoints.value = w.value
    if (r.status === 'fulfilled') resourceStats.value = r.value
    if (i.status === 'fulfilled') interventions.value = i.value
  } catch {
    /* ignore */
  } finally {
    loading.value = false
  }
})

function masteryLevel(score: number): string {
  if (score >= 8) return '优秀'
  if (score >= 6) return '良好'
  if (score >= 4) return '一般'
  return '薄弱'
}

function masteryColor(score: number): string {
  if (score >= 8) return '#4ade80'
  if (score >= 6) return '#38bdf8'
  if (score >= 4) return '#fbbf24'
  return '#f87171'
}

function errorBarWidth(count: number): string {
  return `${Math.round((count / maxErrorCount.value) * 100)}%`
}

function resourceBarWidth(count: number): string {
  return `${Math.round((count / resourceBarMax.value) * 100)}%`
}

function usageRateColor(rate: number): string {
  if (rate >= 0.8) return '#4ade80'
  if (rate >= 0.6) return '#38bdf8'
  if (rate >= 0.4) return '#fbbf24'
  return '#f87171'
}
</script>

<template>
  <el-card shadow="never" class="page-card">
    <el-page-header title="教师看板" @back="router.push({ name: 'home' })" />
    <el-divider />

    <header class="page-hero">
      <div class="hero-main">
        <h2 class="hero-title">
          <el-icon class="hero-icon"><TrendCharts /></el-icon>
          教师数据看板
        </h2>
        <p class="hero-desc">
          班级学情概览 · 共性薄弱点 · 资源生成统计 · 精准教学干预建议
        </p>
      </div>
      <el-tag v-if="isDemo" type="info" effect="plain" size="small" class="demo-tag">
        Demo 数据
      </el-tag>
    </header>

    <div v-if="loading" class="loading-block">
      <el-skeleton :rows="8" animated />
    </div>

    <template v-else>
      <section class="section-block">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><DataLine /></el-icon>
            班级概览
          </h3>
        </div>

        <div class="overview-grid">
          <div class="stat-card">
            <div class="stat-icon stat-icon--primary"><el-icon><User /></el-icon></div>
            <div class="stat-body">
              <span class="stat-value">{{ overview?.student_count ?? '-' }}</span>
              <span class="stat-label">学生数量</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon--blue"><el-icon><Aim /></el-icon></div>
            <div class="stat-body">
              <span class="stat-value" :style="{ color: masteryColor(overview?.avg_mastery ?? 0) }">
                {{ overview?.avg_mastery?.toFixed(1) ?? '-' }}
              </span>
              <span class="stat-label">平均掌握度 ({{ masteryLevel(overview?.avg_mastery ?? 0) }})</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon--green"><el-icon><TrendCharts /></el-icon></div>
            <div class="stat-body">
              <span class="stat-value">{{ overview ? Math.round(overview.active_rate_7d * 100) + '%' : '-' }}</span>
              <span class="stat-label">近 7 天活跃率</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon--orange"><el-icon><Cpu /></el-icon></div>
            <div class="stat-body">
              <span class="stat-value">{{ overview ? Math.round(overview.oj_accept_rate * 100) + '%' : '-' }}</span>
              <span class="stat-label">OJ AC 率</span>
            </div>
          </div>
        </div>

        <div v-if="errorEntries.length" class="error-dist-card">
          <div class="error-dist-head">
            <el-icon><Warning /></el-icon>
            <span>常见错误类型分布</span>
          </div>
          <div class="error-dist-body">
            <div v-for="[type, count] in errorEntries" :key="type" class="error-row">
              <span class="error-type-badge" :class="'error-type--' + type.toLowerCase()">{{ type }}</span>
              <div class="error-bar-track">
                <div class="error-bar-fill" :style="{ width: errorBarWidth(count) }" />
              </div>
              <span class="error-count">{{ count }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="section-block">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Warning /></el-icon>
            共性薄弱点
          </h3>
        </div>

        <div class="weak-grid">
          <div class="weak-card">
            <div class="weak-card-head">
              <el-icon class="weak-icon weak-icon--red"><Opportunity /></el-icon>
              <span>最薄弱模块</span>
            </div>
            <div class="weak-card-body">
              <div v-for="m in weakPoints?.weak_modules ?? []" :key="m.module_key" class="weak-item">
                <div class="weak-item-main">
                  <span class="weak-item-label">{{ m.module_label }}</span>
                  <el-tag size="small" type="danger" effect="plain">{{ m.error_count }} 次错误</el-tag>
                </div>
                <div class="weak-item-bar">
                  <div class="mastery-bar-track">
                    <div
                      class="mastery-bar-fill"
                      :style="{ width: Math.round(m.avg_mastery * 10) + '%', background: masteryColor(m.avg_mastery) }"
                    />
                  </div>
                  <span class="mastery-score" :style="{ color: masteryColor(m.avg_mastery) }">
                    {{ m.avg_mastery.toFixed(1) }}
                  </span>
                </div>
              </div>
              <el-empty v-if="!weakPoints?.weak_modules?.length" description="暂无数据" :image-size="48" />
            </div>
          </div>

          <div class="weak-card">
            <div class="weak-card-head">
              <el-icon class="weak-icon weak-icon--orange"><Document /></el-icon>
              <span>高频错误知识点</span>
            </div>
            <div class="weak-card-body">
              <div v-for="k in weakPoints?.weak_knowledge_points ?? []" :key="k.knowledge_point" class="weak-item">
                <div class="weak-item-main">
                  <span class="weak-item-label">{{ k.knowledge_point }}</span>
                  <el-tag size="small" type="warning" effect="plain">{{ k.error_count }} 次</el-tag>
                </div>
                <div v-if="k.typical_error" class="weak-item-hint">
                  典型错误：{{ k.typical_error }}
                </div>
              </div>
              <el-empty v-if="!weakPoints?.weak_knowledge_points?.length" description="暂无数据" :image-size="48" />
            </div>
          </div>

          <div class="weak-card">
            <div class="weak-card-head">
              <el-icon class="weak-icon weak-icon--yellow"><Cpu /></el-icon>
              <span>易错题目 (WA/TLE)</span>
            </div>
            <div class="weak-card-body">
              <div v-for="p in weakPoints?.weak_problem_types ?? []" :key="p.problem_slug" class="weak-item">
                <div class="weak-item-main">
                  <span class="weak-item-label">{{ p.problem_title }}</span>
                </div>
                <div class="weak-item-tags">
                  <el-tag size="small" type="danger" effect="plain">WA {{ p.wa_count }}</el-tag>
                  <el-tag size="small" type="warning" effect="plain">TLE {{ p.tle_count }}</el-tag>
                </div>
              </div>
              <el-empty v-if="!weakPoints?.weak_problem_types?.length" description="暂无数据" :image-size="48" />
            </div>
          </div>
        </div>

        <div v-if="weakPoints?.recommended_teaching_focus?.length" class="recommend-card">
          <div class="recommend-head">
            <el-icon><StarFilled /></el-icon>
            <span>推荐教师重点讲解</span>
          </div>
          <ul class="recommend-list">
            <li v-for="(r, i) in weakPoints.recommended_teaching_focus" :key="i">{{ r }}</li>
          </ul>
        </div>
      </section>

      <section class="section-block">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Collection /></el-icon>
            资源生成统计
          </h3>
        </div>

        <div class="resource-grid">
          <div v-for="r in resourceStats?.resource_stats ?? []" :key="r.resource_type" class="resource-row">
            <div class="resource-row-left">
              <span class="resource-label">{{ r.resource_label }}</span>
              <div class="resource-bar-track">
                <div class="resource-bar-fill" :style="{ width: resourceBarWidth(r.count) }" />
              </div>
              <span class="resource-count">{{ r.count }}</span>
            </div>
            <div class="resource-row-right">
              <span class="resource-usage" :style="{ color: usageRateColor(r.usage_rate) }">
                {{ Math.round(r.usage_rate * 100) }}% 使用率
              </span>
              <span class="resource-feedback">
                ★ {{ r.avg_feedback_score.toFixed(1) }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="resourceStats?.recommended_supplements?.length" class="recommend-card">
          <div class="recommend-head">
            <el-icon><StarFilled /></el-icon>
            <span>推荐补充资源</span>
          </div>
          <ul class="recommend-list">
            <li v-for="(s, i) in resourceStats.recommended_supplements" :key="i">{{ s }}</li>
          </ul>
        </div>
      </section>

      <section class="section-block">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Bell /></el-icon>
            干预建议
          </h3>
        </div>

        <div class="intervention-grid">
          <div class="intervention-card intervention-card--alert">
            <div class="intervention-head">
              <el-icon class="intervention-icon intervention-icon--red"><Warning /></el-icon>
              <span>连续受挫学生提醒</span>
            </div>
            <div class="intervention-body">
              <div v-for="s in interventions?.struggling_students ?? []" :key="s.username" class="intervention-item">
                <div class="intervention-item-top">
                  <el-avatar :size="28" class="intervention-avatar intervention-avatar--danger">
                    {{ s.username.slice(0, 1) }}
                  </el-avatar>
                  <div class="intervention-item-info">
                    <span class="intervention-item-name">{{ s.username }}</span>
                    <span class="intervention-item-meta">连续 {{ s.consecutive_failures }} 次未通过 · {{ s.last_problem }}</span>
                  </div>
                </div>
                <div class="intervention-item-action">{{ s.suggested_action }}</div>
              </div>
              <el-empty v-if="!interventions?.struggling_students?.length" description="暂无受挫学生" :image-size="48" />
            </div>
          </div>

          <div class="intervention-card intervention-card--topic">
            <div class="intervention-head">
              <el-icon class="intervention-icon intervention-icon--blue"><Document /></el-icon>
              <span>班级共性问题 · 建议生成专题资源</span>
            </div>
            <div class="intervention-body">
              <ul v-if="interventions?.class_common_issues?.length" class="intervention-list">
                <li v-for="(issue, i) in interventions.class_common_issues" :key="i">{{ issue }}</li>
              </ul>
              <el-empty v-else description="暂无共性问题" :image-size="48" />
              <div v-if="interventions?.suggested_topic_resources?.length" class="intervention-suggestions">
                <div class="intervention-suggestions-label">建议生成：</div>
                <el-tag
                  v-for="(r, i) in interventions.suggested_topic_resources"
                  :key="i"
                  type="primary"
                  effect="plain"
                  size="small"
                  class="intervention-tag"
                >
                  {{ r }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="intervention-card intervention-card--star">
            <div class="intervention-head">
              <el-icon class="intervention-icon intervention-icon--green"><Trophy /></el-icon>
              <span>高水平学生 · 推荐拓展项目</span>
            </div>
            <div class="intervention-body">
              <div v-for="h in interventions?.high_performers ?? []" :key="h.username" class="intervention-item">
                <div class="intervention-item-top">
                  <el-avatar :size="28" class="intervention-avatar intervention-avatar--success">
                    {{ h.username.slice(0, 1) }}
                  </el-avatar>
                  <div class="intervention-item-info">
                    <span class="intervention-item-name">{{ h.username }}</span>
                    <span class="intervention-item-meta">AC {{ h.ac_count }} 题 · 掌握度 {{ h.avg_mastery.toFixed(1) }}</span>
                  </div>
                </div>
                <div class="intervention-item-action intervention-item-action--success">{{ h.suggested_project }}</div>
              </div>
              <el-empty v-if="!interventions?.high_performers?.length" description="暂无高水平学生" :image-size="48" />
            </div>
          </div>
        </div>
      </section>
    </template>
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
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.hero-icon {
  color: var(--alp-color-primary);
  font-size: 22px;
}

.hero-desc {
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 13px;
  line-height: 1.5;
}

.demo-tag {
  flex-shrink: 0;
  margin-top: 4px;
}

.loading-block {
  padding: 20px 0;
}

.section-block {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.section-title .el-icon {
  color: var(--alp-color-primary);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--alp-shadow-card-hover);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 18px;
  flex-shrink: 0;
}

.stat-icon--primary {
  background: color-mix(in srgb, var(--alp-color-primary) 15%, transparent);
  color: var(--alp-color-primary);
}

.stat-icon--blue {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
}

.stat-icon--green {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.stat-icon--orange {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.stat-label {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.error-dist-card {
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.error-dist-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin-bottom: 10px;
}

.error-dist-head .el-icon {
  color: #fbbf24;
}

.error-dist-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.error-type-badge {
  width: 36px;
  height: 22px;
  border-radius: 4px;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.error-type--wa { background: #f87171; }
.error-type--tle { background: #fbbf24; color: #333; }
.error-type--re { background: #a78bfa; }
.error-type--ce { background: #94a3b8; }

.error-bar-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--alp-color-primary) 10%, var(--alp-bg-surface));
  overflow: hidden;
}

.error-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--alp-color-primary), var(--alp-color-accent));
  transition: width 0.6s ease;
}

.error-count {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  min-width: 32px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.weak-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.weak-card {
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.weak-card-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin-bottom: 10px;
}

.weak-icon {
  font-size: 16px;
}

.weak-icon--red { color: #f87171; }
.weak-icon--orange { color: #fbbf24; }
.weak-icon--yellow { color: #fb923c; }

.weak-card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.weak-item {
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.weak-item-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.weak-item-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.weak-item-tags {
  display: flex;
  gap: 6px;
}

.weak-item-hint {
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-top: 2px;
}

.weak-item-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mastery-bar-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--alp-color-primary) 8%, var(--alp-bg-surface));
  overflow: hidden;
}

.mastery-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}

.mastery-score {
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  min-width: 28px;
  text-align: right;
}

.recommend-card {
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: linear-gradient(135deg, color-mix(in srgb, var(--alp-color-primary) 6%, var(--alp-bg-soft-block)), var(--alp-bg-soft-block));
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 20%, var(--alp-color-border));
}

.recommend-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin-bottom: 8px;
}

.recommend-head .el-icon {
  color: var(--alp-color-primary);
}

.recommend-list {
  margin: 0;
  padding-left: 16px;
  font-size: 13px;
  color: var(--alp-color-text);
  line-height: 1.8;
}

.resource-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.resource-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.resource-row-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.resource-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  min-width: 72px;
}

.resource-bar-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--alp-color-primary) 8%, var(--alp-bg-surface));
  overflow: hidden;
}

.resource-bar-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--alp-color-primary), var(--alp-color-accent));
  transition: width 0.6s ease;
}

.resource-count {
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
  min-width: 32px;
  text-align: right;
}

.resource-row-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.resource-usage {
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.resource-feedback {
  font-size: 12px;
  color: var(--alp-color-muted);
  font-variant-numeric: tabular-nums;
}

.intervention-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.intervention-card {
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.intervention-card--alert {
  border-left: 3px solid #f87171;
}

.intervention-card--topic {
  border-left: 3px solid #38bdf8;
}

.intervention-card--star {
  border-left: 3px solid #4ade80;
}

.intervention-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin-bottom: 10px;
}

.intervention-icon {
  font-size: 16px;
}

.intervention-icon--red { color: #f87171; }
.intervention-icon--blue { color: #38bdf8; }
.intervention-icon--green { color: #4ade80; }

.intervention-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.intervention-item {
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.intervention-item-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.intervention-avatar {
  font-size: 12px;
}

.intervention-avatar--danger {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

.intervention-avatar--success {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.intervention-item-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.intervention-item-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.intervention-item-meta {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.intervention-item-action {
  font-size: 12px;
  color: #f87171;
  line-height: 1.4;
}

.intervention-item-action--success {
  color: #4ade80;
}

.intervention-list {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: var(--alp-color-text);
  line-height: 1.8;
}

.intervention-suggestions {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--alp-color-border);
}

.intervention-suggestions-label {
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-bottom: 6px;
}

.intervention-tag {
  margin: 0 4px 4px 0;
}

@media (max-width: 1000px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .weak-grid {
    grid-template-columns: 1fr;
  }

  .intervention-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .page-hero {
    flex-direction: column;
  }

  .resource-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .resource-row-left {
    width: 100%;
  }

  .resource-row-right {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
