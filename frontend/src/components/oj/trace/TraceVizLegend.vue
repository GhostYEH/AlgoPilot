<script setup lang="ts">
defineProps<{
  variant: 'matrix' | 'linked_list' | 'memory'
}>()
</script>

<template>
  <ul v-if="variant === 'matrix'" class="trace-legend" aria-label="矩阵图例">
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--cursor" />
      金色框 = 当前计算格 (i, j)
    </li>
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--cell-hot" />
      绿色闪烁 = 本步数值更新
    </li>
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--axis" />
      橙黄行列头 = 当前下标
    </li>
  </ul>
  <ul v-else-if="variant === 'memory'" class="trace-legend" aria-label="内存图例">
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--stack" />
      蓝色边 = 栈帧指针
    </li>
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--heap" />
      紫色边 = 堆节点
    </li>
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--cell-hot" />
      绿色闪烁 = 地址/值本步变化
    </li>
  </ul>
  <ul v-else class="trace-legend" aria-label="链表图例">
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--ptr" />
      蓝色标签 = 指针 (prev / curr / nxt)
    </li>
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--node-hot" />
      高亮节点 = 本步节点或 next 改变
    </li>
    <li>
      <span class="trace-legend-swatch trace-legend-swatch--edge-hot" />
      高亮箭头 = 指向发生变化
    </li>
  </ul>
</template>

<style scoped>
.trace-legend {
  margin: 0 0 8px;
  padding: 6px 8px;
  list-style: none;
  font-size: 11px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
  background: color-mix(in srgb, var(--alp-bg-surface) 60%, transparent);
  border-radius: 6px;
  border: 1px dashed var(--alp-color-border);
}

.trace-legend li {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 2px 0;
}

.trace-legend-swatch {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  border-radius: 4px;
  border: 2px solid var(--alp-color-border);
}

.trace-legend-swatch--cursor {
  border-color: #f59e0b;
  background: color-mix(in srgb, #f59e0b 25%, transparent);
}

.trace-legend-swatch--cell-hot {
  border-color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 30%, transparent);
}

.trace-legend-swatch--axis {
  background: color-mix(in srgb, #f59e0b 20%, transparent);
}

.trace-legend-swatch--ptr {
  border-radius: 3px;
  width: 18px;
  height: 10px;
  border: none;
  background: #22d3ee;
}

.trace-legend-swatch--node-hot {
  border-radius: 50%;
  border-color: var(--el-color-primary);
}

.trace-legend-swatch--edge-hot {
  border: none;
  background: var(--el-color-primary);
  width: 18px;
  height: 4px;
  border-radius: 2px;
}

.trace-legend-swatch--stack {
  border-left: 3px solid #22d3ee;
  border-radius: 2px;
}

.trace-legend-swatch--heap {
  border-left: 3px solid #a78bfa;
  border-radius: 2px;
}
</style>
