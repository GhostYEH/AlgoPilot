<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchAgentsCatalog,
  getStageDetail,
  streamGenerateAllResources,
  type AgentInfo,
  type GeneratedResource,
} from '@/api/orchestrator'
import { isLoggedIn } from '@/stores/auth'
import AgentThinkingConsole from '@/components/agents/AgentThinkingConsole.vue'
import PersonalizedResourceDashboard from '@/components/agents/PersonalizedResourceDashboard.vue'
import type { AgentConsoleLine } from '@/utils/agentConsole'
import { A3_SHOWCASE_AGENTS, DEMO_RESOURCE_PIPELINE } from '@/constants/a3Demo'
import {
  lineFromCollaboration,
  lineFromProgress,
  lineFromWorkflow,
  lineFromAgentLog,
  resourceBootstrapLines,
  systemLine,
} from '@/utils/agentConsole'

const router = useRouter()

const agents = ref<AgentInfo[]>([])
const pipeline = ref<Array<{ stage: string; agent: string; label: string }>>([])
const note = ref('')
const dagMermaid = ref('')
const activeStage = ref(0)

const topic = ref('动态规划入门')
const focusHint = ref('主攻状态转移方程与边界')
const generating = ref(false)
const progress = ref(0)
const consoleLines = ref<AgentConsoleLine[]>([])
const generatedResources = ref<GeneratedResource[]>([])
const activeResourceTab = ref('document')

const stageDetail = computed(() => {
  const s = pipeline.value[activeStage.value]
  return s ? getStageDetail(s.stage) : null
})

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
    agents.value = A3_SHOWCASE_AGENTS.map((a) => ({
      id: a.id,
      display_name: a.id,
      role: a.role,
      layer: a.layer,
    }))
    pipeline.value = [...DEMO_RESOURCE_PIPELINE]
    note.value = '后端 catalog 暂不可用，已加载演示用 Pipeline 说明'
  }
})

function pushLine(line: AgentConsoleLine) {
  consoleLines.value = [...consoleLines.value, line]
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

  generating.value = true
  progress.value = 0
  consoleLines.value = [...resourceBootstrapLines(topic.value)]
  generatedResources.value = []

  try {
    await streamGenerateAllResources(
      { topic: topic.value, focus_hint: focusHint.value },
      {
        onProgress(p) {
          pushLine(lineFromProgress(p))
          if (typeof p.percent === 'number') progress.value = p.percent
          activeResourceTab.value = p.resource_type
        },
        onWorkflow(w) {
          if (w.status === 'done') markRunningDone(w.agent)
          pushLine(lineFromWorkflow(w))
          if (typeof w.percent === 'number') progress.value = w.percent
        },
        onCollaboration(log) {
          for (const row of log) pushLine(lineFromCollaboration(row))
        },
        onAgentLogs(logs) {
          for (const entry of logs) pushLine(lineFromAgentLog(entry))
        },
        onResource(r) {
          generatedResources.value = [
            r,
            ...generatedResources.value.filter((x) => x.id !== r.id),
          ]
          activeResourceTab.value = r.resource_type
          pushLine(
            systemLine(
              `${r.agent_name} 已落库 · ${r.title.slice(0, 40)}`,
              'done',
            ),
          )
        },
        onDone(info) {
          progress.value = 100
          if (info?.fallback_mode) {
            pushLine(
              systemLine(
                'TemplateFallbackAgent：无 LLM Key，已用课程知识库模板降级（非大模型生成）',
                'warn',
              ),
            )
            ElMessage.warning(
              '当前为无模型 Key 的模板降级资源，配置 SPARK_API_PASSWORD 后可生成更高质量内容。',
            )
          } else if (info?.partial_failure) {
            const failed = info.errors?.map((e) => e.agent_name ?? e.resource_type ?? '未知').join('、') ?? '部分资源'
            pushLine(systemLine(`部分资源生成失败（${failed}），其余已装配完毕`, 'warn'))
            ElMessage.warning(`${failed} 生成失败，其余资源已就绪`)
          } else {
            pushLine(systemLine('比赛展示型个性化资源装配完毕！', 'success'))
            ElMessage.success('比赛展示资源已全部生成')
          }
        },
        onError(msg) {
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
  <div class="workbench-page">
    <div class="wb-hero">
      <el-page-header title="多智能体协同工作台" @back="router.push({ name: 'home' })" />
      <p class="wb-desc">{{ note || 'ProfilingAgent 驱动比赛展示资源 Agent 协同生成 · 赛题答辩演示入口' }}</p>
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
        <el-col :xs="24" :md="9">
          <label class="field-label">课程主题</label>
          <el-input v-model="topic" size="large" placeholder="如：动态规划入门" />
        </el-col>
        <el-col :xs="24" :md="9">
          <label class="field-label">生成侧重</label>
          <el-input v-model="focusHint" size="large" placeholder="如：状态转移方程" />
        </el-col>
        <el-col :xs="24" :md="6">
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
      subtitle="Concept → Graph → Quiz → Scenario → Trace → PPT → Video → Reading"
      class="wb-console"
    />

    <PersonalizedResourceDashboard
      v-if="generatedResources.length || generating"
      :resources="generatedResources"
      v-model:active-tab="activeResourceTab"
      class="wb-dashboard"
    />

    <el-collapse v-else class="wb-collapse">
      <el-collapse-item title="架构说明 · DAG Pipeline（答辩备用）" name="arch">
        <div class="dag-visual">
          <div class="dag-node">KnowledgeRetriever</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node accent">八类 Role Agents</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node warn">Verifier</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node">Safety → 落库</div>
        </div>
        <pre v-if="dagMermaid" class="mermaid-src">{{ dagMermaid }}</pre>

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
  border-color: #f59e0b;
}

.dag-arrow {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.mermaid-src {
  font-size: 11px;
  background: var(--alp-bg-soft-block);
  padding: 10px;
  border-radius: 8px;
  overflow: auto;
  max-height: 200px;
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
  background: #22c55e;
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
