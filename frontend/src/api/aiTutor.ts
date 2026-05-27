import axios from 'axios'
import { ElMessage } from 'element-plus'

import { ACCESS_TOKEN_KEY } from '@/constants/authStorage'
import type { AiTutorSectionPayload } from '@/utils/buildLearnContext'
import { getApiBaseUrl } from '@/utils/apiBase'

const baseURL = getApiBaseUrl()

const aiClient = axios.create({
  baseURL,
  timeout: 90000,
})

aiClient.interceptors.request.use((config) => {
  const t = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (t) {
    config.headers.Authorization = `Bearer ${t}`
  }
  return config
})

export interface ChatHistoryItem {
  role: 'user' | 'assistant'
  content: string
}

export interface AiTutorChatParams {
  message: string
  history: ChatHistoryItem[]
  moduleKey: string
  moduleTitle: string
  chapterTag: string
  moduleIntro: string
  section: AiTutorSectionPayload
}

export interface AiTutorChatResult {
  reply: string
}

function toApiBody(params: AiTutorChatParams) {
  return {
    message: params.message,
    history: params.history,
    module_key: params.moduleKey,
    module_title: params.moduleTitle,
    chapter_tag: params.chapterTag,
    module_intro: params.moduleIntro,
    section: params.section,
  }
}

function authHeaders(): HeadersInit {
  const t = localStorage.getItem(ACCESS_TOKEN_KEY)
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (t) h.Authorization = `Bearer ${t}`
  return h
}

export async function postAiTutorChat(params: AiTutorChatParams): Promise<AiTutorChatResult> {
  try {
    const { data } = await aiClient.post<AiTutorChatResult>(
      '/api/ai/tutor/chat',
      toApiBody(params),
    )
    return data
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: unknown } }; message?: string }
    const detail = err.response?.data?.detail
    const msg =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('；')
          : err.message || 'AI 助教请求失败'
    ElMessage.error(msg)
    throw error
  }
}

/** 流式助教（登录后结合画像） */
export async function streamAiTutorChat(
  params: AiTutorChatParams,
  handlers: {
    onToken: (chunk: string) => void
    onDone?: (full: string) => void
    onError?: (msg: string) => void
  },
): Promise<void> {
  const res = await fetch(`${getApiBaseUrl()}/api/orchestrator/tutor/chat/stream`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(toApiBody(params)),
  })
  if (!res.ok) {
    const msg = `助教请求失败（${res.status}）`
    handlers.onError?.(msg)
    ElMessage.error(msg)
    throw new Error(msg)
  }
  const reader = res.body?.getReader()
  if (!reader) throw new Error('无法读取流')
  const decoder = new TextDecoder()
  let buf = ''
  let streamError: string | null = null
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const parts = buf.split('\n\n')
    buf = parts.pop() ?? ''
    for (const part of parts) {
      for (const line of part.split('\n')) {
        if (!line.startsWith('data:')) continue
        try {
          const ev = JSON.parse(line.slice(5).trim()) as Record<string, string>
          if (ev.type === 'token' && ev.content) handlers.onToken(ev.content)
          if (ev.type === 'done' && ev.content) handlers.onDone?.(ev.content)
          if (ev.type === 'error') {
            streamError = String(ev.message || 'AI 助教生成失败')
            handlers.onError?.(streamError)
          }
        } catch {
          /* skip */
        }
      }
    }
  }
  if (streamError) {
    ElMessage.error(streamError)
    throw new Error(streamError)
  }
}
