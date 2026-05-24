const KEY = 'alp-home-activity-v1'

export interface ActivityDay {
  date: string
  visits: number
  solves: number
}

function todayKey(): string {
  return new Date().toISOString().slice(0, 10)
}

function readAll(): Record<string, ActivityDay> {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Record<string, ActivityDay>
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function writeAll(map: Record<string, ActivityDay>) {
  try {
    localStorage.setItem(KEY, JSON.stringify(map))
  } catch {
    /* quota */
  }
}

function bump(field: 'visits' | 'solves', amount = 1) {
  const date = todayKey()
  const map = readAll()
  const row = map[date] ?? { date, visits: 0, solves: 0 }
  row[field] += amount
  map[date] = row
  const keys = Object.keys(map).sort()
  if (keys.length > 120) {
    for (const k of keys.slice(0, keys.length - 120)) delete map[k]
  }
  writeAll(map)
}

export function touchTodayVisit() {
  bump('visits')
}

export function touchTodaySolve(count = 1) {
  bump('solves', count)
}

export interface DaySeriesPoint {
  label: string
  date: string
  visits: number
  solves: number
  total: number
}

export function getLast7DaySeries(): DaySeriesPoint[] {
  const map = readAll()
  const out: DaySeriesPoint[] = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const date = d.toISOString().slice(0, 10)
    const row = map[date]
    const visits = row?.visits ?? 0
    const solves = row?.solves ?? 0
    const label = `${d.getMonth() + 1}/${d.getDate()}`
    out.push({ label, date, visits, solves, total: visits + solves * 2 })
  }
  return out
}

export interface HeatmapCell {
  date: string
  level: 0 | 1 | 2 | 3 | 4
}

/** 近 12 周学习热力（按 visits + solves 分级） */
export function getHeatmapCells(weeks = 12): HeatmapCell[] {
  const map = readAll()
  const cells: HeatmapCell[] = []
  const totalDays = weeks * 7
  for (let i = totalDays - 1; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const date = d.toISOString().slice(0, 10)
    const row = map[date]
    const score = (row?.visits ?? 0) + (row?.solves ?? 0) * 2
    let level: 0 | 1 | 2 | 3 | 4 = 0
    if (score >= 8) level = 4
    else if (score >= 5) level = 3
    else if (score >= 3) level = 2
    else if (score >= 1) level = 1
    cells.push({ date, level })
  }
  return cells
}
