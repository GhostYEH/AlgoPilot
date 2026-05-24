/** 将助教回复中的 Markdown 转为安全 HTML（聊天气泡内展示） */

/** 围栏开始：单独一行 ``` 或 ```python */
const OPEN_FENCE_RE = /^```[\w-]*\s*$/
/** 围栏结束：单独一行 ```（无语言标识） */
const CLOSE_FENCE_RE = /^```\s*$/

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function inlineFormat(text: string): string {
  const tickCount = (text.match(/`/g) || []).length
  let out = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  if (tickCount % 2 === 0) {
    out = out.replace(/`([^`]+)`/g, '<code class="ai-md-code">$1</code>')
  }
  return out
}

type ListKind = 'ul' | 'ol' | null

export function renderAiReplyHtml(raw: string): string {
  const lines = escapeHtml(raw).split('\n')
  const html: string[] = []
  let list: ListKind = null
  let inCode = false
  let codeBuf: string[] = []

  const closeList = () => {
    if (list) {
      html.push(list === 'ul' ? '</ul>' : '</ol>')
      list = null
    }
  }

  const flushCodeBlock = (streaming = false) => {
    if (!inCode) return
    const extra = streaming ? ' ai-md-pre--streaming' : ''
    html.push(
      `<pre class="ai-md-pre${extra}"><code>${codeBuf.join('\n')}</code></pre>`,
    )
    codeBuf = []
    inCode = false
  }

  const openPara = (line: string) => {
    closeList()
    html.push(`<p class="ai-md-p">${inlineFormat(line)}</p>`)
  }

  for (const line of lines) {
    const trimmed = line.trim()

    if (!inCode && OPEN_FENCE_RE.test(trimmed)) {
      closeList()
      inCode = true
      continue
    }

    if (inCode && CLOSE_FENCE_RE.test(trimmed)) {
      flushCodeBlock(false)
      continue
    }

    if (inCode) {
      codeBuf.push(line)
      continue
    }

    if (!trimmed) {
      closeList()
      continue
    }

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

    const ul = trimmed.match(/^[•\-*]\s+(.+)$/)
    if (ul) {
      if (list !== 'ul') {
        closeList()
        html.push('<ul class="ai-md-ul">')
        list = 'ul'
      }
      html.push(`<li>${inlineFormat(ul[1])}</li>`)
      continue
    }

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

  return html.join('') || `<p class="ai-md-p">${inlineFormat(escapeHtml(raw))}</p>`
}
