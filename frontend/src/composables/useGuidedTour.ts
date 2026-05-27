import { computed, ref } from 'vue'
import { ALGORITHM_MODULES } from '@/constants/modules'
import { MODULE_PATH_HINTS } from '@/constants/modulePathHints'
import {
  topoSortConceptIds,
  type ConceptGraphNode,
} from '@/constants/conceptGraph'
import type { LearningPathPlan } from '@/api/orchestrator'

export interface TourStep {
  id: string
  title: string
  summary: string
  kind: 'module' | 'concept' | 'remediation'
  moduleKey: string
}

export function useGuidedTour(
  plan: () => LearningPathPlan | null,
  graphView: () => 'module' | 'concept',
  conceptNodes: () => ConceptGraphNode[],
  options?: () => { stepLimit?: number; remediationOnly?: boolean },
) {
  const active = ref(false)
  const stepIndex = ref(0)
  const remediationMode = ref(false)

  const steps = computed((): TourStep[] => {
    const p = plan()
    const opts = options?.() ?? {}
    const limit = opts.stepLimit ?? 99
    const list: TourStep[] = []

    if (opts.remediationOnly || remediationMode.value) {
      const rem = p?.steps?.find((s) => s.is_remediation)
      if (rem) {
        const hint = MODULE_PATH_HINTS[rem.module_key]
        list.push({
          id: rem.module_key,
          title: `巩固 · ${rem.module_key}`,
          summary: rem.reason || hint?.summary || 'EvaluatorAgent 建议回退巩固先修知识。',
          kind: 'remediation',
          moduleKey: rem.module_key,
        })
        return list
      }
    }

    if (graphView() === 'concept') {
      const nodes = conceptNodes()
      const order = topoSortConceptIds(nodes.filter((n) => n.kind === 'concept'))
      for (const id of order.slice(0, limit)) {
        const n = nodes.find((x) => x.id === id)
        if (!n) continue
        list.push({
          id: n.id,
          title: n.label,
          summary: n.description ?? `掌握「${n.label}」后可解锁关联 OJ 题与 Trace 动画。`,
          kind: 'concept',
          moduleKey: n.moduleKey,
        })
      }
      return list
    }

    const ordered =
      p?.ordered_keys?.length
        ? p.ordered_keys
        : p?.steps?.map((s) => s.module_key) ?? []

    for (const key of ordered.slice(0, limit)) {
      const step = p?.steps?.find((s) => s.module_key === key)
      const hint = MODULE_PATH_HINTS[key]
      list.push({
        id: key,
        title: ALGORITHM_MODULES.find((m) => m.key === key)?.label ?? key,
        summary: step?.reason || hint?.summary || `学习模块 ${key}`,
        kind: step?.is_remediation ? 'remediation' : 'module',
        moduleKey: key,
      })
    }
    return list
  })

  const currentStep = computed(() => steps.value[stepIndex.value] ?? null)
  const isFirst = computed(() => stepIndex.value <= 0)
  const isLast = computed(() => stepIndex.value >= steps.value.length - 1)

  function start(fromIndex = 0, remediationOnly = false) {
    remediationMode.value = remediationOnly
    active.value = true
    stepIndex.value = Math.min(fromIndex, Math.max(steps.value.length - 1, 0))
  }

  function stop() {
    active.value = false
    stepIndex.value = 0
    remediationMode.value = false
  }

  function next() {
    if (stepIndex.value < steps.value.length - 1) stepIndex.value += 1
    else stop()
  }

  function prev() {
    if (stepIndex.value > 0) stepIndex.value -= 1
  }

  function goTo(id: string) {
    const idx = steps.value.findIndex((s) => s.id === id)
    if (idx >= 0) stepIndex.value = idx
  }

  return {
    active,
    stepIndex,
    steps,
    currentStep,
    isFirst,
    isLast,
    start,
    stop,
    next,
    prev,
    goTo,
  }
}
