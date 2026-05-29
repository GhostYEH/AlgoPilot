<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheck, Lock, Search } from '@element-plus/icons-vue'

const props = defineProps<{
  meta?: Record<string, unknown>
  resourceType?: string
}>()

const panel = computed(() => (props.meta?.safety_panel ?? {}) as Record<string, unknown>)
const refs = computed(() =>
  Array.isArray(props.meta?.knowledge_refs) ? (props.meta?.knowledge_refs as string[]) : [],
)
const source = computed(
  () =>
    String(panel.value.knowledge_source ?? '') ||
    (refs.value.length ? refs.value.slice(0, 3).join('、') : '课程知识库检索片段'),
)
const complexityOk = computed(() => panel.value.complexity_verified !== false)
const sensitiveOk = computed(() => panel.value.sensitive_filter_passed !== false)
const agents = computed(() =>
  Array.isArray(panel.value.agents)
    ? (panel.value.agents as string[])
    : ['ContentVerifierAgent', 'SafetyAgent'],
)
const sandbox = computed(() => (panel.value.oj_sandbox ?? {}) as Record<string, string>)
</script>

<template>
  <section class="safety-panel">
    <div class="safety-head">
      <el-icon><Lock /></el-icon>
      <strong>安全与校验面板</strong>
      <span>绿色盾牌 · 可答辩追溯</span>
    </div>
    <div class="safety-grid">
      <div class="safety-item">
        <el-icon><Search /></el-icon>
        <span>知识库溯源：{{ source }}</span>
      </div>
      <div class="safety-item" :class="{ warn: !complexityOk }">
        <el-icon><CircleCheck /></el-icon>
        <span>复杂度事实校验{{ complexityOk ? '通过' : '待人工复核' }}</span>
      </div>
      <div class="safety-item" :class="{ warn: !sensitiveOk }">
        <el-icon><CircleCheck /></el-icon>
        <span>敏感词过滤{{ sensitiveOk ? '通过' : '未通过' }}</span>
      </div>
      <div class="safety-item">
        <el-icon><Lock /></el-icon>
        <span>承办 Agent：{{ agents.join(' / ') }}</span>
      </div>
    </div>
    <details v-if="resourceType === 'trace_animation' || Object.keys(sandbox).length" class="sandbox-detail">
      <summary>OJ 沙盒限制声明</summary>
      <p>限时：{{ sandbox.time_limit ?? '题目级限时 + trace 8s 上限' }}</p>
      <p>限内存：{{ sandbox.memory_limit ?? '题目级内存限制' }}</p>
      <p>系统调用：{{ sandbox.syscall_policy ?? '禁用 system/fork/exec 与危险头文件' }}</p>
      <p>隔离：{{ sandbox.isolation ?? '子进程执行；生产部署建议 Docker 隔离' }}</p>
    </details>
  </section>
</template>

<style scoped>
.safety-panel {
  margin-top: 16px;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, #22c55e 38%, var(--alp-color-border));
  background: color-mix(in srgb, #22c55e 8%, var(--alp-bg-soft-block));
}

.safety-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #22c55e;
}

.safety-head span {
  margin-left: auto;
  color: var(--alp-color-muted);
  font-size: 11px;
}

.safety-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px;
}

.safety-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--alp-bg-surface) 80%, transparent);
  color: var(--alp-color-text);
  font-size: 12px;
}

.safety-item.warn {
  color: #f59e0b;
}

.sandbox-detail {
  margin-top: 10px;
  color: var(--alp-color-muted);
  font-size: 12px;
}

.sandbox-detail summary {
  cursor: pointer;
  color: var(--alp-color-primary);
}

.sandbox-detail p {
  margin: 6px 0 0;
}
</style>
