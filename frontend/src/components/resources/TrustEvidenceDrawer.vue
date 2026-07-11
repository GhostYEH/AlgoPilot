<script setup lang="ts">
import { ref, watch } from 'vue'
import { CircleCheck, CircleClose, Warning, InfoFilled, Lock, Search } from '@element-plus/icons-vue'
import { fetchResourceEvidence, type TrustEvidence, type GeneratedResource } from '@/api/orchestrator'

const props = defineProps<{
  visible: boolean
  resource: GeneratedResource | null
}>()

const emit = defineEmits<{ 'update:visible': [v: boolean] }>()

const loading = ref(false)
const error = ref(false)
const evidence = ref<TrustEvidence | null>(null)

watch(
  () => props.visible && props.resource?.id,
  async (id) => {
    if (!id || !props.visible) return
    loading.value = true
    error.value = false
    try {
      evidence.value = await fetchResourceEvidence(id)
    } catch {
      error.value = true
      evidence.value = null
    } finally {
      loading.value = false
    }
  },
)

function statusIcon(status: string) {
  if (status === 'passed') return CircleCheck
  if (status === 'failed') return CircleClose
  return Warning
}

function statusClass(status: string) {
  if (status === 'passed') return 'ev-passed'
  if (status === 'failed') return 'ev-failed'
  return 'ev-warning'
}

function stageLabel(stage: string) {
  const map: Record<string, string> = {
    rag_retrieve: 'RAG 检索',
    agent_generate: 'Agent 生成',
    content_verify: '内容校验',
    safety_filter: '安全审查',
    persist: '落库',
  }
  return map[stage] || stage
}

function decisionLabel(d: string) {
  const map: Record<string, string> = {
    publish: '已发布',
    draft: '草稿（待校验）',
    blocked: '已拦截',
  }
  return map[d] || d
}

function humanReviewLabel(s: string) {
  const map: Record<string, string> = {
    pending: '待人工复核',
    not_required: '无需人工复核',
    approved: '人工已批准',
    rejected: '人工已驳回',
  }
  return map[s] || s
}

