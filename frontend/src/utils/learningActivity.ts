export interface ActivityDay {
  date: string
  count: number
  eventCount: number
  gameCount: number
  visitCount: number
}

function toDateKey(ts: number): string {
  const d = new Date(ts)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export interface ActivitySource {
  visitTimestamps: number[]
  gameClearTimestamps: number[]
  /** 登录用户的数据库事件时间戳，优先于本地访问记录作为活动来源。 */
  eventTimestamps?: number[]
}

export function buildActivityDays(source: ActivitySource, weeks = 12): ActivityDay[] {
  const visitCounts = new Map<string, number>()
  const gameCounts = new Map<string, number>()
  const eventCounts = new Map<string, number>()

  for (const ts of source.visitTimestamps) {
    const key = toDateKey(ts)
    visitCounts.set(key, (visitCounts.get(key) ?? 0) + 1)
  }

  for (const ts of source.gameClearTimestamps) {
    const key = toDateKey(ts)
    gameCounts.set(key, (gameCounts.get(key) ?? 0) + 1)
  }

  for (const ts of source.eventTimestamps ?? []) {
    const key = toDateKey(ts)
    eventCounts.set(key, (eventCounts.get(key) ?? 0) + 1)
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const start = new Date(today)
  start.setDate(start.getDate() - weeks * 7 + 1)

  const days: ActivityDay[] = []
  const cursor = new Date(start)
  while (cursor <= today) {
    const key = toDateKey(cursor.getTime())
    const vc = visitCounts.get(key) ?? 0
    const gc = gameCounts.get(key) ?? 0
    const ec = eventCounts.get(key) ?? 0
    days.push({
      date: key,
      count: vc + gc + ec,
      eventCount: ec,
      visitCount: vc,
      gameCount: gc,
    })
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
}
