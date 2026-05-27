import { computed, ref, type Ref } from 'vue'
import { getRecentFailureTags } from '@/utils/ojPracticeHistory'
import { getConceptCatalog } from '@/constants/conceptGraph'
import type { LearningPathPlan } from '@/api/orchestrator'

export interface ImpactNode {
  id: string
  label: string
  reason: string
  severity: 'high' | 'medium' | 'low'
}

const ERROR_CONCEPT_MAP: Record<string, string[]> = {
  TLE: ['dp-state', 'greedy-choice', 'binary-search'],
  '边界/WA': ['array-traversal', 'two-pointers-opposite', 'linked-list-pointer'],
  '指针/运行时': ['linked-list-pointer', 'tree-traversal'],
}

export function useLearningImpact(plan: Ref<LearningPathPlan | null>) {
  const showPathDiff = ref(false)
  const previousOrderedKeys = ref<string[]>([])

  const struggleRipple = computed((): ImpactNode[] => {
    const tags = getRecentFailureTags(3)
    const conceptIds = new Set<string>()
    for (const tag of tags) {
      for (const cid of ERROR_CONCEPT_MAP[tag] ?? []) conceptIds.add(cid)
    }
    const catalog = getConceptCatalog()
    return [...conceptIds].map((id) => {
      const c = catalog.find((x) => x.id === id)
      return {
        id,
        label: c?.label ?? id,
        reason: `近期 ${tags.join('、')} 受挫，建议复习`,
        severity: 'high' as const,
      }
    })
  })

  const pathDiff = computed(() => {
    const current = plan.value?.ordered_keys ?? []
    const prev = previousOrderedKeys.value
    if (!prev.length || !showPathDiff.value) return { added: [] as string[], removed: [] as string[] }
    const curSet = new Set(current)
    const prevSet = new Set(prev)
    return {
      added: current.filter((k) => !prevSet.has(k)),
      removed: prev.filter((k) => !curSet.has(k)),
    }
  })

  function snapshotPath() {
    previousOrderedKeys.value = [...(plan.value?.ordered_keys ?? [])]
  }

  function togglePathDiff() {
    if (!showPathDiff.value) snapshotPath()
    showPathDiff.value = !showPathDiff.value
  }

  return {
    showPathDiff,
    struggleRipple,
    pathDiff,
    snapshotPath,
    togglePathDiff,
  }
}
