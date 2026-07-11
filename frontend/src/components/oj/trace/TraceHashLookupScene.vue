<script setup lang="ts">
import type { HashLookupScene } from '@/utils/traceHashLookup'

const props = defineProps<{
  scene: HashLookupScene
  changed: Set<string>
}>()
</script>

<template>
  <div class="ht-trace-scene">
    <article class="ht-trace-card">
      <header class="ht-trace-head">
        <span class="ht-trace-tag">数组 nums</span>
        <span v-if="scene.target != null" class="ht-trace-badge">target = {{ scene.target }}</span>
      </header>
      <div v-if="scene.nums.length" class="ht-arr-row ht-arr-row--idx">
        <div v-for="(n, i) in scene.nums" :key="'n' + i" class="ht-idx-wrap">
          <span
            class="ht-cell"
            :class="{
              'ht-cell--hot': scene.activeIndex === i,
              'ht-cell--dim': scene.found && scene.activeIndex !== i,
              'ht-cell--pulse': changed.has('nums') || changed.has('i'),
            }"
          >{{ n }}</span>
          <span class="ht-idx">i={{ i }}</span>
        </div>
      </div>
      <p v-else class="ht-hint">等待读入数组…</p>
      <p
        v-if="scene.target != null && scene.activeIndex != null && scene.nums[scene.activeIndex]"
        class="ht-lookup"
      >
        查 map：
        <strong>{{ scene.target }} − {{ scene.nums[scene.activeIndex] }} = {{ scene.complement ?? '?' }}</strong>
        <span v-if="scene.lookupKey != null" class="ht-lookup-key">（键 {{ scene.lookupKey }}）</span>
      </p>
    </article>

    <span class="ht-transfer" aria-hidden="true">⇄ 哈希</span>

    <article class="ht-trace-card ht-trace-card--map">
      <header class="ht-trace-head">
        <span class="ht-trace-tag ht-trace-tag--violet">{{ scene.mapName }}</span>
        <span class="ht-trace-badge">先查后插入</span>
      </header>
      <div class="ht-map-entries">
        <div
          v-for="e in scene.mapEntries"
          :key="e.key"
          class="ht-map-entry"
          :class="{
            'ht-map-entry--hot':
              scene.lookupKey != null && e.key === scene.lookupKey && changed.has(scene.mapName),
          }"
        >
          <span class="ht-cell ht-cell--key">{{ e.key }}</span>
          <span class="ht-map-arrow">→ 下标</span>
          <span class="ht-cell">{{ e.value }}</span>
        </div>
        <span v-if="!scene.mapEntries.length" class="ht-empty">（空表，尚未插入）</span>
      </div>
      <p v-if="scene.found" class="ht-found">
        命中：输出下标对
        <strong v-if="scene.result.length === 2"> [{{ scene.result[0] }}, {{ scene.result[1] }}]</strong>
      </p>
    </article>
  </div>
</template>

<style scoped>
.ht-trace-scene {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 12px;
  align-items: stretch;
  margin-bottom: 12px;
}

.ht-trace-card {
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
  padding: 12px 14px;
  background: var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
}

.ht-trace-card--map {
  border-color: color-mix(in srgb, var(--alp-color-accent) 35%, var(--alp-color-border));
}

.ht-trace-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.ht-trace-tag {
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-primary);
}

.ht-trace-tag--violet {
  color: var(--alp-color-accent);
}

.ht-trace-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-color-primary) 15%, transparent);
  color: var(--alp-color-muted);
}

.ht-arr-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: flex-end;
}

.ht-idx-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.ht-cell {
  display: inline-flex;
  min-width: 44px;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.ht-cell--hot {
  border-color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 18%, var(--alp-bg-soft-block));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--alp-color-primary) 25%, transparent);
  transform: scale(1.06);
}

.ht-cell--dim {
  opacity: 0.45;
}

.ht-cell--pulse {
  animation: ht-pulse 0.6s ease;
}

.ht-cell--key {
  border-color: var(--alp-color-accent);
}

.ht-idx {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.ht-lookup {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--alp-color-text);
}

.ht-lookup-key {
  color: var(--alp-color-accent);
  margin-left: 4px;
}

.ht-transfer {
  align-self: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.ht-map-entries {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 48px;
}

.ht-map-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px dashed var(--alp-color-border);
  transition: background 0.15s;
}

.ht-map-entry--hot {
  border-style: solid;
  border-color: var(--alp-color-accent);
  background: color-mix(in srgb, var(--alp-color-accent) 14%, transparent);
}

.ht-map-arrow {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.ht-empty {
  font-size: 13px;
  color: var(--alp-color-muted);
  font-style: italic;
}

.ht-found {
  margin: 10px 0 0;
  font-size: 13px;
  font-weight: 600;
  color: #6aa878;
}

.ht-hint {
  margin: 0;
  font-size: 13px;
  color: var(--alp-color-muted);
}

@keyframes ht-pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.08);
  }
  100% {
    transform: scale(1);
  }
}

@media (max-width: 720px) {
  .ht-trace-scene {
    grid-template-columns: 1fr;
  }

  .ht-transfer {
    text-align: center;
  }
}
</style>
