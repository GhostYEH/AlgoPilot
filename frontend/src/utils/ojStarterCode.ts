import type { ProblemDetail } from '@/api/oj'
import { buildFallbackProblem, guessMethodFromSlug } from '@/api/ojLocal'

const STDIO_PY =
  "import sys\n\n\ndef main():\n    # 洛谷风格：从标准输入读入，向标准输出写出答案\n    pass\n\n\nif __name__ == '__main__':\n    main()\n"

const STDIO_CPP = `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    // 洛谷风格：cin 读入，cout 输出
    return 0;
}
`

function leetcodePython(method: string): string {
  return `from typing import List, Optional


class Solution:
    def ${method}(self, *args, **kwargs):
        pass
`
}

function leetcodeCppList(method: string): string {
  return `#include <bits/stdc++.h>
using namespace std;

struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x) : val(x), next(nullptr) {}
};

class Solution {
public:
    ListNode* ${method}(ListNode* headA, ListNode* headB) {
        return nullptr;
    }
};
`
}

function leetcodeCppGeneric(method: string): string {
  return `#include <bits/stdc++.h>
using namespace std;

class Solution {
public:
    void ${method}() {}
};
`
}

function isStdio(problem: ProblemDetail): boolean {
  if (problem.judge_mode === 'leetcode') return false
  return (
    problem.judge_mode === 'stdio' ||
    problem.entry?.mode === 'stdio' ||
    !problem.entry?.method
  )
}

/** 按当前语言取模板，绝不混用另一种语言的代码 */
export function getStarterForLanguage(
  problem: ProblemDetail,
  language: 'python' | 'cpp',
): string {
  const fromProblem = problem.starter_code?.[language]?.trim()
  if (fromProblem) return fromProblem

  if (isStdio(problem)) {
    return language === 'cpp' ? STDIO_CPP : STDIO_PY
  }

  const method = problem.entry?.method ?? guessMethodFromSlug(problem.slug)
  if (language === 'python') {
    return leetcodePython(method)
  }

  const entryExtra = problem.entry as { needs_list_node?: boolean } | null | undefined
  if (entryExtra?.needs_list_node || method === 'getIntersectionNode') {
    return leetcodeCppList(method)
  }

  return leetcodeCppGeneric(method)
}

export function mergeStarterCode(
  primary: ProblemDetail,
  fallback?: ProblemDetail | null,
): Record<string, string> {
  const fb = fallback?.starter_code ?? {}
  const pri = primary.starter_code ?? {}
  return {
    python: pri.python?.trim() || fb.python?.trim() || '',
    cpp: pri.cpp?.trim() || fb.cpp?.trim() || '',
  }
}

export function enrichProblemStarters(
  problem: ProblemDetail,
  slug: string,
  title: string,
  lcId?: number,
): ProblemDetail {
  const localFb = buildFallbackProblem(slug, title, lcId ?? 0)
  const merged = mergeStarterCode(problem, localFb)
  const filled: ProblemDetail = {
    ...problem,
    starter_code: {
      python: merged.python || getStarterForLanguage({ ...problem, starter_code: merged }, 'python'),
      cpp: merged.cpp || getStarterForLanguage({ ...problem, starter_code: merged }, 'cpp'),
    },
  }
  return filled
}
