<script setup lang="ts">
import { computed } from 'vue'
import type { AssociativeEntry, AssociativeViewHint } from '@/utils/traceProtocol'

const props = defineProps<{
  name: string
  viewHint: AssociativeViewHint
  entries: AssociativeEntry[]
  prevEntries?: AssociativeEntry[]
  varChanged?: boolean
}>()

const label = computed(() => {
  const map: Record<AssociativeViewHint, string> = {
    map: '映射',
    multimap: '多重映射',
    set: '集合',
    multiset: '多重集合',
    unordered_map: '哈希映射',
    unordered_multimap: '哈希多重映射',
    unordered_set: '哈希集合',
    unordered_multiset: '哈希多重集合',
  }
  return map[props.viewHint] ?? '关联容器'
})

const isHash = computed(() => props.viewHint.startsWith('unordered_'))

const prevKeySet = computed(() => new Set((props.prevEntries ?? []).map((e) => e.key)))
const isSetLike = computed(() => props.viewHint.includes('set'))

function entryKey(entry: AssociativeEntry, index: number): string {
  let occurrence = 0
  for (let i = 0; i < index; i++) {
    const candidate = props.entries[i]
    if (candidate?.key === entry.key && candidate.value === entry.value) occurrence++
  }
  return `${entry.key}\u0000${entry.value ?? ''}\u0000${occurrence}`
}

function rowHot(entry: AssociativeEntry): boolean {
  if (!props.varChanged) return false
  return !prevKeySet.value.has(entry.key)
}

function entryChanged(entry: AssociativeEntry): boolean {
  const prev = (props.prevEntries ?? []).find((e) => e.key === entry.key)
  if (!prev) return true
  return prev.value !== entry.value
}
</script>

<template>
  <div class="assoc-trace" :class="{ 'assoc-trace--hash': isHash }">
    <header class="assoc-head">
      <span class="assoc-tag">{{ label }} · {{ name }}</span>
      <span v-if="isHash" class="assoc-badge">哈希槽</span>
      <span class="assoc-count">{{ entries.length }} 项</span>
    </header>

    <TransitionGroup v-if="isHash" name="assoc-item" tag="div" class="assoc-slots">
      <div
        v-for="(entry, i) in entries"
        :key="entryKey(entry, i)"
        class="assoc-slot"
        :class="{
          'assoc-slot--hot': rowHot(entry) || (varChanged && entryChanged(entry)),
        }"
      >
        <span class="assoc-slot-idx">#{{ i }}</span>
        <span class="assoc-slot-key">{{ entry.key }}</span>
        <span v-if="entry.value != null" class="assoc-slot-val">→ {{ entry.value }}</span>
      </div>
      <p v-if="!entries.length" class="assoc-empty">（空哈希表）</p>
    </TransitionGroup>

    <table v-else class="assoc-table" :class="{ 'assoc-table--hot': varChanged }">
      <thead>
        <tr>
          <th>键</th>
          <th v-if="!isSetLike">值</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(entry, i) in entries"
          :key="entryKey(entry, i)"
          :class="{
            'assoc-row--hot': rowHot(entry) || (varChanged && entryChanged(entry)),
          }"
        >
          <td>{{ entry.key }}</td>
          <td v-if="!isSetLike">{{ entry.value ?? '—' }}</td>
        </tr>
        <tr v-if="!entries.length">
          <td :colspan="isSetLike ? 1 : 2" class="assoc-empty">（空）</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.assoc-trace {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, #a78bfa 35%, var(--alp-color-border));
  background: linear-gradient(
    165deg,
    var(--alp-bg-surface) 0%,
    color-mix(in srgb, #a78bfa 8%, var(--alp-bg-soft-block)) 100%
  );
}

.assoc-head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}

.assoc-tag {
  font-size: 12px;
  font-weight: 700;
  color: #a78bfa;
}

.assoc-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, #a78bfa 15%, var(--alp-bg-surface));
}

.assoc-count {
  margin-left: auto;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.assoc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.assoc-trace {
  min-width: 0;
  overflow-x: auto;
}

.assoc-table th,
.assoc-table td {
  padding: 8px 12px;
  border: 1px solid var(--alp-color-border);
  text-align: left;
  font-family: ui-monospace, Consolas, monospace;
}

.assoc-table th {
  background: var(--alp-bg-surface);
  font-weight: 600;
}

.assoc-slots {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.assoc-slot {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 72px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
}

.assoc-item-move,
.assoc-item-enter-active,
.assoc-item-leave-active {
  transition:
    transform 0.32s ease,
    opacity 0.32s ease;
}

.assoc-item-enter-from {
  opacity: 0;
  transform: translateY(-10px) scale(0.92);
}

.assoc-item-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.88);
}

@media (prefers-reduced-motion: reduce) {
  .assoc-item-move,
  .assoc-item-enter-active,
  .assoc-item-leave-active {
    transition: none !important;
  }
}

.assoc-slot-idx {
  font-size: 10px;
  color: var(--el-text-color-secondary);
}

.assoc-slot-key {
  font-weight: 700;
  font-family: ui-monospace, Consolas, monospace;
}

.assoc-slot-val {
  font-size: 12px;
  color: var(--el-color-primary);
}

.assoc-row--hot,
.assoc-slot--hot {
  animation: assoc-pulse 0.55s ease 2;
  background: color-mix(in srgb, var(--el-color-primary) 12%, var(--alp-bg-surface));
}

.assoc-table--hot {
  animation: assoc-pulse-wrap 0.45s ease;
}

.assoc-empty {
  text-align: center;
  color: var(--el-text-color-secondary);
  font-style: italic;
}

@keyframes assoc-pulse {
  0%,
  100% {
    box-shadow: none;
  }
  50% {
    box-shadow: 0 0 0 3px color-mix(in srgb, #a78bfa 35%, transparent);
  }
}

@keyframes assoc-pulse-wrap {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.92;
  }
}
</style>
