import type { ProblemListItem } from '@/api/oj'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { MODULE_PROGRESS_SOURCES } from '@/modules/shared/moduleProgressIndex'
import type { ModuleProgressRow } from '@/utils/learningOverview'
import { loadRecentVisits } from '@/utils/learningBookmarks'

export interface RadarAxis {
  key: string
  label: string
  value: number
}

export interface LeaderboardEntry {
  rank: number
  name: string
  avatarHue: number
  score: number
  unit: string
}

export interface ActivityFeedItem {
  id: string
  user: string
  action: string
  time: string
}

export interface PlatformStat {
  key: string
  label: string
  value: number
  suffix?: string
}

export interface TrainingProblem {
  slug: string
  title: string
  difficulty: string
  etaMin: number
  reason: string
  moduleLabel: string
}

export interface ReviewItem {
  moduleKey: string
  moduleLabel: string
  sectionLabel: string
  dueLabel: string
}

export interface ResourceCard {
  id: string
  title: string
  module: string
  desc: string
  cover: string
  problemCount: number
  passRate: number
  tags: string[]
}

const RESOURCE_META: Record<
  string,
  { cover: string; problemCount: number; passRate: number; tags: string[] }
> = {
  '1': {
    cover: 'linear-gradient(135deg, #f97316 0%, #fb923c 45%, #1e293b 100%)',
    problemCount: 12,
    passRate: 68,
    tags: ['记忆化', '状态转移'],
  },
  '2': {
    cover: 'linear-gradient(135deg, #818cf8 0%, #a78bfa 50%, #0f172a 100%)',
    problemCount: 18,
    passRate: 72,
    tags: ['模板题', '冲刺'],
  },
  '3': {
    cover: 'linear-gradient(135deg, #c084fc 0%, #e879f9 40%, #111827 100%)',
    problemCount: 10,
    passRate: 61,
    tags: ['单调栈', '经典模型'],
  },
  '4': {
    cover: 'linear-gradient(135deg, #f472b6 0%, #fb7185 45%, #0f172a 100%)',
    problemCount: 15,
    passRate: 74,
    tags: ['遍历框架', '递归'],
  },
}

const MODULE_PROBLEM_HINTS: Record<string, { slug: string; title: string; difficulty: string }[]> = {
  array: [
    { slug: 'two-sum', title: '两数之和', difficulty: 'Easy' },
    { slug: 'max-subarray', title: '最大子数组和', difficulty: 'Medium' },
  ],
  'linked-list': [
    { slug: 'reverse-linked-list', title: '反转链表', difficulty: 'Easy' },
  ],
  'binary-tree': [
    { slug: 'binary-tree-inorder', title: '二叉树中序遍历', difficulty: 'Easy' },
  ],
  dp: [
    { slug: 'climbing-stairs', title: '爬楼梯', difficulty: 'Easy' },
    { slug: 'coin-change', title: '零钱兑换', difficulty: 'Medium' },
  ],
  'two-pointers': [
    { slug: 'container-with-most-water', title: '盛最多水的容器', difficulty: 'Medium' },
  ],
  'stack-queue': [
    { slug: 'valid-parentheses', title: '有效的括号', difficulty: 'Easy' },
  ],
  greedy: [{ slug: 'assign-cookies', title: '分发饼干', difficulty: 'Easy' }],
  'hash-table': [{ slug: 'two-sum', title: '两数之和', difficulty: 'Easy' }],
  string: [{ slug: 'valid-palindrome', title: '验证回文串', difficulty: 'Easy' }],
  backtracking: [{ slug: 'subsets', title: '子集', difficulty: 'Medium' }],
  'monotonic-stack': [
    { slug: 'daily-temperatures', title: '每日温度', difficulty: 'Medium' },
  ],
}

function avgPercent(rows: ModuleProgressRow[]): number {
  const tracked = rows.filter((r) => r.hasProgressData && r.available && r.totalCount > 0)
  if (!tracked.length) return 0
  return Math.round(tracked.reduce((a, r) => a + r.percent, 0) / tracked.length)
}

/** 能力雷达六维（按模块分组均值，无进度时给浅色底数便于展示） */
export function buildSkillRadar(rows: ModuleProgressRow[]): RadarAxis[] {
  const byKey = Object.fromEntries(rows.map((r) => [r.key, r]))
  const pick = (keys: string[]) => keys.map((k) => byKey[k]).filter(Boolean) as ModuleProgressRow[]

  const dims: { key: string; label: string; keys: string[] }[] = [
    { key: 'array', label: '数组', keys: ['array'] },
    { key: 'list', label: '链表', keys: ['linked-list'] },
    { key: 'tree', label: '树', keys: ['binary-tree', 'backtracking'] },
    { key: 'dp', label: '动态规划', keys: ['dp', 'greedy'] },
    { key: 'skill', label: '技巧', keys: ['two-pointers', 'stack-queue', 'monotonic-stack'] },
    { key: 'base', label: '基础', keys: ['hash-table', 'string'] },
  ]

  return dims.map((d) => {
    const pct = avgPercent(pick(d.keys))
    const hasAny = pick(d.keys).some((r) => r.hasProgressData)
    return { key: d.key, label: d.label, value: hasAny ? pct : 0 }
  })
}

