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

function findJsonEnd(text: string, start: number): number {
  let depth = 0
  let inString = false
  let escape = false
  for (let i = start; i < text.length; i++) {
    const ch = text[i]
    if (escape) {
      escape = false
      continue
    }
    if (ch === '\\' && inString) {
      escape = true
      continue
    }
    if (ch === '"') {
      inString = !inString
      continue
    }
    if (inString) continue
    if (ch === '{' || ch === '[') depth++
    else if (ch === '}' || ch === ']') {
      depth--
      if (depth === 0) return i
    }
  }
  return -1
}

function cleanJsonText(text: string): string {
  const kbIndex = text.indexOf('---**依据知识库**')
  if (kbIndex >= 0) {
    text = text.slice(0, kbIndex)
  }
  text = text.split('\n').filter(line => !line.includes('course:')).join('\n')
  return text.trim()
}

function extractJsonObjectText(raw: string): string | null {
  let text = raw?.trim()
  if (!text) return null

  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i)
  let candidate: string
  if (fence?.[1]) {
    candidate = fence[1].trim()
  } else if (text.startsWith('{')) {
    candidate = text
  } else {
    const start = text.indexOf('{')
    if (start < 0) return null
    candidate = text.slice(start)
  }

  candidate = cleanJsonText(candidate)

  const start = candidate.indexOf('{')
  if (start < 0) return null
  const end = findJsonEnd(candidate, start)
  if (end >= 0) return candidate.slice(start, end + 1)

  const lastBrace = candidate.lastIndexOf('}')
  if (lastBrace > start) return candidate.slice(start, lastBrace + 1)

  return null
}

export function isLikelyDomainStructureJson(raw: string): boolean {
  const blob = extractJsonObjectText(raw)
  if (!blob) return false
  try {
    const data = JSON.parse(blob)
    if (typeof data === 'object' && data !== null) {
      return 'domain_narrative' in data && 'structure_logic' in data
    }
  } catch {
    // fall through to substring check for malformed JSON
  }
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
    if (
      typeof data !== 'object' ||
      data === null ||
      !('domain_narrative' in data) ||
      !('structure_logic' in data) ||
      typeof data.domain_narrative !== 'object' ||
      data.domain_narrative === null ||
      typeof data.structure_logic !== 'object' ||
      data.structure_logic === null
    ) {
      return null
    }
    return {
      domain_narrative: data.domain_narrative as DomainNarrative,
      structure_logic: data.structure_logic as StructureLogic,
    }
  } catch {
    if (!blob.includes('"domain_narrative"') && !blob.includes('"structure_logic"')) {
      return null
    }
    const closeBraces: number[] = []
    for (let i = 0; i < blob.length; i++) {
      if (blob[i] === '}') closeBraces.push(i)
    }
    for (let i = closeBraces.length - 1; i >= 0; i--) {
      const candidate = blob.slice(0, closeBraces[i] + 1)
      try {
        const data = JSON.parse(candidate) as Record<string, unknown>
        if (typeof data !== 'object' || data === null) continue
        const hasDomain = 'domain_narrative' in data && typeof data.domain_narrative === 'object' && data.domain_narrative !== null
        const hasStructure = 'structure_logic' in data && typeof data.structure_logic === 'object' && data.structure_logic !== null
        if (hasDomain || hasStructure) {
          return {
            domain_narrative: hasDomain ? (data.domain_narrative as DomainNarrative) : {},
            structure_logic: hasStructure ? (data.structure_logic as StructureLogic) : {},
          }
        }
      } catch {
        continue
      }
    }
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
