import { onMounted, onUnmounted, ref } from 'vue'

const QUERY = '(prefers-reduced-motion: reduce)'

/** 系统「减少动态效果」：用于关闭自动轮播、弱化 CSS 动画 */
export function usePrefersReducedMotion() {
  const prefersReducedMotion = ref(false)

  let mq: MediaQueryList | null = null

  function sync() {
    prefersReducedMotion.value =
      typeof window !== 'undefined' && window.matchMedia(QUERY).matches
  }

  onMounted(() => {
    if (typeof window === 'undefined') return
    mq = window.matchMedia(QUERY)
    sync()
    mq.addEventListener('change', sync)
  })

  onUnmounted(() => {
    mq?.removeEventListener('change', sync)
  })

  return { prefersReducedMotion }
}
