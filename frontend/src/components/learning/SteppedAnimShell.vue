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
  <figure class="step-anim" role="img" :aria-label="caption">
    <figcaption class="step-anim-caption">{{ caption }}</figcaption>

    <div v-if="useStepped" class="anim-toolbar" role="group" aria-label="演示控制">
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
      v-if="useStepped && stepHint"
      class="step-desc"
      :class="{ 'step-desc--pulse': hintPulse }"
      aria-live="polite"
    >{{ stepHint }}</p>

    <div class="anim-viz-stage lv-viz-stable">
      <slot />
    </div>
  </figure>
</template>
