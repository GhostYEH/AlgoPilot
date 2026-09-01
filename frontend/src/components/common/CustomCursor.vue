<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { gsap } from 'gsap'

const HOVER_SELECTOR = [
  'a',
  'button:not(:disabled):not(.is-disabled)',
  '[role="button"]:not([aria-disabled="true"]):not(.is-disabled)',
  'input[type="button"]:not(:disabled)',
  'input[type="submit"]:not(:disabled)',
  'input[type="reset"]:not(:disabled)',
  '.el-button:not(.is-disabled):not(:disabled)',
  '.el-menu-item:not(.is-disabled)',
  '.el-sub-menu__title:not(.is-disabled)',
  '.el-dropdown-item:not(.is-disabled)',
  '.el-link',
  'summary',
  '[data-cursor="hover"]',
].join(',')

const NATIVE_CURSOR_SELECTOR = [
  'input:not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]):not([type="color"])',
  'textarea',
  'select',
  '[contenteditable="true"]',
  '.cm-editor',
  '.cm-content',
  '.cm-scroller',
  '.cm-gutters',
].join(',')

const isVisible = ref(false)
const isHovering = ref(false)
const isPressed = ref(false)
const ring = ref<HTMLElement | null>(null)
const dot = ref<HTMLElement | null>(null)

let pointerMediaQuery: MediaQueryList | null = null
let reducedMotionMediaQuery: MediaQueryList | null = null
let listenersActive = false
let cursorContext: gsap.Context | null = null
let ringXTo: ((value: number) => void) | null = null
let ringYTo: ((value: number) => void) | null = null
let dotXTo: ((value: number) => void) | null = null
let dotYTo: ((value: number) => void) | null = null
let reducedMotion = false
let hasPosition = false
let pointerX = 0
let pointerY = 0

function asElement(target: EventTarget | null): Element | null {
  return target instanceof Element ? target : null
}

function isNativeCursorArea(target: EventTarget | null): boolean {
  const element = asElement(target)
  return Boolean(element?.closest(NATIVE_CURSOR_SELECTOR))
}

function isHoverArea(target: EventTarget | null): boolean {
  const element = asElement(target)
  if (!element || isNativeCursorArea(element)) return false
  if (element.closest('[data-cursor="default"]')) return false
  return Boolean(element.closest(HOVER_SELECTOR))
}

function setupCursorMotion() {
  if (!ring.value || !dot.value) return
  cursorContext?.revert()
  cursorContext = gsap.context(() => {
    gsap.set([ring.value, dot.value], { xPercent: -50, yPercent: -50, x: 0, y: 0 })
    ringXTo = gsap.quickTo(ring.value!, 'x', { duration: 0.18, ease: 'power3.out' })
    ringYTo = gsap.quickTo(ring.value!, 'y', { duration: 0.18, ease: 'power3.out' })
    dotXTo = gsap.quickTo(dot.value!, 'x', { duration: 0, ease: 'none' })
    dotYTo = gsap.quickTo(dot.value!, 'y', { duration: 0, ease: 'none' })
  }, ring.value)
}

function writeCursorPosition() {
  if (reducedMotion) {
    gsap.set([ring.value, dot.value], { x: pointerX, y: pointerY, overwrite: 'auto' })
    return
  }
  ringXTo?.(pointerX)
  ringYTo?.(pointerY)
  dotXTo?.(pointerX)
  dotYTo?.(pointerY)
}

function setCursorVisibility(visible: boolean) {
  isVisible.value = visible
  if (!visible) {
    isHovering.value = false
    isPressed.value = false
    hasPosition = false
  }
}

function updateTargetState(target: EventTarget | null) {
  if (isNativeCursorArea(target)) {
    setCursorVisibility(false)
    return
  }

  setCursorVisibility(true)
  isHovering.value = isHoverArea(target)
}

function handlePointerMove(event: PointerEvent) {
  if (event.pointerType && event.pointerType !== 'mouse') return

  pointerX = event.clientX
  pointerY = event.clientY

  if (!hasPosition) {
    hasPosition = true
  }

  writeCursorPosition()
  updateTargetState(event.target)
}

function handlePointerOver(event: PointerEvent) {
  if (event.pointerType && event.pointerType !== 'mouse') return
  if (isNativeCursorArea(event.target)) {
    setCursorVisibility(false)
    return
  }

  isHovering.value = isHoverArea(event.target)
  if (hasPosition) setCursorVisibility(true)
}

function handlePointerOut(event: PointerEvent) {
  if (event.pointerType && event.pointerType !== 'mouse') return
  if (!event.relatedTarget) setCursorVisibility(false)
}

function handlePointerDown(event: PointerEvent) {
  if (event.pointerType && event.pointerType !== 'mouse') return
  isPressed.value = isVisible.value
}

function handlePointerUp() {
  isPressed.value = false
}

function handlePointerLeave(event: PointerEvent) {
  if (!event.relatedTarget) setCursorVisibility(false)
}

