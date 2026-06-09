import type { ProblemDetail, ProblemListItem } from '@/api/oj'

let cache: Record<string, ProblemDetail> | null = null

async function loadBundle(): Promise<Record<string, ProblemDetail> | null> {
  if (cache) return cache

  const urls = ['/oj/bundle.json', `${import.meta.env.BASE_URL || '/'}oj/bundle.json`]
  for (const url of urls) {
    try {
      const normalized = url.replace(/([^:]\/)\/+/g, '$1')
      const res = await fetch(normalized)
      if (!res.ok) continue
      cache = (await res.json()) as Record<string, ProblemDetail>
      return cache
    } catch {
      /* try next */
    }
  }
  return null
}

export async function fetchLocalProblem(slug: string): Promise<ProblemDetail | null> {
  const bundle = await loadBundle()
  return bundle?.[slug] ?? null
}

/** 离线题库列表（后端不可用时 PracticeListView 回退） */
export async function fetchLocalProblemList(): Promise<ProblemListItem[]> {
  const bundle = await loadBundle()
  if (!bundle) return []
  return Object.values(bundle)
    .map((p) => ({
      slug: p.slug,
      title: p.title,
      lc_id: p.lc_id,
      difficulty: p.difficulty,
      ready: Boolean(p.ready),
      module_key: p.module_key,
      tags: p.tags ?? [],
      common_errors: p.common_errors ?? [],
    }))
    .sort((a, b) => a.lc_id - b.lc_id)
}

/** 根据 slug 猜测力扣风格方法名 */
export function guessMethodFromSlug(slug: string): string {
  const map: Record<string, string> = {
    'two-sum': 'twoSum',
    'linked-list-cycle': 'hasCycle',
    'linked-list-cycle-ii': 'detectCycle',
    'intersection-of-two-linked-lists': 'getIntersectionNode',
    'reverse-linked-list': 'reverseList',
    'valid-parentheses': 'isValid',
    'climbing-stairs': 'climbStairs',
    'binary-search': 'search',
    'ti-huan-kong-ge-lcof': 'replaceSpace',
    'replace-space-lcof': 'replaceSpace',
  }
  if (map[slug]) return map[slug]
  const parts = slug.split('-')
  const camel = parts[0] + parts.slice(1).map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join('')
  return camel || 'solve'
}

export function buildFallbackProblem(
  slug: string,
  title: string,
  lcId = 0,
): ProblemDetail {
  return {
    slug,
    title,
    lc_id: lcId,
    difficulty: 'medium',
    description: [
      `## ${title}`,
      '',
      lcId > 0 ? `力扣 ${lcId} · ${title}` : title,
      '',
      '请按**洛谷格式**编写完整程序，使用标准输入/输出。',
      '',
      '当前为**离线题库预览**（后端未连接时也可做题）。',
      '若要运行/提交判题，请启动后端：',
      '`uvicorn main:app --port 9000`',
    ].join('\n'),
    judge_mode: 'stdio',
    entry: { class: 'Main', method: 'main', mode: 'stdio' },
    starter_code: {
      python:
        'import sys\n\n\ndef main():\n    # 从 stdin 读入，向 stdout 输出\n    pass\n\n\nif __name__ == \'__main__\':\n    main()\n',
      cpp:
        '#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    return 0;\n}\n',
    },
    samples: [],
    hidden_count: 0,
    ready: false,
    time_limit_ms: 3000,
    order_insensitive: false,
  }
}
