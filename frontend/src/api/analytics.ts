import request from '@/utils/request'

export interface EffectivenessRow {
  user_id: number
  course_id: string
  chapter_id: string
  skill_id: string
  before_mastery_score: number
  after_mastery_score: number
  mastery_delta: number
  oj_attempts: number
  oj_failures: number
  oj_accept_rate: number
  trace_diagnosis_count: number
  hint_count: number
  resource_completion_count: number
  path_adjustment_count: number
  latest_error_pattern: string
  improvement_summary: string
}

export interface EffectivenessResponse {
  rows: EffectivenessRow[]
  partial: boolean
  missing_fields: string[]
}

export async function fetchEffectiveness(params?: {
  course_id?: string
  chapter_id?: string
}): Promise<EffectivenessResponse> {
  return request.get('/api/analytics/effectiveness', {
    params: {
      course_id: params?.course_id ?? 'data_structures_algorithms',
      chapter_id: params?.chapter_id ?? '',
    },
  }) as Promise<EffectivenessResponse>
}

export function getEffectivenessCsvUrl(params?: {
  course_id?: string
  chapter_id?: string
}): string {
  const base = (request.defaults.baseURL || '') as string
  const sp = new URLSearchParams({
    course_id: params?.course_id ?? 'data_structures_algorithms',
    chapter_id: params?.chapter_id ?? '',
  })
  return `${base}/api/analytics/effectiveness/export.csv?${sp.toString()}`
}

export interface CommunityStats {
  student_count: number
  resource_count: number
  week_ac_count: number
  week_active_count: number
}

export interface CommunityLeaderboardEntry {
  rank: number
  name: string
  avatarHue: number
  score: number
  unit: string
}

export interface CommunityActivityItem {
  id: string
  user: string
  action: string
  time: string
}

export interface CommunityResponse {
  stats: CommunityStats
  ac_board: CommunityLeaderboardEntry[]
  streak_board: CommunityLeaderboardEntry[]
  feed: CommunityActivityItem[]
}

export async function fetchCommunity(): Promise<CommunityResponse> {
  return request.get('/api/analytics/community') as Promise<CommunityResponse>
}
