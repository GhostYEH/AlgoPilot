export interface ActivityDay {
  date: string
  count: number
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
}

export function buildActivityDays(source: ActivitySource, weeks = 12): ActivityDay[] {
  const visitCounts = new Map<string, number>()
  const gameCounts = new Map<string, number>()

  for (const ts of source.visitTimestamps) {
    const key = toDateKey(ts)
    visitCounts.set(key, (visitCounts.get(key) ?? 0) + 1)
  }

  for (const ts of source.gameClearTimestamps) {
    const key = toDateKey(ts)
    gameCounts.set(key, (gameCounts.get(key) ?? 0) + 1)
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
    days.push({
      date: key,
      count: vc + gc,
      visitCount: vc,
      gameCount: gc,
    })
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
}