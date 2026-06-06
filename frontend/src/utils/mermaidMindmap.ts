type MindmapJson = {
  root?: string
  nodes?: Array<{ label: string; parent?: string }>
}

const FOOTER_MARKERS = [
  '依据知识库',
  '内容校验',
  '安全审查',
  '校验详情',
  '条知识库依据',
]

export function escapeMermaidLabel(value: string) {
  return String(value).replaceAll('\\', '\\\\').replaceAll('"', '\\"')
}

function stripKbAnnotations(raw: string) {
  let cleaned = raw.trim()
  cleaned = cleaned.replace(/```(?:mermaid)?\s*([\s\S]*?)```/i, '$1').trim()
  cleaned = cleaned
    .replace(/---\*\*依据知识库\*\*[\s\S]*/g, '')
    .replace(/\n\*\*依据知识库\*\*[\s\S]*/g, '')
    .replace(/---{2,}\s*依据知识库[\s\S]*/g, '')
    .replace(/\n---+\s*\n\*\*依据知识库\*\*[\s\S]*/g, '')
    .replace(/\n内容校验[\s\S]*/g, '')
    .replace(/\n安全审查[\s\S]*/g, '')
  const kept: string[] = []
  for (const line of cleaned.split(/\r?\n/)) {
    const stripped = line.trim()
    if (!stripped) continue
    if (stripped.startsWith('---') || stripped.startsWith('===')) break
    if (stripped.startsWith('%%')) continue
    if (stripped.includes('course:')) continue
    if (FOOTER_MARKERS.some(marker => stripped.includes(marker))) break
    kept.push(line)
  }
  return kept.join('\n').trim()
}

function cleanMindmapLabel(value: string, maxLen = 10) {
  let s = value.trim()
  s = s.replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1')
  s = s.replace(/^\d+[\.)、]\s*/, '')
  s = s.replace(/^ch\d+[-]?\s*/i, '')
  const parts = s.split(/[:：]/, 2)
  if (parts.length === 2) {
    const before = parts[0].trim()
    const after = parts[1].trim()
    s = /[\u4e00-\u9fff]/.test(after) && after.length <= 12 ? after : before
  }
  s = s.replace(/^[a-z]+[-]?/i, '')
  s = s.replace(/[。，、；！？.!?;,（）()\/／\s]+/g, '')
  return s.slice(0, maxLen)
}

function fallbackMindmap(topic = '学习主题') {
  const root = cleanMindmapLabel(topic, 24) || '学习主题'
  return ['mindmap', `  root((${escapeMermaidLabel(root)}))`, '    核心概念', '    关键算法', '    应用场景'].join('\n')
}

function normalizeMindmapSyntax(text: string, fallbackTopic = '学习主题') {
  const lines = stripKbAnnotations(text).split(/\r?\n/)
  if (!lines[0]?.trim().startsWith('mindmap')) return fallbackMindmap(fallbackTopic)
  const fixed = ['mindmap']
  let hasRoot = false
  for (const line of lines.slice(1)) {
    const stripped = line.trim()
    if (!stripped) continue
    if (stripped.startsWith('---') || FOOTER_MARKERS.some(marker => stripped.includes(marker))) break
    if (stripped.startsWith('root')) {
      const raw = stripped.replace(/^root\s*[\(\[\{]+/, '').replace(/[\)\]\}]+$/, '')
      const label = cleanMindmapLabel(raw, 24) || cleanMindmapLabel(fallbackTopic, 24) || '学习主题'
      if (!hasRoot) {
        fixed.push(`  root((${escapeMermaidLabel(label)}))`)
        hasRoot = true
      } else {
        fixed.push(`    ${escapeMermaidLabel(label)}`)
      }
      continue
    }
    const label = cleanMindmapLabel(stripped)
    if (!label) continue
    const rawIndent = line.length - line.trimStart().length
    const indent = Math.max(4, rawIndent > 2 ? rawIndent : 4)
    fixed.push(`${' '.repeat(indent)}${escapeMermaidLabel(label)}`)
  }
  if (!hasRoot) fixed.splice(1, 0, `  root((${escapeMermaidLabel(cleanMindmapLabel(fallbackTopic, 24) || '学习主题')}))`)
  return fixed.length > 2 ? fixed.join('\n') : fallbackMindmap(fallbackTopic)
}

function parseFlowchartLabel(raw: string) {
  const quoted = raw.match(/\["?([^"\]]+)"?\]|\(([^)]+)\)/)
  return quoted?.[1] ?? quoted?.[2] ?? raw
}

