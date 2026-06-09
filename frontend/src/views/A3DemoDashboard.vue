<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Connection,
  DataAnalysis,
  Lock,
  Promotion,
  RefreshRight,
  Warning,
} from '@element-plus/icons-vue'
import AgentThinkingConsole from '@/components/agents/AgentThinkingConsole.vue'
import {
  fetchPersonaProfile,
  fetchLearningPathPlan,
  fetchResources,
  fetchRecommendedResources,
  RESOURCE_TYPE_META,
  PROFILE_DIMENSION_LABELS,
  type GeneratedResource,
  type PersonaDimensions,
  type PersonaProfile,
} from '@/api/orchestrator'
import { fetchMasteryReport, MASTERY_LEVEL_LABELS, type MasteryOverview } from '@/api/mastery'
import { fetchRecentEvents } from '@/api/events'
import { fetchA3Health, fetchSystemHealth, type A3Health, type SystemHealth } from '@/api/health'
import { isLoggedIn } from '@/stores/auth'
import {
  A3_POSITIONING,
  A3_SUBTITLE,
  A3_DEMO_STEPS,
  A3_SHOWCASE_AGENTS,
  A3_COURSE_CHAPTERS,
  MOCK_VERIFICATION_SUMMARY,
  MOCK_PERSONA_DIMENSIONS,
  MOCK_PERSONA_OVERALL_CONFIDENCE,
  MOCK_OJ_TRACE,
  MOCK_LEARNING_EVAL,
  MOCK_RECOMMENDED_RESOURCES,
  type PersonaDimensionScore,
  type OjTraceDemoData,
  type LearningEvalDemoData,
  type RecommendedResourceDemo,
} from '@/constants/a3Demo'
import {
  AGENT_ICONS,
  lineFromAgentLog,
  linesFromAgentLogs,
  systemLine,
  type AgentConsoleLine,
} from '@/utils/agentConsole'
import { getResourceVerification } from '@/utils/verification'

const router = useRouter()
const activeStep = ref(0)
const loading = ref(true)
const loadError = ref('')
const systemHealth = ref<SystemHealth | null>(null)
const a3Health = ref<A3Health | null>(null)

const mockFlags = ref({
  persona: false,
  path: false,
  resources: false,
  mastery: false,
  events: false,
  verification: false,
  recommendations: false,
})

const usingMock = computed(() => Object.values(mockFlags.value).some(Boolean))

const personaSummary = ref('')
const personaDimensions = ref<PersonaDimensionScore[]>([...MOCK_PERSONA_DIMENSIONS])
const personaConfidence = ref(MOCK_PERSONA_OVERALL_CONFIDENCE)
const pathSummary = ref('')
const resources = ref<GeneratedResource[]>([])
const recommendedResources = ref<RecommendedResourceDemo[]>([...MOCK_RECOMMENDED_RESOURCES])
const consoleLines = ref<AgentConsoleLine[]>([])
const verificationStats = ref({ ...MOCK_VERIFICATION_SUMMARY })
const masteryScore = ref<number | null>(null)
const masteryLevel = ref('')
const masteryOverview = ref<MasteryOverview | null>(null)
const ojTraceData = ref<OjTraceDemoData>({ ...MOCK_OJ_TRACE })
const learningEvalData = ref<LearningEvalDemoData>({ ...MOCK_LEARNING_EVAL })

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
  'reading',
] as const

const demoHints = computed(() => {
  const hints = [...(systemHealth.value?.demo_hints ?? [])]
  for (const w of a3Health.value?.warnings ?? []) {
    if (!hints.includes(w)) hints.push(w)
  }
  return hints
})

const autoStepTimer = ref<ReturnType<typeof setInterval> | null>(null)

function startAutoStep() {
  stopAutoStep()
  autoStepTimer.value = setInterval(() => {
    activeStep.value = (activeStep.value + 1) % A3_DEMO_STEPS.length
  }, 4000)
}

