<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import mermaid from 'mermaid'
import type { GeneratedResource } from '@/api/orchestrator'
import CodeEditor from '@/components/oj/CodeEditor.vue'
import TraceSequenceViz from '@/components/oj/trace/TraceSequenceViz.vue'
import TraceAssociativeViz from '@/components/oj/trace/TraceAssociativeViz.vue'
import DomainStructurePanels from '@/components/resources/DomainStructurePanels.vue'
import SafetyValidationPanel from '@/components/resources/SafetyValidationPanel.vue'
import {
  looksLikeUnparsedDomainJson,
  parseDomainStructureContent,
} from '@/utils/domainStructureContent'
import { renderAiReplyHtml } from '@/utils/renderAiReply'
import { CORE_RESOURCE_TAB_META } from '@/utils/agentConsole'
import { synthesizeTtsAudio } from '@/api/tts'
import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'
import {
  associativeEntries,
  associativeViewHint,
  isAssociativeSnapshot,
  isSequenceSnapshot,
  sequenceItems,
  sequenceViewHint,
} from '@/utils/traceProtocol'

const props = defineProps<{
  resources: GeneratedResource[]
  activeTab?: string
}>()

const emit = defineEmits<{ 'update:activeTab': [key: string] }>()

const tab = ref(props.activeTab ?? 'document')
const mermaidHost = ref<HTMLElement | null>(null)
const mermaidError = ref('')

watch(
  () => props.activeTab,
  (v) => {
    if (v) tab.value = v
  },
)

watch(tab, (v) => emit('update:activeTab', v))

const resourceMap = computed(() => {
  const map = new Map<string, GeneratedResource>()
  for (const r of props.resources) {
    const key = normalizeType(r.resource_type)
    if (!map.has(key)) map.set(key, r)
  }
  return map
})

function normalizeType(t: string): string {
  return t
}

const tabs = computed(() =>
  CORE_RESOURCE_TAB_META.map((meta) => ({
    ...meta,
    resource: resourceMap.value.get(meta.key) ?? null,
    ready: resourceMap.value.has(meta.key),
  })),
)

const current = computed(() => resourceMap.value.get(tab.value) ?? null)

// --- 教案 / 沙盒：Domain · Structure 双域 ---
const docResource = computed(() => resourceMap.value.get('document') ?? null)
const scenarioResource = computed(() => resourceMap.value.get('code_case') ?? null)

const docPayload = computed(() =>
  docResource.value ? parseDomainStructureContent(docResource.value.content) : null,
)

const scenarioPayload = computed(() =>
  scenarioResource.value ? parseDomainStructureContent(scenarioResource.value.content) : null,
)

const docUnparsedJson = computed(
  () => !!docResource.value && looksLikeUnparsedDomainJson(docResource.value.content),
)
const scenarioUnparsedJson = computed(
  () => !!scenarioResource.value && looksLikeUnparsedDomainJson(scenarioResource.value.content),
)

const docHtml = computed(() => {
  const r = resourceMap.value.get('document')
  if (!r || docPayload.value) return ''
  return renderAiReplyHtml(r.content)
})

// --- Mermaid ---
const mermaidSrc = computed(() => {
  const r = resourceMap.value.get('mindmap')
  if (!r) return ''
  const c = r.content.trim()
  if (c.startsWith('{')) {
    try {
      const data = JSON.parse(c) as { root?: string; nodes?: Array<{ label: string }> }
      const labels = [data.root, ...(data.nodes?.map((n) => n.label) ?? [])].filter(Boolean)
      return `flowchart TD\n  root["${labels[0] ?? '主题'}"]\n${labels
        .slice(1, 8)
        .map((l, i) => `  n${i}["${l}"] --> root`)
        .join('\n')}`
    } catch {
      return c
    }
  }
  return c
})

