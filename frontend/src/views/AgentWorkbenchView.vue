<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchAgentsCatalog,
  getStageDetail,
  streamGenerateAllResources,
  RESOURCE_TYPE_META,
  type AgentInfo,
  type AgentWorkflowEvent,
  type GeneratedResource,
} from '@/api/orchestrator'
import { isLoggedIn } from '@/stores/auth'
import AgentThinkingConsole from '@/components/agents/AgentThinkingConsole.vue'
import AgentCollaborationFlow from '@/components/agents/AgentCollaborationFlow.vue'
import AgentStatusGrid from '@/components/agents/AgentStatusGrid.vue'
import type { AgentTaskStatus } from '@/components/agents/AgentStatusGrid.vue'
import PersonalizedResourceDashboard from '@/components/agents/PersonalizedResourceDashboard.vue'
import type { AgentConsoleLine } from '@/utils/agentConsole'
import {
  lineFromCollaboration,
  lineFromProgress,
  lineFromWorkflow,
  lineFromAgentLog,
  resourceBootstrapLines,
  systemLine,
} from '@/utils/agentConsole'
import { ALGORITHM_MODULES, generationPresetForModule } from '@/constants/modules'

const router = useRouter()
const props = withDefaults(defineProps<{ embedded?: boolean }>(), { embedded: false })

const FALLBACK_AGENTS: AgentInfo[] = [
  {
    id: 'ProfilingAgent',
    display_name: 'ProfilingAgent',
    role: '提取并更新六维学习画像',
    layer: 'profile',
  },
  {
    id: 'LearningPathAgent',
    display_name: 'LearningPathAgent',
    role: '规划先修 DAG 与巩固节点',
    layer: 'planning',
  },
  {
    id: 'KnowledgeRetriever',
    display_name: 'KnowledgeRetriever',
    role: '检索课程知识库证据',
    layer: 'knowledge',
  },
  {
    id: 'ContentVerifierAgent',
    display_name: 'ContentVerifierAgent',
    role: '校验生成内容与知识证据的一致性',
    layer: 'verification',
  },
  {
    id: 'SafetyAgent',
    display_name: 'SafetyAgent',
    role: '执行内容安全审查',
    layer: 'safety',
  },
]

const FALLBACK_PIPELINE = [
  { stage: 'rag_retrieve', agent: 'KnowledgeRetriever', label: '课程知识检索' },
  { stage: 'agent_generate', agent: 'Role Agents', label: '个性化资源生成' },
  { stage: 'content_verify', agent: 'ContentVerifierAgent', label: '事实与引用校验' },
  { stage: 'safety_filter', agent: 'SafetyAgent', label: '安全审查' },
  { stage: 'persist', agent: 'Orchestrator', label: '资源落库' },
]

const agents = ref<AgentInfo[]>([])
const pipeline = ref<Array<{ stage: string; agent: string; label: string }>>([])
const note = ref('')
const dagMermaid = ref('')
const activeStage = ref(0)

const topic = ref('动态规划入门')
const focusHint = ref('主攻状态转移方程与边界')
const selectedModule = ref('dp')
const generating = ref(false)
const progress = ref(0)
const consoleLines = ref<AgentConsoleLine[]>([])
const generatedResources = ref<GeneratedResource[]>([])
const streamingContent = ref<Record<string, string>>({})
const streamingAttempts = new Map<string, number>()
const workflowEvents = ref<AgentWorkflowEvent[]>([])
const activeResourceTab = ref('document')
const agentStatuses = ref<Map<string, AgentTaskStatus>>(new Map())

function applyModulePreset(moduleKey: string) {
  const preset = generationPresetForModule(moduleKey)
  if (!preset) return
  topic.value = preset.topic
  focusHint.value = preset.focusHint
}

function resourceNeedsReview(resource: GeneratedResource): boolean {
  const verification = resource.verification ?? resource.meta?.verification
  const finalDecision =
    verification && typeof verification === 'object'
      ? (verification as Record<string, unknown>).final_decision
      : undefined
  return resource.meta?.status === 'draft' || finalDecision === 'draft' || finalDecision === 'blocked'
}

const stageDetail = computed(() => {
  const s = pipeline.value[activeStage.value]
  return s ? getStageDetail(s.stage) : null
})

