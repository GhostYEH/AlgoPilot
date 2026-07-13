<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Clock, Collection, Histogram, Star } from '@element-plus/icons-vue'
import OjPracticeRow from '@/components/oj/OjPracticeRow.vue'
import OjPracticeSubpage from '@/components/oj/OjPracticeSubpage.vue'
import { useOjWorkbenchActions } from '@/composables/useOjWorkbenchActions'
import { resolveProblem, type JudgeResponse, type ProblemDetail, type OjLanguage } from '@/api/oj'
import type { AiDiagnoseResponse, TraceDiagnosisReport, TraceResponse } from '@/types/codeTrace'
import { buildFallbackProblem } from '@/api/ojLocal'
import { getOjJudgeDemoScenario } from '@/constants/ojDemo'
import { resetOjStruggleSession } from '@/utils/ojStruggleSession'
import { getOjPracticeRecords, type OjPracticeRecord } from '@/utils/ojPracticeHistory'
import { isOjFavorite, toggleOjFavorite } from '@/utils/ojFavorites'

const route = useRoute()
const router = useRouter()
const slug = computed(() => route.params.slug as string)

const loading = ref(true)
const problem = ref<ProblemDetail | null>(null)
const code = ref('')
const result = ref<JudgeResponse | null>(null)
const trace = ref<TraceResponse | null>(null)
const diagnosis = ref<AiDiagnoseResponse | null>(null)
const traceBugDiagnosis = ref<import('@/types/codeTrace').TraceBugDiagnoseResponse | null>(null)
const traceReport = ref<TraceDiagnosisReport | null>(null)
const traceReportLoading = ref(false)
const apiOnline = ref(false)
const traceCpp = ref(false)
const language = ref<OjLanguage>('cpp')
const activePage = ref<'practice' | 'history' | 'favorite' | 'statistics'>('practice')
const practiceRecords = ref<OjPracticeRecord[]>([])
const favorite = ref(false)

const {
  running,
  submitting,
  tracing,
  narrating,
  diagnosing,
  visualTraceDiagnosing,
  traceSplitOpen,
  traceSourceCode,
  closeTraceSplit,
  onRun,
  onSubmit,
  onTrace,
  onNarrate,
  onAiDiagnose,
  onVisualTraceDiagnose,
  agentConsoleLines,
  struggleView,
  consecutiveFailures,
} = useOjWorkbenchActions({
  slug,
  code,
  language,
  problem,
  apiOnline,
  traceCpp,
  result,
  trace,
  diagnosis,
  traceBugDiagnosis,
  traceReport,
  traceReportLoading,
  router,
  loginRedirect: () => route.fullPath,
})

async function load() {
  loading.value = true
  result.value = null
  trace.value = null
  diagnosis.value = null
  traceBugDiagnosis.value = null
  try {
    const resolved = await resolveProblem(slug.value, { title: slug.value, lc_id: 0 })
    problem.value = resolved.problem
    apiOnline.value = resolved.apiOnline
    traceCpp.value = resolved.traceCpp === true
    code.value =
      resolved.problem.starter_code?.[language.value] ??
      resolved.problem.starter_code?.cpp ??
      resolved.problem.starter_code?.python ??
      ''
  } catch {
    problem.value = buildFallbackProblem(slug.value, slug.value)
    apiOnline.value = false
    traceCpp.value = false
    code.value = problem.value.starter_code?.cpp ?? problem.value.starter_code?.python ?? ''
  } finally {
    loading.value = false
  }
}

onMounted(() => void load())
watch(slug, () => void load())
watch(result, () => { practiceRecords.value = getOjPracticeRecords() }, { flush: 'post' })

function selectPage(page: typeof activePage.value) {
  activePage.value = page
  practiceRecords.value = getOjPracticeRecords()
  favorite.value = isOjFavorite(slug.value)
}

function onToggleFavorite() {
  favorite.value = toggleOjFavorite(slug.value)
}

function resetCode() {
  const p = problem.value?.starter_code
  if (!p) return
  code.value = p[language.value] ?? p.cpp ?? p.python ?? ''
}

async function loadJudgeDemo() {
  const scenario = getOjJudgeDemoScenario(slug.value)
  if (!scenario) return
  closeTraceSplit()
  language.value = scenario.language
  code.value = scenario.code
  result.value = null
  trace.value = null
  diagnosis.value = null
  traceBugDiagnosis.value = null
  traceReport.value = null
  traceReportLoading.value = false
  resetOjStruggleSession(slug.value)
  await nextTick()
  await onRun()
}
</script>

