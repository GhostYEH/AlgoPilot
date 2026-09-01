<script setup lang="ts">
import { computed, onBeforeUnmount } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import { gsap } from 'gsap'
import { usePrefersReducedMotion } from '@/composables/usePrefersReducedMotion'

const props = withDefaults(
  defineProps<{
    route: RouteLocationNormalizedLoaded
    /**
     * 顶层路由壳（App.vue）：仅在「登录/注册 ↔ 主布局」之间过渡，
     * 避免子路由切换时重复播放整页动画。
     */
    shell?: boolean
  }>(),
  { shell: false },
)

/** 路由 meta.transition 可覆盖；公开认证页默认 page-auth */
const transitionName = computed(() => {
  if (props.shell) return 'page-fade-slide'

  const custom = props.route.meta.transition
  if (typeof custom === 'string' && custom.length > 0) return custom
  if (props.route.meta.public) return 'page-auth'
  if (props.route.path.startsWith('/learn/')) return 'page-learn'
  if (props.route.path.startsWith('/practice')) return 'page-instant'
  return 'page-fade-slide'
})

const routeKey = computed(() =>
  props.shell
    ? (props.route.matched[0]?.path ?? props.route.path)
    : props.route.path,
)

const { prefersReducedMotion } = usePrefersReducedMotion()

type TransitionElement = Element & { style?: CSSStyleDeclaration }

let activeContext: gsap.Context | null = null

function isInstant() {
  return transitionName.value === 'page-instant' || prefersReducedMotion.value ||
    (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches)
}

function transitionValues(phase: 'enter' | 'leave') {
  if (transitionName.value === 'page-auth') {
    return phase === 'enter'
      ? { scale: 0.97, y: 14 }
      : { scale: 1.02, y: -8 }
  }
  if (transitionName.value === 'page-learn') {
    return phase === 'enter'
      ? { x: 20, y: 8 }
      : { x: -14, y: 0 }
  }
  return phase === 'enter' ? { x: 0, y: 12 } : { x: 0, y: -6 }
}

function clearTransitionStyles(element: TransitionElement) {
  gsap.set(element, { clearProps: 'opacity,visibility,transform' })
}

function beforeEnter(element: Element) {
  const target = element as TransitionElement
  activeContext?.revert()
  activeContext = null
  if (isInstant()) {
    clearTransitionStyles(target)
    return
  }
  gsap.set(target, { autoAlpha: 0, ...transitionValues('enter') })
}

function enter(element: Element, done: () => void) {
  const target = element as TransitionElement
  if (isInstant()) {
    clearTransitionStyles(target)
    done()
    return
  }
  activeContext = gsap.context(() => {
    gsap.to(target, {
      autoAlpha: 1,
      x: 0,
      y: 0,
      scale: 1,
      duration: 0.28,
      ease: 'power3.out',
      overwrite: 'auto',
      onComplete: () => {
        clearTransitionStyles(target)
        done()
      },
    })
  }, target)
}

function leave(element: Element, done: () => void) {
  const target = element as TransitionElement
  if (isInstant()) {
    done()
    return
  }
  activeContext?.revert()
  activeContext = gsap.context(() => {
    gsap.to(target, {
      autoAlpha: 0,
      ...transitionValues('leave'),
      duration: 0.14,
      ease: 'power2.in',
      overwrite: 'auto',
      onComplete: done,
    })
  }, target)
}

function cancel(element: Element) {
  const target = element as TransitionElement
  gsap.killTweensOf(target)
  clearTransitionStyles(target)
  activeContext?.revert()
  activeContext = null
}

onBeforeUnmount(() => {
  // Transition hooks own the individual tweens; this handles route teardown.
  activeContext?.revert()
  activeContext = null
})
</script>

<template>
  <Transition
    :name="transitionName"
    :mode="transitionName === 'page-instant' ? 'default' : 'out-in'"
    :css="false"
    appear
    @before-enter="beforeEnter"
    @enter="enter"
    @leave="leave"
    @enter-cancelled="cancel"
    @leave-cancelled="cancel"
  >
    <div :key="routeKey" class="page-transition-root">
      <slot />
    </div>
  </Transition>
</template>

<style scoped>
.page-transition-root {
  width: 100%;
  min-height: 0;
}
</style>
