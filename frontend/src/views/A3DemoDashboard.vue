<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  Connection,
  DataAnalysis,
  FolderOpened,
  Lock,
  Promotion,
  Reading,
  RefreshRight,
  VideoPlay,
  Warning,
} from '@element-plus/icons-vue'
import AgentThinkingConsole from '@/components/agents/AgentThinkingConsole.vue'
import MasteryEvaluationCard from '@/components/learning/MasteryEvaluationCard.vue'
import {
  fetchLearningPathPlan,
  fetchPersonaProfile,
  fetchResources,
  RESOURCE_TYPE_META,
  type GeneratedResource,
} from '@/api/orchestrator'
import { fetchMasteryReport } from '@/api/mastery'
import { fetchRecentEvents } from '@/api/events'
import { fetchA3Health, fetchSystemHealth, type A3Health, type ReadinessLevel, type SystemHealth } from '@/api/health'
import { isLoggedIn } from '@/stores/auth'
import {
  A3_COURSE_CHAPTERS,
  A3_DEMO_STEPS,
  A3_FEATURES,
  A3_POSITIONING,
  A3_SHOWCASE_AGENTS,
  MOCK_VERIFICATION_SUMMARY,
} from '@/constants/a3Demo'
import {
  AGENT_ICONS,
  lineFromAgentLog,
  linesFromAgentLogs,
  systemLine,
  type AgentConsoleLine,
} from '@/utils/agentConsole'
import { getResourceVerification, verificationDisplayTag } from '@/utils/verification'

const router = useRouter()
const activeStep = ref(0)
const loading = ref(true)
const loadError = ref('')
const systemHealth = ref<SystemHealth | null>(null)
const a3Health = ref<A3Health | null>(null)

const A3_HEALTH_LABELS: { key: keyof A3Health; label: string }[] = [
  { key: 'course_knowledge_ready', label: '课程知识库' },
  { key: 'profile_chat_ready', label: '画像对话' },
  { key: 'persona_patch_ready', label: '画像 Patch' },
  { key: 'skill_cards_ready', label: 'SkillCard' },
  { key: 'resource_generation_ready', label: '资源生成' },
  { key: 'verifier_ready', label: 'Verifier' },
  { key: 'safety_ready', label: 'Safety' },
  { key: 'oj_trace_ready', label: 'OJ Trace' },
  { key: 'student_memory_ready', label: 'StudentMemory' },
  { key: 'mastery_ready', label: 'Mastery' },
  { key: 'learning_path_ready', label: 'LearningPath' },
  { key: 'event_bus_ready', label: 'EventBus' },
  { key: 'llm_configured', label: 'LLM 已配置' },
  { key: 'tts_configured', label: 'TTS 已配置' },
]

const READINESS_LEVEL_META: Record<
  ReadinessLevel,
  { label: string; tagType: 'danger' | 'warning' | 'success' | 'primary' }
> = {
  blocked: { label: '阻断 · 不宜演示', tagType: 'danger' },
  risky: { label: '有风险 · 谨慎录屏', tagType: 'warning' },
  ready: { label: '可演示', tagType: 'success' },
  excellent: { label: '最佳状态', tagType: 'primary' },
}

const readinessMeta = computed(() => {
  const level = a3Health.value?.readiness_level ?? 'blocked'
  return READINESS_LEVEL_META[level]
})

const readinessProgressStatus = computed(() => {
  const score = a3Health.value?.readiness_score ?? 0
  if (score >= 90) return 'success'
  if (score >= 75) return ''
  if (score >= 50) return 'warning'
  return 'exception'
})

const mockFlags = ref({
  persona: false,
  path: false,
  resources: false,
  mastery: false,
  events: false,
  verification: false,
})

const usingMock = computed(() => Object.values(mockFlags.value).some(Boolean))

const personaSummary = ref('')
const pathSummary = ref('')
const resources = ref<GeneratedResource[]>([])
const consoleLines = ref<AgentConsoleLine[]>([])
const verificationStats = ref({ ...MOCK_VERIFICATION_SUMMARY })
const masteryScore = ref<number | null>(null)
const masteryLevel = ref('')

const MOCK_PERSONA =
  '大一计科学生，视觉型学习者；链表与指针操作偏弱，动态规划刚入门；目标为期末算法课 85 分以上。'
const MOCK_PATH =
  '先巩固线性表与栈队列，再进入树与图；动态规划章节插入 SkillCard 引导练习。'

