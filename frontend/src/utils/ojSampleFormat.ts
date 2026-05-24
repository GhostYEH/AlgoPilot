/** 洛谷风格样例展示（与后端 stdio_io.leetcode_case_to_stdio 规则一致） */

export type OjSampleCase = {
  stdin?: string
  stdout?: string
  args?: unknown[]
  expected?: unknown
}

function isIntOrNoneList(val: unknown[]): boolean {
  return val.every((x) => x === null || typeof x === 'number')
}

function formatInputArg(val: unknown): string[] {
  if (val && typeof val === 'object' && !Array.isArray(val)) {
    const o = val as Record<string, unknown>
    if ('a' in o && 'b' in o && 'common' in o) {
      const lines: string[] = []
      for (const key of ['a', 'b', 'common'] as const) {
        const arr = (Array.isArray(o[key]) ? o[key] : []) as number[]
        lines.push(String(arr.length))
        if (arr.length) lines.push(arr.map(String).join(' '))
      }
      return lines
    }
    return [JSON.stringify(val)]
  }

  if (Array.isArray(val)) {
    if (val.length === 0) return ['0']
    if (isIntOrNoneList(val)) {
      const tokens = val.map((x) => (x === null ? 'null' : String(x)))
      return [String(val.length), tokens.join(' ')]
    }
    if (val.every((x) => typeof x === 'string')) {
      return val as string[]
    }
    if (val.every((x) => Array.isArray(x) && (x as number[]).every((y) => typeof y === 'number'))) {
      const rows = val as number[][]
      const lines = [String(rows.length)]
      for (const row of rows) lines.push(row.join(' '))
      return lines
    }
    return [JSON.stringify(val)]
  }

  if (typeof val === 'boolean') return [String(val)]
  if (typeof val === 'number') return [String(val)]
  if (typeof val === 'string') return [val]
  if (val === null || val === undefined) return ['0']
  return [String(val)]
}

function formatExpectedOutput(expected: unknown): string {
  if (expected === null || expected === undefined) return 'null'
  if (typeof expected === 'boolean') return expected ? 'true' : 'false'
  if (typeof expected === 'number') return String(expected)
  if (typeof expected === 'string') return expected
  if (Array.isArray(expected)) {
    if (expected.length === 0) return ''
    if (expected.every((x) => typeof x === 'number')) {
      return (expected as number[]).join(' ')
    }
    if (expected.every((x) => typeof x === 'string')) {
      return JSON.stringify(expected)
    }
    if (expected.every((x) => Array.isArray(x))) {
      const rows = expected as unknown[][]
      if (rows.every((row) => row.every((y) => typeof y === 'number'))) {
        return rows.map((row) => (row as number[]).join(' ')).join('\n')
      }
      return JSON.stringify(expected)
    }
    return JSON.stringify(expected)
  }
  return String(expected)
}

function argsToStdio(args: unknown[], expected: unknown): { in: string; out: string } {
  const linesIn: string[] = []
  for (const arg of args) {
    linesIn.push(...formatInputArg(arg))
  }
  return { in: linesIn.join('\n'), out: formatExpectedOutput(expected) }
}

export function formatSampleInput(c: OjSampleCase): string {
  if (c.stdin != null && c.stdin !== '') return String(c.stdin).replace(/\r\n/g, '\n').trimEnd()
  if (c.args) return argsToStdio(c.args, c.expected).in
  return ''
}

export function formatSampleOutput(c: OjSampleCase): string {
  if (c.stdout != null && c.stdout !== '') return String(c.stdout).replace(/\r\n/g, '\n').trimEnd()
  if (c.args) return argsToStdio(c.args, c.expected).out
  return ''
}

export function isStdioJudgeMode(judgeMode?: string, entry?: { mode?: string } | null): boolean {
  return judgeMode === 'stdio' || entry?.mode === 'stdio'
}
