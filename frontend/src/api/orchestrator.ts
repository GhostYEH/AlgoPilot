import { ElMessage } from 'element-plus'

import { ACCESS_TOKEN_KEY } from '@/constants/authStorage'
import { getApiBaseUrl } from '@/utils/apiBase'
import request from '@/utils/request'
import { verificationDisplayTag } from '@/utils/verification'

export interface ChatHistoryItem {
  role: 'user' | 'assistant'
  content: string
}

export interface PersonaDimensions {
  knowledge_base: string
  cognitive_style: string
  coding_ability: string
  learning_goals: string
  error_preference: string
  grit_level: string
}

export const PROFILE_DIMENSION_LABELS: Record<keyof PersonaDimensions, string> = {
  knowledge_base: '知识基础',
  cognitive_style: '认知风格',
  coding_ability: '代码实操能力',
  learning_goals: '学习目标',
  error_preference: '易错点偏好',
  grit_level: '抗挫折心理',
}

export interface LearningEvidenceBrief {
  id: number
  event_type: string
  event_label: string
  problem_slug: string
  skill_id: string
  chapter_id: string
  summary: string
  at: string | null
}

export interface PersonaProfile {
  summary: string
  dimensions: PersonaDimensions
  updated_at: string | null
  dimension_scores?: Record<string, number>
  dimension_confidence?: Record<string, string>
  coverage_missing?: string[]
  dimension_evidence?: Record<string, string[]>
  update_reason?: string
  recent_evidence?: LearningEvidenceBrief[]
  fallback?: boolean
  fallback_reason?: string
  generated_by?: string
}

export interface PersonaChatMeta {
  fallback?: boolean
  fallback_reason?: string
  generated_by?: string
}

/** 学习证据 event_type → 来源标签与 el-tag 类型 */
export const EVIDENCE_SOURCE_META: Record<
  string,
  { label: string; tagType: 'success' | 'warning' | 'danger' | 'info' | 'primary' }
> = {
  oj_submit_fail: { label: 'OJ', tagType: 'warning' },
  oj_diagnosis: { label: 'OJ 诊断', tagType: 'danger' },
  trace_diagnosis: { label: 'Trace', tagType: 'primary' },
  evaluation_struggle: { label: '练习', tagType: 'info' },
  resource_complete: { label: '资源学习', tagType: 'success' },
  quiz_complete: { label: '练习', tagType: 'success' },
  section_done: { label: '资源学习', tagType: 'success' },
  skill_recommended: { label: '对话', tagType: 'info' },
  persona_chat: { label: '对话', tagType: 'info' },
}

/** event_type → 主要影响维度 */
export const EVIDENCE_DIMENSION_FOR_EVENT: Record<string, keyof PersonaDimensions> = {
  oj_submit_fail: 'coding_ability',
  oj_diagnosis: 'error_preference',
  trace_diagnosis: 'error_preference',
  evaluation_struggle: 'grit_level',
  resource_complete: 'knowledge_base',
  quiz_complete: 'knowledge_base',
  section_done: 'knowledge_base',
  skill_recommended: 'learning_goals',
  persona_chat: 'cognitive_style',
}

export interface PathStepItem {
  module_key: string
  rank: number
  reason: string
  phase: string
  prerequisites?: string[]
  difficulty?: string
  is_remediation?: boolean
  explain?: string
}

export interface LearningPathPlan {
  agent_name: string
  summary: string
  rationale: string
  next_module_key: string | null
  ordered_keys: string[]
  steps: PathStepItem[]
  updated_at: string | null
  remediation_inserted?: boolean
}

export interface AgentLogItem {
  agent: string
  agent_id?: string
  agent_name?: string
  action: string
  detail?: string
  status?: string
  timestamp?: string
  duration_ms?: number | null
  validation_result?: Record<string, unknown> | null
  retry_count?: number
  input_summary?: string
  output_summary?: string
  failure_reason?: string
}

export type AgentWorkflowStatus =
  | 'waiting'
  | 'running'
  | 'success'
  | 'retry'
  | 'failed'
  | 'skipped'

