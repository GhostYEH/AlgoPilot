<script setup lang="ts">
import { computed } from 'vue'
import type { StackScene } from '@/utils/traceStack'

const props = defineProps<{
  scene: StackScene
  changed: Set<string>
}>()

/** 展示：栈顶在上（items 数组为栈底→栈顶） */
const cellsTopFirst = computed(() => [...props.scene.items].reverse())
</script>

<template>
  <div class="ts-trace">
    <header class="ts-head">
      <span class="ts-tag">栈 {{ scene.name }}</span>
      <span class="ts-badge">LIFO · 后进先出</span>
      <span v-if="scene.isValid != null" class="ts-badge" :class="scene.isValid ? 'ts-badge--ok' : 'ts-badge--bad'">
        is_valid = {{ scene.isValid }}
      </span>
    </header>

    <div v-if="scene.inputString != null" class="ts-input">
      <span class="ts-input-label">输入 s</span>
      <code class="ts-input-val">{{ scene.inputString === '' ? '""' : scene.inputString }}</code>
    </div>

    <div v-if="scene.currentChar != null" class="ts-cursor">
      <span class="ts-cursor-label">当前字符 c</span>
      <code class="ts-cursor-val">{{ scene.currentChar }}</code>
    </div>

    <div class="ts-stack-wrap">
      <span class="ts-cap ts-cap--top">栈顶 ↑</span>
      <div class="ts-stack-lane" :class="{ 'ts-stack-lane--hot': changed.has(scene.name) }">
        <template v-if="cellsTopFirst.length">
          <span
            v-for="(cell, i) in cellsTopFirst"
            :key="i + '-' + cell"
            class="ts-cell"
            :class="{
              'ts-cell--top': i === 0,
              'ts-cell--hot': changed.has(scene.name) && i === 0,
            }"
          >{{ cell }}</span>
        </template>
        <span v-else class="ts-empty">（空栈）</span>
      </div>
      <span class="ts-cap ts-cap--bottom">栈底</span>
    </div>

    <p v-if="!cellsTopFirst.length" class="ts-hint">
      <template v-if="scene.currentChar === '('">
        当前字符为「(」，下一步 push 后栈内会出现该元素。
      </template>
      <template v-else-if="scene.currentChar === ')'">
        当前字符为「)」，若栈非空将执行 pop。
      </template>
      <template v-else>
        当前步栈为空；执行 push 后此处会显示栈内元素（栈顶在上方高亮）。
      </template>
    </p>
  </div>
</template>

<style scoped>
.ts-trace {
  margin-bottom: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, #f59e0b 35%, var(--alp-color-border));
  background: linear-gradient(
    165deg,
    var(--alp-bg-surface) 0%,
    color-mix(in srgb, #f59e0b 8%, var(--alp-bg-soft-block)) 100%
  );
  box-shadow: var(--alp-shadow-card);
}

.ts-head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.ts-tag {
  font-size: 12px;
  font-weight: 700;
  color: #f59e0b;
}

.ts-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, #f59e0b 14%, transparent);
  color: var(--alp-color-muted);
}

.ts-badge--ok {
  color: #4ade80;
}

.ts-badge--bad {
  color: #f87171;
}

.ts-input {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px dashed var(--alp-color-border);
}

.ts-input-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.ts-input-val {
  font-size: 15px;
  font-weight: 600;
  font-family: ui-monospace, Consolas, monospace;
}

.ts-cursor {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding: 6px 10px;
  border-radius: 8px;
  background: color-mix(in srgb, #22d3ee 10%, var(--alp-bg-soft-block));
  border: 1px solid color-mix(in srgb, #22d3ee 35%, var(--alp-color-border));
}

.ts-cursor-label {
  font-size: 12px;
  font-weight: 600;
  color: #22d3ee;
}

.ts-cursor-val {
  font-size: 18px;
  font-weight: 700;
  font-family: ui-monospace, Consolas, monospace;
}

.ts-stack-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.ts-cap {
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.ts-stack-lane {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
  min-width: 72px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.ts-stack-lane--hot {
  border-color: #f59e0b;
}

.ts-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 6px 16px;
  border-radius: 8px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  font-size: 18px;
  font-weight: 700;
  font-family: ui-monospace, Consolas, monospace;
}

.ts-cell--top {
  border-color: #f59e0b;
  background: color-mix(in srgb, #f59e0b 16%, var(--alp-bg-surface));
  box-shadow: 0 0 0 2px color-mix(in srgb, #f59e0b 25%, transparent);
}

.ts-cell--hot {
  animation: ts-pulse 0.55s ease;
}

.ts-empty {
  text-align: center;
  font-size: 13px;
  color: var(--alp-color-muted);
  font-style: italic;
  padding: 12px 0;
}

.ts-hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  text-align: center;
}

@keyframes ts-pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}
</style>
