<script setup lang="ts">
import { computed } from 'vue'
import { Collection, Compass, Document, TrendCharts } from '@element-plus/icons-vue'
import type { OjTutoringPayload } from '@/types/codeTrace'

const props = defineProps<{
  tutoring: OjTutoringPayload | null | undefined
}>()

const hasTutoring = computed(() => Boolean(props.tutoring))

/** 兼容旧 API：profile_updated 仅镜像 persona_updated */
const personaUpdated = computed(
  () => props.tutoring?.persona_updated ?? props.tutoring?.profile_updated ?? false,
)
const memoryRecorded = computed(
  () => props.tutoring?.memory_recorded ?? !!props.tutoring?.memory_event_id,
)
const masteryUpdated = computed(() => props.tutoring?.mastery_updated ?? false)

const showLearningOutcome = computed(
  () =>
    memoryRecorded.value ||
    masteryUpdated.value ||
    personaUpdated.value ||
    !!props.tutoring?.persona_patch_summary ||
    !!props.tutoring?.mastery_update_summary,
)

const errorTagType = computed(() => {
  const p = props.tutoring?.error_pattern ?? ''
  if (p.includes('pointer') || p.includes('initialization') || p.includes('state_transition')) {
    return 'warning'
  }
  if (p.includes('time_complexity')) return 'danger'
  return 'info'
})

const resourceTypeLabel: Record<string, string> = {
  document: '概念文档',
  mindmap: '思维导图',
  exercises: '变式题单',
  code_case: '代码沙盒',
  trace_animation: 'Trace 动画',
  ppt: 'PPT 胶片',
  video_script: '短视频脚本',
  reading: '拓展阅读',
}
</script>

<template>
  <section v-if="hasTutoring && tutoring" class="oj-tutoring-section">
    <header class="oj-tutoring-head">
      <el-icon><Compass /></el-icon>
      <span>智能辅导 · Trace 闭环</span>
    </header>

    <div v-if="tutoring.matched_skill" class="tutoring-block">
      <div class="block-label">匹配技能卡</div>
      <div class="skill-card-brief">
        <el-tag type="primary" size="small">{{ tutoring.matched_skill.name }}</el-tag>
        <span class="skill-id">{{ tutoring.matched_skill.id }}</span>
        <p v-if="tutoring.matched_skill.description" class="skill-desc">
          {{ tutoring.matched_skill.description }}
        </p>
      </div>
    </div>

    <div class="tutoring-meta">
      <el-tag v-if="tutoring.error_pattern_label" :type="errorTagType" size="small">
        {{ tutoring.error_pattern_label }}
      </el-tag>
      <el-tag v-if="(tutoring.bug_step_index ?? 0) >= 0" size="small" type="danger">
        关键 Trace 步骤 · Step {{ (tutoring.bug_step_index ?? 0) + 1 }}
      </el-tag>
      <el-tag size="small" type="info">提示层级 L{{ tutoring.hint_level }}</el-tag>
    </div>

    <p v-if="tutoring.trace_summary" class="trace-summary">{{ tutoring.trace_summary }}</p>

    <div v-if="tutoring.layered_hints?.length" class="tutoring-block">
      <div class="block-label">分层提示</div>
      <ul class="hint-list">
        <li v-for="(hint, i) in tutoring.layered_hints" :key="i">{{ hint }}</li>
      </ul>
      <p class="hint-note">提示按层级递进，不会直接给出完整可提交答案。</p>
    </div>

    <div v-if="tutoring.recommended_resources?.length" class="tutoring-block">
      <div class="block-label">
        <el-icon><Document /></el-icon>
        推荐复习资源
      </div>
      <ul class="resource-list">
        <li v-for="(res, i) in tutoring.recommended_resources" :key="i">
          <el-tag size="small" effect="plain">
            {{ resourceTypeLabel[res.resource_type] ?? res.resource_type }}
          </el-tag>
          <span class="resource-topic">{{ res.topic }}</span>
          <span v-if="res.reason" class="resource-reason">{{ res.reason }}</span>
        </li>
      </ul>
    </div>

    <div v-if="showLearningOutcome" class="tutoring-block tutoring-block--profile">
      <div class="block-label">
        <el-icon><TrendCharts /></el-icon>
        学习闭环反馈
      </div>
      <el-alert
        v-if="memoryRecorded"
        type="info"
        :closable="false"
        show-icon
        title="已写入学习记忆"
        :description="
          tutoring.memory_event_id
            ? `StudentMemory #${tutoring.memory_event_id} · 错因与 Trace 摘要已入库`
            : '错因与 Trace 摘要已入库'
        "
        class="outcome-alert"
      />
      <el-alert
        v-if="masteryUpdated"
        type="warning"
        :closable="false"
        show-icon
        title="已更新掌握度评估"
        :description="tutoring.mastery_update_summary || 'MasteryAgent 已重算掌握度'"
        class="outcome-alert"
      />
      <el-alert
        v-if="personaUpdated"
        type="success"
        :closable="false"
        show-icon
        title="已更新学习画像"
        :description="tutoring.persona_patch_summary || '六维画像已随本次诊断更新'"
        class="outcome-alert"
      />
      <el-alert
        v-else-if="memoryRecorded && tutoring.persona_patch_warning"
        type="info"
        :closable="false"
        show-icon
        title="本次诊断未更新画像"
        :description="tutoring.persona_patch_warning"
        class="outcome-alert"
      />
      <p v-if="tutoring.path_adjustment_hint" class="path-hint">
        <el-icon><Collection /></el-icon>
        {{ tutoring.path_adjustment_hint }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.oj-tutoring-section {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 35%, var(--alp-color-border));
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--el-color-primary) 5%, var(--alp-bg-surface-muted)) 0%,
    var(--alp-bg-surface-muted) 100%
  );
}

.oj-tutoring-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 15px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.tutoring-block {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.tutoring-block--profile {
  margin-bottom: 0;
  border-color: color-mix(in srgb, var(--el-color-success) 30%, var(--alp-color-border));
}

.block-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.tutoring-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.trace-summary {
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--el-text-color-secondary);
}

.skill-card-brief {
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

.hint-list,
.resource-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}

.hint-note {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
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

.mastery-summary,
.path-hint {
  margin: 0 0 6px;
  font-size: 13px;
  line-height: 1.55;
}

.path-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  color: var(--el-color-warning);
}

.outcome-alert {
  margin-bottom: 8px;
}
</style>
