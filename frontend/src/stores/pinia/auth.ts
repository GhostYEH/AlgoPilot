import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  applyRemoteProgressPayload,
  clearLocalLearningProgress,
  exportProgressPayload,
} from '@/utils/learningStorage'
import type { UserInfo } from '@/api/auth'
import { ACCESS_TOKEN_KEY, USER_JSON_KEY } from '@/constants/authStorage'
import { usePersonaStore } from '@/stores/pinia/persona'

/** 用户级本地数据键：登出/切换账号时需清理，避免跨账号数据泄漏 */
const USER_SCOPED_STORAGE_KEYS = [
  'alp-home-activity-v1',
  'alp-oj-practice-history',
  'alp-learning-favorites-v1',
  'alp-learning-recent-v1',
]

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

const PROGRESS_OWNER_KEY = 'alp_progress_owner_user_id'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(ACCESS_TOKEN_KEY))
  const user = ref<UserInfo | null>(readUserFromStorage())

  const isLoggedIn = computed(() => !!token.value)
  const isTeacher = computed(() => user.value?.role === 'teacher')

  function getToken() {
    return token.value
  }

  function getUser() {
    return user.value
  }

  function clearRefs() {
    token.value = null
    user.value = null
  }

  function setSession(accessToken: string, u: UserInfo) {
    const owner = localStorage.getItem(PROGRESS_OWNER_KEY)
    if (owner && owner !== String(u.id)) {
      clearLocalLearningProgress()
      for (const key of USER_SCOPED_STORAGE_KEYS) {
        localStorage.removeItem(key)
      }
      // 切换账号时失效旧 persona 画像缓存
      try {
        usePersonaStore().invalidate()
      } catch {
        /* ignore */
      }
    }
    token.value = accessToken
    user.value = u
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(USER_JSON_KEY, JSON.stringify(u))
    localStorage.setItem(PROGRESS_OWNER_KEY, String(u.id))
  }

  function clearSession() {
    clearRefs()
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(USER_JSON_KEY)
    localStorage.removeItem(PROGRESS_OWNER_KEY)
    clearLocalLearningProgress()
    for (const key of USER_SCOPED_STORAGE_KEYS) {
      localStorage.removeItem(key)
    }
    // 失效 persona 画像缓存，防止跨账号读取旧画像
    try {
      usePersonaStore().invalidate()
    } catch {
      /* persona store 尚未初始化，忽略 */
    }
  }

  async function syncLearningProgressAfterAuth() {
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

  function logout() {
    clearSession()
  }

  return {
    token,
    user,
    isLoggedIn,
    isTeacher,
    getToken,
    getUser,
    clearRefs,
    setSession,
    clearSession,
    syncLearningProgressAfterAuth,
    logout,
  }
})
