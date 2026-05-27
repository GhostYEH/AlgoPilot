import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  fetchLearningPathPlan,
  replanLearningPath,
  type LearningPathPlan,
  type PathStepItem,
} from '@/api/orchestrator'
import { buildLearningOverview, type ModuleProgressRow } from '@/utils/learningOverview'
import { useAuthStore } from '@/stores/pinia/auth'

export function sortRowsByPlan(rows: ModuleProgressRow[], orderedKeys: string[]): ModuleProgressRow[] {
  if (!orderedKeys.length) return rows
  const index = new Map(orderedKeys.map((k, i) => [k, i]))
  return [...rows].sort((a, b) => {
    const ia = index.get(a.key) ?? 999
    const ib = index.get(b.key) ?? 999
    return ia - ib
  })
}

export const useLearningPathStore = defineStore('learningPath', () => {
  const plan = ref<LearningPathPlan | null>(null)
  const loading = ref(false)
  const loaded = ref(false)

  const hasPlan = computed(() => !!plan.value?.ordered_keys?.length)

  const stepMap = computed(() => {
    const m = new Map<string, PathStepItem>()
    for (const s of plan.value?.steps ?? []) {
      m.set(s.module_key, s)
    }
    return m
  })

  const recommendedNext = computed(() => {
    const key = plan.value?.next_module_key
    if (!key) return buildLearningOverview().nextModule
    const overview = buildLearningOverview()
    return overview.rows.find((r) => r.key === key) ?? overview.nextModule
  })

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

  async function loadPlan() {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) {
      plan.value = null
      loaded.value = true
      return
    }
    try {
      const { plan: p } = await fetchLearningPathPlan()
      plan.value = p
    } catch {
      plan.value = null
    } finally {
      loaded.value = true
    }
  }

  async function replan() {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) return null
    loading.value = true
    try {
      plan.value = await replanLearningPath(buildReplanPayload())
      return plan.value
    } finally {
      loading.value = false
    }
  }

  function clearPlan() {
    plan.value = null
  }

  return {
    plan,
    loading,
    loaded,
    hasPlan,
    stepMap,
    recommendedNext,
    loadPlan,
    replan,
    clearPlan,
  }
})
