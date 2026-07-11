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

/** 阶段进度：已完成 / 总数 */
function phaseProgress(phase: { agents: FlowAgent[] }): { done: number; total: number } {
  const total = phase.agents.length
  const done = phase.agents.filter(
    (a) => {
      const s = statusFor(a.id)
      return s === 'success' || s === 'skipped'
    },
  ).length
  return { done, total }
}

/** 阶段整体状态：用于高亮当前活跃阶段 */
function phaseStatus(phase: { agents: FlowAgent[] }): AgentWorkflowStatus {
  const statuses = phase.agents.map((a) => statusFor(a.id))
  if (statuses.every((s) => s === 'waiting')) return 'waiting'
  if (statuses.some((s) => s === 'running' || s === 'retry')) return 'running'
  if (statuses.some((s) => s === 'failed')) return 'failed'
  if (statuses.every((s) => s === 'success' || s === 'skipped')) return 'success'
  return 'waiting'
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
      title="尚未收到 SSE 事件，流程图以 waiting 状态降级展示。点击上方「启动个性化资源生成」按钮后，将实时更新各 Agent 状态。"
    />

    <div class="phase-track">
      <section
        v-for="(phase, phaseIndex) in phases"
        :key="phase.label"
        class="phase-column"
        :class="[`phase-status-${phaseStatus(phase)}`]"
      >
        <div class="phase-head">
          <div class="phase-index">{{ phaseIndex + 1 }}</div>
          <div class="phase-meta">
            <strong>{{ phase.label }}</strong>
            <span class="phase-progress">{{ phaseProgress(phase).done }}/{{ phaseProgress(phase).total }}</span>
          </div>
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
            <span class="node-status-icon">
              <span class="status-glyph" />
            </span>
            <span class="node-copy">
              <strong>{{ agent.label }}</strong>
              <small>{{ agent.role }}</small>
            </span>
            <span class="status-badge">{{ statusLabels[statusFor(agent.id)] }}</span>
          </button>
        </div>

        <!-- 阶段间连接器 -->
        <span v-if="phaseIndex < phases.length - 1" class="phase-connector" aria-hidden="true">
          <span class="connector-line" />
          <span class="connector-arrow" />
        </span>
      </section>
    </div>

    <el-card shadow="never" class="agent-detail">
      <template #header>
        <div class="detail-head">
          <div class="detail-title">
            <span class="detail-role">{{ selectedAgent.role }}</span>
            <strong>{{ selectedAgent.label }}</strong>
          </div>
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
          <p>{{ selectedEvent?.input_summary || (hasSseEvents ? '等待 Agent 接收任务' : '系统就绪，等待启动资源生成') }}</p>
        </div>
        <div>
          <span>输出摘要</span>
          <p>{{ selectedEvent?.output_summary || selectedEvent?.message || (hasSseEvents ? '暂无输出' : '启动后将实时展示生成结果') }}</p>
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
  padding: 22px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-lg);
  background: var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
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
  letter-spacing: 0.02em;
}

.flow-header p {
  margin: 7px 0 0;
  color: var(--alp-color-muted);
  font-size: 13px;
}

.flow-fallback {
  margin-top: 14px;
}

/* ── 阶段轨道 ── */
.phase-track {
  display: grid;
  grid-template-columns: 1fr 0.72fr 2.2fr 1.2fr 0.8fr;
  gap: 28px;
  margin-top: 20px;
  overflow-x: auto;
  padding: 6px 4px 14px;
}

.phase-column {
  position: relative;
  min-width: 158px;
  padding: 12px 10px 14px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-lg);
  background: var(--alp-bg-soft-block);
  transition: border-color var(--alp-transition-fast), background var(--alp-transition-fast);
}

/* 阶段顶部彩条 */
.phase-column::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 14px;
  right: 14px;
  height: 2px;
  border-radius: 2px;
  background: color-mix(in srgb, var(--alp-color-muted) 40%, transparent);
  transition: background var(--alp-transition-fast);
}

/* 活跃阶段高亮 */
.phase-column.phase-status-running {
  border-color: color-mix(in srgb, var(--alp-color-primary) 45%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-primary-soft) 60%, var(--alp-bg-soft-block));
}

.phase-column.phase-status-running::before {
  background: var(--alp-color-primary);
  box-shadow: 0 0 10px var(--alp-color-primary-glow);
}

.phase-column.phase-status-success {
  border-color: color-mix(in srgb, var(--alp-color-success) 35%, var(--alp-color-border));
}

.phase-column.phase-status-success::before {
  background: var(--alp-color-success);
}

.phase-column.phase-status-failed::before {
  background: var(--alp-color-danger);
}

/* ── 阶段头部 ── */
.phase-head {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
}

.phase-index {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border-radius: 50%;
  background: var(--alp-color-primary-soft);
  color: var(--alp-color-primary);
  font-size: 12px;
  font-weight: 700;
}

.phase-meta {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.phase-meta strong {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--alp-color-text-secondary);
}

.phase-progress {
  color: var(--alp-color-muted);
  font-size: 10px;
  font-variant-numeric: tabular-nums;
}

/* ── 阶段间连接器 ── */
.phase-connector {
  position: absolute;
  top: 22px;
  right: -23px;
  display: flex;
  align-items: center;
  width: 18px;
  height: 16px;
  pointer-events: none;
}