function formatTime(iso: string) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso.slice(0, 16)
    return d.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return iso.slice(0, 16)
  }
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    direction="rtl"
    size="520px"
    :title="`可信证据链 · ${resource?.agent_name ?? ''}`"
    @update:model-value="emit('update:visible', $event)"
  >
    <div v-loading="loading" class="evidence-drawer-body">
      <el-alert
        v-if="error"
        type="error"
        :closable="false"
        show-icon
        title="证据链加载失败"
        description="请检查网络或稍后重试。"
      />

      <template v-if="evidence">
        <section class="ev-section">
          <h4 class="ev-section-title"><el-icon><InfoFilled /></el-icon> 基本信息</h4>
          <div class="ev-info-grid">
            <div class="ev-info-item">
              <span class="ev-info-label">生成 Agent</span>
              <span class="ev-info-value">{{ evidence.agent_name }}</span>
            </div>
            <div class="ev-info-item" v-if="evidence.agent_role">
              <span class="ev-info-label">角色</span>
              <span class="ev-info-value">{{ evidence.agent_role }}</span>
            </div>
            <div class="ev-info-item">
              <span class="ev-info-label">生成时间</span>
              <span class="ev-info-value">{{ formatTime(evidence.generated_at) }}</span>
            </div>
            <div class="ev-info-item">
              <span class="ev-info-label">版本 / Hash</span>
              <span class="ev-info-value mono">v{{ evidence.version }} · {{ evidence.content_hash || '—' }}</span>
            </div>
            <div class="ev-info-item">
              <span class="ev-info-label">最终决策</span>
              <el-tag size="small" :type="evidence.final_decision === 'publish' ? 'success' : evidence.final_decision === 'blocked' ? 'danger' : 'warning'" effect="plain">
                {{ decisionLabel(evidence.final_decision) }}
              </el-tag>
            </div>
            <div class="ev-info-item">
              <span class="ev-info-label">人工复核</span>
              <el-tag size="small" :type="evidence.human_review === 'approved' ? 'success' : evidence.human_review === 'pending' ? 'warning' : 'info'" effect="plain">
                {{ humanReviewLabel(evidence.human_review) }}
              </el-tag>
            </div>
          </div>
        </section>

        <section v-if="evidence.profile_summary" class="ev-section">
          <h4 class="ev-section-title"><el-icon><InfoFilled /></el-icon> 学生画像摘要</h4>
          <p class="ev-profile-text">{{ evidence.profile_summary }}</p>
        </section>

        <section class="ev-section">
          <h4 class="ev-section-title"><el-icon><Search /></el-icon> 知识库来源</h4>
          <div v-if="evidence.knowledge_chunks.length" class="ev-chunks">
            <div v-for="c in evidence.knowledge_chunks" :key="c.chunk_id" class="ev-chunk">
              <code class="ev-chunk-id">{{ c.chunk_id }}</code>
              <span v-if="c.title" class="ev-chunk-title">{{ c.title }}</span>
              <p v-if="c.snippet" class="ev-chunk-snippet">{{ c.snippet }}</p>
            </div>
          </div>
          <p v-else class="ev-empty-hint">未检索到知识库片段</p>
        </section>

        <section class="ev-section">
          <h4 class="ev-section-title"><el-icon><Lock /></el-icon> 生成证据时间线</h4>
          <div class="ev-timeline">
            <div
              v-for="(step, i) in evidence.timeline"
              :key="i"
              class="ev-timeline-item"
              :class="statusClass(step.status)"
            >
              <div class="ev-timeline-dot">
                <el-icon :size="14"><component :is="statusIcon(step.status)" /></el-icon>
              </div>
              <div class="ev-timeline-content">
                <div class="ev-timeline-head">
                  <span class="ev-timeline-stage">{{ stageLabel(step.stage) }}</span>
                  <el-tag size="small" :type="step.status === 'passed' ? 'success' : step.status === 'failed' ? 'danger' : 'warning'" effect="plain" class="ev-timeline-tag">
                    {{ step.status }}
                  </el-tag>
                </div>
                <span class="ev-timeline-agent">{{ step.agent }}</span>
                <p class="ev-timeline-detail">{{ step.detail }}</p>
              </div>
            </div>
          </div>
        </section>

        <section class="ev-section">
          <h4 class="ev-section-title">校验与安全状态</h4>
          <div class="ev-status-row">
            <div class="ev-status-item" :class="statusClass(evidence.verifier_status)">
              <el-icon><component :is="statusIcon(evidence.verifier_status)" /></el-icon>
              <span>ContentVerifier <strong>{{ evidence.verifier_status }}</strong></span>
            </div>
            <div class="ev-status-item" :class="statusClass(evidence.safety_status)">
              <el-icon><component :is="statusIcon(evidence.safety_status)" /></el-icon>
              <span>SafetyAgent <strong>{{ evidence.safety_status }}</strong></span>
            </div>
          </div>
          <div v-if="evidence.retry_count > 0" class="ev-retry-hint">
            <el-icon><Warning /></el-icon>
            发生 {{ evidence.retry_count }} 次重试
          </div>
        </section>

        <el-alert
          v-if="evidence.used_fallback"
          type="warning"
          :closable="false"
          show-icon
          title="模板降级生成"
          :description="evidence.fallback_reason || 'LLM 不可用，使用课程知识库模板降级生成。适合演示/离线场景，请勿当作大模型原创输出。'"
          class="ev-fallback-alert"
        />

        <section v-if="evidence.hallucination_risks.length || evidence.unsupported_claims.length" class="ev-section">
          <h4 class="ev-section-title">风险详情</h4>
          <div v-if="evidence.hallucination_risks.length" class="ev-risk-block ev-risk-hall">
            <h5>可能幻觉</h5>
            <ul>
              <li v-for="(r, i) in evidence.hallucination_risks" :key="`h-${i}`">{{ r }}</li>
            </ul>
          </div>
          <div v-if="evidence.unsupported_claims.length" class="ev-risk-block ev-risk-unsup">
            <h5>缺乏依据的表述</h5>
            <ul>
              <li v-for="(r, i) in evidence.unsupported_claims" :key="`u-${i}`">{{ r }}</li>
            </ul>
          </div>
        </section>
      </template>
    </div>
  </el-drawer>
