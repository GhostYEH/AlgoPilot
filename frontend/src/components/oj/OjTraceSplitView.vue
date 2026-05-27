<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import { nextTick, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import { usePrefersReducedMotion } from '@/composables/usePrefersReducedMotion'
import { traceHighlightLineKey } from '@/composables/useTraceHighlight'
import CodeTracePanel from '@/components/oj/CodeTracePanel.vue'
import type { TraceResponse } from '@/types/codeTrace'

const props = defineProps<{
  open: boolean
  userCode: string
  trace: TraceResponse | null
  tracing?: boolean
  narrating?: boolean
  visualTraceDiagnosing?: boolean
  slug?: string
  problemDescription?: string
  language?: 'python' | 'cpp'
  judgeVerdict?: string | null
  bugDiagnosis?: import('@/types/codeTrace').TraceBugDiagnoseResponse | null
}>()

const emit = defineEmits<{ close: []; narrate: [] }>()

const traceHighlightLine = ref(0)
provide(traceHighlightLineKey, traceHighlightLine)

const { prefersReducedMotion } = usePrefersReducedMotion()
const paneReady = ref(false)

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      paneReady.value = false
      return
    }
    paneReady.value = false
    await nextTick()
    if (prefersReducedMotion.value) {
      paneReady.value = true
      return
    }
    requestAnimationFrame(() => {
      paneReady.value = true
    })
  },
  { immediate: true },
)

onMounted(() => {
  if (props.open && !prefersReducedMotion.value) {
    requestAnimationFrame(() => {
      paneReady.value = true
    })
  }
})

watch(
  () => props.open,
  (open) => {
    if (typeof document === 'undefined') return
    document.body.style.overflow = open ? 'hidden' : ''
  },
  { immediate: true },
)

onUnmounted(() => {
  if (typeof document !== 'undefined') document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="oj-trace-backdrop">
      <div
        v-if="open"
        class="oj-trace-backdrop"
        aria-hidden="true"
        @click="emit('close')"
      />
    </Transition>

    <Transition name="oj-trace-shell">
      <div
        v-if="open"
        class="oj-trace-split"
        :class="{ 'oj-trace-split--ready': paneReady }"
        role="dialog"
        aria-modal="true"
        aria-label="可视化调试"
      >
        <div class="oj-trace-split__left">
          <slot />
        </div>

        <div
          class="oj-trace-split__right"
          :class="{ 'oj-trace-split__right--ready': paneReady }"
        >
          <header class="oj-trace-split__head">
            <div class="oj-trace-split__head-text">
              <h2 class="oj-trace-split__title">可视化调试</h2>
              <p class="oj-trace-split__subtitle">左侧编辑代码，右侧查看数据结构变化</p>
            </div>
            <el-button
              type="primary"
              plain
              size="small"
              :icon="Close"
              @click="emit('close')"
            >
              退出调试
            </el-button>
          </header>

          <div class="oj-trace-split__viz">
            <CodeTracePanel
              split-mode
              :trace="trace"
              :user-code="userCode"
              :trace-source-code="userCode"
              :loading="tracing || visualTraceDiagnosing"
              :narrating="narrating"
              :slug="slug"
              :problem-description="problemDescription"
              :language="language"
              :judge-verdict="judgeVerdict"
              :bug-diagnosis="bugDiagnosis"
              @narrate="emit('narrate')"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.oj-trace-backdrop {
  position: fixed;
  inset: var(--alp-header-height, 60px) 0 0 0;
  z-index: 180;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(2px);
}

.oj-trace-split {
  position: fixed;
  inset: var(--alp-header-height, 60px) 0 0 0;
  z-index: 190;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  width: 100%;
  max-width: 100vw;
  overflow: hidden;
  background: var(--alp-bg-surface);
  box-shadow: 0 -8px 40px rgba(15, 23, 42, 0.12);
}

.oj-trace-split__left {
  flex: 1 1 50%;
  min-width: 0;
  max-width: 50%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--alp-color-border);
  transform: translateX(12%);
  opacity: 0.88;
  transition:
    transform 0.5s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.42s ease,
    max-width 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}

.oj-trace-split--ready .oj-trace-split__left {
  transform: translateX(0);
  opacity: 1;
}

.oj-trace-split__right {
  flex: 0 0 0;
  min-width: 0;
  max-width: 0;
  opacity: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--alp-bg-surface-muted);
  transition:
    flex 0.5s cubic-bezier(0.22, 1, 0.36, 1),
    max-width 0.5s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.38s ease;
}

.oj-trace-split__right--ready {
  flex: 1 1 50%;
  max-width: 50%;
  opacity: 1;
}

.oj-trace-split__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--alp-color-border);
  flex-shrink: 0;
}

.oj-trace-split__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.oj-trace-split__subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.oj-trace-split__viz {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 0 12px 12px;
}

.oj-trace-split__viz :deep(.code-trace-panel) {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px 0 4px;
  box-sizing: border-box;
}

.oj-trace-split__viz :deep(.step-anim) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.oj-trace-split__viz :deep(.anim-viz-stage) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.oj-trace-split__viz :deep(.trace-narration) {
  flex-shrink: 0;
  margin-bottom: 6px;
}

.oj-trace-split__viz :deep(.trace-layout--split) {
  flex: 1;
  min-height: 0;
}

.oj-trace-split__viz :deep(.trace-ai-diagnosis-card) {
  flex-shrink: 0;
  margin-top: 8px;
}

.oj-trace-backdrop-enter-active,
.oj-trace-backdrop-leave-active {
  transition: opacity 0.32s ease;
}

.oj-trace-backdrop-enter-from,
.oj-trace-backdrop-leave-to {
  opacity: 0;
}

.oj-trace-shell-enter-active {
  transition: opacity 0.28s ease;
}

.oj-trace-shell-leave-active {
  transition: opacity 0.22s ease;
}

.oj-trace-shell-enter-from,
.oj-trace-shell-leave-to {
  opacity: 0;
}

.oj-trace-shell-leave-active .oj-trace-split__left {
  transition:
    transform 0.32s ease,
    opacity 0.28s ease;
  transform: translateX(6%);
}

.oj-trace-shell-leave-active .oj-trace-split__right {
  transition:
    flex 0.32s ease,
    max-width 0.32s ease,
    opacity 0.25s ease;
}

@media (max-width: 900px) {
  .oj-trace-split {
    flex-direction: column;
  }

  .oj-trace-split__left {
    max-width: none;
    flex: 0 0 45%;
    max-height: 45%;
    border-right: none;
    border-bottom: 1px solid var(--alp-color-border);
  }

  .oj-trace-split__right--ready {
    max-width: none;
    flex: 1 1 55%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .oj-trace-split__left,
  .oj-trace-split__right {
    transition: none !important;
    transform: none !important;
    opacity: 1 !important;
  }

  .oj-trace-split__right--ready {
    flex: 1 1 50%;
    max-width: 50%;
  }
}
</style>
