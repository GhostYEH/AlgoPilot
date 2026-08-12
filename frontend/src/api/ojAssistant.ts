import axios from 'axios'
import { ElMessage } from 'element-plus'

import { getApiBaseUrl } from '@/utils/apiBase'

const baseURL = getApiBaseUrl()

const client = axios.create({
  baseURL,
  timeout: 90000,
})

export type OjAssistantMode = 'ds_hint' | 'code_hint'

export interface OjAssistantParams {
  mode: OjAssistantMode
  problemSlug: string
  problemTitle: string
  problemDescription: string
  difficulty: string
  judgeMode: string
  entryMethod?: string | null
  language: 'python' | 'cpp'
  userCode: string
  samplesText: string
}

function toBody(p: OjAssistantParams) {
  return {
    mode: p.mode,
    problem_slug: p.problemSlug,
    problem_title: p.problemTitle,
    problem_description: p.problemDescription,
    difficulty: p.difficulty,
    judge_mode: p.judgeMode,
    entry_method: p.entryMethod ?? null,
    language: p.language,
    user_code: p.userCode,
    samples_text: p.samplesText,
  }
}

export async function postOjAssistant(params: OjAssistantParams): Promise<{ reply: string }> {
  try {
    const { data } = await client.post<{ reply: string }>('/api/ai/oj/assistant', toBody(params))
    return data
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: unknown } }; message?: string }
    const detail = err.response?.data?.detail
    const msg =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('；')
          : err.message || '智能体请求失败'
    ElMessage.error(msg)
    throw error
  }
}

/**
 * 流式 OJ 助手（SSE）。
 * 通过 fetch + ReadableStream 实时消费 token，配合 onToken 回调实时渲染。
 */
export async function streamOjAssistant(
  params: OjAssistantParams,
  handlers: {
    onToken: (chunk: string) => void
    onDone?: (full: string) => void
    onError?: (msg: string) => void
  },
): Promise<void> {
  const controller = new AbortController()
  const timeoutMs = 150000
  let timer: ReturnType<typeof setTimeout> | null = null
  const resetTimeout = () => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => controller.abort(), timeoutMs)
  }
  resetTimeout()

  let res: Response
  try {
    res = await fetch(`${baseURL}/api/ai/oj/assistant/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(toBody(params)),
      signal: controller.signal,
    })
  } catch (error: unknown) {
    if (timer) clearTimeout(timer)
    const msg = 'AI 助手连接失败，请检查网络后重试'
    handlers.onError?.(msg)
    ElMessage.error(msg)
    throw error
  }
  if (!res.ok) {
    const msg = `AI 助手请求失败（${res.status}）`
    handlers.onError?.(msg)
    ElMessage.error(msg)
    throw new Error(msg)
  }
  const reader = res.body?.getReader()
  if (!reader) throw new Error('无法读取流')
  const decoder = new TextDecoder()
  let buf = ''
  let streamError: string | null = null
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      resetTimeout()
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
              streamError = String(ev.message || 'AI 助手生成失败')
              handlers.onError?.(streamError)
            }
          } catch {
            /* skip */
          }
        }
      }
    }
  } catch (error: unknown) {
    if (controller.signal.aborted) {
      const msg = 'AI 助手响应超时，请稍后重试'
      handlers.onError?.(msg)
      ElMessage.error(msg)
      throw new Error(msg)
    }
    throw error
  } finally {
    if (timer) clearTimeout(timer)
  }
  if (streamError) {
    ElMessage.error(streamError)
    throw new Error(streamError)
  }
}
