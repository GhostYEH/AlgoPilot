<script setup lang="ts">
import { computed } from 'vue'
import type { TraceStepBrief } from '@/types/codeTrace'

const props = defineProps<{
  steps: TraceStepBrief[]
  errorStepIndex: number
}>()

const displaySteps = computed(() => {
  if (props.steps.length <= 20) return props.steps
  const errorIdx = props.errorStepIndex
  const around = props.steps.filter(
    (s) => Math.abs(s.step_index - errorIdx) <= 3,
  )
  const head = props.steps.slice(0, 4)
  const tail = props.steps.slice(-4)
  const seen = new Set<number>()
  const out: TraceStepBrief[] = []
  for (const s of [...head, ...around, ...tail]) {
    if (!seen.has(s.step_index)) {
      seen.add(s.step_index)
      out.push(s)
    }
  }
  return out.sort((a, b) => a.step_index - b.step_index)
})

const hasGap = computed(() => displaySteps.value.length < props.steps.length)
</script>

<template>
  <div class="step-timeline">
    <div
      v-for="step in displaySteps"
      :key="step.step_index"
      class="step-item"
      :class="{
        'step-item--error': step.is_error_step || step.step_index === errorStepIndex,
        'step-item--changed': step.changed_vars.length > 0 && step.step_index !== errorStepIndex,
      }"
    >
      <div class="step-dot" />
      <div class="step-body">
        <div class="step-head">
          <span class="step-idx">Step {{ step.step_index + 1 }}</span>
          <span class="step-line">L{{ step.line }}</span>
          <el-tag
            v-if="step.is_error_step || step.step_index === errorStepIndex"
            size="small"
            type="danger"
            effect="dark"
          >
            出错
          </el-tag>
        </div>
        <div v-if="step.changed_vars.length" class="step-vars">
          <span
            v-for="v in step.changed_vars"
            :key="v"
            class="step-var-chip"
            :class="{ 'step-var-chip--error': step.step_index === errorStepIndex }"
          >
            <span class="var-name">{{ v }}</span>
            <span v-if="step.var_summary[v]" class="var-val">= {{ step.var_summary[v] }}</span>
          </span>
        </div>
        <div v-else class="step-no-change">无变量变化</div>
      </div>
    </div>
    <p v-if="hasGap" class="step-gap">… 共 {{ steps.length }} 步，已省略中间步骤 …</p>
  </div>
</template>

<style scoped>
.step-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
  padding-left: 16px;
}

.step-timeline::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--alp-color-border);
  border-radius: 1px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 4px 0;
  position: relative;
}

.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--el-color-info-light-5);
  border: 2px solid var(--alp-bg-surface);
  flex-shrink: 0;
  margin-top: 5px;
  position: relative;
  z-index: 1;
}

.step-item--changed .step-dot {
  background: var(--el-color-primary);
}

.step-item--error .step-dot {
  background: var(--el-color-danger);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-danger) 25%, transparent);
}

.step-body {
  flex: 1;
  min-width: 0;
  padding: 2px 0;
}

.step-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.step-idx {
  font-size: 12px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.step-item--error .step-idx {
  color: var(--el-color-danger);
}

.step-line {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-color-primary);
  font-family: ui-monospace, Consolas, monospace;
}

.step-vars {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.step-var-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-family: ui-monospace, Consolas, monospace;
  background: color-mix(in srgb, var(--el-color-primary) 8%, var(--alp-bg-surface-muted));
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 20%, var(--alp-color-border));
}

.step-var-chip--error {
  background: color-mix(in srgb, var(--el-color-danger) 10%, var(--alp-bg-surface-muted));
  border-color: color-mix(in srgb, var(--el-color-danger) 30%, var(--alp-color-border));
}

.var-name {
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.step-var-chip--error .var-name {
  color: var(--el-color-danger);
}

.var-val {
  color: var(--el-text-color-secondary);
}

.step-no-change {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.step-gap {
  margin: 4px 0 0 26px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  font-style: italic;
}
</style>