export interface AgentWorkflowEvent {
  agent: string
  detail: string
  agent_id: string
  agent_name: string
  stage: string
  status: AgentWorkflowStatus
  message: string
  timestamp: string
  duration_ms: number | null
  validation_result: Record<string, unknown> | null
  retry_count: number
  input_summary: string
  output_summary: string
  failure_reason: string
  resource_type?: string
  percent?: number
}

function normalizeWorkflowStatus(status: unknown): AgentWorkflowStatus {
  const value = String(status ?? '').toLowerCase()
  if (value === 'done' || value === 'passed') return 'success'
  if (value === 'warn' || value === 'retrying') return 'retry'
  if (value === 'error') return 'failed'
  if (
    value === 'waiting' ||
    value === 'running' ||
    value === 'success' ||
    value === 'retry' ||
    value === 'failed' ||
    value === 'skipped'
  ) {
    return value
  }
  return 'waiting'
}

function workflowEventFromSse(ev: Record<string, unknown>): AgentWorkflowEvent {
  const agentName = String(ev.agent_name ?? ev.agent ?? ev.agent_id ?? '')
  return {
    agent: agentName,
    detail: String(ev.detail ?? ev.message ?? ''),
    agent_id: String(ev.agent_id ?? agentName),
    agent_name: agentName,
    stage: String(ev.stage ?? ev.event_type ?? ''),
    status: normalizeWorkflowStatus(ev.status),
    message: String(ev.message ?? ev.detail ?? ''),
    timestamp: String(ev.timestamp ?? new Date().toISOString()),
    duration_ms: typeof ev.duration_ms === 'number' ? ev.duration_ms : null,
    validation_result:
      ev.validation_result && typeof ev.validation_result === 'object'
        ? (ev.validation_result as Record<string, unknown>)
        : null,
    retry_count: typeof ev.retry_count === 'number' ? ev.retry_count : 0,
    input_summary: String(ev.input_summary ?? ''),
    output_summary: String(ev.output_summary ?? ''),
    failure_reason: String(ev.failure_reason ?? ''),
    resource_type: typeof ev.resource_type === 'string' ? ev.resource_type : undefined,
    percent: typeof ev.percent === 'number' ? ev.percent : undefined,
  }
}

export interface SkillCardSummary {
  id: string
  name: string
  course_id?: string
  chapter_id?: string
  description?: string
}

export interface OjStruggleEvaluationResult {
  agent_name: string
  struggle_detected: boolean
  consecutive_failures: number
  remediation_module_key: string | null
  remediation_label: string
  planner_notified: boolean
  path_updated: boolean
  agent_logs: AgentLogItem[]
  plan_summary: string
  recommended_skill_cards?: SkillCardSummary[]
  course_id?: string
  chapter_id?: string
  matched_skill?: SkillCardSummary | null
  error_pattern?: string
  error_pattern_label?: string
  recommended_actions?: string[]
  recommended_resources?: Array<{
    resource_type: string
    topic?: string
    reason?: string
    chapter_id?: string
  }>
  memory_recorded?: boolean
  memory_event_id?: number | null
  mastery_updated?: boolean
  mastery_update_summary?: string
  path_adjustment_suggestion?: string
}

export interface GeneratedResource {
  id: number
  resource_type: string
  agent_name: string
  title: string
  content: string
  meta: Record<string, unknown>
  sources?: ResourceSource[]
  created_at: string
  verification?: Record<string, unknown> | null
  explain?: string
}

export interface ResourceSource {
  chunk_id: string
  module_id: string
  chapter_title: string
  section_title: string
  source_path: string
  relevance_score: number
  excerpt: string
}


export const RESOURCE_TYPE_META: Record<
  string,
  { label: string; agentName: string; color: string }
> = {
  document: { label: '概念讲解', agentName: 'ConceptAgent', color: '#4a6e94' },
  mindmap: { label: '知识思维导图', agentName: 'GraphAgent', color: '#8b5cf6' },
  exercises: { label: '个性化题单', agentName: 'QuizAgent', color: '#9c7a3d' },
  code_case: { label: '剧本沙盒', agentName: 'ScenarioAgent', color: '#9e5a5a' },
  trace_animation: { label: '轨迹动画', agentName: 'TraceAgent', color: '#ec4899' },
  reading: { label: '分层阅读', agentName: 'ReadingAgent', color: '#3d8a6e' },
}

export interface AgentInfo {
  id: string
  display_name: string
  role: string
  layer: string
}