const statusGridResources = computed(() =>
  Object.keys(RESOURCE_TYPE_META).map((rt) => ({
    resource_type: rt,
    agent_name: RESOURCE_TYPE_META[rt].agentName,
    status: agentStatuses.value.get(rt) ?? ('pending' as AgentTaskStatus),
  })),
)

const catalogError = ref(false)

onMounted(async () => {
  try {
    const r = await fetchAgentsCatalog()
    agents.value = r.agents
    pipeline.value = r.resource_pipeline
    note.value = r.framework_note
    dagMermaid.value = r.dag_mermaid ?? ''
  } catch {
    catalogError.value = true
    agents.value = [...FALLBACK_AGENTS]
    pipeline.value = [...FALLBACK_PIPELINE]
    note.value = '后端 catalog 暂不可用，已加载演示用 Pipeline 说明'
  }
})

function pushLine(line: AgentConsoleLine) {
  consoleLines.value = [...consoleLines.value, line]
}

function pushWorkflowEvent(event: AgentWorkflowEvent) {
  workflowEvents.value = [...workflowEvents.value, event]
}

function progressWorkflowEvent(p: {
  resource_type?: string
  agent_name?: string
  label?: string
  percent?: number
}): AgentWorkflowEvent {
  const agentName = p.agent_name || 'Orchestrator'
  const label = p.label || p.resource_type || '任务初始化'
  return {
    agent: agentName,
    detail: label,
    agent_id: agentName,
    agent_name: agentName,
    stage: 'agent_generate',
    status: 'running',
    message: label,
    timestamp: new Date().toISOString(),
    duration_ms: null,
    validation_result: null,
    retry_count: 0,
    input_summary: `${topic.value} | ${focusHint.value}`,
    output_summary: '',
    failure_reason: '',
    resource_type: p.resource_type,
    percent: p.percent,
  }
}

function markRunningDone(agent: string) {
  consoleLines.value = consoleLines.value.map((l) =>
    l.agent === agent && l.status === 'running' ? { ...l, status: 'done' as const } : l,
  )
}

