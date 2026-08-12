/** 各模块小节完成度 localStorage（与云端 payload 键一致） */

export function createSectionProgress(storageKey: string) {
  function loadSectionDone(): Record<string, boolean> {
    try {
      const raw = localStorage.getItem(storageKey)
      if (!raw) return {}
      const o = JSON.parse(raw) as unknown
      return typeof o === 'object' && o !== null && !Array.isArray(o)
        ? (o as Record<string, boolean>)
        : {}
    } catch {
      return {}
    }
  }

  function saveSectionDone(map: Record<string, boolean>) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(map))
    } catch {
      /* ignore quota */
    }
  }

  function toggleSectionDone(id: string, done: boolean, prev: Record<string, boolean>) {
    const next = { ...prev, [id]: done }
    saveSectionDone(next)
    return next
  }

  return { STORAGE_KEY: storageKey, loadSectionDone, toggleSectionDone }
}