export interface WorkflowStageDetail {
  stage: string
  agent: string
  label: string
  input?: string
  output?: string
}

const STAGE_IO: Record<string, WorkflowStageDetail> = {
  rag_retrieve: {
    stage: 'rag_retrieve',
    agent: 'KnowledgeRetriever',
    label: 'BM25 检索',
    input: 'topic + module_key + focus_hint',
    output: 'Top-K 知识库切片 id 列表',
  },
  agent_generate: {
    stage: 'agent_generate',
    agent: 'role_agent',
    label: '角色生成',
    input: '画像 + 知识库 + 协作上下文 / revised_hint',
    output: 'Markdown 或 JSON 正文',
  },
  content_verify: {
    stage: 'content_verify',
    agent: 'ContentVerifierAgent',
    label: '校验闭环',
    input: '正文 + 知识库片段',
    output: 'passed / draft + revised_hint',
  },
  safety_filter: {
    stage: 'safety_filter',
    agent: 'ContentSafety',
    label: '安全过滤',
    input: '校验后正文',
    output: '脱敏后正文',
  },
  persist: {
    stage: 'persist',
    agent: 'Orchestrator',
    label: '落库',
    input: 'meta.verified / meta.status',
    output: 'published 或 draft',
  },
}

export async function fetchAgentsCatalog(): Promise<{
  agents: AgentInfo[]
  resource_pipeline: Array<{ stage: string; agent: string; label: string }>
  framework_note: string
  dag_mermaid?: string
}> {
  return request.get('/api/orchestrator/agents') as Promise<{
    agents: AgentInfo[]
    resource_pipeline: Array<{ stage: string; agent: string; label: string }>
    framework_note: string
    dag_mermaid?: string
  }>
}

export function getStageDetail(stage: string): WorkflowStageDetail {
  return STAGE_IO[stage] ?? { stage, agent: stage, label: stage }
}

function authHeaders(): HeadersInit {
  const t = localStorage.getItem(ACCESS_TOKEN_KEY)
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (t) h.Authorization = `Bearer ${t}`
  return h
}

function parseSseChunk(chunk: string, onEvent: (data: Record<string, unknown>) => void): string {
  const parts = chunk.split('\n\n')
  const remainder = parts.pop() ?? ''
  for (const part of parts) {
    for (const line of part.split('\n')) {
      if (!line.startsWith('data:')) continue
      const json = line.slice(5).trim()
      if (!json) continue
      try {
        onEvent(JSON.parse(json) as Record<string, unknown>)
      } catch {
        /* skip malformed */
      }
    }
  }
  return remainder
}

async function readHttpError(res: Response, fallback: string): Promise<string> {
  let msg = `${fallback}（${res.status}）`
  try {
    const err = (await res.json()) as { detail?: unknown }
    if (err.detail) msg = String(err.detail)
  } catch {
    /* ignore */
  }
  return msg
}

async function consumeSse(
  url: string,
  body: unknown,
  onEvent: (data: Record<string, unknown>) => void,
  timeoutMs = 150000,
): Promise<void> {
  const controller = new AbortController()
  let timedOut = false
  let timeoutId: ReturnType<typeof window.setTimeout> | undefined
  const resetTimeout = () => {
    if (timeoutId) window.clearTimeout(timeoutId)
    timeoutId = window.setTimeout(() => {
      timedOut = true
      controller.abort()
    }, timeoutMs)
  }

  resetTimeout()
  try {
    const res = await fetch(`${getApiBaseUrl()}${url}`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(body),
      signal: controller.signal,
    })
    if (!res.ok) {
      throw new Error(await readHttpError(res, '请求失败'))
    }
    const reader = res.body?.getReader()
    if (!reader) throw new Error('无法读取流式响应')
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      resetTimeout()
      buf += decoder.decode(value, { stream: true })
      buf = parseSseChunk(buf, onEvent)
    }
    buf += decoder.decode()
    if (buf.trim()) parseSseChunk(`${buf}\n\n`, onEvent)
  } catch (error) {
    if (timedOut) throw new Error('生成服务超过 150 秒未返回进度，请稍后重试。')
    throw error
  } finally {
    if (timeoutId) window.clearTimeout(timeoutId)
  }
}

