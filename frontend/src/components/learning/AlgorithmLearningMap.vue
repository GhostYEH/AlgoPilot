<script setup lang="ts">
import { computed } from 'vue'
import { Check, Lock } from '@element-plus/icons-vue'
import {
  ALGORITHM_MODULES,
  MODULE_PHASE_LABELS,
  type AlgorithmModuleItem,
  type ModulePhase,
} from '@/constants/modules'
import { getModuleProgressPercent } from '@/utils/moduleProgressSummary'

const props = defineProps<{
  collapsed?: boolean
  activeKey: string
}>()

const emit = defineEmits<{
  select: [key: string]
}>()

/** 带阶段标题的首项索引 */
const phaseStartIndices = computed(() => {
  const map = new Map<ModulePhase, number>()
  ALGORITHM_MODULES.forEach((m, i) => {
    if (!map.has(m.phase)) map.set(m.phase, i)
  })
  return map
})

function showPhaseLabel(module: AlgorithmModuleItem, index: number): boolean {
  return phaseStartIndices.value.get(module.phase) === index
}

function progressFor(key: string): number {
  return getModuleProgressPercent(key)
}

function nodeStatus(
  key: string,
  available: boolean,
): 'active' | 'done' | 'in-progress' | 'idle' | 'planned' {
  if (key === props.activeKey) return 'active'
  const pct = progressFor(key)
  if (pct === 100) return 'done'
  if (pct > 0) return 'in-progress'
  if (!available) return 'planned'
  return 'idle'
}

function onSelect(key: string) {
  emit('select', key)
}

/** 节点序号（学习路径顺序） */
function stepNo(index: number): string {
  return String(index + 1).padStart(2, '0')
}
</script>

<template>
  <nav class="learning-map" :class="{ 'is-collapsed': collapsed }" aria-label="算法学习地图">
    <ol class="map-track">
      <template v-for="(module, index) in ALGORITHM_MODULES" :key="module.key">
        <li v-if="showPhaseLabel(module, index) && !collapsed" class="phase-label">
          <span class="phase-text">{{ MODULE_PHASE_LABELS[module.phase] }}</span>
        </li>

        <li class="map-node-wrap">
          <div
            class="connector connector--top"
            :class="{ 'is-hidden': index === 0 }"
            aria-hidden="true"
          />

          <button
            type="button"
            class="map-node"
            :class="[
              `status-${nodeStatus(module.key, module.available)}`,
              { 'is-active': module.key === activeKey },
            ]"
            :style="{ '--node-accent': module.accent }"
            :title="module.label"
            :aria-current="module.key === activeKey ? 'step' : undefined"
            @click="onSelect(module.key)"
          >
            <span class="node-ring" aria-hidden="true">
              <svg
                v-if="progressFor(module.key) >= 0"
                class="progress-ring"
                viewBox="0 0 36 36"
                aria-hidden="true"
              >
                <circle class="ring-bg" cx="18" cy="18" r="15.5" pathLength="100" />
                <circle
                  class="ring-fg"
                  cx="18"
                  cy="18"
                  r="15.5"
                  pathLength="100"
                  :stroke-dasharray="`${Math.max(0, progressFor(module.key))} 100`"
                />
              </svg>
            </span>

            <span class="node-core">
              <el-icon v-if="nodeStatus(module.key, module.available) === 'done'" class="node-icon">
                <Check />
              </el-icon>
              <el-icon
                v-else-if="!module.available && module.key !== activeKey"
                class="node-icon node-icon--muted"
              >
                <Lock />
              </el-icon>
              <span v-else class="node-glyph" aria-hidden="true">{{ module.label.charAt(0) }}</span>
            </span>

            <span v-if="!collapsed" class="node-step">{{ stepNo(index) }}</span>
          </button>

          <div v-if="!collapsed" class="node-body">
            <span class="node-label">{{ module.label }}</span>
            <span v-if="progressFor(module.key) >= 0" class="node-meta">
              {{ progressFor(module.key) }}%
            </span>
            <span v-else-if="!module.available" class="node-meta node-meta--muted">规划中</span>
            <span v-else class="node-meta node-meta--muted">未开始</span>
          </div>

          <div
            class="connector connector--bottom"
            :class="{ 'is-hidden': index === ALGORITHM_MODULES.length - 1 }"
            aria-hidden="true"
          />
        </li>
      </template>
    </ol>
  </nav>