const resourcePreviewTypes = [
  'document',
  'mindmap',
  'exercises',
  'code_case',
  'trace_animation',
  'ppt',
  'video_script',
  'reading',
] as const

const previewByType = computed(() => {
  const map = new Map<string, GeneratedResource>()
  for (const r of resources.value) {
    if (!map.has(r.resource_type)) map.set(r.resource_type, r)
  }
  return map
})

const closedLoop = [
  '对话式画像',
  '个性化路径',
  '多智能体资源',
  '智能辅导',
  '效果评估',
  '动态调整',
]

const demoHints = computed(() => {
  const hints = [...(systemHealth.value?.demo_hints ?? [])]
  for (const w of a3Health.value?.warnings ?? []) {
    if (!hints.includes(w)) hints.push(w)
  }
  return hints
})

const a3HealthActions = computed(() => a3Health.value?.recommended_actions ?? [])

function goStep(idx: number) {
  activeStep.value = idx
  const step = A3_DEMO_STEPS[idx]
  if (step?.route) void router.push(step.route)
}

function buildDemoConsoleLines(): AgentConsoleLine[] {
  return [
    systemLine('A3 演示闭环 · EventBus 编排多智能体协同', 'running'),
    lineFromAgentLog({
      agent: 'ProfilingAgent',
      action: '画像同步',
      detail: '六维画像已注入资源生成上下文',
      status: 'done',
    }),
    lineFromAgentLog({
      agent: 'KnowledgeRetriever',
      action: 'BM25 检索',
      detail: '命中课程知识库 5 条切片',
      status: 'done',
    }),
    lineFromAgentLog({
      agent: 'ContentVerifierAgent',
      action: 'verify_pass',
      detail: '对照知识库校验通过',
      status: 'done',
    }),
    lineFromAgentLog({
      agent: 'SafetyAgent',
      action: '内容安全审查通过',
      detail: '未发现 Prompt 注入与敏感词',
      status: 'done',
    }),
    lineFromAgentLog({
      agent: 'MasteryAgent',
      action: 'recalculate',
      detail: '掌握度 62 · competent',
      status: 'done',
    }),
    lineFromAgentLog({
      agent: 'LearningPathAgent',
      action: 'path_adjusted',
      detail: '低掌握度章节已建议插入巩固节点',
      status: 'done',
    }),
  ]
}

function buildMockResources(): GeneratedResource[] {
  return resourcePreviewTypes.map((type, i) => ({
    id: -(i + 1),
    resource_type: type,
    agent_name: RESOURCE_TYPE_META[type]?.agentName ?? type,
    title: `演示 · ${RESOURCE_TYPE_META[type]?.label ?? type}`,
    content: '',
    meta: {
      status: 'published',
      verified: true,
      chapter_id: A3_COURSE_CHAPTERS[i % A3_COURSE_CHAPTERS.length]?.id,
      verification: {
        verifier_status: 'passed',
        safety_status: 'passed',
        evidence_count: 3,
        risk_label: '无风险',
        final_decision: 'publish',
      },
    },
    created_at: new Date().toISOString(),
  }))
}

function aggregateVerification(items: GeneratedResource[]) {
  let passed = 0
  let warning = 0
  let failed = 0
  let evidenceTotal = 0
  for (const r of items) {
    const v = getResourceVerification(r.meta)
    if (!v) continue
    if (v.verifier_status === 'passed' && v.safety_status === 'passed') passed += 1
    else if (v.safety_status === 'failed' || v.final_decision === 'blocked') failed += 1
    else warning += 1
    evidenceTotal += v.evidence_count ?? v.grounded_chunks?.length ?? 0
  }
  if (passed + warning + failed === 0) return null
  return {
    passed,
    warning,
    failed,
    evidenceTotal,
    riskLabel: failed ? '安全警告' : warning ? '可能幻觉' : '无风险',
    skipReason: '',
  }
}

function applyFieldFallbacks() {
  if (!personaSummary.value) {
    personaSummary.value = MOCK_PERSONA
    mockFlags.value.persona = true
  }
  if (!pathSummary.value) {
    pathSummary.value = MOCK_PATH
    mockFlags.value.path = true
  }
  if (!resources.value.length) {
    resources.value = buildMockResources()
    mockFlags.value.resources = true
  }
  if (masteryScore.value == null) {
    masteryScore.value = 58
    masteryLevel.value = 'improving'
    mockFlags.value.mastery = true
  }
  if (!consoleLines.value.length) {
    consoleLines.value = buildDemoConsoleLines()
    mockFlags.value.events = true
  }
  const agg = aggregateVerification(resources.value)
  if (agg) {
    verificationStats.value = agg
  } else if (mockFlags.value.resources) {
    verificationStats.value = { ...MOCK_VERIFICATION_SUMMARY }
    mockFlags.value.verification = true
  }
}

