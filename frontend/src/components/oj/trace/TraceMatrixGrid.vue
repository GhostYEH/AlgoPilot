<script setup lang="ts">
import { computed } from 'vue'
import TraceVizLegend from '@/components/oj/trace/TraceVizLegend.vue'
import type { MatrixValue } from '@/types/codeTrace'

const props = defineProps<{
  name: string
  matrix: MatrixValue
  hotCells?: string[]
  varChanged?: boolean
  /** 当前计算格坐标（来自 i,j 或 r,c） */
  activeRow?: number | null
  activeCol?: number | null
}>()

const hotSet = computed(() => new Set(props.hotCells ?? []))

const colHeaders = computed(() =>
  Array.from({ length: props.matrix.cols }, (_, i) => i),
)

function cellKey(r: number, c: number) {
  return `${r},${c}`
}

function isHot(r: number, c: number) {
  return hotSet.value.has(cellKey(r, c))
}

function isActive(r: number, c: number) {
  return props.activeRow === r && props.activeCol === c
}

function isRowHeaderHot(r: number) {
  return props.activeRow === r
}

function isColHeaderHot(c: number) {
  return props.activeCol === c
}
</script>

<template>
  <div class="trace-matrix" :class="{ 'trace-matrix--var-hot': varChanged }">
    <div class="trace-matrix-label">
      {{ name }}
      <span class="tag">DP 表</span>
      <span v-if="activeRow != null && activeCol != null" class="cursor-hint">
        当前格 ({{ activeRow }}, {{ activeCol }})
      </span>
    </div>
    <TraceVizLegend variant="matrix" />

    <div class="trace-matrix-table-wrap">
      <table class="trace-matrix-table" role="grid" :aria-label="`${name} 二维表`">
        <thead>
          <tr>
            <th class="corner" scope="col" />
            <th
              v-for="c in colHeaders"
              :key="'h' + c"
              class="col-head"
              :class="{ 'col-head--active': isColHeaderHot(c) }"
              scope="col"
            >
              {{ c }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, r) in matrix.cells" :key="r">
            <th
              class="row-head"
              :class="{ 'row-head--active': isRowHeaderHot(r) }"
              scope="row"
            >
              {{ r }}
            </th>
            <td
              v-for="(cell, c) in row"
              :key="c"
              class="trace-matrix-cell"
              :class="{
                'trace-matrix-cell--hot': isHot(r, c),
                'trace-matrix-cell--active': isActive(r, c),
              }"
              role="gridcell"
            >
              <span class="trace-matrix-val">{{ cell === null || cell === '' ? '·' : cell }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.trace-matrix {
  margin-bottom: 14px;
}

.trace-matrix-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.trace-matrix--var-hot .trace-matrix-label {
  color: var(--el-color-primary);
}

.tag {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.cursor-hint {
  font-size: 11px;
  font-weight: 600;
  color: #f59e0b;
}

.trace-matrix-table-wrap {
  overflow: auto;
  max-width: 100%;
  padding: 8px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.trace-matrix-table {
  border-collapse: separate;
  border-spacing: 4px;
}

.corner {
  width: 28px;
  background: transparent;
  border: none;
}

.col-head,
.row-head {
  font-size: 11px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
  text-align: center;
  padding: 4px 6px;
  transition:
    color 0.2s,
    background 0.2s;
}

.col-head--active,
.row-head--active {
  color: #f59e0b;
  background: color-mix(in srgb, #f59e0b 15%, transparent);
  border-radius: 4px;
}

.trace-matrix-cell {
  min-width: 48px;
  min-height: 48px;
  text-align: center;
  vertical-align: middle;
  border-radius: 8px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  transition:
    border-color 0.25s,
    background 0.25s,
    transform 0.25s,
    box-shadow 0.25s;
}

.trace-matrix-cell--active {
  border-color: #f59e0b;
  box-shadow:
    0 0 0 2px color-mix(in srgb, #f59e0b 35%, transparent),
    inset 0 0 0 1px #f59e0b;
  background: color-mix(in srgb, #f59e0b 12%, var(--alp-bg-surface));
}

.trace-matrix-cell--hot {
  border-color: #22c55e;
  background: color-mix(in srgb, #22c55e 28%, transparent);
  animation: matrix-pulse 0.55s ease;
}

.trace-matrix-cell--active.trace-matrix-cell--hot {
  animation: matrix-pulse-active 0.55s ease;
}

.trace-matrix-val {
  font-size: 15px;
  font-weight: 700;
  font-family: ui-monospace, Consolas, monospace;
}

@keyframes matrix-pulse {
  0% {
    transform: scale(1);
  }
  45% {
    transform: scale(1.06);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes matrix-pulse-active {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 color-mix(in srgb, #f59e0b 50%, transparent);
  }
  50% {
    transform: scale(1.08);
    box-shadow: 0 0 0 6px transparent;
  }
  100% {
    transform: scale(1);
  }
}
</style>
