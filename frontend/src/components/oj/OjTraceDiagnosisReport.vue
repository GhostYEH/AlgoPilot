<script setup lang="ts">
import { computed } from 'vue'
import {
  Warning,
  Document,
  MagicStick,
  Compass,
  TrendCharts,
  Collection,
  Guide,
} from '@element-plus/icons-vue'
import type { TraceDiagnosisReport } from '@/types/codeTrace'
import OjTraceStepTimeline from '@/components/oj/OjTraceStepTimeline.vue'

const props = defineProps<{
  report: TraceDiagnosisReport | null
  loading?: boolean
  consecutiveFailures?: number
}>()

const VERDICT_TAG: Record<string, { label: string; type: 'danger' | 'warning' | 'info' }> = {
  WA: { label: 'WA · 答案错误', type: 'warning' },
  TLE: { label: 'TLE · 超时', type: 'danger' },
  RE: { label: 'RE · 运行错误', type: 'danger' },
  CE: { label: 'CE · 编译错误', type: 'danger' },
}

const errorTag = computed(() => {
  const et = props.report?.error_type ?? ''
  return VERDICT_TAG[et] ?? { label: et || '未知', type: 'info' as const }
})

const sourceLabel = computed(() => {
  const s = props.report?.source
  if (s === 'llm') return 'AI 诊断'
  if (s === 'demo') return '静态兜底'
  return '规则诊断'
})

const sourceTagType = computed(() => {
  const s = props.report?.source
  if (s === 'llm') return 'success'
  if (s === 'demo') return 'info'
  return 'warning'
})

const confidenceMeta = computed(() => {
  const confidence = props.report?.diagnosis_confidence
  if (confidence === 'high') return { label: '高置信度', type: 'success' as const }
  if (confidence === 'medium') return { label: '中等置信度', type: 'warning' as const }
  return { label: '线索级', type: 'info' as const }
})

const RESOURCE_TYPE_LABEL: Record<string, string> = {
  document: '概念文档',
  mindmap: '思维导图',
  exercises: '变式题单',
  code_case: '代码沙盒',
  trace_animation: 'Trace 动画',
  reading: '拓展阅读',
}

const errorStepDisplay = computed(() => {
  const es = props.report?.error_step
  if (!es) return null
  return `Step ${es.step_index + 1} · 代码第 ${es.line} 行`
})
</script>

