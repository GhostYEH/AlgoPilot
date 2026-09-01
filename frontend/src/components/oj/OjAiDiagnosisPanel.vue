<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowRight, CircleCheck, MagicStick, View, Warning } from '@element-plus/icons-vue'
import type { AiDiagnoseResponse } from '@/types/codeTrace'

const props = defineProps<{
  diagnosis: AiDiagnoseResponse | null
  loading?: boolean
  traceAvailable?: boolean
}>()

const emit = defineEmits<{ viewTrace: [] }>()
const revealedLevel = ref(1)
const detailsOpen = ref<string[]>(['exec-evidence'])

const guided = computed(() => props.diagnosis?.diagnosis ?? null)
const hints = computed(() => guided.value?.hints ?? [])
const nextHint = computed(() => hints.value.find((hint) => hint.level > revealedLevel.value))

watch(
  () => props.diagnosis,
  () => {
    revealedLevel.value = 1
    detailsOpen.value = []
  },
)

const confidenceMeta = computed(() => {
  const value = guided.value?.confidence
  if (value === 'high') return { label: '高置信度', type: 'success' as const }
  if (value === 'medium') return { label: '中等置信度', type: 'warning' as const }
  return { label: '线索级', type: 'info' as const }
})

const sourceMeta = computed(() => {
  const source = guided.value?.source ?? props.diagnosis?.edge_case.source ?? ''
  if (source === 'llm') return { label: 'Spark Lite 分析', type: 'success' as const }
  if (source.startsWith('rule:')) return { label: '专项规则验证', type: 'warning' as const }
  return { label: '规则兜底', type: 'info' as const }
})

const verdictMeta = computed(() => {
  const verdict = props.diagnosis?.edge_verdict ?? ''
  if (verdict === 'AC') return { label: '未复现错误', type: 'warning' as const }
  if (verdict === 'WA') return { label: '已复现 WA', type: 'danger' as const }
  if (verdict) return { label: `已复现 ${verdict}`, type: 'danger' as const }
  return { label: '等待验证', type: 'info' as const }
})

function revealNextHint() {
  if (nextHint.value) revealedLevel.value = Math.max(revealedLevel.value, nextHint.value.level)
}
</script>

