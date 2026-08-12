<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { GeneratedResource } from '@/api/orchestrator'
import { synthesizeTTS } from '@/api/tts'
import DomainStructurePanels from '@/components/resources/DomainStructurePanels.vue'
import SafetyValidationPanel from '@/components/resources/SafetyValidationPanel.vue'
import TrustEvidenceDrawer from '@/components/resources/TrustEvidenceDrawer.vue'
import {
  looksLikeUnparsedDomainJson,
  parseDomainStructureContent,
} from '@/utils/domainStructureContent'
import { normalizeMindmapSource } from '@/utils/mermaidMindmap'
import { renderAiReplyHtml } from '@/utils/renderAiReply'
import { CORE_RESOURCE_TAB_META } from '@/utils/agentConsole'
import { parseStructuredJson } from '@/utils/structuredJson'
import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'
import {
  associativeEntries,
  associativeViewHint,
  isAssociativeSnapshot,
  isSequenceSnapshot,
  sequenceItems,
  sequenceViewHint,
} from '@/utils/traceProtocol'

const CodeEditor = defineAsyncComponent(() => import('@/components/oj/CodeEditor.vue'))
const TraceSequenceViz = defineAsyncComponent(
  () => import('@/components/oj/trace/TraceSequenceViz.vue'),
)
const TraceAssociativeViz = defineAsyncComponent(
  () => import('@/components/oj/trace/TraceAssociativeViz.vue'),
)

type MermaidApi = typeof import('mermaid').default
let mermaidApi: MermaidApi | null = null
let mermaidRenderSeq = 0

const props = defineProps<{
  resources: GeneratedResource[]
  activeTab?: string
  streamingContent?: Record<string, string>
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
const activeStreamingContent = computed(() => props.streamingContent?.[tab.value] ?? '')

// --- 学案 / 沙盒：Domain · Structure 双域 ---
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
  return normalizeMindmapSource(r.content)
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
  if (tab.value !== 'mindmap' || !mermaidSrc.value) return
  await nextTick()
  const currentHost = mermaidHost.value
  if (!currentHost) return
  try {
    const mermaid = await loadMermaid()
    if (renderSeq !== mermaidRenderSeq || tab.value !== 'mindmap') return
    const parsed = await mermaid.parse(mermaidSrc.value, { suppressErrors: true })
    if (parsed === false) throw new Error('Mermaid 语法校验失败')
    const { svg } = await mermaid.render(`mmd-${Date.now()}-${renderSeq}`, mermaidSrc.value)
    if (renderSeq !== mermaidRenderSeq || tab.value !== 'mindmap') return
    if (svg.includes('Syntax error in text')) throw new Error('Mermaid 语法校验失败')
    currentHost.innerHTML = svg
  } catch (e) {
    if (renderSeq !== mermaidRenderSeq) return
    mermaidError.value = e instanceof Error ? e.message : 'Mermaid 渲染失败'
    currentHost.innerHTML = '<div class="mermaid-placeholder">思维导图暂不可渲染</div>'
  }
}

watch([tab, mermaidSrc], () => void renderMermaid(), { flush: 'post' })
onMounted(() => void renderMermaid())

function robustJsonParse(text: string): unknown | null {
  return parseStructuredJson(text)
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
  message?: string
  result_preview?: string | null
  stdin?: string
  stdout?: string
}

const tracePayload = computed((): TracePayload | null => {
  const r = resourceMap.value.get('trace_animation')
  if (!r) return null
  const data = robustJsonParse(r.content) as TracePayload | null
  return data
})

const traceStepIndex = ref(0)
const tracePlaying = ref(false)
let tracePlaybackTimer: ReturnType<typeof setInterval> | null = null

const traceSteps = computed(() => tracePayload.value?.steps ?? [])

watch(traceSteps, () => {
  stopTracePlayback()
  traceStepIndex.value = 0
})

const currentTraceStep = computed(() => traceSteps.value[traceStepIndex.value] ?? null)

const tracePrevStep = computed(() =>
  traceStepIndex.value > 0 ? traceSteps.value[traceStepIndex.value - 1] : null,
)

const traceCodeLines = computed(() => (tracePayload.value?.code ?? '').split('\n'))
const traceCurrentLine = computed(() => currentTraceStep.value?.line ?? 0)

function stopTracePlayback() {
  tracePlaying.value = false
  if (tracePlaybackTimer) clearInterval(tracePlaybackTimer)
  tracePlaybackTimer = null
}

function tracePrevious() {
  stopTracePlayback()
  traceStepIndex.value = Math.max(0, traceStepIndex.value - 1)
}

function traceNext() {
  stopTracePlayback()
  traceStepIndex.value = Math.min(traceSteps.value.length - 1, traceStepIndex.value + 1)
}

