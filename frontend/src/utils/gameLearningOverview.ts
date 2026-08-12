import { ALL_GAMES, MODULE_GAME_MAP } from '@/modules/games/gameRegistry'
import {
  clearedCount,
  getGameHistory,
  type GameClearRecord,
} from '@/modules/games/gameProgress'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'

export interface GameProgressRow {
  gameId: string
  title: string
  moduleKey: string
  moduleLabel: string
  cleared: number
  total: number
  percent: number
  routeName?: string
}

export interface GameLearningOverview {
  totalLevelsCleared: number
  totalLevels: number
  overallPercent: number
  rows: GameProgressRow[]
  recentHistory: GameClearRecord[]
}

export function buildGameLearningOverview(): GameLearningOverview {
  const rows: GameProgressRow[] = ALL_GAMES.map((g) => {
    const cleared = clearedCount(g.id, g.levels.length)
    const total = g.levels.length
    const mod = ALGORITHM_MODULES.find((m) => m.key === g.moduleKey)
    return {
      gameId: g.id,
      title: g.title,
      moduleKey: g.moduleKey,
      moduleLabel: mod?.label ?? (g.moduleKey === '_global' ? '综合' : g.moduleKey),
      cleared,
      total,
      percent: total ? Math.round((cleared / total) * 100) : 0,
      routeName:
        g.moduleKey !== '_global' ? MODULE_ROUTE_NAMES[g.moduleKey] : undefined,
    }
  })

  const totalLevelsCleared = rows.reduce((a, r) => a + r.cleared, 0)
  const totalLevels = rows.reduce((a, r) => a + r.total, 0)

  return {
    totalLevelsCleared,
    totalLevels,
    overallPercent: totalLevels ? Math.round((totalLevelsCleared / totalLevels) * 100) : 0,
    rows: rows.sort((a, b) => b.percent - a.percent || b.cleared - a.cleared),
    recentHistory: getGameHistory().slice(0, 50),
  }
}

export function moduleKeyForGame(gameId: string): string | undefined {
  const entry = Object.entries(MODULE_GAME_MAP).find(([, id]) => id === gameId)
  return entry?.[0]
}
