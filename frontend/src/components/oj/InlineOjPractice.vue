<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import OjPracticeRow from '@/components/oj/OjPracticeRow.vue'
import { useOjWorkbenchActions } from '@/composables/useOjWorkbenchActions'
import {
  resolveProblem,
  type JudgeResponse,
  type ProblemDetail,
} from '@/api/oj'
import type { AiDiagnoseResponse, TraceDiagnosisReport, TraceResponse } from '@/types/codeTrace'
import type { PracticeLink } from '@/modules/shared/learningTypes'
import { buildFallbackProblem } from '@/api/ojLocal'
import { enrichProblemStarters, getStarterForLanguage } from '@/utils/ojStarterCode'

const props = defineProps<{
  main?: PracticeLink
  related?: PracticeLink[]
  linkLabel?: (p: PracticeLink) => string
}>()

const router = useRouter()
const activeSlug = ref('')
const loading = ref(false)
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
const language = ref<'python' | 'cpp'>('cpp')

defineExpose({
  problem,
  language,
  code,
})

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
  slug: activeSlug,
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
  loginRedirect: () => router.currentRoute.value.fullPath,
})

const tabs = computed(() => {
  const items: { slug: string; label: string; link: PracticeLink }[] = []
  if (props.main) {
    items.push({
      slug: props.main.slug,
      label: props.linkLabel?.(props.main) ?? props.main.title,
      link: props.main,
    })
  }
  for (const r of props.related ?? []) {
    items.push({
      slug: r.slug,
      label: props.linkLabel?.(r) ?? (r.id > 0 ? `力扣 ${r.id}` : r.title),
      link: r,
    })
  }
  return items
})

function findLink(slug: string): PracticeLink | undefined {
  if (props.main?.slug === slug) return props.main
  return props.related?.find((r) => r.slug === slug)
}

function applyStarter(p: ProblemDetail) {
  code.value = getStarterForLanguage(p, language.value)
}

watch(
  () => [props.main?.slug, props.related?.map((r) => r.slug).join(',')],
  () => {
    activeSlug.value = props.main?.slug ?? props.related?.[0]?.slug ?? ''
  },
  { immediate: true },
)

watch(
  activeSlug,
  (slug) => {
    if (slug) void loadProblem(slug)
  },
  { immediate: true },
)

watch(language, () => {
  if (problem.value) applyStarter(problem.value)
})

async function loadProblem(slug: string) {
  loading.value = true
  result.value = null
  trace.value = null
  diagnosis.value = null
  traceBugDiagnosis.value = null
  const link = findLink(slug)
  const meta = {
    title: link?.title ?? slug,
    lc_id: link?.id ?? 0,
  }

  try {
    const resolved = await resolveProblem(slug, meta)
    problem.value = enrichProblemStarters(resolved.problem, slug, meta.title, meta.lc_id)
    apiOnline.value = resolved.apiOnline
    traceCpp.value = resolved.traceCpp === true
    applyStarter(problem.value)
  } catch {
    problem.value = enrichProblemStarters(
      buildFallbackProblem(slug, meta.title, meta.lc_id),
      slug,
      meta.title,
      meta.lc_id,
    )
    apiOnline.value = false
    traceCpp.value = false
    applyStarter(problem.value)
  } finally {
    loading.value = false
  }
}

function resetCode() {
  if (problem.value) applyStarter(problem.value)
}
</script>

<template>
  <div v-if="tabs.length" class="inline-oj-wrap inline-oj">
    <el-tabs v-if="tabs.length > 1" v-model="activeSlug" class="oj-tabs">
      <el-tab-pane v-for="t in tabs" :key="t.slug" :label="t.label" :name="t.slug" />
    </el-tabs>

    <div v-loading="loading" class="oj-panel">
      <OjPracticeRow
        v-if="problem"
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
        @close-trace="closeTraceSplit"
        @reset="resetCode"
      />
    </div>
  </div>
</template>

<style scoped>
.inline-oj-wrap {
  margin-top: 12px;
  width: 100%;
}

.oj-tabs :deep(.el-tabs__header) {
  margin-bottom: 8px;
}

.oj-panel {
  min-height: 520px;
}
</style>
