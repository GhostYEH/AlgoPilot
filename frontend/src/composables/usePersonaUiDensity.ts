import { computed, type Ref } from 'vue'
import type { PersonaProfile } from '@/api/orchestrator'

export type GraphDetailLevel = 'minimal' | 'standard' | 'detailed'

export interface PersonaUiSettings {
  graphDetail: GraphDetailLevel
  tourStepLimit: number
  showComplexity: boolean
  defaultResourceTab: 'document' | 'trace'
  conceptNodeLimit: number
  showAstAudit: boolean
  encouragementLevel: 'high' | 'normal'
  labelStyle: 'plain' | 'technical'
}

const DEFAULT: PersonaUiSettings = {
  graphDetail: 'standard',
  tourStepLimit: 8,
  showComplexity: false,
  defaultResourceTab: 'document',
  conceptNodeLimit: 16,
  showAstAudit: false,
  encouragementLevel: 'normal',
  labelStyle: 'plain',
}

export function derivePersonaUiSettings(
  scores: Record<string, number> | PersonaProfile['dimension_scores'] | undefined,
): PersonaUiSettings {
  if (!scores) return { ...DEFAULT }

  const kb = scores.knowledge_base ?? 5
  const cognitive = scores.cognitive_style ?? 5
  const coding = scores.coding_ability ?? 5
  const grit = scores.grit ?? 5

  const settings: PersonaUiSettings = { ...DEFAULT }

  if (kb <= 4) {
    settings.graphDetail = 'minimal'
    settings.conceptNodeLimit = 8
    settings.labelStyle = 'plain'
    settings.showComplexity = false
  } else if (kb >= 8) {
    settings.graphDetail = 'detailed'
    settings.conceptNodeLimit = 24
    settings.labelStyle = 'technical'
  }

  if (cognitive >= 7) {
    settings.defaultResourceTab = 'trace'
  }

  if (coding >= 8) {
    settings.showComplexity = true
    settings.showAstAudit = true
    settings.graphDetail = 'detailed'
  }

  if (grit <= 4) {
    settings.tourStepLimit = 4
    settings.encouragementLevel = 'high'
  } else if (grit >= 8) {
    settings.tourStepLimit = 12
  }

  return settings
}

export function usePersonaUiDensity(
  personaScores: Ref<Record<string, number>>,
) {
  const settings = computed(() => derivePersonaUiSettings(personaScores.value))
  return { settings }
}
