<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import OjPracticeRow from '@/components/oj/OjPracticeRow.vue'
import { useOjWorkbenchActions } from '@/composables/useOjWorkbenchActions'
import { resolveProblem, type JudgeResponse, type ProblemDetail, type OjLanguage } from '@/api/oj'
import type { AiDiagnoseResponse, TraceResponse } from '@/types/codeTrace'
import { buildFallbackProblem } from '@/api/ojLocal'

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
const apiOnline = ref(false)
const traceCpp = ref(false)
const language = ref<OjLanguage>('cpp')

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

function resetCode() {
  const p = problem.value?.starter_code
  if (!p) return
  code.value = p[language.value] ?? p.cpp ?? p.python ?? ''
}
</script>

<template>
  <div v-loading="loading" class="practice-problem-page">
    <header class="head">
      <el-button text :icon="ArrowLeft" @click="router.push({ name: 'practice-list' })">
        返回题库
      </el-button>
    </header>

    <OjPracticeRow
      v-if="problem"
      v-model="code"
      v-model:language="language"
      hints-outside
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
      :api-online="apiOnline"
      :trace-cpp="traceCpp"
      :agent-console-lines="agentConsoleLines"
      @run="onRun"
      @submit="onSubmit"
      @trace="onTrace"
      @narrate="onNarrate"
      @diagnose="onAiDiagnose"
      @visual-trace-diagnose="onVisualTraceDiagnose"
      @close-trace="closeTraceSplit"
      @reset="resetCode"
    />
    <el-empty v-else-if="!loading" description="题目不存在" />
  </div>
</template>

<style scoped>
.practice-problem-page {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 8px var(--alp-layout-padding-x, 16px) 24px;
  box-sizing: border-box;
  overflow: visible;
  min-width: 0;
}

.practice-problem-page :deep(.oj-practice-layout) {
  margin-left: calc(-1 * var(--alp-layout-padding-x, 16px));
  margin-right: calc(-1 * var(--alp-layout-padding-x, 16px));
  width: calc(100% + 2 * var(--alp-layout-padding-x, 16px));
  max-width: none;
}

.head {
  margin-bottom: 12px;
}

@media (max-width: 600px) {
  .practice-problem-page {
    padding-left: 12px;
    padding-right: 12px;
  }

  .practice-problem-page :deep(.oj-practice-layout) {
    width: 100%;
    margin-left: 0;
    margin-right: 0;
  }
}
</style>
