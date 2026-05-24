/** 各学习模块共用的章节类型 */

export type DifficultyLabel = '入门' | '基础' | '进阶'

export interface PracticeLink {
  id: number
  title: string
  slug: string
}

/** 分主题展开的讲解块（适合理论基础等长文节） */
export interface LearnTopicBlock {
  title: string
  /** 该主题开篇说明，可选 */
  intro?: string
  points: string[]
}

export interface LearnSection {
  id: string
  title: string
  subtitle: string
  difficulty: DifficultyLabel
  estMinutes: number
  keywords: string[]
  /** 本节开篇导读，显示在动画下方 */
  overview?: string
  /** 分主题详解；与 points 可同时存在 */
  topicBlocks?: LearnTopicBlock[]
  points: string[]
  pitfalls?: string[]
  checklist?: string[]
  complexityHint?: string
  /** 核心代码骨架，便于手敲对照 */
  codeSketch?: string
  main?: PracticeLink
  related?: PracticeLink[]
}

export function leetcodeCnUrl(slug: string) {
  return `https://leetcode.cn/problems/${slug}/`
}
