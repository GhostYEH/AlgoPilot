import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  fetchLearningPathPlan,
  replanLearningPath,
  type LearningPathPlan,
  type PathStepItem,
} from '@/api/orchestrator'
import { fetchMasteryReport, MASTERY_LEVEL_LABELS } from '@/api/mastery'
import { buildLearningOverview, type ModuleProgressRow } from '@/utils/learningOverview'
import {
  computePathReplanDiff,
  type PathReplanDiffResult,
  type ReplanContext,
} from '@/utils/pathReplanDiff'
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
  const lastReplanDiff = ref<PathReplanDiffResult | null>(null)

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

  async function gatherMasteryEvidence(): Promise<string[]> {
    try {
      const overview = await fetchMasteryReport()
      const lines: string[] = []
      lines.push(
        `掌握度 ${overview.overall_score}（${MASTERY_LEVEL_LABELS[overview.overall_level]}）`,
      )
      const report = overview.report ?? overview.chapters?.[0]
      if (report?.weak_skills?.length) {
        lines.push(`薄弱技能：${report.weak_skills.slice(0, 4).join('、')}`)
      }
      if (report?.path_adjustment_suggestion) {
        lines.push(report.path_adjustment_suggestion)
      }
      for (const action of report?.recommended_actions?.slice(0, 2) ?? []) {
        lines.push(action)
      }
      return lines
    } catch {
      return []
    }
  }

  function applyReplanDiff(
    beforeKeys: string[],
    newPlan: LearningPathPlan,
    context?: ReplanContext,
    extraEvidence?: string[],
    beforeSteps?: PathStepItem[],
  ) {
    lastReplanDiff.value = computePathReplanDiff(beforeKeys, newPlan, {
      beforeSteps: beforeSteps ?? plan.value?.steps,
      context,
      extraEvidence,
    })
  }

  async function replan(context?: ReplanContext) {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) return null
    const beforeKeys = [...(plan.value?.ordered_keys ?? [])]
    const beforeSteps = plan.value?.steps ?? []
    loading.value = true
    try {
      const newPlan = await replanLearningPath(buildReplanPayload())
      plan.value = newPlan
      const masteryEvidence = await gatherMasteryEvidence()
      applyReplanDiff(beforeKeys, newPlan, context, masteryEvidence, beforeSteps)
      return newPlan
    } finally {
      loading.value = false
    }
  }

  async function recordExternalReplan(
    beforeKeys: string[],
    context: ReplanContext,
    beforeSteps?: PathStepItem[],
  ) {
    if (!plan.value) return
    const masteryEvidence = await gatherMasteryEvidence()
    applyReplanDiff(beforeKeys, plan.value, context, masteryEvidence, beforeSteps)
  }

  function clearReplanDiff() {
    lastReplanDiff.value = null
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
    lastReplanDiff,
    loadPlan,
    replan,
    recordExternalReplan,
    clearReplanDiff,
    clearPlan,
  }
})
