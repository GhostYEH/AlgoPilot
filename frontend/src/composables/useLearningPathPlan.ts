import { storeToRefs } from 'pinia'

import {
  sortRowsByPlan,
  useLearningPathStore,
} from '@/stores/pinia/learningPath'

export { sortRowsByPlan }

export function useLearningPathPlan() {
  const store = useLearningPathStore()
  const { plan, loading, loaded, hasPlan, stepMap, recommendedNext, lastReplanDiff } =
    storeToRefs(store)

  return {
    plan,
    loading,
    hasPlan,
    loaded,
    stepMap,
    recommendedNext,
    lastReplanDiff,
    loadPlan: store.loadPlan,
    replan: store.replan,
    recordExternalReplan: store.recordExternalReplan,
    clearReplanDiff: store.clearReplanDiff,
    clearPlan: store.clearPlan,
  }
}