function stopAutoStep() {
  if (autoStepTimer.value) {
    clearInterval(autoStepTimer.value)
    autoStepTimer.value = null
  }
}

function goStep(idx: number) {
  activeStep.value = idx
  stopAutoStep()
  startAutoStep()
  const step = A3_DEMO_STEPS[idx]
  if (step?.route) void router.push(step.route as { name: string })
}

const CONFIDENCE_LABELS: Record<string, string> = { low: '低', medium: '中', high: '高' }
const CONFIDENCE_COLORS: Record<string, string> = { low: '#f59e0b', medium: '#38bdf8', high: '#10b981' }

const PUSH_STRATEGY_LABELS: Record<string, string> = {
  consolidate: '巩固优先',
  advance: '推进优先',
  review: '回退复习',
  maintain: '保持节奏',
}

function radarPoints(dimensions: PersonaDimensionScore[], cx: number, cy: number, r: number): string {
  const n = dimensions.length
  return dimensions
    .map((d, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2
      const ratio = d.score / 100
      const x = cx + r * ratio * Math.cos(angle)
      const y = cy + r * ratio * Math.sin(angle)
      return `${x},${y}`
    })
    .join(' ')
}

function radarAxes(dimensions: PersonaDimensionScore[], cx: number, cy: number, r: number) {
  const n = dimensions.length
  return dimensions.map((d, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2
    const x = cx + r * Math.cos(angle)
    const y = cy + r * Math.sin(angle)
    const labelX = cx + (r + 18) * Math.cos(angle)
    const labelY = cy + (r + 18) * Math.sin(angle)
    return { x2: x, y2: y, labelX, labelY, label: d.label, score: d.score, confidence: d.confidence }
  })
}

