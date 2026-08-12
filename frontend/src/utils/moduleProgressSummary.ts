import { MODULE_PROGRESS_SOURCES } from '@/modules/shared/moduleProgressIndex'

/** 无进度数据时返回 -1 */
export function getModuleProgressPercent(moduleKey: string): number {
  const src = MODULE_PROGRESS_SOURCES[moduleKey]
  if (!src || src.sectionIds.length === 0) return -1
  const done = src.loadDone()
  const completed = src.sectionIds.filter((id) => done[id]).length
  return Math.round((completed / src.sectionIds.length) * 100)
}

export function isModuleFullyComplete(moduleKey: string): boolean {
  return getModuleProgressPercent(moduleKey) === 100
}
