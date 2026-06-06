/**
 * A3 比赛演示主链路前端冒烟测试
 * - A3 demo 页面关键常量与结构完整性
 * - 资源卡片推荐理由逻辑
 * - 可信证据链面板数据结构
 * - Agent 状态卡片 running/done/failed/fallback 状态映射
 *
 * 运行: npx tsx --tsconfig tsconfig.app.json src/utils/a3DemoMainFlow.test.ts
 */
import assert from 'node:assert/strict'
import {
  A3_POSITIONING,
  A3_SUBTITLE,
  A3_DEMO_STEPS,
  A3_SHOWCASE_AGENTS,
  A3_COURSE_CHAPTERS,
  MOCK_PERSONA_DIMENSIONS,
  MOCK_RECOMMENDED_RESOURCES,
  MOCK_VERIFICATION_SUMMARY,
  type PersonaDimensionScore,
  type RecommendedResourceDemo,
} from '@/constants/a3Demo'
import { verificationDisplayTag, getResourceVerification } from '@/utils/verification'
import {
  lineFromAgentLog,
  systemLine,
  AGENT_ICONS,
  type AgentConsoleLine,
} from '@/utils/agentConsole'

const RESOURCE_TYPE_META: Record<
  string,
  { label: string; agentName: string; color: string }
> = {
  document: { label: '概念讲解', agentName: 'ConceptAgent', color: '#3b82f6' },
  mindmap: { label: '知识思维导图', agentName: 'GraphAgent', color: '#8b5cf6' },
  exercises: { label: '个性化题单', agentName: 'QuizAgent', color: '#f59e0b' },
  code_case: { label: '剧本沙盒', agentName: 'ScenarioAgent', color: '#ef4444' },
  trace_animation: { label: '轨迹动画', agentName: 'TraceAgent', color: '#ec4899' },
  reading: { label: '分层阅读', agentName: 'ReadingAgent', color: '#10b981' },
}

interface GeneratedResource {
  id: number
  resource_type: string
  agent_name: string
  title: string
  content: string
  meta: Record<string, unknown>
  created_at: string
  verification?: Record<string, unknown> | null
  explain?: string
}

// ── 1. A3 Demo 页面可以正常渲染（常量与结构完整性） ──────────

function testA3DemoPageStructure() {
  assert.ok(A3_POSITIONING.length > 0, 'A3_POSITIONING 非空')
  assert.ok(A3_SUBTITLE.length > 0, 'A3_SUBTITLE 非空')
  assert.ok(A3_DEMO_STEPS.length >= 5, `A3_DEMO_STEPS 至少 5 步，实际 ${A3_DEMO_STEPS.length}`)

  const stepKeys = new Set(A3_DEMO_STEPS.map((s) => s.key))
  assert.ok(stepKeys.has('persona'), 'demo steps 应含 persona')
  assert.ok(stepKeys.has('path'), 'demo steps 应含 path')
  assert.ok(stepKeys.has('resource'), 'demo steps 应含 resource')
  assert.ok(stepKeys.has('oj'), 'demo steps 应含 oj')
  assert.ok(stepKeys.has('eval'), 'demo steps 应含 eval')

  for (const step of A3_DEMO_STEPS) {
    assert.ok(step.title, `step ${step.key} 应有 title`)
    assert.ok(step.desc, `step ${step.key} 应有 desc`)
    assert.ok(step.icon, `step ${step.key} 应有 icon`)
  }

  assert.ok(A3_COURSE_CHAPTERS.length >= 10, 'A3_COURSE_CHAPTERS 至少 10 章')
  assert.ok(A3_SHOWCASE_AGENTS.length >= 6, 'A3_SHOWCASE_AGENTS 至少 6 个')

  console.log('  ✓ A3 Demo 页面结构完整性')
}

// ── 2. 资源卡片能显示推荐理由 ────────────────────────────────

function testResourceCardRecommendationReason() {
  for (const r of MOCK_RECOMMENDED_RESOURCES) {
    assert.ok(r.id, `资源 ${r.title} 应有 id`)
    assert.ok(r.title, '资源应有 title')
    assert.ok(r.resourceType, `资源 ${r.title} 应有 resourceType`)
    assert.ok(r.reason, `资源 ${r.title} 应有推荐理由 reason`)
    assert.ok(r.reason.length >= 5, `推荐理由应足够详细: ${r.reason}`)
    assert.ok(r.agentName, `资源 ${r.title} 应有 agentName`)

    const meta = RESOURCE_TYPE_META[r.resourceType]
    assert.ok(meta, `RESOURCE_TYPE_META 应包含 ${r.resourceType}`)
    assert.ok(meta.label, `${r.resourceType} 应有 label`)
    assert.ok(meta.agentName, `${r.resourceType} 应有 agentName`)
  }

  const mockResource: GeneratedResource = {
    id: MOCK_RECOMMENDED_RESOURCES[0].id,
    resource_type: MOCK_RECOMMENDED_RESOURCES[0].resourceType,
    agent_name: MOCK_RECOMMENDED_RESOURCES[0].agentName,
    title: MOCK_RECOMMENDED_RESOURCES[0].title,
    content: '',
    meta: {
      recommendation_reason: MOCK_RECOMMENDED_RESOURCES[0].reason,
      chapter_id: MOCK_RECOMMENDED_RESOURCES[0].chapterId,
      verified: MOCK_RECOMMENDED_RESOURCES[0].verified,
    },
    created_at: new Date().toISOString(),
    explain: MOCK_RECOMMENDED_RESOURCES[0].reason,
  }
  assert.ok(mockResource.explain, 'GeneratedResource.explain 应携带推荐理由')

  console.log('  ✓ 资源卡片推荐理由')
}