function radarGridRings(cx: number, cy: number, r: number, n: number, sides: number) {
  const rings = []
  for (let ring = 1; ring <= n; ring++) {
    const ratio = ring / n
    const points: string[] = []
    for (let i = 0; i < sides; i++) {
      const angle = (Math.PI * 2 * i) / sides - Math.PI / 2
      points.push(`${cx + r * ratio * Math.cos(angle)},${cy + r * ratio * Math.sin(angle)}`)
    }
    rings.push(points.join(' '))
  }
  return rings
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

function mapPersonaToDimensions(profile: PersonaProfile): PersonaDimensionScore[] {
  const scores = profile.dimension_scores ?? {}
  const conf = profile.dimension_confidence ?? {}
  const keys: (keyof PersonaDimensions)[] = [
    'knowledge_base',
    'cognitive_style',
    'coding_ability',
    'learning_goals',
    'error_preference',
    'grit_level',
  ]
  return keys.map((key) => ({
    key,
    label: PROFILE_DIMENSION_LABELS[key],
    score: scores[key] != null ? Number(scores[key]) : 50,
    confidence: (conf[key] as 'low' | 'medium' | 'high') ?? 'medium',
  }))
}

function applyFieldFallbacks() {
  if (!personaSummary.value) {
    personaSummary.value = MOCK_PERSONA
    personaDimensions.value = [...MOCK_PERSONA_DIMENSIONS]
    personaConfidence.value = MOCK_PERSONA_OVERALL_CONFIDENCE
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
    recommendations: false,
  }
  personaSummary.value = ''
  pathSummary.value = ''
  resources.value = []
  consoleLines.value = []
  masteryScore.value = null
  masteryLevel.value = ''
  masteryOverview.value = null
  verificationStats.value = { ...MOCK_VERIFICATION_SUMMARY }

  systemHealth.value = await fetchSystemHealth()
  a3Health.value = await fetchA3Health()

  let apiErrors = 0

  if (isLoggedIn.value) {
    try {
      const profile = await fetchPersonaProfile()
      if (profile.summary) personaSummary.value = profile.summary
      if (profile.dimensions) {
        personaDimensions.value = mapPersonaToDimensions(profile)
        if (profile.dimension_confidence) {
          const confValues = Object.values(profile.dimension_confidence)
          const highCount = confValues.filter((v) => v === 'high').length
          personaConfidence.value = highCount / confValues.length
        }
      }
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
      masteryOverview.value = mastery
      if (mastery.overall_score != null) {
        masteryScore.value = mastery.overall_score
        masteryLevel.value = mastery.overall_level
      }
      if (mastery.report) {
        learningEvalData.value = {
          overallScore: mastery.overall_score,
          level: mastery.overall_level,
          levelLabel: MASTERY_LEVEL_LABELS[mastery.overall_level],
          trend: mastery.report.mastery_trend,
          trendLabel: mastery.report.mastery_trend === 'rising' ? '上升' : mastery.report.mastery_trend === 'falling' ? '下降' : '平稳',
          confidence: mastery.report.confidence_level,
          dimensions: mastery.report.component_scores.map((c) => ({
            key: c.key,
            label: c.label,
            score: c.score,
          })),
          weakSkills: mastery.report.weak_skills,
          pushStrategy: 'consolidate',
          pathAdjustment: mastery.report.path_adjustment_suggestion,
          suggestedReplan: mastery.report.path_adjustment_suggestion.length > 0,
        }
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
    try {
      const recItems = await fetchRecommendedResources({ limit: 5 })
      if (recItems.length) {
        recommendedResources.value = recItems.map((r) => ({
          id: r.id,
          title: r.title,
          resourceType: r.resource_type,
          agentName: r.agent_name,
          chapterId: String(r.meta?.chapter_id ?? ''),
          reason: String(r.meta?.recommendation_reason ?? '基于画像与学习路径推荐'),
          verified: r.meta?.verified === true,
        }))
      }
    } catch {
      mockFlags.value.recommendations = true
    }
    if (apiErrors >= 3) {
      loadError.value = '部分后端接口暂不可用，已用演示数据补全空白区块'
    }
  }

  applyFieldFallbacks()
  loading.value = false
}

onMounted(() => {
  void loadDashboard()
  startAutoStep()
})

onUnmounted(() => {
  stopAutoStep()
})
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
    </el-alert>

    <!-- ===== 1. Hero 区 ===== -->
    <section class="hero">
      <div class="hero-glow" aria-hidden="true" />
      <div class="hero-inner">
        <el-tag type="primary" effect="dark" round class="hero-badge">中国软件杯 A3 · 比赛演示</el-tag>
        <h1 class="hero-title">{{ A3_POSITIONING }}</h1>
        <p class="hero-sub">{{ A3_SUBTITLE }}</p>
        <div class="hero-actions">
          <el-button type="primary" size="large" round @click="goStep(0)">
            <el-icon><Promotion /></el-icon>
            开始 7 分钟演示
          </el-button>
          <el-button size="large" round @click="router.push({ name: 'agent-workbench' })">
            多智能体工作台
          </el-button>
        </div>
        <el-tag v-if="usingMock" type="warning" effect="plain" class="mock-tag">
          <el-icon><Warning /></el-icon>
          含演示数据（真实 API 可用时优先展示）
        </el-tag>
      </div>
    </section>

    <!-- ===== 2. 闭环流程图 ===== -->
    <section class="section">
      <h2 class="section-title">完整闭环流程</h2>
      <div class="loop-flow">
        <template v-for="(step, i) in A3_DEMO_STEPS" :key="step.key">
          <div
            class="loop-node"
            :class="{ active: activeStep === i, done: activeStep > i }"
            @click="goStep(i)"
          >
            <span class="loop-node-icon">{{ step.icon }}</span>
            <span class="loop-node-label">{{ step.title }}</span>
            <span class="loop-node-desc">{{ step.desc }}</span>
          </div>
          <div v-if="i < A3_DEMO_STEPS.length - 1" class="loop-arrow">
            <svg width="32" height="16" viewBox="0 0 32 16">
              <line x1="0" y1="8" x2="24" y2="8" stroke="currentColor" stroke-width="2" />
              <polygon points="24,3 32,8 24,13" fill="currentColor" />
            </svg>
          </div>
        </template>
        <div class="loop-arrow loop-arrow-return">
          <svg width="32" height="32" viewBox="0 0 32 32">
            <path d="M28,28 L4,28 L4,4 L12,4" stroke="currentColor" stroke-width="2" fill="none" />
            <polygon points="8,4 16,4 12,0" fill="currentColor" />
          </svg>
          <span class="return-label">自适应</span>
        </div>
      </div>
    </section>

    <!-- ===== 3. 六维画像卡片 ===== -->
    <section class="section">
      <h2 class="section-title">六维学生画像</h2>
      <div class="persona-panel">
        <div class="radar-wrap">
          <svg
            :width="280"
            :height="280"
            :viewBox="`0 0 280 280`"
            class="radar-svg"
          >
            <g v-for="(ring, ri) in radarGridRings(140, 140, 100, 4, personaDimensions.length)" :key="ri">
              <polygon :points="ring" fill="none" stroke="var(--alp-color-border)" stroke-width="0.8" />
            </g>
            <line
              v-for="ax in radarAxes(personaDimensions, 140, 140, 100)"
              :key="ax.label"
              x1="140" y1="140"
              :x2="ax.x2" :y2="ax.y2"
              stroke="var(--alp-color-border)"
              stroke-width="0.6"
            />
            <polygon
              :points="radarPoints(personaDimensions, 140, 140, 100)"
              fill="rgba(56, 189, 248, 0.18)"
              stroke="var(--alp-color-primary)"
              stroke-width="2"
            />
            <circle
              v-for="(d, di) in personaDimensions"
              :key="'dot-' + di"
              :cx="140 + 100 * (d.score / 100) * Math.cos((Math.PI * 2 * di) / personaDimensions.length - Math.PI / 2)"
              :cy="140 + 100 * (d.score / 100) * Math.sin((Math.PI * 2 * di) / personaDimensions.length - Math.PI / 2)"
              r="4"
              :fill="CONFIDENCE_COLORS[d.confidence]"
            />
            <text
              v-for="(ax, ai) in radarAxes(personaDimensions, 140, 140, 100)"
              :key="'lbl-' + ai"
              :x="ax.labelX"
              :y="ax.labelY"
              text-anchor="middle"
              dominant-baseline="central"
              fill="var(--alp-color-text)"
              font-size="11"
              font-weight="600"
            >{{ ax.label }}</text>
          </svg>
        </div>
        <div class="persona-details">
          <div class="persona-summary-text">
            <strong>画像摘要</strong>
            <p>{{ personaSummary }}</p>
            <el-tag v-if="mockFlags.persona" size="small" type="warning" effect="plain">演示数据</el-tag>
          </div>
          <div class="dimension-bars">
            <div v-for="dim in personaDimensions" :key="dim.key" class="dim-bar-row">
              <span class="dim-label">{{ dim.label }}</span>
              <el-progress
                :percentage="dim.score"
                :stroke-width="10"
                :color="CONFIDENCE_COLORS[dim.confidence]"
                class="dim-progress"
              />
              <el-tag size="small" effect="plain" :type="dim.confidence === 'high' ? 'success' : dim.confidence === 'medium' ? 'warning' : 'danger'">
                置信度 {{ CONFIDENCE_LABELS[dim.confidence] }}
              </el-tag>
            </div>
          </div>
          <div class="confidence-overall">
            <span>画像整体置信度</span>
            <strong>{{ (personaConfidence * 100).toFixed(0) }}%</strong>
            <el-progress
              :percentage="personaConfidence * 100"
              :stroke-width="8"
              :show-text="false"
              class="confidence-progress"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- ===== 4. Agent 协同状态区 ===== -->
    <section class="section">
      <h2 class="section-title">
        <el-icon><Connection /></el-icon>
        多智能体协同状态
      </h2>
      <el-row :gutter="16">
        <el-col :xs="24" :lg="14">
          <div class="agent-grid">
            <div v-for="a in A3_SHOWCASE_AGENTS" :key="a.id" class="agent-card">
              <div class="agent-card-head">
                <span class="agent-icon">{{ AGENT_ICONS[a.id] ?? '🤖' }}</span>
                <div class="agent-card-info">
                  <strong>{{ a.id }}</strong>
                  <small>{{ a.role }}</small>
                </div>
                <el-tag
                  :type="a.status === 'done' ? 'success' : a.status === 'running' ? 'warning' : a.status === 'error' ? 'danger' : 'info'"
                  size="small"
                  effect="plain"
                >
                  {{ a.status === 'done' ? '已完成' : a.status === 'running' ? '运行中' : a.status === 'error' ? '异常' : '空闲' }}
                </el-tag>
              </div>
              <div class="agent-card-body">
                <span v-if="a.resourceType" class="agent-resource-type">
                  资源类型：{{ RESOURCE_TYPE_META[a.resourceType]?.label ?? a.resourceType }}
                </span>
                <span class="agent-recent-log">{{ a.recentLog }}</span>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :lg="10">
          <section class="panel console-panel">
            <h3 class="subsection-title">Agent 执行日志</h3>
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
    </section>

    <!-- ===== 5. 推荐资源区 ===== -->
    <section class="section">
      <h2 class="section-title">个性化推荐资源</h2>
      <div class="rec-grid">
        <div v-for="r in recommendedResources" :key="r.id" class="rec-card">
          <div class="rec-card-head">
            <span
              class="rec-type-dot"
              :style="{ background: RESOURCE_TYPE_META[r.resourceType]?.color ?? '#64748b' }"
            />
            <strong class="rec-title">{{ r.title }}</strong>
            <el-tag
              size="small"
              effect="plain"
              :type="r.verified ? 'success' : 'warning'"
            >
              {{ r.verified ? '已校验' : '待校验' }}
            </el-tag>
          </div>
          <div class="rec-card-meta">
            <span>{{ RESOURCE_TYPE_META[r.resourceType]?.label ?? r.resourceType }}</span>
            <span>·</span>
            <span>{{ r.agentName }}</span>
          </div>
          <div class="rec-reason">
            <strong>为什么推荐给你：</strong>
            <p>{{ r.reason }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== 6. OJ Trace 诊断区 ===== -->
    <section class="section">
      <h2 class="section-title">OJ Trace 诊断</h2>
      <div class="oj-trace-panel">
        <el-row :gutter="16">
          <el-col :xs="24" :lg="12">
            <div class="oj-error-card">
              <div class="oj-error-head">
                <el-tag type="danger" effect="dark" size="small">{{ ojTraceData.verdict }}</el-tag>
                <strong>{{ ojTraceData.problemTitle }}</strong>
                <el-tag size="small" effect="plain">{{ ojTraceData.language }}</el-tag>
              </div>
              <div class="oj-error-type">
                <span>错误类型：</span>
                <el-tag type="danger" effect="plain" size="small">{{ ojTraceData.errorType }}</el-tag>
              </div>
              <div class="oj-failed-case">
                <strong>失败用例：</strong>
                <code>{{ ojTraceData.failedCase }}</code>
              </div>
              <pre class="oj-code-block"><code>{{ ojTraceData.errorCode }}</code></pre>
            </div>
          </el-col>
          <el-col :xs="24" :lg="12">
            <div class="oj-trace-steps">
              <h4>Trace 步骤摘要</h4>
              <div class="trace-step-list">
                <div
                  v-for="(step, si) in ojTraceData.traceSteps"
                  :key="si"
                  class="trace-step"
                  :class="{ bug: step.isBug }"
                >
                  <span class="trace-step-line">L{{ step.line }}</span>
                  <span class="trace-step-desc">{{ step.desc }}</span>
                  <el-tag v-if="step.isBug" type="danger" size="small" effect="dark">Bug</el-tag>
                </div>
              </div>
            </div>
            <div class="oj-ai-diagnosis">
              <h4>AI 诊断建议</h4>
              <div class="diagnosis-content">
                <p>{{ ojTraceData.aiDiagnosis }}</p>
              </div>
              <div class="diagnosis-fix">
                <strong>修复建议：</strong>
                <p>{{ ojTraceData.suggestedFix }}</p>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- ===== 7. 学习评估区 ===== -->
    <section class="section">
      <h2 class="section-title">
        <el-icon><DataAnalysis /></el-icon>
        学习效果评估
      </h2>
      <div class="eval-panel">
        <el-row :gutter="16">
          <el-col :xs="24" :lg="14">
            <div class="eval-main-card">
              <div class="eval-score-block">
                <div class="eval-score-big">
                  <span class="eval-label">总掌握度</span>
                  <strong class="eval-score-num">{{ learningEvalData.overallScore }}</strong>
                  <el-tag
                    :type="learningEvalData.level === 'advanced' ? 'success' : learningEvalData.level === 'competent' ? 'primary' : learningEvalData.level === 'improving' ? 'warning' : 'danger'"
                    size="small"
                  >
                    {{ learningEvalData.levelLabel }}
                  </el-tag>
                </div>
                <div class="eval-meta-row">
                  <div class="eval-meta-item">
                    <span class="meta-label">趋势</span>
                    <el-tag
                      :type="learningEvalData.trend === 'rising' ? 'success' : learningEvalData.trend === 'falling' ? 'danger' : 'info'"
                      size="small"
                    >
                      {{ learningEvalData.trendLabel }}
                    </el-tag>
                  </div>
                  <div class="eval-meta-item">
                    <span class="meta-label">置信度</span>
                    <el-tag
                      :type="learningEvalData.confidence === 'high' ? 'success' : learningEvalData.confidence === 'medium' ? 'warning' : 'info'"
                      size="small"
                    >
                      {{ CONFIDENCE_LABELS[learningEvalData.confidence] ?? learningEvalData.confidence }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <div class="eval-dimensions">
                <h4>多维评分</h4>
                <div class="eval-dim-grid">
                  <div v-for="dim in learningEvalData.dimensions" :key="dim.key" class="eval-dim-item">
                    <span class="dim-name">{{ dim.label }}</span>
                    <el-progress
                      :percentage="dim.score"
                      :stroke-width="8"
                      :status="dim.score >= 60 ? 'success' : dim.score < 40 ? 'exception' : undefined"
                    />
                  </div>
                </div>
              </div>
              <div v-if="learningEvalData.weakSkills.length" class="eval-weak">
                <h4>薄弱技能</h4>
                <el-space wrap>
                  <el-tag v-for="s in learningEvalData.weakSkills" :key="s" type="danger" effect="plain" size="small">
                    {{ s }}
                  </el-tag>
                </el-space>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :lg="10">
            <div class="eval-strategy-card">
              <div class="strategy-head">
                <strong>Push Strategy</strong>
                <el-tag type="primary" effect="plain" size="small">
                  {{ PUSH_STRATEGY_LABELS[learningEvalData.pushStrategy] ?? learningEvalData.pushStrategy }}
                </el-tag>
              </div>
              <p class="strategy-desc">{{ learningEvalData.pathAdjustment }}</p>
              <div v-if="learningEvalData.suggestedReplan" class="replan-action">
                <el-button type="primary" plain size="small" @click="router.push({ name: 'learning-path' })">
                  建议重排路径
                </el-button>
              </div>
            </div>
            <div class="safety-mini-card">
              <div class="safety-mini-head">
                <el-icon><Lock /></el-icon>
                <span>防幻觉与安全</span>
              </div>
              <div class="safety-mini-stats">
                <div class="s-stat">
                  <strong>{{ verificationStats.passed }}</strong>
                  <span>校验通过</span>
                </div>
                <div class="s-stat warn">
                  <strong>{{ verificationStats.warning }}</strong>
                  <span>告警</span>
                </div>
                <div class="s-stat">
                  <strong>{{ verificationStats.evidenceTotal }}</strong>
                  <span>引用片段</span>
                </div>
              </div>
              <el-tag size="small" effect="plain">{{ verificationStats.riskLabel }}</el-tag>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>
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
  margin: 0 0 8px;
  font-size: clamp(1.15rem, 2.2vw, 1.5rem);
  line-height: 1.35;
  font-weight: 700;
  color: var(--alp-color-text);
}

.hero-sub {
  margin: 0 0 16px;
  color: var(--alp-color-primary);
  font-size: 15px;
  line-height: 1.6;
  font-weight: 600;
  letter-spacing: 0.5px;
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
  margin-bottom: 28px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
}

.subsection-title {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.panel {
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card, 12px);
  padding: 18px;
  margin-bottom: 16px;
}

/* ===== 闭环流程图 ===== */
.loop-flow {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0;
  padding: 20px 16px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card, 12px);
  position: relative;
}

.loop-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 110px;
  text-align: center;
}

.loop-node:hover {
  border-color: var(--alp-color-primary);
  transform: translateY(-2px);
}

.loop-node.active {
  border-color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 12%, var(--alp-bg-surface));
  box-shadow: 0 0 16px color-mix(in srgb, var(--alp-color-primary) 25%, transparent);
}

.loop-node.done {
  border-color: #10b981;
  opacity: 0.85;
}

.loop-node-icon {
  font-size: 24px;
  line-height: 1;
}

.loop-node-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.loop-node-desc {
  font-size: 10px;
  color: var(--alp-color-muted);
  line-height: 1.3;
}

.loop-arrow {
  color: var(--alp-color-muted);
  flex-shrink: 0;
  padding: 0 4px;
}

.loop-arrow-return {
  position: absolute;
  right: 16px;
  bottom: -4px;
  color: var(--alp-color-primary);
  opacity: 0.6;
}

.return-label {
  font-size: 10px;
  color: var(--alp-color-primary);
  position: absolute;
  bottom: -14px;
  right: 0;
}

/* ===== 六维画像 ===== */
.persona-panel {
  display: flex;
  gap: 24px;
  padding: 20px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card, 12px);
}

