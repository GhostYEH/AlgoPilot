<script setup lang="ts">
export interface GameTool {
  id: string
  label: string
  hint?: string
  disabled?: boolean
}

defineProps<{
  tools: GameTool[]
  activeId: string | null
}>()

const emit = defineEmits<{ select: [id: string] }>()
</script>

<template>
  <div class="tool-palette">
    <span class="palette-label">当前工具</span>
    <div class="tool-btns">
      <button
        v-for="t in tools"
        :key="t.id"
        type="button"
        class="tool-btn"
        :class="{ 'is-active': activeId === t.id, 'is-disabled': t.disabled }"
        :disabled="t.disabled"
        :title="t.hint"
        @click="emit('select', t.id)"
      >
        {{ t.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.tool-palette {
  margin-bottom: 12px;
}

.palette-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.tool-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tool-btn {
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-text);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition:
    border-color 0.12s,
    background 0.12s,
    transform 0.12s;
}

.tool-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, #22d3ee 50%, transparent);
}

.tool-btn.is-active {
  border-color: #22d3ee;
  background: color-mix(in srgb, #22d3ee 18%, transparent);
  color: #7dd3fc;
}

.tool-btn.is-disabled,
.tool-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
