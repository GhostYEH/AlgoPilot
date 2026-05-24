import { computed, onUnmounted, ref, watch, type Ref } from 'vue'
import type { TraceResponse, TraceStep } from '@/types/codeTrace'
import { usePrefersReducedMotion } from '@/composables/usePrefersReducedMotion'

export const TRACE_PLAYBACK_SPEEDS = [0.5, 1, 2] as const
export type TracePlaybackSpeed = (typeof TRACE_PLAYBACK_SPEEDS)[number]

const BASE_STEP_MS = 850

export function useCodeTracePlayback(trace: Ref<TraceResponse | null>) {
  const { prefersReducedMotion } = usePrefersReducedMotion()

  const playing = ref(false)
  const frame = ref(0)
  const playbackSpeed = ref<TracePlaybackSpeed>(1)
  let tick: ReturnType<typeof setInterval> | null = null

  const steps = computed<TraceStep[]>(() => trace.value?.steps ?? [])
  const maxFrame = computed(() => Math.max(0, steps.value.length - 1))
  const current = computed(() => steps.value[frame.value] ?? null)
  const hasTrace = computed(() => (trace.value?.steps.length ?? 0) > 0)

  const stepIntervalMs = computed(() => {
    if (prefersReducedMotion.value) return 0
    return Math.round(BASE_STEP_MS / playbackSpeed.value)
  })

  function clearTick() {
    if (tick) {
      clearInterval(tick)
      tick = null
    }
  }

  function armTick() {
    clearTick()
    const ms = stepIntervalMs.value
    if (!playing.value || ms <= 0 || maxFrame.value <= 0) return
    tick = setInterval(() => {
      frame.value = frame.value >= maxFrame.value ? 0 : frame.value + 1
    }, ms)
  }

  function setPlaybackSpeed(speed: TracePlaybackSpeed) {
    playbackSpeed.value = speed
    armTick()
  }

  function togglePlay() {
    if (prefersReducedMotion.value) {
      next()
      return
    }
    playing.value = !playing.value
    armTick()
  }

  function next() {
    frame.value = frame.value >= maxFrame.value ? 0 : frame.value + 1
  }

  function prev() {
    frame.value = frame.value <= 0 ? maxFrame.value : frame.value - 1
  }

  function reset() {
    frame.value = 0
    if (!prefersReducedMotion.value) playing.value = true
    armTick()
  }

  function stop() {
    playing.value = false
    clearTick()
  }

  function jumpToFrame(index: number) {
    const target = Math.max(0, Math.min(index, maxFrame.value))
    frame.value = target
    playing.value = false
    clearTick()
  }

  watch(trace, () => {
    frame.value = 0
    playing.value = !prefersReducedMotion.value && hasTrace.value
    armTick()
  })

  watch([playing, maxFrame, stepIntervalMs, prefersReducedMotion], armTick)

  onUnmounted(clearTick)

  return {
    playing,
    frame,
    maxFrame,
    current,
    hasTrace,
    playbackSpeed,
    stepIntervalMs,
    setPlaybackSpeed,
    togglePlay,
    next,
    prev,
    reset,
    stop,
    jumpToFrame,
  }
}
