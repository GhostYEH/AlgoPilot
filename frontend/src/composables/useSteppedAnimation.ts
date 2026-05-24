import { computed, onMounted, onUnmounted, ref, watch, type Ref } from 'vue'
import { usePrefersReducedMotion } from '@/composables/usePrefersReducedMotion'

export interface UseSteppedAnimationOptions {
  sectionId: Ref<string>
  maxStepForSection: (id: string) => number
  stepMs?: number
  onSectionChange?: () => void
}

/** 分步演示：自动轮播；标签页隐藏时暂停；减少动态效果时不自动播放 */
export function useSteppedAnimation(opts: UseSteppedAnimationOptions) {
  const { prefersReducedMotion } = usePrefersReducedMotion()

  const baseStepMs = opts.stepMs ?? 900
  let tick: ReturnType<typeof setInterval> | null = null

  const playing = ref(true)
  const step = ref(0)
  const tabHidden = ref(false)

  const maxStep = computed(() => Math.max(0, opts.maxStepForSection(opts.sectionId.value)))
  const useStepped = computed(() => maxStep.value > 0)

  const stepIntervalMs = computed(() => {
    if (prefersReducedMotion.value) return 0
    return baseStepMs
  })

  function clearTick() {
    if (tick) {
      clearInterval(tick)
      tick = null
    }
  }

  function canAutoPlay() {
    return useStepped.value && playing.value && !tabHidden.value && stepIntervalMs.value > 0
  }

  function armTick() {
    clearTick()
    if (!canAutoPlay()) return
    const m = maxStep.value
    const ms = stepIntervalMs.value
    tick = setInterval(() => {
      step.value = step.value >= m ? 0 : step.value + 1
    }, ms)
  }

  function onVisibilityChange() {
    tabHidden.value = typeof document !== 'undefined' && document.hidden
    armTick()
  }

  function togglePlay() {
    if (prefersReducedMotion.value) {
      manualNext()
      return
    }
    playing.value = !playing.value
    armTick()
  }

  function manualNext() {
    const m = maxStep.value
    step.value = step.value >= m ? 0 : step.value + 1
  }

  function resetAnim() {
    step.value = 0
    opts.onSectionChange?.()
    if (!prefersReducedMotion.value) {
      playing.value = true
    }
    armTick()
  }

  watch(
    () => opts.sectionId.value,
    () => {
      step.value = 0
      if (!prefersReducedMotion.value) {
        playing.value = true
      }
      armTick()
    },
  )

  watch([playing, useStepped, maxStep, stepIntervalMs, tabHidden], armTick)

  watch(prefersReducedMotion, (reduced) => {
    if (reduced) {
      playing.value = false
      clearTick()
    } else {
      playing.value = true
      armTick()
    }
  })

  onMounted(() => {
    if (!prefersReducedMotion.value) {
      playing.value = true
    }
    document.addEventListener('visibilitychange', onVisibilityChange)
    onVisibilityChange()
    armTick()
  })

  onUnmounted(() => {
    clearTick()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return {
    playing,
    step,
    useStepped,
    maxStep,
    prefersReducedMotion,
    togglePlay,
    manualNext,
    resetAnim,
  }
}