function handleWindowBlur() {
  setCursorVisibility(false)
}

function addListeners() {
  if (listenersActive) return
  listenersActive = true
  setupCursorMotion()
  document.documentElement.classList.add('alp-custom-cursor-enabled')
  document.addEventListener('pointermove', handlePointerMove, { passive: true })
  document.addEventListener('pointerover', handlePointerOver, { passive: true })
  document.addEventListener('pointerout', handlePointerOut, { passive: true })
  document.addEventListener('pointerdown', handlePointerDown, { passive: true })
  document.addEventListener('pointerup', handlePointerUp, { passive: true })
  document.addEventListener('pointercancel', handlePointerUp, { passive: true })
  document.addEventListener('pointerleave', handlePointerLeave, { passive: true })
  window.addEventListener('blur', handleWindowBlur)
}

function removeListeners() {
  if (listenersActive) {
    listenersActive = false
    document.documentElement.classList.remove('alp-custom-cursor-enabled')
    document.removeEventListener('pointermove', handlePointerMove)
    document.removeEventListener('pointerover', handlePointerOver)
    document.removeEventListener('pointerout', handlePointerOut)
    document.removeEventListener('pointerdown', handlePointerDown)
    document.removeEventListener('pointerup', handlePointerUp)
    document.removeEventListener('pointercancel', handlePointerUp)
    document.removeEventListener('pointerleave', handlePointerLeave)
    window.removeEventListener('blur', handleWindowBlur)
  }

  cursorContext?.revert()
  cursorContext = null
  ringXTo = null
  ringYTo = null
  dotXTo = null
  dotYTo = null
  hasPosition = false
  setCursorVisibility(false)
}

function handlePointerCapabilityChange(event: MediaQueryListEvent) {
  if (event.matches) addListeners()
  else removeListeners()
}

function handleReducedMotionChange(event: MediaQueryListEvent) {
  reducedMotion = event.matches
  if (reducedMotion && hasPosition) writeCursorPosition()
}

onMounted(() => {
  pointerMediaQuery = window.matchMedia('(hover: hover) and (pointer: fine)')
  reducedMotionMediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotion = reducedMotionMediaQuery.matches

  pointerMediaQuery.addEventListener('change', handlePointerCapabilityChange)
  reducedMotionMediaQuery.addEventListener('change', handleReducedMotionChange)

  if (pointerMediaQuery.matches) addListeners()
})

onBeforeUnmount(() => {
  removeListeners()
  pointerMediaQuery?.removeEventListener('change', handlePointerCapabilityChange)
  reducedMotionMediaQuery?.removeEventListener('change', handleReducedMotionChange)
})
</script>

<template>
  <div
    class="custom-cursor"
    :class="{
      'is-visible': isVisible,
      'is-hovering': isHovering,
      'is-pressed': isPressed,
    }"
    aria-hidden="true"
  >
    <span ref="ring" class="custom-cursor__ring">
      <span class="custom-cursor__ring-shape" />
    </span>
    <span ref="dot" class="custom-cursor__dot">
      <span class="custom-cursor__dot-shape" />
    </span>
  </div>
</template>

<style>
.custom-cursor {
  --alp-cursor-size: 30px;
  position: fixed;
  inset: 0 auto auto 0;
  z-index: 2147483647;
  width: 0;
  height: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.14s ease;
}

.custom-cursor.is-visible {
  opacity: 1;
}

.custom-cursor__ring,
.custom-cursor__dot {
  position: fixed;
  top: 0;
  left: 0;
  pointer-events: none;
  transform: translate3d(0, 0, 0);
  will-change: transform;
}

.custom-cursor__ring {
  width: var(--alp-cursor-size);
  height: var(--alp-cursor-size);
}

.custom-cursor__dot {
  width: 6px;
  height: 6px;
}

.custom-cursor__ring-shape,
.custom-cursor__dot-shape {
  display: block;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  border-radius: 50%;
  background: transparent;
}

.custom-cursor__ring-shape {
  border: 1px solid var(--alp-cursor-color);
  transition: transform 0.28s var(--alp-ease-out-expo);
}

.custom-cursor__dot-shape {
  background: var(--alp-cursor-color);
  transition:
    opacity 0.22s var(--alp-ease-out-expo),
    transform 0.22s var(--alp-ease-out-expo);
}

.custom-cursor.is-hovering .custom-cursor__ring-shape {
  transform: scale(2.6667);
}

.custom-cursor.is-hovering .custom-cursor__dot-shape {
  opacity: 0;
  transform: scale(0);
}

.custom-cursor.is-pressed .custom-cursor__ring-shape {
  transform: scale(0.8667);
}

.custom-cursor.is-hovering.is-pressed .custom-cursor__ring-shape {
  transform: scale(2.4);
}

@media (hover: none), (pointer: coarse) {
  .custom-cursor {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .custom-cursor,
  .custom-cursor__ring-shape,
  .custom-cursor__dot-shape {
    transition-duration: 0.01s;
  }
}
</style>
