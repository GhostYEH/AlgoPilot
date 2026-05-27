import { renderAiReplyHtml } from '@/utils/renderAiReply'

export interface DomainNarrative {
  headline?: string
  story?: string
  mission?: string
  illustration_hint?: string
}

export interface StructureLogic {
  learning_objectives?: string[]
  abstract_model?: string
  problem_formalization?: string
  data_structures?: string[]
  algorithm_outline?: string
  code_framework?: string
  step_hints?: string[]
  time_complexity?: string
  space_complexity?: string
  correctness_proof?: string
  pitfalls?: string[]
}

export interface DomainStructurePayload {
  domain_narrative: DomainNarrative
  structure_logic: StructureLogic
}

function extractJsonObjectText(raw: string): string | null {
  const text = raw?.trim()
  if (!text) return null

  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i)
  if (fence?.[1]) return fence[1].trim()

  if (text.startsWith('{')) return text

  const start = text.indexOf('{')
  const end = text.lastIndexOf('}')
  if (start >= 0 && end > start) return text.slice(start, end + 1)

  return null
}

export function isLikelyDomainStructureJson(raw: string): boolean {
  const blob = extractJsonObjectText(raw)
  if (!blob) return false
  return (
    blob.includes('"domain_narrative"') &&
    blob.includes('"structure_logic"')
  )
}

export function parseDomainStructureContent(raw: string): DomainStructurePayload | null {
  const blob = extractJsonObjectText(raw)
  if (!blob) return null
  try {
    const data = JSON.parse(blob) as Record<string, unknown>
    if (!data.domain_narrative || !data.structure_logic) return null
    return {
      domain_narrative: data.domain_narrative as DomainNarrative,
      structure_logic: data.structure_logic as StructureLogic,
    }
  } catch {
    return null
  }
}

/** 是否为未解析成功的双域 JSON 原文（避免直接暴露 { } 给用户） */
export function looksLikeUnparsedDomainJson(raw: string): boolean {
  return isLikelyDomainStructureJson(raw) && !parseDomainStructureContent(raw)
}

export function renderDomainStoryHtml(domain: DomainNarrative): string {
  const parts: string[] = []
  if (domain.headline) parts.push(`### ${domain.headline}`)
  if (domain.story) parts.push(domain.story)
  if (domain.mission) parts.push(`**任务使命：** ${domain.mission}`)
  return renderAiReplyHtml(parts.join('\n\n'))
}

export function renderStructureOutlineHtml(structure: StructureLogic): string {
  const blocks: string[] = []
  if (structure.problem_formalization) {
    blocks.push(`**形式化题意**\n\n${structure.problem_formalization}`)
  }
  if (structure.abstract_model) {
    blocks.push(`**抽象模型**\n\n${structure.abstract_model}`)
  }
  if (structure.algorithm_outline) {
    blocks.push(`**算法步骤**\n\n${structure.algorithm_outline}`)
  }
  return renderAiReplyHtml(blocks.join('\n\n'))
}