<template>
  <div v-if="report || loading" v-loading="loading" class="trace-report">
    <header class="trace-report__head">
      <el-icon class="trace-report__icon"><MagicStick /></el-icon>
      <span class="trace-report__title">AI Trace 诊断报告</span>
      <el-tag v-if="report" size="small" :type="sourceTagType" effect="plain">
        {{ sourceLabel }}
      </el-tag>
      <el-tag v-if="report" size="small" :type="confidenceMeta.type" effect="plain">
        {{ confidenceMeta.label }}
      </el-tag>
    </header>

    <template v-if="report">
      <el-alert
        v-if="report.evidence_summary"
        :type="report.trace_case_reproduced ? 'success' : 'warning'"
        :title="report.trace_case_reproduced ? '失败用例已复现' : '诊断证据有限'"
        :description="report.evidence_summary"
        :closable="false"
        show-icon
        class="trace-report__evidence"
      />
      <p class="trace-report__learning-loop-note">
        系统不仅判断对错，还基于 Trace 捕捉学生错误发生的具体步骤，并反向更新学习画像与路径规划。
      </p>
      <div class="trace-report__meta">
        <div class="trace-report__meta-row">
          <span class="trace-report__label">错误类型</span>
          <el-tag size="small" :type="errorTag.type">{{ errorTag.label }}</el-tag>
        </div>
        <div v-if="report.error_category_label" class="trace-report__meta-row">
          <span class="trace-report__label">错因分类</span>
          <el-tag size="small" type="danger" effect="plain">
            {{ report.error_category_label }}
          </el-tag>
        </div>
        <div class="trace-report__meta-row">
          <span class="trace-report__label">失败测试点</span>
          <span class="trace-report__value">{{ report.failed_test_point || '—' }}</span>
        </div>
        <div v-if="errorStepDisplay" class="trace-report__meta-row trace-report__meta-row--error">
          <span class="trace-report__label">
            <el-icon><Warning /></el-icon>
            出错步骤
          </span>
          <el-tag size="small" type="danger" effect="dark">{{ errorStepDisplay }}</el-tag>
        </div>
      </div>

      <section v-if="report.key_variable_changes.length" class="trace-report__section">
        <div class="trace-report__section-title">
          <el-icon><TrendCharts /></el-icon>
          关键变量变化
        </div>
        <div class="trace-report__var-changes">
          <div
            v-for="(vc, i) in report.key_variable_changes"
            :key="i"
            class="trace-report__var-change"
            :class="{ 'trace-report__var-change--error': report.error_step?.step_index === vc.step_index }"
          >
            <span class="vc-step">Step {{ vc.step_index + 1 }}</span>
            <span class="vc-line">L{{ vc.line }}</span>
            <span class="vc-name">{{ vc.variable_name }}</span>
            <span class="vc-arrow">→</span>
            <span class="vc-before">{{ vc.before }}</span>
            <span class="vc-sep">→</span>
            <span class="vc-after">{{ vc.after }}</span>
          </div>
        </div>
      </section>

      <section v-if="report.possible_cause" class="trace-report__section">
        <div class="trace-report__section-title">
          <el-icon><Warning /></el-icon>
          可能原因
        </div>
        <p class="trace-report__text">{{ report.possible_cause }}</p>
      </section>

      <section v-if="report.why_failed" class="trace-report__section">
        <div class="trace-report__section-title">
          <el-icon><Warning /></el-icon>
          为什么导致 WA
        </div>
        <p class="trace-report__text">{{ report.why_failed }}</p>
      </section>

      <section v-if="report.fix_suggestion" class="trace-report__section trace-report__section--fix">
        <div class="trace-report__section-title">
          <el-icon><Compass /></el-icon>
          修复建议
        </div>
        <p class="trace-report__text trace-report__text--fix">{{ report.fix_suggestion }}</p>
      </section>

      <section
        v-if="report.recommended_knowledge_points.length"
        class="trace-report__section"
      >
        <div class="trace-report__section-title">
          <el-icon><Collection /></el-icon>
          推荐巩固知识点
        </div>
        <div class="trace-report__knowledge-points">
          <el-tag
            v-for="point in report.recommended_knowledge_points"
            :key="point"
            size="small"
            type="warning"
            effect="plain"
          >
            {{ point }}
          </el-tag>
        </div>
      </section>

      <section v-if="report.trace_steps.length" class="trace-report__section">
        <div class="trace-report__section-title">
          <el-icon><Collection /></el-icon>
          执行轨迹概览
        </div>
        <OjTraceStepTimeline
          :steps="report.trace_steps"
          :error-step-index="report.error_step?.step_index ?? -1"
        />
      </section>

      <section v-if="report.recommended_resources.length" class="trace-report__section">
        <div class="trace-report__section-title">
          <el-icon><Document /></el-icon>
          推荐复习资源
        </div>
        <ul class="trace-report__resources">
          <li v-for="(res, i) in report.recommended_resources" :key="i">
            <el-tag size="small" effect="plain">
              {{ RESOURCE_TYPE_LABEL[res.resource_type] ?? res.resource_type }}
            </el-tag>
            <span class="res-topic">{{ res.topic }}</span>
            <span v-if="res.reason" class="res-reason">{{ res.reason }}</span>
          </li>
        </ul>
      </section>

      <div v-if="report.path_rearrange_triggered" class="trace-report__path-alert">
        <el-icon><Guide /></el-icon>
        <div>
          <strong>学习路径调整建议</strong>
          <p>
            {{
              report.intervention_suggestion ||
              report.tutoring?.path_adjustment_hint ||
              '检测到知识薄弱点，建议在当前路径前插入对应巩固节点。'
            }}
          </p>
        </div>
      </div>
      <div
        v-else-if="report.learning_intervention_generated && report.intervention_suggestion"
        class="trace-report__intervention"
      >
        <el-icon><Guide /></el-icon>
        <span>{{ report.intervention_suggestion }}</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.trace-report {
  margin-top: 12px;
  padding: 16px 18px;
  border-radius: var(--alp-radius-card);
  border: 1px solid color-mix(in srgb, var(--el-color-danger) 40%, var(--alp-color-border));
  background: color-mix(in srgb, var(--el-color-danger) 6%, var(--alp-bg-surface-muted));
}

