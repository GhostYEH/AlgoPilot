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
