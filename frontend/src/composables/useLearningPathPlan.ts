import { computed, ref } from 'vue'
import {
  fetchLearningPathPlan,
  replanLearningPath,
  type LearningPathPlan,
  type PathStepItem,
} from '@/api/orchestrator'
import { buildLearningOverview, type ModuleProgressRow } from '@/utils/learningOverview'
import { isLoggedIn } from '@/stores/auth'

const planRef = ref<LearningPathPlan | null>(null)
const loadingRef = ref(false)
const loadedRef = ref(false)

function buildReplanPayload() {
  const overview = buildLearningOverview()
  return {
    overall_percent: overview.overallPercent,
    modules: overview.rows.map((r) => ({
      key: r.key,
      label: r.label,
      phase: r.phase,
      available: r.available,
      percent: r.percent,
      done_count: r.doneCount,
      total_count: r.totalCount,
    })),
  }
}

export function sortRowsByPlan(rows: ModuleProgressRow[], orderedKeys: string[]): ModuleProgressRow[] {
  if (!orderedKeys.length) return rows
  const index = new Map(orderedKeys.map((k, i) => [k, i]))
  return [...rows].sort((a, b) => {
    const ia = index.get(a.key) ?? 999
    const ib = index.get(b.key) ?? 999
    return ia - ib
  })
}

export function useLearningPathPlan() {
  const plan = computed(() => planRef.value)
  const loading = computed(() => loadingRef.value)
  const hasPlan = computed(() => !!planRef.value?.ordered_keys?.length)

  const stepMap = computed(() => {
    const m = new Map<string, PathStepItem>()
    for (const s of planRef.value?.steps ?? []) {
      m.set(s.module_key, s)
    }
    return m
  })

  const recommendedNext = computed(() => {
    const key = planRef.value?.next_module_key
    if (!key) return buildLearningOverview().nextModule
    const overview = buildLearningOverview()
    return overview.rows.find((r) => r.key === key) ?? overview.nextModule
  })

  async function loadPlan() {
    if (!isLoggedIn.value) {
      planRef.value = null
      loadedRef.value = true
      return
    }
    try {
      const { plan: p } = await fetchLearningPathPlan()
      planRef.value = p
    } catch {
      planRef.value = null
    } finally {
      loadedRef.value = true
    }
  }

  async function replan() {
    if (!isLoggedIn.value) return null
    loadingRef.value = true
    try {
      planRef.value = await replanLearningPath(buildReplanPayload())
      return planRef.value
    } finally {
      loadingRef.value = false
    }
  }

  function clearPlan() {
    planRef.value = null
  }

  return {
    plan,
    loading,
    hasPlan,
    loaded: computed(() => loadedRef.value),
    stepMap,
    recommendedNext,
    loadPlan,
    replan,
    clearPlan,
    sortRowsByPlan,
  }
}
