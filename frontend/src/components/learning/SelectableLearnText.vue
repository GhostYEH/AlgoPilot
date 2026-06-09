<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, unref, watch } from 'vue'
import { ChatLineRound } from '@element-plus/icons-vue'
import { formatSelectionQuestion, useAiTutorBridge } from '@/composables/aiTutorBridge'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    /** 划词最少字符数 */
    minLength?: number
    /** 划词最多字符数 */
    maxLength?: number
    /** 小节切换时收起浮层 */
    sectionId?: string
  }>(),
  { minLength: 2, maxLength: 400 },
)

const rootRef = ref<HTMLElement | null>(null)
const bridge = useAiTutorBridge()
const tutorLoading = computed(() => (bridge ? unref(bridge.loading) : false))

const popover = ref({
  visible: false,
  top: 0,
  left: 0,
  text: '',
})

let hideTimer: ReturnType<typeof setTimeout> | null = null

function clearHideTimer() {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
}

function hidePopover() {
  popover.value.visible = false
  popover.value.text = ''
}

watch(
  () => props.sectionId,
  () => hidePopover(),
)

function scheduleHide() {
  clearHideTimer()
  hideTimer = setTimeout(hidePopover, 120)
}

function isExcludedNode(node: Node | null): boolean {
  if (!node) return true
  const el =
    node.nodeType === Node.ELEMENT_NODE
      ? (node as Element)
      : node.parentElement
  if (!el) return true
  return !!el.closest(
    'button, a, input, textarea, select, .el-button, .el-switch, .el-link, .ai-tutor-aside, .selection-ask-popover, pre.code-sketch, .inline-oj, .oj-body',
  )
}

function getSelectionInRoot(): string | null {
  const root = rootRef.value
  const sel = window.getSelection()
  if (!root || !sel || sel.isCollapsed || sel.rangeCount === 0) return null

  const range = sel.getRangeAt(0)
  if (isExcludedNode(range.commonAncestorContainer)) return null
  if (!root.contains(range.commonAncestorContainer)) return null

  const text = sel.toString().replace(/\s+/g, ' ').trim()
  if (text.length < props.minLength || text.length > props.maxLength) return null
  return text
}

function placePopover(text: string, range: Range) {
  const rect = range.getBoundingClientRect()
  if (!rect.width && !rect.height) return

  const pad = 8
  const cardW = 132
  let left = rect.left + rect.width / 2 - cardW / 2
  left = Math.max(pad, Math.min(left, window.innerWidth - cardW - pad))

  let top = rect.top - 44
  if (top < pad) top = rect.bottom + 8

  popover.value = { visible: true, top, left, text }
}

function onMouseUp() {
  clearHideTimer()
  requestAnimationFrame(() => {
    const root = rootRef.value
    const sel = window.getSelection()
    if (!root || !sel || sel.rangeCount === 0) {
      hidePopover()
      return
    }

    const text = getSelectionInRoot()
    if (!text) {
      if (!popover.value.visible) hidePopover()
      return
    }

    placePopover(text, sel.getRangeAt(0))
  })
}

function onDocumentMouseDown(e: MouseEvent) {
  const t = e.target as Node
  if (t instanceof Element && t.closest('.selection-ask-popover')) return
  scheduleHide()
}

function onScroll() {
  hidePopover()
}

function onAsk() {
  if (!bridge) {
    console.warn('[SelectableLearnText] bridge is null, cannot ask')
    hidePopover()
    return
  }
  if (!popover.value.text || unref(bridge.loading)) {
    console.warn('[SelectableLearnText] onAsk early return', { text: popover.value.text, loading: unref(bridge.loading) })
    return
  }
  const q = formatSelectionQuestion(popover.value.text)
  console.log('[SelectableLearnText] asking:', q)
  bridge.ask(q)
  hidePopover()
  window.getSelection()?.removeAllRanges()
}

function onPopoverEnter() {
  clearHideTimer()
}

function onPopoverLeave() {
  scheduleHide()
}

onMounted(() => {
  document.addEventListener('mousedown', onDocumentMouseDown)
  window.addEventListener('scroll', onScroll, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocumentMouseDown)
  window.removeEventListener('scroll', onScroll, true)
  clearHideTimer()
})
</script>

<template>
  <div ref="rootRef" class="selectable-learn-text" v-bind="$attrs" @mouseup="onMouseUp">
    <slot />
  </div>

  <Teleport to="body">
    <Transition name="selection-ask-fade">
      <div
        v-if="popover.visible"
        class="selection-ask-popover"
        :style="{ top: `${popover.top}px`, left: `${popover.left}px` }"
        role="toolbar"
        aria-label="划词提问"
        @mouseenter="onPopoverEnter"
        @mouseleave="onPopoverLeave"
      >
        <button
          type="button"
          class="selection-ask-btn"
          :disabled="!bridge || tutorLoading"
          @mousedown.prevent
          @click="onAsk"
        >
          <el-icon><ChatLineRound /></el-icon>
          {{ tutorLoading ? '思考中…' : '问一问' }}
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.selectable-learn-text {
  user-select: text;
  -webkit-user-select: text;
}

.selectable-learn-text :deep(::selection) {
  background: rgba(56, 189, 248, 0.35);
  color: var(--alp-color-text);
}
</style>

<style>
.selection-ask-popover {
  position: fixed;
  z-index: 3500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  border-radius: 10px;
  background: var(--alp-bg-surface-solid, #151d2e);
  border: 1px solid rgba(56, 189, 248, 0.45);
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.45),
    0 0 0 1px rgba(56, 189, 248, 0.12);
  pointer-events: auto;
}

.selection-ask-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-primary, #38bdf8);
  background: var(--alp-color-primary-soft, rgba(56, 189, 248, 0.16));
  border: none;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition:
    background 0.15s ease,
    color 0.15s ease;
}

.selection-ask-btn:hover:not(:disabled) {
  background: rgba(56, 189, 248, 0.28);
  color: #e0f2fe;
}

.selection-ask-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.selection-ask-fade-enter-active,
.selection-ask-fade-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

.selection-ask-fade-enter-from,
.selection-ask-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