async function renderMermaid() {
  mermaidError.value = ''
  if (tab.value !== 'mindmap' || !mermaidSrc.value) return
  await nextTick()
  const host = mermaidHost.value
  if (!host) return
  try {
    mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })
    const { svg } = await mermaid.render(`mmd-${Date.now()}`, mermaidSrc.value)
    host.innerHTML = svg
  } catch (e) {
    mermaidError.value = e instanceof Error ? e.message : 'Mermaid 渲染失败'
    host.innerHTML = `<pre class="mermaid-fallback">${mermaidSrc.value}</pre>`
  }
}

watch([tab, mermaidSrc], () => void renderMermaid(), { flush: 'post' })
onMounted(() => void renderMermaid())

// --- Quiz ---
interface QuizQ {
  type: string
  stem: string
  options?: string[]
  hint?: string
  focus?: string
  difficulty?: string
}

const quizQuestions = computed((): QuizQ[] => {
  const r = resourceMap.value.get('exercises')
  if (!r) return []
  try {
    const data = JSON.parse(r.content) as { questions?: QuizQ[] }
    return data.questions ?? []
  } catch {
    return []
  }
})

const quizAnswers = ref<Record<number, string>>({})
const quizRevealed = ref<Record<number, boolean>>({})

function revealHint(i: number) {
  quizRevealed.value = { ...quizRevealed.value, [i]: true }
}

// --- Scenario（旧版 Markdown 兼容）---
const scenarioLegacy = computed(() => {
  const raw = resourceMap.value.get('code_case')?.content ?? ''
  return scenarioPayload.value ? null : raw
})

const scenarioBg = computed(() =>
  scenarioLegacy.value ? extractSection(scenarioLegacy.value, '剧本背景') : '',
)
const scenarioGoal = computed(() =>
  scenarioLegacy.value ? extractSection(scenarioLegacy.value, '任务目标') : '',
)
const scenarioCode = computed(() =>
  scenarioLegacy.value ? extractCodeBlock(scenarioLegacy.value) : '',
)
const scenarioEditorCode = ref('')

watch(
  () => scenarioPayload.value?.structure_logic?.code_framework ?? scenarioCode.value,
  (c) => {
    scenarioEditorCode.value = c
  },
  { immediate: true },
)

