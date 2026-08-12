<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Check, Clock, DataAnalysis, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { ProblemDetail } from '@/api/oj'
import {
  fetchSubmission,
  type OjSubmissionDetail,
  type OjSubmissionListItem,
} from '@/api/oj'
import type { OjPracticeRecord } from '@/utils/ojPracticeHistory'

const props = defineProps<{
  page: 'history' | 'favorite' | 'statistics'
  problem: ProblemDetail
  records: OjPracticeRecord[]
  favorite: boolean
  /** 数据库中的真实提交记录（登录且后端在线时由父组件提供） */
  dbSubmissions?: OjSubmissionListItem[]
}>()

const emit = defineEmits<{ toggleFavorite: []; back: [] }>()

const useDb = computed(() => Boolean(props.dbSubmissions && props.dbSubmissions.length))

/** 统一的历史记录条目：DB 优先，localStorage 兜底 */
type HistoryRow = {
  key: string
  id?: number
  verdict: string
  language?: string
  passed?: number
  total?: number
  runtimeMsAvg?: number
  at: number | string
  source: 'db' | 'local'
}

const historyRows = computed<HistoryRow[]>(() => {
  if (useDb.value) {
    return (props.dbSubmissions ?? []).map((s) => ({
      key: `db-${s.id}`,
      id: s.id,
      verdict: s.verdict,
      language: s.language,
      passed: s.passed,
      total: s.total,
      runtimeMsAvg: s.runtime_ms_avg,
      at: new Date(s.created_at).getTime(),
      source: 'db',
    }))
  }
  return props.records
    .filter((item) => item.slug === props.problem.slug)
    .reverse()
    .map((item, idx) => ({
      key: `local-${item.at}-${idx}`,
      verdict: item.verdict,
      at: item.at,
      source: 'local',
    }))
})

const accepted = computed(() => historyRows.value.filter((r) => r.verdict === 'AC').length)
const acceptanceRate = computed(() =>
  historyRows.value.length
    ? Math.round((accepted.value / historyRows.value.length) * 100)
    : 0,
)
const lastAttempt = computed(() => historyRows.value[0])

function verdictLabel(value: string) {
  return (
    ({
      AC: '通过',
      WA: '答案错误',
      TLE: '超时',
      RE: '运行错误',
      CE: '编译错误',
    }) as Record<string, string>
  )[value] ?? value
}

function verdictType(value: string) {
  return value === 'AC' ? 'success' : value === 'WA' ? 'warning' : 'danger'
}

function languageLabel(value?: string) {
  if (!value) return ''
  return value === 'cpp' ? 'C++' : 'Python'
}

function formatTime(value: number | string) {
  const ts = typeof value === 'string' ? new Date(value).getTime() : value
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(ts))
}

// ─── 详情抽屉 ───
const detailLoading = ref(false)
const detailOpen = ref(false)
const detail = ref<OjSubmissionDetail | null>(null)

async function openDetail(row: HistoryRow) {
  if (!row.id) return
  detailLoading.value = true
  detailOpen.value = true
  detail.value = null
  try {
    detail.value = await fetchSubmission(row.id)
  } catch {
    ElMessage.warning('加载提交详情失败')
    detailOpen.value = false
  } finally {
    detailLoading.value = false
  }
}

watch(
  () => props.page,
  () => {
    detailOpen.value = false
    detail.value = null
  },
)
</script>

