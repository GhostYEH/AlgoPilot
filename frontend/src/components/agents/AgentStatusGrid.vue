<script setup lang="ts">
import { computed } from 'vue'
import { RESOURCE_TYPE_META } from '@/api/orchestrator'

export type AgentTaskStatus = 'pending' | 'running' | 'verifying' | 'retrying' | 'safe_checking' | 'done' | 'needs_review' | 'failed' | 'fallback'

export interface AgentStatusItem {
  resource_type: string
  agent_name: string
  status: AgentTaskStatus
}

const props = withDefaults(
  defineProps<{
    resources: AgentStatusItem[]
    active?: boolean
  }>(),
  { active: false },
)

const STATUS_TAG_TYPE: Record<AgentTaskStatus, 'info' | 'primary' | 'warning' | 'success' | 'danger'> = {
  pending: 'info',
  running: 'primary',
  verifying: 'warning',
  retrying: 'warning',
  safe_checking: 'warning',
  done: 'success',
  needs_review: 'warning',
  failed: 'danger',
  fallback: 'warning',
}

const STATUS_LABEL: Record<AgentTaskStatus, string> = {
  pending: '等待中',
  running: '生成中',
  verifying: '校验中',
  retrying: '重试中',
  safe_checking: '安全审查',
  done: '已完成',
  needs_review: '待复核',
  failed: '失败',
  fallback: '降级',
}

const enriched = computed(() =>
  props.resources.map((r) => {
    const meta = RESOURCE_TYPE_META[r.resource_type]
    return {
      ...r,
      label: meta?.label ?? r.resource_type,
      color: meta?.color ?? 'var(--alp-color-muted)',
      tagType: STATUS_TAG_TYPE[r.status],
      statusLabel: STATUS_LABEL[r.status],
    }
  }),
)
</script>

<template>
  <div class="status-grid" :class="{ 'status-grid--live': active }">
    <div class="grid-header">
      <span class="grid-title">Agent 资源状态</span>
      <span v-if="active" class="live-indicator">● LIVE</span>
    </div>
    <div class="grid-cards">
      <div
        v-for="item in enriched"
        :key="item.resource_type"
        class="agent-card"
        :class="[`agent-card--${item.status}`]"
      >
        <div class="card-icon" :style="{ color: item.color, borderColor: item.color }">
          {{ item.label.charAt(0) }}
        </div>
        <div class="card-body">
          <span class="card-agent">{{ item.agent_name }}</span>
          <span class="card-type">{{ item.label }}</span>
        </div>
        <div class="card-status">
          <el-tag :type="item.tagType" size="small" :class="{ 'tag--pulse': item.status === 'running' }">
            {{ item.statusLabel }}
          </el-tag>
          <span v-if="item.status === 'retrying'" class="retry-hint">重试中…</span>
          <span v-if="item.status === 'fallback'" class="fallback-hint">模板降级</span>
          <span v-if="item.status === 'needs_review'" class="fallback-hint">内容未发布</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.status-grid {
  --grid-bg: var(--alp-bg-code-ish);
  --grid-border: color-mix(in srgb, var(--alp-color-primary) 30%, #1e293b);
  --grid-glow: color-mix(in srgb, var(--alp-color-primary) 20%, transparent);
  --grid-text: var(--alp-color-text-secondary);
  --grid-muted: var(--alp-color-muted);
  --grid-accent: var(--alp-color-primary);

  border-radius: 16px;
  border: 1px solid var(--grid-border);
  background: var(--grid-bg);
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--alp-color-primary) 6%, transparent),
    0 12px 32px color-mix(in srgb, #000 40%, transparent),
    inset 0 1px 0 color-mix(in srgb, #fff 5%, transparent);
  overflow: hidden;
  padding: 16px;
}

.status-grid--live {
  animation: grid-pulse 2.4s ease-in-out infinite;
}

@keyframes grid-pulse {
  0%, 100% {
    box-shadow:
      0 0 0 1px color-mix(in srgb, var(--alp-color-primary) 10%, transparent),
      0 12px 32px color-mix(in srgb, #000 40%, transparent),
      0 0 32px color-mix(in srgb, var(--alp-color-primary) 6%, transparent);
  }
  50% {
    box-shadow:
      0 0 0 1px color-mix(in srgb, var(--alp-color-primary) 18%, transparent),
      0 12px 32px color-mix(in srgb, #000 40%, transparent),
      0 0 48px color-mix(in srgb, var(--alp-color-accent) 10%, transparent);
  }
}

.grid-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid color-mix(in srgb, #fff 8%, transparent);
}

.grid-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--grid-accent);
  letter-spacing: 0.04em;
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
}

.live-indicator {
  font-size: 10px;
  color: var(--alp-color-success);
  animation: blink 1.4s step-end infinite;
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
}

@keyframes blink {
  50% { opacity: 0.4; }
}

.grid-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

@media (max-width: 768px) {
  .grid-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

.agent-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 10px 12px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, #fff 8%, transparent);
  background: color-mix(in srgb, #fff 3%, transparent);
  transition: border-color 0.3s, box-shadow 0.3s;
  text-align: center;
}

.agent-card:hover {
  border-color: color-mix(in srgb, var(--grid-accent) 35%, transparent);
  box-shadow: 0 0 16px color-mix(in srgb, var(--grid-accent) 12%, transparent);
}

.agent-card--running {
  border-color: color-mix(in srgb, var(--alp-color-primary) 40%, transparent);
  box-shadow: 0 0 20px color-mix(in srgb, var(--alp-color-primary) 14%, transparent);
  animation: card-pulse 1.8s ease-in-out infinite;
}

@keyframes card-pulse {
  0%, 100% { box-shadow: 0 0 12px color-mix(in srgb, var(--alp-color-primary) 10%, transparent); }
  50% { box-shadow: 0 0 28px color-mix(in srgb, var(--alp-color-primary) 22%, transparent); }
}

.agent-card--done {
  border-color: color-mix(in srgb, #6aa878 30%, transparent);
}

.agent-card--failed {
  border-color: color-mix(in srgb, var(--alp-color-danger) 35%, transparent);
  box-shadow: 0 0 12px color-mix(in srgb, #f87171 10%, transparent);
}

.agent-card--fallback {
  border-color: color-mix(in srgb, var(--alp-color-warning) 30%, transparent);
}

.card-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1.5px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
  background: color-mix(in srgb, currentColor 10%, transparent);
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.card-agent {
  font-size: 11px;
  font-weight: 600;
  color: var(--grid-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
}

.card-type {
  font-size: 10px;
  color: var(--grid-muted);
}

.card-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.tag--pulse {
  animation: tag-pulse 1.2s ease-in-out infinite;
}

@keyframes tag-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.retry-hint,
.fallback-hint {
  font-size: 9px;
  color: var(--alp-color-warning);
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
}
</style>
