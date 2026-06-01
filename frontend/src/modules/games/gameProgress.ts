import { getGameById } from './gameRegistry'
import { schedulePushLearningProgress } from '@/utils/learningRemoteSync'
import { isLoggedIn } from '@/stores/auth'

export const GAME_PROGRESS_PAYLOAD_KEY = 'alp_game_progress_v1'

const LOCAL_STORAGE_KEY = GAME_PROGRESS_PAYLOAD_KEY

export interface GameClearRecord {
  gameId: string
  levelId: string
  gameTitle: string
  levelTitle: string
  moduleKey: string
  clearedAt: number
}

export interface GameProgressState {
  clearedLevels: Record<string, string[]>
  history: GameClearRecord[]
}

function emptyState(): GameProgressState {
  return { clearedLevels: {}, history: [] }
}

function loadRaw(): GameProgressState {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY)
    if (!raw) return emptyState()
    const parsed = JSON.parse(raw) as GameProgressState
    return {
      clearedLevels: parsed.clearedLevels ?? {},
      history: Array.isArray(parsed.history) ? parsed.history : [],
    }
  } catch {
    return emptyState()
  }
}

function save(state: GameProgressState) {
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(state))
  } catch {
    /* quota */
  }
}

function mergeLevelSets(a: string[] = [], b: string[] = []): string[] {
  return [...new Set([...a, ...b])]
}

function mergeHistory(a: GameClearRecord[], b: GameClearRecord[]): GameClearRecord[] {
  const map = new Map<string, GameClearRecord>()
  for (const r of [...a, ...b]) {
    const key = `${r.gameId}:${r.levelId}`
    const prev = map.get(key)
    if (!prev || r.clearedAt > prev.clearedAt) map.set(key, r)
  }
  return [...map.values()].sort((x, y) => y.clearedAt - x.clearedAt)
}

export function mergeGameProgress(local: GameProgressState, remote: GameProgressState): GameProgressState {
  const gameIds = new Set([
    ...Object.keys(local.clearedLevels),
    ...Object.keys(remote.clearedLevels),
  ])
  const clearedLevels: Record<string, string[]> = {}
  for (const gid of gameIds) {
    clearedLevels[gid] = mergeLevelSets(
      local.clearedLevels[gid],
      remote.clearedLevels[gid],
    )
  }
  return {
    clearedLevels,
    history: mergeHistory(local.history, remote.history),
  }
}

/** 导出到云端 payload */
export function exportGameProgressPayload(): GameProgressState {
  return loadRaw()
}

/** 从云端 payload 合并写回本地 */
export function applyRemoteGameProgress(remote: unknown) {
  if (!remote || typeof remote !== 'object') return
  const r = remote as GameProgressState
  if (!r.clearedLevels && !r.history) return
  const merged = mergeGameProgress(loadRaw(), {
    clearedLevels: r.clearedLevels ?? {},
    history: r.history ?? [],
  })
  save(merged)
}

export function isLevelCleared(gameId: string, levelId: string): boolean {
  return (loadRaw().clearedLevels[gameId] ?? []).includes(levelId)
}

export interface MarkLevelMeta {
  gameTitle?: string
  levelTitle?: string
  moduleKey?: string
}

export function markLevelCleared(gameId: string, levelId: string, meta?: MarkLevelMeta) {
  const s = loadRaw()
  const set = new Set(s.clearedLevels[gameId] ?? [])
  const isNew = !set.has(levelId)
  set.add(levelId)
  s.clearedLevels[gameId] = [...set]

  if (isNew) {
    const game = getGameById(gameId)
    const level = game?.levels.find((l) => l.id === levelId)
    s.history.unshift({
      gameId,
      levelId,
      gameTitle: meta?.gameTitle ?? game?.title ?? gameId,
      levelTitle: meta?.levelTitle ?? level?.title ?? levelId,
      moduleKey: meta?.moduleKey ?? game?.moduleKey ?? '',
      clearedAt: Date.now(),
    })
    if (s.history.length > 200) s.history.length = 200
  }

  save(s)
  schedulePushLearningProgress()

  if (isLoggedIn.value) {
    _pushGamePracticeToMemory(gameId, levelId, meta)
  }
}

async function _pushGamePracticeToMemory(
  gameId: string,
  levelId: string,
  meta?: MarkLevelMeta,
) {
  try {
    const { recordGamePractice } = await import('@/api/memory')
    const game = getGameById(gameId)
    const moduleKey = meta?.moduleKey ?? game?.moduleKey ?? ''
    await recordGamePractice({
      event_type: 'gamified_practice_complete',
      course_id: 'data_structures_algorithms',
      chapter_id: '',
      skill_id: '',
      game_id: gameId,
      level: levelId,
      module_key: moduleKey,
      success: true,
      score: 0,
      attempts: 1,
      time_spent_seconds: 0,
      evidence_text: `完成游戏 ${meta?.gameTitle ?? gameId} 关卡 ${meta?.levelTitle ?? levelId}`,
    })
  } catch {
    /* 静默失败，不影响本地进度 */
  }
}

export function clearedCount(gameId: string, total: number): number {
  const n = (loadRaw().clearedLevels[gameId] ?? []).length
  return Math.min(total, n)
}

export function getGameHistory(): GameClearRecord[] {
  return loadRaw().history
}

export function getAllClearedSummary(): { gameId: string; cleared: number; total: number }[] {
  const s = loadRaw()
  return Object.entries(s.clearedLevels).map(([gameId, levels]) => {
    const game = getGameById(gameId)
    return {
      gameId,
      cleared: levels.length,
      total: game?.levels.length ?? levels.length,
    }
  })
}
