<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, RefreshRight, User, TrendCharts, Cpu, Collection, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchStudentRoster,
  fetchStudentDetail,
  type StudentRosterItem,
  type StudentDetailResponse,
} from '@/api/teacherDashboard'
import StudentDetailDrawer from './StudentDetailDrawer.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const loadError = ref('')
const roster = ref<StudentRosterItem[]>([])
const generatedAt = ref('')
const searchQuery = ref('')
const filterWeak = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)

// 详情抽屉
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref<StudentDetailResponse | null>(null)

const filteredStudents = computed(() => {
  let list = roster.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter((s) => s.username.toLowerCase().includes(q))
  }
  if (filterWeak.value) {
    list = list.filter((s) => s.weak_modules.length > 0)
  }
  return list
})

const pagedStudents = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredStudents.value.slice(start, start + pageSize.value)
})

watch([searchQuery, filterWeak], () => {
  currentPage.value = 1
})

const summary = computed(() => {
  const total = roster.value.length
  if (total === 0) return { total: 0, avgMastery: 0, avgProgress: 0, totalOj: 0, totalResources: 0 }
  const avgMastery = roster.value.reduce((sum, s) => sum + s.mastery_score, 0) / total
  const avgProgress = roster.value.reduce((sum, s) => sum + s.progress_percent, 0) / total
  const totalOj = roster.value.reduce((sum, s) => sum + s.oj_submissions, 0)
  const totalResources = roster.value.reduce((sum, s) => sum + s.resource_count, 0)
  return {
    total,
    avgMastery: Math.round(avgMastery * 10) / 10,
    avgProgress: Math.round(avgProgress * 10) / 10,
    totalOj,
    totalResources,
  }
})

const MODULE_LABELS: Record<string, string> = {
  array: '数组',
  'linked-list': '链表',
  'stack-queue': '栈与队列',
  string: '字符串',
  'two-pointers': '双指针',
  'hash-table': '哈希表',
  'binary-tree': '二叉树',
  graph: '图',
  sorting: '排序',
  greedy: '贪心',
  dp: '动态规划',
  backtracking: '回溯',
  'monotonic-stack': '单调栈',
}

function masteryColor(score: number): string {
  if (score >= 80) return '#6aa878'
  if (score >= 50) return '#9c7a3d'
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

async function loadRoster() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await fetchStudentRoster()
    roster.value = res.students
    generatedAt.value = res.generated_at
    const studentId = route.query.student
    if (studentId) {
      const target = roster.value.find((s) => String(s.user_id) === String(studentId))
      if (target) {
        openDetail(target)
      }
      router.replace({ query: {} })
    }
  } catch {
    loadError.value = '学情数据暂时无法加载，请确认后端服务已启动后重试。'
  } finally {
    loading.value = false
  }
}

