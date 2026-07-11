import request from '@/utils/request'

export interface ClassLearningOverview {
  student_count: number
  profile_count: number
  average_mastery: number
  resource_count: number
  oj_submission_count: number
}

export interface WeakKnowledgePoint {
  module_key: string
  module_label: string
  error_count: number
  affected_students: number
}

export interface ErrorTypeStat {
  error_type: string
  label: string
  count: number
  percentage: number
}

export interface TeachingSuggestion {
  title: string
  reason: string
  focus: string
}

export interface RecommendedOjProblem {
  slug: string
  title: string
}

export interface ReinforcementPack {
  module_key: string
  module_label: string
  resource_types: string[]
  oj_problems: RecommendedOjProblem[]
}

export interface TeacherDashboardSummary {
  overview: ClassLearningOverview
  weak_knowledge_points: WeakKnowledgePoint[]
  error_types: ErrorTypeStat[]
  teaching_suggestions: TeachingSuggestion[]
  reinforcement_packs: ReinforcementPack[]
  data_note: string
  generated_at: string
}

export function fetchTeacherDashboardSummary() {
  return request.get<unknown, TeacherDashboardSummary>('/api/teacher/dashboard-summary')
}

// ==================== 学情管理：学生花名册 ====================

export interface StudentRosterItem {
  user_id: number
  username: string
  created_at: string
  mastery_score: number
  progress_percent: number
  profile_summary: string
  oj_submissions: number
  oj_accepted: number
  resource_count: number
  weak_modules: string[]
  last_active: string
}

export interface StudentRosterResponse {
  total: number
  students: StudentRosterItem[]
  generated_at: string
}

export interface StudentDetailModuleProgress {
  module_key: string
  module_label: string
  percent: number
  mastery_score: number
}

export interface StudentDetailResponse {
  user_id: number
  username: string
  created_at: string
  mastery_score: number
  progress_percent: number
  profile_summary: string
  profile_dimensions: Record<string, unknown>
  oj_submissions: number
  oj_accepted: number
  resource_count: number
  weak_modules: string[]
  last_active: string
  module_progress: StudentDetailModuleProgress[]
  recent_memories: Array<Record<string, unknown>>
}

export function fetchStudentRoster() {
  return request.get<unknown, StudentRosterResponse>('/api/teacher/students')
}

export function fetchStudentDetail(userId: number) {
  return request.get<unknown, StudentDetailResponse>(`/api/teacher/students/${userId}`)
}

// ==================== OJ 学情分析 ====================

export interface OjProblemStat {
  slug: string
  title: string
  module_key: string
  module_label: string
  difficulty: string
  total_submissions: number
  accepted: number
  acceptance_rate: number
  common_errors: string[]
}

export interface OjModuleStat {
  module_key: string
  module_label: string
  total_submissions: number
  accepted: number
  acceptance_rate: number
}

export interface OjAnalyticsResponse {
  total_submissions: number
  accepted: number
  acceptance_rate: number
  active_students: number
  per_problem: OjProblemStat[]
  per_module: OjModuleStat[]
  generated_at: string
}

export function fetchOjAnalytics() {
  return request.get<unknown, OjAnalyticsResponse>('/api/teacher/oj-analytics')
}
