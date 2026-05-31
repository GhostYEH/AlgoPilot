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
