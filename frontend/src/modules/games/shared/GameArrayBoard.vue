<script setup lang="ts">
/**
 * 可点击数组格：支持多指针标注与高亮
 */
withDefaults(
  defineProps<{
    values: (number | string)[]
    pointers?: Record<string, number | undefined>
    activeIndex?: number
    correctIndex?: number
    wrongIndex?: number
    clickable?: boolean
  }>(),
  { pointers: () => ({}), clickable: true },
)

const emit = defineEmits<{ select: [index: number] }>()

const pointerColors: Record<string, string> = {
  L: '#3a8a9e',
  R: '#9e6e88',
  M: '#9c8540',
  slow: '#7a6e9e',
  fast: '#9e6e4a',
  i: '#3d8a7e',
  j: '#9e6470',
}
</script>

<template>
  <div class="game-array-board">
    <button
      v-for="(v, i) in values"
      :key="i"
      type="button"
      class="game-array-cell"
      :class="{
        'is-active': i === activeIndex,
        'is-correct': i === correctIndex,
        'is-wrong': i === wrongIndex,
        'is-clickable': clickable,
      }"
      :disabled="!clickable"
      @click="emit('select', i)"
    >
      <span class="cell-val">{{ v }}</span>
      <span class="cell-idx">{{ i }}</span>
      <span class="cell-ptrs">
        <span
          v-for="(idx, name) in pointers"
          v-show="idx === i"
          :key="name"
          class="ptr-badge"
          :style="{ '--ptr-color': pointerColors[name] ?? '#3a8a9e' }"
        >{{ name }}</span>
      </span>
    </button>
  </div>
</template>

<style scoped>
.game-array-board {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: flex-end;
  margin-bottom: 12px;
}

.game-array-cell {
  position: relative;
  min-width: 48px;
  min-height: 52px;
  padding: 8px 10px 6px;
  border-radius: 10px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-text);
  cursor: default;
  transition: transform 0.12s, border-color 0.12s, box-shadow 0.12s, filter var(--alp-transition-fast);
}

.game-array-cell.is-clickable {
  cursor: pointer;
}

.game-array-cell.is-clickable:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, #3a8a9e 55%, transparent);
  box-shadow: var(--alp-shadow-btn-hover);
  filter: brightness(1.08);
}

.game-array-cell.is-active {
  border-color: #3a8a9e;
  box-shadow: 0 0 0 3px color-mix(in srgb, #3a8a9e 28%, transparent);
}

.game-array-cell.is-correct {
  border-color: #4a8a5e;
  background: color-mix(in srgb, #4a8a5e 15%, transparent);
}

.game-array-cell.is-wrong {
  border-color: #9e5a5a;
  animation: shake 0.35s ease;
}

.cell-val {
  display: block;
  font-size: 16px;
  font-weight: 700;
}

.cell-idx {
  display: block;
  font-size: 10px;
  color: var(--alp-color-muted);
  margin-top: 2px;
}

.cell-ptrs {
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 2px;
}

.ptr-badge {
  padding: 1px 5px;
  font-size: 9px;
  font-weight: 700;
  border-radius: 4px;
  background: var(--ptr-color);
  color: #0f172a;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-4px);
  }
  75% {
    transform: translateX(4px);
  }
}
</style>
