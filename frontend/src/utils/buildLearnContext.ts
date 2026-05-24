import type { LearnSection } from '@/modules/shared/learningTypes'

export interface AiTutorSectionPayload {
  id: string
  title: string
  subtitle: string
  difficulty: string
  est_minutes: number
  keywords: string[]
  overview?: string | null
  points: string[]
  topic_blocks: { title: string; intro?: string; points: string[] }[]
  pitfalls: string[]
  checklist: string[]
  complexity_hint?: string | null
  code_sketch?: string | null
}

export function sectionToAiContext(section: LearnSection): AiTutorSectionPayload {
  return {
    id: section.id,
    title: section.title,
    subtitle: section.subtitle,
    difficulty: section.difficulty,
    est_minutes: section.estMinutes,
    keywords: section.keywords ?? [],
    overview: section.overview ?? null,
    points: section.points ?? [],
    topic_blocks: (section.topicBlocks ?? []).map((b) => ({
      title: b.title,
      intro: b.intro,
      points: b.points ?? [],
    })),
    pitfalls: section.pitfalls ?? [],
    checklist: section.checklist ?? [],
    complexity_hint: section.complexityHint ?? null,
    code_sketch: section.codeSketch ?? null,
  }
}