<template>
  <section v-if="diagnosis || loading" v-loading="loading" class="ai-diagnosis" aria-live="polite">
    <header class="ai-diagnosis__head">
      <div class="ai-diagnosis__identity">
        <span class="ai-diagnosis__icon"><el-icon><MagicStick /></el-icon></span>
        <div>
          <h3>AI 诊断</h3>
          <p>先看证据，再逐层获得提示</p>
        </div>
      </div>
      <div v-if="diagnosis" class="ai-diagnosis__badges">
        <el-tag size="small" :type="verdictMeta.type">{{ verdictMeta.label }}</el-tag>
        <el-tag size="small" :type="confidenceMeta.type" effect="plain">
          {{ confidenceMeta.label }}
        </el-tag>
        <el-tag size="small" :type="sourceMeta.type" effect="plain">{{ sourceMeta.label }}</el-tag>
      </div>
    </header>

    <template v-if="diagnosis">
      <div v-if="guided" class="ai-diagnosis__focus">
        <div class="ai-diagnosis__focus-top">
          <span class="ai-diagnosis__eyebrow">最早可疑位置</span>
          <span class="ai-diagnosis__location">
            Step {{ guided.bug_step_index + 1 }}
            <template v-if="guided.bug_line"> · 第 {{ guided.bug_line }} 行</template>
          </span>
        </div>
        <h4>{{ guided.title }}</h4>
        <div v-if="guided.observation_question" class="ai-diagnosis__question">
          <el-icon><Warning /></el-icon>
          <div>
            <strong>先想一想</strong>
            <p>{{ guided.observation_question }}</p>
          </div>
        </div>

        <div v-if="guided.actual_state || guided.expected_state" class="ai-diagnosis__evidence-grid">
          <div class="evidence-card evidence-card--actual">
            <span>Trace 实际状态</span>
            <p>{{ guided.actual_state || '轨迹未捕获到足够状态' }}</p>
          </div>
          <div class="evidence-card evidence-card--expected">
            <span>此处应满足</span>
            <p>{{ guided.expected_state || guided.invariant || '请结合题意手算此步状态' }}</p>
          </div>
        </div>
      </div>

      <div v-if="hints.length" class="ai-diagnosis__hints">
        <div class="section-heading">
          <div>
            <span>引导式提示</span>
            <small>按需展开，不直接给出完整答案</small>
          </div>
          <span class="hint-progress">L{{ revealedLevel }} / L{{ hints.length }}</span>
        </div>

        <article
          v-for="hint in hints.filter((item) => item.level <= revealedLevel)"
          :key="hint.level"
          class="hint-card"
          :class="`hint-card--${hint.level}`"
        >
          <span class="hint-card__level">L{{ hint.level }}</span>
          <div>
            <strong>{{ hint.title }}</strong>
            <p>{{ hint.content }}</p>
          </div>
        </article>

        <el-button v-if="nextHint" plain class="reveal-button" @click="revealNextHint">
          我还需要一点提示
          <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>

      <div v-if="guided && revealedLevel >= 2" class="ai-diagnosis__conclusion">
        <div class="section-heading"><span>为什么会错</span></div>
        <p>{{ guided.root_cause }}</p>
        <div v-if="guided.invariant" class="invariant-line">
          <strong>被破坏的不变量：</strong>{{ guided.invariant }}
        </div>
      </div>

      <div v-if="guided && revealedLevel >= 3" class="ai-diagnosis__next-step">
        <div>
          <span>修改方向</span>
          <p>{{ guided.fix_direction || '只调整首次破坏不变量的语句，再重新验证。' }}</p>
        </div>
        <div>
          <span>如何验证</span>
          <p>{{ guided.verification }}</p>
        </div>
      </div>

      <div class="ai-diagnosis__actions">
        <el-button
          v-if="traceAvailable"
          type="primary"
          plain
          :icon="View"
          @click="emit('viewTrace')"
        >
          查看关键步骤的执行证据
        </el-button>
        <span v-if="guided">将自动定位到 Step {{ guided.bug_step_index + 1 }}</span>
      </div>

      <el-collapse v-model="detailsOpen" class="ai-diagnosis__details">
        <el-collapse-item name="evidence" title="诊断测例与复杂度（展开查看）">
          <div class="detail-grid">
            <div class="detail-card">
              <span>本次诊断输入</span>
              <code>{{ diagnosis.edge_case.input_preview || '无输入预览' }}</code>
              <p>{{ diagnosis.edge_case.reason }}</p>
            </div>
            <div class="detail-card">
              <span>复杂度观察</span>
              <strong>{{ diagnosis.complexity?.estimated_complexity ?? '未分析' }}</strong>
              <p>{{ diagnosis.complexity?.report ?? '' }}</p>
            </div>
          </div>
        </el-collapse-item>

        <el-collapse-item
          v-if="diagnosis.execution_evidence || diagnosis.first_divergence || diagnosis.counterexample"
          name="exec-evidence"
          title="执行证据链（展开查看）"
        >
          <!-- 失败测试用例 -->
          <div v-if="diagnosis.execution_evidence?.failed_test_cases?.length" class="evidence-failed-cases">
            <div class="section-heading">
              <span>失败测试用例</span>
              <small>共 {{ diagnosis.execution_evidence.failed_test_cases.length }} 个</small>
            </div>
            <div
              v-for="(tc, idx) in diagnosis.execution_evidence.failed_test_cases.slice(0, 3)"
              :key="idx"
              class="detail-card"
            >
              <span>用例 #{{ (tc as Record<string, unknown>).index ?? idx }}</span>
              <code>输入: {{ String((tc as Record<string, unknown>).input_preview ?? '').slice(0, 100) }}</code>
              <code>期望: {{ String((tc as Record<string, unknown>).expected_output ?? '').slice(0, 100) }}</code>
              <code>实际: {{ String((tc as Record<string, unknown>).actual_output ?? '').slice(0, 100) }}</code>
            </div>
          </div>

          <!-- First Divergence -->
          <div class="evidence-fd">
            <div class="section-heading">
              <span>首次状态偏离</span>
              <small v-if="diagnosis.first_divergence?.detected">
                Step {{ diagnosis.first_divergence.step_index }} · 变量 {{ diagnosis.first_divergence.divergent_variable }}
              </small>
            </div>
            <template v-if="diagnosis.first_divergence?.detected">
              <div class="detail-grid">
                <div class="evidence-card evidence-card--actual">
                  <span>学生状态</span>
                  <p>{{ diagnosis.first_divergence.student_state }}</p>
                </div>
                <div class="evidence-card evidence-card--expected">
                  <span>参考状态</span>
                  <p>{{ diagnosis.first_divergence.reference_state }}</p>
                </div>
              </div>
              <p class="evidence-fd__explanation">{{ diagnosis.first_divergence.explanation }}</p>
            </template>
            <p v-else class="evidence-fd__fallback">
              {{ diagnosis.first_divergence?.reason || '暂未找到可靠的首次状态偏离点（可能缺少参考解或执行轨迹不可比较）' }}
            </p>
          </div>

          <!-- Bug 分类与可疑行 -->
          <div v-if="diagnosis.execution_evidence?.bug_diagnosis" class="detail-grid">
            <div class="detail-card">
              <span>Bug 类型</span>
              <strong>{{ diagnosis.execution_evidence.bug_diagnosis?.bug_type_label || diagnosis.execution_evidence.bug_diagnosis?.bug_type || '暂未确定错误类型' }}</strong>
              <p v-if="diagnosis.execution_evidence.bug_diagnosis?.root_cause">
                {{ String(diagnosis.execution_evidence.bug_diagnosis.root_cause).slice(0, 200) }}
              </p>
            </div>
            <div class="detail-card">
              <span>可疑代码行</span>
              <code>{{
                Array.isArray(diagnosis.execution_evidence.bug_diagnosis?.suspicious_lines)
                  ? (diagnosis.execution_evidence.bug_diagnosis.suspicious_lines as number[]).join(', ')
                  : '未定位'
              }}</code>
              <p v-if="diagnosis.execution_evidence.bug_diagnosis?.confidence">
                置信度: {{ diagnosis.execution_evidence.bug_diagnosis.confidence }}
              </p>
            </div>
          </div>

          <!-- Counterexample -->
          <div v-if="diagnosis.counterexample" class="evidence-ce">
            <div class="section-heading">
              <span>反例生成</span>
              <small>{{ diagnosis.counterexample.source === 'generated_verified' ? '已验证反例' : '保留原始失败样例' }}</small>
            </div>
            <div class="detail-grid">
              <div class="detail-card">
                <span>候选数 / 验证数</span>
                <strong>{{ diagnosis.counterexample.candidate_count }} / {{ diagnosis.counterexample.verified_count }}</strong>
              </div>
              <div class="detail-card">
                <span>耗时</span>
                <strong>{{ diagnosis.counterexample.latency_ms }} ms</strong>
              </div>
            </div>
            <p v-if="diagnosis.counterexample.reason">{{ diagnosis.counterexample.reason }}</p>
          </div>
        </el-collapse-item>
      </el-collapse>

      <footer v-if="diagnosis.tutoring" class="ai-diagnosis__learning-receipt">
        <el-icon><CircleCheck /></el-icon>
        <span>
          {{ diagnosis.tutoring.matched_skill?.name || '本题错因' }}已纳入学习建议
          <template v-if="diagnosis.tutoring.memory_recorded">，并写入个人错题记忆</template>
        </span>
      </footer>
    </template>
  </section>