function toggleTracePlayback() {
  if (tracePlaying.value) {
    stopTracePlayback()
    return
  }
  if (traceStepIndex.value >= traceSteps.value.length - 1) traceStepIndex.value = 0
  tracePlaying.value = true
  tracePlaybackTimer = setInterval(() => {
    if (traceStepIndex.value >= traceSteps.value.length - 1) {
      stopTracePlayback()
      return
    }
    traceStepIndex.value++
  }, 900)
}

onBeforeUnmount(stopTracePlayback)

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

function formatTraceValue(snapshot: TraceVarSnapshot | undefined): string {
  if (!snapshot) return '未定义'
  const value = snapshot.value
  if (value === null) return 'None'
  if (typeof value === 'string') return value || '空字符串'
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

const traceVariables = computed(() => {
  const currentVars = currentTraceStep.value?.vars ?? {}
  const previousVars = tracePrevStep.value?.vars ?? {}
  const changed = new Set(currentTraceStep.value?.changed ?? [])
  return Object.entries(currentVars).map(([name, snapshot]) => ({
    name,
    type: snapshot.type || typeof snapshot.value,
    current: formatTraceValue(snapshot),
    previous: formatTraceValue(previousVars[name]),
    changed: changed.has(name),
  }))
})

interface ReadingLevel {
  level: string
  fit_for?: string
  items?: Array<{ title: string; type?: string; why?: string; task?: string }>
}

const readingPayload = computed(() => {
  const r = resourceMap.value.get('reading')
  if (!r) return null
  return robustJsonParse(r.content) as { reading_goal?: string; levels?: ReadingLevel[] } | null
})

// --- Exercises（个性化题单）---
interface ExerciseQuestion {
  type?: string
  stem?: string
  options?: string[]
  answer?: string
  hint?: string
  explanation?: string
  focus?: string
  difficulty?: string
}

const exercisesPayload = computed(() => {
  const r = resourceMap.value.get('exercises')
  if (!r) return null
  const data = robustJsonParse(r.content) as { questions?: ExerciseQuestion[] } | null
  return data?.questions ?? null
})

const exerciseInputs = ref<Record<number, string>>({})
const exerciseRevealed = ref<Record<number, boolean>>({})

watch(exercisesPayload, () => {
  exerciseInputs.value = {}
  exerciseRevealed.value = {}
}, { immediate: true })

function isExerciseCorrect(idx: number, q: ExerciseQuestion): boolean | null {
  if (!exerciseRevealed.value[idx]) return null
  if (q.type === 'choice') {
    return !!exerciseInputs.value[idx] && exerciseInputs.value[idx] === q.answer
  }
  return null
}

function revealExercise(idx: number) {
  exerciseRevealed.value[idx] = true
}

function resetExercises() {
  exerciseInputs.value = {}
  exerciseRevealed.value = {}
}

// --- VideoScript（教学短视频脚本）---
interface VideoShot {
  index?: number
  scene?: string
  visual_hint?: string
  subtitle?: string
  voiceover?: string
  duration_sec?: number
}

interface VideoScriptPayload {
  title?: string
  duration_sec?: number
  goal?: string
  shots?: VideoShot[]
  summary?: string
}

const videoScriptPayload = computed<VideoScriptPayload | null>(() => {
  const r = resourceMap.value.get('video_script')
  if (!r) return null
  return robustJsonParse(r.content) as VideoScriptPayload | null
})

const videoShots = computed<VideoShot[]>(() => videoScriptPayload.value?.shots ?? [])
const videoTotalDuration = computed(() =>
  videoShots.value.reduce((acc, s) => acc + (Number(s.duration_sec) || 0), 0),
)

// 当前播放分镜索引（-1 表示未开始；shots.length 表示已播完）
const videoCurrentShot = ref(-1)
const videoPlaying = ref(false)
const videoTtsLoading = ref(false)
// 每镜的 TTS URL 缓存（按 shot.index）
const videoTtsUrls = ref<Record<number, string>>({})
let videoAudioEl: HTMLAudioElement | null = null
let videoPlayTimer: ReturnType<typeof setTimeout> | null = null

function ensureVideoAudio(): HTMLAudioElement | null {
  if (!videoAudioEl) {
    videoAudioEl = new Audio()
    videoAudioEl.preload = 'auto'
  }
  return videoAudioEl
}

function stopVideoPlayback() {
  videoPlaying.value = false
  if (videoPlayTimer) {
    clearTimeout(videoPlayTimer)
    videoPlayTimer = null
  }
  if (videoAudioEl) {
    videoAudioEl.pause()
    videoAudioEl.currentTime = 0
  }
}

async function ensureShotTtsUrl(shot: VideoShot): Promise<string | null> {
  const idx = shot.index ?? -1
  if (idx < 0) return null
  if (videoTtsUrls.value[idx]) return videoTtsUrls.value[idx]
  const text = (shot.voiceover || '').trim()
  if (!text) return null
  const blob = await synthesizeTTS({ text })
  const url = URL.createObjectURL(blob)
  videoTtsUrls.value[idx] = url
  return url
}

async function playVideoFromShot(startIdx: number) {
  const shots = videoShots.value
  if (!shots.length) return
  if (startIdx < 0 || startIdx >= shots.length) return
  stopVideoPlayback()
  videoCurrentShot.value = startIdx
  videoPlaying.value = true
  await playShot(shots[startIdx])
}

async function playShot(shot: VideoShot) {
  const duration = Math.max(3, Number(shot.duration_sec) || 8)
  const audio = ensureVideoAudio()
  if (!audio) {
    // 浏览器不支持 Audio：仅按 duration 计时推进
    videoPlayTimer = setTimeout(() => {
      advanceToNextShot()
    }, duration * 1000)
    return
  }

  // 尝试播放配音：若 TTS 可用，则用音频时长作为分镜时长；否则用 duration_sec
  let audioOk = false
  try {
    videoTtsLoading.value = true
    const url = await ensureShotTtsUrl(shot)
    if (url) {
      audio.src = url
      await audio.play()
      audioOk = true
    }
  } catch {
    // TTS 失败：静默降级为无声分镜，不阻断播放
    audioOk = false
  } finally {
    videoTtsLoading.value = false
  }

  const waitMs = audioOk ? Math.max(duration * 1000, (audio.duration || 0) * 1000) : duration * 1000
  videoPlayTimer = setTimeout(() => {
    advanceToNextShot()
  }, waitMs)
}

function advanceToNextShot() {
  const next = videoCurrentShot.value + 1
  const shots = videoShots.value
  if (next >= shots.length) {
    // 播放结束
    videoPlaying.value = false
    videoCurrentShot.value = shots.length // 标记为已播完
    if (videoAudioEl) {
      videoAudioEl.pause()
      videoAudioEl.currentTime = 0
    }
    return
  }
  videoCurrentShot.value = next
  void playShot(shots[next])
}

function toggleVideoPlayback() {
  if (videoPlaying.value) {
    stopVideoPlayback()
    return
  }
  const shots = videoShots.value
  if (!shots.length) return
  // 已播完或未开始：从头开始
  const start = videoCurrentShot.value < 0 || videoCurrentShot.value >= shots.length ? 0 : videoCurrentShot.value
  void playVideoFromShot(start)
}

function jumpToShot(idx: number) {
  if (idx < 0 || idx >= videoShots.value.length) return
  void playVideoFromShot(idx)
}

async function readSingleShot(shot: VideoShot) {
  const text = (shot.voiceover || '').trim()
  if (!text) {
    return
  }
  try {
    videoTtsLoading.value = true
    stopVideoPlayback()
    const audio = ensureVideoAudio()
    if (!audio) {
      ElMessage.warning('当前浏览器不支持音频播放')
      return
    }
    // 优先用缓存 URL
    let url = videoTtsUrls.value[shot.index ?? -1]
    if (!url) {
      const blob = await synthesizeTTS({ text })
      url = URL.createObjectURL(blob)
      if (shot.index !== undefined) videoTtsUrls.value[shot.index] = url
    }
    audio.src = url
    videoCurrentShot.value = shot.index ?? -1
    await audio.play()
  } catch (e) {
    const err = e as { response?: { status?: number } }
    if (err?.response?.status === 503) {
      ElMessage.warning('语音合成未配置：请联系管理员启用讯飞 TTS')
    } else {
      ElMessage.error('语音合成失败，请稍后重试')
    }
  } finally {
    videoTtsLoading.value = false
  }
}

watch(videoScriptPayload, () => {
  stopVideoPlayback()
  videoCurrentShot.value = -1
  // 撤销旧 URL
  for (const k of Object.keys(videoTtsUrls.value)) {
    URL.revokeObjectURL(videoTtsUrls.value[Number(k)])
  }
  videoTtsUrls.value = {}
}, { immediate: true })

onBeforeUnmount(() => {
  stopVideoPlayback()
  for (const k of Object.keys(videoTtsUrls.value)) {
    URL.revokeObjectURL(videoTtsUrls.value[Number(k)])
  }
  videoTtsUrls.value = {}
  if (videoAudioEl) {
    videoAudioEl.pause()
    videoAudioEl = null
  }
})

const evidenceVisible = ref(false)
const evidenceResource = ref<GeneratedResource | null>(null)

function openEvidence() {
  if (current.value) {
    evidenceResource.value = current.value
    evidenceVisible.value = true
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
      <article v-if="activeStreamingContent && !current" class="panel-card stream-preview-card" aria-live="polite">
        <header class="panel-head">
          <h3>正在实时生成{{ tabs.find((item) => item.key === tab)?.label ?? '学习资源' }}</h3>
          <span class="panel-meta"><span class="stream-progress-dot" /> 内容持续更新中</span>
        </header>
        <div v-if="!activeStreamingContent.trim()" class="stream-progress-copy">
          <p>正在整理结构、核对课程知识并生成可视化内容，完成后将在这里自动呈现。</p>
        </div>
        <div v-else class="doc-body ai-md-body stream-delta" v-html="renderAiReplyHtml(activeStreamingContent)" />
      </article>

      <template v-else>
      <!-- 自适应学案 -->
      <article v-if="tab === 'document'" class="panel-card panel-card--doc">
        <header class="panel-head">
          <h3>自适应学案</h3>
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
          description="内容似为 Domain/Structure 结构但格式不完整。请重新生成学案。"
        />
        <div v-else-if="docHtml" class="doc-body ai-md-body" v-html="docHtml" />
        <el-empty v-else description="ConceptAgent 生成后将呈现「业务故事 + 结构剖析」双域学案" />
      </article>

      <!-- 知识思维导图 -->
      <article v-if="tab === 'mindmap'" class="panel-card panel-card--graph">
        <header class="panel-head">
          <h3>知识思维导图</h3>
          <span class="panel-meta">GraphAgent · 思维导图</span>
        </header>
        <div ref="mermaidHost" class="mermaid-host" />
        <p v-if="mermaidError" class="mermaid-err">{{ mermaidError }}</p>
        <el-empty v-if="!mermaidSrc" description="等待 GraphAgent 输出思维导图" />
      </article>

      <!-- 个性化题单 -->
      <article v-if="tab === 'exercises'" class="panel-card panel-card--exercises">
        <header class="panel-head">
          <h3>个性化题单</h3>
          <span class="panel-meta">ExerciseAgent · 选择 / 填空</span>
        </header>
        <template v-if="exercisesPayload && exercisesPayload.length">
          <div class="quiz-toolbar">
            <span class="quiz-progress">
              共 {{ exercisesPayload.length }} 题 ·
              已作答 {{ Object.keys(exerciseInputs).length }} / {{ exercisesPayload.length }}
            </span>
            <div class="quiz-toolbar-actions">
              <el-button size="small" @click="resetExercises">重置作答</el-button>
            </div>
          </div>
          <div class="quiz-grid">
            <article
              v-for="(q, idx) in exercisesPayload"
              :key="idx"
              class="quiz-card"
            >
              <header class="quiz-head">
                <span class="quiz-badge">{{ q.type === 'choice' ? '选择' : '填空' }} · 第 {{ idx + 1 }} 题</span>
                <span v-if="q.difficulty" class="quiz-diff">难度：{{ q.difficulty }}</span>
                <span v-if="q.focus" class="quiz-focus-tag">焦点：{{ q.focus }}</span>
              </header>
              <p class="quiz-stem">{{ q.stem }}</p>

              <div v-if="q.type === 'choice'" class="quiz-options">
                <el-button
                  v-for="opt in q.options || []"
                  :key="opt"
                  size="small"
                  :type="exerciseInputs[idx] === opt ? 'primary' : 'default'"
                  :plain="exerciseInputs[idx] !== opt"
                  @click="exerciseInputs[idx] = opt"
                >
                  {{ opt }}
                </el-button>
              </div>
              <div v-else class="quiz-fill">
                <el-input
                  v-model="exerciseInputs[idx]"
                  size="small"
                  placeholder="请输入答案后点击「查看解析」"
                  clearable
                />
              </div>

              <p v-if="q.hint" class="quiz-hint">提示：{{ q.hint }}</p>

              <div class="quiz-toolbar-actions">
                <el-button
                  size="small"
                  type="primary"
                  plain
                  :disabled="exerciseRevealed[idx]"
                  @click="revealExercise(idx)"
                >
                  查看解析
                </el-button>
              </div>

              <div v-if="exerciseRevealed[idx]" class="quiz-answer">
                <p>
                  <strong>参考答案：</strong>{{ q.answer }}
                </p>
                <p v-if="q.type === 'choice' && isExerciseCorrect(idx, q) === true" class="quiz-correct">
                  ✓ 回答正确
                </p>
                <p v-else-if="q.type === 'choice' && isExerciseCorrect(idx, q) === false" class="quiz-wrong">
                  ✗ 回答错误，请结合解析再思考一次
                </p>
                <p v-if="q.explanation"><strong>解析：</strong>{{ q.explanation }}</p>
              </div>
            </article>
          </div>
        </template>
        <el-empty v-else description="ExerciseAgent 将基于易错点生成 3 选择 + 2 填空个性化题单" />
      </article>

      <!-- 剧情实操沙盒 -->
      <article v-if="tab === 'code_case'" class="panel-card panel-card--scenario">
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
      <article v-if="tab === 'trace_animation'" class="panel-card panel-card--trace">
        <header class="panel-head">
          <h3>执行轨迹回放</h3>
          <span class="panel-meta">TraceAgent · trace_viz</span>
        </header>
        <div v-if="traceSteps.length" class="trace-layout">
          <div class="trace-overview">
            <div>
              <strong>{{ tracePayload?.title || '算法执行过程' }}</strong>
              <p v-if="tracePayload?.narration_hint" class="trace-hint">{{ tracePayload.narration_hint }}</p>
            </div>
            <div class="trace-facts">
              <span>Step {{ traceStepIndex + 1 }} / {{ traceSteps.length }}</span>
              <span>源码第 {{ traceCurrentLine }} 行</span>
              <span class="trace-verdict">{{ tracePayload?.verdict ?? 'OK' }}</span>
            </div>
          </div>
          <div class="trace-controls">
            <el-button size="small" :disabled="traceStepIndex === 0" @click="tracePrevious">上一步</el-button>
            <el-button size="small" type="primary" plain @click="toggleTracePlayback">
              {{ tracePlaying ? '暂停' : '自动播放' }}
            </el-button>
            <el-button size="small" :disabled="traceStepIndex >= traceSteps.length - 1" @click="traceNext">下一步</el-button>
            <el-slider
              v-model="traceStepIndex"
              :min="0"
              :max="Math.max(0, traceSteps.length - 1)"
              :format-tooltip="(v: number) => `Step ${v + 1}`"
              @input="stopTracePlayback"
            />
          </div>
          <div class="trace-workspace">
            <section class="trace-source-panel" aria-label="题解源码执行位置">
              <header>题解源码</header>
              <ol class="trace-source-lines">
                <li
                  v-for="(line, index) in traceCodeLines"
                  :key="index"
                  :class="{ active: index + 1 === traceCurrentLine }"
                >
                  <code>{{ line || ' ' }}</code>
                </li>
              </ol>
            </section>
            <section class="trace-state-panel" aria-label="当前变量状态">
              <header>
                <span>变量状态</span>
                <small>{{ currentTraceStep?.changed?.length ? `本步变化：${currentTraceStep.changed.join('、')}` : '本步无变量变化' }}</small>
              </header>
              <div v-if="traceVariables.length" class="trace-variable-grid">
                <article
                  v-for="variable in traceVariables"
                  :key="variable.name"
                  class="trace-variable-card"
                  :class="{ changed: variable.changed }"
                >
                  <div class="trace-variable-head">
                    <strong>{{ variable.name }}</strong>
                    <span>{{ variable.type }}</span>
                  </div>
                  <div class="trace-variable-change">
                    <code v-if="traceStepIndex > 0">{{ variable.previous }}</code>
                    <span v-if="traceStepIndex > 0">→</span>
                    <code>{{ variable.current }}</code>
                  </div>
                </article>
              </div>
              <el-empty v-else :image-size="54" description="当前步骤没有可展示变量" />
            </section>
          </div>
          <div v-if="traceSnap && traceVarName && (traceIsSequence || traceIsAssociative)" class="trace-viz-wrap">
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
          </div>
          <div v-if="tracePayload?.stdin || tracePayload?.result_preview || tracePayload?.stdout" class="trace-io">
            <div><span>输入</span><pre>{{ tracePayload?.stdin || '—' }}</pre></div>
            <div><span>实际输出</span><pre>{{ tracePayload?.result_preview || '—' }}</pre></div>
            <div><span>期望输出</span><pre>{{ tracePayload?.stdout || '—' }}</pre></div>
          </div>
        </div>
        <el-empty v-else description="TraceAgent 将录制标准题解并逐步回放" />
      </article>

      <!-- 分层拓展阅读 -->
      <article v-if="tab === 'reading'" class="panel-card panel-card--reading">
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

      <!-- 教学短视频脚本 -->
      <article v-if="tab === 'video_script'" class="panel-card panel-card--video">
        <header class="panel-head">
          <h3>教学短视频脚本</h3>
          <span class="panel-meta">VideoScriptAgent · 分镜 + 字幕 + 配音文案</span>
        </header>

        <div v-if="videoScriptPayload" class="video-info">
          <div class="video-info-row">
            <strong>{{ videoScriptPayload.title || '教学短视频' }}</strong>
            <span class="video-info-meta">
              时长 {{ videoScriptPayload.duration_sec ?? videoTotalDuration }}s ·
              {{ videoShots.length }} 镜
            </span>
          </div>
          <p v-if="videoScriptPayload.goal" class="video-goal">
            <span class="video-goal-tag">学习目标</span>{{ videoScriptPayload.goal }}
          </p>
        </div>

        <div v-if="videoScriptPayload" class="video-controls">
          <el-button
            :type="videoPlaying ? 'warning' : 'primary'"
            :loading="videoTtsLoading"
            size="small"
            @click="toggleVideoPlayback"
          >
            {{ videoPlaying ? '⏸ 暂停' : '▶ 播放伪视频' }}
          </el-button>
          <el-button
            v-if="videoCurrentShot >= 0 && videoCurrentShot < videoShots.length"
            size="small"
            @click="jumpToShot(videoCurrentShot)"
          >
            重播本镜
          </el-button>
          <el-button
            size="small"
            :disabled="videoCurrentShot < 0 || videoCurrentShot >= videoShots.length"
            @click="stopVideoPlayback"
          >
            ⏹ 停止
          </el-button>
          <span v-if="videoPlaying" class="video-now-playing">
            正在播放：第 {{ videoCurrentShot + 1 }} 镜 / 共 {{ videoShots.length }} 镜
          </span>
          <span v-else-if="videoCurrentShot >= videoShots.length" class="video-finished">
            ✓ 播放完毕
          </span>
          <span v-else-if="videoCurrentShot >= 0" class="video-paused">
            已暂停于第 {{ videoCurrentShot + 1 }} 镜
          </span>
        </div>

        <div v-if="videoShots.length" class="video-shots">
          <article
            v-for="(shot, idx) in videoShots"
            :key="shot.index ?? idx"
            class="video-shot"
            :class="{
              'video-shot--active': videoCurrentShot === (shot.index ?? idx),
              'video-shot--done': videoCurrentShot > (shot.index ?? idx) && videoCurrentShot < videoShots.length,
            }"
            @click="jumpToShot(shot.index ?? idx)"
          >
            <header class="video-shot-head">
              <span class="video-shot-index">第 {{ shot.index ?? idx + 1 }} 镜</span>
              <span class="video-shot-duration">{{ shot.duration_sec ?? 8 }}s</span>
            </header>
            <p v-if="shot.scene" class="video-shot-scene">{{ shot.scene }}</p>
            <p v-if="shot.visual_hint" class="video-shot-hint">画面提示：{{ shot.visual_hint }}</p>
            <p v-if="shot.subtitle" class="video-shot-subtitle">「{{ shot.subtitle }}」</p>
            <p v-if="shot.voiceover" class="video-shot-voiceover">
              <span class="video-vo-tag">配音</span>{{ shot.voiceover }}
            </p>
            <div class="video-shot-actions">
              <el-button
                size="small"
                plain
                :loading="videoTtsLoading && videoCurrentShot === (shot.index ?? idx)"
                @click.stop="readSingleShot(shot)"
              >
                🔊 朗读本镜
              </el-button>
            </div>
          </article>
        </div>

        <p v-if="videoScriptPayload?.summary" class="video-summary">
          <span class="video-summary-tag">结尾总结</span>{{ videoScriptPayload.summary }}
        </p>

        <el-empty v-else description="VideoScriptAgent 将生成 60～90 秒教学短视频脚本（含分镜 + 字幕 + 配音文案）" />
      </article>
      </template>
    </div>
    <SafetyValidationPanel
      v-if="current"
      :meta="current.meta"
      :resource-type="current.resource_type"
    />
    <div v-if="current" class="evidence-trigger">
      <el-button type="primary" plain size="small" @click="openEvidence">
        🔗 可信证据链
      </el-button>
    </div>
    <TrustEvidenceDrawer
      v-model:visible="evidenceVisible"
      :resource="evidenceResource"
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
  background: color-mix(in srgb, var(--alp-color-primary) 8%, var(--alp-bg-surface));
}

.dash-tab.ready .tab-dot {
  background: var(--alp-color-success);
  box-shadow: 0 0 8px var(--alp-color-primary-glow);
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

.stream-preview-card {
  min-height: 360px;
}

.stream-delta {
  padding: 12px 16px;
  font-size: 13.5px;
  line-height: 1.75;
  color: var(--alp-color-text);
  border-left: 3px solid color-mix(in srgb, var(--alp-color-primary) 45%, transparent);
  background: color-mix(in srgb, var(--alp-color-primary) 4%, transparent);
  border-radius: 4px;
  max-height: 60vh;
  overflow-y: auto;
}

.stream-delta :deep(.ai-md-p) {
  margin: 0 0 0.5em;
}

.stream-delta :deep(.ai-md-p:last-child) {
  margin-bottom: 0;
}

.stream-delta :deep(.ai-md-h) {
  margin: 0.6em 0 0.35em;
  font-size: 0.95em;
  font-weight: 600;
  color: var(--alp-color-text);
}

.stream-delta :deep(.ai-md-code) {
  padding: 0.1em 0.35em;
  font-size: 0.88em;
  font-family: ui-monospace, Consolas, monospace;
  background: color-mix(in srgb, var(--alp-color-primary) 12%, transparent);
  border-radius: 4px;
}

.stream-delta :deep(.ai-md-pre) {
  margin: 0.5em 0;
  padding: 0.5em 0.65em;
  background: var(--alp-bg-soft-block, rgba(0, 0, 0, 0.04));
  border: 1px solid var(--alp-color-border);
  border-radius: 6px;
  font-size: 12.5px;
  white-space: pre-wrap;
  word-break: break-word;
}

.stream-delta :deep(.ai-md-ul),
.stream-delta :deep(.ai-md-ol) {
  margin: 0.35em 0 0.5em;
  padding-left: 1.2em;
}

.stream-delta :deep(.ai-md-table) {
  width: 100%;
  margin: 0.5em 0;
  border-collapse: collapse;
  font-size: 0.9em;
}

.stream-delta :deep(.ai-md-table th),
.stream-delta :deep(.ai-md-table td) {
  padding: 0.3em 0.55em;
  border: 1px solid var(--alp-color-border);
  text-align: left;
}

.stream-delta :deep(.ai-md-table th) {
  background: var(--alp-bg-nav, rgba(0, 0, 0, 0.04));
  font-weight: 600;
}

.stream-progress-copy {
  min-height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--alp-color-muted);
  text-align: center;
}

.stream-progress-copy p {
  max-width: 520px;
  margin: 0;
  line-height: 1.7;
}

.stream-progress-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--alp-color-primary);
  box-shadow: 0 0 0 0 color-mix(in srgb, var(--alp-color-primary) 35%, transparent);
  animation: stream-pulse 1.4s infinite;
}