function extractSection(md: string, heading: string): string {
  const re = new RegExp(`##\\s*${heading}[\\s\\S]*?(?=##|$)`, 'i')
  const m = md.match(re)
  if (!m) return ''
  return m[0].replace(/^##[^\n]*\n?/, '').trim()
}

function extractCodeBlock(md: string): string {
  const m = md.match(/```(?:python|py)?\s*([\s\S]*?)```/i)
  return m?.[1]?.trim() ?? md.slice(0, 800)
}

// --- Trace ---
interface TracePayload {
  code?: string
  steps?: TraceStep[]
  verdict?: string
  narration_hint?: string
  title?: string
}

const tracePayload = computed((): TracePayload | null => {
  const r = resourceMap.value.get('trace_animation')
  if (!r) return null
  try {
    return JSON.parse(r.content) as TracePayload
  } catch {
    return null
  }
})

const traceStepIndex = ref(0)

const traceSteps = computed(() => tracePayload.value?.steps ?? [])

watch(traceSteps, () => {
  traceStepIndex.value = 0
})

const currentTraceStep = computed(() => traceSteps.value[traceStepIndex.value] ?? null)

const tracePrevStep = computed(() =>
  traceStepIndex.value > 0 ? traceSteps.value[traceStepIndex.value - 1] : null,
)

function pickPrimaryVar(step: TraceStep | null): string | null {
  if (!step?.vars) return null
  const changed = step.changed ?? []
  if (changed.length) return changed[0]
  return Object.keys(step.vars)[0] ?? null
}

const traceVarName = computed(() => pickPrimaryVar(currentTraceStep.value))

const traceSnap = computed((): TraceVarSnapshot | null => {
  const name = traceVarName.value
  if (!name || !currentTraceStep.value?.vars) return null
  return (currentTraceStep.value.vars[name] as TraceVarSnapshot) ?? null
})

const tracePrevSnap = computed((): TraceVarSnapshot | null => {
  const name = traceVarName.value
  if (!name || !tracePrevStep.value?.vars) return null
  return (tracePrevStep.value.vars[name] as TraceVarSnapshot) ?? null
})

const traceIsSequence = computed(() => traceSnap.value && isSequenceSnapshot(traceSnap.value))
const traceIsAssociative = computed(() => traceSnap.value && isAssociativeSnapshot(traceSnap.value))

interface PptSlide {
  title: string
  subtitle?: string
  layout?: string
  bullets?: string[]
  visual_hint?: string
  speaker_note?: string
}

interface VideoScene {
  time_range: string
  visual: string
  voiceover: string
  animation_focus: string
}

interface ReadingLevel {
  level: string
  fit_for?: string
  items?: Array<{ title: string; type?: string; why?: string; task?: string }>
}

const pptPayload = computed(() => {
  const r = resourceMap.value.get('ppt')
  if (!r) return null
  try {
    return JSON.parse(r.content) as { deck_title?: string; design_style?: string; slides?: PptSlide[] }
  } catch {
    return null
  }
})

const videoPayload = computed(() => {
  const r = resourceMap.value.get('video_script')
  if (!r) return null
  try {
    return JSON.parse(r.content) as {
      title?: string
      duration_seconds?: number
      cognitive_style?: string
      tts_preview_text?: string
      scenes?: VideoScene[]
    }
  } catch {
    return null
  }
})

const readingPayload = computed(() => {
  const r = resourceMap.value.get('reading')
  if (!r) return null
  try {
    return JSON.parse(r.content) as { reading_goal?: string; levels?: ReadingLevel[] }
  } catch {
    return null
  }
})

const ttsLoading = ref(false)

async function playVideoTtsPreview() {
  const text = videoPayload.value?.tts_preview_text?.trim()
  if (!text) return
  ttsLoading.value = true
  try {
    const blob = await synthesizeTtsAudio({ text })
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.onended = () => URL.revokeObjectURL(url)
    audio.onerror = () => URL.revokeObjectURL(url)
    await audio.play()
  } finally {
    ttsLoading.value = false
  }
}
</script>

<template>
  <div class="resource-dashboard">
    <nav class="dash-tabs" role="tablist">
      <button
        v-for="t in tabs"
        :key="t.key"
        type="button"
        role="tab"
        class="dash-tab"
        :class="{ active: tab === t.key, ready: t.ready }"
        :aria-selected="tab === t.key"
        @click="tab = t.key"
      >
        <span class="tab-icon">{{ t.icon }}</span>
        <span class="tab-label">{{ t.label }}</span>
        <span class="tab-agent">{{ t.agent }}</span>
        <span v-if="t.ready" class="tab-dot" />
      </button>
    </nav>

    <div class="dash-panel">
      <!-- 自适应教案 -->
      <article v-show="tab === 'document'" class="panel-card panel-card--doc">
        <header class="panel-head">
          <h3>自适应教案</h3>
          <span v-if="current" class="panel-meta">{{ current.agent_name }}</span>
        </header>
        <DomainStructurePanels
          v-if="docPayload && docResource"
          :content="docResource.content"
          mode="document"
        />
        <el-alert
          v-else-if="docUnparsedJson"
          type="warning"
          :closable="false"
          show-icon
          title="双域 JSON 解析失败"
          description="内容似为 Domain/Structure 结构但格式不完整。请重新生成教案。"
        />
        <div v-else-if="docHtml" class="doc-body ai-md-body" v-html="docHtml" />
        <el-empty v-else description="ConceptAgent 生成后将呈现「业务故事 + 结构剖析」双域教案" />
      </article>

      <!-- 知识思维导图 -->
      <article v-show="tab === 'mindmap'" class="panel-card panel-card--graph">
        <header class="panel-head">
          <h3>知识思维导图</h3>
          <span class="panel-meta">GraphAgent · Mermaid</span>
        </header>
        <div ref="mermaidHost" class="mermaid-host" />
        <p v-if="mermaidError" class="mermaid-err">{{ mermaidError }}</p>
        <el-empty v-if="!mermaidSrc" description="等待 GraphAgent 输出 Mermaid 拓扑" />
      </article>

      <!-- 个性化自测题 -->
      <article v-show="tab === 'exercises'" class="panel-card panel-card--quiz">
        <header class="panel-head">
          <h3>个性化自测题</h3>
          <span class="panel-meta">QuizAgent · 3 题精练</span>
        </header>
        <div v-if="quizQuestions.length" class="quiz-grid">
          <div v-for="(q, i) in quizQuestions" :key="i" class="quiz-card">
            <div class="quiz-head">
              <span class="quiz-badge">{{ q.type === 'choice' ? '选择题' : '填空题' }}</span>
              <span class="quiz-diff">{{ q.difficulty ?? 'medium' }}</span>
            </div>
            <p class="quiz-stem">{{ i + 1 }}. {{ q.stem }}</p>
            <el-radio-group
              v-if="q.type === 'choice' && q.options?.length"
              v-model="quizAnswers[i]"
              class="quiz-options"
            >
              <el-radio v-for="(opt, j) in q.options" :key="j" :value="opt">{{ opt }}</el-radio>
            </el-radio-group>
            <el-input
              v-else-if="q.type === 'fill'"
              v-model="quizAnswers[i]"
              placeholder="输入你的答案"
              class="quiz-fill"
            />
            <el-button link type="primary" size="small" @click="revealHint(i)">查看提示</el-button>
            <p v-if="quizRevealed[i] && q.hint" class="quiz-hint">💡 {{ q.hint }}</p>
            <p v-if="q.focus" class="quiz-focus">考查：{{ q.focus }}</p>
          </div>
        </div>
        <el-empty v-else description="QuizAgent 将根据易错点生成 3 道练习题" />
      </article>

      <!-- 剧情实操沙盒 -->
      <article v-show="tab === 'code_case'" class="panel-card panel-card--scenario">
        <header class="panel-head">
          <h3>剧情实操沙盒</h3>
          <span class="panel-meta">ScenarioAgent</span>
        </header>
        <DomainStructurePanels
          v-if="scenarioPayload && scenarioResource"
          :content="scenarioResource.content"
          mode="scenario"
          editable-code
          @update:code="scenarioEditorCode = $event"
        />
        <el-alert
          v-else-if="scenarioUnparsedJson"
          type="warning"
          :closable="false"
          show-icon
          title="双域 JSON 解析失败"
          description="内容似为 Domain/Structure 结构但格式不完整。请重新生成沙盒剧本。"
        />
        <div v-else-if="scenarioBg || scenarioCode" class="scenario-layout">
          <aside class="scenario-story">
            <h4>剧本背景</h4>
            <p>{{ scenarioBg || '（等待剧本生成）' }}</p>
            <h4 v-if="scenarioGoal">任务目标</h4>
            <p v-if="scenarioGoal">{{ scenarioGoal }}</p>
          </aside>
          <section class="scenario-code">
            <h4>代码框架 · 补全 // TODO</h4>
            <CodeEditor v-model="scenarioEditorCode" language="python" :readonly="false" min-height="280px" />
          </section>
        </div>
        <el-empty v-else description="ScenarioAgent 将生成「叙事剧本 + 结构沙盒」双域内容" />
      </article>

      <!-- 执行轨迹回放 -->
      <article v-show="tab === 'trace_animation'" class="panel-card panel-card--trace">
        <header class="panel-head">
          <h3>执行轨迹回放</h3>
          <span class="panel-meta">TraceAgent · trace_viz</span>
        </header>
        <div v-if="traceSteps.length" class="trace-layout">
          <p v-if="tracePayload?.narration_hint" class="trace-hint">{{ tracePayload.narration_hint }}</p>
          <div class="trace-controls">
            <el-slider
              v-model="traceStepIndex"
              :min="0"
              :max="Math.max(0, traceSteps.length - 1)"
              :format-tooltip="(v: number) => `Step ${v + 1}`"
            />
            <span class="trace-verdict">{{ tracePayload?.verdict ?? 'OK' }}</span>
          </div>
          <div v-if="traceSnap && traceVarName" class="trace-viz-wrap">
            <TraceSequenceViz
              v-if="traceIsSequence"
              :name="traceVarName"
              :view-hint="sequenceViewHint(traceSnap)"
              :items="sequenceItems(traceSnap)"
              :prev-items="tracePrevSnap ? sequenceItems(tracePrevSnap) : []"
              :var-changed="true"
            />
            <TraceAssociativeViz
              v-else-if="traceIsAssociative"
              :name="traceVarName"
              :view-hint="associativeViewHint(traceSnap)"
              :entries="associativeEntries(traceSnap)"
              :prev-entries="tracePrevSnap ? associativeEntries(tracePrevSnap) : []"
              :var-changed="true"
            />
            <pre v-else class="trace-raw">{{ JSON.stringify(traceSnap, null, 2) }}</pre>
          </div>
          <details class="trace-code-fold">
            <summary>题解源码</summary>
            <pre>{{ tracePayload?.code }}</pre>
          </details>
        </div>
        <el-empty v-else description="TraceAgent 将录制标准题解并逐步回放" />
      </article>

      <!-- PPT 胶片预览 -->
      <article v-show="tab === 'ppt'" class="panel-card panel-card--ppt">
        <header class="panel-head">
          <h3>{{ pptPayload?.deck_title ?? 'PPT 胶片预览' }}</h3>
          <span class="panel-meta">PptAgent · {{ pptPayload?.design_style ?? 'JSON Preview' }}</span>
        </header>
        <el-carousel v-if="pptPayload?.slides?.length" height="280px" indicator-position="outside">
          <el-carousel-item v-for="(slide, i) in pptPayload.slides" :key="i">
            <section class="ppt-slide">
              <span class="ppt-page">Slide {{ i + 1 }} · {{ slide.layout ?? 'concept' }}</span>
              <h4>{{ slide.title }}</h4>
              <p v-if="slide.subtitle" class="ppt-subtitle">{{ slide.subtitle }}</p>
              <ul>
                <li v-for="(b, j) in slide.bullets ?? []" :key="j">{{ b }}</li>
              </ul>
              <div class="ppt-note">
                <span>{{ slide.visual_hint }}</span>
                <small>{{ slide.speaker_note }}</small>
              </div>
            </section>
          </el-carousel-item>
        </el-carousel>
        <el-empty v-else description="PptAgent 将输出可轮播展示的核心知识胶片" />
      </article>

      <!-- 教学短视频分镜脚本 -->
      <article v-show="tab === 'video_script'" class="panel-card panel-card--video">
        <header class="panel-head">
          <h3>{{ videoPayload?.title ?? '60 秒教学短视频脚本' }}</h3>
          <span class="panel-meta">VideoScriptAgent · iFlytek TTS Ready</span>
        </header>
        <div v-if="videoPayload?.scenes?.length" class="video-script">
          <div class="tts-preview">
            <div>
              <strong>科大讯飞 TTS 试听文案</strong>
              <p>{{ videoPayload.tts_preview_text }}</p>
            </div>
            <el-button
              type="primary"
              plain
              :loading="ttsLoading"
              :disabled="!videoPayload.tts_preview_text"
              @click="playVideoTtsPreview"
            >
              试听
            </el-button>
          </div>
          <div class="scene-grid">
            <div v-for="(scene, i) in videoPayload.scenes" :key="i" class="scene-card">
              <span class="scene-time">{{ scene.time_range }}</span>
              <h4>画面</h4>
              <p>{{ scene.visual }}</p>
              <h4>旁白</h4>
              <p>{{ scene.voiceover }}</p>
              <h4>动画重点</h4>
              <p>{{ scene.animation_focus }}</p>
            </div>
          </div>
        </div>
        <el-empty v-else description="VideoScriptAgent 将根据认知风格生成 60 秒分镜脚本" />
      </article>

      <!-- 分层拓展阅读 -->
      <article v-show="tab === 'reading'" class="panel-card panel-card--reading">
        <header class="panel-head">
          <h3>分层拓展阅读</h3>
          <span class="panel-meta">ReadingAgent · 基础 / 进阶 / 挑战</span>
        </header>
        <p v-if="readingPayload?.reading_goal" class="reading-goal">{{ readingPayload.reading_goal }}</p>
        <div v-if="readingPayload?.levels?.length" class="reading-levels">
          <section v-for="level in readingPayload.levels" :key="level.level" class="reading-level">
            <h4>{{ level.level }}</h4>
            <p class="reading-fit">{{ level.fit_for }}</p>
            <div v-for="(item, i) in level.items ?? []" :key="i" class="reading-item">
              <strong>{{ item.title }}</strong>
              <span>{{ item.type }}</span>
              <p>{{ item.why }}</p>
              <small>读后任务：{{ item.task }}</small>
            </div>
          </section>
        </div>
        <el-empty v-else description="ReadingAgent 将生成三层拓展阅读清单" />
      </article>
    </div>
    <SafetyValidationPanel
      v-if="current"
      :meta="current.meta"
      :resource-type="current.resource_type"
    />
  </div>
</template>

<style scoped>
.resource-dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dash-tabs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
  gap: 10px;
}

