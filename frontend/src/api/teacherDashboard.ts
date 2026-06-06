import request from '@/utils/request'

export interface ClassOverviewResponse {
  student_count: number
  avg_mastery: number
  active_rate_7d: number
  oj_accept_rate: number
  error_type_distribution: Record<string, number>
  is_demo: boolean
}

export interface WeakModuleItem {
  module_key: string
  module_label: string
  avg_mastery: number
  error_count: number
}

export interface WeakKnowledgeItem {
  knowledge_point: string
  error_count: number
  typical_error: string
}

export interface WeakProblemTypeItem {
  problem_slug: string
  problem_title: string
  wa_count: number
  tle_count: number
}

export interface WeakPointsResponse {
  weak_modules: WeakModuleItem[]
  weak_knowledge_points: WeakKnowledgeItem[]
  weak_problem_types: WeakProblemTypeItem[]
  recommended_teaching_focus: string[]
  is_demo: boolean
}

export interface ResourceStatItem {
  resource_type: string
  resource_label: string
  count: number
  usage_rate: number
  avg_feedback_score: number
}

export interface ResourceStatsResponse {
  resource_stats: ResourceStatItem[]
  recommended_supplements: string[]
  is_demo: boolean
}

export interface StrugglingStudentItem {
  user_id: number
  username: string
  consecutive_failures: number
  last_problem: string
  suggested_action: string
}

export interface HighPerformerItem {
  user_id: number
  username: string
  ac_count: number
  avg_mastery: number
  suggested_project: string
}

export interface InterventionResponse {
  struggling_students: StrugglingStudentItem[]
  class_common_issues: string[]
  suggested_topic_resources: string[]
  high_performers: HighPerformerItem[]
  is_demo: boolean
}

export async function fetchClassOverview(): Promise<ClassOverviewResponse> {
  return request.get('/api/teacher-dashboard/class-overview') as Promise<ClassOverviewResponse>
}

export async function fetchWeakPoints(): Promise<WeakPointsResponse> {
  return request.get('/api/teacher-dashboard/weak-points') as Promise<WeakPointsResponse>
}

export async function fetchResourceStats(): Promise<ResourceStatsResponse> {
  return request.get('/api/teacher-dashboard/resource-stats') as Promise<ResourceStatsResponse>
}

export async function fetchInterventions(): Promise<InterventionResponse> {
  return request.get('/api/teacher-dashboard/interventions') as Promise<InterventionResponse>
}
