<script setup lang="ts">
import { DArrowRight, RefreshRight, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { ref, watch } from 'vue'
import { usePrefersReducedMotion } from '@/composables/usePrefersReducedMotion'

const props = defineProps<{
  caption: string
  useStepped: boolean
  stepHint?: string
  step: number
  maxStep: number
  playing: boolean
  /** OJ 分屏：隐藏顶部工具条，由底部统一控制 */
  hideToolbar?: boolean
  /** 分屏：步骤说明并入紧凑顶栏 */
  compactHint?: boolean
}>()

const emit = defineEmits<{
  togglePlay: []
  next: []
  reset: []
}>()

const { prefersReducedMotion } = usePrefersReducedMotion()
const hintPulse = ref(false)
let hintPulseTimer: ReturnType<typeof setTimeout> | null = null

watch(
  () => props.step,
  () => {
    if (prefersReducedMotion.value) return
    hintPulse.value = false
    if (hintPulseTimer) clearTimeout(hintPulseTimer)
    requestAnimationFrame(() => {
      hintPulse.value = true
      hintPulseTimer = setTimeout(() => {
        hintPulse.value = false
      }, 560)
    })
  },
)
</script>

<template>
  <figure
    class="step-anim"
    :class="{ 'step-anim--compact': compactHint }"
    role="img"
    :aria-label="caption"
  >
    <figcaption v-if="!compactHint" class="step-anim-caption">{{ caption }}</figcaption>
    <div v-else-if="caption" class="step-anim-caption step-anim-caption--inline">{{ caption }}</div>

    <div
      v-if="useStepped && !hideToolbar"
      class="anim-toolbar"
      role="group"
      aria-label="演示控制"
    >
      <el-button-group size="small">
        <el-button :icon="playing ? VideoPause : VideoPlay" @click="emit('togglePlay')">
          {{ playing ? '暂停' : prefersReducedMotion ? '步进' : '播放' }}
        </el-button>
        <el-button :icon="DArrowRight" @click="emit('next')">下一步</el-button>
        <el-button :icon="RefreshRight" @click="emit('reset')">重置</el-button>
      </el-button-group>
      <span class="anim-toolbar-meta">帧 {{ step + 1 }} / {{ maxStep + 1 }}</span>
    </div>
    <p
      v-if="useStepped && stepHint && !compactHint"
      class="step-desc"
      :class="{ 'step-desc--pulse': hintPulse }"
      aria-live="polite"
    >{{ stepHint }}</p>

    <div class="anim-viz-stage lv-viz-stable" :class="{ 'anim-viz-stage--fill': compactHint }">
      <slot />
    </div>
  </figure>
</template>

<style scoped>
.step-anim--compact {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
  margin: 0;
  width: 100%;
}

.step-anim-caption--inline {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  text-align: left;
}

.anim-viz-stage--fill {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
</style>