@media (max-width: 960px) {
  .dash-tabs {
    grid-template-columns: repeat(2, 1fr);
  }
}

.dash-tab {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 14px 12px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--alp-color-border) 80%, transparent);
  background: color-mix(in srgb, var(--alp-bg-surface) 90%, transparent);
  cursor: pointer;
  transition:
    transform 0.25s ease,
    border-color 0.25s,
    box-shadow 0.25s;
  text-align: left;
}

.dash-tab:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--alp-color-primary) 40%, transparent);
}

.dash-tab.active {
  border-color: var(--alp-color-primary);
  box-shadow: 0 0 24px color-mix(in srgb, var(--alp-color-primary) 18%, transparent);
  background: linear-gradient(
    145deg,
    color-mix(in srgb, var(--alp-color-primary) 8%, var(--alp-bg-surface)),
    var(--alp-bg-surface)
  );
}

.dash-tab.ready .tab-dot {
  background: #4ade80;
  box-shadow: 0 0 8px #4ade80;
}

.tab-icon {
  font-size: 1.25rem;
}

.tab-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.tab-agent {
  font-size: 10px;
  color: var(--alp-color-muted);
  font-family: ui-monospace, monospace;
}

.tab-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--alp-color-muted);
}

.dash-panel {
  min-height: 360px;
}

