function stripFenceAndPrefix(raw: string): string {
  let text = raw.trim()
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i)
  if (fence?.[1]) text = fence[1].trim()
  return text.replace(/^\s*json\s*(?:\\n|\r?\n)/i, '').trim()
}

function findBalancedJson(text: string): string | null {
  const objectStart = text.indexOf('{')
  const arrayStart = text.indexOf('[')
  const starts = [objectStart, arrayStart].filter((value) => value >= 0)
  if (!starts.length) return null
  const start = Math.min(...starts)
  let depth = 0
  let inString = false
  let escaped = false
  for (let i = start; i < text.length; i++) {
    const char = text[i]
    if (escaped) { escaped = false; continue }
    if (char === '\\' && inString) { escaped = true; continue }
    if (char === '"') { inString = !inString; continue }
    if (inString) continue
    if (char === '{' || char === '[') depth++
    if (char === '}' || char === ']') {
      depth--
      if (depth === 0) return text.slice(start, i + 1)
    }
  }
  return null
}

/** 容忍代码围栏、json 前缀、夹带说明，以及模型常见的二次 JSON 编码。 */
export function parseStructuredJson(raw: string): unknown | null {
  let text = stripFenceAndPrefix(raw ?? '')
  for (let pass = 0; pass < 4 && text; pass++) {
    try {
      const parsed = JSON.parse(text) as unknown
      if (typeof parsed === 'string') {
        text = stripFenceAndPrefix(parsed)
        continue
      }
      return parsed
    } catch {
      const balanced = findBalancedJson(text)
      if (balanced && balanced !== text) {
        text = balanced
        continue
      }
      if (text.includes('\\"domain_narrative\\"') || text.includes('\\"code\\"')) {
        const decoded = text
          .replace(/\\r\\n/g, '\n')
          .replace(/\\n/g, '\n')
          .replace(/\\"/g, '"')
        if (decoded !== text) {
          text = stripFenceAndPrefix(decoded)
          continue
        }
      }
      return null
    }
  }
  return null
}