.connector-line {
  flex: 1;
  height: 2px;
  background: linear-gradient(
    to right,
    color-mix(in srgb, var(--alp-color-primary) 50%, transparent),
    color-mix(in srgb, var(--alp-color-primary) 20%, transparent)
  );
}

.connector-arrow {
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 7px solid color-mix(in srgb, var(--alp-color-primary) 55%, transparent);
}

/* 活跃阶段向右流出时，连接线动画 */
.phase-column.phase-status-running .connector-line {
  background: linear-gradient(
    to right,
    var(--alp-color-primary),
    color-mix(in srgb, var(--alp-color-primary) 30%, transparent)
  );
  background-size: 6px 100%;
  animation: flow-dash 0.9s linear infinite;
}

@keyframes flow-dash {
  to {
    background-position: 12px 0;
  }
}

/* ── Agent 节点 ── */
.phase-agents {
  display: grid;
  gap: 9px;
}

.agent-node {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 60px;
  padding: 10px 11px;
  border: 1px solid var(--alp-color-border);
  border-left: 3px solid var(--alp-color-muted);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  color: var(--alp-color-text);
  text-align: left;
  cursor: pointer;
  transition:
    transform var(--alp-transition-fast),
    border-color var(--alp-transition-fast),
    box-shadow var(--alp-transition-fast);
}

.agent-node:hover,
.agent-node.selected {
  border-color: var(--alp-color-primary);
  box-shadow: var(--alp-shadow-glow);
  transform: translateY(-1px);
}

.agent-node.selected {
  border-left-width: 3px;
}

/* 状态图标容器 */
.node-status-icon {
  display: grid;
  width: 16px;
  height: 16px;
  place-items: center;
  border-radius: 50%;
  background: color-mix(in srgb, var(--alp-color-muted) 20%, transparent);
  transition: background var(--alp-transition-fast);
}

.status-glyph {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--alp-color-muted);
  transition: background var(--alp-transition-fast), transform var(--alp-transition-fast);
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
  white-space: nowrap;
}

.node-copy small {
  margin-top: 3px;
  color: var(--alp-color-muted);
  font-size: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-badge {
  padding: 2px 6px;
  border-radius: var(--alp-radius-pill);
  background: color-mix(in srgb, var(--alp-color-muted) 16%, transparent);
  color: var(--alp-color-muted);
  font-size: 9px;
  font-weight: 600;
  white-space: nowrap;
  transition: background var(--alp-transition-fast), color var(--alp-transition-fast);
}

/* ── 各状态样式 ── */
.status-waiting {
  border-left-color: var(--alp-color-muted);
}

.status-running {
  border-left-color: var(--alp-color-primary);
}
.status-running .node-status-icon {
  background: var(--alp-color-primary-soft);
}
.status-running .status-glyph {
  background: var(--alp-color-primary);
  animation: node-pulse 1s infinite;
  box-shadow: 0 0 8px var(--alp-color-primary-glow);
}
.status-running .status-badge {
  background: var(--alp-color-primary-soft);
  color: var(--alp-color-primary);
}

.status-success {
  border-left-color: var(--alp-color-success);
}
.status-success .node-status-icon {
  background: color-mix(in srgb, var(--alp-color-success) 18%, transparent);
}
.status-success .status-glyph {
  background: var(--alp-color-success);
}
.status-success .status-badge {
  background: color-mix(in srgb, var(--alp-color-success) 16%, transparent);
  color: var(--alp-color-success);
}

.status-retry {
  border-left-color: var(--alp-color-warning);
}
.status-retry .node-status-icon {
  background: var(--alp-color-accent-soft);
}
.status-retry .status-glyph {
  background: var(--alp-color-warning);
  animation: node-pulse 0.8s infinite;
}
.status-retry .status-badge {
  background: var(--alp-color-accent-soft);
  color: var(--alp-color-warning);
}

.status-failed {
  border-left-color: var(--alp-color-danger);
}
.status-failed .node-status-icon {
  background: color-mix(in srgb, var(--alp-color-danger) 18%, transparent);
}
.status-failed .status-glyph {
  background: var(--alp-color-danger);
}
.status-failed .status-badge {
  background: color-mix(in srgb, var(--alp-color-danger) 16%, transparent);
  color: var(--alp-color-danger);
}

.status-skipped {
  border-left-color: var(--alp-color-muted);
}
.status-skipped .node-status-icon {
  background: color-mix(in srgb, var(--alp-color-muted) 12%, transparent);
}
.status-skipped .status-glyph {
  background: var(--alp-color-muted);
}
.status-skipped .status-badge {
  background: color-mix(in srgb, var(--alp-color-muted) 14%, transparent);
  color: var(--alp-color-muted);
}

@keyframes node-pulse {
  50% {
    opacity: 0.4;
    transform: scale(1.4);
  }
}

/* ── 详情面板 ── */
.agent-detail {
  margin-top: 12px;
}

.detail-head {
  gap: 12px;
}

.detail-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-role {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.detail-title strong {
  font-size: 14px;
}

.detail-tag {
  border: 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.detail-grid > div {
  padding: 10px 12px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
}

.detail-grid span {
  color: var(--alp-color-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.detail-grid p {
  margin: 6px 0 0;
  overflow-wrap: anywhere;
  font-size: 12px;
  line-height: 1.55;
  color: var(--alp-color-text-secondary);
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
