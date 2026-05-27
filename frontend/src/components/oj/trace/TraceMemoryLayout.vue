<script setup lang="ts">
import { computed } from 'vue'
import TraceVizLegend from '@/components/oj/trace/TraceVizLegend.vue'
import type { MemoryRegion, MemorySlot } from '@/utils/traceMemory'

const props = defineProps<{
  slots: MemorySlot[]
  hotIds?: string[]
  varChanged?: boolean
}>()

const hotSet = computed(() => new Set(props.hotIds ?? []))

const grouped = computed(() => {
  const regions: MemoryRegion[] = ['stack', 'global', 'heap']
  const labels: Record<MemoryRegion, string> = {
    stack: '栈帧 (Stack)',
    global: '全局 / 静态',
    heap: '堆 (Heap)',
  }
  return regions
    .map((region) => ({
      region,
      label: labels[region],
      items: props.slots.filter((s) => s.region === region),
    }))
    .filter((g) => g.items.length > 0)
})

function isHot(id: string) {
  return hotSet.value.has(id)
}
</script>

<template>
  <div class="trace-memory" :class="{ 'trace-memory--var-hot': varChanged }">
    <div class="trace-memory-label">
      C++ 内存布局
      <span class="tag">GDB</span>
    </div>
    <TraceVizLegend variant="memory" />

    <div class="trace-memory-regions">
      <section v-for="group in grouped" :key="group.region" class="memory-region">
        <header class="region-head">{{ group.label }}</header>
        <div class="memory-stack">
          <div
            v-for="slot in group.items"
            :key="slot.id"
            class="memory-slot"
            :class="{
              'memory-slot--hot': isHot(slot.id),
              [`memory-slot--${group.region}`]: true,
            }"
          >
            <span class="slot-name">{{ slot.name }}</span>
            <span class="slot-addr">{{ slot.address }}</span>
            <span class="slot-val">{{ slot.displayValue }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.trace-memory {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, #38bdf8 25%, var(--alp-color-border));
  background: color-mix(in srgb, #0f172a 6%, var(--alp-bg-soft-block));
}

.trace-memory--var-hot {
  border-color: color-mix(in srgb, #4ade80 45%, var(--alp-color-border));
}

.trace-memory-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin-bottom: 8px;
}

.tag {
  font-size: 10px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
  background: color-mix(in srgb, #38bdf8 15%, transparent);
  color: #38bdf8;
}

.trace-memory-regions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.region-head {
  font-size: 10px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--alp-color-muted);
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px dashed color-mix(in srgb, #fff 10%, transparent);
}

.memory-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
  font-size: 11px;
}

.memory-slot {
  display: grid;
  grid-template-columns: minmax(72px, 1fr) minmax(100px, 1.2fr) minmax(80px, 1fr);
  gap: 8px;
  align-items: center;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid color-mix(in srgb, #fff 8%, transparent);
  background: color-mix(in srgb, #fff 3%, transparent);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.memory-slot--stack {
  border-left: 3px solid #38bdf8;
}

.memory-slot--heap {
  border-left: 3px solid #a78bfa;
}

.memory-slot--global {
  border-left: 3px solid #94a3b8;
}

.memory-slot--hot {
  border-color: #4ade80;
  box-shadow: 0 0 0 1px color-mix(in srgb, #4ade80 40%, transparent);
  animation: mem-pulse 0.55s ease;
}

@keyframes mem-pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.5);
  }
  45% {
    transform: scale(1.02);
    box-shadow: 0 0 14px 2px rgba(74, 222, 128, 0.35);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 1px color-mix(in srgb, #4ade80 40%, transparent);
  }
}

.slot-name {
  color: #e2e8f0;
  font-weight: 600;
}

.slot-addr {
  color: #38bdf8;
  font-variant-numeric: tabular-nums;
}

.slot-val {
  color: #a5f3fc;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