.panel-card {
  padding: 20px 22px;
  border-radius: 16px;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 20%, var(--alp-color-border));
  background: var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
  animation: panel-in 0.4s ease-out;
}

@keyframes panel-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
}

.panel-meta {
  font-size: 11px;
  color: var(--alp-color-primary);
  font-family: ui-monospace, monospace;
}

.doc-body {
  line-height: 1.7;
  font-size: 14px;
}

.mermaid-host {
  min-height: 240px;
  display: flex;
  justify-content: center;
  padding: 16px;
  border-radius: 12px;
  background: #0f172a;
  overflow: auto;
}

.mermaid-host :deep(svg) {
  max-width: 100%;
  height: auto;
}

.mermaid-err {
  color: #f87171;
  font-size: 12px;
  margin-top: 8px;
}

.quiz-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.quiz-card {
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: color-mix(in srgb, var(--alp-bg-soft-block) 60%, transparent);
}

.quiz-head {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.quiz-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-primary) 15%, transparent);
  color: var(--alp-color-primary);
}

.quiz-diff {
  font-size: 10px;
  color: var(--alp-color-muted);
}

.quiz-stem {
  margin: 0 0 12px;
  font-weight: 600;
  line-height: 1.5;
}

.quiz-options {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 8px;
}

.quiz-fill {
  margin-bottom: 8px;
  max-width: 360px;
}