.radar-wrap {
  flex-shrink: 0;
}

.radar-svg {
  display: block;
}

.persona-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.persona-summary-text strong {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
}

.persona-summary-text p {
  margin: 0 0 6px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.dimension-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dim-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dim-label {
  width: 72px;
  font-size: 12px;
  color: var(--alp-color-text);
  flex-shrink: 0;
}

.dim-progress {
  flex: 1;
}

.confidence-overall {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--alp-bg-surface);
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
}

.confidence-overall span {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.confidence-overall strong {
  font-size: 18px;
  color: var(--alp-color-primary);
}

.confidence-progress {
  flex: 1;
}

/* ===== Agent 协同 ===== */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.agent-card {
  padding: 12px;
  border-radius: 10px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  transition: border-color 0.15s;
}

.agent-card:hover {
  border-color: var(--alp-color-primary);
}

.agent-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.agent-icon {
  font-size: 20px;
}

.agent-card-info {
  flex: 1;
  min-width: 0;
}

.agent-card-info strong {
  display: block;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-card-info small {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.agent-card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.agent-resource-type {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.agent-recent-log {
  font-size: 11px;
  color: var(--alp-color-text);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.console-panel :deep(.agent-terminal) {
  min-height: 320px;
}

/* ===== 推荐资源 ===== */
.rec-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.rec-card {
  padding: 14px;
  border-radius: 10px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-top: 3px solid var(--alp-color-primary);
  transition: transform 0.15s, border-color 0.15s;
}

.rec-card:hover {
  transform: translateY(-2px);
  border-color: var(--alp-color-primary);
}

.rec-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rec-type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.rec-title {
  flex: 1;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rec-card-meta {
  display: flex;
  gap: 6px;
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-bottom: 10px;
}

.rec-reason {
  font-size: 12px;
  line-height: 1.5;
}

.rec-reason strong {
  display: block;
  margin-bottom: 4px;
  color: var(--alp-color-primary);
  font-size: 11px;
}

.rec-reason p {
  margin: 0;
  color: var(--alp-color-muted);
}

/* ===== OJ Trace ===== */
.oj-trace-panel {
  padding: 20px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card, 12px);
}

.oj-error-card {
  padding: 14px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  border-left: 3px solid #ef4444;
}

.oj-error-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 14px;
}

.oj-error-type {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--alp-color-text);
}

.oj-failed-case {
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.oj-failed-case code {
  background: var(--alp-bg-code-ish);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  color: #f59e0b;
}

.oj-code-block {
  margin: 0;
  padding: 12px;
  background: var(--alp-bg-code-ish);
  border-radius: 8px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.6;
  color: var(--alp-color-text);
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
}

.oj-trace-steps {
  padding: 14px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  margin-bottom: 12px;
}

.oj-trace-steps h4 {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
}

.trace-step-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.trace-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  background: var(--alp-bg-soft-block);
  border: 1px solid transparent;
}

.trace-step.bug {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
}

.trace-step-line {
  font-family: 'Fira Code', monospace;
  font-size: 11px;
  color: var(--alp-color-primary);
  font-weight: 600;
  min-width: 28px;
}

.trace-step-desc {
  flex: 1;
  color: var(--alp-color-text);
}

.oj-ai-diagnosis {
  padding: 14px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  border-left: 3px solid #10b981;
}

.oj-ai-diagnosis h4 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
}

.diagnosis-content p {
  margin: 0 0 10px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.diagnosis-fix {
  font-size: 12px;
}

.diagnosis-fix strong {
  color: #10b981;
}

.diagnosis-fix p {
  margin: 4px 0 0;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

/* ===== 学习评估 ===== */
.eval-panel {
  padding: 20px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card, 12px);
}

.eval-main-card {
  padding: 18px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
}

.eval-score-block {
  margin-bottom: 16px;
}

.eval-score-big {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 10px;
}

.eval-label {
  font-size: 14px;
  color: var(--alp-color-muted);
}

.eval-score-num {
  font-size: 36px;
  color: var(--alp-color-primary);
}

.eval-meta-row {
  display: flex;
  gap: 16px;
}

.eval-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-label {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.eval-dimensions h4,
.eval-weak h4 {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
}

.eval-dim-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.eval-dim-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dim-name {
  width: 64px;
  font-size: 12px;
  color: var(--alp-color-muted);
  flex-shrink: 0;
}

.eval-weak {
  margin-top: 14px;
}

.eval-strategy-card {
  padding: 16px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  margin-bottom: 12px;
  border-left: 3px solid var(--alp-color-primary);
}

.strategy-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 14px;
}

.strategy-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.6;
}

.replan-action {
  display: flex;
  justify-content: flex-end;
}

.safety-mini-card {
  padding: 14px;
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
}

.safety-mini-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-weight: 600;
  font-size: 13px;
}

.safety-mini-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
}

.s-stat {
  text-align: center;
}

.s-stat strong {
  display: block;
  font-size: 20px;
  color: var(--alp-color-primary);
}

.s-stat span {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.s-stat.warn strong {
  color: #f59e0b;
}

@media (max-width: 768px) {
  .hero {
    padding: 20px 16px;
  }

  .persona-panel {
    flex-direction: column;
  }

  .loop-flow {
    justify-content: center;
  }

  .loop-arrow svg {
    width: 20px;
    height: 10px;
  }

  .loop-arrow-return {
    display: none;
  }

  .agent-grid {
    grid-template-columns: 1fr;
  }

  .rec-grid {
    grid-template-columns: 1fr;
  }

  .eval-dim-grid {
    grid-template-columns: 1fr;
  }
}
</style>