async function loadDashboard() {
  loading.value = true
  loadError.value = ''
  mockFlags.value = {
    persona: false,
    path: false,
    resources: false,
    mastery: false,
    events: false,
    verification: false,
  }
  personaSummary.value = ''
  pathSummary.value = ''
  resources.value = []
  consoleLines.value = []
  masteryScore.value = null
  masteryLevel.value = ''
  verificationStats.value = { ...MOCK_VERIFICATION_SUMMARY }

  systemHealth.value = await fetchSystemHealth()
  a3Health.value = await fetchA3Health()

  let apiErrors = 0

  if (isLoggedIn.value) {
    try {
      const profile = await fetchPersonaProfile()
      if (profile.summary) personaSummary.value = profile.summary
    } catch {
      apiErrors += 1
    }
    try {
      const { plan } = await fetchLearningPathPlan()
      if (plan?.summary) pathSummary.value = plan.summary
    } catch {
      apiErrors += 1
    }
    try {
      const items = await fetchResources()
      if (items.length) {
        resources.value = items.slice(0, 16)
        const agg = aggregateVerification(items)
        if (agg) verificationStats.value = agg
      }
    } catch {
      apiErrors += 1
    }
    try {
      const mastery = await fetchMasteryReport()
      if (mastery.overall_score != null) {
        masteryScore.value = mastery.overall_score
        masteryLevel.value = mastery.overall_level
      }
    } catch {
      apiErrors += 1
    }
    try {
      const events = await fetchRecentEvents({ limit: 8 })
      const logs = events.items.flatMap((e) => e.agent_logs ?? []).slice(0, 12)
      if (logs.length) {
        consoleLines.value = [
          systemLine('EventBus · 最近学习事件链', 'done'),
          ...linesFromAgentLogs(logs),
        ]
      }
    } catch {
      apiErrors += 1
    }
    if (apiErrors >= 3) {
      loadError.value = '部分后端接口暂不可用，已用演示数据补全空白区块'
    }
  }

  applyFieldFallbacks()
  loading.value = false
}

onMounted(loadDashboard)
</script>

