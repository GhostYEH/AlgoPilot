import { getApiBaseUrl } from '@/utils/apiBase'

export interface SystemHealth {
  status: string
  llm_configured?: boolean
  trace_python?: boolean
  trace_cpp?: boolean
  cpp_compiler?: boolean
  hints?: string[]
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
