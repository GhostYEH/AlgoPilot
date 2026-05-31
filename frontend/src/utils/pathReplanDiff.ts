import { ALGORITHM_MODULES } from '@/constants/modules'
import type { LearningPathPlan, PathStepItem } from '@/api/orchestrator'
import { getRecentFailureTags } from '@/utils/ojPracticeHistory'

export type PathDiffStatus =
  | 'added'
  | 'moved_up'
  | 'moved_down'
  | 'remediation'
  | 'unchanged'
  | 'removed'

export interface PathReplanDiffItem {
  moduleKey: string
  label: string
  status: PathDiffStatus
  beforeRank: number | null
  afterRank: number | null
  rankDelta: number
  reason: string
}

export interface ReplanContext {
  trigger?: 'manual' | 'evaluation' | 'persona' | 'oj_struggle' | 'mastery' | 'universe'
  triggerLabel?: string
  evidence?: string[]
}

export interface PathReplanDiffResult {
  beforeKeys: string[]
  afterKeys: string[]
  items: PathReplanDiffItem[]
  hasChanges: boolean
  trigger: string
  triggerLabel: string
  summary: string
  rationale: string
  remediationInserted: boolean
  evidence: string[]
  explanation: string
  at: string
}

function moduleLabel(key: string) {
  return ALGORITHM_MODULES.find((m) => m.key === key)?.label ?? key
}

function stepMap(steps: PathStepItem[]) {
  return new Map(steps.map((s) => [s.module_key, s]))
}

export function computePathReplanDiff(
  beforeKeys: string[],
  afterPlan: LearningPathPlan,
  options?: {
    beforeSteps?: PathStepItem[]
    context?: ReplanContext
    extraEvidence?: string[]
  },
): PathReplanDiffResult {
  const afterKeys = afterPlan.ordered_keys ?? []
  const afterSteps = stepMap(afterPlan.steps ?? [])
  const beforeSteps = stepMap(options?.beforeSteps ?? [])
  const remediationKeys = new Set(
    (afterPlan.steps ?? []).filter((s) => s.is_remediation).map((s) => s.module_key),
  )

  const allKeys = [...new Set([...beforeKeys, ...afterKeys])]
  const items: PathReplanDiffItem[] = []

  for (const key of allKeys) {
    const beforeIdx = beforeKeys.indexOf(key)
    const afterIdx = afterKeys.indexOf(key)
    const beforeRank = beforeIdx >= 0 ? beforeIdx + 1 : null
    const afterRank = afterIdx >= 0 ? afterIdx + 1 : null
    const step = afterSteps.get(key) ?? beforeSteps.get(key)

    let status: PathDiffStatus
    if (remediationKeys.has(key)) {
      status = 'remediation'
    } else if (beforeIdx < 0 && afterIdx >= 0) {
      status = 'added'
    } else if (beforeIdx >= 0 && afterIdx < 0) {
      status = 'removed'
    } else if (beforeIdx >= 0 && afterIdx >= 0) {
      const delta = afterIdx - beforeIdx
      if (delta < 0) status = 'moved_up'
      else if (delta > 0) status = 'moved_down'
      else status = 'unchanged'
    } else {
      continue
    }

    items.push({
      moduleKey: key,
      label: moduleLabel(key),
      status,
      beforeRank,
      afterRank,
      rankDelta: beforeIdx >= 0 && afterIdx >= 0 ? afterIdx - beforeIdx : 0,
      reason: step?.reason ?? '',
    })
  }

  const changedItems = items.filter((i) => i.status !== 'unchanged')
  const hasChanges =
    changedItems.length > 0 ||
    beforeKeys.join('|') !== afterKeys.join('|') ||
    afterPlan.remediation_inserted === true

  const evidence = collectEvidence(afterPlan, options?.extraEvidence, options?.context?.evidence)

  return {
    beforeKeys: [...beforeKeys],
    afterKeys: [...afterKeys],
    items: items.sort((a, b) => {
      const rankA = a.afterRank ?? a.beforeRank ?? 999
      const rankB = b.afterRank ?? b.beforeRank ?? 999
      return rankA - rankB
    }),
    hasChanges,
    trigger: options?.context?.trigger ?? 'manual',
    triggerLabel: options?.context?.triggerLabel ?? triggerDefaultLabel(options?.context?.trigger),
    summary: afterPlan.summary ?? '',
    rationale: afterPlan.rationale ?? '',
    remediationInserted: !!afterPlan.remediation_inserted,
    evidence,
    explanation: buildExplanation(changedItems, afterPlan, hasChanges),
    at: new Date().toISOString(),
  }
}

function triggerDefaultLabel(trigger?: ReplanContext['trigger']) {
  const map: Record<string, string> = {
    manual: '手动重排路径',
    evaluation: '按评估重排路径',
    persona: '画像更新后重排',
    oj_struggle: 'OJ 连续受挫触发',
    mastery: '掌握度驱动调整',
    universe: '宇宙图路径规划',
  }
  return map[trigger ?? 'manual'] ?? '路径重排'
}

function collectEvidence(
  plan: LearningPathPlan,
  extra?: string[],
  contextEvidence?: string[],
): string[] {
  const lines: string[] = []
  const seen = new Set<string>()

  function push(line: string) {
    const t = line.trim()
    if (!t || seen.has(t)) return
    seen.add(t)
    lines.push(t)
  }

  for (const e of contextEvidence ?? []) push(e)
  for (const e of extra ?? []) push(e)

  if (plan.rationale) push(plan.rationale)
  if (plan.summary && plan.summary !== plan.rationale) push(plan.summary)

  for (const step of plan.steps ?? []) {
    if (step.is_remediation && step.reason) {
      push(`巩固节点 · ${moduleLabel(step.module_key)}：${step.reason}`)
    } else if (step.reason) {
      push(`${moduleLabel(step.module_key)}：${step.reason}`)
    }
  }

  const recentErrors = getRecentFailureTags(3)
  if (recentErrors.length) {
    push(`近期 OJ 错因：${recentErrors.join('、')}`)
  }

  return lines.slice(0, 8)
}

function buildExplanation(
  changedItems: PathReplanDiffItem[],
  plan: LearningPathPlan,
  hasChanges: boolean,
): string {
  if (!hasChanges) {
    return '本次评估后路径无需调整。'
  }
  if (plan.rationale?.trim()) {
    return plan.rationale.trim()
  }
  if (plan.summary?.trim()) {
    return plan.summary.trim()
  }

  const parts: string[] = []
  const remediations = changedItems.filter((i) => i.status === 'remediation')
  const added = changedItems.filter((i) => i.status === 'added')
  const up = changedItems.filter((i) => i.status === 'moved_up')
  const down = changedItems.filter((i) => i.status === 'moved_down')

  if (remediations.length) {
    parts.push(`插入巩固节点「${remediations.map((i) => i.label).join('、')}」`)
  }
  if (added.length) {
    parts.push(`新增模块 ${added.map((i) => i.label).join('、')}`)
  }
  if (up.length) {
    parts.push(`提前学习 ${up.map((i) => i.label).join('、')}`)
  }
  if (down.length) {
    parts.push(`延后学习 ${down.map((i) => i.label).join('、')}`)
  }

  return parts.length ? parts.join('；') + '。' : '路径顺序已根据当前学情更新。'
}