async function runResourceGeneration() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后生成个性化资源')
    void router.push({ name: 'login', query: { redirect: '/agent-workbench' } })
    return
  }
  if (generating.value) return
  if (!topic.value.trim()) {
    ElMessage.warning('请填写与课程模块一致的课程主题')
    return
  }

  generating.value = true
  progress.value = 0
  consoleLines.value = [...resourceBootstrapLines(topic.value)]
  workflowEvents.value = []
  generatedResources.value = []
  streamingContent.value = {}
  streamingAttempts.clear()

  const statusMap = new Map<string, AgentTaskStatus>()
  for (const rt of Object.keys(RESOURCE_TYPE_META)) {
    statusMap.set(rt, 'pending')
  }
  agentStatuses.value = statusMap

  try {
    await streamGenerateAllResources(
      {
        topic: topic.value,
        module_key: selectedModule.value || undefined,
        focus_hint: focusHint.value,
      },
      {
        onProgress(p) {
          pushLine(lineFromProgress(p))
          pushWorkflowEvent(progressWorkflowEvent(p))
          if (typeof p.percent === 'number') progress.value = p.percent
          if (!p.resource_type) return
          activeResourceTab.value = p.resource_type
          statusMap.set(p.resource_type, 'running')
          agentStatuses.value = new Map(statusMap)
        },
        onWorkflow(w) {
          pushWorkflowEvent(w)
          if (w.status === 'success' || w.status === 'skipped') markRunningDone(w.agent)
          pushLine(lineFromWorkflow(w))
          if (typeof w.percent === 'number') progress.value = w.percent
          if (w.stage === 'content_verify' && w.status === 'running') {
            const rt = Object.entries(RESOURCE_TYPE_META).find(([, m]) => m.agentName === w.agent)?.[0]
            if (rt) { statusMap.set(rt, 'verifying'); agentStatuses.value = new Map(statusMap) }
          }
          if (w.stage === 'content_verify' && w.status === 'retry') {
            const rt = Object.entries(RESOURCE_TYPE_META).find(([, m]) => m.agentName === w.agent)?.[0]
            if (rt) { statusMap.set(rt, 'retrying'); agentStatuses.value = new Map(statusMap) }
          }
          if (w.stage === 'safety_filter' && w.status === 'running') {
            const rt = Object.entries(RESOURCE_TYPE_META).find(([, m]) => m.agentName === w.agent)?.[0]
            if (rt) { statusMap.set(rt, 'safe_checking'); agentStatuses.value = new Map(statusMap) }
          }
          if (w.stage === 'agent_generate' && w.status === 'success') {
            const rt = Object.entries(RESOURCE_TYPE_META).find(([, m]) => m.agentName === w.agent)?.[0]
            if (rt) { statusMap.set(rt, 'running'); agentStatuses.value = new Map(statusMap) }
          }
        },
        onCollaboration(log) {
          for (const row of log) pushLine(lineFromCollaboration(row))
        },
        onAgentLogs(logs) {
          for (const entry of logs) pushLine(lineFromAgentLog(entry))
        },
        onContentDelta(chunk) {
          const previousAttempt = streamingAttempts.get(chunk.resource_type)
          const previous = previousAttempt === chunk.attempt
            ? (streamingContent.value[chunk.resource_type] ?? '')
            : ''
          streamingAttempts.set(chunk.resource_type, chunk.attempt)
          streamingContent.value = {
            ...streamingContent.value,
            [chunk.resource_type]: `${previous}${chunk.delta}`,
          }
          // 仅在当前 tab 无对应流式内容时切换，避免并行生成时 tab 反复跳
          const activeTabHasStream = Boolean(streamingContent.value[activeResourceTab.value])
          if (!activeTabHasStream) activeResourceTab.value = chunk.resource_type
        },
        onRegenerateClear(info) {
          // 后端检测到上一轮输出未通过校验，清空已显示的流式内容，让新一轮 delta 从空开始追加
          const nextStreaming = { ...streamingContent.value }
          delete nextStreaming[info.resource_type]
          streamingContent.value = nextStreaming
          streamingAttempts.set(info.resource_type, info.attempt)
          statusMap.set(info.resource_type, 'retrying')
          agentStatuses.value = new Map(statusMap)
          activeResourceTab.value = info.resource_type
          pushLine(
            systemLine(
              `${info.agent_name} 上一轮输出未通过校验，正在重新生成（第 ${info.attempt} 次）：${info.reason}`,
              'warn',
            ),
          )
        },
        onResource(r) {
          generatedResources.value = [
            r,
            ...generatedResources.value.filter((x) => x.id !== r.id),
          ]
          activeResourceTab.value = r.resource_type
          const nextStreaming = { ...streamingContent.value }
          delete nextStreaming[r.resource_type]
          streamingContent.value = nextStreaming
          const needsReview = resourceNeedsReview(r)
          statusMap.set(r.resource_type, needsReview ? 'needs_review' : 'done')
          agentStatuses.value = new Map(statusMap)
          const roleAgent = RESOURCE_TYPE_META[r.resource_type]?.agentName ?? r.agent_name
          pushWorkflowEvent({
            agent: roleAgent,
            detail: r.title,
            agent_id: roleAgent,
            agent_name: roleAgent,
            stage: 'resource_ready',
            status: needsReview ? 'failed' : 'success',
            message: needsReview ? `${r.title} 已生成，等待内容复核` : `${r.title} 已发布`,
            timestamp: r.created_at || new Date().toISOString(),
            duration_ms: null,
            validation_result:
              r.verification && typeof r.verification === 'object'
                ? r.verification
                : ((r.meta?.verification as Record<string, unknown> | undefined) ?? null),
            retry_count: Number(
              (r.meta?.verification as Record<string, unknown> | undefined)?.retry_count ?? 0,
            ),
            input_summary: `${topic.value} | ${r.resource_type}`,
            output_summary: `${r.title} | ${r.content.length} chars`,
            failure_reason: needsReview ? '内容校验未通过，资源保留为草稿' : '',
            resource_type: r.resource_type,
          })
          pushLine(
            systemLine(
              `${r.agent_name} 已落库 · ${r.title.slice(0, 40)}`,
              'done',
            ),
          )
        },
        onDone(info) {
          progress.value = 100
          const reviewCount = [...statusMap.values()].filter((status) => status === 'needs_review').length
          if (info?.fallback_mode) {
            for (const [rt, s] of statusMap) {
              if (s !== 'done') statusMap.set(rt, 'fallback')
            }
            agentStatuses.value = new Map(statusMap)
            pushLine(
              systemLine(
                'TemplateFallbackAgent：无 LLM Key，已用课程知识库模板降级（非大模型生成）',
                'warn',
              ),
            )
            ElMessage.warning(
              '当前为无模型 Key 的模板降级资源，配置 AI 模型 API Key 后可生成更高质量内容。',
            )
          } else if (info?.partial_failure) {
            const failed = info.errors?.map((e) => e.agent_name ?? e.resource_type ?? '未知').join('、') ?? '部分资源'
            if (info.errors) {
              for (const e of info.errors) {
                if (e.resource_type) { statusMap.set(e.resource_type, 'failed') }
              }
              agentStatuses.value = new Map(statusMap)
            }
            pushLine(systemLine(`部分资源生成失败（${failed}），其余已装配完毕`, 'warn'))
            ElMessage.warning(`${failed} 生成失败，其余资源已就绪`)
          } else if (reviewCount) {
            pushLine(systemLine(`${reviewCount} 项资源待内容复核，其余资源已发布`, 'warn'))
            ElMessage.warning(`${reviewCount} 项资源未通过内容校验，已标记为待复核`)
          } else {
            pushLine(systemLine('个性化学习资源装配完毕！', 'success'))
            ElMessage.success('个性化学习资源已全部生成')
          }
        },
        onError(msg, resourceType) {
          if (resourceType) {
            const nextStreaming = { ...streamingContent.value }
            delete nextStreaming[resourceType]
            streamingContent.value = nextStreaming
            statusMap.set(resourceType, 'failed')
            agentStatuses.value = new Map(statusMap)
          } else {
            streamingContent.value = {}
          }
          pushLine(systemLine(msg || '生成管线异常终止', 'error'))
        },
      },
    )
  } finally {
    generating.value = false
  }
}