async function openDetail(student: StudentRosterItem) {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  try {
    detailData.value = await fetchStudentDetail(student.user_id)
  } catch {
    ElMessage.error('学生详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(loadRoster)
</script>

<template>
  <main class="teacher-roster">
    <section class="dashboard-hero">
      <div class="hero-copy">
        <div class="hero-kicker">
          <el-icon><User /></el-icon>
          AlgoPilot 学情管理
        </div>
        <h1>学生学情管理</h1>
        <p>
          逐人追踪学习画像、掌握度、OJ 提交与资源使用情况，
          快速定位需要重点关注的学生，支持按薄弱模块筛选。
        </p>
        <div class="hero-meta">
          <span>数据更新时间：{{ formatDate(generatedAt) }}</span>
          <span>课程：数据结构与算法</span>
        </div>
      </div>
      <div class="hero-actions">
        <el-button :loading="loading" :icon="RefreshRight" @click="loadRoster">
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

    <div v-if="loading && !roster.length" class="loading-card">
      <el-skeleton :rows="8" animated />
    </div>

    <template v-else>
      <section class="dashboard-section">
        <div class="metric-grid">
          <article class="metric-card metric-card--blue">
            <div class="metric-icon"><el-icon><User /></el-icon></div>
            <div>
              <strong>{{ summary.total }}</strong>
              <span>学生总数</span>
            </div>
          </article>
          <article class="metric-card metric-card--green">
            <div class="metric-icon"><el-icon><TrendCharts /></el-icon></div>
            <div>
              <strong>{{ summary.avgMastery }}%</strong>
              <span>平均掌握度</span>
            </div>
          </article>
          <article class="metric-card metric-card--purple">
            <div class="metric-icon"><el-icon><TrendCharts /></el-icon></div>
            <div>
              <strong>{{ summary.avgProgress }}%</strong>
              <span>平均学习进度</span>
            </div>
          </article>
          <article class="metric-card metric-card--cyan">
            <div class="metric-icon"><el-icon><Cpu /></el-icon></div>
            <div>
              <strong>{{ summary.totalOj }}</strong>
              <span>OJ 提交总数</span>
            </div>
          </article>
          <article class="metric-card metric-card--orange">
            <div class="metric-icon"><el-icon><Collection /></el-icon></div>
            <div>
              <strong>{{ summary.totalResources }}</strong>
              <span>资源生成总数</span>
            </div>
          </article>
        </div>
      </section>

      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <span class="section-eyebrow">STUDENT ROSTER</span>
            <h2>学生花名册</h2>
          </div>
          <div class="filter-bar">
            <el-switch
              v-model="filterWeak"
              active-text="仅看薄弱学生"
              inline-prompt
            />
            <el-input
              v-model="searchQuery"
              placeholder="搜索学生用户名"
              :prefix-icon="Search"
              clearable
              style="width: 200px"
            />
          </div>
        </div>

        <div class="table-card">
          <el-table
            :data="pagedStudents"
            stripe
            style="width: 100%"
            @row-click="openDetail"
            row-class-name="roster-row"
            empty-text="暂无学生数据"
          >
            <el-table-column prop="username" label="学生" min-width="120">
              <template #default="{ row }">
                <div class="student-cell">
                  <el-avatar :size="30" class="student-avatar">
                    {{ row.username.slice(0, 1).toUpperCase() }}
                  </el-avatar>
                  <span>{{ row.username }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="掌握度" min-width="130" align="center">
              <template #default="{ row }">
                <div class="mastery-cell">
                  <div class="bar-track">
                    <div
                      class="bar-fill"
                      :style="{ width: `${row.mastery_score}%`, background: masteryColor(row.mastery_score) }"
                    />
                  </div>
                  <span :style="{ color: masteryColor(row.mastery_score) }">{{ row.mastery_score.toFixed(1) }}%</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="学习进度" min-width="130" align="center">
              <template #default="{ row }">
                <div class="mastery-cell">
                  <div class="bar-track">
                    <div class="bar-fill bar-fill--primary" :style="{ width: `${row.progress_percent}%` }" />
                  </div>
                  <span>{{ row.progress_percent.toFixed(1) }}%</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="OJ 提交" min-width="100" align="center">
              <template #default="{ row }">
                <span class="oj-stat">{{ row.oj_submissions }} 次</span>
                <span v-if="row.oj_accepted" class="oj-ac">AC {{ row.oj_accepted }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="resource_count" label="资源数" min-width="80" align="center" />
            <el-table-column label="薄弱模块" min-width="180">
              <template #default="{ row }">
                <div class="tag-row">
                  <el-tag
                    v-for="mod in row.weak_modules"
                    :key="mod"
                    size="small"
                    type="danger"
                    effect="plain"
                  >
                    {{ MODULE_LABELS[mod] || mod }}
                  </el-tag>
                  <span v-if="!row.weak_modules.length" class="text-muted">--</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="最近活跃" min-width="110" align="center">
              <template #default="{ row }">
                <span class="text-muted">{{ formatDate(row.last_active) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center" fixed="right">
              <template #default="{ row }">
                <el-button size="small" text :icon="View" @click.stop="openDetail(row as StudentRosterItem)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="filteredStudents.length"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              background
              small
            />
          </div>
        </div>
      </section>
    </template>

    <!-- 学生详情抽屉 -->
    <StudentDetailDrawer
      v-model="detailVisible"
      :detail="detailData"
      :loading="detailLoading"
    />
  </main>
</template>

<style scoped>
.teacher-roster {
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

.loading-card {
  padding: 24px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
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

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
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
  box-shadow: var(--alp-shadow-card-hover);
}

.metric-card--blue { --metric-color: #3a8a9e; }
.metric-card--purple { --metric-color: #7a6e9e; }
.metric-card--green { --metric-color: #6aa878; }
.metric-card--orange { --metric-color: #9c7a3d; }
.metric-card--cyan { --metric-color: #3a8a9e; }

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

.table-card {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  overflow: hidden;
}

.table-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px;
  border-top: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
}

.student-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.student-avatar {
  flex: 0 0 30px;
  background: var(--alp-bg-code-ish);
  border: 1px solid rgba(var(--alp-color-primary-rgb), 0.36);
  color: var(--alp-color-text);
  font-size: 12px;
}

.mastery-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-track {
  flex: 1;
  min-width: 40px;
  height: 8px;
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

.bar-fill--primary {
  background: var(--alp-color-primary);
}

.bar-fill--danger {
  background: #9e6470;
}

.oj-stat {
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.oj-ac {
  display: block;
  font-size: 11px;
  color: #6aa878;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.text-muted {
  color: var(--alp-color-muted);
  font-size: 12px;
}

:deep(.roster-row) {
  cursor: pointer;
  transition: background var(--alp-transition-fast);
}

:deep(.roster-row:hover) {
  background: var(--alp-bg-nav-hover);
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
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
}
</style>
