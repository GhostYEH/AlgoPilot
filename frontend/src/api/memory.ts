import request from '@/utils/request'

import type { LearningEvidenceBrief } from '@/api/orchestrator'

export interface MemorySummary {
  course_id: string
  learning_memory_summary: string
  weak_patterns: string[]
  recent_count: number
  dimension_evidence: Record<string, string[]>
  update_reason: string
  recent_evidence: LearningEvidenceBrief[]
  generated_at: string
}

export interface GamePracticePayload {
  event_type: 'gamified_practice_complete'
  course_id: string
  chapter_id: string
  skill_id: string
  game_id: string
  level: string
  module_key: string
  success: boolean
  score: number
  attempts: number
  time_spent_seconds: number
  evidence_text: string
}

export async function fetchMemorySummary(params?: {
  course_id?: string
  limit?: number
}): Promise<MemorySummary> {
  return request.get('/api/memory/summary', {
    params: {
      course_id: params?.course_id ?? 'data_structures_algorithms',
      limit: params?.limit ?? 12,
    },
  }) as Promise<MemorySummary>
}

export async function recordGamePractice(payload: GamePracticePayload): Promise<void> {
  await request.post('/api/memory/events', {
    event_type: payload.event_type,
    course_id: payload.course_id,
    chapter_id: payload.chapter_id,
    skill_id: payload.skill_id,
    problem_slug: `game:${payload.game_id}:${payload.level}`,
    trace_summary: payload.evidence_text || `游戏 ${payload.game_id} 关卡 ${payload.level} ${payload.success ? '通关' : '未通关'}`,
    mastery_delta: payload.success ? 1 : 0,
    evidence_json: {
      game_id: payload.game_id,
      level: payload.level,
      module_key: payload.module_key,
      success: payload.success,
      score: payload.score,
      attempts: payload.attempts,
      time_spent_seconds: payload.time_spent_seconds,
      evidence_text: payload.evidence_text,
      persona_dimension: 'knowledge_base',
    },
  })
}