</template>

<style scoped>
.evidence-drawer-body {
  padding: 0 4px;
}

.ev-section {
  margin-bottom: 20px;
}

.ev-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-primary);
}

.ev-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.ev-info-item {
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.ev-info-label {
  display: block;
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-bottom: 2px;
}

.ev-info-value {
  font-size: 13px;
  color: var(--alp-color-text);
  font-weight: 500;
}

.ev-info-value.mono {
  font-family: ui-monospace, monospace;
  font-size: 11px;
  font-weight: 400;
  word-break: break-all;
}

.ev-profile-text {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  font-size: 12px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.ev-chunks {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ev-chunk {
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.ev-chunk-id {
  font-size: 11px;
  font-family: ui-monospace, monospace;
  color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 12%, transparent);
  padding: 1px 6px;
  border-radius: 4px;
}

.ev-chunk-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin-left: 6px;
}

.ev-chunk-snippet {
  margin: 6px 0 0;
  font-size: 11px;
  line-height: 1.5;
  color: var(--alp-color-muted);
}

.ev-empty-hint {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.ev-timeline {
  position: relative;
  padding-left: 24px;
}

.ev-timeline::before {
  content: '';
  position: absolute;
  left: 9px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: var(--alp-color-border);
  border-radius: 1px;
}

.ev-timeline-item {
  position: relative;
  padding-bottom: 18px;
}

.ev-timeline-item:last-child {
  padding-bottom: 0;
}

.ev-timeline-dot {
  position: absolute;
  left: -24px;
  top: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.ev-passed .ev-timeline-dot {
  background: var(--alp-color-success);
  color: #fff;
}

.ev-warning .ev-timeline-dot {
  background: var(--alp-color-warning);
  color: #fff;
}

.ev-failed .ev-timeline-dot {
  background: var(--alp-color-danger);
  color: #fff;
}

.ev-timeline-content {
  padding-left: 4px;
}

.ev-timeline-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.ev-timeline-stage {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.ev-timeline-tag {
  font-size: 10px;
}

.ev-timeline-agent {
  font-size: 11px;
  color: var(--alp-color-muted);
  font-family: ui-monospace, monospace;
}

.ev-timeline-detail {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--alp-color-muted);
}

.ev-status-row {
  display: flex;
  gap: 12px;
}

.ev-status-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-size: 12px;
  color: var(--alp-color-text);
}

.ev-status-item.ev-passed {
  border-color: color-mix(in srgb, #4a8a5e 40%, var(--alp-color-border));
  color: var(--alp-color-success);
}

.ev-status-item.ev-warning {
  border-color: color-mix(in srgb, #9c7a3d 40%, var(--alp-color-border));
  color: var(--alp-color-warning);
}

.ev-status-item.ev-failed {
  border-color: color-mix(in srgb, #9e5a5a 40%, var(--alp-color-border));
  color: var(--alp-color-danger);
}

.ev-retry-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--alp-color-warning);
}

.ev-fallback-alert {
  margin-bottom: 16px;
}

.ev-risk-block {
  margin-bottom: 10px;
  font-size: 12px;
}

.ev-risk-block h5 {
  margin: 0 0 4px;
  font-size: 12px;
}

.ev-risk-block ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.6;
}

.ev-risk-hall {
  color: var(--alp-color-warning);
}

.ev-risk-unsup {
  color: var(--alp-color-muted);
}
</style>
