<script setup lang="ts">
import type { MapEntry } from '@/utils/traceHashLookup'

defineProps<{
  name: string
  entries: MapEntry[]
  hotKeys?: Set<string>
  varChanged?: boolean
}>()
</script>

<template>
  <article class="trace-dict" :class="{ 'trace-dict--hot': varChanged }">
    <header class="trace-dict-head">
      <span class="trace-dict-tag">{{ name }}</span>
      <span class="trace-dict-badge">{{ entries.length }} 项</span>
    </header>
    <div v-if="entries.length" class="trace-dict-entries">
      <div
        v-for="e in entries"
        :key="e.key"
        class="trace-dict-entry"
        :class="{ 'trace-dict-entry--hot': hotKeys?.has(e.key) }"
      >
        <span class="trace-dict-key">{{ e.key }}</span>
        <span class="trace-dict-arrow">→</span>
        <span class="trace-dict-val">{{ e.value }}</span>
      </div>
    </div>
    <p v-else class="trace-dict-empty">（空）</p>
  </article>
</template>

<style scoped>
.trace-dict {
  margin-bottom: 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
  padding: 12px 14px;
  background: var(--alp-bg-soft-block);
}

.trace-dict--hot {
  border-color: color-mix(in srgb, var(--alp-color-accent) 45%, var(--alp-color-border));
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--alp-color-accent) 20%, transparent);
}

.trace-dict-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.trace-dict-tag {
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-accent);
}

.trace-dict-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--alp-color-accent) 12%, transparent);
  color: var(--alp-color-muted);
}

.trace-dict-entries {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.trace-dict-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px dashed var(--alp-color-border);
  font-family: ui-monospace, Consolas, monospace;
  font-size: 14px;
}

.trace-dict-entry--hot {
  border-style: solid;
  border-color: var(--alp-color-accent);
  background: color-mix(in srgb, var(--alp-color-accent) 12%, transparent);
}

.trace-dict-key {
  font-weight: 700;
  color: #c4b5fd;
}

.trace-dict-arrow {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.trace-dict-val {
  font-weight: 600;
}

.trace-dict-empty {
  margin: 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  font-style: italic;
}
</style>
