<script setup lang="ts">
import { computed } from 'vue'
import {
  Compass,
  Collection,
  TrendCharts,
  Document,
  User,
  MagicStick,
  Cpu,
} from '@element-plus/icons-vue'
import type { OjTutoringPayload } from '@/types/codeTrace'
import type { OjStruggleEvaluationResult } from '@/api/orchestrator'

const props = defineProps<{
  tutoring?: OjTutoringPayload | null
  struggle?: OjStruggleEvaluationResult | null
  problemSlug?: string
  consecutiveFailures?: number
  verdict?: string
}>()

const VERDICT_LABEL: Record<string, string> = {
  WA: '答案错误',
  RE: '运行错误',
  TLE: '超时',
  CE: '编译错误',
  AC: '通过',
}

const VERDICT_TAG_TYPE: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
  WA: 'warning',
  RE: 'danger',
  TLE: 'danger',
  CE: 'danger',
  AC: 'success',
}

const verdictLabel = computed(() => VERDICT_LABEL[props.verdict ?? ''] ?? props.verdict ?? '')
const verdictTagType = computed(() => VERDICT_TAG_TYPE[props.verdict ?? ''] ?? 'info')

const errorPattern = computed(
  () => props.tutoring?.error_pattern || props.struggle?.error_pattern || '',
)
const errorPatternLabel = computed(
  () =>
    props.tutoring?.error_pattern_label || props.struggle?.error_pattern_label || '',
)
const matchedSkill = computed(
  () => props.tutoring?.matched_skill || props.struggle?.matched_skill || null,
)
const bugStepIndex = computed(() => props.tutoring?.bug_step_index)
const memoryRecorded = computed(
  () => props.tutoring?.memory_recorded ?? props.struggle?.memory_recorded ?? false,
)
const memoryEventId = computed(
  () => props.tutoring?.memory_event_id ?? props.struggle?.memory_event_id ?? null,
)
const masteryUpdated = computed(
  () => props.tutoring?.mastery_updated ?? props.struggle?.mastery_updated ?? false,
)
const masteryUpdateSummary = computed(
  () => props.tutoring?.mastery_update_summary || props.struggle?.mastery_update_summary || '',
)
const personaUpdated = computed(() => props.tutoring?.persona_updated ?? false)
const personaPatchSummary = computed(() => props.tutoring?.persona_patch_summary || '')
const pathAdjustment = computed(
  () =>
    props.tutoring?.path_adjustment_hint ||
    props.struggle?.path_adjustment_suggestion ||
    '',
)
const recommendedResources = computed(
  () => props.tutoring?.recommended_resources || props.struggle?.recommended_resources || [],
)
const consecutiveFailures = computed(
  () => props.consecutiveFailures ?? props.struggle?.consecutive_failures ?? 0,
)
const chapterId = computed(
  () => props.tutoring?.chapter_id || props.struggle?.chapter_id || '',
)
const skillId = computed(() => props.tutoring?.skill_id || '')

const hasAnyIntervention = computed(
  () =>
    memoryRecorded.value ||
    masteryUpdated.value ||
    personaUpdated.value ||
    !!matchedSkill.value ||
    !!errorPattern.value ||
    !!pathAdjustment.value ||
    (bugStepIndex.value ?? -1) >= 0 ||
    recommendedResources.value.length > 0,
)

const RESOURCE_TYPE_LABEL: Record<string, string> = {
  document: '概念文档',
  mindmap: '思维导图',
  exercises: '变式题单',
  code_case: '代码沙盒',
  trace_animation: 'Trace 动画',
  reading: '拓展阅读',
}

interface ChainNode {
  name: string
  status: 'done' | 'not_triggered'
  detail: string
}

const agentChain = computed<ChainNode[]>(() => [
  {
    name: 'OjDiagnosisAgent',
    status: errorPattern.value ? 'done' : 'not_triggered',
    detail: errorPattern.value
      ? `${errorPatternLabel.value || errorPattern.value}${(bugStepIndex.value ?? -1) >= 0 ? ` · Trace Step ${bugStepIndex.value! + 1}` : ''}`
      : '未触发',
  },
  {
    name: 'SkillRouter',
    status: matchedSkill.value ? 'done' : 'not_triggered',
    detail: matchedSkill.value
      ? `${matchedSkill.value.name}（${matchedSkill.value.id}）`
      : '未触发',
  },
  {
    name: 'MemoryAgent',
    status: memoryRecorded.value ? 'done' : 'not_triggered',
    detail: memoryRecorded.value
      ? memoryEventId.value
        ? `StudentMemory #${memoryEventId.value} 已写入`
        : '错因摘要已入库'
      : '未触发',
  },
  {
    name: 'MasteryAgent',
    status: masteryUpdated.value ? 'done' : 'not_triggered',
    detail: masteryUpdated.value
      ? masteryUpdateSummary.value || '掌握度已重算'
      : '未触发',
  },
  {
    name: 'LearningPathAgent',
    status: pathAdjustment.value ? 'done' : 'not_triggered',
    detail: pathAdjustment.value || '未触发',
  },
])

const doneCount = computed(() => agentChain.value.filter((n) => n.status === 'done').length)
</script>