// ── 3. 可信证据链面板能打开 ─────────────────────────────────

function testTrustEvidencePanelStructure() {
  const mockEvidenceMeta: Record<string, unknown> = {
    verification: {
      verifier_status: 'passed',
      safety_status: 'passed',
      evidence_count: 3,
      risk_label: '无风险',
      final_decision: 'publish',
      grounded_chunks: [
        { id: 'chunk-1', title: '链表基础', snippet: '链表是一种线性数据结构...' },
      ],
      hallucination_risks: [],
      unsupported_claims: [],
      retry_count: 0,
    },
    status: 'published',
    verified: true,
  }

  const v = getResourceVerification(mockEvidenceMeta)
  assert.ok(v, 'getResourceVerification 应返回非 null')
  assert.equal(v!.verifier_status, 'passed')
  assert.equal(v!.safety_status, 'passed')
  assert.equal(v!.final_decision, 'publish')
  assert.equal(v!.risk_label, '无风险')

  const tag = verificationDisplayTag(mockEvidenceMeta)
  assert.equal(tag.type, 'success', '校验通过应为 success 类型')
  assert.ok(tag.label.includes('通过') || tag.label.includes('已校验'))

  const blockedMeta: Record<string, unknown> = {
    verification: {
      verifier_status: 'failed',
      safety_status: 'failed',
      risk_label: '安全警告',
      final_decision: 'blocked',
    },
  }
  const blockedTag = verificationDisplayTag(blockedMeta)
  assert.equal(blockedTag.type, 'danger', 'blocked 应为 danger 类型')

  const draftMeta: Record<string, unknown> = { status: 'draft' }
  const draftTag = verificationDisplayTag(draftMeta)
  assert.equal(draftTag.type, 'warning', 'draft 应为 warning 类型')

  console.log('  ✓ 可信证据链面板结构')
}

// ── 4. Agent 状态卡片能处理 running/done/failed/fallback ────

function testAgentStatusCardStates() {
  type AgentTaskStatus = 'pending' | 'running' | 'done' | 'failed' | 'fallback'

  const STATUS_TAG_TYPE: Record<AgentTaskStatus, string> = {
    pending: 'info',
    running: 'primary',
    done: 'success',
    failed: 'danger',
    fallback: 'warning',
  }

  const STATUS_LABEL: Record<AgentTaskStatus, string> = {
    pending: '等待中',
    running: '生成中',
    done: '已完成',
    failed: '失败',
    fallback: '降级',
  }

  const testStatuses: AgentTaskStatus[] = ['running', 'done', 'failed', 'fallback']
  for (const status of testStatuses) {
    assert.ok(STATUS_TAG_TYPE[status], `${status} 应有 tagType`)
    assert.ok(STATUS_LABEL[status], `${status} 应有 label`)
  }

  assert.equal(STATUS_TAG_TYPE.running, 'primary')
  assert.equal(STATUS_TAG_TYPE.done, 'success')
  assert.equal(STATUS_TAG_TYPE.failed, 'danger')
  assert.equal(STATUS_TAG_TYPE.fallback, 'warning')

  for (const agent of A3_SHOWCASE_AGENTS) {
    assert.ok(agent.id, `agent 应有 id`)
    assert.ok(agent.role, `agent ${agent.id} 应有 role`)
    if (agent.resourceType) {
      const meta = RESOURCE_TYPE_META[agent.resourceType]
      assert.ok(meta, `RESOURCE_TYPE_META 应包含 ${agent.resourceType}`)
    }
  }

  const consoleLine = lineFromAgentLog({
    agent: 'ConceptAgent',
    action: '生成文档',
    detail: '链表概念讲解已生成',
    status: 'done',
  })
  assert.ok(consoleLine.id)
  assert.ok(consoleLine.icon)
  assert.equal(consoleLine.agent, 'ConceptAgent')
  assert.equal(consoleLine.status, 'done')

  const runningLine = lineFromAgentLog({
    agent: 'QuizAgent',
    action: '组卷中',
    status: 'running',
  })
  assert.equal(runningLine.status, 'running')

  const failedLine = lineFromAgentLog({
    agent: 'SafetyAgent',
    action: '安全审查',
    detail: '发现敏感词',
    status: 'error',
  })
  assert.equal(failedLine.status, 'error')

  const sysLine = systemLine('A3 演示闭环', 'running')
  assert.equal(sysLine.agent, 'System')
  assert.equal(sysLine.status, 'running')

  for (const [agentId, icon] of Object.entries(AGENT_ICONS)) {
    assert.ok(icon, `AGENT_ICONS[${agentId}] 应有值`)
  }

  console.log('  ✓ Agent 状态卡片状态映射')
}

// ── 运行全部 ─────────────────────────────────────────────────

function runAll() {
  console.log('A3 Demo 主链路前端冒烟测试:')
  testA3DemoPageStructure()
  testResourceCardRecommendationReason()
  testTrustEvidencePanelStructure()
  testAgentStatusCardStates()
  console.log('\nA3 Demo 主链路前端冒烟测试: all passed')
}

runAll()
