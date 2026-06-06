/**
 * 认证状态（Pinia）— 保留原有导出以兼容现有 import。
 */
import { computed } from 'vue'
import { storeToRefs } from 'pinia'

import type { UserInfo } from '@/api/auth'
import { useAuthStore } from '@/stores/pinia/auth'

export { useAuthStore } from '@/stores/pinia/auth'

export const isLoggedIn = computed(() => useAuthStore().isLoggedIn)

export const isTeacher = computed(() => useAuthStore().isTeacher)

export function getToken() {
  return useAuthStore().getToken()
}

export function getUser() {
  return useAuthStore().getUser()
}

export function clearRefs() {
  useAuthStore().clearRefs()
}

export function setSession(accessToken: string, u: UserInfo) {
  useAuthStore().setSession(accessToken, u)
}

export function clearSession() {
  useAuthStore().clearSession()
}

export async function syncLearningProgressAfterAuth() {
  return useAuthStore().syncLearningProgressAfterAuth()
}

export function logout() {
  useAuthStore().logout()
}

/** 在组件内使用响应式 token / user */
export function useAuthRefs() {
  const store = useAuthStore()
  return storeToRefs(store)
}
