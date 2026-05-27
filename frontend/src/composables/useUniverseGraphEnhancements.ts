import { computed, ref, watch, type Ref } from 'vue'
import {
  buildConceptGraphEdges,
  buildConceptGraphNodes,
  getConceptsForModule,
  getProblemsForConcept,
  validateConceptGraph,
} from '@/constants/conceptGraph'
import { useConceptMastery } from '@/composables/useConceptMastery'
import { useGuidedTour } from '@/composables/useGuidedTour'
import { useLearningImpact } from '@/composables/useLearningImpact'
import { usePersonaUiDensity } from '@/composables/usePersonaUiDensity'
import { semanticSearch, type SemanticSearchResult } from '@/api/search'
import type { LearningPathPlan } from '@/api/orchestrator'

import type { UniverseNodeStatus } from '@/components/learning/AlgorithmUniverseGraph.vue'

export interface UniverseGraphNodeLite {
  id: string
  label: string
  accent: string
  weight: number
  radius: number
  score: number
  percent: number
  available: boolean
  status: UniverseNodeStatus
  isRemediation?: boolean
  isNext?: boolean
  rank?: number
  reason?: string
}

export function useUniverseGraphEnhancements(
  plan: Ref<LearningPathPlan | null>,
  personaScores: Ref<Record<string, number>>,
  moduleNodes: Ref<UniverseGraphNodeLite[]>,
  moduleEdges: Ref<Array<{ source: string; target: string }>>,
  selectedKey: Ref<string>,
) {
  const graphView = ref<'module' | 'concept'>('module')
  const searchQuery = ref('')
  const searchLoading = ref(false)
  const searchResults = ref<SemanticSearchResult[]>([])
  const highlightIds = ref<Set<string>>(new Set())
  const graphIssues = computed(() => validateConceptGraph())

  const { masteryMap } = useConceptMastery()
  const { settings: uiSettings } = usePersonaUiDensity(personaScores)
  const impact = useLearningImpact(plan)

  const conceptNodesRaw = computed(() =>
    buildConceptGraphNodes(masteryMap.value, {
      includeProblems: uiSettings.value.graphDetail !== 'minimal',
      limit: uiSettings.value.conceptNodeLimit,
    }),
  )

  const conceptEdgesRaw = computed(() => buildConceptGraphEdges(conceptNodesRaw.value))

  const tour = useGuidedTour(
    () => plan.value,
    () => graphView.value,
    () => conceptNodesRaw.value,
    () => ({ stepLimit: uiSettings.value.tourStepLimit }),
  )

  function conceptToUniverseNode(c: ReturnType<typeof buildConceptGraphNodes>[number]): UniverseGraphNodeLite {
    const pct = Math.round(c.mastery)
    let status: UniverseNodeStatus = 'progress'
    if (pct >= 80) status = 'mastered'
    else if (highlightIds.value.has(c.id)) status = 'active'
    return {
      id: c.id,
      label: c.label,
      accent: c.accent,
      weight: c.mastery / 10,
      radius: c.radius,
      score: Math.round(c.mastery / 10),
      percent: pct,
      available: true,
      status,
      isRemediation: impact.struggleRipple.value.some((x) => x.id === c.id),
    }
  }

  const displayNodes = computed(() => {
    if (graphView.value === 'concept') {
      return conceptNodesRaw.value.map(conceptToUniverseNode)
    }
    return moduleNodes.value.map((n) => ({
      ...n,
      status: highlightIds.value.has(n.id)
        ? ('active' as const)
        : impact.pathDiff.value.added.includes(n.id)
          ? ('remediation' as const)
          : n.status,
    }))
  })

  const displayEdges = computed(() => {
    if (graphView.value === 'concept') {
      return conceptEdgesRaw.value.map((e) => ({ source: e.source, target: e.target }))
    }
    return moduleEdges.value
  })

  const selectedConceptDetail = computed(() => {
    const c = conceptNodesRaw.value.find((n) => n.id === selectedKey.value)
    if (!c || c.kind !== 'concept') return null
    return {
      concept: c,
      problems: getProblemsForConcept(c.id),
    }
  })

  const selectedModuleConcepts = computed(() => {
    if (graphView.value === 'module') {
      return getConceptsForModule(selectedKey.value)
    }
    return []
  })

  async function runSearch() {
    const q = searchQuery.value.trim()
    if (!q) {
      searchResults.value = []
      highlightIds.value = new Set()
      return
    }
    searchLoading.value = true
    try {
      const res = await semanticSearch({ q, top_k: 8 })
      searchResults.value = res.results
      highlightIds.value = new Set(res.highlight_node_ids)
      if (res.highlight_node_ids.some((id) => conceptNodesRaw.value.some((c) => c.id === id))) {
        graphView.value = 'concept'
      }
    } catch {
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }

  function clearSearch() {
    searchQuery.value = ''
    searchResults.value = []
    highlightIds.value = new Set()
  }

  function applySearchHit(hit: SemanticSearchResult) {
    if (hit.module_key) selectedKey.value = hit.module_key
    if (hit.concept_ids.length) {
      graphView.value = 'concept'
      selectedKey.value = hit.concept_ids[0]
    }
    highlightIds.value = new Set(hit.node_ids)
    tour.goTo(hit.module_key || hit.id)
  }

  watch(
    () => tour.currentStep.value?.id,
    (id) => {
      if (!tour.active.value || !id) return
      selectedKey.value = id
      highlightIds.value = new Set([id])
    },
  )

  watch(
    () => plan.value?.remediation_inserted,
    (v) => {
      if (v) tour.start(0, true)
    },
  )

  return {
    graphView,
    searchQuery,
    searchLoading,
    searchResults,
    highlightIds,
    graphIssues,
    uiSettings,
    impact,
    tour,
    masteryMap,
    conceptNodesRaw,
    displayNodes,
    displayEdges,
    selectedConceptDetail,
    selectedModuleConcepts,
    runSearch,
    clearSearch,
    applySearchHit,
  }
}
