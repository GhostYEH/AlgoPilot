import { onMounted, onBeforeUnmount, ref, type Ref } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

/**
 * AlgoPilot GSAP \u52a8\u753b\u7ec4\u5408\u5f0f\u51fd\u6570
 * \u57fa\u4e8e Impeccable animate.md \u6700\u4f73\u5b9e\u8df5 + GSAP Core skills
 */

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * 从 ref.value 中解析出真正的 DOM 元素。
 * 当 ref 绑定到 Vue 组件（如 el-row）时，ref.value 是组件实例而非 DOM 元素，
 * 此时通过 $el 取到组件的根 DOM 节点。
 */
function resolveEl(el: HTMLElement | null): HTMLElement | null {
  if (!el) return null
  if (typeof el.querySelectorAll === 'function') return el
  const root = (el as any).$el
  return root instanceof HTMLElement ? root : null
}

/** \u6de1\u5165 + \u4e0a\u6ed1\u5165\u573a */
export function useFadeSlideIn(
  refEl: Ref<HTMLElement | null>,
  options?: { y?: number; duration?: number; delay?: number; ease?: string },
) {
  if (prefersReducedMotion()) return
  const opts = { y: 12, duration: 0.3, delay: 0, ease: 'power2.out', ...options }
  onMounted(() => {
    if (!refEl.value) return
    gsap.from(refEl.value, {
      y: opts.y, opacity: 0, duration: opts.duration, delay: opts.delay,
      ease: opts.ease, clearProps: 'transform,opacity',
    })
  })
}

/** \u4ea4\u9519\u5165\u573a (\u5217\u8868/\u5361\u7247\u7f51\u683c) */
export function useStaggerIn(
  refContainer: Ref<HTMLElement | null>,
  selector: string,
  options?: { stagger?: number; from?: string; y?: number; duration?: number },
) {
  if (prefersReducedMotion()) return
  const opts = { stagger: 0.04, from: 'start', y: 12, duration: 0.3, ...options }
  onMounted(() => {
    const container = resolveEl(refContainer.value)
    if (!container) return
    const items = container.querySelectorAll(selector)
    if (items.length === 0) return
    gsap.from(items, {
      y: opts.y, opacity: 0, duration: opts.duration,
      stagger: { each: opts.stagger, from: opts.from as any },
      ease: 'power2.out', clearProps: 'transform,opacity',
    })
  })
}

/** 缩放入场 */
export function useScaleIn(
  refEl: Ref<HTMLElement | null>,
  options?: { duration?: number; ease?: string },
) {
  if (prefersReducedMotion()) return
  const opts = { duration: 0.4, ease: 'back.out(1.4)', ...options }
  onMounted(() => {
    if (!refEl.value) return
    gsap.from(refEl.value, {
      scale: 0.92, opacity: 0, duration: opts.duration,
      ease: opts.ease, clearProps: 'transform,opacity',
    })
  })
}

/** \u6eda\u52a8\u65f6\u89e6\u53d1\u6de1\u5165\u4e0a\u6ed1 */
export function useScrollReveal(
  refEl: Ref<HTMLElement | null>,
  options?: { y?: number; duration?: number; stagger?: number; start?: string },
) {
  if (prefersReducedMotion()) return
  const opts = { y: 16, duration: 0.3, stagger: 0, start: 'top 88%', ...options }
  let st: ScrollTrigger | null = null
  onMounted(() => {
    const el = resolveEl(refEl.value)
    if (!el) return
    st = ScrollTrigger.create({
      trigger: el,
      start: opts.start,
      toggleActions: 'play none none none',
      onEnter: () => {
        const target = resolveEl(refEl.value)
        if (!target) return
        gsap.from(target, {
          y: opts.y, opacity: 0, duration: opts.duration,
          stagger: opts.stagger > 0 ? opts.stagger : undefined,
          ease: 'power2.out', clearProps: 'transform,opacity',
        })
      },
    })
  })
  onBeforeUnmount(() => st?.kill())
}

/** \u5fae\u4ea4\u4e92: \u6309\u94ae\u5f39\u8d77 */
export function useBtnBounce(refEl: Ref<HTMLElement | null>) {
  function bounce() {
    if (!refEl.value || prefersReducedMotion()) return
    gsap.timeline()
      .to(refEl.value, { scale: 0.95, duration: 0.08, ease: 'power2.in' })
      .to(refEl.value, { scale: 1.03, duration: 0.12, ease: 'power2.out' })
      .to(refEl.value, { scale: 1, duration: 0.06 })
  }
  return { bounce }
}

/** \u6570\u5b57\u9012\u589e\u52a8\u753b */
export function useCountUp(
  _refEl: Ref<HTMLElement | null>,
  target: number,
  options?: { duration?: number },
) {
  const opts = { duration: 1.2, ...options }
  const displayed = ref(0)
  onMounted(() => {
    if (prefersReducedMotion()) { displayed.value = target; return }
    const obj = { val: 0 }
    gsap.to(obj, {
      val: target, duration: opts.duration, ease: 'power2.out',
      onUpdate: () => { displayed.value = Math.round(obj.val) },
    })
  })
  return { displayed }
}

/** \u521d\u59cb\u5316 GSAP \u5168\u5c40\u9ed8\u8ba4\u503c */
export function initGsapDefaults() {
  gsap.defaults({ duration: 0.25, ease: 'power2.out' })
}

/** Dramatic hero entrance timeline — stagger children for visible effect */
export function useHeroEntrance(
  refContainer: Ref<HTMLElement | null>,
  options?: { delay?: number; duration?: number },
) {
  if (prefersReducedMotion()) return
  const opts = { delay: 0.2, duration: 0.7, ...options }
  onMounted(() => {
    if (!refContainer.value) return
    const children = refContainer.value.children
    if (!children.length) return
    gsap.from(children, {
      y: 40,
      opacity: 0,
      duration: opts.duration,
      stagger: 0.12,
      ease: 'power3.out',
      delay: opts.delay,
      clearProps: 'transform,opacity',
    })
  })
}

/** Visible card stagger — cards fly in from below with bounce */
export function useCardStagger(
  refContainer: Ref<HTMLElement | null>,
  selector: string,
  options?: { stagger?: number; y?: number; duration?: number; ease?: string },
) {
  if (prefersReducedMotion()) return
  const opts = { stagger: 0.08, y: 30, duration: 0.6, ease: 'back.out(1.4)', ...options }
  onMounted(() => {
    const container = resolveEl(refContainer.value)
    if (!container) return
    const items = container.querySelectorAll(selector)
    if (!items.length) return
    gsap.from(items, {
      y: opts.y,
      opacity: 0,
      scale: 0.95,
      duration: opts.duration,
      stagger: opts.stagger,
      ease: opts.ease,
      clearProps: 'transform,opacity',
    })
  })
}
