import type { Verdict } from '@/api/oj'

export const OJ_STRUGGLE_THRESHOLD = 3

const FAIL_VERDICTS: Verdict[] = ['WA', 'RE', 'TLE', 'CE']

/** 按 problem_slug 统计当前浏览器会话内的连续失败次数 */
const failureCountBySlug = new Map<string, number>()

/** 本轮连续失败是否已触发过 oj-struggle（AC 或换题后重置） */
const triggeredForSlug = new Map<string, boolean>()

export function isFailVerdict(verdict: Verdict | undefined): verdict is Verdict {
  return !!verdict && FAIL_VERDICTS.includes(verdict)
}

export function getConsecutiveFailures(slug: string): number {
  return failureCountBySlug.get(slug) ?? 0
}

/**
 * 记录一次判题结果。AC 清零当前题目计数；失败则累加。
 * @returns 更新后的连续失败次数
 */
export function recordOjVerdictForStruggle(slug: string, verdict: Verdict | undefined): number {
  if (!slug) return 0
  if (verdict === 'AC') {
    failureCountBySlug.set(slug, 0)
    triggeredForSlug.delete(slug)
    return 0
  }
  if (!isFailVerdict(verdict)) {
    return failureCountBySlug.get(slug) ?? 0
  }
  const next = (failureCountBySlug.get(slug) ?? 0) + 1
  failureCountBySlug.set(slug, next)
  return next
}

/** 是否应自动调用 oj-struggle（达阈值且本轮尚未触发） */
export function shouldAutoTriggerOjStruggle(slug: string): boolean {
  const n = getConsecutiveFailures(slug)
  return n >= OJ_STRUGGLE_THRESHOLD && !triggeredForSlug.get(slug)
}

export function markOjStruggleTriggered(slug: string) {
  if (slug) triggeredForSlug.set(slug, true)
}

export function resetOjStruggleSession(slug?: string) {
  if (slug) {
    failureCountBySlug.delete(slug)
    triggeredForSlug.delete(slug)
    return
  }
  failureCountBySlug.clear()
  triggeredForSlug.clear()
}
