/** 双指针模块学习进度（本地存储；与后端 `learning_progress.payload` 中的键一致） */
export const TWO_POINTERS_SECTION_STORAGE_KEY = 'alp-two-pointers-section-done-v1'

const STORAGE_KEY = TWO_POINTERS_SECTION_STORAGE_KEY

export function loadSectionDone(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const o = JSON.parse(raw) as unknown
    return typeof o === 'object' && o !== null && !Array.isArray(o) ? (o as Record<string, boolean>) : {}
  } catch {
    return {}
  }
}

export function saveSectionDone(map: Record<string, boolean>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map))
  } catch {
    /* ignore quota */
  }
}

export function toggleSectionDone(id: string, done: boolean, prev: Record<string, boolean>) {
  const next = { ...prev, [id]: done }
  saveSectionDone(next)
  return next
}
