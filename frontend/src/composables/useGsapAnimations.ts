import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

/**
 * AlgoPilot 的 GSAP 动画组合式函数。
 * 所有 DOM 动画都在 mounted 后创建，并通过 gsap.context 在卸载时回滚。
 */

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function resolveEl(el: HTMLElement | null): HTMLElement | null {
  if (!el) return null
  if (typeof el.querySelectorAll === 'function') return el
  const root = (el as any).$el
  return root instanceof HTMLElement ? root : null
}

function useScopedContext(
  refEl: Ref<HTMLElement | null>,
  setup: (scope: HTMLElement) => void,
) {
  let context: gsap.Context | null = null

  onMounted(() => {
    const scope = resolveEl(refEl.value)
    if (!scope || prefersReducedMotion()) return
    context = gsap.context(() => setup(scope), scope)
  })

  onBeforeUnmount(() => context?.revert())
}

/** 淡入 + 上滑入场 */
export function useFadeSlideIn(
  refEl: Ref<HTMLElement | null>,
  options?: { y?: number; duration?: number; delay?: number; ease?: string },
) {
  const opts = { y: 12, duration: 0.3, delay: 0, ease: 'power2.out', ...options }
  useScopedContext(refEl, (scope) => {
    gsap.from(scope, {
      y: opts.y,
      autoAlpha: 0,
      duration: opts.duration,
      delay: opts.delay,
      ease: opts.ease,
      clearProps: 'transform,opacity,visibility',
    })
  })
}

/** 交错入场（列表/卡片网格） */
export function useStaggerIn(
  refContainer: Ref<HTMLElement | null>,
  selector: string,
  options?: { stagger?: number; from?: string; y?: number; duration?: number },
) {
  const opts = { stagger: 0.04, from: 'start', y: 12, duration: 0.3, ...options }
  useScopedContext(refContainer, (container) => {
    const items = container.querySelectorAll(selector)
    if (!items.length) return
    gsap.from(items, {
      y: opts.y,
      autoAlpha: 0,
      duration: opts.duration,
      stagger: { each: opts.stagger, from: opts.from as any },
      ease: 'power2.out',
      clearProps: 'transform,opacity,visibility',
    })
  })
}

/** 缩放入场 */
export function useScaleIn(
  refEl: Ref<HTMLElement | null>,
  options?: { duration?: number; ease?: string },
) {
  const opts = { duration: 0.4, ease: 'back.out(1.4)', ...options }
  useScopedContext(refEl, (scope) => {
    gsap.from(scope, {
      scale: 0.92,
      autoAlpha: 0,
      duration: opts.duration,
      ease: opts.ease,
      clearProps: 'transform,opacity,visibility',
    })
  })
}

/** 滚动时触发淡入上滑 */
export function useScrollReveal(
  refEl: Ref<HTMLElement | null>,
  options?: { y?: number; duration?: number; stagger?: number; start?: string },
) {
  const opts = { y: 16, duration: 0.3, stagger: 0, start: 'top 88%', ...options }
  let trigger: ScrollTrigger | null = null

  useScopedContext(refEl, (scope) => {
    trigger = ScrollTrigger.create({
      trigger: scope,
      start: opts.start,
      toggleActions: 'play none none none',
      onEnter: () => {
        gsap.from(scope, {
          y: opts.y,
          autoAlpha: 0,
          duration: opts.duration,
          stagger: opts.stagger > 0 ? opts.stagger : undefined,
          ease: 'power2.out',
          clearProps: 'transform,opacity,visibility',
        })
      },
    })
  })

  onBeforeUnmount(() => trigger?.kill())
}

/** 微交互：按钮弹起 */
export function useBtnBounce(refEl: Ref<HTMLElement | null>) {
  let timeline: gsap.core.Timeline | null = null

  function bounce() {
    const target = resolveEl(refEl.value)
    if (!target || prefersReducedMotion()) return
    timeline?.kill()
    timeline = gsap.timeline({ defaults: { overwrite: 'auto' } })
      .to(target, { scale: 0.95, duration: 0.08, ease: 'power2.in' })
      .to(target, { scale: 1.03, duration: 0.12, ease: 'power2.out' })
      .to(target, { scale: 1, duration: 0.06 })
  }

  onBeforeUnmount(() => timeline?.kill())
  return { bounce }
}

/** 数字递增动画 */
export function useCountUp(
  _refEl: Ref<HTMLElement | null>,
  target: number,
  options?: { duration?: number },
) {
  const opts = { duration: 1.2, ...options }
  const displayed = ref(0)
  let tween: gsap.core.Tween | null = null

  onMounted(() => {
    if (prefersReducedMotion()) {
      displayed.value = target
      return
    }
    const obj = { val: 0 }
    tween = gsap.to(obj, {
      val: target,
      duration: opts.duration,
      ease: 'power2.out',
      onUpdate: () => { displayed.value = Math.round(obj.val) },
    })
  })

  onBeforeUnmount(() => tween?.kill())
  return { displayed }
}

/** 初始化 GSAP 全局默认值 */
export function initGsapDefaults() {
  gsap.defaults({ duration: 0.25, ease: 'power2.out' })
}

/** Hero 入场：交错展示直接子元素 */
export function useHeroEntrance(
  refContainer: Ref<HTMLElement | null>,
  options?: { delay?: number; duration?: number },
) {
  const opts = { delay: 0.2, duration: 0.7, ...options }
  useScopedContext(refContainer, (container) => {
    const children = container.children
    if (!children.length) return
    gsap.from(children, {
      y: 40,
      autoAlpha: 0,
      duration: opts.duration,
      stagger: 0.12,
      ease: 'power3.out',
      delay: opts.delay,
      clearProps: 'transform,opacity,visibility',
    })
  })
}

/** 卡片交错入场 */
export function useCardStagger(
  refContainer: Ref<HTMLElement | null>,
  selector: string,
  options?: { stagger?: number; y?: number; duration?: number; ease?: string },
) {
  const opts = { stagger: 0.08, y: 30, duration: 0.6, ease: 'back.out(1.4)', ...options }
  useScopedContext(refContainer, (container) => {
    const items = container.querySelectorAll(selector)
    if (!items.length) return
    gsap.from(items, {
      y: opts.y,
      autoAlpha: 0,
      scale: 0.95,
      duration: opts.duration,
      stagger: opts.stagger,
      ease: opts.ease,
      clearProps: 'transform,opacity,visibility',
    })
  })
}