.quiz-hint {
  font-size: 13px;
  color: var(--alp-color-muted);
  margin: 8px 0 0;
}

.quiz-focus {
  font-size: 11px;
  color: var(--alp-color-primary);
  margin: 6px 0 0;
}

.scenario-layout {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 18px;
}

@media (max-width: 768px) {
  .scenario-layout {
    grid-template-columns: 1fr;
  }
}

.scenario-story h4,
.scenario-code h4 {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--alp-color-primary);
}

.scenario-story p {
  margin: 0 0 14px;
  font-size: 14px;
  line-height: 1.65;
  color: var(--alp-color-muted);
}

.trace-hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--alp-color-muted);
}

.trace-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.trace-controls .el-slider {
  flex: 1;
}

.trace-verdict {
  font-size: 11px;
  font-family: ui-monospace, monospace;
  color: #4ade80;
}

.trace-viz-wrap {
  min-height: 200px;
  padding: 12px 0;
}

.trace-raw {
  font-size: 11px;
  overflow: auto;
  max-height: 200px;
}

.trace-code-fold {
  margin-top: 16px;
  font-size: 12px;
}

.trace-code-fold pre {
  margin-top: 8px;
  padding: 12px;
  border-radius: 8px;
  background: var(--alp-bg-code-ish);
  overflow: auto;
  max-height: 180px;
}

