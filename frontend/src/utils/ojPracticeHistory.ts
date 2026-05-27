/** OJ 练习历史（localStorage），用于概念掌握度估算 */

const STORAGE_KEY = 'alp-oj-practice-history'

export interface OjPracticeRecord {
  slug: string
  verdict: string
  at: number
  moduleKey?: string
}

function loadAll(): OjPracticeRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const data = JSON.parse(raw) as OjPracticeRecord[]
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

function saveAll(records: OjPracticeRecord[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records.slice(-200)))
}

export function recordOjPractice(slug: string, verdict: string, moduleKey?: string) {
  const records = loadAll()
  records.push({ slug, verdict, at: Date.now(), moduleKey })
  saveAll(records)
}

export function getOjPracticeBySlug(): Map<string, { ac: number; total: number; lastVerdict: string }> {
  const map = new Map<string, { ac: number; total: number; lastVerdict: string }>()
  for (const r of loadAll()) {
    const cur = map.get(r.slug) ?? { ac: 0, total: 0, lastVerdict: r.verdict }
    cur.total += 1
    if (r.verdict === 'AC') cur.ac += 1
    cur.lastVerdict = r.verdict
    map.set(r.slug, cur)
  }
  return map
}

export function getRecentFailureTags(limit = 5): string[] {
  const tags: string[] = []
  for (const r of [...loadAll()].reverse()) {
    if (r.verdict === 'AC') continue
    const tag = r.verdict === 'TLE' ? 'TLE' : r.verdict === 'RE' ? '指针/运行时' : '边界/WA'
    if (!tags.includes(tag)) tags.push(tag)
    if (tags.length >= limit) break
  }
  return tags
}
