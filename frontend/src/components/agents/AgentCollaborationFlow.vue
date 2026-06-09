<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type {
  AgentWorkflowEvent,
  AgentWorkflowStatus,
} from '@/api/orchestrator'

const props = withDefaults(
  defineProps<{
    events: AgentWorkflowEvent[]
    active?: boolean
  }>(),
  { active: false },
)

interface FlowAgent {
  id: string
  label: string
  role: string
}

const phases: Array<{ label: string; agents: FlowAgent[] }> = [
  {
    label: '学习上下文',
    agents: [
      { id: 'ProfilingAgent', label: 'ProfilingAgent', role: '六维学习画像' },
      { id: 'LearningPathAgent', label: 'LearningPathAgent', role: '学习路径上下文' },
    ],
  },
  {
    label: '知识检索',
    agents: [
      { id: 'KnowledgeRetriever', label: 'KnowledgeRetriever', role: '课程知识库检索' },
    ],
  },
  {
    label: '并行资源生成',
    agents: [
      { id: 'ConceptAgent', label: 'ConceptAgent', role: '概念讲解' },
      { id: 'GraphAgent', label: 'GraphAgent', role: '知识图谱' },
      { id: 'QuizAgent', label: 'QuizAgent', role: '个性化练习' },
      { id: 'ScenarioAgent', label: 'ScenarioAgent', role: '场景沙箱' },
      { id: 'TraceAgent', label: 'TraceAgent', role: '执行轨迹' },
      { id: 'PptAgent', label: 'PptAgent', role: '演示文稿' },
      { id: 'VideoScriptAgent', label: 'VideoScriptAgent', role: '视频脚本' },
      { id: 'ReadingAgent', label: 'ReadingAgent', role: '分层阅读' },
    ],
  },
  {
    label: '校验回流',
    agents: [
      { id: 'ContentVerifierAgent', label: 'ContentVerifierAgent', role: '事实与依据校验' },
      { id: 'SafetyAgent', label: 'SafetyAgent', role: '安全审查' },
    ],
  },
  {
    label: '效果评估',
    agents: [
      { id: 'EvaluationAgent', label: 'EvaluationAgent', role: '批次质量评估' },
    ],
  },
]

const allAgents = phases.flatMap((phase) => phase.agents)
const selectedId = ref('ProfilingAgent')

const latestByAgent = computed(() => {
  const result = new Map<string, AgentWorkflowEvent>()
  for (const event of props.events) {
    if (!event.agent_name) continue
    const previous = result.get(event.agent_name)
    if (
      previous?.status === 'success' &&
      event.status === 'skipped' &&
      event.agent_name === 'ContentVerifierAgent'
    ) {
      continue
    }
    result.set(event.agent_name, event)
  }
  return result
})

watch(
  () => props.events.length,
  () => {
    let running: AgentWorkflowEvent | undefined
    for (let index = props.events.length - 1; index >= 0; index -= 1) {
      const event = props.events[index]
      if (event.status === 'running' || event.status === 'retry') {
        running = event
        break
      }
    }
    if (running && allAgents.some((agent) => agent.id === running.agent_name)) {
      selectedId.value = running.agent_name
    }
  },
)

const selectedAgent = computed(
  () => allAgents.find((agent) => agent.id === selectedId.value) ?? allAgents[0],
)
const selectedEvent = computed(() => latestByAgent.value.get(selectedId.value))
const hasSseEvents = computed(() => props.events.length > 0)

const statusLabels: Record<AgentWorkflowStatus, string> = {
  waiting: '等待',
  running: '运行中',
  success: '成功',
  retry: '重试',
  failed: '失败',
  skipped: '跳过',
}

function statusFor(agentId: string): AgentWorkflowStatus {
  return latestByAgent.value.get(agentId)?.status ?? 'waiting'
}

function validationText(event?: AgentWorkflowEvent): string {
  if (!event?.validation_result) return '暂无校验结果'
  return Object.entries(event.validation_result)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join('；')
}

function durationText(duration?: number | null): string {
  if (duration == null) return '未记录'
  if (duration < 1000) return `${duration} ms`
  return `${(duration / 1000).toFixed(2)} s`
}
</script>