.ppt-slide {
  height: 100%;
  padding: 22px 26px;
  border-radius: 12px;
  background:
    linear-gradient(135deg, color-mix(in srgb, #06b6d4 18%, transparent), transparent 48%),
    color-mix(in srgb, var(--alp-bg-soft-block) 78%, transparent);
  border: 1px solid color-mix(in srgb, #06b6d4 32%, var(--alp-color-border));
}

.ppt-page,
.scene-time {
  font-size: 11px;
  color: var(--alp-color-primary);
  font-family: ui-monospace, monospace;
}

.ppt-slide h4 {
  margin: 12px 0 6px;
  font-size: 24px;
}

.ppt-subtitle,
.reading-goal {
  margin: 0 0 12px;
  color: var(--alp-color-muted);
}

.ppt-slide ul {
  margin: 14px 0;
  padding-left: 18px;
  line-height: 1.8;
}

.ppt-note {
  display: grid;
  gap: 4px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--alp-color-border);
  font-size: 12px;
  color: var(--alp-color-muted);
}

.tts-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px;
  margin-bottom: 14px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, #ec4899 32%, var(--alp-color-border));
  background: color-mix(in srgb, #ec4899 8%, var(--alp-bg-soft-block));
}

.tts-preview p {
  margin: 6px 0 0;
  color: var(--alp-color-muted);
  line-height: 1.6;
}

.scene-grid,
.reading-levels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.scene-card,
.reading-level {
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.scene-card h4,
.reading-level h4 {
  margin: 10px 0 4px;
  color: var(--alp-color-primary);
  font-size: 13px;
}

.scene-card p,
.reading-fit,
.reading-item p {
  margin: 0 0 8px;
  color: var(--alp-color-muted);
  line-height: 1.55;
  font-size: 13px;
}

.reading-item {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--alp-color-border);
}

.reading-item strong {
  display: block;
  margin-bottom: 4px;
}

.reading-item span,
.reading-item small {
  color: var(--alp-color-muted);
  font-size: 11px;
}
</style>
