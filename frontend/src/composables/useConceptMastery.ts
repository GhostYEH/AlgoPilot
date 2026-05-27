import { computed } from 'vue'
import { buildLearningOverview } from '@/utils/learningOverview'
import { getConceptCatalog, getProblemCatalog } from '@/constants/conceptGraph'
import { getOjPracticeBySlug } from '@/utils/ojPracticeHistory'

/** 概念 / 题目掌握度 0–100 */
export function useConceptMastery() {
  const masteryMap = computed(() => {
    const overview = buildLearningOverview()
    const ojStats = getOjPracticeBySlug()
    const map: Record<string, number> = {}

    for (const row of overview.rows) {
      map[row.key] = row.percent
    }

    for (const c of getConceptCatalog()) {
      const modPct = map[c.module_key] ?? 0
      map[c.id] = Math.round(modPct * 0.6)
    }

    for (const p of getProblemCatalog()) {
      const stat = ojStats.get(p.slug)
      if (stat) {
        const rate = stat.total ? (stat.ac / stat.total) * 100 : 0
        map[p.slug] = stat.ac > 0 ? Math.max(70, rate) : Math.min(30, rate)
        map[p.id] = map[p.slug]
        for (const cid of p.concept_ids) {
          map[cid] = Math.max(map[cid] ?? 0, map[p.slug] * 0.85)
        }
      }
    }

    return map
  })

  return { masteryMap }
}
