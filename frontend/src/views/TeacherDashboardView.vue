<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowDown,
  ArrowUp,
  DataAnalysis,
  RefreshRight,
  Search,
  TrendCharts,
  Warning,
} from '@element-plus/icons-vue'
import {
  fetchStudentRoster,
  fetchTeacherDashboardSummary,
  type StudentRosterItem,
  type TeacherDashboardSummary,
} from '@/api/teacherDashboard'

const router = useRouter()
const loading = ref(false)
const loadError = ref('')
const summary = ref<TeacherDashboardSummary | null>(null)
const students = ref<StudentRosterItem[]>([])
const search = ref('')
const riskFilter = ref('all')
const page = ref(1)
const pageSize = 8

const emptySummary = (): TeacherDashboardSummary => ({
  overview: { student_count: 0, profile_count: 0, average_mastery: 0, resource_count: 0, oj_submission_count: 0 },
  weak_knowledge_points: [], error_types: [], teaching_suggestions: [], reinforcement_packs: [],
  data_note: '当前暂未取得教学数据，服务恢复后点击刷新即可重新加载。', generated_at: '',
})

const overview = computed(() => summary.value?.overview ?? emptySummary().overview)
const engagement = computed(() => overview.value.student_count
  ? Math.round((overview.value.profile_count / overview.value.student_count) * 100) : 0)

function studentRisk(student: StudentRosterItem) {
  if (student.mastery_score < 50 || student.progress_percent < 40) return 'high'
  if (student.mastery_score < 65 || student.progress_percent < 60) return 'medium'
  if (student.weak_modules.length) return 'low'
  return 'normal'
}

const riskLabel: Record<string, string> = { high: '高风险', medium: '中风险', low: '低风险', normal: '正常' }
const filteredStudents = computed(() => students.value.filter((student) => {
  const matchesSearch = student.username.toLowerCase().includes(search.value.trim().toLowerCase())
  return matchesSearch && (riskFilter.value === 'all' || studentRisk(student) === riskFilter.value)
}))
const pagedStudents = computed(() => filteredStudents.value.slice((page.value - 1) * pageSize, page.value * pageSize))

const distribution = computed(() => {
  const ranges = [
    { label: '0–59', min: 0, max: 59 }, { label: '60–69', min: 60, max: 69 },
    { label: '70–79', min: 70, max: 79 }, { label: '80–89', min: 80, max: 89 },
    { label: '90–100', min: 90, max: 100 },
  ]
  return ranges.map((range) => ({ ...range, count: students.value.filter((s) => s.mastery_score >= range.min && s.mastery_score <= range.max).length }))
})
const maxDistribution = computed(() => Math.max(1, ...distribution.value.map((item) => item.count)))

const alerts = computed(() => students.value
  .filter((student) => studentRisk(student) !== 'normal')
  .sort((a, b) => a.mastery_score - b.mastery_score)
  .slice(0, 5))

function formatDate(value?: string) {
  if (!value) return '--'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '--' : new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit' }).format(date)
}

async function loadDashboard() {
  loading.value = true
  loadError.value = ''
  const [summaryResult, rosterResult] = await Promise.allSettled([
    fetchTeacherDashboardSummary(), fetchStudentRoster(),
  ])
  summary.value = summaryResult.status === 'fulfilled' ? summaryResult.value : emptySummary()
  students.value = rosterResult.status === 'fulfilled' ? rosterResult.value.students : []
  if (summaryResult.status === 'rejected' || rosterResult.status === 'rejected') {
    loadError.value = '部分教学数据暂时不可用，当前已展示可获取的数据。'
  }
  loading.value = false
}

function goStudent(student: StudentRosterItem) {
  router.push({ name: 'student-roster', query: { student: String(student.user_id) } })
}

onMounted(loadDashboard)
</script>

