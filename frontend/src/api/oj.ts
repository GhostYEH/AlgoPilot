import axios from 'axios'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { ACCESS_TOKEN_KEY } from '@/constants/authStorage'
import { getApiBaseUrl } from '@/utils/apiBase'
import { buildFallbackProblem, fetchLocalProblem, fetchLocalProblemList } from '@/api/ojLocal'
import { enrichProblemStarters } from '@/utils/ojStarterCode'
import { formatOjAxiosError } from '@/utils/ojErrors'

const baseURL = getApiBaseUrl()

const judgeClient = axios.create({
  baseURL,
  timeout: 60000,
})

const ojReadClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 8000,
})

judgeClient.interceptors.request.use((config) => {
  const t = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (t) config.headers.Authorization = `Bearer ${t}`
  return config
})

judgeClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status as number | undefined
    if (status === 401) {
      ElMessage.warning('登录已过期，请重新登录后再提交')
    } else {
      ElMessage.error(formatOjAxiosError(error))
    }
    return Promise.reject(error)
  },
)

export interface ProblemListItem {
  slug: string
  title: string
  lc_id: number
  difficulty: string
  ready: boolean
  module_key?: string
  tags?: string[]
  common_errors?: string[]
}

export interface ProblemDetail {
  slug: string
  title: string
  lc_id: number
  difficulty: string
  description: string
  judge_mode?: 'stdio' | 'leetcode' | string
  entry: { class?: string; method?: string; mode?: string } | null
  starter_code: Record<string, string>
  samples: Array<{
    args?: unknown[]
    expected?: unknown
    stdin?: string
    stdout?: string
  }>
  hidden_count: number
  ready: boolean
  time_limit_ms: number
  order_insensitive: boolean
  module_key?: string
  tags?: string[]
  common_errors?: string[]
}

export type Verdict = 'AC' | 'WA' | 'TLE' | 'RE' | 'CE'

export interface CaseResult {
  index: number
  verdict: Verdict
  message: string
  input_preview: string
  expected_preview: string
  actual_preview: string | null
  runtime_ms: number | null
}

export interface JudgeResponse {
  verdict: Verdict
  passed: number
  total: number
  cases: CaseResult[]
  compile_error: string | null
  event_id?: string | null
  event_logs?: Array<{ agent: string; action: string; detail?: string; status?: string }>
}

export type OjLanguage = 'python' | 'cpp'

export async function fetchProblems(q?: string): Promise<ProblemListItem[]> {
  const query = q?.trim()
  try {
    return await request.get<unknown, ProblemListItem[]>('/api/oj/problems', {
      params: query ? { q: query } : {},
    })
  } catch {
    const local = await fetchLocalProblemList()
    if (!query) return local
    const lower = query.toLowerCase()
    return local.filter(
      (p) =>
        p.slug.toLowerCase().includes(lower) || p.title.toLowerCase().includes(lower),
    )
  }
}

export interface ResolveProblemResult {
  problem: ProblemDetail
  apiOnline: boolean
  tracePython?: boolean
  traceCpp?: boolean
}

type OjCapabilities = {
  trace_python?: boolean
  trace_cpp?: boolean
  cpp_compiler?: string | null
  gdb_available?: boolean
  gdb_path?: string | null
}

export function inferTraceCpp(caps: OjCapabilities): boolean {
  if (caps.trace_cpp === true) return true
  if (caps.trace_cpp === false) return false
  if (caps.gdb_available === true && caps.cpp_compiler) return true
  return false
}

/**
 * 加载题目：先本地 bundle（无需后端），再尝试 API 刷新；保证始终返回可展示题目。
 */
export async function resolveProblem(
  slug: string,
  meta: { title: string; lc_id?: number },
): Promise<ResolveProblemResult> {
  const local = (await fetchLocalProblem(slug)) ?? null
  let problem: ProblemDetail =
    local ?? buildFallbackProblem(slug, meta.title, meta.lc_id ?? 0)

  let apiOnline = false
  let tracePython = true
  let traceCpp = false
  try {
    await ojReadClient.get('/api/health', { timeout: 3000 })
    apiOnline = true
    try {
      const { data: caps } = await ojReadClient.get<OjCapabilities>(
        '/api/oj/capabilities',
        { timeout: 5000 },
      )
      tracePython = caps.trace_python !== false
      traceCpp = inferTraceCpp(caps)
    } catch {
      /* 能力接口失败时仍允许尝试追踪，由 trace 接口返回真实错误 */
      traceCpp = true
    }
    try {
      const { data } = await ojReadClient.get<ProblemDetail>(
        `/api/oj/problems/${encodeURIComponent(slug)}`,
      )
      problem = enrichProblemStarters(data, slug, meta.title, meta.lc_id ?? 0)
    } catch {
      problem = enrichProblemStarters(problem, slug, meta.title, meta.lc_id ?? 0)
    }
  } catch {
    apiOnline = false
    problem = enrichProblemStarters(problem, slug, meta.title, meta.lc_id ?? 0)
  }

  return { problem, apiOnline, tracePython, traceCpp }
}

/** 探测判题后端是否在线（运行/提交前可再调一次） */
export async function probeApiOnline(): Promise<boolean> {
  try {
    await ojReadClient.get('/api/health', { timeout: 3000 })
    return true
  } catch {
    return false
  }
}

/** @deprecated 使用 resolveProblem */
export async function fetchProblem(
  slug: string,
  fallback?: { title: string; lc_id?: number },
): Promise<ProblemDetail> {
  const meta = fallback ?? { title: slug, lc_id: 0 }
  const { problem } = await resolveProblem(slug, meta)
  return problem
}