export async function fetchPersonaProfile(): Promise<PersonaProfile> {
  return request.get('/api/orchestrator/persona/profile') as Promise<PersonaProfile>
}

export async function fetchPersonaHistory(): Promise<ChatHistoryItem[]> {
  const r = (await request.get('/api/orchestrator/persona/history')) as { history: ChatHistoryItem[] }
  return r.history ?? []
}

export async function streamPersonaChat(
  params: { message: string; history: ChatHistoryItem[] },
  handlers: {
    onToken: (chunk: string) => void
    onDone?: (full: string, meta?: PersonaChatMeta) => void
    onError?: (msg: string) => void
  },
): Promise<void> {
  try {
    await consumeSse('/api/orchestrator/persona/chat', params, (ev) => {
      if (ev.type === 'token' && typeof ev.content === 'string') handlers.onToken(ev.content)
      if (ev.type === 'done' && typeof ev.content === 'string') {
        const meta = (ev.meta ?? {}) as PersonaChatMeta
        handlers.onDone?.(ev.content, meta)
      }
      if (ev.type === 'error') handlers.onError?.(String(ev.message ?? '对话失败'))
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : '对话失败'
    ElMessage.error(msg)
    handlers.onError?.(msg)
    throw e
  }
}

export async function fetchLearningPathPlan(): Promise<{ plan: LearningPathPlan | null }> {
  return request.get('/api/orchestrator/learning-path/plan') as Promise<{
    plan: LearningPathPlan | null
  }>
}

export async function replanLearningPath(body: {
  overall_percent: number
  modules: Array<{
    key: string
    label: string
    phase: string
    available: boolean
    percent: number
    done_count: number
    total_count: number
  }>
}): Promise<LearningPathPlan> {
  return request.post('/api/orchestrator/learning-path/replan', body, {
    timeout: 120000,
  }) as Promise<LearningPathPlan>
}

export async function evaluateOjStruggle(body: {
  module_key?: string
  problem_slug?: string
  knowledge_point?: string
  verdict?: string
  consecutive_failures: number
  error_pattern?: string
  overall_percent: number
  modules: Array<{
    key: string
    label: string
    phase: string
    available: boolean
    percent: number
    done_count: number
    total_count: number
  }>
}): Promise<OjStruggleEvaluationResult> {
  return request.post('/api/orchestrator/evaluation/oj-struggle', body, {
    timeout: 120000,
  }) as Promise<OjStruggleEvaluationResult>
}

export interface LearningEvaluation {
  agent_name: string
  overall_score: number
  dimensions: Array<{ key: string; label: string; score: number }>
  weak_module_keys: string[]
  suggestions: string[]
  narrative: string
  push_strategy: string
}

export async function patchPersonaFromLearning(body: {
  weak_module_keys?: string[]
  signals?: Array<{
    event_type: string
    module_key?: string
    detail?: string
  }>
}): Promise<PersonaProfile> {
  return request.post('/api/orchestrator/persona/patch-from-learning', body) as Promise<PersonaProfile>
}

export async function fetchRecommendedResources(params?: {
  module_key?: string
  limit?: number
}): Promise<GeneratedResource[]> {
  const r = (await request.get('/api/orchestrator/resources/recommendations', {
    params: { module_key: params?.module_key ?? '', limit: params?.limit ?? 6 },
  })) as { items: GeneratedResource[] }
  return r.items ?? []
}

export async function fetchLearningEvaluation(body: {
  overall_percent: number
  modules: Array<{
    key: string
    label: string
    phase: string
    available: boolean
    percent: number
    done_count: number
    total_count: number
  }>
}): Promise<LearningEvaluation> {
  return request.post('/api/orchestrator/evaluation', body, {
    timeout: 90000,
  }) as Promise<LearningEvaluation>
}

export async function syncPersonaFromStored(): Promise<{
  profile: PersonaProfile
  message: string
  fallback?: boolean
  fallback_reason?: string
  generated_by?: string
}> {
  return request.post('/api/orchestrator/persona/sync-from-stored', {}) as Promise<{
    profile: PersonaProfile
    message: string
    fallback?: boolean
    fallback_reason?: string
    generated_by?: string
  }>
}

export function resourceVerifyTag(meta: Record<string, unknown>): {
  label: string
  type: 'success' | 'warning' | 'info' | 'danger'
} {
  const t = verificationDisplayTag(meta)
  return { label: t.label, type: t.type }
}

export async function streamGenerateResource(
  params: {
    resource_type: string
    topic?: string
    module_key?: string
    focus_hint?: string
  },
  handlers: {
    onProgress?: (p: { percent?: number }) => void
    onWorkflow?: (w: AgentWorkflowEvent) => void
    onResource?: (r: GeneratedResource) => void
    onContentDelta?: (chunk: {
      resource_type: string
      agent_name: string
      delta: string
      attempt: number
    }) => void
    onDone?: (info?: {
      partial_failure?: boolean
      errors?: Array<{ resource_type?: string; agent_name?: string; error: string }>
    }) => void
    onError?: (msg: string, resourceType?: string) => void
  },
): Promise<void> {
  try {
    await consumeSse('/api/orchestrator/resources/generate?stream=true', params, (ev) => {
      if (ev.type === 'progress') handlers.onProgress?.(ev as { percent?: number })
      if (ev.type === 'workflow') {
        handlers.onWorkflow?.(workflowEventFromSse(ev))
      }
      if (ev.type === 'resource' && ev.resource) {
        handlers.onResource?.(ev.resource as GeneratedResource)
      }
      if (
        ev.type === 'content_delta' &&
        typeof ev.resource_type === 'string' &&
        typeof ev.delta === 'string'
      ) {
        handlers.onContentDelta?.({
          resource_type: ev.resource_type,
          agent_name: String(ev.agent_name ?? ''),
          delta: ev.delta,
          attempt: typeof ev.attempt === 'number' ? ev.attempt : 1,
        })
      }
      if (ev.type === 'done') handlers.onDone?.()
      if (ev.type === 'error') {
        const msg = String(ev.message)
        ElMessage.error(msg)
        handlers.onError?.(
          msg,
          typeof ev.resource_type === 'string' ? ev.resource_type : undefined,
        )
      }
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : '生成失败'
    ElMessage.error(msg)
    handlers.onError?.(msg)
    throw e
  }
}

/** @deprecated 优先使用 streamGenerateResource */
export async function generateResource(params: {
  resource_type: string
  topic?: string
  module_key?: string
  focus_hint?: string
}): Promise<GeneratedResource> {
  return new Promise((resolve, reject) => {
    streamGenerateResource(params, {
      onResource: resolve,
      onError: reject,
    }).catch(reject)
  })
}

export async function deleteResource(resourceId: number): Promise<void> {
  await request.delete(`/api/orchestrator/resources/${resourceId}`)
}

export async function setResourceFavorite(
  resourceId: number,
  favorited: boolean,
): Promise<GeneratedResource> {
  const r = (await request.patch(
    `/api/orchestrator/resources/${resourceId}/favorite`,
    null,
    { params: { favorited } },
  )) as { resource: GeneratedResource }
  return r.resource
}

export async function fetchResources(): Promise<GeneratedResource[]> {
  const r = (await request.get('/api/orchestrator/resources')) as { items: GeneratedResource[] }
  return r.items ?? []
}

export interface TrustEvidence {
  resource_id: number
  agent_name: string
  agent_role: string
  profile_summary: string
  knowledge_chunks: Array<{
    chunk_id: string
    title: string
    snippet: string
    module_id?: string
    chapter_title?: string
    section_title?: string
    source_path?: string
    relevance_score?: number
  }>
  verifier_status: 'passed' | 'warning' | 'failed'
  safety_status: 'passed' | 'warning' | 'failed'
  retry_count: number
  used_fallback: boolean
  fallback_reason: string
  generated_at: string
  content_hash: string
  version: number
  human_review: 'pending' | 'not_required' | 'approved' | 'rejected'
  timeline: Array<{ stage: string; agent: string; status: 'passed' | 'warning' | 'failed'; detail: string; timestamp: string }>
  hallucination_risks: string[]
  unsupported_claims: string[]
  final_decision: 'publish' | 'draft' | 'blocked'
}

export async function fetchResourceEvidence(resourceId: number): Promise<TrustEvidence> {
  return request.get(`/api/orchestrator/resources/${resourceId}/evidence`) as Promise<TrustEvidence>
}

export async function streamGenerateAllResources(
  params: { topic: string; module_key?: string; focus_hint?: string },
  handlers: {
    onProgress?: (p: {
      step: number
      total: number
      resource_type?: string
      agent_name?: string
      label?: string
      percent?: number
      parallel?: boolean
    }) => void
    onWorkflow?: (w: AgentWorkflowEvent) => void
    onCollaboration?: (
      log: Array<{ agent: string; action: string; detail: string; role?: string; status?: string }>,
    ) => void
    onAgentLogs?: (
      logs: Array<{ agent: string; action: string; detail?: string; role?: string; status?: string }>,
    ) => void
    onResource?: (r: GeneratedResource) => void
    onContentDelta?: (chunk: {
      resource_type: string
      agent_name: string
      delta: string
      attempt: number
    }) => void
    onDone?: (info?: {
      partial_failure?: boolean
      reused_count?: number
      fallback_mode?: boolean
      fallback_reason?: string
      errors?: Array<{ resource_type?: string; agent_name?: string; error: string }>
    }) => void
    onHeartbeat?: (info: { message: string; percent?: number; timestamp?: string }) => void
    onError?: (msg: string, resourceType?: string) => void
  },
): Promise<void> {
  try {
    await consumeSse('/api/orchestrator/resources/generate-all', params, (ev) => {
      if (ev.type === 'heartbeat') {
        handlers.onHeartbeat?.({
          message: String(ev.message ?? ''),
          percent: typeof ev.percent === 'number' ? ev.percent : undefined,
          timestamp: typeof ev.timestamp === 'string' ? ev.timestamp : undefined,
        })
      }
      if (ev.type === 'progress') {
        handlers.onProgress?.(ev as Parameters<NonNullable<typeof handlers.onProgress>>[0])
      }
      if (ev.type === 'workflow') {
        handlers.onWorkflow?.(workflowEventFromSse(ev))
      }
      if (ev.type === 'collaboration') {
        if (Array.isArray(ev.log)) {
          handlers.onCollaboration?.(
            ev.log as Array<{ agent: string; action: string; detail: string }>,
          )
        }
        if (Array.isArray(ev.agent_logs)) {
          handlers.onAgentLogs?.(
            ev.agent_logs as Array<{
              agent: string
              action: string
              detail?: string
              role?: string
              status?: string
            }>,
          )
        }
      }
      if (ev.type === 'resource' && ev.resource) {
        handlers.onResource?.(ev.resource as GeneratedResource)
        if (Array.isArray(ev.agent_logs)) {
          handlers.onAgentLogs?.(
            ev.agent_logs as Array<{
              agent: string
              action: string
              detail?: string
              role?: string
              status?: string
            }>,
          )
        }
      }
      if (
        ev.type === 'content_delta' &&
        typeof ev.resource_type === 'string' &&
        typeof ev.delta === 'string'
      ) {
        handlers.onContentDelta?.({
          resource_type: ev.resource_type,
          agent_name: String(ev.agent_name ?? ''),
          delta: ev.delta,
          attempt: typeof ev.attempt === 'number' ? ev.attempt : 1,
        })
      }
      if (ev.type === 'done') {
        handlers.onDone?.({
          partial_failure: ev.partial_failure === true,
          reused_count: typeof ev.reused_count === 'number' ? ev.reused_count : undefined,
          fallback_mode: ev.fallback_mode === true,
          fallback_reason:
            typeof ev.fallback_reason === 'string' ? ev.fallback_reason : undefined,
          errors: Array.isArray(ev.errors)
            ? (ev.errors as Array<{ resource_type?: string; agent_name?: string; error: string }>)
            : undefined,
        })
        if (Array.isArray(ev.agent_logs)) {
          handlers.onAgentLogs?.(
            ev.agent_logs as Array<{
              agent: string
              action: string
              detail?: string
              role?: string
              status?: string
            }>,
          )
        }
      }
      if (ev.type === 'error') {
        const msg = String(ev.message)
        ElMessage.error(msg)
        handlers.onError?.(
          msg,
          typeof ev.resource_type === 'string' ? ev.resource_type : undefined,
        )
      }
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : '生成失败'
    ElMessage.error(msg)
    handlers.onError?.(msg)
    throw e
  }
}
