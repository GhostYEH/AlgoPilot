<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheck, Lock, Warning } from '@element-plus/icons-vue'
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
const source = computed(() => {
  if (String(panel.value.knowledge_source ?? '')) return String(panel.value.knowledge_source)
  if (refs.value.length) {
    return refs.value
      .slice(0, 3)
      .map((r) => r.split(':').pop() || r)
      .join('、')
  }
  return '课程知识库'
})
const evidenceCount = computed(
  () =>
    verification.value?.evidence_count ??
    verification.value?.grounded_chunks?.length ??
    refs.value.length,
)
const sandbox = computed(() => (panel.value.oj_sandbox ?? {}) as Record<string, string>)
const verifierStatus = computed(() => verification.value?.verifier_status ?? 'warning')
const safetyStatus = computed(() => verification.value?.safety_status ?? 'warning')
const hasRisks = computed(
  () =>
    verification.value?.hallucination_risks?.length ||
    verification.value?.unsupported_claims?.length ||
    verification.value?.sensitive_risks?.length ||
    verification.value?.prompt_injection_risks?.length,
)
</script>

<template>
  <section class="safety-panel" :class="`shield-${panel.shield ?? 'yellow'}`">
    <div class="safety-head">
      <el-icon><Lock /></el-icon>
      <strong>内容校验</strong>
      <el-tag size="small" :type="display.type" effect="plain">{{ display.label }}</el-tag>
    </div>

    <div class="safety-summary">
      <div class="safety-badge" :class="{ ok: verifierStatus === 'passed' }">
        <el-icon><CircleCheck /></el-icon>
        <span>{{ verifierStatus === 'passed' ? '内容校验通过' : '内容待复核' }}</span>
      </div>
      <div class="safety-badge" :class="{ ok: safetyStatus === 'passed' }">
        <el-icon><CircleCheck /></el-icon>
        <span>{{ safetyStatus === 'passed' ? '安全审查通过' : '安全审查待确认' }}</span>
      </div>
      <div class="safety-badge">
        <span class="evidence-num">{{ evidenceCount }}</span>
        <span>条知识库依据</span>
      </div>
    </div>

    <p v-if="verification?.skip_reason" class="skip-reason">
      <el-icon><Warning /></el-icon>
      {{ verification.skip_reason }}
    </p>

    <div v-if="hasRisks" class="risk-section">
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
    </div>

    <details class="safety-detail">
      <summary>校验详情</summary>
      <div class="detail-content">
        <p>知识库溯源：{{ source }}</p>
        <p>校验状态：{{ verifierStatus }}</p>
        <p>安全状态：{{ safetyStatus }}</p>
        <div v-if="verification?.grounded_chunks?.length" class="evidence-block">
          <h4>检索证据片段</h4>
          <ul>
            <li v-for="c in verification.grounded_chunks.slice(0, 5)" :key="c.id">
              {{ c.title }} — {{ c.snippet }}
            </li>
          </ul>
        </div>
        <div v-if="resourceType === 'trace_animation' || Object.keys(sandbox).length" class="sandbox-detail">
          <h4>沙盒限制</h4>
          <p>限时：{{ sandbox.time_limit ?? '题目级限时 + trace 8s 上限' }}</p>
          <p>限内存：{{ sandbox.memory_limit ?? '题目级内存限制' }}</p>
          <p>系统调用：{{ sandbox.syscall_policy ?? '禁用 system/fork/exec 与危险头文件' }}</p>
          <p>隔离：{{ sandbox.isolation ?? '子进程执行；生产部署建议 Docker 隔离' }}</p>
        </div>
      </div>
    </details>
  </section>
</template>

<style scoped>
.safety-panel {
  margin-top: 16px;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--alp-color-success) 38%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-success) 8%, var(--alp-bg-soft-block));
}

.safety-panel.shield-yellow {
  border-color: color-mix(in srgb, var(--alp-color-warning) 40%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-warning) 8%, var(--alp-bg-soft-block));
}

.safety-panel.shield-red {
  border-color: color-mix(in srgb, var(--alp-color-danger) 40%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-danger) 8%, var(--alp-bg-soft-block));
}

.safety-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  color: var(--alp-color-success);
}

.shield-yellow .safety-head,
.shield-red .safety-head {
  color: var(--alp-color-text);
}

.safety-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.safety-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--alp-bg-surface) 80%, transparent);
  color: var(--alp-color-muted);
  font-size: 12px;
}

.safety-badge.ok {
  color: var(--alp-color-success);
}

.evidence-num {
  font-weight: 700;
  color: var(--alp-color-primary);
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

.risk-section {
  margin-top: 12px;
}

.risk-block {
  margin-top: 8px;
  font-size: 12px;
}

.risk-block h4 {
  margin: 0 0 6px;
  font-size: 12px;
}

.risk-block ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.5;
}

.warn-block {
  color: var(--alp-color-warning);
}

.danger-block {
  color: var(--alp-color-danger);
}

.safety-detail {
  margin-top: 10px;
}

.safety-detail summary {
  cursor: pointer;
  color: var(--alp-color-primary);
  font-size: 12px;
}

.detail-content {
  margin-top: 8px;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.6;
}

.detail-content p {
  margin: 4px 0;
}

.evidence-block {
  margin-top: 8px;
}

.evidence-block h4 {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--alp-color-text);
}

.evidence-block ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.5;
}

.sandbox-detail {
  margin-top: 8px;
}

.sandbox-detail h4 {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--alp-color-text);
}

.sandbox-detail p {
  margin: 4px 0;
}
</style>