</template>

<style scoped>
.ai-diagnosis {
  margin-top: 12px;
  padding: 18px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 32%, var(--alp-color-border));
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface-muted);
}

.ai-diagnosis__head,
.ai-diagnosis__identity,
.ai-diagnosis__badges,
.ai-diagnosis__focus-top,
.section-heading,
.ai-diagnosis__actions,
.ai-diagnosis__learning-receipt {
  display: flex;
  align-items: center;
}

.ai-diagnosis__head { justify-content: space-between; gap: 14px; margin-bottom: 14px; flex-wrap: wrap; }
.ai-diagnosis__identity { gap: 10px; }
.ai-diagnosis__icon { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 10px; color: #fff; background: var(--el-color-primary); }
.ai-diagnosis__identity h3 { margin: 0; font-size: 17px; }
.ai-diagnosis__identity p { margin: 2px 0 0; font-size: 12px; color: var(--el-text-color-secondary); }
.ai-diagnosis__badges { gap: 6px; flex-wrap: wrap; }
.ai-diagnosis__focus { padding: 16px; border-radius: 12px; border: 1px solid var(--alp-color-border); background: var(--alp-bg-surface); }
.ai-diagnosis__focus-top { justify-content: space-between; gap: 12px; }
.ai-diagnosis__eyebrow { color: var(--el-color-danger); font-size: 12px; font-weight: 700; letter-spacing: .04em; }
.ai-diagnosis__location { font: 12px ui-monospace, Consolas, monospace; color: var(--el-text-color-secondary); }
.ai-diagnosis__focus h4 { margin: 8px 0 14px; font-size: 18px; line-height: 1.45; }
.ai-diagnosis__question { display: flex; gap: 10px; padding: 12px; border-radius: 10px; color: var(--el-color-primary); background: color-mix(in srgb, var(--el-color-primary) 8%, var(--alp-bg-surface)); }
.ai-diagnosis__question strong { font-size: 13px; }
.ai-diagnosis__question p { margin: 3px 0 0; color: var(--el-text-color-primary); line-height: 1.6; }

.ai-diagnosis__evidence-grid,
.detail-grid,
.ai-diagnosis__next-step { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.evidence-card,
.detail-card,
.ai-diagnosis__next-step > div { padding: 12px; border-radius: 10px; border: 1px solid var(--alp-color-border); background: var(--alp-bg-surface-muted); }
.evidence-card > span,
.detail-card > span,
.ai-diagnosis__next-step span { display: block; margin-bottom: 6px; font-size: 12px; font-weight: 700; color: var(--el-text-color-secondary); }
.evidence-card p,
.detail-card p,
.ai-diagnosis__next-step p { margin: 0; font-size: 13px; line-height: 1.65; }
.evidence-card--actual { border-left: 3px solid var(--el-color-danger); }
.evidence-card--expected { border-left: 3px solid var(--el-color-success); }

.ai-diagnosis__hints,
.ai-diagnosis__conclusion { margin-top: 14px; padding: 14px; border: 1px solid var(--alp-color-border); border-radius: 12px; background: var(--alp-bg-surface); }
.section-heading { justify-content: space-between; gap: 10px; margin-bottom: 10px; font-size: 14px; font-weight: 700; }
.section-heading > div { display: flex; flex-direction: column; }
.section-heading small { margin-top: 2px; font-size: 11px; font-weight: 400; color: var(--el-text-color-placeholder); }
.hint-progress { font: 12px ui-monospace, Consolas, monospace; color: var(--el-color-primary); }
.hint-card { display: flex; gap: 10px; margin-top: 8px; padding: 11px 12px; border-radius: 9px; background: var(--alp-bg-surface-muted); }
.hint-card__level { flex: 0 0 auto; color: var(--el-color-primary); font: 700 12px ui-monospace, Consolas, monospace; }
.hint-card strong { font-size: 13px; }
.hint-card p { margin: 3px 0 0; font-size: 13px; line-height: 1.6; }
.hint-card--3 { background: color-mix(in srgb, var(--el-color-warning) 9%, var(--alp-bg-surface-muted)); }
.reveal-button { margin-top: 10px; width: 100%; }

.ai-diagnosis__conclusion p { margin: 0; font-size: 13px; line-height: 1.7; }
.invariant-line { margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--alp-color-border); font-size: 13px; line-height: 1.6; }
.ai-diagnosis__actions { gap: 10px; margin-top: 14px; flex-wrap: wrap; }
.ai-diagnosis__actions span { font-size: 12px; color: var(--el-text-color-secondary); }
.ai-diagnosis__details { margin-top: 12px; }
.detail-card code { display: block; max-height: 72px; overflow: auto; white-space: pre-wrap; font-size: 12px; }
.detail-card strong { display: block; margin-bottom: 6px; color: var(--el-color-primary); }
.ai-diagnosis__learning-receipt { gap: 7px; margin-top: 10px; color: var(--el-color-success); font-size: 12px; }

.evidence-failed-cases, .evidence-fd, .evidence-ce { margin-top: 12px; padding-top: 10px; border-top: 1px dashed var(--alp-color-border); }
.evidence-fd__explanation { margin: 8px 0 0; font-size: 13px; line-height: 1.6; color: var(--el-text-color-regular); }
.evidence-fd__fallback { margin: 8px 0 0; font-size: 13px; line-height: 1.6; color: var(--el-text-color-secondary); font-style: italic; }
.evidence-ce p { margin: 6px 0 0; font-size: 12px; color: var(--el-text-color-secondary); }

@media (max-width: 760px) {
  .ai-diagnosis__evidence-grid,
  .detail-grid,
  .ai-diagnosis__next-step { grid-template-columns: 1fr; }
}
</style>
