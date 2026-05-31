<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheck, Lock, Search, Warning } from '@element-plus/icons-vue'
import { getResourceVerification, verificationDisplayTag } from '@/utils/verification'

const props = defineProps<{
  meta?: Record<string, unknown>
  resourceType?: string
}>()

const verification = computed(() => getResourceVerification(props.meta))
const display = computed(() => verificationDisplayTag(props.meta ?? {}))
const panel = computed(() => (props.meta?.safety_panel ?? {}) as Record<string, unknown>)
const refs = computed(() =>
  Array.isArray(props.meta?.knowledge_refs) ? (props.meta?.knowledge_refs as string[]) : [],
)
const source = computed(
  () =>
    String(panel.value.knowledge_source ?? '') ||
    (refs.value.length ? refs.value.slice(0, 3).join('、') : '课程知识库检索片段'),
)
const chapterId = computed(() => verification.value?.chapter_id || props.meta?.chapter_id || '')
const evidenceCount = computed(
  () =>
    verification.value?.evidence_count ??
    verification.value?.grounded_chunks?.length ??
    refs.value.length,
)
const agents = computed(() =>
  Array.isArray(panel.value.agents)
    ? (panel.value.agents as string[])
    : ['ContentVerifierAgent', 'SafetyAgent'],
)
const sandbox = computed(() => (panel.value.oj_sandbox ?? {}) as Record<string, string>)
const verifierStatus = computed(() => verification.value?.verifier_status ?? 'warning')
const safetyStatus = computed(() => verification.value?.safety_status ?? 'warning')
</script>

<template>
  <section class="safety-panel" :class="`shield-${panel.shield ?? 'yellow'}`">
    <div class="safety-head">
      <el-icon><Lock /></el-icon>
      <strong>内容校验与安全证据</strong>
      <el-tag size="small" :type="display.type" effect="plain">{{ display.label }}</el-tag>
      <el-tag v-if="display.riskLabel" size="small" type="info" effect="plain">
        {{ display.riskLabel }}
      </el-tag>
    </div>

    <div class="status-row">
      <span>Verifier：<strong>{{ verifierStatus }}</strong></span>
      <span>Safety：<strong>{{ safetyStatus }}</strong></span>
      <span v-if="chapterId">章节：<strong>{{ chapterId }}</strong></span>
      <span>检索证据：<strong>{{ evidenceCount }}</strong> 条</span>
      <span v-if="verification?.retry_count">重试：<strong>{{ verification.retry_count }}</strong> 次</span>
    </div>

    <div class="safety-grid">
      <div class="safety-item">
        <el-icon><Search /></el-icon>
        <span>知识库溯源：{{ source }}</span>
      </div>
      <div class="safety-item" :class="{ warn: verifierStatus !== 'passed' }">
        <el-icon><CircleCheck /></el-icon>
        <span>ContentVerifier {{ verifierStatus === 'passed' ? '通过' : '待复核' }}</span>
      </div>
      <div class="safety-item" :class="{ warn: safetyStatus !== 'passed' }">
        <el-icon><CircleCheck /></el-icon>
        <span>SafetyAgent {{ safetyStatus === 'passed' ? '通过' : '告警' }}</span>
      </div>
      <div class="safety-item">
        <el-icon><Lock /></el-icon>
        <span>承办 Agent：{{ agents.join(' / ') }}</span>
      </div>
    </div>

    <p v-if="verification?.skip_reason" class="skip-reason">
      <el-icon><Warning /></el-icon>
      {{ verification.skip_reason }}
    </p>

    <div v-if="verification?.grounded_chunks?.length" class="evidence-block">
      <h4>检索证据片段</h4>
      <ul>
        <li v-for="c in verification.grounded_chunks.slice(0, 5)" :key="c.id">
          <code>{{ c.id }}</code> {{ c.title }} — {{ c.snippet }}
        </li>
      </ul>
    </div>

    <div v-if="verification?.hallucination_risks?.length" class="risk-block warn-block">
      <h4>可能幻觉</h4>
      <ul>
        <li v-for="(r, i) in verification.hallucination_risks" :key="`h-${i}`">{{ r }}</li>
      </ul>
    </div>

    <div v-if="verification?.unsupported_claims?.length" class="risk-block">
      <h4>缺乏依据的表述</h4>
      <ul>
        <li v-for="(r, i) in verification.unsupported_claims" :key="`u-${i}`">{{ r }}</li>
      </ul>
    </div>

    <div
      v-if="verification?.sensitive_risks?.length || verification?.prompt_injection_risks?.length"
      class="risk-block danger-block"
    >
      <h4>安全风险</h4>
      <ul>
        <li v-for="(r, i) in verification?.sensitive_risks ?? []" :key="`s-${i}`">{{ r }}</li>
        <li v-for="(r, i) in verification?.prompt_injection_risks ?? []" :key="`p-${i}`">{{ r }}</li>
      </ul>
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

.safety-panel.shield-yellow {
  border-color: color-mix(in srgb, #f59e0b 40%, var(--alp-color-border));
  background: color-mix(in srgb, #f59e0b 8%, var(--alp-bg-soft-block));
}

.safety-panel.shield-red {
  border-color: color-mix(in srgb, #ef4444 40%, var(--alp-color-border));
  background: color-mix(in srgb, #ef4444 8%, var(--alp-bg-soft-block));
}

.safety-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  color: #22c55e;
}

.shield-yellow .safety-head,
.shield-red .safety-head {
  color: var(--alp-color-text);
}

.status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--alp-color-muted);
  margin-bottom: 10px;
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

.skip-reason {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.evidence-block,
.risk-block {
  margin-top: 10px;
  font-size: 12px;
}

.evidence-block h4,
.risk-block h4 {
  margin: 0 0 6px;
  font-size: 12px;
}

.evidence-block ul,
.risk-block ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.5;
}

.warn-block {
  color: #d97706;
}

.danger-block {
  color: #dc2626;
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
