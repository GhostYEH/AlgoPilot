import { ACCESS_TOKEN_KEY } from '@/constants/authStorage'

let timer: ReturnType<typeof setTimeout> | null = null

function hasAccessToken() {
  return !!localStorage.getItem(ACCESS_TOKEN_KEY)
}

/** 登录后将本地小节进度防抖同步到服务端（经后端 API，默认 SQLite 持久化） */
export function schedulePushLearningProgress() {
  if (!hasAccessToken()) return
  if (timer) clearTimeout(timer)
  timer = setTimeout(async () => {
    timer = null
    try {
      const { saveLearningProgress } = await import('@/api/learning')
      const { exportProgressPayload } = await import('@/utils/learningStorage')
      const payload = exportProgressPayload()
      await saveLearningProgress(payload as Record<string, unknown>)
      const { schedulePersonaLearningPatch } = await import('@/utils/personaLearningSync')
      schedulePersonaLearningPatch()
    } catch {
      /* ElMessage 由 axios 拦截器处理 */
    }
  }, 1200)
}
