import axios from 'axios'

import { ACCESS_TOKEN_KEY } from '@/constants/authStorage'
import { getApiBaseUrl } from '@/utils/apiBase'

const baseURL = getApiBaseUrl()

const ttsClient = axios.create({
  baseURL,
  timeout: 60000,
  responseType: 'blob',
})

ttsClient.interceptors.request.use((config) => {
  const t = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (t) {
    config.headers.Authorization = `Bearer ${t}`
  }
  return config
})

export interface TtsSynthesizeParams {
  /** 待合成文本（1-3000 字符） */
  text: string
  /** 发音人 vcn，可选；默认由后端使用讯飞 x4_xiaoyan */
  voice?: string
}

/**
 * 调用后端已注册的 /api/ai/tts/synthesize 合成 MP3 音频流，返回 Blob。
 * 调用方可通过 `URL.createObjectURL(blob)` 生成 <audio> src。
 */
export async function synthesizeTTS(params: TtsSynthesizeParams): Promise<Blob> {
  const { data } = await ttsClient.post<Blob>(
    '/api/ai/tts/synthesize',
    {
      text: params.text,
      voice: params.voice ?? null,
    },
  )
  return data
}

/** 提取纯文本：去掉 markdown 围栏/标记，便于 TTS 朗读 */
export function plainTextForTts(raw: string): string {
  let s = raw
  // 去掉代码围栏（含 mermaid）的代码内容，仅保留围栏前后的文字
  s = s.replace(/```[\s\S]*?```/g, '（代码块）')
  // 去掉行内代码
  s = s.replace(/`([^`]+)`/g, '$1')
  // 去掉 markdown 标题井号
  s = s.replace(/^#{1,6}\s+/gm, '')
  // 去掉粗体/斜体标记
  s = s.replace(/\*\*(.+?)\*\*/g, '$1')
  s = s.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1$2')
  // 去掉删除线
  s = s.replace(/~~([^~]+)~~/g, '$1')
  // 去掉图片
  s = s.replace(/!\[[^\]]*\]\([^)]+\)/g, '')
  // 链接只保留文字
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '$1')
  // 列表标记
  s = s.replace(/^[•\-*+]\s+/gm, '')
  s = s.replace(/^\d+\.\s+/gm, '')
  // 引用块
  s = s.replace(/^>\s?/gm, '')
  // 水平线
  s = s.replace(/^(---|\*\*\*|___)\s*$/gm, '')
  // 压缩多余空白
  s = s.replace(/\n{3,}/g, '\n\n').trim()
  // 截断到 3000 字符（与后端 schema 一致）
  if (s.length > 3000) s = s.slice(0, 3000)
  return s
}