<template>
  <div v-loading="loading" class="a3-demo">
    <el-alert
      v-if="loadError"
      type="warning"
      :closable="false"
      show-icon
      class="demo-alert"
      :title="loadError"
    >
      <el-button size="small" :icon="RefreshRight" @click="loadDashboard">重试</el-button>
    </el-alert>

    <el-alert
      v-if="demoHints.length"
      type="info"
      :closable="true"
      show-icon
      class="demo-alert"
      title="演示环境提示"
    >
      <ul class="hint-list">
        <li v-for="(h, i) in demoHints" :key="i">{{ h }}</li>
      </ul>
      <ul v-if="a3HealthActions.length" class="hint-list action-list">
        <li v-for="(a, i) in a3HealthActions" :key="`a-${i}`"><strong>建议：</strong>{{ a }}</li>
      </ul>
    </el-alert>

    <!-- A3 核心流程自检 -->
    <section v-if="a3Health" class="section health-section">
      <h2 class="section-title">A3 演示可用性</h2>
      <div class="readiness-panel">
        <div class="readiness-score-block">
          <el-progress
            type="dashboard"
            :percentage="a3Health.readiness_score"
            :status="readinessProgressStatus || undefined"
            :width="120"
          />
          <div class="readiness-score-text">
            <el-tag :type="readinessMeta.tagType" effect="dark" round>
              {{ readinessMeta.label }}
            </el-tag>
            <p class="readiness-score-caption">演示可用性评分</p>
          </div>
        </div>
        <div class="readiness-details">
          <el-alert
            v-if="a3Health.blockers.length"
            type="error"
            :closable="false"
            show-icon
            title="阻断项（需先修复）"
            class="readiness-alert"
          >
            <ul class="hint-list">
              <li v-for="(b, i) in a3Health.blockers" :key="`b-${i}`">{{ b }}</li>
            </ul>
          </el-alert>
          <el-alert
            v-if="a3Health.warnings.length"
            type="warning"
            :closable="false"
            show-icon
            title="风险项"
            class="readiness-alert"
          >
            <ul class="hint-list">
              <li v-for="(w, i) in a3Health.warnings" :key="`w-${i}`">{{ w }}</li>
            </ul>
          </el-alert>
          <p v-if="a3Health.demo_path_recommendation" class="demo-path-rec">
            <strong>推荐演示路径：</strong>{{ a3Health.demo_path_recommendation }}
          </p>
        </div>
      </div>

      <h3 class="subsection-title">子系统状态</h3>
      <div class="health-grid">
        <div v-for="item in A3_HEALTH_LABELS" :key="item.key" class="health-chip">
          <span>{{ item.label }}</span>
          <el-tag
            :type="a3Health[item.key] ? 'success' : 'warning'"
            size="small"
            effect="plain"
          >
            {{ a3Health[item.key] ? '就绪' : '待修复' }}
          </el-tag>
        </div>
      </div>
    </section>
    <!-- Hero -->
    <section class="hero">
      <div class="hero-glow" aria-hidden="true" />
      <div class="hero-inner">
        <el-tag type="primary" effect="dark" round class="hero-badge">中国软件杯 A3 · 比赛演示</el-tag>
        <h1 class="hero-title">{{ A3_POSITIONING }}</h1>
        <p class="hero-sub">
          完整闭环：对话式画像 → 个性化路径 → 多智能体资源生成 → 智能辅导 → 学习效果评估 → 动态调整
        </p>
        <div class="loop-pills">
          <span v-for="(label, i) in closedLoop" :key="label" class="loop-pill">
            {{ label }}
            <el-icon v-if="i < closedLoop.length - 1"><ArrowRight /></el-icon>
          </span>
        </div>
        <div class="hero-actions">
          <el-button type="primary" size="large" round @click="goStep(0)">
            <el-icon><Promotion /></el-icon>
            开始 7 分钟演示
          </el-button>
          <el-button size="large" round @click="router.push({ name: 'agent-workbench' })">
            <el-icon><FolderOpened /></el-icon>
            多智能体工作台
          </el-button>
        </div>
        <el-tag v-if="usingMock" type="warning" effect="plain" class="mock-tag">
          <el-icon><Warning /></el-icon>
          含演示数据（真实 API 可用时优先展示）
        </el-tag>
      </div>
    </section>

    <!-- 赛题功能完成度 -->
    <section class="section">
      <h2 class="section-title">赛题功能完成度</h2>
      <div class="feature-grid">
        <div v-for="f in A3_FEATURES" :key="f.key" class="feature-card">
          <span class="feature-icon">{{ f.icon }}</span>
          <div>
            <strong>{{ f.title }}</strong>
            <p>{{ f.desc }}</p>
          </div>
          <el-tag type="success" size="small" effect="plain">已实现</el-tag>
        </div>
      </div>
    </section>

    <!-- 一键演示 Stepper -->
    <section class="section stepper-section">
      <h2 class="section-title">
        <el-icon><VideoPlay /></el-icon>
        一键演示流程（7 分钟）
      </h2>
      <el-steps :active="activeStep" align-center finish-status="success" class="demo-steps">
        <el-step
          v-for="(s, i) in A3_DEMO_STEPS"
          :key="i"
          :title="s.title"
          :description="s.desc"
          @click="goStep(i)"
        />
      </el-steps>
      <p class="context-snippet">
        <span v-if="personaSummary">
          <strong>画像摘要：</strong>{{ personaSummary.slice(0, 80) }}…
          <el-tag v-if="mockFlags.persona" size="small" type="warning" effect="plain">演示</el-tag>
        </span>
        <span v-if="pathSummary">
          <strong>路径策略：</strong>{{ pathSummary.slice(0, 80) }}…
          <el-tag v-if="mockFlags.path" size="small" type="warning" effect="plain">演示</el-tag>
        </span>
      </p>
    </section>

    <!-- 多智能体 + 日志 -->
    <el-row :gutter="16" class="section">
      <el-col :xs="24" :lg="14">
        <section class="panel">
          <h2 class="section-title">
            <el-icon><Connection /></el-icon>
            多智能体协作
          </h2>
          <div class="agent-grid">
            <div v-for="a in A3_SHOWCASE_AGENTS" :key="a.id" class="agent-chip">
              <span class="agent-icon">{{ AGENT_ICONS[a.id] ?? '🤖' }}</span>
              <div>
                <strong>{{ a.id }}</strong>
                <small>{{ a.role }}</small>
              </div>
              <el-tag size="small" effect="plain">{{ a.layer }}</el-tag>
            </div>
          </div>
        </section>

        <section class="panel">
          <h2 class="section-title">
            <el-icon><Reading /></el-icon>
            《数据结构与算法》课程知识库
          </h2>
          <div class="chapter-grid">
            <div v-for="ch in A3_COURSE_CHAPTERS" :key="ch.id" class="chapter-card">
              <span class="ch-id">{{ ch.id.replace('ch', '').slice(0, 2) }}</span>
              <strong>{{ ch.title }}</strong>
              <el-tag size="small" effect="plain">{{ ch.difficulty }}</el-tag>
            </div>
          </div>
        </section>
      </el-col>

      <el-col :xs="24" :lg="10">
        <section class="panel console-panel">
          <h2 class="section-title">Agent 执行日志</h2>
          <AgentThinkingConsole
            :lines="consoleLines"
            :active="loading"
            mode="resource"
            title="A3 Demo Terminal"
            subtitle="EventBus · multi-agent synergy"
          />
        </section>
      </el-col>
    </el-row>

    <!-- 资源成果预览 -->
    <section class="section panel">
      <h2 class="section-title">多模态资源生成成果</h2>
      <div class="resource-grid">
        <div
          v-for="type in resourcePreviewTypes"
          :key="type"
          class="resource-tile"
          :style="{ '--accent': RESOURCE_TYPE_META[type]?.color ?? '#64748b' }"
          @click="router.push({ name: 'resources' })"
        >
          <span class="res-type">{{ RESOURCE_TYPE_META[type]?.label ?? type }}</span>
          <span class="res-agent">{{ RESOURCE_TYPE_META[type]?.agentName }}</span>
          <template v-if="previewByType.get(type)">
            <p class="res-title">{{ previewByType.get(type)!.title }}</p>
            <el-tag
              size="small"
              effect="plain"
              :type="verificationDisplayTag(previewByType.get(type)!.meta).type"
            >
              {{ verificationDisplayTag(previewByType.get(type)!.meta).riskLabel }}
            </el-tag>
          </template>
          <el-tag v-else size="small" type="info" effect="plain">待生成</el-tag>
        </div>
      </div>
    </section>

    <!-- 评估 + 安全 -->
    <el-row :gutter="16" class="section">
      <el-col :xs="24" :lg="14">
        <MasteryEvaluationCard v-if="isLoggedIn" />
        <el-card v-else shadow="never" class="eval-fallback">
          <div class="eval-fallback-head">
            <el-icon><DataAnalysis /></el-icon>
            <span>MasteryAgent · 学习效果评估</span>
            <el-tag type="warning" size="small" effect="plain">演示数据</el-tag>
          </div>
          <div class="eval-score-row">
            总掌握度 <strong>{{ masteryScore ?? 58 }}</strong>
            <el-tag size="small">{{ masteryLevel || 'improving' }}</el-tag>
          </div>
          <p>薄弱技能：链表指针操作、DP 状态设计</p>
          <p>下一步：完成 ch02 巩固练习 → 重算掌握度 → 路径 Agent 解锁下一章</p>
          <el-button type="primary" plain size="small" @click="router.push({ name: 'login' })">
            登录查看真实评估
          </el-button>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="safety-card">
          <div class="safety-card-head">
            <el-icon><Lock /></el-icon>
            <span>防幻觉与安全状态</span>
            <el-tag v-if="usingMock" size="small" type="warning" effect="plain">演示数据</el-tag>
          </div>
          <div class="safety-stats">
            <div class="stat">
              <strong>{{ verificationStats.passed }}</strong>
              <span>校验通过</span>
            </div>
            <div class="stat warn">
              <strong>{{ verificationStats.warning }}</strong>
              <span>告警</span>
            </div>
            <div class="stat">
              <strong>{{ verificationStats.evidenceTotal }}</strong>
              <span>引用片段</span>
            </div>
          </div>
          <p class="risk-line">
            风险标签：<el-tag size="small" effect="plain">{{ verificationStats.riskLabel }}</el-tag>
          </p>
          <ul class="safety-list">
            <li>ContentVerifierAgent：题号 / 复杂度 / 章节引用规则快检 + LLM 对照</li>
            <li>SafetyAgent：敏感词 · Prompt 注入 · 学术幻觉预警</li>
            <li>trace_animation 跳过文本校验，Safety 仍审查并记录 skip_reason</li>
          </ul>
          <el-button plain size="small" @click="router.push({ name: 'resources' })">
            查看资源校验证据
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.a3-demo {
  max-width: 1280px;
  margin: 0 auto;
  animation: fade-in 0.4s ease;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.hero {
  position: relative;
  border-radius: var(--alp-radius-card, 12px);
  padding: 32px 28px;
  margin-bottom: 24px;
  overflow: hidden;
  border: 1px solid var(--alp-color-border);
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--alp-color-primary) 12%, var(--alp-bg-soft-block)),
    var(--alp-bg-soft-block)
  );
}

