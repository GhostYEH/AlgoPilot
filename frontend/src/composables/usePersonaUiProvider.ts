import { computed, inject, provide, watch, type ComputedRef, type InjectionKey } from 'vue'

import { fetchPersonaProfile } from '@/api/orchestrator'
import { derivePersonaUiSettings, type PersonaUiSettings } from '@/composables/usePersonaUiDensity'
import { isLoggedIn } from '@/stores/auth'
import { usePersonaStore } from '@/stores/pinia/persona'

export const PERSONA_UI_KEY: InjectionKey<ComputedRef<PersonaUiSettings>> = Symbol('personaUi')

/** 在 MainLayout 调用一次，向子路由注入画像驱动 UI 设置 */
export function providePersonaUi() {
  const personaStore = usePersonaStore()

  watch(
    () => isLoggedIn.value,
    (logged) => {
      if (logged) void personaStore.loadProfile()
      else personaStore.invalidate()
    },
    { immediate: true },
  )

  const settings = computed(() =>
    derivePersonaUiSettings(personaStore.profile?.dimension_scores),
  )

  provide(PERSONA_UI_KEY, settings)
  return { settings, personaStore }
}

export function usePersonaUi() {
  const injected = inject(PERSONA_UI_KEY)
  if (injected) return injected
  return computed(() => derivePersonaUiSettings(undefined))
}

/** 未走 Layout 时按需拉取画像（如独立页） */
export async function ensurePersonaLoaded() {
  if (!isLoggedIn.value) return
  const store = usePersonaStore()
  if (!store.loaded) await store.loadProfile()
  if (!store.profile) {
    try {
      store.setProfile(await fetchPersonaProfile())
    } catch {
      /* ignore */
    }
  }
}
