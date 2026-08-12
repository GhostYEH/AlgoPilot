import { computed } from 'vue'
import { loadRecentVisits } from '@/utils/learningBookmarks'
import { buildActivityDays, type ActivityDay, type ActivitySource } from '@/utils/learningActivity'
import { buildGameLearningOverview } from '@/utils/gameLearningOverview'

export function useLearningActivity() {
  const recentVisits = computed(() => loadRecentVisits())
  const gameOverview = computed(() => buildGameLearningOverview())

  const activityDays = computed<ActivityDay[]>(() => {
    const source: ActivitySource = {
      visitTimestamps: recentVisits.value.map((v) => v.visitedAt),
      gameClearTimestamps: gameOverview.value.recentHistory.map((r) => r.clearedAt),
    }
    return buildActivityDays(source)
  })

  return {
    activityDays,
    recentVisits,
    gameOverview,
  }
}