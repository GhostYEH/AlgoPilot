import request from '@/utils/request'

export type MasteryLevel = 'beginner' | 'improving' | 'competent' | 'advanced'
export type MasteryTrend = 'rising' | 'stable' | 'falling'
export type ConfidenceLevel = 'low' | 'medium' | 'high'

export interface MasteryEvidenceItem {
  source: string
  detail: string
  at?: string | null
}

export interface MasteryComponentScore {
  key: string
  label: string
  score: number
  weight: number
  weighted: number
  data_available: boolean
  note: string
}

export interface MasteryResourceHint {
  resource_type: string
  topic: string
  reason: string
}

export interface MasteryReport {
  user_id: number
  course_id: string
  chapter_id: string
  chapter_title: string
  mastery_score: number
  mastery_level: MasteryLevel
  weak_skills: string[]
  strong_skills: string[]
  evidence: MasteryEvidenceItem[]
  component_scores: MasteryComponentScore[]
  recommended_actions: string[]
  recommended_resources: MasteryResourceHint[]
  path_adjustment_suggestion: string
  mastery_probability: number
  mastery_trend: MasteryTrend
  confidence_level: ConfidenceLevel
  probability_explanation: string
  updated_at: string
}

export interface MasteryOverview {
  course_id: string
  overall_score: number
  overall_level: MasteryLevel
  report: MasteryReport | null
  chapters: MasteryReport[]
  updated_at: string
}

export const MASTERY_LEVEL_LABELS: Record<MasteryLevel, string> = {
  beginner: '入门',
  improving: '提升中',
  competent: '达标',
  advanced: '优秀',
}

export const MASTERY_TREND_LABELS: Record<MasteryTrend, string> = {
  rising: '上升',
  stable: '平稳',
  falling: '下降',
}

export const CONFIDENCE_LEVEL_LABELS: Record<ConfidenceLevel, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

export async function fetchMasteryReport(params?: {
  course_id?: string
  chapter_id?: string
}): Promise<MasteryOverview> {
  return request.get('/api/mastery/report', {
    params: {
      course_id: params?.course_id ?? 'data_structures_algorithms',
      chapter_id: params?.chapter_id ?? '',
    },
  }) as Promise<MasteryOverview>
}

export async function recalculateMastery(body: {
  course_id?: string
  chapter_id?: string
  overall_percent?: number
  modules?: Array<{
    key: string
    label: string
    phase: string
    available: boolean
    percent: number
    done_count: number
    total_count: number
  }>
}): Promise<{ ok: boolean; overview: MasteryOverview }> {
  return request.post('/api/mastery/recalculate', {
    course_id: body.course_id ?? 'data_structures_algorithms',
    chapter_id: body.chapter_id ?? '',
    overall_percent: body.overall_percent ?? 0,
    modules: body.modules ?? [],
  }) as Promise<{ ok: boolean; overview: MasteryOverview }>
}