.trace-report__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.trace-report__icon {
  color: var(--el-color-danger);
  font-size: 20px;
}

.trace-report__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.trace-report__meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.trace-report__learning-loop-note {
  margin: 0 0 12px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 35%, var(--alp-color-border));
  background: color-mix(in srgb, var(--el-color-primary) 7%, var(--alp-bg-surface));
  font-size: 13px;
  line-height: 1.65;
  color: var(--el-text-color-primary);
}

.trace-report__evidence {
  margin-bottom: 12px;
}

.trace-report__meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.trace-report__meta-row--error {
  padding: 6px 10px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--el-color-danger) 10%, var(--alp-bg-surface));
  border: 1px solid color-mix(in srgb, var(--el-color-danger) 30%, var(--alp-color-border));
}

.trace-report__label {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 80px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.trace-report__value {
  color: var(--el-text-color-primary);
  font-size: 13px;
}

.trace-report__section {
  margin-bottom: 14px;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.trace-report__section--fix {
  border-color: color-mix(in srgb, var(--el-color-success) 35%, var(--alp-color-border));
}

.trace-report__section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.trace-report__text {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--el-text-color-regular);
}

.trace-report__text--fix {
  color: var(--el-color-success);
  font-weight: 500;
}

.trace-report__var-changes {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.trace-report__var-change {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-family: ui-monospace, Consolas, monospace;
  background: var(--alp-bg-surface-muted);
  border: 1px solid var(--alp-color-border);
}

.trace-report__var-change--error {
  border-color: color-mix(in srgb, var(--el-color-danger) 50%, var(--alp-color-border));
  background: color-mix(in srgb, var(--el-color-danger) 8%, var(--alp-bg-surface-muted));
}

.vc-step {
  color: var(--el-text-color-secondary);
  font-weight: 600;
}

.vc-line {
  color: var(--el-color-primary);
  font-weight: 600;
}

.vc-name {
  color: var(--el-color-danger);
  font-weight: 700;
}

.vc-arrow,
.vc-sep {
  color: var(--el-text-color-placeholder);
}

.vc-before {
  color: var(--el-text-color-secondary);
}

.vc-after {
  color: var(--el-color-primary);
  font-weight: 600;
}

.trace-report__resources {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}

.trace-report__knowledge-points {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.trace-report__resources li {
  margin-bottom: 6px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.res-topic {
  font-weight: 500;
}

.res-reason {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.trace-report__path-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color-warning) 12%, var(--alp-bg-surface));
  border: 1px solid color-mix(in srgb, var(--el-color-warning) 40%, var(--alp-color-border));
  font-size: 14px;
  font-weight: 600;
  color: var(--el-color-warning);
  animation: path-alert-pulse 1.5s ease-in-out 2;
}

.trace-report__path-alert strong {
  display: block;
  margin-bottom: 4px;
}

.trace-report__path-alert p {
  margin: 0;
  line-height: 1.6;
  color: var(--el-text-color-regular);
  font-weight: 400;
}

.trace-report__intervention {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color-primary) 10%, var(--alp-bg-surface));
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 35%, var(--alp-color-border));
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-color-primary);
}

@keyframes path-alert-pulse {
  0%, 100% { box-shadow: 0 0 0 0 transparent; }
  50% { box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-warning) 25%, transparent); }
}
</style>
