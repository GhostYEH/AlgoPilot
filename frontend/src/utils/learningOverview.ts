import {
  ALGORITHM_MODULES,
  MODULE_PHASE_LABELS,
  type AlgorithmModuleItem,
  type ModulePhase,
} from '@/constants/modules'
import { MODULE_PROGRESS_SOURCES } from '@/modules/shared/moduleProgressIndex'
import { getModuleProgressPercent } from '@/utils/moduleProgressSummary'

export interface ModuleProgressRow {
  key: string
  label: string
  phase: ModulePhase
  available: boolean
  accent: string
  percent: number
  doneCount: number
  totalCount: number
  hasProgressData: boolean
}

export interface LearningOverview {
  overallPercent: number
  trackedModules: number
  completedModules: number
  inProgressModules: ModuleProgressRow[]
  strongModules: ModuleProgressRow[]
  weakModules: ModuleProgressRow[]
  rows: ModuleProgressRow[]
  nextModule: AlgorithmModuleItem | null
}

function moduleRow(m: AlgorithmModuleItem): ModuleProgressRow {
  const src = MODULE_PROGRESS_SOURCES[m.key]
  const percent = getModuleProgressPercent(m.key)
  const hasProgressData = percent >= 0
  let doneCount = 0
  let totalCount = 0
  if (src && src.sectionIds.length > 0) {
    totalCount = src.sectionIds.length
    const done = src.loadDone()
    doneCount = src.sectionIds.filter((id) => done[id]).length
  }
  return {
    key: m.key,
    label: m.label,
    phase: m.phase,
    available: m.available,
    accent: m.accent,
    percent: hasProgressData ? percent : 0,
    doneCount,
    totalCount,
    hasProgressData,
  }
}

/** 汇总各模块学习进度与强弱项 */
export function buildLearningOverview(): LearningOverview {
  const rows = ALGORITHM_MODULES.map(moduleRow)
  const tracked = rows.filter((r) => r.hasProgressData && r.available)
  const withPct = tracked.filter((r) => r.totalCount > 0)

  let overallPercent = 0
  if (withPct.length > 0) {
    const sum = withPct.reduce((acc, r) => acc + r.percent, 0)
    overallPercent = Math.round(sum / withPct.length)
  }

  const completedModules = tracked.filter((r) => r.percent === 100).length
  const inProgressModules = tracked.filter((r) => r.percent > 0 && r.percent < 100)

  const strongModules = [...tracked]
    .filter((r) => r.percent >= 60)
    .sort((a, b) => b.percent - a.percent)
    .slice(0, 4)

  const weakModules = [...tracked]
    .filter((r) => r.available && r.percent < 40)
    .sort((a, b) => a.percent - b.percent)
    .slice(0, 4)

  const nextModule =
    ALGORITHM_MODULES.find((m) => {
      if (!m.available) return false
      const pct = getModuleProgressPercent(m.key)
      return pct >= 0 && pct < 100
    }) ??
    ALGORITHM_MODULES.find((m) => m.available && getModuleProgressPercent(m.key) < 0) ??
    null

  return {
    overallPercent,
    trackedModules: tracked.length,
    completedModules,
    inProgressModules,
    strongModules,
    weakModules,
    rows,
    nextModule,
  }
}

export function getPhaseModules(phase: ModulePhase): ModuleProgressRow[] {
  return buildLearningOverview().rows.filter((r) => r.phase === phase)
}

export function phaseLabel(phase: ModulePhase): string {
  return MODULE_PHASE_LABELS[phase]
}
