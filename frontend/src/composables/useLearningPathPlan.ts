import { storeToRefs } from 'pinia'

import {
  sortRowsByPlan,
  useLearningPathStore,
} from '@/stores/pinia/learningPath'

export { sortRowsByPlan }

export function useLearningPathPlan() {
  const store = useLearningPathStore()
  const { plan, loading, loaded, hasPlan, stepMap, recommendedNext } = storeToRefs(store)

  return {
    plan,
    loading,
    hasPlan,
    loaded,
    stepMap,
    recommendedNext,
    loadPlan: store.loadPlan,
    replan: store.replan,
    clearPlan: store.clearPlan,
  }
}
