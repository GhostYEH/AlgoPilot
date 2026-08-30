<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'
import { usePrefersReducedMotion } from '@/composables/usePrefersReducedMotion'

type LiquidGlassMode = 'standard' | 'polar' | 'prominent'

interface Props {
  tag?: string
  displacementScale?: number
  blurAmount?: number
  saturation?: number
  aberrationIntensity?: number
  elasticity?: number
  cornerRadius?: number | string
  padding?: string
  overLight?: boolean
  interactive?: boolean
  mode?: LiquidGlassMode
}

const props = withDefaults(defineProps<Props>(), {
  tag: 'div',
  displacementScale: 28,
  blurAmount: 18,
  saturation: 165,
  aberrationIntensity: 1.4,
  elasticity: 0.16,
  cornerRadius: 16,
  padding: '0',
  overLight: false,
  interactive: true,
  mode: 'standard',
})

const root = ref<HTMLElement | null>(null)
const mapUrl = ref('')
const filterEnabled = ref(true)
const { prefersReducedMotion } = usePrefersReducedMotion()
const uid = `alp-liquid-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`
let resizeObserver: ResizeObserver | null = null
let transparencyQuery: MediaQueryList | null = null
let resizeFrame = 0
let pointerFrame = 0
let pendingPointer: PointerEvent | null = null

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function smoothstep(edge0: number, edge1: number, value: number) {
  const x = clamp((value - edge0) / (edge1 - edge0), 0, 1)
  return x * x * (3 - 2 * x)
}

/**
 * Procedural replacement for liquid-glass-react's bundled displacement images.
 * R drives horizontal refraction and B drives vertical refraction. Keeping the
 * map small makes ResizeObserver updates cheap while SVG stretches it cleanly.
 */
function createDisplacementMap(width: number, height: number, mode: LiquidGlassMode) {
  const canvas = document.createElement('canvas')
  const longest = Math.max(width, height, 1)
  const scale = Math.min(1, 256 / longest)
  canvas.width = Math.max(48, Math.round(width * scale))
  canvas.height = Math.max(32, Math.round(height * scale))

  const context = canvas.getContext('2d')
  if (!context) return ''

  const image = context.createImageData(canvas.width, canvas.height)
  const data = image.data
  const edgeStart = mode === 'prominent' ? 0.38 : mode === 'polar' ? 0.48 : 0.58
  const strength = mode === 'prominent' ? 1 : mode === 'polar' ? 0.86 : 0.72

  for (let y = 0; y < canvas.height; y += 1) {
    for (let x = 0; x < canvas.width; x += 1) {
      const nx = (x / Math.max(1, canvas.width - 1)) * 2 - 1
      const ny = (y / Math.max(1, canvas.height - 1)) * 2 - 1
      const radial = Math.sqrt(nx * nx + ny * ny) / Math.SQRT2
      const roundedEdge = Math.max(Math.abs(nx), Math.abs(ny))
      const distance = mode === 'polar' ? radial : roundedEdge
      const edge = smoothstep(edgeStart, 1, distance) * strength
      const length = Math.max(0.0001, Math.sqrt(nx * nx + ny * ny))
      const directionX = nx / length
      const directionY = ny / length
      const offset = (y * canvas.width + x) * 4

      data[offset] = clamp(Math.round(128 + directionX * 127 * edge), 0, 255)
      data[offset + 1] = 128
      data[offset + 2] = clamp(Math.round(128 + directionY * 127 * edge), 0, 255)
      data[offset + 3] = 255
    }
  }

  context.putImageData(image, 0, 0)
  return canvas.toDataURL('image/png')
}

function updateGeometry() {
  if (!root.value || !filterEnabled.value) {
    mapUrl.value = ''
    return
  }
  const rect = root.value.getBoundingClientRect()
  if (rect.width < 1 || rect.height < 1) return
  mapUrl.value = createDisplacementMap(rect.width, rect.height, props.mode)
}

function scheduleGeometryUpdate() {
  cancelAnimationFrame(resizeFrame)
  resizeFrame = requestAnimationFrame(updateGeometry)
}