function selectStage(idx: number) {
  activeStage.value = idx
}

function agentStatus(id: string): 'running' | 'idle' {
  if (!generating.value) return 'idle'
  const running = consoleLines.value.some((l) => l.agent === id && l.status === 'running')
  return running ? 'running' : 'idle'
}
</script>

<template>
  <div class="workbench-page" :class="{ 'workbench-page--embedded': props.embedded }">
    <div class="wb-hero">
      <el-page-header v-if="!props.embedded" title="智能化学习" @back="router.push({ name: 'home' })" />
      <p class="wb-desc">{{ note || '结合学习画像与课程知识，协同生成并校验个性化学习资源' }}</p>
      <el-alert
        v-if="catalogError"
        type="warning"
        :closable="false"
        show-icon
        title="Agent 目录加载失败，已展示演示 Pipeline；登录后可生成资源（无 LLM Key 时为模板降级）"
        class="wb-catalog-alert"
      />
    </div>

    <section class="wb-generate">
      <el-row :gutter="12" align="middle">
        <el-col :xs="24" :md="6">
          <label class="field-label">课程模块</label>
          <el-select
            v-model="selectedModule"
            size="large"
            filterable
            placeholder="选择课程模块"
            style="width: 100%"
            @change="applyModulePreset"
          >
            <el-option
              v-for="item in ALGORITHM_MODULES"
              :key="item.key"
              :label="item.label"
              :value="item.key"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :md="7">
          <label class="field-label">课程主题</label>
          <el-input v-model="topic" size="large" placeholder="如：动态规划入门" />
        </el-col>
        <el-col :xs="24" :md="6">
          <label class="field-label">生成侧重</label>
          <el-input v-model="focusHint" size="large" placeholder="如：状态转移方程" />
        </el-col>
        <el-col :xs="24" :md="5">
          <el-button
            type="primary"
            size="large"
            class="gen-btn"
            :icon="MagicStick"
            :loading="generating"
            @click="runResourceGeneration"
          >
            启动个性化资源生成
          </el-button>
        </el-col>
      </el-row>
    </section>

    <AgentThinkingConsole
      :lines="consoleLines"
      :active="generating"
      :progress="progress"
      mode="resource"
      title="Agent Synergy Terminal"
      subtitle="Concept → Graph → Quiz → Scenario → Trace → Reading"
      class="wb-console"
    />

    <AgentCollaborationFlow
      :events="workflowEvents"
      :active="generating"
      class="wb-flow"
    />

    <AgentStatusGrid
      v-if="generating || agentStatuses.size > 0"
      :resources="statusGridResources"
      :active="generating"
      class="wb-status-grid"
    />

    <PersonalizedResourceDashboard
      v-if="generatedResources.length || generating"
      :resources="generatedResources"
      :streaming-content="streamingContent"
      v-model:active-tab="activeResourceTab"
      class="wb-dashboard"
    />

    <el-collapse v-else class="wb-collapse">
      <el-collapse-item title="架构说明 · DAG Pipeline" name="arch">
        <div class="dag-visual">
          <div class="dag-node">KnowledgeRetriever</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node accent">八类 Role Agents</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node warn">Verifier</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node">Safety → 落库</div>
        </div>
        <p v-if="dagMermaid" class="dag-note">系统编排结构已加载，生成时可在上方协作流程中查看实时状态。</p>

        <h3 class="section-title">Pipeline 阶段</h3>
        <el-steps :active="activeStage" finish-status="success" align-center class="pipeline-steps">
          <el-step
            v-for="(s, idx) in pipeline"
            :key="s.stage"
            :title="s.agent"
            :description="s.label"
            class="clickable-step"
            @click="selectStage(idx)"
          />
        </el-steps>
        <el-card v-if="stageDetail" shadow="never" class="io-card">
          <template #header>阶段 I/O · {{ stageDetail.label }}</template>
          <p><strong>Agent：</strong>{{ stageDetail.agent }}</p>
          <p><strong>输入：</strong>{{ stageDetail.input ?? '—' }}</p>
          <p><strong>输出：</strong>{{ stageDetail.output ?? '—' }}</p>
        </el-card>

        <h3 class="section-title">注册 Agent</h3>
        <el-row :gutter="12">
          <el-col v-for="a in agents" :key="a.id" :xs="24" :sm="12" :md="8">
            <el-card shadow="hover" class="agent-card" :class="{ running: agentStatus(a.id) === 'running' }">
              <div class="agent-head">
                <span class="agent-id">{{ a.display_name }}</span>
                <span class="status-dot" :class="agentStatus(a.id)" />
              </div>
              <el-tag size="small" effect="plain">{{ a.layer }}</el-tag>
              <p>{{ a.role }}</p>
            </el-card>
          </el-col>
        </el-row>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<style scoped>