.hero-glow {
  position: absolute;
  inset: -40% 30% auto -20%;
  height: 200px;
  background: radial-gradient(circle, color-mix(in srgb, var(--alp-color-primary) 25%, transparent), transparent 70%);
  pointer-events: none;
}

.hero-inner {
  position: relative;
  z-index: 1;
}

.hero-badge {
  margin-bottom: 12px;
}

.hero-title {
  margin: 0 0 12px;
  font-size: clamp(1.25rem, 2.5vw, 1.65rem);
  line-height: 1.35;
  font-weight: 700;
  color: var(--alp-color-text);
}

.hero-sub {
  margin: 0 0 16px;
  color: var(--alp-color-muted);
  font-size: 14px;
  line-height: 1.6;
  max-width: 920px;
}

.loop-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.loop-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-bg-surface) 85%, transparent);
  border: 1px solid var(--alp-color-border);
  font-size: 12px;
  color: var(--alp-color-text);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.mock-tag {
  margin-top: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.demo-alert {
  margin-bottom: 16px;
}

.hint-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.5;
}

.section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 600;
}

.panel {
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card, 12px);
  padding: 18px;
  margin-bottom: 16px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.readiness-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.readiness-score-block {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.readiness-score-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.readiness-score-caption {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.readiness-details {
  flex: 1;
  min-width: 260px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.readiness-alert {
  margin: 0;
}

.demo-path-rec {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.subsection-title {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.health-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
  font-size: 13px;
}

.action-list {
  margin-top: 8px;
}

.feature-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: start;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.feature-icon {
  font-size: 28px;
  line-height: 1;
}

.feature-card p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.demo-steps {
  cursor: pointer;
  margin-bottom: 12px;
}

.demo-steps :deep(.el-step__title) {
  font-size: 13px;
}

.context-snippet {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: var(--alp-color-muted);
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px dashed var(--alp-color-border);
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.agent-chip {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 8px;
  align-items: center;
  padding: 10px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.agent-icon {
  font-size: 22px;
}

.agent-chip strong {
  display: block;
  font-size: 12px;
}

.agent-chip small {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.chapter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
}

.chapter-card {
  padding: 10px;
  border-radius: 8px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ch-id {
  font-size: 10px;
  color: var(--alp-color-primary);
  font-weight: 600;
}

.console-panel :deep(.agent-terminal) {
  min-height: 320px;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}

.resource-tile {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  cursor: pointer;
  transition: border-color 0.15s, transform 0.15s;
  border-top: 3px solid var(--accent);
}

.resource-tile:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.res-type {
  display: block;
  font-weight: 600;
  font-size: 13px;
}

.res-agent {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.res-title {
  margin: 6px 0;
  font-size: 11px;
  line-height: 1.4;
  color: var(--alp-color-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.eval-fallback,
.safety-card {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card, 12px);
}

.eval-fallback-head,
.safety-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 12px;
}

.eval-score-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}

.eval-score-row strong {
  font-size: 32px;
  color: var(--alp-color-primary);
}

.safety-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.stat {
  text-align: center;
}

.stat strong {
  display: block;
  font-size: 24px;
  color: var(--alp-color-primary);
}

.stat span {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.stat.warn strong {
  color: #f59e0b;
}

.risk-line {
  font-size: 13px;
  margin: 0 0 10px;
}

.safety-list {
  margin: 0 0 12px;
  padding-left: 18px;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.6;
}

@media (max-width: 768px) {
  .hero {
    padding: 20px 16px;
  }

  .loop-pill .el-icon {
    display: none;
  }
}
</style>
