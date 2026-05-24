<script setup lang="ts">
import OjWorkbench from '@/components/oj/OjWorkbench.vue'
import OjDsHintCard from '@/components/oj/OjDsHintCard.vue'
import OjCodeHintCard from '@/components/oj/OjCodeHintCard.vue'
import OjTraceSplitView from '@/components/oj/OjTraceSplitView.vue'
import type { JudgeResponse, ProblemDetail } from '@/api/oj'

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
  apiOnline: boolean
  traceCpp?: boolean
  hintsOutside?: boolean
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
        'oj-practice-shell--outside': hintsOutside && !traceSplitOpen,
        'oj-practice-shell--behind': traceSplitOpen,
      }"
    >
      <OjDsHintCard
        v-show="!traceSplitOpen"
        class="oj-practice-side oj-practice-side--ds"
        :problem="problem"
        :language="language"
      />
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
        :api-online="apiOnline"
        :trace-cpp="traceCpp"
        @run="emit('run')"
        @submit="emit('submit')"
        @reset="emit('reset')"
        @trace="emit('trace')"
        @diagnose="emit('diagnose')"
        @visual-trace-diagnose="emit('visualTraceDiagnose')"
      />
      <OjCodeHintCard
        v-show="!traceSplitOpen"
        class="oj-practice-side oj-practice-side--hint"
        :problem="problem"
        :language="language"
        :user-code="code"
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
  --oj-side-width: 220px;
  --oj-side-gap: 16px;
  --oj-sticky-top: calc(var(--alp-header-height, 60px) + 16px);
  position: relative;
  display: grid;
  grid-template-columns: var(--oj-side-width) minmax(0, 1fr) var(--oj-side-width);
  gap: var(--oj-side-gap);
  align-items: start;
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

.oj-practice-shell--outside {
  --oj-outside-pad: calc(var(--oj-side-width) + var(--oj-side-gap));
  width: calc(100% + 2 * var(--oj-outside-pad));
  max-width: none;
  margin-left: calc(-1 * var(--oj-outside-pad));
  margin-right: calc(-1 * var(--oj-outside-pad));
  padding-left: 0;
  padding-right: 0;
  grid-template-columns: var(--oj-side-width) minmax(0, 1fr) var(--oj-side-width);
}

.oj-practice-center {
  min-width: 0;
  width: 100%;
  grid-column: 2;
}

.oj-practice-center--split {
  height: 100%;
}

.oj-practice-shell--outside .oj-practice-side--ds {
  grid-column: 1;
  justify-self: start;
}

.oj-practice-shell--outside .oj-practice-side--hint {
  grid-column: 3;
  justify-self: end;
}

.oj-practice-side {
  width: var(--oj-side-width);
  min-width: var(--oj-side-width);
  max-width: var(--oj-side-width);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: var(--oj-sticky-top);
  align-self: start;
  max-height: calc(100vh - var(--oj-sticky-top) - 24px);
  flex-shrink: 0;
}

.oj-practice-side :deep(.oj-agent-card) {
  flex: 1;
  min-height: 0;
  max-height: inherit;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.oj-practice-side :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.oj-practice-side :deep(.oj-agent-body) {
  flex: 1;
  min-height: 80px;
  max-height: none;
  overflow-y: auto;
}

@media (min-width: 1400px) {
  .oj-practice-shell {
    --oj-side-width: 240px;
  }
}

@media (min-width: 1600px) {
  .oj-practice-shell {
    --oj-side-width: min(248px, var(--alp-aside-width, 248px));
  }
}

@media (max-width: 1199px) {
  .oj-practice-shell {
    --oj-side-width: 200px;
  }
}

@media (max-width: 1399px) {
  .oj-practice-shell,
  .oj-practice-shell--outside {
    width: 100%;
    margin-left: 0;
    margin-right: 0;
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }

  .oj-practice-center,
  .oj-practice-shell--outside .oj-practice-side--ds,
  .oj-practice-shell--outside .oj-practice-center,
  .oj-practice-shell--outside .oj-practice-side--hint {
    grid-column: 1;
  }

  .oj-practice-side {
    position: static;
    max-height: none;
  }

  .oj-practice-side :deep(.oj-agent-card) {
    max-height: none;
  }

  .oj-practice-side :deep(.oj-agent-body) {
    max-height: 200px;
  }
}
</style>