function renderPointerEffect(event: PointerEvent) {
  const el = root.value
  if (!el || !props.interactive || prefersReducedMotion.value) return

  const rect = el.getBoundingClientRect()
  const halfWidth = Math.max(1, rect.width / 2)
  const halfHeight = Math.max(1, rect.height / 2)
  const dx = event.clientX - (rect.left + halfWidth)
  const dy = event.clientY - (rect.top + halfHeight)
  const nx = clamp(dx / halfWidth, -1, 1)
  const ny = clamp(dy / halfHeight, -1, 1)
  const distance = Math.min(1, Math.sqrt(nx * nx + ny * ny))
  const pull = props.elasticity * (1 - distance * 0.28)
  const angle = 135 + nx * 42 + ny * 18

  el.style.setProperty('--lg-shift-x', `${dx * pull * 0.12}px`)
  el.style.setProperty('--lg-shift-y', `${dy * pull * 0.12}px`)
  el.style.setProperty('--lg-scale-x', `${1 + Math.abs(nx) * pull * 0.08 - Math.abs(ny) * pull * 0.035}`)
  el.style.setProperty('--lg-scale-y', `${1 + Math.abs(ny) * pull * 0.08 - Math.abs(nx) * pull * 0.035}`)
  el.style.setProperty('--lg-angle', `${angle}deg`)
  el.style.setProperty('--lg-light-x', `${50 + nx * 34}%`)
  el.style.setProperty('--lg-light-y', `${18 + ny * 24}%`)
}

function onPointerMove(event: PointerEvent) {
  // Touch pointers should remain dedicated to scrolling and tapping. The
  // elastic follow effect is useful for mouse and pen input only.
  if (event.pointerType === 'touch') return
  pendingPointer = event
  if (pointerFrame) return
  pointerFrame = requestAnimationFrame(() => {
    pointerFrame = 0
    if (pendingPointer) renderPointerEffect(pendingPointer)
  })
}

function onPointerLeave() {
  pendingPointer = null
  const el = root.value
  if (!el) return
  el.style.setProperty('--lg-shift-x', '0px')
  el.style.setProperty('--lg-shift-y', '0px')
  el.style.setProperty('--lg-scale-x', '1')
  el.style.setProperty('--lg-scale-y', '1')
  el.style.setProperty('--lg-angle', '135deg')
  el.style.setProperty('--lg-light-x', '22%')
  el.style.setProperty('--lg-light-y', '0%')
}

const radiusValue = computed(() =>
  typeof props.cornerRadius === 'number' ? `${props.cornerRadius}px` : props.cornerRadius,
)

const rootStyle = computed(() => ({
  '--lg-radius': radiusValue.value,
  '--lg-padding': props.padding,
  '--lg-blur': `${props.blurAmount}px`,
  '--lg-saturation': `${props.saturation}%`,
  '--lg-displacement': props.displacementScale,
} as Record<string, string | number>))

const warpStyle = computed(() => ({
  filter: filterEnabled.value && mapUrl.value ? `url(#${uid})` : undefined,
}))

watch(() => props.mode, scheduleGeometryUpdate)

function syncFilterSupport() {
  const isFirefox = /firefox/i.test(navigator.userAgent)
  const reduceTransparency = transparencyQuery?.matches ?? false
  const supportsSvgFilter = typeof CSS === 'undefined' || CSS.supports('filter', 'url("#test")')
  filterEnabled.value = !isFirefox && !reduceTransparency && supportsSvgFilter
  scheduleGeometryUpdate()
}