.workbench-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 8px 4px 48px;
}

.wb-hero {
  margin-bottom: 20px;
}

.wb-desc {
  margin: 12px 0 0;
  color: var(--alp-color-muted);
  line-height: 1.6;
  font-size: 14px;
}

.wb-generate {
  margin-bottom: 20px;
  padding: 18px 20px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 25%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-primary) 4%, var(--alp-bg-surface));
}

.field-label {
  display: block;
  font-size: 12px;
  color: var(--alp-color-muted);
  margin-bottom: 6px;
}

.gen-btn {
  width: 100%;
  margin-top: 22px;
}

.wb-console {
  margin-bottom: 24px;
}

.workbench-page--embedded {
  max-width: none;
  padding: 0;
}

.workbench-page--embedded .wb-hero {
  margin-bottom: 14px;
}

.wb-flow {
  margin-bottom: 24px;
}

.wb-status-grid {
  margin-bottom: 24px;
}

.wb-dashboard {
  margin-bottom: 24px;
}

.wb-collapse {
  margin-top: 8px;
}

.section-title {
  font-size: 15px;
  margin: 20px 0 12px;
}

.dag-visual {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.dag-node {
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  font-size: 12px;
}

.dag-node.accent {
  border-color: var(--alp-color-primary);
  color: var(--alp-color-primary);
}

.dag-node.warn {
  border-color: #9c7a3d;
}

.dag-arrow {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.dag-note {
  margin: 12px 0;
  color: var(--alp-color-muted);
  font-size: 13px;
  line-height: 1.6;
}

.io-card p {
  margin: 6px 0;
  font-size: 13px;
}

.pipeline-steps :deep(.el-step__title) {
  cursor: pointer;
}

.agent-card {
  margin-bottom: 12px;
  min-height: 100px;
}

.agent-card.running {
  box-shadow: 0 0 0 2px var(--alp-color-primary);
}

.agent-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.agent-id {
  font-weight: 700;
  color: var(--alp-color-primary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-dot.running {
  background: #4a8a5e;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  50% {
    opacity: 0.4;
  }
}

.agent-card p {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
}
</style>