<template>
  <section class="collaboration-flow">
    <header class="flow-header">
      <div>
        <h2>智能体协作流程图</h2>
        <p>系统采用可观测多智能体编排机制，每个资源生成过程均可追踪、可校验、可回滚。</p>
      </div>
      <el-tag :type="active ? 'primary' : hasSseEvents ? 'success' : 'info'" effect="plain">
        {{ active ? 'SSE 实时流' : hasSseEvents ? '本次流程已结束' : '等待事件' }}
      </el-tag>
    </header>

    <el-alert
      v-if="!hasSseEvents"
      class="flow-fallback"
      type="info"
      :closable="false"
      show-icon
      title="尚未收到 SSE 事件，流程图以 waiting 状态降级展示。启动一次资源生成后将实时更新。"
    />

    <div class="phase-track">
      <section v-for="(phase, phaseIndex) in phases" :key="phase.label" class="phase-column">
        <div class="phase-title">
          <span>{{ phaseIndex + 1 }}</span>
          {{ phase.label }}
        </div>
        <div class="phase-agents">
          <button
            v-for="agent in phase.agents"
            :key="agent.id"
            type="button"
            class="agent-node"
            :class="[
              `status-${statusFor(agent.id)}`,
              { selected: selectedId === agent.id },
            ]"
            @click="selectedId = agent.id"
          >
            <span class="node-status-dot" />
            <span class="node-copy">
              <strong>{{ agent.label }}</strong>
              <small>{{ agent.role }}</small>
            </span>
            <span class="status-badge">{{ statusLabels[statusFor(agent.id)] }}</span>
          </button>
        </div>
      </section>
    </div>

    <el-card shadow="never" class="agent-detail">
      <template #header>
        <div class="detail-head">
          <strong>{{ selectedAgent.label }}</strong>
          <el-tag
            size="small"
            effect="dark"
            :class="`detail-tag status-${statusFor(selectedAgent.id)}`"
          >
            {{ statusLabels[statusFor(selectedAgent.id)] }}
          </el-tag>
        </div>
      </template>
      <div class="detail-grid">
        <div>
          <span>输入摘要</span>
          <p>{{ selectedEvent?.input_summary || '等待 Agent 接收任务' }}</p>
        </div>
        <div>
          <span>输出摘要</span>
          <p>{{ selectedEvent?.output_summary || selectedEvent?.message || '暂无输出' }}</p>
        </div>
        <div>
          <span>耗时</span>
          <p>{{ durationText(selectedEvent?.duration_ms) }}</p>
        </div>
        <div>
          <span>校验结果</span>
          <p>{{ validationText(selectedEvent) }}</p>
        </div>
        <div>
          <span>失败原因</span>
          <p>{{ selectedEvent?.failure_reason || '无' }}</p>
        </div>
        <div>
          <span>重试次数</span>
          <p>{{ selectedEvent?.retry_count ?? 0 }}</p>
        </div>
      </div>
    </el-card>
  </section>
</template>

<style scoped>
.collaboration-flow {
  margin-bottom: 24px;
  padding: 20px;
  border: 1px solid var(--alp-color-border);
  border-radius: 16px;
  background: var(--alp-bg-surface);
}

.flow-header,
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.flow-header h2 {
  margin: 0;
  font-size: 18px;
}

.flow-header p {
  margin: 7px 0 0;
  color: var(--alp-color-muted);
  font-size: 13px;
}

.flow-fallback {
  margin-top: 14px;
}

.phase-track {
  display: grid;
  grid-template-columns: 1fr 0.72fr 2.2fr 1.2fr 0.8fr;
  gap: 24px;
  margin-top: 18px;
  overflow-x: auto;
  padding: 4px 2px 12px;
}

.phase-column {
  position: relative;
  min-width: 150px;
}

.phase-column:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 31px;
  right: -20px;
  width: 16px;
  border-top: 2px solid color-mix(in srgb, var(--alp-color-primary) 45%, var(--alp-color-border));
}

.phase-column:not(:last-child)::before {
  content: '';
  position: absolute;
  top: 27px;
  right: -22px;
  border: 5px solid transparent;
  border-left-color: color-mix(in srgb, var(--alp-color-primary) 55%, var(--alp-color-border));
}

.phase-title {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 10px;
  color: var(--alp-color-muted);
  font-size: 12px;
  font-weight: 700;
}

.phase-title span {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: 50%;
  background: color-mix(in srgb, var(--alp-color-primary) 12%, transparent);
  color: var(--alp-color-primary);
}

.phase-agents {
  display: grid;
  gap: 8px;
}

.agent-node {
  display: grid;
  grid-template-columns: 9px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 58px;
  padding: 9px 10px;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-text);
  text-align: left;
  cursor: pointer;
  transition: 0.2s ease;
}

.agent-node:hover,
.agent-node.selected {
  border-color: var(--alp-color-primary);
  transform: translateY(-1px);
}

.node-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}

.node-copy {
  min-width: 0;
}

.node-copy strong,
.node-copy small {
  display: block;
}

.node-copy strong {
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
}

.node-copy small {
  margin-top: 3px;
  color: var(--alp-color-muted);
  font-size: 10px;
}

.status-badge {
  padding: 2px 5px;
  border-radius: 999px;
  background: color-mix(in srgb, #94a3b8 14%, transparent);
  color: #64748b;
  font-size: 9px;
  white-space: nowrap;
}

.status-running .node-status-dot {
  background: #3b82f6;
  animation: node-pulse 1s infinite;
}

.status-success .node-status-dot {
  background: #22c55e;
}

.status-retry .node-status-dot {
  background: #f59e0b;
  animation: node-pulse 0.8s infinite;
}

.status-failed .node-status-dot {
  background: #ef4444;
}

.status-skipped .node-status-dot {
  background: #64748b;
}

.status-running .status-badge {
  color: #2563eb;
}

.status-success .status-badge {
  color: #16a34a;
}

.status-retry .status-badge {
  color: #d97706;
}

.status-failed .status-badge {
  color: #dc2626;
}

@keyframes node-pulse {
  50% {
    opacity: 0.35;
    transform: scale(1.35);
  }
}

.agent-detail {
  margin-top: 8px;
}

.detail-tag {
  border: 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.detail-grid span {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.detail-grid p {
  margin: 5px 0 0;
  overflow-wrap: anywhere;
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 900px) {
  .phase-track {
    grid-template-columns: repeat(5, minmax(180px, 1fr));
  }

  .detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .flow-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
