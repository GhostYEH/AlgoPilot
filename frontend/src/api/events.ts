import request from '@/utils/request'
import type { AgentLogItem } from '@/api/orchestrator'

export interface LearningEventRecord {
  event_id: string
  event_type: string
  user_id: number
  course_id: string
  chapter_id: string
  skill_id: string
  payload: Record<string, unknown>
  created_at: string
  handled_by: string[]
  status: string
  agent_logs: AgentLogItem[]
  handler_errors: string[]
}

export interface EventLogQuery {
  items: LearningEventRecord[]
  total: number
}

export async function fetchRecentEvents(params?: {
  event_type?: string
  limit?: number
}): Promise<EventLogQuery> {
  return request.get('/api/events/recent', {
    params: {
      event_type: params?.event_type ?? '',
      limit: params?.limit ?? 20,
    },
  }) as Promise<EventLogQuery>
}

export async function fetchEventById(eventId: string): Promise<LearningEventRecord> {
  return request.get(`/api/events/${eventId}`) as Promise<LearningEventRecord>
}
