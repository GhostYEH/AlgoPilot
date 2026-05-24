import { computed, ref } from 'vue'

import { applyRemoteProgressPayload, exportProgressPayload } from '@/utils/learningStorage'
import type { UserInfo } from '@/api/auth'
import { ACCESS_TOKEN_KEY, USER_JSON_KEY } from '@/constants/authStorage'

const token = ref<string | null>(localStorage.getItem(ACCESS_TOKEN_KEY))
const user = ref<UserInfo | null>(null)

function readUserFromStorage(): UserInfo | null {
  try {
    const raw = localStorage.getItem(USER_JSON_KEY)
    if (!raw) return null
    const o = JSON.parse(raw) as unknown
    if (!o || typeof o !== 'object' || !('id' in o) || !('username' in o)) return null
    return o as UserInfo
  } catch {
    return null
  }
}

user.value = readUserFromStorage()

export const isLoggedIn = computed(() => !!token.value)

export function getToken() {
  return token.value
}

export function getUser() {
  return user.value
}

/** 仅清空内存态（与 localStorage 清除配合，供请求层避免循环依赖） */
export function clearRefs() {
  token.value = null
  user.value = null
}

export function setSession(accessToken: string, u: UserInfo) {
  token.value = accessToken
  user.value = u
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(USER_JSON_KEY, JSON.stringify(u))
}

export function clearSession() {
  clearRefs()
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(USER_JSON_KEY)
}

/** 登录/注册成功后：拉取或上传学习进度并与本地合并 */
export async function syncLearningProgressAfterAuth() {
  if (!token.value) return
  try {
    const { fetchLearningProgress, saveLearningProgress } = await import('@/api/learning')
    const remote = await fetchLearningProgress()
    const serverPayload = remote.payload || {}
    const localPayload = exportProgressPayload()
    const serverEmpty = Object.keys(serverPayload).length === 0
    const localEmpty = Object.keys(localPayload).length === 0

    if (!serverEmpty) {
      applyRemoteProgressPayload(serverPayload as Record<string, unknown>)
    }
    if (serverEmpty && !localEmpty) {
      await saveLearningProgress(localPayload as Record<string, unknown>)
    }
    if (!serverEmpty && !localEmpty) {
      const merged = exportProgressPayload()
      await saveLearningProgress(merged as Record<string, unknown>)
    }
  } catch {
    /* request 拦截器已提示 */
  }
}

export function logout() {
  clearSession()
}