<template>
  <section class="practice-subpage">
    <header class="subpage-head">
      <div>
        <span class="subpage-context">#{{ problem.lc_id || '—' }} {{ problem.title }}</span>
        <h2>{{ page === 'history' ? '提交记录' : page === 'favorite' ? '题目收藏' : '练习统计' }}</h2>
        <p v-if="page === 'history'" class="subpage-source">
          {{ useDb ? '来自数据库（已登录）' : '本地浏览器记录（登录后显示真实提交）' }}
        </p>
      </div>
      <el-button @click="emit('back')">返回练习</el-button>
    </header>

    <template v-if="page === 'history'">
      <div v-if="historyRows.length" class="history-list">
        <article
          v-for="(item, index) in historyRows"
          :key="item.key"
          class="history-row"
          :class="{ clickable: item.source === 'db' }"
          @click="item.source === 'db' ? openDetail(item) : null"
        >
          <span class="history-index">{{ historyRows.length - index }}</span>
          <el-tag :type="verdictType(item.verdict)" effect="plain">{{ verdictLabel(item.verdict) }}</el-tag>
          <div class="history-meta">
            <time :datetime="new Date(item.at).toISOString()">{{ formatTime(item.at) }}</time>
            <span v-if="item.language" class="meta-tag">{{ languageLabel(item.language) }}</span>
            <span v-if="item.total" class="meta-tag">{{ item.passed }}/{{ item.total }} 用例</span>
            <span v-if="item.runtimeMsAvg" class="meta-tag">{{ item.runtimeMsAvg }}ms</span>
          </div>
          <span class="history-source">
            {{ index === 0 ? '最近一次' : '历史提交' }}
            <span v-if="item.source === 'db'" class="hint">点击查看代码 ›</span>
          </span>
        </article>
      </div>
      <el-empty v-else description="还没有运行或提交记录">
        <el-button type="primary" @click="emit('back')">开始第一次练习</el-button>
      </el-empty>
    </template>

    <template v-else-if="page === 'favorite'">
      <div class="favorite-panel">
        <el-icon class="favorite-icon" :class="{ active: favorite }"><Star /></el-icon>
        <h3>{{ favorite ? '这道题已加入收藏' : '收藏这道题，稍后继续练习' }}</h3>
        <p>收藏状态会保存在当前浏览器中，你可以随时回来查看题目与最近练习结果。</p>
        <el-button :type="favorite ? 'default' : 'primary'" @click="emit('toggleFavorite')">
          {{ favorite ? '取消收藏' : '加入收藏' }}
        </el-button>
      </div>
    </template>

    <template v-else>
      <div class="stats-strip">
        <div><el-icon><Clock /></el-icon><span>尝试次数</span><strong>{{ historyRows.length }}</strong></div>
        <div><el-icon><Check /></el-icon><span>通过次数</span><strong>{{ accepted }}</strong></div>
        <div><el-icon><DataAnalysis /></el-icon><span>通过率</span><strong>{{ acceptanceRate }}%</strong></div>
      </div>
      <div class="stats-detail">
        <div><span>最近结果</span><el-tag v-if="lastAttempt" :type="verdictType(lastAttempt.verdict)">{{ verdictLabel(lastAttempt.verdict) }}</el-tag><strong v-else>暂无</strong></div>
        <div><span>最近练习</span><strong>{{ lastAttempt ? formatTime(lastAttempt.at) : '尚未开始' }}</strong></div>
        <div><span>当前状态</span><strong>{{ accepted ? '已通过，可继续优化' : historyRows.length ? '继续定位问题' : '等待首次提交' }}</strong></div>
      </div>
    </template>

    <el-drawer
      v-model="detailOpen"
      title="提交详情"
      direction="rtl"
      size="60%"
      :destroy-on-close="true"
    >
      <div v-loading="detailLoading" class="detail-body">
        <template v-if="detail">
          <div class="detail-head">
            <el-tag :type="verdictType(detail.verdict)" effect="plain">{{ verdictLabel(detail.verdict) }}</el-tag>
            <span class="meta-tag">{{ languageLabel(detail.language) }}</span>
            <span class="meta-tag">{{ detail.passed }}/{{ detail.total }} 用例</span>
            <span v-if="detail.runtime_ms_avg" class="meta-tag">均 {{ detail.runtime_ms_avg }}ms</span>
            <time class="meta-tag">{{ formatTime(detail.created_at) }}</time>
          </div>
          <pre v-if="detail.compile_error" class="compile-error"><code>{{ detail.compile_error }}</code></pre>
          <section class="detail-section">
            <h4>提交代码</h4>
            <pre class="code-block"><code>{{ detail.code }}</code></pre>
          </section>
          <section v-if="detail.cases.length" class="detail-section">
            <h4>用例结果</h4>
            <ul class="case-list">
              <li v-for="c in detail.cases" :key="c.index">
                <el-tag size="small" :type="verdictType(c.verdict)">#{{ c.index }} {{ verdictLabel(c.verdict) }}</el-tag>
                <span v-if="c.runtime_ms != null" class="meta-tag">{{ c.runtime_ms }}ms</span>
                <div v-if="c.message" class="case-message">{{ c.message }}</div>
              </li>
            </ul>
          </section>
        </template>
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.practice-subpage { height: 100%; overflow: auto; padding: 28px clamp(20px, 4vw, 56px); box-sizing: border-box; background: var(--alp-bg-surface); color: var(--alp-color-text); }
.subpage-head { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid var(--alp-color-border); }
.subpage-context { color: var(--alp-color-muted); font-size: 13px; }
.subpage-head h2 { margin: 5px 0 0; font-size: 22px; }
.subpage-source { margin: 6px 0 0; color: var(--alp-color-muted); font-size: 12px; }
.history-list { margin-top: 18px; border: 1px solid var(--alp-color-border); border-radius: var(--alp-radius-card); overflow: hidden; }
.history-row { display: grid; grid-template-columns: 42px 110px minmax(150px, 1fr) 120px; align-items: center; gap: 12px; min-height: 54px; padding: 0 16px; }
.history-row + .history-row { border-top: 1px solid var(--alp-color-border); }
.history-row.clickable { cursor: pointer; }
.history-row.clickable:hover { background: var(--alp-bg-hover); }
.history-index, .history-source, .history-row time { color: var(--alp-color-muted); font-size: 12px; }
.history-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; min-width: 0; }
.history-meta time { font-size: 12px; }
.meta-tag { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 4px; background: var(--alp-bg-hover); color: var(--alp-color-muted); font-size: 11px; }
.hint { display: inline-block; margin-left: 6px; color: var(--alp-color-primary); }
.favorite-panel { max-width: 560px; margin: 56px auto; text-align: center; }
.favorite-icon { font-size: 44px; color: var(--alp-color-muted); }
.favorite-icon.active { color: var(--el-color-warning); }
.favorite-panel h3 { margin: 16px 0 8px; }
.favorite-panel p { margin: 0 auto 20px; color: var(--alp-color-muted); line-height: 1.7; }
.stats-strip { display: flex; margin-top: 22px; border: 1px solid var(--alp-color-border); border-radius: var(--alp-radius-card); overflow: hidden; }
.stats-strip > div { flex: 1; display: grid; grid-template-columns: 24px 1fr; gap: 5px 10px; padding: 20px; }
.stats-strip > div + div { border-left: 1px solid var(--alp-color-border); }
.stats-strip .el-icon { grid-row: 1 / 3; align-self: center; color: var(--alp-color-primary); font-size: 20px; }
.stats-strip span, .stats-detail span { color: var(--alp-color-muted); font-size: 12px; }
.stats-strip strong { font-size: 24px; }
.stats-detail { margin-top: 18px; }
.stats-detail > div { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 48px; border-bottom: 1px solid var(--alp-color-border); }
.stats-detail strong { font-size: 13px; }

.detail-body { padding: 0 20px 24px; }
.detail-head { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 12px; }
.compile-error { background: var(--el-color-danger-light-9); border: 1px solid var(--el-color-danger-light-5); border-radius: 6px; padding: 12px; font-size: 12px; color: var(--el-color-danger); overflow: auto; max-height: 160px; }
.detail-section { margin-top: 16px; }
.detail-section h4 { margin: 0 0 8px; font-size: 13px; color: var(--alp-color-muted); }
.code-block { background: var(--alp-bg-surface-muted); border: 1px solid var(--alp-color-border); border-radius: 6px; padding: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; line-height: 1.55; overflow: auto; max-height: 360px; white-space: pre; }
.case-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.case-list li { padding: 8px 10px; border: 1px solid var(--alp-color-border); border-radius: 6px; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.case-message { width: 100%; color: var(--alp-color-muted); font-size: 12px; word-break: break-all; }

@media (max-width: 700px) {
  .subpage-head { align-items: flex-start; }
  .history-row { grid-template-columns: 32px 90px 1fr; }
  .history-source { display: none; }
  .stats-strip { flex-direction: column; }
  .stats-strip > div + div { border-left: 0; border-top: 1px solid var(--alp-color-border); }
}
</style>
