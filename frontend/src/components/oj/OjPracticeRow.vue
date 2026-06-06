<script setup lang="ts">
import OjWorkbench from '@/components/oj/OjWorkbench.vue'
import OjTraceSplitView from '@/components/oj/OjTraceSplitView.vue'
import type { JudgeResponse, ProblemDetail } from '@/api/oj'
import type { OjStruggleInterventionView } from '@/composables/useOjStruggleIntervention'

defineProps<{
  problem: ProblemDetail
  running: boolean
  submitting: boolean
  tracing?: boolean
  narrating?: boolean
  diagnosing?: boolean
  visualTraceDiagnosing?: boolean
  traceSplitOpen?: boolean
  traceSourceCode?: string
  result: JudgeResponse | null
  trace?: import('@/types/codeTrace').TraceResponse | null
  diagnosis?: import('@/types/codeTrace').AiDiagnoseResponse | null
  traceBugDiagnosis?: import('@/types/codeTrace').TraceBugDiagnoseResponse | null
  traceReport?: import('@/types/codeTrace').TraceDiagnosisReport | null
  traceReportLoading?: boolean
  apiOnline: boolean
  traceCpp?: boolean
  agentConsoleLines?: import('@/utils/agentConsole').AgentConsoleLine[]
  struggleView?: OjStruggleInterventionView | null
  consecutiveFailures?: number
}>()

const code = defineModel<string>({ required: true })
const language = defineModel<'python' | 'cpp'>('language', { required: true })

const emit = defineEmits<{
  run: []
  submit: []
  reset: []
  trace: []
  narrate: []
  diagnose: []
  visualTraceDiagnose: []
  closeTrace: []
}>()
</script>

<template>
  <div class="oj-practice-layout">
    <div
      class="oj-practice-shell"
      :class="{
        'oj-practice-shell--behind': traceSplitOpen,
      }"
    >
      <OjWorkbench
        v-if="!traceSplitOpen"
        v-model="code"
        v-model:language="language"
        class="oj-practice-center"
        :problem="problem"
        :running="running"
        :submitting="submitting"
        :tracing="tracing"
        :diagnosing="diagnosing"
        :visual-trace-diagnosing="visualTraceDiagnosing"
        :result="result"
        :diagnosis="diagnosis"
        :trace-report="traceReport"
        :trace-report-loading="traceReportLoading"
        :api-online="apiOnline"
        :trace-cpp="traceCpp"
        :agent-console-lines="agentConsoleLines"
        :struggle-view="struggleView"
        :consecutive-failures="consecutiveFailures"
        @run="emit('run')"
        @submit="emit('submit')"
        @reset="emit('reset')"
        @trace="emit('trace')"
        @diagnose="emit('diagnose')"
        @visual-trace-diagnose="emit('visualTraceDiagnose')"
      />
    </div>

    <OjTraceSplitView
      :open="traceSplitOpen ?? false"
      :trace="trace ?? null"
      :user-code="traceSourceCode || code"
      :tracing="tracing"
      :visual-trace-diagnosing="visualTraceDiagnosing"
      :narrating="narrating"
      :slug="problem.slug"
      :problem-description="problem.description"
      :language="language"
      :judge-verdict="result?.verdict ?? null"
      :bug-diagnosis="traceBugDiagnosis ?? null"
      @close="emit('closeTrace')"
      @narrate="emit('narrate')"
    >
      <OjWorkbench
        v-model="code"
        v-model:language="language"
        class="oj-practice-center oj-practice-center--split"
        :problem="problem"
        :running="running"
        :submitting="submitting"
        :tracing="tracing"
        :diagnosing="diagnosing"
        :visual-trace-diagnosing="visualTraceDiagnosing"
        :result="result"
        :diagnosis="diagnosis"
        :api-online="apiOnline"
        :trace-cpp="traceCpp"
        trace-layout
        @run="emit('run')"
        @submit="emit('submit')"
        @reset="emit('reset')"
        @trace="emit('trace')"
        @diagnose="emit('diagnose')"
        @visual-trace-diagnose="emit('visualTraceDiagnose')"
      />
    </OjTraceSplitView>
  </div>
</template>

<style scoped>
.oj-practice-layout {
  width: 100%;
  min-width: 0;
}

.oj-practice-shell {
  position: relative;
  width: 100%;
  min-height: 520px;
  box-sizing: border-box;
  transition: opacity 0.28s ease, filter 0.28s ease;
}

.oj-practice-shell--behind {
  opacity: 0.35;
  filter: blur(1px);
  pointer-events: none;
}

.oj-practice-center {
  min-width: 0;
  width: 100%;
}

.oj-practice-center--split {
  height: 100%;
}
</style>
