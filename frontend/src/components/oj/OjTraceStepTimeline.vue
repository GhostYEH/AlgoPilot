<script setup lang="ts">
import { computed } from 'vue'
import type { TraceStepBrief } from '@/types/codeTrace'

const props = defineProps<{
  steps: TraceStepBrief[]
  errorStepIndex: number
}>()

const displaySteps = computed(() => {
  if (props.steps.length <= 20) return props.steps
  const aroundError = props.steps.filter(
    (step) => Math.abs(step.step_index - props.errorStepIndex) <= 3,
  )
  const seen = new Set<number>()
  return [...props.steps.slice(0, 4), ...aroundError, ...props.steps.slice(-4)]
    .filter((step) => {
      if (seen.has(step.step_index)) return false
      seen.add(step.step_index)
      return true
    })
    .sort((a, b) => a.step_index - b.step_index)
})

type TimelineItem =
  | { kind: 'step'; step: TraceStepBrief }
  | { kind: 'gap'; from: number; to: number; count: number }

const timelineItems = computed<TimelineItem[]>(() => {
  const items: TimelineItem[] = []
  displaySteps.value.forEach((step, index) => {
    const previous = displaySteps.value[index - 1]
    if (previous && step.step_index - previous.step_index > 1) {
      items.push({
        kind: 'gap',
        from: previous.step_index + 2,
        to: step.step_index,
        count: step.step_index - previous.step_index - 1,
      })
    }
    items.push({ kind: 'step', step })
  })
  return items
})

const changedStepCount = computed(
  () => props.steps.filter((step) => step.changed_vars.length > 0).length,
)
</script>

<template>
  <div class="trace-preview">
    <header class="trace-preview__summary">
      <div>
        <strong>{{ steps.length }}</strong>
        <span>轨迹步骤</span>
      </div>
      <div>
        <strong>{{ changedStepCount }}</strong>
        <span>变量发生变化</span>
      </div>
      <div v-if="errorStepIndex >= 0" class="trace-preview__summary-error">
        <strong>Step {{ errorStepIndex + 1 }}</strong>
        <span>首次可疑步骤</span>
      </div>
    </header>

    <div class="step-grid">
      <template
        v-for="item in timelineItems"
        :key="item.kind === 'step' ? `step-${item.step.step_index}` : `gap-${item.from}`"
      >
        <div v-if="item.kind === 'gap'" class="step-gap">
          <span>省略 {{ item.count }} 步</span>
          <small>Step {{ item.from }}–{{ item.to }}</small>
        </div>

        <article
          v-else
          class="step-card"
          :class="{
            'step-card--error': item.step.is_error_step || item.step.step_index === errorStepIndex,
            'step-card--changed': item.step.changed_vars.length > 0 && item.step.step_index !== errorStepIndex,
          }"
        >
          <header class="step-card__head">
            <div class="step-number">{{ item.step.step_index + 1 }}</div>
            <div class="step-meta">
              <strong>Step {{ item.step.step_index + 1 }}</strong>
              <span>代码第 {{ item.step.line }} 行</span>
            </div>
            <el-tag
              v-if="item.step.is_error_step || item.step.step_index === errorStepIndex"
              size="small"
              type="danger"
              effect="dark"
            >
              首次可疑
            </el-tag>
            <span v-else-if="item.step.changed_vars.length" class="step-status">已更新</span>
          </header>

          <div v-if="item.step.changed_vars.length" class="step-vars">
            <div v-for="variable in item.step.changed_vars" :key="variable" class="step-var">
              <span class="var-name">{{ variable }}</span>
              <code class="var-val">{{ item.step.var_summary[variable] || '—' }}</code>
            </div>
          </div>
          <div v-else class="step-no-change">本步没有记录到变量变化</div>
        </article>
      </template>
    </div>
  </div>
</template>

<style scoped>
.trace-preview {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.trace-preview__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  overflow: hidden;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  background: var(--alp-bg-surface-muted);
}

.trace-preview__summary > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  padding: 10px 12px;
}

.trace-preview__summary > div + div {
  border-left: 1px solid var(--alp-color-border);
}

.trace-preview__summary strong {
  font-size: 15px;
  line-height: 1.2;
  color: var(--el-text-color-primary);
}

.trace-preview__summary span {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.trace-preview__summary-error strong,
.trace-preview__summary-error span {
  color: var(--el-color-danger);
}

.step-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 10px;
  align-items: stretch;
}

.step-card {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  background: var(--alp-bg-surface);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.step-card--changed {
  border-color: color-mix(in srgb, var(--el-color-primary) 28%, var(--alp-color-border));
}

.step-card--error {
  border-color: color-mix(in srgb, var(--el-color-danger) 65%, var(--alp-color-border));
  background: color-mix(in srgb, var(--el-color-danger) 7%, var(--alp-bg-surface));
  box-shadow: 0 8px 24px color-mix(in srgb, var(--el-color-danger) 11%, transparent);
}

.step-card__head {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  margin-bottom: 10px;
}

.step-number {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 10%, var(--alp-bg-surface-muted));
  font: 700 12px/1 ui-monospace, Consolas, monospace;
}

.step-card--error .step-number {
  color: #fff;
  background: var(--el-color-danger);
}

.step-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.step-meta strong {
  font-size: 12px;
  color: var(--el-text-color-primary);
}

.step-meta span,
.step-status {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.step-status {
  color: var(--el-color-primary);
  font-weight: 600;
}

.step-vars {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
  gap: 6px;
}

.step-var {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  padding: 7px 8px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 16%, var(--alp-color-border));
  border-radius: 7px;
  background: var(--alp-bg-surface-muted);
}

.step-card--error .step-var {
  border-color: color-mix(in srgb, var(--el-color-danger) 25%, var(--alp-color-border));
}

.var-name {
  overflow: hidden;
  color: var(--el-text-color-secondary);
  font: 600 10px/1.3 ui-monospace, Consolas, monospace;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.var-val {
  overflow: hidden;
  padding: 0;
  color: var(--el-text-color-primary);
  background: transparent;
  font: 600 12px/1.4 ui-monospace, Consolas, monospace;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-no-change {
  padding: 8px;
  border-radius: 7px;
  color: var(--el-text-color-placeholder);
  background: var(--alp-bg-surface-muted);
  font-size: 11px;
  text-align: center;
}

.step-gap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 84px;
  padding: 10px;
  border: 1px dashed var(--alp-color-border);
  border-radius: 10px;
  color: var(--el-text-color-secondary);
  background: var(--alp-bg-surface-muted);
  font-size: 12px;
}

.step-gap small {
  margin-top: 3px;
  color: var(--el-text-color-placeholder);
  font-family: ui-monospace, Consolas, monospace;
}

@media (max-width: 680px) {
  .trace-preview__summary {
    grid-template-columns: 1fr;
  }

  .trace-preview__summary > div + div {
    border-top: 1px solid var(--alp-color-border);
    border-left: 0;
  }

  .step-grid {
    grid-template-columns: 1fr;
  }
}
</style>