<template>
  <section v-if="hasAnyIntervention" class="intervention-receipt">
    <header class="receipt-head">
      <el-icon><Cpu /></el-icon>
      <span>AI 干预回执卡</span>
      <el-tag size="small" type="success" effect="plain">
        {{ doneCount }}/{{ agentChain.length }} 智能体已响应
      </el-tag>
    </header>

    <div class="receipt-trigger">
      <span class="trigger-label">干预触发</span>
      <div class="trigger-tags">
        <el-tag
          v-if="verdict"
          size="small"
          :type="verdictTagType"
        >
          {{ verdictLabel }}
        </el-tag>
        <el-tag
          v-if="consecutiveFailures >= 2"
          size="small"
          type="danger"
          effect="plain"
        >
          连续 {{ consecutiveFailures }} 次未通过
        </el-tag>
        <el-tag v-if="problemSlug" size="small" effect="plain" type="info">
          {{ problemSlug }}
        </el-tag>
        <el-tag v-if="chapterId" size="small" effect="plain">
          {{ chapterId }}
        </el-tag>
        <el-tag v-if="skillId" size="small" effect="plain">
          {{ skillId }}
        </el-tag>
      </div>
    </div>

    <div class="receipt-chain">
      <div class="chain-label">智能体链路</div>
      <el-timeline>
        <el-timeline-item
          v-for="(node, i) in agentChain"
          :key="i"
          :type="node.status === 'done' ? 'success' : 'info'"
          :hollow="node.status !== 'done'"
          :timestamp="node.name"
          placement="top"
        >
          <span
            class="chain-detail"
            :class="{ 'chain-detail--muted': node.status !== 'done' }"
          >
            {{ node.detail }}
          </span>
        </el-timeline-item>
      </el-timeline>
    </div>

    <div v-if="matchedSkill" class="receipt-block">
      <div class="block-label">
        <el-icon><Compass /></el-icon>
        命中 SkillCard
      </div>
      <div class="skill-brief">
        <el-tag type="primary" size="small">{{ matchedSkill.name }}</el-tag>
        <span class="skill-id">{{ matchedSkill.id }}</span>
        <p v-if="matchedSkill.description" class="skill-desc">{{ matchedSkill.description }}</p>
      </div>
    </div>

    <div class="receipt-meta">
      <el-tag v-if="errorPatternLabel || errorPattern" type="warning" size="small">
        错因：{{ errorPatternLabel || errorPattern }}
      </el-tag>
      <el-tag v-if="(bugStepIndex ?? -1) >= 0" type="danger" size="small">
        Trace Step {{ bugStepIndex! + 1 }}
      </el-tag>
    </div>

    <div class="receipt-outcomes">
      <el-tag
        :type="memoryRecorded ? 'success' : 'info'"
        size="small"
        effect="plain"
      >
        <el-icon><Collection /></el-icon>
        StudentMemory {{ memoryRecorded ? '已写入' : '未触发' }}
      </el-tag>
      <el-tag
        :type="masteryUpdated ? 'warning' : 'info'"
        size="small"
        effect="plain"
      >
        <el-icon><TrendCharts /></el-icon>
        Mastery {{ masteryUpdated ? '已更新' : '未触发' }}
      </el-tag>
      <el-tag
        :type="personaUpdated ? 'success' : 'info'"
        size="small"
        effect="plain"
      >
        <el-icon><User /></el-icon>
        Persona {{ personaUpdated ? '已更新' : '未触发' }}
      </el-tag>
    </div>

    <p v-if="masteryUpdated && masteryUpdateSummary" class="receipt-summary">
      <el-icon><TrendCharts /></el-icon>
      {{ masteryUpdateSummary }}
    </p>
    <p v-if="personaUpdated && personaPatchSummary" class="receipt-summary">
      <el-icon><User /></el-icon>
      {{ personaPatchSummary }}
    </p>

    <p v-if="pathAdjustment" class="receipt-path">
      <el-icon><MagicStick /></el-icon>
      {{ pathAdjustment }}
    </p>

    <div v-if="recommendedResources.length" class="receipt-block">
      <div class="block-label">
        <el-icon><Document /></el-icon>
        推荐资源
      </div>
      <ul class="resource-list">
        <li v-for="(res, i) in recommendedResources" :key="i">
          <el-tag size="small" effect="plain">
            {{ RESOURCE_TYPE_LABEL[res.resource_type] ?? res.resource_type }}
          </el-tag>
          <span class="resource-topic">{{ res.topic }}</span>
          <span v-if="res.reason" class="resource-reason">{{ res.reason }}</span>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.intervention-receipt {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  border: 1px solid color-mix(in srgb, var(--el-color-success) 35%, var(--alp-color-border));
  background: color-mix(in srgb, var(--el-color-success) 5%, var(--alp-bg-surface-muted));
}

.receipt-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 700;
  color: var(--el-color-success);
}

.receipt-trigger {
  margin-bottom: 12px;
}

.trigger-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 6px;
}

.trigger-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.receipt-chain {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.chain-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.receipt-chain :deep(.el-timeline) {
  padding-left: 0;
}

.receipt-chain :deep(.el-timeline-item__wrapper) {
  padding-left: 18px;
}

.receipt-chain :deep(.el-timeline-item__timestamp) {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.chain-detail {
  font-size: 12px;
  line-height: 1.55;
  color: var(--el-text-color-regular);
}

.chain-detail--muted {
  color: var(--el-text-color-placeholder);
}

.receipt-block {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.block-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.skill-brief {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skill-id {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  font-family: ui-monospace, Consolas, monospace;
}

.skill-desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.receipt-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.receipt-outcomes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.receipt-summary,
.receipt-path {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 0 0 8px;
  font-size: 12px;
  line-height: 1.55;
  color: var(--el-text-color-secondary);
}

.receipt-path {
  color: var(--el-color-warning);
}

.resource-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}

.resource-list li {
  margin-bottom: 6px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.resource-topic {
  font-weight: 500;
}

.resource-reason {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
