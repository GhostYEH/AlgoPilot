<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import DomainStructurePanels from '@/components/resources/DomainStructurePanels.vue'
import TraceAnimationPlayer from '@/components/resources/TraceAnimationPlayer.vue'
import {
  looksLikeUnparsedDomainJson,
  parseDomainStructureContent,
} from '@/utils/domainStructureContent'
import { normalizeMindmapSource } from '@/utils/mermaidMindmap'
import { renderAiReplyHtml } from '@/utils/renderAiReply'

type MermaidApi = typeof import('mermaid').default
let mermaidApi: MermaidApi | null = null
let mermaidRenderSeq = 0

const props = defineProps<{
  resourceType: string
  content: string
  meta?: Record<string, unknown>
}>()

const mermaidHost = ref<HTMLElement | null>(null)
const mermaidError = ref('')

function robustJsonParse(text: string): unknown | null {
  if (!text || typeof text !== 'string') return null
  let cleaned = text.trim()
  const kbIdx = cleaned.indexOf('---**依据知识库**')
  if (kbIdx >= 0) cleaned = cleaned.slice(0, kbIdx)
  cleaned = cleaned.split('\n').filter(line => !line.includes('course:')).join('\n').trim()
  const fence = cleaned.match(/```(?:json)?\s*([\s\S]*?)```/i)
  if (fence?.[1]) cleaned = fence[1].trim()
  try {
    return JSON.parse(cleaned)
  } catch {
    const start = cleaned.indexOf('{')
    if (start < 0) return null
    let depth = 0
    let inStr = false
    let esc = false
    for (let i = start; i < cleaned.length; i++) {
      const ch = cleaned[i]
      if (esc) { esc = false; continue }
      if (ch === '\\' && inStr) { esc = true; continue }
      if (ch === '"') { inStr = !inStr; continue }
      if (inStr) continue
      if (ch === '{' || ch === '[') depth++
      else if (ch === '}' || ch === ']') {
        depth--
        if (depth === 0) {
          try { return JSON.parse(cleaned.slice(start, i + 1)) } catch { return null }
        }
      }
    }
  }
  return null
}

const parsed = computed(() => {
  if (props.resourceType === 'document' || props.resourceType === 'code_case') {
    return null
  }
  return robustJsonParse(safeContent.value) as Record<string, unknown> | null
})

