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
