<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, ref, watch } from 'vue'
import type { TraceStep, TraceVarSnapshot } from '@/types/codeTrace'
import {
  associativeEntries,
  associativeViewHint,
  isAssociativeSnapshot,
  isSequenceSnapshot,
  sequenceItems,
  sequenceViewHint,
} from '@/utils/traceProtocol'

const TraceSequenceViz = defineAsyncComponent(
  () => import('@/components/oj/trace/TraceSequenceViz.vue'),
)
const TraceAssociativeViz = defineAsyncComponent(
  () => import('@/components/oj/trace/TraceAssociativeViz.vue'),
)

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

const props = defineProps<{
  payload: Record<string, unknown>
  meta?: Record<string, unknown>
}>()

const tracePayload = computed(() => props.payload as TracePayload)
const traceSteps = computed(() => tracePayload.value.steps ?? [])
const stepIndex = ref(0)
const playing = ref(false)
let playbackTimer: ReturnType<typeof setInterval> | null = null

const currentStep = computed(() => traceSteps.value[stepIndex.value] ?? null)
const previousStep = computed(() =>
  stepIndex.value > 0 ? traceSteps.value[stepIndex.value - 1] : null,
)
const codeLines = computed(() => (tracePayload.value.code ?? '').split('\n'))
const currentLine = computed(() => currentStep.value?.line ?? 0)

function stopPlayback() {
  playing.value = false
  if (playbackTimer) clearInterval(playbackTimer)
  playbackTimer = null
}

function previous() {
  stopPlayback()
  stepIndex.value = Math.max(0, stepIndex.value - 1)
}

function next() {
  stopPlayback()
  stepIndex.value = Math.min(traceSteps.value.length - 1, stepIndex.value + 1)
}

function togglePlayback() {
  if (playing.value) {
    stopPlayback()
    return
  }
  if (!traceSteps.value.length) return
  if (stepIndex.value >= traceSteps.value.length - 1) stepIndex.value = 0
  playing.value = true
  playbackTimer = setInterval(() => {
    if (stepIndex.value >= traceSteps.value.length - 1) {
      stopPlayback()
      return
    }
    stepIndex.value += 1
  }, 900)
}

watch(
  () => props.payload,
  () => {
    stopPlayback()
    stepIndex.value = 0
  },
)
onBeforeUnmount(stopPlayback)

function pickPrimaryVar(step: TraceStep | null): string | null {
  if (!step?.vars) return null
  return step.changed?.[0] ?? Object.keys(step.vars)[0] ?? null
}

const primaryVarName = computed(() => pickPrimaryVar(currentStep.value))
const currentSnapshot = computed((): TraceVarSnapshot | null => {
  const name = primaryVarName.value
  if (!name || !currentStep.value?.vars) return null
  return currentStep.value.vars[name] ?? null
})
const previousSnapshot = computed((): TraceVarSnapshot | null => {
  const name = primaryVarName.value
  if (!name || !previousStep.value?.vars) return null
  return previousStep.value.vars[name] ?? null
})
const isSequence = computed(
  () => !!currentSnapshot.value && isSequenceSnapshot(currentSnapshot.value),
)
const isAssociative = computed(
  () => !!currentSnapshot.value && isAssociativeSnapshot(currentSnapshot.value),
)

function formatValue(snapshot: TraceVarSnapshot | undefined): string {
  if (!snapshot) return '未定义'
  if (snapshot.value === null) return 'None'
  if (typeof snapshot.value === 'string') return snapshot.value || '空字符串'
  if (
    typeof snapshot.value === 'number' ||
    typeof snapshot.value === 'boolean'
  ) return String(snapshot.value)
  try {
    return JSON.stringify(snapshot.value, null, 2)
  } catch {
    return String(snapshot.value)
  }
}

const variables = computed(() => {
  const currentVars = currentStep.value?.vars ?? {}
  const previousVars = previousStep.value?.vars ?? {}
  const changed = new Set(currentStep.value?.changed ?? [])
  return Object.entries(currentVars).map(([name, snapshot]) => ({
    name,
    type: snapshot.type || typeof snapshot.value,
    current: formatValue(snapshot),
    previous: formatValue(previousVars[name]),
    changed: changed.has(name),
  }))
})
</script>

