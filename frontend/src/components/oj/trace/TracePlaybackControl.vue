<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  DArrowLeft,
  DArrowRight,
  VideoPause,
  VideoPlay,
  RefreshRight,
  Warning,
} from '@element-plus/icons-vue'
import {
  TRACE_PLAYBACK_SPEEDS,
  type TracePlaybackSpeed,
} from '@/composables/useCodeTracePlayback'

const props = defineProps<{
  frame: number
  maxFrame: number
  playing: boolean
  playbackSpeed: TracePlaybackSpeed
  bugStepIndex: number | null
  splitMode?: boolean
  hasTrace: boolean
}>()

const emit = defineEmits<{
  togglePlay: []
  next: []
  prev: []
  reset: []
  jumpToFrame: [index: number]
  setPlaybackSpeed: [speed: TracePlaybackSpeed]
}>()

const sliderValue = computed({
  get: () => props.frame,
  set: (v: number) => emit('jumpToFrame', v),
})

const bugMarkerLeft = computed(() => {
  if (props.bugStepIndex == null || props.maxFrame <= 0) return null
  return `${(props.bugStepIndex / props.maxFrame) * 100}%`
})

const isOnBugFrame = computed(
  () => props.bugStepIndex !== null && props.frame === props.bugStepIndex,
)

const dragging = ref(false)

function onSliderChange(val: number | number[]) {
  const n = Array.isArray(val) ? val[0] : val
  if (typeof n === 'number') emit('jumpToFrame', n)
}

function jumpToBugStep() {
  if (props.bugStepIndex != null) {
    emit('jumpToFrame', props.bugStepIndex)
  }
}

watch(
  () => props.frame,
  () => {
    dragging.value = false
  },
)
</script>

<template>
  <div
    v-if="hasTrace"
    class="trace-playback-control"
    :class="{ 'trace-playback-control--split': splitMode, 'trace-playback-control--bug-active': isOnBugFrame }"
    role="group"
    aria-label="时间旅行调试"
  >
    <div class="tpc-row">
      <el-button-group size="small">
        <el-button :icon="playing ? VideoPause : VideoPlay" @click="emit('togglePlay')">
          {{ playing ? '暂停' : '播放' }}
        </el-button>
        <el-button :icon="DArrowLeft" @click="emit('prev')">上一步</el-button>
        <el-button :icon="DArrowRight" @click="emit('next')">下一步</el-button>
        <el-button :icon="RefreshRight" @click="emit('reset')">重置</el-button>
      </el-button-group>

      <div class="tpc-speed">
        <span class="tpc-speed-label">速度</span>
        <el-radio-group
          :model-value="playbackSpeed"
          size="small"
          @update:model-value="emit('setPlaybackSpeed', $event as TracePlaybackSpeed)"
        >
          <el-radio-button
            v-for="s in TRACE_PLAYBACK_SPEEDS"
            :key="s"
            :value="s"
          >
            {{ s }}×
          </el-radio-button>
        </el-radio-group>
      </div>

      <span class="tpc-step-meta">
        步 <strong class="tpc-step-current">{{ frame + 1 }}</strong> / {{ maxFrame + 1 }}
      </span>

      <el-button
        v-if="bugStepIndex != null"
        size="small"
        type="danger"
        plain
        :icon="Warning"
        class="tpc-bug-jump"
        @click="jumpToBugStep"
      >
        跳转到错误步 #{{ bugStepIndex + 1 }}
      </el-button>
    </div>

    <div class="tpc-slider-row">
      <div class="tpc-slider-wrap">
        <el-slider
          v-model="sliderValue"
          :min="0"
          :max="maxFrame"
          :step="1"
          :show-tooltip="false"
          size="small"
          class="tpc-slider"
          @change="onSliderChange"
        />
        <span
          v-if="bugMarkerLeft != null"
          class="tpc-bug-marker"
          :style="{ left: bugMarkerLeft }"
          :title="`AI 诊断错误步骤 #${bugStepIndex! + 1}`"
          @click.stop="jumpToBugStep"
        />
      </div>
    </div>
  </div>

  <div v-else class="tpc-empty">
    <span class="tpc-empty-text">暂无执行轨迹，请先运行可视化调试</span>
  </div>
</template>

<style scoped>
.trace-playback-control {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  padding: 10px 12px 8px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.trace-playback-control--split {
  flex-shrink: 0;
  margin-top: 8px;
  position: sticky;
  bottom: 0;
  z-index: 2;
  background: var(--alp-bg-surface-solid);
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.12);
}

.trace-playback-control--bug-active {
  border-color: color-mix(in srgb, var(--el-color-danger) 50%, var(--alp-color-border));
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-danger) 18%, transparent);
}

.tpc-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 14px;
}

.tpc-speed {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tpc-speed-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.tpc-step-meta {
  font-size: 12px;
  color: var(--el-text-color-regular);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.tpc-step-current {
  color: var(--el-color-primary);
  font-size: 14px;
}

.tpc-bug-jump {
  margin-left: auto;
  border-color: color-mix(in srgb, var(--el-color-danger) 55%, transparent) !important;
  background: color-mix(in srgb, var(--el-color-danger) 12%, transparent) !important;
}

.tpc-slider-row {
  display: flex;
  align-items: center;
  padding: 0 2px;
}

.tpc-slider-wrap {
  position: relative;
  flex: 1;
  min-width: 0;
}

.tpc-slider {
  width: 100%;
}

.tpc-slider :deep(.el-slider__runway) {
  height: 6px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--el-color-primary) 12%, var(--el-fill-color-light));
}

.tpc-slider :deep(.el-slider__bar) {
  height: 6px;
  border-radius: 3px;
}

.tpc-slider :deep(.el-slider__button-wrapper) {
  top: -16px;
}

.tpc-slider :deep(.el-slider__button) {
  width: 14px;
  height: 14px;
  border: 2px solid var(--el-color-primary);
}

.tpc-bug-marker {
  position: absolute;
  top: 50%;
  width: 10px;
  height: 10px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: var(--el-color-danger);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-danger) 30%, transparent),
    0 0 8px color-mix(in srgb, var(--el-color-danger) 50%, transparent);
  cursor: pointer;
  z-index: 1;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  animation: tpc-bug-pulse 2s ease-in-out infinite;
}

.tpc-bug-marker:hover {
  transform: translate(-50%, -50%) scale(1.4);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-danger) 40%, transparent),
    0 0 12px color-mix(in srgb, var(--el-color-danger) 60%, transparent);
}

@keyframes tpc-bug-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-danger) 30%, transparent),
      0 0 8px color-mix(in srgb, var(--el-color-danger) 50%, transparent);
  }
  50% {
    box-shadow: 0 0 0 4px color-mix(in srgb, var(--el-color-danger) 20%, transparent),
      0 0 14px color-mix(in srgb, var(--el-color-danger) 60%, transparent);
  }
}

.tpc-empty {
  margin-top: 12px;
  padding: 16px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px dashed var(--alp-color-border);
  text-align: center;
}

.tpc-empty-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

@media (max-width: 720px) {
  .tpc-bug-jump {
    margin-left: 0;
    width: 100%;
  }
}
</style>
