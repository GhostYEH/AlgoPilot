export interface ResourceSource {
  chunk_id: string
  module_id: string
  chapter_title: string
  section_title: string
  source_path: string
  relevance_score: number
  excerpt: string
}

interface ResourceLike {
  sources?: unknown
  meta?: Record<string, unknown>
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : null
}

function fromRecord(raw: Record<string, unknown>): ResourceSource | null {
  const chunkId = String(raw.chunk_id ?? raw.id ?? '').trim()
  if (!chunkId) return null
  return {
    chunk_id: chunkId,
    module_id: String(raw.module_id ?? raw.module_key ?? ''),
    chapter_title: String(raw.chapter_title ?? raw.title ?? ''),
    section_title: String(raw.section_title ?? raw.section ?? raw.title ?? ''),
    source_path: String(raw.source_path ?? ''),
    relevance_score: Number(raw.relevance_score ?? 0) || 0,
    excerpt: String(raw.excerpt ?? raw.snippet ?? ''),
  }
}

export function normalizeResourceSources(resource: ResourceLike | null | undefined): ResourceSource[] {
  if (!resource) return []
  const meta = resource.meta ?? {}
  const direct = Array.isArray(resource.sources)
    ? resource.sources
    : Array.isArray(meta.sources)
      ? meta.sources
      : []

  let candidates = direct
  if (!candidates.length) {
    const verification = asRecord(meta.verification)
    candidates = Array.isArray(verification?.grounded_chunks)
      ? verification.grounded_chunks
      : []
  }

  const normalized = candidates
    .map(asRecord)
    .filter((item): item is Record<string, unknown> => item !== null)
    .map(fromRecord)
    .filter((item): item is ResourceSource => item !== null)

  if (normalized.length) return normalized.slice(0, 5)

  const legacyRefs = Array.isArray(meta.knowledge_refs) ? meta.knowledge_refs : []
  return legacyRefs.slice(0, 5).map((ref) => ({
    chunk_id: String(ref),
    module_id: String(meta.module_key ?? ''),
    chapter_title: '课程知识库',
    section_title: '旧版来源记录',
    source_path: '',
    relevance_score: 0,
    excerpt: '该资源生成于来源详情字段上线前，仅保留了知识切片 ID。',
  }))
}

export function relevanceLabel(score: number): string {
  if (!Number.isFinite(score) || score <= 0) return '未记录'
  return `${Math.round(Math.min(1, score) * 100)}%`
}
