<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchAgentsCatalog,
  getStageDetail,
  type AgentInfo,
} from '@/api/orchestrator'

const router = useRouter()
const agents = ref<AgentInfo[]>([])
const pipeline = ref<Array<{ stage: string; agent: string; label: string }>>([])
const note = ref('')
const dagMermaid = ref('')
const activeStage = ref(0)
const demoRunning = ref(false)
const demoAgent = ref('')
const collabLogs = ref<Array<{ agent: string; action: string; detail: string }>>([])
const logExpanded = ref(false)

const stageDetail = computed(() => {
  const s = pipeline.value[activeStage.value]
  return s ? getStageDetail(s.stage) : null
})

onMounted(async () => {
  try {
    const r = await fetchAgentsCatalog()
    agents.value = r.agents
    pipeline.value = r.resource_pipeline
    note.value = r.framework_note
    dagMermaid.value = r.dag_mermaid ?? ''
  } catch {
    agents.value = []
  }
})

function agentStatus(id: string): 'running' | 'idle' {
  if (!demoRunning.value) return 'idle'
  if (demoAgent.value && id.includes(demoAgent.value.replace('Agent', ''))) return 'running'
  if (demoAgent.value === id) return 'running'
  return 'idle'
}

async function runPipelineDemo() {
  if (demoRunning.value || !pipeline.value.length) return
  demoRunning.value = true
  collabLogs.value = []
  for (let i = 0; i < pipeline.value.length; i++) {
    activeStage.value = i
    const s = pipeline.value[i]
    demoAgent.value = s.agent === 'role_agent' ? 'DocAgent' : s.agent
    collabLogs.value.push({
      agent: demoAgent.value,
      action: s.stage,
      detail: `${s.label} · running`,
    })
    await new Promise((r) => setTimeout(r, 700))
    collabLogs.value[collabLogs.value.length - 1] = {
      agent: demoAgent.value,
      action: s.stage,
      detail: `${s.label} · done`,
    }
  }
  demoRunning.value = false
  demoAgent.value = ''
  ElMessage.success('DAG 演示完成（示意各阶段输入/输出）')
}

function selectStage(idx: number) {
  activeStage.value = idx
}
</script>

<template>
  <el-card shadow="never" class="page-card">
    <el-page-header title="多智能体工作台" @back="router.push({ name: 'home' })" />
    <el-divider />
    <p class="muted">{{ note }}</p>

    <div class="toolbar">
      <el-button type="primary" :loading="demoRunning" @click="runPipelineDemo">
        运行动态 Pipeline 演示
      </el-button>
      <el-button @click="logExpanded = !logExpanded">
        {{ logExpanded ? '收起' : '展开' }}协作日志
      </el-button>
    </div>

    <h3 class="section-title">DAG 架构（条件路由 + 校验闭环）</h3>
    <el-row :gutter="12">
      <el-col :xs="24" :md="14">
        <div class="dag-visual">
          <div class="dag-node">KnowledgeRetriever</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node accent">Role Agents</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node warn">Verifier?</div>
          <span class="dag-arrow">→</span>
          <div class="dag-node">Safety → 落库</div>
        </div>
        <pre v-if="dagMermaid" class="mermaid-src">{{ dagMermaid }}</pre>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-card v-if="stageDetail" shadow="never" class="io-card">
          <template #header>阶段 I/O · {{ stageDetail.label }}</template>
          <p><strong>Agent：</strong>{{ stageDetail.agent }}</p>
          <p><strong>输入：</strong>{{ stageDetail.input ?? '—' }}</p>
          <p><strong>输出：</strong>{{ stageDetail.output ?? '—' }}</p>
        </el-card>
      </el-col>
    </el-row>

    <h3 class="section-title">资源生成 Pipeline（可点击阶段）</h3>
    <el-steps
      :active="activeStage"
      finish-status="success"
      align-center
      class="pipeline-steps"
    >
      <el-step
        v-for="(s, idx) in pipeline"
        :key="s.stage"
        :title="s.agent === 'role_agent' ? '角色 Agent' : s.agent"
        :description="s.label"
        class="clickable-step"
        @click="selectStage(idx)"
      />
    </el-steps>

    <h3 class="section-title">角色智能体</h3>
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

    <el-drawer v-model="logExpanded" title="Agent 协作日志" size="90%" direction="btt">
      <el-empty v-if="!collabLogs.length" description="点击「运行动态 Pipeline 演示」或去资源库批量生成查看真实日志" />
      <ul v-else class="log-list">
        <li v-for="(row, i) in collabLogs" :key="i">
          <strong>{{ row.agent }}</strong> · {{ row.action }} — {{ row.detail }}
        </li>
      </ul>
    </el-drawer>
  </el-card>
</template>

<style scoped>
.page-card {
  border-radius: var(--alp-radius-card);
}

.muted {
  color: var(--alp-color-muted);
  line-height: 1.6;
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
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
  transition: box-shadow 0.3s;
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

.log-list {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  line-height: 1.7;
  padding-left: 18px;
}
</style>
