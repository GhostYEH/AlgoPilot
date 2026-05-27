import { usePersonaStore } from '@/stores/pinia/persona'
import { isLoggedIn } from '@/stores/auth'

/** 清除画像缓存（画像同步成功后调用） */
export function invalidatePersonaCache() {
  usePersonaStore().invalidate()
}

async function loadProfileCached() {
  if (!isLoggedIn.value) return null
  return usePersonaStore().loadProfile()
}

/** 登录用户是否尚未完成破冰画像（无 updated_at） */
export async function needsOnboarding(): Promise<boolean> {
  if (!isLoggedIn.value) return false
  const profile = await loadProfileCached()
  if (profile === null) return false
  return !profile.updated_at
}

/** 路由守卫：允许未完成画像时访问的路由名 */
export const ONBOARDING_ALLOWED_ROUTE_NAMES = new Set([
  'login',
  'register',
  'learning-path',
  'home',
  'help',
  'stl-playground',
])
