const FAVORITES_KEY = 'alp-learning-favorites-v1'
const RECENT_KEY = 'alp-learning-recent-v1'
const MAX_RECENT = 12

export interface RecentVisit {
  moduleKey: string
  label: string
  visitedAt: number
}

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function writeJson(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* ignore quota */
  }
}

export function loadFavoriteKeys(): string[] {
  const list = readJson<string[]>(FAVORITES_KEY, [])
  return Array.isArray(list) ? list : []
}

export function isFavorite(moduleKey: string): boolean {
  return loadFavoriteKeys().includes(moduleKey)
}

export function toggleFavorite(moduleKey: string): boolean {
  const set = new Set(loadFavoriteKeys())
  const next = set.has(moduleKey)
  if (next) set.delete(moduleKey)
  else set.add(moduleKey)
  writeJson(FAVORITES_KEY, [...set])
  return !next
}

export function loadRecentVisits(): RecentVisit[] {
  const list = readJson<RecentVisit[]>(RECENT_KEY, [])
  return Array.isArray(list) ? list : []
}

/** 记录模块访问（用于「最近学习」） */
export function recordModuleVisit(moduleKey: string, label: string) {
  const now = Date.now()
  const filtered = loadRecentVisits().filter((v) => v.moduleKey !== moduleKey)
  const next: RecentVisit[] = [{ moduleKey, label, visitedAt: now }, ...filtered].slice(
    0,
    MAX_RECENT,
  )
  writeJson(RECENT_KEY, next)
}