export async function runSamples(slug: string, code: string, language: OjLanguage = 'python') {
  const { data } = await judgeClient.post<JudgeResponse>(
    `/api/oj/problems/${encodeURIComponent(slug)}/run`,
    { code, language },
  )
  return data
}

export async function submitCode(slug: string, code: string, language: OjLanguage = 'python') {
  const { data } = await judgeClient.post<JudgeResponse>(
    `/api/oj/problems/${encodeURIComponent(slug)}/submit`,
    { code, language },
  )
  return data
}

export type { TraceResponse, TraceStep, TraceVarSnapshot } from '@/types/codeTrace'

export async function traceExecution(
  slug: string,
  code: string,
  language: OjLanguage = 'python',
  caseIndex?: number,
) {
  const { data } = await judgeClient.post<import('@/types/codeTrace').TraceResponse>(
    `/api/oj/problems/${encodeURIComponent(slug)}/trace`,
    {
      code,
      language,
      ...(caseIndex !== undefined ? { case_index: caseIndex } : {}),
    },
  )
  return data
}

export async function traceNarration(
  slug: string,
  payload: {
    code: string
    language: OjLanguage
    steps: import('@/types/codeTrace').TraceStep[]
    problem_title?: string
  },
) {
  const { data } = await judgeClient.post<import('@/types/codeTrace').TraceResponse>(
    `/api/oj/problems/${encodeURIComponent(slug)}/trace/narrate`,
    payload,
  )
  return data
}

export async function traceBugDiagnose(
  slug: string,
  payload: {
    code: string
    language: OjLanguage
    steps: import('@/types/codeTrace').TraceStep[]
    problem_description?: string
    judge_verdict?: string
  },
) {
  const { data } = await judgeClient.post<import('@/types/codeTrace').TraceBugDiagnoseResponse>(
    `/api/oj/problems/${encodeURIComponent(slug)}/diagnose`,
    payload,
    { timeout: 90000 },
  )
  return data
}

export async function aiDiagnose(
  slug: string,
  payload: {
    code: string
    language: OjLanguage
    judge_verdict?: string
    failed_cases?: CaseResult[]
  },
) {
  const { data } = await judgeClient.post<import('@/types/codeTrace').AiDiagnoseResponse>(
    `/api/oj/problems/${encodeURIComponent(slug)}/ai/diagnose`,
    payload,
    { timeout: 120000 },
  )
  return data
}

export async function fetchTraceReport(
  slug: string,
  payload: {
    code: string
    language: OjLanguage
    judge_verdict?: string
    failed_cases?: CaseResult[]
  },
) {
  const { data } = await judgeClient.post<import('@/types/codeTrace').TraceDiagnosisReport>(
    `/api/oj/problems/${encodeURIComponent(slug)}/trace-report`,
    payload,
    { timeout: 120000 },
  )
  return data
}

export async function fetchOjCapabilities(): Promise<OjCapabilities> {
  try {
    await ojReadClient.get('/api/health', { timeout: 3000 })
    const { data } = await ojReadClient.get<OjCapabilities>('/api/oj/capabilities', {
      timeout: 5000,
    })
    return data
  } catch {
    return { trace_python: true, trace_cpp: true }
  }
}

export function practicePath(slug: string) {
  return `/practice/${slug}`
}

// ──────────────────────────── 教师 OJ 管理 ────────────────────────────

export interface AdminTestCase {
  args?: unknown[]
  expected?: unknown
  stdin?: string
  stdout?: string
  note?: string
}

export interface AdminProblemCases {
  slug: string
  title: string
  judge_mode: string
  entry: Record<string, unknown>
  samples: AdminTestCase[]
  hidden: AdminTestCase[]
}

export interface AdminChapter {
  id: string
  title: string
  difficulty: string
  module_keys: string[]
  recommended_problems: string[]
}

export interface CreateProblemPayload {
  slug: string
  title: string
  module_key?: string
  difficulty?: string
  lc_id?: number
  description?: string
  judge_mode?: string
  entry?: Record<string, unknown> | null
  starter_code?: Record<string, string> | null
  samples?: AdminTestCase[]
  hidden?: AdminTestCase[]
  tags?: string[]
  common_errors?: string[]
}

export async function fetchAdminCases(slug: string): Promise<AdminProblemCases> {
  const { data } = await judgeClient.get<AdminProblemCases>(
    `/api/oj/admin/problems/${slug}/cases`,
  )
  return data
}

export async function updateAdminCases(
  slug: string,
  samples: AdminTestCase[],
  hidden: AdminTestCase[],
): Promise<AdminProblemCases> {
  const { data } = await judgeClient.put<AdminProblemCases>(
    `/api/oj/admin/problems/${slug}/cases`,
    { samples, hidden },
  )
  return data
}

export async function fetchAdminChapters(): Promise<AdminChapter[]> {
  const { data } = await judgeClient.get<AdminChapter[]>('/api/oj/admin/chapters')
  return data
}

export async function createProblem(payload: CreateProblemPayload): Promise<unknown> {
  const { data } = await judgeClient.post('/api/oj/admin/problems', payload)
  return data
}

export async function attachProblemToChapter(
  slug: string,
  chapterId: string,
): Promise<{ chapter_id: string; slug: string; recommended_problems: string[] }> {
  const { data } = await judgeClient.post('/api/oj/admin/chapters/attach', {
    slug,
    chapter_id: chapterId,
  })
  return data
}
