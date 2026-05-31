import { getApiBaseUrl } from '@/utils/apiBase'

export interface SystemHealth {
  status: string
  llm_configured?: boolean
  tts_configured?: boolean
  trace_python?: boolean
  trace_cpp?: boolean
  cpp_compiler?: boolean
  demo_hints?: string[]
}

export type ReadinessLevel = 'blocked' | 'risky' | 'ready' | 'excellent'

export interface A3Health {
  course_knowledge_ready: boolean
  profile_chat_ready: boolean
  persona_patch_ready: boolean
  skill_cards_ready: boolean
  resource_generation_ready: boolean
  verifier_ready: boolean
  safety_ready: boolean
  oj_trace_ready: boolean
  student_memory_ready: boolean
  mastery_ready: boolean
  learning_path_ready: boolean
  event_bus_ready: boolean
  llm_configured: boolean
  tts_configured: boolean
  trace_python?: boolean
  trace_cpp?: boolean
  readiness_score: number
  readiness_level: ReadinessLevel
  blockers: string[]
  warnings: string[]
  recommended_actions: string[]
  demo_path_recommendation: string
}

export async function fetchSystemHealth(): Promise<SystemHealth | null> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/api/health`, { cache: 'no-store' })
    if (!res.ok) return null
    return (await res.json()) as SystemHealth
  } catch {
    return null
  }
}

export async function fetchA3Health(): Promise<A3Health | null> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/api/a3/health`, { cache: 'no-store' })
    if (!res.ok) return null
    return (await res.json()) as A3Health
  } catch {
    return null
  }
}
