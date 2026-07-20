/** 将助教回复中的 Markdown 转为安全 HTML（聊天气泡内展示） */

/** 围栏开始：单独一行 ``` 或 ```python 或 ```mermaid */
const OPEN_FENCE_RE = /^```([\w-]*)\s*$/
/** 围栏结束：单独一行 ```（无语言标识） */
const CLOSE_FENCE_RE = /^```\s*$/

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** mermaid.js 单例（懒加载，避免影响首屏） */
type MermaidApi = typeof import('mermaid').default
let _mermaidApi: MermaidApi | null = null
let _mermaidInitDone = false

async function loadMermaid(): Promise<MermaidApi> {
  if (!_mermaidApi) {
    _mermaidApi = (await import('mermaid')).default
  }
  if (!_mermaidInitDone) {
    _mermaidApi.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
    })
    _mermaidInitDone = true
  }
  return _mermaidApi
}

/** 行内格式：粗体、行内代码、链接、删除线、斜体 */
function inlineFormat(text: string): string {
  const tickCount = (text.match(/`/g) || []).length
  // 先处理链接 [text](url)，避免被后续替换破坏
  let out = text.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a class="ai-md-link" href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
  )
  // 删除线
  out = out.replace(/~~([^~]+)~~/g, '<del>$1</del>')
  // 粗体
  out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // 斜体（避免与粗体冲突，要求 * 两侧非 *）
  out = out.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
  // 行内代码（仅当反引号成对出现时）
  if (tickCount % 2 === 0) {
    out = out.replace(/`([^`]+)`/g, '<code class="ai-md-code">$1</code>')
  }
  return out
}

type ListKind = 'ul' | 'ol' | null

export function renderAiReplyHtml(raw: string): string {
  // Markdown 结构在原文上识别；普通文本与非 Mermaid 代码再分别转义。
  // 若先转义整段文本，Mermaid 的 `-->` 会变成 `--&gt;`，从而必然解析失败。
  const lines = raw.split('\n')
  const html: string[] = []
  let list: ListKind = null
  let inCode = false
  let codeLang = ''
  let codeBuf: string[] = []
  let inTable = false
  let tableHeader: string[] = []
  let tableRows: string[][] = []
  let inBlockquote = false
  let blockquoteBuf: string[] = []

  const closeList = () => {
    if (list) {
      html.push(list === 'ul' ? '</ul>' : '</ol>')
      list = null
    }
  }

  const closeBlockquote = () => {
    if (inBlockquote) {
      html.push(
        `<blockquote class="ai-md-quote">${inlineFormat(blockquoteBuf.join(' '))}</blockquote>`,
      )
      blockquoteBuf = []
      inBlockquote = false
    }
  }

  const flushTable = () => {
    if (!inTable) return
    if (tableHeader.length > 0) {
      html.push('<table class="ai-md-table">')
      html.push('<thead><tr>')
      for (const cell of tableHeader) {
        html.push(`<th>${inlineFormat(cell)}</th>`)
      }
      html.push('</tr></thead>')
      if (tableRows.length > 0) {
        html.push('<tbody>')
        for (const row of tableRows) {
          html.push('<tr>')
          for (const cell of row) {
            html.push(`<td>${inlineFormat(cell)}</td>`)
          }
          html.push('</tr>')
        }
        html.push('</tbody>')
      }
      html.push('</table>')
    }
    inTable = false
    tableHeader = []
    tableRows = []
  }

  const flushCodeBlock = (streaming = false) => {
    if (!inCode) return
    const extra = streaming ? ' ai-md-pre--streaming' : ''
    const lang = codeLang.trim().toLowerCase()
    if (lang === 'mermaid') {
      // mermaid 块：以占位 div 形式输出，由 enhanceMermaidBlocks 异步渲染
      const src = codeBuf.join('\n')
      const encoded = encodeURIComponent(src)
      html.push(
        `<div class="ai-md-mermaid" data-src="${encoded}"><div class="ai-md-mermaid-placeholder">正在渲染图解…</div></div>`,
      )
    } else {
      html.push(
        `<pre class="ai-md-pre${extra}"><code>${codeBuf.join('\n')}</code></pre>`,
      )
    }
    codeBuf = []
    codeLang = ''
    inCode = false
  }

  const openPara = (line: string) => {
    closeList()
    closeBlockquote()
    html.push(`<p class="ai-md-p">${inlineFormat(line)}</p>`)
  }

  /** 解析表格行：返回单元格数组，若非表格行返回 null */
  const parseTableRow = (line: string): string[] | null => {
    const trimmed = line.trim()
    if (!trimmed.startsWith('|') || !trimmed.endsWith('|')) return null
    // 去掉首尾管道符后按 | 切分
    const inner = trimmed.slice(1, -1)
    return inner.split('|').map((c) => c.trim())
  }

  /** 检测表格分隔行：| --- | :---: | ---: | */
  const isTableSeparator = (line: string): boolean => {
    const cells = parseTableRow(line)
    if (!cells) return false
    return cells.every((c) => /^:?-{3,}:?$/.test(c))
  }

  for (const line of lines) {
    const rawTrimmed = line.trim()
    const trimmed = escapeHtml(line).trim()

    // 代码块优先级最高
    if (!inCode) {
      const fenceMatch = rawTrimmed.match(OPEN_FENCE_RE)
      if (fenceMatch) {
        closeList()
        closeBlockquote()
        flushTable()
        inCode = true
        codeLang = fenceMatch[1] || ''
        continue
      }
    }

    if (inCode && CLOSE_FENCE_RE.test(rawTrimmed)) {
      flushCodeBlock(false)
      continue
    }

    if (inCode) {
      codeBuf.push(codeLang.trim().toLowerCase() === 'mermaid' ? line : escapeHtml(line))
      continue
    }

    // 表格处理
    const tableCells = parseTableRow(trimmed)
    if (tableCells) {
      if (!inTable) {
        // 进入表格：第一行是表头
        closeList()
        closeBlockquote()
        inTable = true
        tableHeader = tableCells
        continue
      }
      if (isTableSeparator(trimmed)) {
        // 分隔行，跳过
        continue
      }
      tableRows.push(tableCells)
      continue
    } else if (inTable) {
      // 表格结束
      flushTable()
    }

    if (!trimmed) {
      closeList()
      closeBlockquote()
      continue
    }

    // 水平线
    if (/^(---|\*\*\*|___)\s*$/.test(trimmed)) {
      closeList()
      closeBlockquote()
      html.push('<hr class="ai-md-hr" />')
      continue
    }

    // 引用块（escapeHtml 已将 > 转为 &gt;，故匹配 &gt;）
    const quote = trimmed.match(/^&gt;\s*(.*)$/)
    if (quote) {
      closeList()
      inBlockquote = true
      if (quote[1]) {
        blockquoteBuf.push(quote[1])
      }
      continue
    } else if (inBlockquote) {
      closeBlockquote()
    }

    // 标题
    const h4 = trimmed.match(/^####\s+(.+)$/)
    if (h4) {
      closeList()
      html.push(`<h4 class="ai-md-h">${inlineFormat(h4[1])}</h4>`)
      continue
    }

    const h3 = trimmed.match(/^###\s+(.+)$/)
    if (h3) {
      closeList()
      html.push(`<h3 class="ai-md-h">${inlineFormat(h3[1])}</h3>`)
      continue
    }

    const h2 = trimmed.match(/^##\s+(.+)$/)
    if (h2) {
      closeList()
      html.push(`<h2 class="ai-md-h ai-md-h--2">${inlineFormat(h2[1])}</h2>`)
      continue
    }

    const h1 = trimmed.match(/^#\s+(.+)$/)
    if (h1) {
      closeList()
      html.push(`<h2 class="ai-md-h ai-md-h--2">${inlineFormat(h1[1])}</h2>`)
      continue
    }

    // 无序列表：支持 •、-、*、+ 前缀
    const ul = trimmed.match(/^[•\-*+]\s+(.+)$/)
    if (ul) {
      if (list !== 'ul') {
        closeList()
        html.push('<ul class="ai-md-ul">')
        list = 'ul'
      }
      html.push(`<li>${inlineFormat(ul[1])}</li>`)
      continue
    }

    // 有序列表
    const ol = trimmed.match(/^\d+\.\s+(.+)$/)
    if (ol) {
      if (list !== 'ol') {
        closeList()
        html.push('<ol class="ai-md-ol">')
        list = 'ol'
      }
      html.push(`<li>${inlineFormat(ol[1])}</li>`)
      continue
    }

    openPara(trimmed)
  }

  if (inCode) {
    flushCodeBlock(true)
  }
  closeList()
  closeBlockquote()
  flushTable()

  return html.join('') || `<p class="ai-md-p">${inlineFormat(escapeHtml(raw))}</p>`
}

/** 渲染序号，保证后到的 enhance 调用可以中断前一次未完成的渲染 */
let _enhanceSeq = 0

/**
 * 扫描容器内的 `.ai-md-mermaid` 占位 div，逐个调用 mermaid.js 渲染为 SVG。
 *
 * 用法：在 v-html 设置后，于 nextTick 中调用 `enhanceMermaidBlocks(hostEl)`。
 * 幂等：已渲染过的节点（含 data-rendered 标记）会跳过。
 */
export async function enhanceMermaidBlocks(host: HTMLElement | null): Promise<void> {
  if (!host) return
  const blocks = Array.from(host.querySelectorAll<HTMLElement>('.ai-md-mermaid'))
  if (blocks.length === 0) return

  const seq = ++_enhanceSeq
  let mermaid: MermaidApi | null = null
  try {
    mermaid = await loadMermaid()
  } catch (e) {
    const reason = e instanceof Error ? e.message : 'mermaid 加载失败'
    for (const el of blocks) {
      if (el.dataset.rendered) continue
      el.classList.add('ai-md-mermaid--error')
      el.innerHTML = `<div class="ai-md-mermaid-placeholder">图解加载失败：${escapeHtml(reason)}</div>`
      el.dataset.rendered = 'error'
    }
    return
  }
  if (seq !== _enhanceSeq) return

  for (const el of blocks) {
    if (el.dataset.rendered) continue
    const encoded = el.dataset.src || ''
    const src = decodeURIComponent(encoded)
    if (!src.trim()) {
      el.dataset.rendered = 'empty'
      continue
    }
    try {
      const parsed = await mermaid.parse(src, { suppressErrors: true })
      if (parsed === false) throw new Error('Mermaid 语法校验失败')
      if (seq !== _enhanceSeq) return
      const id = `ai-md-mermaid-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
      const { svg } = await mermaid.render(id, src)
      if (seq !== _enhanceSeq) return
      if (svg.includes('Syntax error in text')) throw new Error('Mermaid 语法校验失败')
      el.innerHTML = svg
      el.classList.add('ai-md-mermaid--rendered')
      el.dataset.rendered = 'ok'
    } catch (e) {
      if (seq !== _enhanceSeq) return
      const reason = e instanceof Error ? e.message : 'Mermaid 渲染失败'
      el.classList.add('ai-md-mermaid--error')
      el.innerHTML = `<div class="ai-md-mermaid-placeholder">图解渲染失败：${escapeHtml(reason)}</div>`
      el.dataset.rendered = 'error'
    }
  }
}
