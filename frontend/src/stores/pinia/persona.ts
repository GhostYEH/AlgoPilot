import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchPersonaProfile, type PersonaProfile } from '@/api/orchestrator'

export const usePersonaStore = defineStore('persona', () => {
  const profile = ref<PersonaProfile | null>(null)
  const loading = ref(false)
  const loaded = ref(false)

  const dimensionScores = computed(() => profile.value?.dimension_scores ?? {})
  const hasProfile = computed(() => !!profile.value?.updated_at)

  async function loadProfile(force = false) {
    if (loaded.value && !force) return profile.value
    loading.value = true
    try {
      profile.value = await fetchPersonaProfile()
      return profile.value
    } catch {
      profile.value = null
      return null
    } finally {
      loading.value = false
      loaded.value = true
    }
  }

  function setProfile(p: PersonaProfile | null) {
    profile.value = p
    loaded.value = true
  }

  function invalidate() {
    loaded.value = false
    profile.value = null
  }

  return {
    profile,
    loading,
    loaded,
    dimensionScores,
    hasProfile,
    loadProfile,
    setProfile,
    invalidate,
  }
})