function convertFlowchartToMindmap(text: string, fallbackTopic = '学习主题') {
  const labels = new Map<string, string>()
  const children = new Map<string, string[]>()
  const childIds = new Set<string>()
  for (const line of stripKbAnnotations(text).split(/\r?\n/).slice(1)) {
    const stripped = line.trim()
    if (!stripped || stripped.startsWith('%%')) continue
    const edge = stripped.match(/^(\w+)(?:\[[^\]]+\]|\([^)]+\))?\s*--?>\s*(\w+)(?:\[[^\]]+\]|\([^)]+\))?/)
    const node = stripped.match(/^(\w+)(\[[^\]]+\]|\([^)]+\))/)
    if (node) labels.set(node[1], parseFlowchartLabel(node[2]))
    if (!edge) continue
    const [leftRaw, rightRaw] = stripped.split(/--?>/)
    const left = leftRaw.trim()
    const right = rightRaw.trim()
    const srcId = edge[1]
    const dstId = edge[2]
    labels.set(srcId, parseFlowchartLabel(left.replace(/^(\w+)/, '')))
    labels.set(dstId, parseFlowchartLabel(right.replace(/^(\w+)/, '')))
    if (!children.has(srcId)) children.set(srcId, [])
    children.get(srcId)!.push(dstId)
    childIds.add(dstId)
  }
  const roots = [...labels.keys()].filter(id => !childIds.has(id))
  const rootId = roots[0] ?? [...children.keys()][0]
  if (!rootId) return fallbackMindmap(fallbackTopic)
  const root = cleanMindmapLabel(labels.get(rootId) || fallbackTopic, 24) || '学习主题'
  const lines = ['mindmap', `  root((${escapeMermaidLabel(root)}))`]
  const visited = new Set<string>()
  const walk = (id: string, depth: number) => {
    if (visited.has(id)) return
    visited.add(id)
    for (const child of children.get(id) ?? []) {
      const label = cleanMindmapLabel(labels.get(child) || child)
      if (!label) continue
      lines.push(`${'    '.repeat(depth + 1)}${escapeMermaidLabel(label)}`)
      walk(child, depth + 1)
    }
  }
  walk(rootId, 0)
  return lines.length > 2 ? lines.join('\n') : fallbackMindmap(root)
}

function jsonToMindmap(content: string) {
  const data = JSON.parse(content) as MindmapJson
  const rootLabel = cleanMindmapLabel(String(data.root ?? '主题'), 24) || '主题'
  const nodes = data.nodes ?? []
  const childrenOf = new Map<string, string[]>()
  for (const n of nodes) {
    const parent = n.parent ?? rootLabel
    if (!childrenOf.has(parent)) childrenOf.set(parent, [])
    childrenOf.get(parent)!.push(n.label)
  }
  const lines = ['mindmap', `  root((${escapeMermaidLabel(rootLabel)}))`]
  const visited = new Set<string>()
  const walk = (label: string, depth: number) => {
    if (visited.has(label)) return
    visited.add(label)
    for (const kid of childrenOf.get(label) ?? []) {
      const cleanKid = cleanMindmapLabel(kid)
      if (!cleanKid) continue
      lines.push(`${'    '.repeat(depth + 1)}${escapeMermaidLabel(cleanKid)}`)
      walk(kid, depth + 1)
    }
  }
  walk(rootLabel, 0)
  for (const n of nodes) {
    if (!visited.has(n.label)) {
      const label = cleanMindmapLabel(n.label)
      if (label) lines.push(`    ${escapeMermaidLabel(label)}`)
    }
  }
  return lines.length > 2 ? lines.join('\n') : fallbackMindmap(rootLabel)
}

export function normalizeMindmapSource(content: string, fallbackTopic = '学习主题') {
  const cleaned = stripKbAnnotations(content)
  if (!cleaned) return ''
  if (cleaned.startsWith('mindmap')) return normalizeMindmapSyntax(cleaned, fallbackTopic)
  if (cleaned.startsWith('flowchart') || cleaned.startsWith('graph')) {
    return convertFlowchartToMindmap(cleaned, fallbackTopic)
  }
  if (cleaned.startsWith('{')) {
    try {
      return jsonToMindmap(cleaned)
    } catch {
      return fallbackMindmap(fallbackTopic)
    }
  }
  return fallbackMindmap(fallbackTopic)
}