</template>

<style scoped>
.learning-map {
  padding: 8px 10px 16px;
}

.map-track {
  list-style: none;
  margin: 0;
  padding: 0;
}

.phase-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 14px 0 6px 4px;
  padding-left: 2px;
}

.phase-label:first-child {
  margin-top: 4px;
}

.phase-text {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--alp-color-muted);
  text-transform: uppercase;
  white-space: nowrap;
}

.phase-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--alp-color-border);
}

.map-node-wrap {
  position: relative;
  display: grid;
  grid-template-columns: 44px 1fr;
  grid-template-rows: auto auto auto;
  column-gap: 10px;
  align-items: center;
  min-height: 52px;
}

.connector {
  grid-column: 1;
  justify-self: center;
  width: 2px;
  height: 10px;
  border-radius: 1px;
  background: rgba(148, 163, 184, 0.3);
}

.connector.is-hidden {
  visibility: hidden;
}

.connector--top {
  grid-row: 1;
}

.map-node {
  grid-column: 1;
  grid-row: 2;
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin: 0 auto;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 50%;
  transition:
    transform var(--alp-transition-fast),
    filter var(--alp-transition-fast);
}

.map-node:hover {
  transform: scale(1.06);
}

.map-node:focus-visible {
  outline: 2px solid var(--node-accent, var(--alp-color-primary));
  outline-offset: 3px;
}

.node-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--alp-bg-surface-solid);
  border: 2px solid rgba(148, 163, 184, 0.35);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
  transition:
    border-color var(--alp-transition-fast),
    box-shadow var(--alp-transition-fast);
}

.progress-ring {
  position: absolute;
  inset: -2px;
  width: calc(100% + 4px);
  height: calc(100% + 4px);
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: rgba(148, 163, 184, 0.2);
  stroke-width: 2.5;
}

.ring-fg {
  fill: none;
  stroke: var(--node-accent, var(--alp-color-primary));
  stroke-width: 2.5;
  stroke-linecap: round;
  transition: stroke-dasharray 0.35s ease;
}

.node-core {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.85);
}

.node-glyph {
  font-size: 13px;
  font-weight: 700;
  color: var(--node-accent, var(--alp-color-primary));
}

.node-icon {
  font-size: 16px;
  color: #6aa878;
}

.node-icon--muted {
  color: var(--alp-color-muted);
  font-size: 14px;
}

.node-step {
  position: absolute;
  right: -2px;
  bottom: -2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  font-size: 9px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  color: var(--alp-color-muted);
  background: var(--alp-bg-surface-solid);
  border: 1px solid var(--alp-color-border);
  border-radius: 8px;
}

.node-body {
  grid-column: 2;
  grid-row: 2;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  text-align: left;
}

.node-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  line-height: 1.3;
  transition: color var(--alp-transition-fast);
}

.node-meta {
  font-size: 11px;
  color: var(--node-accent, var(--alp-color-primary));
  font-variant-numeric: tabular-nums;
}

.node-meta--muted {
  color: var(--alp-color-muted);
}

.connector--bottom {
  grid-row: 3;
}

/* 状态 */
.map-node.is-active .node-ring {
  border-color: var(--node-accent, var(--alp-color-primary));
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--node-accent, #3d8a7e) 22%, transparent),
    0 8px 20px color-mix(in srgb, var(--node-accent, #3d8a7e) 28%, transparent);
}

.map-node.is-active .node-label {
  color: var(--node-accent, var(--alp-color-primary));
}

.status-done .node-ring {
  border-color: rgba(106, 168, 120, 0.55);
}

.status-planned .node-ring {
  border-style: dashed;
  opacity: 0.85;
}

.status-planned .node-glyph {
  opacity: 0.65;
}

/* 折叠：仅节点列 */
.learning-map.is-collapsed {
  padding: 8px 6px 16px;
}

.learning-map.is-collapsed .map-node-wrap {
  grid-template-columns: 1fr;
  justify-items: center;
  min-height: 48px;
}

.learning-map.is-collapsed .node-body,
.learning-map.is-collapsed .node-step {
  display: none;
}

.learning-map.is-collapsed .connector {
  height: 8px;
}
</style>