<template>
  <div v-loading="loading" class="practice-problem-page">
    <header v-if="problem" class="problem-toolbar">
      <div class="problem-toolbar__identity">
        <el-button text :icon="ArrowLeft" @click="router.push({ name: 'practice-list' })">返回题库</el-button>
        <span class="toolbar-divider" />
        <strong>#{{ problem.lc_id || '—' }} {{ problem.title }}</strong>
        <el-tag size="small" type="warning" effect="dark">{{ problem.difficulty === 'easy' ? '简单' : problem.difficulty === 'hard' ? '困难' : '中等' }}</el-tag>
        <el-tag size="small" effect="plain">算法训练</el-tag>
      </div>
      <div class="problem-toolbar__actions">
        <span class="service-state" :class="{ online: apiOnline }">{{ apiOnline ? '判题服务在线' : '离线模式' }}</span>
        <el-button size="small" :loading="running" @click="onRun">运行</el-button>
        <el-button size="small" type="primary" :loading="submitting" @click="onSubmit">提交</el-button>
      </div>
    </header>

    <div v-if="problem" class="problem-workspace">
      <nav class="problem-rail" aria-label="题目工具">
        <button class="rail-item" :class="{ 'is-active': activePage === 'practice' }" type="button" @click="selectPage('practice')"><el-icon><Collection /></el-icon><span>练习</span></button>
        <button class="rail-item" :class="{ 'is-active': activePage === 'history' }" type="button" @click="selectPage('history')"><el-icon><Clock /></el-icon><span>记录</span></button>
        <button class="rail-item" :class="{ 'is-active': activePage === 'favorite' }" type="button" @click="selectPage('favorite')"><el-icon><Star /></el-icon><span>收藏</span></button>
        <button class="rail-item" :class="{ 'is-active': activePage === 'statistics' }" type="button" @click="selectPage('statistics')"><el-icon><Histogram /></el-icon><span>统计</span></button>
      </nav>
      <OjPracticeRow
      v-if="activePage === 'practice'"
      v-model="code"
      v-model:language="language"
      :problem="problem"
      :running="running"
      :submitting="submitting"
      :tracing="tracing"
      :narrating="narrating"
      :diagnosing="diagnosing"
      :visual-trace-diagnosing="visualTraceDiagnosing"
      :trace-split-open="traceSplitOpen"
      :trace-source-code="traceSourceCode"
      :result="result"
      :trace="trace"
      :diagnosis="diagnosis"
      :trace-bug-diagnosis="traceBugDiagnosis"
      :trace-report="traceReport"
      :trace-report-loading="traceReportLoading"
      :api-online="apiOnline"
      :trace-cpp="traceCpp"
      :agent-console-lines="agentConsoleLines"
      :struggle-view="struggleView"
      :consecutive-failures="consecutiveFailures"
      @run="onRun"
      @submit="onSubmit"
      @trace="onTrace"
      @narrate="onNarrate"
      @diagnose="onAiDiagnose"
      @visual-trace-diagnose="onVisualTraceDiagnose"
      @demo="loadJudgeDemo"
      @close-trace="closeTraceSplit"
      @reset="resetCode"
      />
      <OjPracticeSubpage
        v-else
        :page="activePage"
        :problem="problem"
        :records="practiceRecords"
        :favorite="favorite"
        @back="selectPage('practice')"
        @toggle-favorite="onToggleFavorite"
      />
    </div>
    <el-empty v-else-if="!loading" description="题目不存在" />
  </div>
</template>

<style scoped>
.practice-problem-page {
  width: 100%;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
  min-width: 0;
  height: calc(100vh - var(--alp-header-height));
  background: #08151b;
}

.problem-toolbar {
  min-height: 52px; display: flex; align-items: center; justify-content: space-between;
  gap: 16px; padding: 0 16px; border-bottom: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-muted); box-sizing: border-box;
}
.problem-toolbar__identity, .problem-toolbar__actions { display: flex; align-items: center; gap: 9px; min-width: 0; }
.problem-toolbar__identity strong { overflow: hidden; color: var(--alp-color-text); font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.toolbar-divider { width: 1px; height: 22px; background: var(--alp-color-border); }
.service-state { font-size: 12px; color: var(--alp-color-danger); }
.service-state.online { color: var(--alp-color-success); }
.problem-workspace { display: grid; grid-template-columns: 58px minmax(0, 1fr); height: calc(100% - 52px); min-height: 0; }
.problem-rail { display: flex; flex-direction: column; gap: 6px; padding: 10px 6px; border-right: 1px solid var(--alp-color-border); background: #09171d; }
.rail-item { display: flex; min-height: 52px; flex-direction: column; align-items: center; justify-content: center; gap: 4px; border: 0; border-radius: 4px; background: transparent; color: var(--alp-color-muted); cursor: pointer; font: inherit; font-size: 10px; }
.rail-item .el-icon { font-size: 17px; }
.rail-item:hover { color: var(--alp-color-text); background: var(--alp-bg-hover); }
.rail-item.is-active { color: var(--alp-color-primary); background: var(--alp-color-primary-soft); }
.problem-workspace :deep(.oj-practice-layout), .problem-workspace :deep(.oj-practice-shell), .problem-workspace :deep(.oj-practice-center) { height: 100%; min-height: 0; }
html:not(.dark) .practice-problem-page { background: var(--alp-bg-page); }
html:not(.dark) .problem-rail { background: #f8fafc; }

@media (max-width: 900px) {
  .practice-problem-page { height: auto; min-height: calc(100vh - var(--alp-header-height)); overflow: visible; }
  .problem-toolbar { flex-wrap: wrap; padding-block: 8px; }
  .problem-toolbar__actions .service-state { display: none; }
  .problem-workspace { grid-template-columns: 1fr; height: auto; }
  .problem-rail { flex-direction: row; border-right: 0; border-bottom: 1px solid var(--alp-color-border); }
  .rail-item { min-height: 40px; flex: 1; flex-direction: row; }
}

@media (max-width: 600px) {
  .practice-problem-page {
    padding-left: 12px;
    padding-right: 12px;
  }
}
</style>
