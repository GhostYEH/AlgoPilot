/** 将访问/闯关时间戳聚合为按日计数，供学习热力图使用 */
export interface ActivityDay {
  date: string
  count: number
}

function toDateKey(ts: number): string {
  const d = new Date(ts)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function buildActivityDays(timestamps: number[], weeks = 12): ActivityDay[] {
  const counts = new Map<string, number>()
  for (const ts of timestamps) {
    const key = toDateKey(ts)
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const start = new Date(today)
  start.setDate(start.getDate() - weeks * 7 + 1)

  const days: ActivityDay[] = []
  const cursor = new Date(start)
  while (cursor <= today) {
    const key = toDateKey(cursor.getTime())
    days.push({ date: key, count: counts.get(key) ?? 0 })
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
}