@keyframes stream-pulse {
  70% { box-shadow: 0 0 0 10px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}

.mermaid-host {
  min-height: 320px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  border-radius: 12px;
  background: var(--alp-bg-surface-solid);
  overflow: auto;
}

.mermaid-host :deep(svg) {
  max-width: 100%;
  height: auto;
  min-height: 280px;
}

.mermaid-host :deep(.node rect),
.mermaid-host :deep(.node circle),
.mermaid-host :deep(.node polygon),
.mermaid-host :deep(.node ellipse) {
  stroke-width: 2px;
}

.mermaid-host :deep(.edgePath .path) {
  stroke-width: 2px;
}

.mermaid-host :deep(.mermaid-placeholder) {
  color: var(--alp-color-muted);
  font-size: 13px;
}

.mermaid-err {
  color: var(--alp-color-danger);
  font-size: 12px;
  margin-top: 8px;
}

.quiz-grid {
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

.quiz-focus-tag {
  font-size: 10px;
  color: var(--alp-color-primary);
  margin-left: auto;
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
  margin: 5px 0 0;
  font-size: 13px;
  color: var(--alp-color-muted);
}

.trace-overview {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.trace-facts {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.trace-facts > span {
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  color: var(--alp-color-muted);
  font-size: 11px;
}

.trace-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.trace-controls .el-slider {
  flex: 1;
  margin-left: 10px;
}

.trace-verdict {
  font-size: 11px;
  font-family: ui-monospace, monospace;
  color: var(--alp-color-success);
}

.trace-viz-wrap {
  margin-top: 14px;
  min-height: 150px;
  padding: 14px;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
}

.trace-workspace {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(360px, 1.1fr);
  gap: 14px;
}

.trace-source-panel,
.trace-state-panel {
  min-width: 0;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
  overflow: hidden;
}

.trace-source-panel > header,
.trace-state-panel > header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-size: 12px;
  font-weight: 700;
}

.trace-state-panel > header small {
  color: var(--alp-color-muted);
  font-weight: 400;
}

.trace-source-lines {
  margin: 0;
  padding: 8px 0 8px 44px;
  max-height: 350px;
  overflow: auto;
  background: var(--alp-bg-code-ish);
  color: var(--alp-color-muted);
  font: 12px/1.75 ui-monospace, 'Cascadia Code', Consolas, monospace;
}

.trace-source-lines li {
  padding: 0 12px 0 8px;
  border-left: 3px solid transparent;
  white-space: pre;
}

.trace-source-lines li.active {
  border-left-color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 16%, transparent);
  color: var(--alp-color-primary);
}

.trace-source-lines code {
  color: inherit;
}

.trace-variable-grid {
  display: grid;
  gap: 8px;
  padding: 10px;
  max-height: 350px;
  overflow: auto;
}

.trace-variable-card {
  padding: 10px 11px;
  border: 1px solid var(--alp-color-border);
  border-radius: 9px;
  background: var(--alp-bg-surface);
}

.trace-variable-card.changed {
  border-color: color-mix(in srgb, var(--alp-color-primary) 55%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-primary) 7%, var(--alp-bg-surface));
}

.trace-variable-head,
.trace-variable-change {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trace-variable-head {
  justify-content: space-between;
  margin-bottom: 8px;
}

.trace-variable-head span {
  color: var(--alp-color-muted);
  font-size: 10px;
  font-family: ui-monospace, monospace;
}

.trace-variable-change code {
  min-width: 0;
  padding: 4px 7px;
  border-radius: 6px;
  background: var(--alp-bg-code-ish);
  white-space: pre-wrap;
  margin: 0;
  overflow-wrap: anywhere;
  font-size: 12px;
}

.trace-variable-change > span {
  color: var(--alp-color-primary);
  font-weight: 700;
}

.trace-io {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.trace-io > div {
  padding: 10px 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  background: var(--alp-bg-soft-block);
}

.trace-io span {
  color: var(--alp-color-muted);
  font-size: 10px;
}

.trace-io pre {
  margin: 6px 0 0;
  white-space: pre-wrap;
  font-size: 12px;
}

@media (max-width: 960px) {
  .trace-workspace,
  .trace-io {
    grid-template-columns: 1fr;
  }

  .trace-overview,
  .trace-controls {
    align-items: stretch;
    flex-wrap: wrap;
  }

  .trace-controls .el-slider {
    flex-basis: 100%;
    margin-left: 0;
  }
}

.reading-goal {
  margin: 0 0 12px;
  color: var(--alp-color-muted);
}

.reading-levels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}


.reading-level {
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.reading-level h4 {
  margin: 10px 0 4px;
  color: var(--alp-color-primary);
  font-size: 13px;
}

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

/* --- 教学短视频脚本 --- */
.panel-card--video {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.video-info {
  padding: 12px 14px;
  border-radius: 8px;
  background: rgba(124, 58, 237, 0.08);
  border: 1px solid rgba(124, 58, 237, 0.2);
}

.video-info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.video-info-row strong {
  font-size: 15px;
  color: var(--alp-color-text);
}

.video-info-meta {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.video-goal {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.video-goal-tag,
.video-vo-tag,
.video-summary-tag {
  display: inline-block;
  margin-right: 6px;
  padding: 1px 8px;
  font-size: 11px;
  border-radius: 10px;
  background: rgba(124, 58, 237, 0.18);
  color: #7c3aed;
  vertical-align: middle;
}

.video-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-color-surface-2, rgba(0, 0, 0, 0.04));
  border: 1px solid var(--alp-color-border);
}

.video-now-playing {
  color: #7c3aed;
  font-size: 12px;
  font-weight: 500;
}

.video-finished {
  color: #10b981;
  font-size: 12px;
}

.video-paused {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.video-shots {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.video-shot {
  position: relative;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--alp-color-surface, #fff);
  border: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.video-shot:hover {
  border-color: rgba(124, 58, 237, 0.4);
  box-shadow: 0 2px 10px rgba(124, 58, 237, 0.12);
  transform: translateY(-1px);
}

.video-shot--active {
  border-color: #7c3aed;
  box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.3);
  background: rgba(124, 58, 237, 0.06);
}

.video-shot--done {
  opacity: 0.65;
}

.video-shot-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.video-shot-index {
  font-size: 12px;
  font-weight: 600;
  color: #7c3aed;
}

.video-shot-duration {
  font-size: 11px;
  color: var(--alp-color-muted);
  padding: 1px 6px;
  border-radius: 8px;
  background: var(--alp-color-surface-2, rgba(0, 0, 0, 0.05));
}

.video-shot-scene {
  margin: 0 0 6px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.video-shot-hint {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.video-shot-subtitle {
  margin: 0 0 8px;
  padding: 6px 10px;
  border-left: 3px solid #7c3aed;
  background: rgba(124, 58, 237, 0.06);
  font-size: 13px;
  font-weight: 500;
  color: var(--alp-color-text);
  border-radius: 4px;
}

.video-shot-voiceover {
  margin: 0 0 8px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.video-shot-actions {
  display: flex;
  justify-content: flex-end;
}

.video-summary {
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  font-size: 13px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.evidence-trigger {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
