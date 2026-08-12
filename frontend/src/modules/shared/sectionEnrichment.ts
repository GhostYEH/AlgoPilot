/**
 * 各学习模块章节加厚：overview + topicBlocks 合并进 LearnSection
 */
import type { LearnSection, LearnTopicBlock } from '@/modules/shared/learningTypes'

export interface SectionEnrichment {
  overview?: string
  topicBlocks?: LearnTopicBlock[]
  summaryPoints?: string[]
  extraPitfalls?: string[]
  extraChecklist?: string[]
  estMinutes?: number
}

export function applySectionEnrichment(sections: LearnSection[]): LearnSection[] {
  return sections
}

/** 有分主题块时，底部「速记」不再重复铺开全部原始 points */
function resolvePointsAfterEnrichment(s: LearnSection, e: SectionEnrichment): string[] {
  const hasTopics = !!(e.topicBlocks?.length)
  if (hasTopics) {
    if (e.summaryPoints?.length) return e.summaryPoints
    return s.points.slice(0, Math.min(3, s.points.length))
  }
  if (e.summaryPoints?.length) return [...s.points, ...e.summaryPoints]
  return s.points
}

export function mergeEnrichment<T extends LearnSection>(
  sections: T[],
  enrichment: Record<string, SectionEnrichment>,
): T[] {
  return sections.map((s) => {
    const e = enrichment[s.id]
    if (!e) return s
    return {
      ...s,
      overview: e.overview ?? s.overview,
      topicBlocks: e.topicBlocks ?? s.topicBlocks,
      estMinutes: e.estMinutes ?? s.estMinutes,
      points: resolvePointsAfterEnrichment(s, e),
      pitfalls: e.extraPitfalls?.length ? [...(s.pitfalls ?? []), ...e.extraPitfalls] : s.pitfalls,
      checklist: e.extraChecklist?.length ? [...(s.checklist ?? []), ...e.extraChecklist] : s.checklist,
    } as T
  })
}
