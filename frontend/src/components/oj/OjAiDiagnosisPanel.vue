<script setup lang="ts">
import { computed } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'
import type { AiDiagnoseResponse } from '@/types/codeTrace'
import OjTutoringSection from '@/components/oj/OjTutoringSection.vue'

const props = defineProps<{
  diagnosis: AiDiagnoseResponse | null
  loading?: boolean
}>()

const edgeVerdictType = computed(() => {
  const v = props.diagnosis?.edge_verdict
  if (v === 'AC') return 'success'
  if (v === 'WA') return 'warning'
  return 'danger'
})

const edgeVerdictLabel = computed(() => {
  const map: Record<string, string> = {
    AC: '通过',
    WA: '答案错误',
    TLE: '超时',
    RE: '运行错误',
    CE: '编译错误',
  }
  return map[props.diagnosis?.edge_verdict ?? ''] ?? props.diagnosis?.edge_verdict
})
</script>

<template>
  <div v-if="diagnosis || loading" v-loading="loading" class="ai-diagnosis-panel">
    <header class="ai-diagnosis-head">
      <el-icon class="ai-diagnosis-icon"><MagicStick /></el-icon>
      <span class="ai-diagnosis-title">AI 深度诊断</span>
    </header>

    <template v-if="diagnosis">
      <p class="ai-diagnosis-summary">{{ diagnosis.summary }}</p>

      <section class="ai-diagnosis-block">
        <div class="block-label">边界测例</div>
        <div class="edge-meta">
          <el-tag size="small" type="info">{{ diagnosis.edge_case.category }}</el-tag>
          <el-tag size="small" :type="edgeVerdictType">判题 {{ edgeVerdictLabel }}</el-tag>
        </div>
        <p class="edge-reason">{{ diagnosis.edge_case.reason }}</p>
        <div class="io-preview">
          <div class="io-preview-row">
            <span class="io-preview-label">输入</span>
            <pre class="io-preview-val">{{ diagnosis.edge_case.input_preview }}</pre>
          </div>
          <div class="io-preview-row">
            <span class="io-preview-label">期望</span>
            <pre class="io-preview-val">{{ diagnosis.edge_case.expected_preview }}</pre>
          </div>
        </div>
      </section>

      <section class="ai-diagnosis-block ai-diagnosis-block--complexity">
        <div class="block-label">时空复杂度具象化</div>
        <div class="complexity-tags">
          <el-tag size="small" type="primary">N = {{ diagnosis.complexity.input_size_n }}</el-tag>
          <el-tag size="small">{{ diagnosis.complexity.total_steps }} 步</el-tag>
          <el-tag size="small" type="warning">{{ diagnosis.complexity.estimated_complexity }}</el-tag>
        </div>
        <p class="complexity-report">{{ diagnosis.complexity.report }}</p>
        <p v-if="diagnosis.complexity.alternative_hint" class="complexity-alt">
          {{ diagnosis.complexity.alternative_hint }}
        </p>
      </section>

      <OjTutoringSection :tutoring="diagnosis.tutoring" />
    </template>
  </div>
</template>

<style scoped>
.ai-diagnosis-panel {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  border: 1px solid color-mix(in srgb, var(--el-color-danger) 35%, var(--alp-color-border));
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--el-color-danger) 6%, var(--alp-bg-surface-muted)) 0%,
    var(--alp-bg-surface-muted) 100%
  );
}

.ai-diagnosis-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.ai-diagnosis-icon {
  color: var(--el-color-danger);
  font-size: 18px;
}

.ai-diagnosis-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.ai-diagnosis-summary {
  margin: 0 0 12px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.ai-diagnosis-block {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.ai-diagnosis-block--complexity {
  margin-bottom: 0;
  border-color: color-mix(in srgb, var(--el-color-primary) 30%, var(--alp-color-border));
}

.block-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.edge-meta,
.complexity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.edge-reason {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--el-text-color-secondary);
}

.io-preview {
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.io-preview-row {
  display: grid;
  grid-template-columns: 48px 1fr;
  border-bottom: 1px solid var(--el-border-color-extra-light);
}

.io-preview-row:last-child {
  border-bottom: none;
}

.io-preview-label {
  padding: 6px 8px;
  font-size: 11px;
  font-weight: 600;
  background: var(--el-fill-color-light);
}

.io-preview-val {
  margin: 0;
  padding: 6px 8px;
  font-size: 12px;
  font-family: ui-monospace, Consolas, monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

.complexity-report {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--el-text-color-regular);
}

.complexity-alt {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.55;
  color: var(--el-color-primary);
}
</style>