const isQuiz = computed(
  () => props.resourceType === 'exercises' || props.meta?.format === 'quiz_json',
)
const isMindmap = computed(
  () => props.resourceType === 'mindmap' || props.meta?.format === 'mindmap_json',
)
const isReading = computed(
  () => props.resourceType === 'reading' || props.meta?.format === 'leveled_reading_json',
)
const isTrace = computed(
  () => props.resourceType === 'trace_animation' || props.meta?.format === 'trace_json',
)
const isPpt = computed(
  () => props.resourceType === 'ppt' || props.meta?.format === 'ppt_outline_json',
)
const safeContent = computed(() => props.content ?? '')
const looksLikeRawJson = computed(() => {
  const text = safeContent.value.trim()
  return text.startsWith('{') || text.startsWith('[') || /^```json\b/i.test(text)
})
const domainStructure = computed(() => parseDomainStructureContent(safeContent.value))
const isDocOrScenario = computed(
  () => props.resourceType === 'document' || props.resourceType === 'code_case',
)
const isDomainStructure = computed(
  () =>
    !!domainStructure.value &&
    (isDocOrScenario.value || props.meta?.format === 'domain_structure_json'),
)
const unparsedDomainJson = computed(
  () =>
    isDocOrScenario.value &&
    (looksLikeUnparsedDomainJson(safeContent.value) || looksLikeRawJson.value),
)
const legacyMarkdown = computed(
  () =>
    isDocOrScenario.value &&
    !domainStructure.value &&
    !unparsedDomainJson.value &&
    !!safeContent.value.trim(),
)
const domainStructureMode = computed((): 'document' | 'scenario' =>
  props.resourceType === 'code_case' ? 'scenario' : 'document',
)
const structuredPayloadUnavailable = computed(() => {
  const format = String(props.meta?.format ?? '')
  return (
    looksLikeRawJson.value ||
    format.includes('json') ||
    ['exercises', 'reading', 'trace_animation'].includes(props.resourceType)
  )
})

const mermaidSrc = computed(() => {
  if (!isMindmap.value) return ''
  return normalizeMindmapSource(safeContent.value)
})

async function loadMermaid() {
  if (!mermaidApi) {
    mermaidApi = (await import('mermaid')).default
    mermaidApi.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })
  }
  return mermaidApi
}

async function renderMermaid() {
  const renderSeq = ++mermaidRenderSeq
  mermaidError.value = ''
  const host = mermaidHost.value
  if (host) host.innerHTML = ''
  if (!isMindmap.value || !mermaidSrc.value) return
  await nextTick()
  const currentHost = mermaidHost.value
  if (!currentHost) return
  try {
    const mermaid = await loadMermaid()
    if (renderSeq !== mermaidRenderSeq) return
    const parsed = await mermaid.parse(mermaidSrc.value, { suppressErrors: true })
    if (parsed === false) throw new Error('Mermaid 语法校验失败')
    const { svg } = await mermaid.render(`mmd-preview-${Date.now()}-${renderSeq}`, mermaidSrc.value)
    if (renderSeq !== mermaidRenderSeq) return
    if (svg.includes('Syntax error in text')) throw new Error('Mermaid 语法校验失败')
    currentHost.innerHTML = svg
  } catch (e) {
    if (renderSeq !== mermaidRenderSeq) return
    mermaidError.value = e instanceof Error ? e.message : 'Mermaid 渲染失败'
    currentHost.innerHTML = '<div class="mindmap-placeholder">思维导图暂不可渲染</div>'
  }
}

watch([mermaidSrc], () => void renderMermaid(), { flush: 'post' })
onMounted(() => void renderMermaid())

interface QuizQ {
  type: string
  stem: string
  options?: string[]
  hint?: string
  focus?: string
  difficulty?: string
  answer?: string
  explanation?: string
}

const quizQuestions = computed((): QuizQ[] => {
  if (!parsed.value || !Array.isArray((parsed.value as Record<string, unknown>).questions)) return []
  return (parsed.value as { questions: QuizQ[] }).questions
})

const quizAnswers = reactive<Record<number, string>>({})
const quizRevealed = reactive<Record<number, boolean>>({})
const quizSubmitted = ref(false)

function revealHint(i: number) {
  quizRevealed[i] = true
}

function submitQuiz() {
  quizSubmitted.value = true
}

function resetQuiz() {
  Object.keys(quizAnswers).forEach(k => delete quizAnswers[Number(k)])
  Object.keys(quizRevealed).forEach(k => delete quizRevealed[Number(k)])
  quizSubmitted.value = false
}

const answeredCount = computed(() => {
  return quizQuestions.value.filter((_, i) => quizAnswers[i]?.trim()).length
})

function difficultyLabel(value?: string): string {
  return { easy: '基础', medium: '进阶', hard: '挑战' }[value ?? 'medium'] ?? '进阶'
}

interface PptSlide {
  layout: string
  title?: string
  subtitle?: string
  bullets?: string[]
  code?: string
  notes?: string
}

const pptOutline = computed<{ title?: string; slides?: PptSlide[] } | null>(() => {
  if (!isPpt.value) return null
  const data = parsed.value as Record<string, unknown> | null
  if (!data) return null
  const slides = Array.isArray(data.slides) ? (data.slides as PptSlide[]) : []
  return { title: typeof data.title === 'string' ? data.title : '', slides }
})

const pptSlides = computed<PptSlide[]>(() => pptOutline.value?.slides ?? [])

const PPT_LAYOUT_LABELS: Record<string, string> = {
  cover: '封面',
  agenda: '目录',
  content: '正文',
  code: '代码',
  closing: '收尾',
}

function pptLayoutLabel(layout: string): string {
  return PPT_LAYOUT_LABELS[layout] ?? layout
}
</script>

<template>
  <div v-if="isQuiz && quizQuestions.length" class="quiz-preview">
    <div class="quiz-toolbar">
      <span class="quiz-progress">已答 {{ answeredCount }} / {{ quizQuestions.length }} 题</span>
      <div class="quiz-toolbar-actions">
        <el-button v-if="!quizSubmitted" type="primary" size="small" :disabled="answeredCount === 0" @click="submitQuiz">
          提交答案
        </el-button>
        <el-button v-else size="small" @click="resetQuiz">
          重新作答
        </el-button>
      </div>
    </div>
    <div
      v-for="(q, i) in quizQuestions"
      :key="i"
      class="quiz-item"
      :class="{ 'quiz-item--answered': quizAnswers[i]?.trim(), 'quiz-item--submitted': quizSubmitted }"
    >
      <div class="quiz-head">
        <span class="quiz-badge">{{ q.type === 'choice' ? '选择题' : '填空题' }}</span>
        <span class="quiz-diff">{{ difficultyLabel(q.difficulty) }}</span>
        <span v-if="q.focus" class="quiz-focus-tag">考查：{{ q.focus }}</span>
      </div>
      <p class="quiz-stem">{{ i + 1 }}. {{ q.stem }}</p>

      <el-radio-group
        v-if="q.type === 'choice' && q.options?.length"
        v-model="quizAnswers[i]"
        :disabled="quizSubmitted"
        class="quiz-options"
      >
        <el-radio v-for="(opt, j) in q.options" :key="j" :value="opt" class="quiz-option">
          <span class="quiz-option-label">{{ String.fromCharCode(65 + j) }}.</span> {{ opt }}
        </el-radio>
      </el-radio-group>

      <el-input
        v-else-if="q.type === 'fill'"
        v-model="quizAnswers[i]"
        :disabled="quizSubmitted"
        placeholder="输入你的答案"
        class="quiz-fill"
      />

      <div class="quiz-actions">
        <el-button link type="primary" size="small" @click="revealHint(i)">查看提示</el-button>
      </div>
      <p v-if="quizRevealed[i] && q.hint" class="quiz-hint">💡 {{ q.hint }}</p>
      <div v-if="quizSubmitted && q.answer" class="quiz-answer">
        <strong v-if="q.type === 'choice'" :class="quizAnswers[i] === q.answer ? 'quiz-correct' : 'quiz-wrong'">
          {{ quizAnswers[i] === q.answer ? '回答正确' : '回答有误' }}
        </strong>
        <p><b>参考答案：</b>{{ q.answer }}</p>
        <p v-if="q.explanation"><b>解析：</b>{{ q.explanation }}</p>
      </div>
    </div>
  </div>

  <div v-else-if="isMindmap && mermaidSrc" class="mindmap-preview">
    <div ref="mermaidHost" class="mindmap-mermaid-host" />
    <p v-if="mermaidError" class="mindmap-err">{{ mermaidError }}</p>
  </div>

  <div v-else-if="isMindmap && parsed" class="mindmap-json">
    <p><strong>根节点：</strong>{{ parsed.root }}</p>
    <ul v-if="Array.isArray(parsed.nodes)">
      <li v-for="(n, i) in (parsed.nodes as Array<Record<string, string>>)" :key="i">
        {{ n.label }} <span class="muted">({{ n.parent }})</span>
      </li>
    </ul>
  </div>

  <TraceAnimationPlayer
    v-else-if="isTrace && parsed"
    :payload="parsed"
    :meta="meta"
  />

  <DomainStructurePanels
    v-else-if="isDomainStructure"
    :content="content"
    :mode="domainStructureMode"
  />

  <div v-else-if="isPpt && pptSlides.length" class="ppt-preview">
    <div class="ppt-deck-header">
      <span class="ppt-deck-icon">PPT</span>
      <div class="ppt-deck-title">
        <span class="ppt-deck-label">课程讲义 PPT 大纲</span>
        <strong>{{ pptOutline?.title || '未命名讲义' }}</strong>
        <span class="ppt-deck-meta">共 {{ pptSlides.length }} 页 · 可在右侧「下载 PPT」生成 .pptx 文件</span>
      </div>
    </div>
    <div class="ppt-slide-list">
      <div
        v-for="(slide, i) in pptSlides"
        :key="i"
        class="ppt-slide"
        :class="`ppt-slide--${slide.layout}`"
      >
        <div class="ppt-slide-side">
          <span class="ppt-slide-index">{{ i + 1 }}</span>
          <span class="ppt-slide-layout">{{ pptLayoutLabel(slide.layout) }}</span>
        </div>
        <div class="ppt-slide-body">
          <h4 v-if="slide.title">{{ slide.title }}</h4>
          <p v-if="slide.subtitle" class="ppt-slide-subtitle">{{ slide.subtitle }}</p>
          <ul v-if="slide.bullets?.length" class="ppt-slide-bullets">
            <li v-for="(b, j) in slide.bullets" :key="j">{{ b }}</li>
          </ul>
          <pre v-if="slide.code" class="ppt-slide-code"><code>{{ slide.code }}</code></pre>
          <p v-if="slide.notes" class="ppt-slide-notes">讲者备注：{{ slide.notes }}</p>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="isReading && parsed?.levels" class="reading-preview">
    <h3>分层拓展阅读</h3>
    <p class="muted">{{ parsed.reading_goal }}</p>
    <section
      v-for="(level, i) in (parsed.levels as Array<Record<string, unknown>>)"
      :key="i"
      class="reading-level"
    >
      <h4>{{ level.level }}</h4>
      <p class="muted">{{ level.fit_for }}</p>
      <div
        v-for="(item, j) in ((level.items as Array<Record<string, string>>) ?? [])"
        :key="j"
        class="reading-item"
      >
        <strong>{{ item.title }}</strong>
        <span>{{ item.type }}</span>
        <p>{{ item.why }}</p>
        <small>读后任务：{{ item.task }}</small>
      </div>
    </section>
  </div>

  <el-alert
    v-else-if="unparsedDomainJson"
    type="warning"
    :closable="false"
    show-icon
    title="双域 JSON 解析失败"
    description="内容似为 Domain/Structure 结构但格式不完整。请重新生成资源，或联系管理员检查 Agent 输出。"
  />

  <div
    v-else-if="legacyMarkdown"
    class="preview-body ai-md-body"
    v-html="renderAiReplyHtml(content)"
  />

  <el-alert
    v-else-if="parsed || structuredPayloadUnavailable"
    type="info"
    :closable="false"
    show-icon
    title="内容暂时无法展示"
    description="系统已拦截未完成整理的结构化数据，请重新生成这份资源。"
  />

  <div v-else class="preview-body ai-md-body" v-html="renderAiReplyHtml(content)" />
</template>

<style scoped>
.quiz-preview {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.quiz-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.quiz-progress {
  font-size: 13px;
  color: var(--alp-color-primary);
  font-weight: 500;
}

.quiz-toolbar-actions {
  display: flex;
  gap: 8px;
}

.quiz-item {
  padding: 16px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: color-mix(in srgb, var(--alp-bg-soft-block) 60%, transparent);
  transition: border-color 0.25s;
}

.quiz-item--answered {
  border-color: color-mix(in srgb, var(--alp-color-primary) 40%, transparent);
}

.quiz-item--submitted {
  opacity: 0.85;
}

.quiz-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.quiz-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-primary) 15%, transparent);
  color: var(--alp-color-primary);
  font-weight: 500;
}

.quiz-diff {
  font-size: 10px;
  color: var(--alp-color-muted);
}

.quiz-focus-tag {
  font-size: 10px;
  color: var(--alp-color-primary);
  margin-left: auto;
}

.quiz-stem {
  margin: 0 0 12px;
  font-weight: 600;
  line-height: 1.5;
  font-size: 14px;
}

.quiz-options {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 10px;
}

.quiz-option {
  width: 100%;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  transition: background 0.2s, border-color 0.2s;
}

.quiz-option:hover {
  background: color-mix(in srgb, var(--alp-color-primary) 8%, transparent);
}

.quiz-option-label {
  font-weight: 600;
  margin-right: 4px;
  color: var(--alp-color-primary);
}

.quiz-fill {
  margin-bottom: 10px;
  max-width: 400px;
}

.quiz-actions {
  margin-top: 4px;
}

.quiz-hint {
  font-size: 13px;
  color: var(--alp-color-muted);
  margin: 8px 0 0;
  padding: 6px 10px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--el-color-warning-light-9) 40%, transparent);
}

.quiz-answer {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color-primary-light-9) 65%, transparent);
  font-size: 13px;
  line-height: 1.65;
}

.quiz-answer p { margin: 4px 0 0; }
.quiz-correct { color: var(--el-color-success); }
.quiz-wrong { color: var(--el-color-danger); }

.mindmap-preview {
  min-height: 280px;
}

.mindmap-mermaid-host {
  min-height: 280px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  background: #0f172a;
  overflow: auto;
}

.mindmap-mermaid-host :deep(svg) {
  max-width: 100%;
  height: auto;
  min-height: 240px;
}

.mindmap-mermaid-host :deep(.mindmap-placeholder) {
  color: #94a3b8;
  font-size: 13px;
}

.mindmap-err {
  color: #f87171;
  font-size: 12px;
  margin-top: 8px;
}

.mindmap-json .muted {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.preview-body {
  line-height: 1.6;
  font-size: 14px;
}

.reading-level {
  margin-bottom: 12px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.reading-item span,
.reading-item small,
.muted {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.reading-item strong {
  display: block;
  margin: 6px 0;
}

.reading-item p {
  margin: 6px 0;
  line-height: 1.55;
}

.reading-level h4 {
  margin: 0 0 6px;
  color: var(--alp-color-primary);
}

.reading-item {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--alp-color-border);
}

/* PPT 大纲预览：沿用 --alp-* 全局变量，保持与暗色主题一致 */
.ppt-preview {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ppt-deck-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--alp-color-primary) 10%, var(--alp-bg-soft-block));
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 35%, transparent);
}

.ppt-deck-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: var(--alp-color-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.ppt-deck-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.ppt-deck-label {
  font-size: 11px;
  color: var(--alp-color-muted);
  letter-spacing: 0.5px;
}

.ppt-deck-title strong {
  font-size: 16px;
  color: var(--alp-color-primary);
  line-height: 1.3;
}

.ppt-deck-meta {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.ppt-slide-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ppt-slide {
  display: flex;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--alp-bg-soft-block);
  transition: border-color 0.2s;
}

.ppt-slide:hover {
  border-color: color-mix(in srgb, var(--alp-color-primary) 40%, transparent);
}

.ppt-slide-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 56px;
  padding: 10px 4px;
  background: color-mix(in srgb, var(--alp-color-primary) 12%, transparent);
  color: var(--alp-color-primary);
  flex-shrink: 0;
}

.ppt-slide-index {
  font-size: 16px;
  font-weight: 700;
  line-height: 1;
}

.ppt-slide-layout {
  font-size: 10px;
  letter-spacing: 0.5px;
  opacity: 0.85;
}

.ppt-slide--cover .ppt-slide-side,
.ppt-slide--closing .ppt-slide-side {
  background: color-mix(in srgb, var(--alp-color-primary) 25%, transparent);
}

.ppt-slide--code .ppt-slide-side {
  background: color-mix(in srgb, var(--el-color-warning-light-9) 30%, transparent);
  color: var(--el-color-warning);
}

.ppt-slide-body {
  flex: 1;
  padding: 12px 14px;
  min-width: 0;
}

.ppt-slide-body h4 {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-text);
  line-height: 1.4;
}

.ppt-slide-subtitle {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.ppt-slide-bullets {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.ppt-slide-bullets li {
  margin: 2px 0;
}

.ppt-slide-code {
  margin: 6px 0 0;
  padding: 10px 12px;
  background: #181f1d;
  border-radius: 6px;
  overflow: auto;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.55;
  color: #e6e6e6;
}

.ppt-slide-code code {
  font-family: inherit;
  white-space: pre;
}

.ppt-slide-notes {
  margin: 8px 0 0;
  padding: 6px 10px;
  font-size: 11px;
  color: var(--alp-color-muted);
  background: color-mix(in srgb, var(--alp-color-primary) 6%, transparent);
  border-radius: 6px;
  line-height: 1.5;
}

</style>
