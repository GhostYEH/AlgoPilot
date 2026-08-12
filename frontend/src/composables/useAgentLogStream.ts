import { onUnmounted, ref, watch, type Ref } from 'vue'
import type { AgentConsoleLine } from '@/utils/agentConsole'
import { inferLogTier, type LogTier } from '@/utils/agentConsole'

export interface StreamedConsoleLine extends AgentConsoleLine {
  tier: LogTier
  /** 打字机效果：当前已显示的消息片段 */
  typedMessage: string
  /** 该行打字是否完成 */
  typingDone: boolean
}

const TRACE_TRIGGER_RE =
  /正在生成动画资源|trace_runner|轨迹动画|编译标准题解/i

function isStreamRestart(next: AgentConsoleLine[], prev: AgentConsoleLine[] | undefined): boolean {
  if (!prev?.length) return next.length > 0
  if (next.length < prev.length) return true
  return next[0]?.id !== prev[0]?.id
}

export function useAgentLogStream(
  source: Ref<AgentConsoleLine[]>,
  options?: {
    lineIntervalMs?: number
    charIntervalMs?: number
    enabled?: Ref<boolean>
  },
) {
  const lineIntervalMs = options?.lineIntervalMs ?? 500
  const charIntervalMs = options?.charIntervalMs ?? 18
  const enabled = options?.enabled

  const visibleLines = ref<StreamedConsoleLine[]>([])
  const traceVizActive = ref(false)
  const traceAssemblyPhase = ref<'idle' | 'generating' | 'ready'>('idle')

  let lineTimer: number | undefined
  let charTimer: number | undefined
  let traceReadyTimer: number | undefined
  let queueIndex = 0
  let typingIndex = -1

  function clearTimers() {
    if (lineTimer) window.clearTimeout(lineTimer)
    if (charTimer) window.clearInterval(charTimer)
    if (traceReadyTimer) window.clearTimeout(traceReadyTimer)
    lineTimer = undefined
    charTimer = undefined
    traceReadyTimer = undefined
  }

  function isEnabled(): boolean {
    return enabled?.value !== false
  }

  function checkTraceTrigger(line: AgentConsoleLine) {
    if (!TRACE_TRIGGER_RE.test(line.message)) return
    traceVizActive.value = true
    traceAssemblyPhase.value = 'generating'
    if (traceReadyTimer) window.clearTimeout(traceReadyTimer)
    traceReadyTimer = window.setTimeout(() => {
      traceAssemblyPhase.value = 'ready'
      traceReadyTimer = undefined
    }, 2200)
  }

  function startTypingLine(idx: number) {
    if (!isEnabled()) return
    if (charTimer) window.clearInterval(charTimer)
    const line = visibleLines.value[idx]
    if (!line) return

    typingIndex = idx
    let pos = 0
    const full = line.message

    charTimer = window.setInterval(() => {
      pos += 1
      const current = visibleLines.value[idx]
      if (!current) {
        if (charTimer) window.clearInterval(charTimer)
        charTimer = undefined
        typingIndex = -1
        return
      }
      if (pos >= full.length) {
        visibleLines.value[idx] = {
          ...current,
          typedMessage: full,
          typingDone: true,
        }
        if (charTimer) window.clearInterval(charTimer)
        charTimer = undefined
        typingIndex = -1
        scheduleNextLine()
        return
      }
      visibleLines.value[idx] = {
        ...current,
        typedMessage: full.slice(0, pos),
      }
    }, charIntervalMs)
  }

  function scheduleNextLine() {
    if (!isEnabled()) return
    if (lineTimer) window.clearTimeout(lineTimer)
    if (queueIndex >= source.value.length) return
    if (typingIndex >= 0) return

    lineTimer = window.setTimeout(() => {
      lineTimer = undefined
      const raw = source.value[queueIndex]
      queueIndex += 1
      if (!raw) return

      checkTraceTrigger(raw)

      const streamed: StreamedConsoleLine = {
        ...raw,
        tier: inferLogTier(raw.agent, raw.status, raw.message),
        typedMessage: '',
        typingDone: false,
      }
      visibleLines.value = [...visibleLines.value, streamed]
      startTypingLine(visibleLines.value.length - 1)
    }, lineIntervalMs)
  }

  function hardReset() {
    clearTimers()
    queueIndex = 0
    typingIndex = -1
    visibleLines.value = []
    traceVizActive.value = false
    traceAssemblyPhase.value = 'idle'
  }

  function resetStream() {
    hardReset()
    if (isEnabled() && source.value.length) scheduleNextLine()
  }

  watch(
    () => source.value,
    (lines, old) => {
      if (!isEnabled()) return

      if (!lines.length) {
        hardReset()
        return
      }

      if (isStreamRestart(lines, old)) {
        hardReset()
        scheduleNextLine()
        return
      }

      if (
        lines.length > (old?.length ?? 0) &&
        queueIndex < lines.length &&
        typingIndex < 0 &&
        queueIndex >= visibleLines.value.length
      ) {
        scheduleNextLine()
      }
    },
  )

  if (enabled) {
    watch(enabled, (on) => {
      if (!on) {
        clearTimers()
        typingIndex = -1
        return
      }
      if (source.value.length && !visibleLines.value.length) {
        queueIndex = 0
        scheduleNextLine()
      }
    })
  }

  onUnmounted(clearTimers)

  return {
    visibleLines,
    traceVizActive,
    traceAssemblyPhase,
    resetStream,
  }
}
