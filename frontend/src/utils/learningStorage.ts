import { ARRAY_SECTION_STORAGE_KEY } from '@/modules/array/arrayProgress'
import { HASH_TABLE_SECTION_STORAGE_KEY } from '@/modules/hashTable/hashTableProgress'
import { LINKED_LIST_SECTION_STORAGE_KEY } from '@/modules/linkedList/linkedListProgress'
import { STRING_SECTION_STORAGE_KEY } from '@/modules/string/stringProgress'
import { TWO_POINTERS_SECTION_STORAGE_KEY } from '@/modules/twoPointers/twoPointersProgress'
import { STACK_QUEUE_SECTION_STORAGE_KEY } from '@/modules/stackQueue/stackQueueProgress'
import { BINARY_TREE_SECTION_STORAGE_KEY } from '@/modules/binaryTree/binaryTreeProgress'
import { BACKTRACKING_SECTION_STORAGE_KEY } from '@/modules/backtracking/backtrackingProgress'
import { GREEDY_SECTION_STORAGE_KEY } from '@/modules/greedy/greedyProgress'
import { DP_SECTION_STORAGE_KEY } from '@/modules/dp/dpProgress'
import { MONOTONIC_STACK_SECTION_STORAGE_KEY } from '@/modules/monotonicStack/monotonicStackProgress'
import {
  applyRemoteGameProgress,
  exportGameProgressPayload,
  GAME_PROGRESS_PAYLOAD_KEY,
} from '@/modules/games/gameProgress'

/** 参与云端同步的 localStorage 键（随模块扩展在此追加） */
export const LEARNING_STORAGE_KEYS = [
  ARRAY_SECTION_STORAGE_KEY,
  HASH_TABLE_SECTION_STORAGE_KEY,
  LINKED_LIST_SECTION_STORAGE_KEY,
  STRING_SECTION_STORAGE_KEY,
  TWO_POINTERS_SECTION_STORAGE_KEY,
  STACK_QUEUE_SECTION_STORAGE_KEY,
  BINARY_TREE_SECTION_STORAGE_KEY,
  BACKTRACKING_SECTION_STORAGE_KEY,
  GREEDY_SECTION_STORAGE_KEY,
  DP_SECTION_STORAGE_KEY,
  MONOTONIC_STACK_SECTION_STORAGE_KEY,
] as const

export type LearningStorageKey = (typeof LEARNING_STORAGE_KEYS)[number]

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

/** 将若干 localStorage 键打包为可 JSON 序列化的对象（值已解析） */
export function exportProgressPayload(): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const key of LEARNING_STORAGE_KEYS) {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) continue
      const parsed = JSON.parse(raw) as unknown
      if (!isPlainObject(parsed)) continue
      const flat: Record<string, boolean> = {}
      for (const [k, v] of Object.entries(parsed)) {
        flat[k] = !!v
      }
      out[key] = flat
    } catch {
      /* ignore */
    }
  }
  const gameProgress = exportGameProgressPayload()
  if (
    Object.keys(gameProgress.clearedLevels).length > 0 ||
    gameProgress.history.length > 0
  ) {
    out[GAME_PROGRESS_PAYLOAD_KEY] = gameProgress
  }
  return out
}

/** 合并两个「小节完成」映射：任一侧为 true 则视为完成 */
export function mergeSectionDoneMaps(
  local: Record<string, boolean>,
  remote: Record<string, boolean>,
): Record<string, boolean> {
  const keys = new Set([...Object.keys(local), ...Object.keys(remote)])
  const out: Record<string, boolean> = {}
  for (const k of keys) out[k] = !!(local[k] || remote[k])
  return out
}

/** 将服务端 payload 写回 localStorage，并与当前本地值按小节合并 */
export function applyRemoteProgressPayload(remote: Record<string, unknown>) {
  if (remote[GAME_PROGRESS_PAYLOAD_KEY] != null) {
    applyRemoteGameProgress(remote[GAME_PROGRESS_PAYLOAD_KEY])
  }

  for (const key of LEARNING_STORAGE_KEYS) {
    const remoteVal = remote[key]
    if (!isPlainObject(remoteVal)) continue
    const remoteDone: Record<string, boolean> = {}
    for (const [k, v] of Object.entries(remoteVal)) {
      remoteDone[k] = !!v
    }
    let localDone: Record<string, boolean> = {}
    try {
      const raw = localStorage.getItem(key)
      if (raw) {
        const parsed = JSON.parse(raw) as unknown
        if (isPlainObject(parsed)) {
          for (const [k, v] of Object.entries(parsed)) localDone[k] = !!v
        }
      }
    } catch {
      localDone = {}
    }
    const merged = mergeSectionDoneMaps(localDone, remoteDone)
    try {
      localStorage.setItem(key, JSON.stringify(merged))
    } catch {
      /* ignore quota */
    }
  }
}