<template>
  <main class="teacher-dashboard" v-loading="loading">
    <el-alert v-if="loadError" class="load-alert" type="warning" :title="loadError" show-icon :closable="false" />

    <section class="overview-panel">
      <div class="section-title-row">
        <div><h1>系统实例学情概览</h1><p>{{ summary?.data_note || '当前系统实例内学生学习记录的只读聚合视图' }}</p></div>
        <el-button :icon="RefreshRight" :loading="loading" @click="loadDashboard">刷新数据</el-button>
      </div>
      <div class="metric-grid">
        <article><span>平均掌握度</span><strong>{{ overview.average_mastery.toFixed(1) }}</strong><small class="up"><el-icon><ArrowUp /></el-icon> 实时汇总</small></article>
        <article><span>活跃学习率</span><strong>{{ engagement }}<i>%</i></strong><small class="up"><el-icon><ArrowUp /></el-icon> {{ overview.profile_count }} 人有画像</small></article>
        <article><span>OJ 学习记录数</span><strong>{{ overview.oj_submission_count }}</strong><small>成功与失败事件合计</small></article>
        <article><span>平均学习进度</span><strong>{{ students.length ? Math.round(students.reduce((sum, s) => sum + s.progress_percent, 0) / students.length) : 0 }}<i>%</i></strong><small class="up"><el-icon><ArrowUp /></el-icon> 持续更新</small></article>
        <article><span>资源生成数</span><strong>{{ overview.resource_count }}</strong><small>本课程累计</small></article>
        <article><span>预警学生数</span><strong>{{ alerts.length }}</strong><small class="down"><el-icon><ArrowDown /></el-icon> 需重点关注</small></article>
      </div>
    </section>

    <section class="dashboard-body">
      <div class="main-column">
        <div class="analysis-grid">
          <article class="data-panel distribution-panel">
            <header><h2>学业分布</h2><span>按掌握度分段</span></header>
            <div class="bar-chart" role="img" aria-label="学生掌握度分布柱状图">
              <div v-for="item in distribution" :key="item.label" class="bar-column">
                <span>{{ item.count }}</span>
                <div class="bar" :style="{ height: `${Math.max(5, item.count / maxDistribution * 100)}%` }" />
                <small>{{ item.label }}</small>
              </div>
            </div>
          </article>

          <article class="data-panel weak-panel">
            <header><h2>薄弱知识点 Top 5</h2><span>影响范围</span></header>
            <div class="weak-table">
              <div class="weak-head"><span>知识点</span><span>错误次数</span><span>影响学生</span></div>
              <div v-for="item in summary?.weak_knowledge_points.slice(0, 5)" :key="item.module_key" class="weak-row">
                <strong>{{ item.module_label }}</strong><span>{{ item.error_count }}</span><span>{{ item.affected_students }} 人</span>
              </div>
              <el-empty v-if="!summary?.weak_knowledge_points.length" description="暂无薄弱点记录" :image-size="56" />
            </div>
          </article>

        </div>

        <article class="data-panel student-panel">
          <header class="student-header">
            <h2>学生学情列表</h2>
            <div class="table-tools">
              <el-select v-model="riskFilter" aria-label="风险筛选" @change="page = 1">
                <el-option label="全部状态" value="all" /><el-option label="高风险" value="high" /><el-option label="中风险" value="medium" /><el-option label="低风险" value="low" /><el-option label="正常" value="normal" />
              </el-select>
              <el-input v-model="search" :prefix-icon="Search" clearable placeholder="搜索学生姓名" @input="page = 1" />
            </div>
          </header>
          <el-table :data="pagedStudents" row-key="user_id" class="student-table" @row-click="goStudent">
            <el-table-column prop="username" label="学生姓名" min-width="120" />
            <el-table-column label="掌握度" min-width="100"><template #default="{ row }">{{ row.mastery_score.toFixed(1) }}</template></el-table-column>
            <el-table-column label="学习进度" min-width="150"><template #default="{ row }"><el-progress :percentage="Math.round(row.progress_percent)" :stroke-width="6" :show-text="false" /> <span class="progress-value">{{ Math.round(row.progress_percent) }}%</span></template></el-table-column>
            <el-table-column prop="oj_submissions" label="OJ 提交" min-width="90" />
            <el-table-column label="薄弱知识点" min-width="180"><template #default="{ row }">{{ row.weak_modules.slice(0, 2).join('、') || '—' }}</template></el-table-column>
            <el-table-column label="预警状态" min-width="100"><template #default="{ row }"><span class="risk-tag" :class="`risk-${studentRisk(row)}`">{{ riskLabel[studentRisk(row)] }}</span></template></el-table-column>
            <el-table-column label="操作" width="76"><template #default="{ row }"><el-button link type="primary" @click.stop="goStudent(row)"><el-icon><TrendCharts /></el-icon>详情</el-button></template></el-table-column>
          </el-table>
          <footer class="table-footer"><span>共 {{ filteredStudents.length }} 名学生</span><el-pagination v-model:current-page="page" :page-size="pageSize" :total="filteredStudents.length" layout="prev, pager, next" /></footer>
        </article>
      </div>

      <aside class="side-column">
        <article class="data-panel alert-panel">
          <header><h2>学习预警</h2><router-link to="/student-roster">查看全部</router-link></header>
          <button v-for="student in alerts" :key="student.user_id" class="alert-row" @click="goStudent(student)">
            <i :class="`risk-${studentRisk(student)}`" /><strong>{{ student.username }}</strong><span>{{ student.weak_modules[0] || '学习投入度偏低' }}</span><time>{{ formatDate(student.last_active) }}</time>
          </button>
          <el-empty v-if="!alerts.length" description="暂无学习预警" :image-size="56" />
        </article>

        <article class="data-panel advice-panel">
          <header><h2>个性化建议</h2><span>基于当前学情</span></header>
          <div v-for="(item, index) in summary?.teaching_suggestions.slice(0, 3)" :key="item.title" class="advice-item">
            <div class="advice-icon"><el-icon><DataAnalysis v-if="index === 0" /><Warning v-else /></el-icon></div>
            <div><h3>{{ item.title }}</h3><p>{{ item.reason }}</p><router-link to="/teacher-workbench">生成教学资源</router-link></div>
          </div>
          <el-empty v-if="!summary?.teaching_suggestions.length" description="暂无教学建议" :image-size="56" />
        </article>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.teacher-dashboard{width:100%;max-width:1600px;margin:0 auto;color:var(--alp-color-text);font-family:Inter,"PingFang SC","Microsoft YaHei",sans-serif}.load-alert{margin-bottom:12px}.overview-panel,.data-panel{background:var(--alp-bg-surface);border:1px solid var(--alp-color-border);border-radius:8px}.overview-panel{padding:16px}.section-title-row,.data-panel>header,.student-header{display:flex;align-items:center;justify-content:space-between;gap:16px}.section-title-row{margin-bottom:14px}.section-title-row h1,.data-panel h2{margin:0;font-size:16px;line-height:1.4}.section-title-row p,.data-panel header span{margin:3px 0 0;color:var(--alp-color-muted);font-size:12px}.metric-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));border:1px solid var(--alp-color-border);border-radius:6px;overflow:hidden}.metric-grid article{display:flex;flex-direction:column;min-height:100px;padding:15px 17px;border-right:1px solid var(--alp-color-border)}.metric-grid article:last-child{border-right:0}.metric-grid span{font-size:12px;color:var(--alp-color-text-secondary)}.metric-grid strong{margin:8px 0 6px;font-size:28px;line-height:1;color:var(--alp-color-text)}.metric-grid strong i{font-size:14px;font-style:normal;font-weight:500}.metric-grid small{display:flex;align-items:center;gap:3px;color:var(--alp-color-muted);font-size:11px}.metric-grid .up{color:#16a064}.metric-grid .down{color:#d84a4a}.dashboard-body{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:12px;margin-top:12px}.main-column,.side-column{display:flex;flex-direction:column;gap:12px;min-width:0}.analysis-grid{display:grid;grid-template-columns:1fr 1.08fr;gap:12px}.data-panel{min-width:0;overflow:hidden}.data-panel>header{height:48px;padding:0 14px;border-bottom:1px solid var(--alp-color-border)}.data-panel header a,.advice-item a{color:var(--alp-color-primary);font-size:12px;text-decoration:none}.bar-chart{display:flex;align-items:flex-end;justify-content:space-around;height:180px;padding:25px 16px 28px;border-bottom:1px solid var(--alp-color-border)}.bar-column{position:relative;display:flex;align-items:center;flex-direction:column;justify-content:flex-end;width:15%;height:100%}.bar-column>span{margin-bottom:5px;color:var(--alp-color-primary);font-size:11px}.bar-column .bar{width:100%;max-width:34px;min-height:4px;background:var(--alp-color-primary);border-radius:3px 3px 0 0}.bar-column small{position:absolute;bottom:-20px;color:var(--alp-color-muted);font-size:10px}.weak-table{padding:0 14px 8px}.weak-head,.weak-row{display:grid;grid-template-columns:minmax(0,1fr) 70px 70px;align-items:center;gap:8px;min-height:38px;border-bottom:1px solid var(--alp-color-border);font-size:11px}.weak-head{color:var(--alp-color-muted)}.weak-row strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}.weak-row span{color:var(--alp-color-text-secondary)}.student-header{height:auto!important;padding:11px 14px!important}.table-tools{display:flex;gap:8px}.table-tools :deep(.el-select){width:120px}.table-tools :deep(.el-input){width:190px}.student-table{width:100%;cursor:pointer}.progress-value{margin-left:8px;font-size:11px}.risk-tag{display:inline-flex;padding:3px 7px;border-radius:999px;font-size:11px}.risk-high{color:#dc2626;background:#fef2f2}.risk-medium{color:#d97706;background:#fffbeb}.risk-low{color:#b7791f;background:#fff8dd}.risk-normal{color:#128052;background:#eefbf4}.table-footer{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;color:var(--alp-color-muted);font-size:12px;border-top:1px solid var(--alp-color-border)}.alert-row{display:grid;grid-template-columns:8px 58px minmax(0,1fr) 42px;align-items:center;gap:8px;width:100%;min-height:46px;padding:0 14px;border:0;border-bottom:1px solid var(--alp-color-border);background:transparent;color:inherit;text-align:left;cursor:pointer}.alert-row:hover{background:var(--alp-bg-nav-hover)}.alert-row i{width:7px;height:7px;border-radius:50%}.alert-row i.risk-high{background:#ef4444}.alert-row i.risk-medium{background:#f59e0b}.alert-row i.risk-low{background:#eab308}.alert-row strong{font-size:12px}.alert-row span{overflow:hidden;color:var(--alp-color-text-secondary);font-size:11px;text-overflow:ellipsis;white-space:nowrap}.alert-row time{color:var(--alp-color-muted);font-size:10px}.advice-panel{flex:1}.advice-item{display:grid;grid-template-columns:32px minmax(0,1fr);gap:10px;padding:15px 14px;border-bottom:1px solid var(--alp-color-border)}.advice-icon{display:grid;place-items:center;width:30px;height:30px;border-radius:6px;color:var(--alp-color-primary);background:var(--alp-bg-nav-active)}.advice-item h3{margin:0 0 5px;font-size:13px}.advice-item p{margin:0 0 8px;color:var(--alp-color-text-secondary);font-size:11px;line-height:1.6}@media(max-width:1250px){.metric-grid{grid-template-columns:repeat(3,1fr)}.metric-grid article:nth-child(3){border-right:0}.metric-grid article:nth-child(-n+3){border-bottom:1px solid var(--alp-color-border)}.dashboard-body{grid-template-columns:1fr}.side-column{display:grid;grid-template-columns:1fr 1fr}.analysis-grid{grid-template-columns:1fr 1fr}}@media(max-width:760px){.metric-grid,.analysis-grid,.side-column{grid-template-columns:1fr}.metric-grid article{border-right:0!important;border-bottom:1px solid var(--alp-color-border)}.dashboard-body{display:block}.side-column{display:grid;margin-top:12px}.section-title-row,.student-header{align-items:flex-start;flex-direction:column}.table-tools{width:100%}.table-tools :deep(.el-select),.table-tools :deep(.el-input){width:50%}}
</style>
