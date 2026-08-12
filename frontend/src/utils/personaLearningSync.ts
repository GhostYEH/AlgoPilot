import { ACCESS_TOKEN_KEY } from '@/constants/authStorage'
import { buildLearningOverview } from '@/utils/learningOverview'

let timer: ReturnType<typeof setTimeout> | null = null

function hasToken() {
  return !!localStorage.getItem(ACCESS_TOKEN_KEY)
}

/** 随学随新：将本地进度薄弱模块与学习信号同步到画像（防抖） */
export function schedulePersonaLearningPatch(extra?: {
  event_type?: 'section_done' | 'oj_submit' | 'module_visit'
  module_key?: string
  detail?: string
}) {
  if (!hasToken()) return
  if (timer) clearTimeout(timer)
  timer = setTimeout(async () => {
    timer = null
    try {
      const { patchPersonaFromLearning } = await import('@/api/orchestrator')
      const overview = buildLearningOverview()
      const weak = overview.weakModules.map((m) => m.key)
      const signals = extra?.event_type
        ? [
            {
              event_type: extra.event_type,
              module_key: extra.module_key ?? '',
              detail: extra.detail ?? '',
            },
          ]
        : []
      await patchPersonaFromLearning({
        weak_module_keys: weak,
        signals,
      })
    } catch {
      /* 静默失败，不打扰学习流程 */
    }
  }, 2000)
}
