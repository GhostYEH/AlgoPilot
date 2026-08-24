<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

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
let animationFrame: number | null = null
let reducedMotion = false
let hasPosition = false
let pointerX = 0
let pointerY = 0
let ringX = 0
let ringY = 0

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

function writePosition(element: HTMLElement | null, x: number, y: number) {
  if (!element) return
  element.style.setProperty('--alp-cursor-x', `${x}px`)
  element.style.setProperty('--alp-cursor-y', `${y}px`)
}

function animateRing() {
  animationFrame = null
  if (!isVisible.value) return

  const easing = reducedMotion ? 1 : 0.24
  ringX += (pointerX - ringX) * easing
  ringY += (pointerY - ringY) * easing
  writePosition(ring.value, ringX, ringY)

  const distance = Math.max(Math.abs(pointerX - ringX), Math.abs(pointerY - ringY))
  if (distance > 0.1) {
    animationFrame = window.requestAnimationFrame(animateRing)
  }
}

function startRingAnimation() {
  if (animationFrame === null) {
    animationFrame = window.requestAnimationFrame(animateRing)
  }
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
    ringX = pointerX
    ringY = pointerY
    hasPosition = true
    writePosition(ring.value, ringX, ringY)
  }

  writePosition(dot.value, pointerX, pointerY)
  updateTargetState(event.target)
  startRingAnimation()
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
  if (!listenersActive) return
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

  if (animationFrame !== null) {
    window.cancelAnimationFrame(animationFrame)
    animationFrame = null
  }
  hasPosition = false
  setCursorVisibility(false)
}

function handlePointerCapabilityChange(event: MediaQueryListEvent) {
  if (event.matches) addListeners()
  else removeListeners()
}

function handleReducedMotionChange(event: MediaQueryListEvent) {
  reducedMotion = event.matches
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
  transform: translate3d(var(--alp-cursor-x, 0px), var(--alp-cursor-y, 0px), 0)
    translate3d(-50%, -50%, 0);
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