export function getLeaderboardAc(): LeaderboardEntry[] {
  return []
}

export function getLeaderboardStreak(): LeaderboardEntry[] {
  return []
}

export function getActivityFeed(): ActivityFeedItem[] {
  return []
}

export function buildPlatformStats(ojReady: number | null): PlatformStat[] {
  return [
    {
      key: 'oj',
      label: '可判题目',
      value: ojReady ?? 0,
      suffix: ojReady == null ? '' : ' 道',
    },
  ]
}

function hashDaySeed(): number {
  const s = new Date().toISOString().slice(0, 10)
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  return h
}

export function pickDailyProblem(
  problems: ProblemListItem[],
): TrainingProblem | null {
  const ready = problems.filter((p) => p.ready)
  if (!ready.length) return null
  const idx = hashDaySeed() % ready.length
  const p = ready[idx]
  return {
    slug: p.slug,
    title: p.title,
    difficulty: p.difficulty,
    etaMin: p.difficulty === 'Hard' ? 45 : p.difficulty === 'Medium' ? 25 : 15,
    reason: '每日一题 · 打卡入口',
    moduleLabel: 'OJ',
  }
}

export function pickTargetedProblems(
  weakRows: ModuleProgressRow[],
  problems: ProblemListItem[],
  limit = 3,
): TrainingProblem[] {
  const ready = problems.filter((p) => p.ready)
  const out: TrainingProblem[] = []
  const weakKeys = weakRows.length
    ? weakRows.map((r) => r.key)
    : ['array', 'two-pointers', 'dp']

  for (const key of weakKeys) {
    if (out.length >= limit) break
    const mod = ALGORITHM_MODULES.find((m) => m.key === key)
    const hints = MODULE_PROBLEM_HINTS[key]
    if (hints?.length) {
      const h = hints[out.length % hints.length]
      out.push({
        slug: h.slug,
        title: h.title,
        difficulty: h.difficulty,
        etaMin: h.difficulty === 'Hard' ? 40 : h.difficulty === 'Medium' ? 28 : 18,
        reason: `薄弱：${mod?.label ?? key}`,
        moduleLabel: mod?.label ?? key,
      })
      continue
    }
    const fallback = ready[out.length % Math.max(ready.length, 1)]
    if (fallback) {
      out.push({
        slug: fallback.slug,
        title: fallback.title,
        difficulty: fallback.difficulty,
        etaMin: 20,
        reason: `建议加强：${mod?.label ?? key}`,
        moduleLabel: mod?.label ?? key,
      })
    }
  }
  return out.slice(0, limit)
}

export function buildReviewQueue(limit = 4): ReviewItem[] {
  const items: ReviewItem[] = []
  for (const mod of ALGORITHM_MODULES) {
    if (!mod.available || items.length >= limit) continue
    const src = MODULE_PROGRESS_SOURCES[mod.key]
    if (!src?.sectionIds.length) continue
    const done = src.loadDone()
    const undone = src.sectionIds.filter((id) => !done[id])
    if (!undone.length) continue
    const started = src.sectionIds.some((id) => done[id])
    if (!started) continue
    items.push({
      moduleKey: mod.key,
      moduleLabel: mod.label,
      sectionLabel: `未完成 ${undone.length} 个小节`,
      dueLabel: undone.length >= 3 ? '建议今日复习' : '有空回顾',
    })
  }
  return items.slice(0, limit)
}

export function enrichResources(
  list: Array<{ id: string; title: string; module: string; desc: string }>,
): ResourceCard[] {
  return list.map((r) => {
    const meta = RESOURCE_META[r.id] ?? {
      cover: 'linear-gradient(135deg, #38bdf8, #0f172a)',
      problemCount: 8,
      passRate: 65,
      tags: ['讲义'],
    }
    return { ...r, ...meta }
  })
}

export function formatRecentRelative(ts: number): string {
  const diff = Date.now() - ts
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} 小时前`
  const day = Math.floor(hr / 24)
  return `${day} 天前`
}

export function getRecentForHome(limit = 5) {
  return loadRecentVisits().slice(0, limit)
}

export function moduleRouteName(moduleKey: string): string | undefined {
  return MODULE_ROUTE_NAMES[moduleKey]
}

export const HOME_ANNOUNCEMENTS = [
  { id: 'a1', type: 'info' as const, text: '栈与队列模块已支持食堂闯关小游戏，完成可解锁成就。' },
  { id: 'a2', type: 'warning' as const, text: '本周六 02:00–04:00 判题服务例行维护，请提前提交。' },
  { id: 'a3', type: 'success' as const, text: '在线 OJ 已接入 Python / C++ 双语言判题。' },
]