<template>
  <div v-if="traceSteps.length" class="trace-player">
    <div class="trace-overview">
      <div>
        <strong>{{ tracePayload.title || '算法执行过程' }}</strong>
        <p v-if="tracePayload.narration_hint" class="trace-hint">
          {{ tracePayload.narration_hint }}
        </p>
      </div>
      <div class="trace-facts">
        <span>Step {{ stepIndex + 1 }} / {{ traceSteps.length }}</span>
        <span>源码第 {{ currentLine }} 行</span>
        <span class="trace-verdict">{{ tracePayload.verdict ?? 'OK' }}</span>
      </div>
    </div>

    <el-alert
      v-if="meta?.trace_recovered"
      type="success"
      :closable="false"
      show-icon
      title="已自动修复不可执行的 Agent 输出，并录制同主题有效轨迹"
      class="trace-recovered"
    />

    <div class="trace-controls">
      <el-button size="small" :disabled="stepIndex === 0" @click="previous">上一步</el-button>
      <el-button size="small" type="primary" @click="togglePlayback">
        {{ playing ? '暂停' : stepIndex >= traceSteps.length - 1 ? '重新播放' : '播放动画' }}
      </el-button>
      <el-button
        size="small"
        :disabled="stepIndex >= traceSteps.length - 1"
        @click="next"
      >
        下一步
      </el-button>
      <el-slider
        v-model="stepIndex"
        :min="0"
        :max="Math.max(0, traceSteps.length - 1)"
        :format-tooltip="(value: number) => `Step ${value + 1}`"
        @input="stopPlayback"
      />
    </div>

    <div class="trace-workspace">
      <section class="trace-source-panel" aria-label="题解源码执行位置">
        <header>题解源码</header>
        <ol class="trace-source-lines">
          <li
            v-for="(line, index) in codeLines"
            :key="index"
            :class="{ active: index + 1 === currentLine }"
          >
            <code>{{ line || ' ' }}</code>
          </li>
        </ol>
      </section>

      <section class="trace-state-panel" aria-label="当前变量状态">
        <header>
          <span>变量状态</span>
          <small>
            {{ currentStep?.changed?.length ? `本步变化：${currentStep.changed.join('、')}` : '本步无变量变化' }}
          </small>
        </header>
        <div v-if="variables.length" class="trace-variable-grid">
          <article
            v-for="variable in variables"
            :key="variable.name"
            class="trace-variable-card"
            :class="{ changed: variable.changed }"
          >
            <div class="trace-variable-head">
              <strong>{{ variable.name }}</strong>
              <span>{{ variable.type }}</span>
            </div>
            <div class="trace-variable-change">
              <code v-if="stepIndex > 0">{{ variable.previous }}</code>
              <span v-if="stepIndex > 0">→</span>
              <code>{{ variable.current }}</code>
            </div>
          </article>
        </div>
        <el-empty v-else :image-size="54" description="当前步骤没有可展示变量" />
      </section>
    </div>

    <div
      v-if="currentSnapshot && primaryVarName && (isSequence || isAssociative)"
      class="trace-viz-wrap"
    >
      <TraceSequenceViz
        v-if="isSequence"
        :name="primaryVarName"
        :view-hint="sequenceViewHint(currentSnapshot)"
        :items="sequenceItems(currentSnapshot)"
        :prev-items="previousSnapshot ? sequenceItems(previousSnapshot) : []"
        :var-changed="true"
      />
      <TraceAssociativeViz
        v-else-if="isAssociative"
        :name="primaryVarName"
        :view-hint="associativeViewHint(currentSnapshot)"
        :entries="associativeEntries(currentSnapshot)"
        :prev-entries="previousSnapshot ? associativeEntries(previousSnapshot) : []"
        :var-changed="true"
      />
    </div>

    <div v-if="tracePayload.stdin || tracePayload.result_preview || tracePayload.stdout" class="trace-io">
      <div><span>输入</span><pre>{{ tracePayload.stdin || '—' }}</pre></div>
      <div><span>实际输出</span><pre>{{ tracePayload.result_preview || '—' }}</pre></div>
      <div><span>期望输出</span><pre>{{ tracePayload.stdout || '—' }}</pre></div>
    </div>
  </div>

  <div v-else class="trace-unavailable">
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="这份历史资源没有录到可播放轨迹"
      description="系统只保留了 Agent 生成的代码，且该代码未通过执行追踪。请重新生成资源；新版本会自动替换不可执行结果。"
    />
    <pre v-if="tracePayload.code" class="legacy-code"><code>{{ tracePayload.code }}</code></pre>
  </div>
</template>

<style scoped>
.trace-overview {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.trace-hint {
  margin: 5px 0 0;
  font-size: 13px;
  color: var(--alp-color-muted);
}

.trace-facts {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.trace-facts > span {
  padding: 4px 8px;
  border: 1px solid var(--alp-color-border);
  border-radius: 999px;
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-muted);
  font-size: 11px;
}

.trace-verdict {
  color: var(--alp-color-success);
  font-family: ui-monospace, monospace;
}

.trace-recovered {
  margin-bottom: 12px;
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

.trace-workspace {
  display: grid;
  grid-template-columns: minmax(280px, 0.9fr) minmax(300px, 1.1fr);
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
  font: 10px ui-monospace, monospace;
}

.trace-variable-change code {
  min-width: 0;
  padding: 4px 7px;
  border-radius: 6px;
  background: var(--alp-bg-code-ish);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 12px;
}

.trace-variable-change > span {
  color: var(--alp-color-primary);
  font-weight: 700;
}

.trace-viz-wrap {
  margin-top: 14px;
  min-height: 150px;
  padding: 14px;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
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

.trace-unavailable {
  display: grid;
  gap: 12px;
}

.legacy-code {
  margin: 0;
  padding: 12px;
  max-height: 320px;
  overflow: auto;
  border-radius: 10px;
  background: var(--alp-bg-code-ish);
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
</style>
