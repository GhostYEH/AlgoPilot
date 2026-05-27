import { ElMessage } from 'element-plus'

import { ACCESS_TOKEN_KEY } from '@/constants/authStorage'
import { getApiBaseUrl } from '@/utils/apiBase'

export interface TtsSynthesizeParams {
  text: string
  voice?: string
}

export async function synthesizeTtsAudio(params: TtsSynthesizeParams): Promise<Blob> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${getApiBaseUrl()}/api/ai/tts/synthesize`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      text: params.text,
      voice: params.voice,
    }),
  })

  if (!res.ok) {
    let msg = `语音合成失败（${res.status}）`
    try {
      const data = (await res.json()) as { detail?: string }
      if (typeof data.detail === 'string') msg = data.detail
    } catch {
      const t = await res.text()
      if (t) msg = t.slice(0, 200)
    }
    ElMessage.error(msg)
    throw new Error(msg)
  }

  return res.blob()
}