onMounted(async () => {
  transparencyQuery = window.matchMedia('(prefers-reduced-transparency: reduce)')
  transparencyQuery.addEventListener('change', syncFilterSupport)
  syncFilterSupport()
  await nextTick()
  updateGeometry()
  if (root.value && 'ResizeObserver' in window) {
    resizeObserver = new ResizeObserver(scheduleGeometryUpdate)
    resizeObserver.observe(root.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  transparencyQuery?.removeEventListener('change', syncFilterSupport)
  cancelAnimationFrame(resizeFrame)
  cancelAnimationFrame(pointerFrame)
})
</script>

<template>
  <component
    :is="tag"
    ref="root"
    class="liquid-glass"
    :class="{
      'liquid-glass--interactive': interactive,
      'liquid-glass--over-light': overLight,
      'liquid-glass--fallback': !filterEnabled,
    }"
    :style="rootStyle"
    :type="tag === 'button' ? 'button' : undefined"
    @pointermove="onPointerMove"
    @pointerleave="onPointerLeave"
  >
    <svg class="liquid-glass__filter" aria-hidden="true" focusable="false">
      <defs>
        <filter :id="uid" x="-30%" y="-30%" width="160%" height="160%" color-interpolation-filters="sRGB">
          <feImage
            v-if="mapUrl"
            x="0"
            y="0"
            width="100%"
            height="100%"
            :href="mapUrl"
            preserveAspectRatio="none"
            result="displacement-map"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="displacement-map"
            :scale="displacementScale"
            xChannelSelector="R"
            yChannelSelector="B"
            result="red-shift"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="displacement-map"
            :scale="displacementScale - aberrationIntensity * 1.8"
            xChannelSelector="R"
            yChannelSelector="B"
            result="green-shift"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="displacement-map"
            :scale="displacementScale - aberrationIntensity * 3.6"
            xChannelSelector="R"
            yChannelSelector="B"
            result="blue-shift"
          />
          <feColorMatrix in="red-shift" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="red" />
          <feColorMatrix in="green-shift" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="green" />
          <feColorMatrix in="blue-shift" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="blue" />
          <feBlend in="green" in2="blue" mode="screen" result="green-blue" />
          <feBlend in="red" in2="green-blue" mode="screen" />
        </filter>
      </defs>
    </svg>
    <span class="liquid-glass__warp" :style="warpStyle" aria-hidden="true" />
    <span class="liquid-glass__tint" aria-hidden="true" />
    <span class="liquid-glass__shine" aria-hidden="true" />
    <span class="liquid-glass__content"><slot /></span>
  </component>
</template>

<style scoped>
.liquid-glass {
  --lg-shift-x: 0px;
  --lg-shift-y: 0px;
  --lg-scale-x: 1;
  --lg-scale-y: 1;
  --lg-angle: 135deg;
  --lg-light-x: 22%;
  --lg-light-y: 0%;
  position: relative;
  isolation: isolate;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding: var(--lg-padding);
  overflow: hidden;
  border: 1px solid var(--alp-liquid-border, rgba(255, 255, 255, 0.28));
  border-radius: var(--lg-radius);
  background: transparent;
  color: inherit;
  box-shadow: var(--alp-liquid-shadow);
  transform: translate3d(var(--lg-shift-x), var(--lg-shift-y), 0) scaleX(var(--lg-scale-x)) scaleY(var(--lg-scale-y));
  transform-origin: center;
  transition:
    transform 220ms var(--alp-ease-out-expo),
    box-shadow 220ms ease,
    border-color 220ms ease;
}

.liquid-glass--interactive {
  cursor: pointer;
  touch-action: manipulation;
}

.liquid-glass--interactive:hover {
  border-color: var(--alp-liquid-border-hover, rgba(255, 255, 255, 0.46));
  box-shadow: var(--alp-liquid-shadow-hover);
}

.liquid-glass--interactive:active {
  transform: translate3d(var(--lg-shift-x), calc(var(--lg-shift-y) + 1px), 0) scale(0.97);
}

.liquid-glass__filter {
  position: absolute;
  width: 0;
  height: 0;
  pointer-events: none;
}

.liquid-glass__warp,
.liquid-glass__tint,
.liquid-glass__shine {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

.liquid-glass__warp {
  z-index: -3;
  backdrop-filter: blur(var(--lg-blur)) saturate(var(--lg-saturation)) contrast(1.04);
  -webkit-backdrop-filter: blur(var(--lg-blur)) saturate(var(--lg-saturation)) contrast(1.04);
}

.liquid-glass__tint {
  z-index: -2;
  background: var(--alp-liquid-fill);
}

.liquid-glass__shine {
  z-index: -1;
  inset: 1px;
  background:
    radial-gradient(circle at var(--lg-light-x) var(--lg-light-y), rgba(255, 255, 255, 0.52), transparent 34%),
    linear-gradient(var(--lg-angle), rgba(255, 255, 255, 0.24), transparent 38%, rgba(255, 255, 255, 0.09) 74%, transparent);
  mix-blend-mode: screen;
  opacity: 0.68;
}

.liquid-glass__content {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.liquid-glass--over-light .liquid-glass__tint {
  background: var(--alp-liquid-fill-over-light);
}

.liquid-glass--fallback .liquid-glass__warp {
  filter: none !important;
}

@media (prefers-reduced-motion: reduce) {
  .liquid-glass {
    transform: none !important;
    transition: none !important;
  }
}

@media (prefers-reduced-transparency: reduce) {
  .liquid-glass__warp {
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }

  .liquid-glass__tint {
    background: var(--alp-liquid-solid-fallback);
  }
}
</style>
