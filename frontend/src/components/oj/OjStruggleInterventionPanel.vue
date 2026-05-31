<script setup lang="ts">
import { computed } from 'vue'
import { Collection, Guide, TrendCharts, Warning } from '@element-plus/icons-vue'
import type { OjStruggleInterventionView } from '@/composables/useOjStruggleIntervention'

const props = defineProps<{
  state: OjStruggleInterventionView | null
}>()

const showPanel = computed(
  () =>
    !!props.state &&
    (props.state.loading ||
      props.state.fallbackMode ||
      !!props.state.result ||
      !!props.state.errorMessage),
)

const skillCards = computed(() => props.state?.result?.recommended_skill_cards ?? [])

const errorSummary = computed(() => {
  const r = props.state?.result
  if (!r) return props.state?.errorPattern ?? ''
  const parts = [
    r.plan_summary,
    r.remediation_label ? `巩固建议：${r.remediation_label}` : '',
    props.state?.errorPattern,
  ].filter(Boolean)
  return parts.join(' · ')
})
</script>

<template>
  <section v-if="showPanel && state" class="struggle-panel">
    <header class="struggle-head">
      <el-icon><Warning /></el-icon>
      <span>智能体学情干预 · EvaluatorAgent</span>
      <el-tag v-if="state.consecutiveFailures >= 3" size="small" type="danger" effect="plain">
        连续 {{ state.consecutiveFailures }} 次未通过
      </el-tag>
    </header>

    <div v-if="state.loading" class="struggle-loading" aria-live="polite" aria-busy="true">
      <div class="struggle-spinner" aria-hidden="true" />
      <p>检测到连续受挫，智能体正在分析学习短板……</p>
    </div>

    <el-alert
      v-else-if="state.fallbackMode"
      type="warning"
      :closable="false"
      show-icon
      title="本地学情提示"
      :description="state.fallbackMessage"
    />

    <el-alert
      v-else-if="state.errorMessage"
      type="error"
      :closable="false"
      show-icon
      title="智能体干预暂不可用"
      :description="state.errorMessage"
    />

    <template v-else-if="state.result">
      <p v-if="errorSummary" class="struggle-summary">{{ errorSummary }}</p>

      <div
        v-if="state.result.remediation_label || state.result.remediation_module_key"
        class="struggle-block"
      >
        <span class="block-label">推荐资源</span>
        <p class="resource-hint">
          优先巩固模块「{{ state.result.remediation_label || state.result.remediation_module_key }}」
          <template v-if="state.result.remediation_module_key">
            （{{ state.result.remediation_module_key }}）
          </template>
        </p>
      </div>

      <div v-if="skillCards.length" class="struggle-block">
        <span class="block-label">推荐 SkillCard</span>
        <ul class="skill-list">
          <li v-for="card in skillCards" :key="card.id">
            <el-tag type="primary" size="small">{{ card.name }}</el-tag>
            <span class="skill-id">{{ card.id }}</span>
            <p v-if="card.description" class="skill-desc">{{ card.description }}</p>
          </li>
        </ul>
      </div>

      <div class="struggle-outcomes">
        <el-tag v-if="state.memoryWritten" type="info" size="small" effect="plain">
          已写入 StudentMemory
        </el-tag>
        <el-tag v-if="state.masteryLinked" type="warning" size="small" effect="plain">
          已联动掌握度评估
        </el-tag>
        <el-tag v-if="state.pathAdjustSuggested" type="success" size="small" effect="plain">
          <el-icon><Guide /></el-icon>
          建议调整学习路径
        </el-tag>
        <el-tag v-else-if="state.result.struggle_detected" type="info" size="small" effect="plain">
          路径暂无需调整
        </el-tag>
      </div>

      <p v-if="state.pathAdjustSuggested && state.result.remediation_label" class="path-hint">
        <el-icon><Collection /></el-icon>
        PlannerAgent：优先巩固「{{ state.result.remediation_label }}」
        <template v-if="state.result.path_updated">（路径已更新）</template>
      </p>

      <p v-if="state.result.plan_summary && !errorSummary.includes(state.result.plan_summary)" class="plan-summary">
        <el-icon><TrendCharts /></el-icon>
        {{ state.result.plan_summary }}
      </p>
    </template>
  </section>
</template>

<style scoped>
.struggle-panel {
  margin: 10px 0 0;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  border: 1px solid color-mix(in srgb, var(--el-color-warning) 40%, var(--alp-color-border));
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--el-color-warning) 8%, var(--alp-bg-surface-muted)) 0%,
    var(--alp-bg-surface-muted) 100%
  );
}

.struggle-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-color-warning);
}

.struggle-loading {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.struggle-spinner {
  width: 22px;
  height: 22px;
  border: 2px solid color-mix(in srgb, var(--el-color-warning) 25%, transparent);
  border-top-color: var(--el-color-warning);
  border-radius: 50%;
  animation: struggle-spin 0.85s linear infinite;
  flex-shrink: 0;
}

@keyframes struggle-spin {
  to {
    transform: rotate(360deg);
  }
}

.struggle-summary {
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--el-text-color-primary);
}

.resource-hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--el-text-color-regular);
}

.struggle-block {
  margin-bottom: 10px;
}

.block-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 6px;
}

.skill-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.skill-list li {
  padding: 8px 10px;
  margin-bottom: 6px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
}

.skill-id {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-left: 6px;
  font-family: ui-monospace, Consolas, monospace;
}

.skill-desc {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--el-text-color-secondary);
}

.struggle-outcomes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.path-hint,
.plan-summary {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 0 0 6px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.path-hint {
  color: var(--el-color-warning);
}
</style>
