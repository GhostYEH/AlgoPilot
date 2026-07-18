import type { Directive, DirectiveBinding } from 'vue'

type WindowState = {
  key: string
  resizeObserver: ResizeObserver
  mutationObserver: MutationObserver
  observedChild: Element | null
  frame: number | null
}

const states = new WeakMap<HTMLElement, WindowState>()
const maximumHeights = new Map<string, number>()

function animationKey(binding: DirectiveBinding<string>) {
  return binding.value || 'learning-animation'
}

function applyRememberedHeight(el: HTMLElement, key: string) {
  const height = maximumHeights.get(key)
  if (height) el.style.setProperty('--lv-section-window-h', `${height}px`)
  else el.style.removeProperty('--lv-section-window-h')
}

function measure(el: HTMLElement, state: WindowState) {
  if (state.frame !== null) cancelAnimationFrame(state.frame)
  state.frame = requestAnimationFrame(() => {
    state.frame = null
    const child = el.firstElementChild as HTMLElement | null
    if (!child) return

    const height = Math.ceil(Math.max(child.scrollHeight, child.getBoundingClientRect().height))
    if (height <= 0) return

    const previous = maximumHeights.get(state.key) ?? 0
    if (height <= previous) return

    maximumHeights.set(state.key, height)
    el.style.setProperty('--lv-section-window-h', `${height}px`)
  })
}

function observeCurrentChild(el: HTMLElement, state: WindowState) {
  const child = el.firstElementChild
  if (child === state.observedChild) {
    measure(el, state)
    return
  }

  if (state.observedChild) state.resizeObserver.unobserve(state.observedChild)
  state.observedChild = child
  if (child) state.resizeObserver.observe(child)
  measure(el, state)
}

export const stableAnimationWindow: Directive<HTMLElement, string> = {
  mounted(el, binding) {
    const state: WindowState = {
      key: animationKey(binding),
      resizeObserver: new ResizeObserver(() => measure(el, state)),
      mutationObserver: new MutationObserver(() => observeCurrentChild(el, state)),
      observedChild: null,
      frame: null,
    }

    states.set(el, state)
    applyRememberedHeight(el, state.key)
    state.mutationObserver.observe(el, { childList: true })
    observeCurrentChild(el, state)
  },

  updated(el, binding) {
    const state = states.get(el)
    if (!state) return

    const nextKey = animationKey(binding)
    if (nextKey !== state.key) {
      state.key = nextKey
      applyRememberedHeight(el, nextKey)
    }
    observeCurrentChild(el, state)
  },

  unmounted(el) {
    const state = states.get(el)
    if (!state) return
    if (state.frame !== null) cancelAnimationFrame(state.frame)
    state.resizeObserver.disconnect()
    state.mutationObserver.disconnect()
    states.delete(el)
  },
}

