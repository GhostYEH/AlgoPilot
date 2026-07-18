<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Document,
  EditPen,
  MagicStick,
  Monitor,
  Reading,
  RefreshRight,
  Share,
  VideoCamera,
  View,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  fetchResourceEvidence,
  fetchResources,
  RESOURCE_TYPE_META,
  streamGenerateAllResources,
  type GeneratedResource,
  type TrustEvidence,
} from '@/api/orchestrator'
import { ALGORITHM_MODULES, generationPresetForModule } from '@/constants/modules'
import ResourceContentPreview from '@/components/resources/ResourceContentPreview.vue'
import { verificationDisplayTag } from '@/utils/verification'

const loading = ref(false)
const generating = ref(false)
const resources = ref<GeneratedResource[]>([])
const topic = ref('数据结构与算法')
const selectedModule = ref('')
const focusHint = ref('')
const progressPercent = ref(0)
const progressText = ref('')
const previewVisible = ref(false)
const previewResource = ref<GeneratedResource | null>(null)
const previewEvidence = ref<TrustEvidence | null>(null)
const previewEvidenceLoading = ref(false)

const TYPE_ICONS: Record<string, typeof Document> = {
  document: Document,
  mindmap: Share,
  exercises: EditPen,
  reading: Reading,
  code_case: Monitor,
  trace_animation: VideoCamera,
}

const availableTypes = computed(() =>
  Object.entries(RESOURCE_TYPE_META).map(([key, meta]) => ({
    key,
    label: meta.label,
    agentName: meta.agentName,
    color: meta.color,
    icon: TYPE_ICONS[key] || Document,
  })),
)

const moduleOptions = computed(() =>
  ALGORITHM_MODULES.map((m) => ({ value: m.key, label: m.label })),
)

function applyModulePreset(moduleKey: string) {
  const preset = generationPresetForModule(moduleKey)
  if (!preset) return
  topic.value = preset.topic
  focusHint.value = preset.focusHint
}

function formatDate(value: string): string {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function parseEmbeddedJson(text: string): Record<string, unknown> | null {
  const start = text.indexOf('{')
  if (start < 0) return null
  let depth = 0
  let inString = false
  let escaped = false

  for (let index = start; index < text.length; index += 1) {
    const char = text[index]
    if (escaped) {
      escaped = false
      continue
    }
    if (char === '\\' && inString) {
      escaped = true
      continue
    }
    if (char === '"') {
      inString = !inString
      continue
    }
    if (inString) continue
    if (char === '{' || char === '[') depth += 1
    if (char === '}' || char === ']') depth -= 1
    if (depth === 0) {
      try {
        return JSON.parse(text.slice(start, index + 1)) as Record<string, unknown>
      } catch {
        return null
      }
    }
  }
  return null
}

function resourceSummary(resource: GeneratedResource): string {
  const content = resource.content?.trim()
  if (!content) return '内容已生成，点击查看完整资源。'

  const cleaned = content
    .replace(/```(?:json|markdown|md)?/gi, '')
    .replace(/---\*\*依据知识库[\s\S]*$/i, '')
    .replace(/^#+\s*/gm, '')
    .trim()

  const parsed = parseEmbeddedJson(cleaned)
  if (parsed) {
    const candidates = [
      parsed.reading_goal,
      parsed.title,
      parsed.summary,
      parsed.narration_hint,
      parsed.description,
    ]
    const summary = candidates.find((item) => typeof item === 'string' && item.trim())
    if (typeof summary === 'string') return summary.trim()

    const narrative = parsed.domain_narrative
    if (narrative && typeof narrative === 'object') {
      const domainNarrative = narrative as Record<string, unknown>
      const narrativeSummary = [domainNarrative.headline, domainNarrative.story].find(
        (item) => typeof item === 'string' && item.trim(),
      )
      if (typeof narrativeSummary === 'string') return narrativeSummary.trim()
    }

    if (Array.isArray(parsed.levels)) {
      return `包含 ${parsed.levels.length} 个阅读层级，已按学习基础组织内容与读后任务。`
    }
    if (Array.isArray(parsed.questions)) {
      return `包含 ${parsed.questions.length} 道分层练习题，支持作答、提示与教学聚焦。`
    }
  }

  if (cleaned.startsWith('{') || cleaned.startsWith('[')) {
    return '结构化教学资源已生成，内容整理完成后可查看。'
  }

  const plain = cleaned
    .replace(/\{[\s\S]*?\}/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[*_`>#\[\]]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
  return plain.slice(0, 96) || '结构化教学资源已生成，点击查看完整内容。'
}

async function loadResources() {
  loading.value = true
  try {
    resources.value = await fetchResources()
  } catch {
    ElMessage.error('已有资源加载失败')
  } finally {
    loading.value = false
  }
}

async function generateAll() {
  if (generating.value) return
  if (!selectedModule.value) {
    ElMessage.warning('请先选择知识模块，再生成教学资源')
    return
  }
  if (!topic.value.trim()) {
    ElMessage.warning('请填写与知识模块一致的教学主题')
    return
  }
  generating.value = true
  progressPercent.value = 0
  progressText.value = '正在初始化多智能体流水线...'

  try {
    await streamGenerateAllResources(
      {
        topic: topic.value || '数据结构与算法',
        module_key: selectedModule.value || undefined,
        focus_hint: focusHint.value || undefined,
      },
      {
        onProgress: (p) => {
          if (typeof p.percent === 'number') {
            progressPercent.value = Math.max(0, Math.min(100, Math.round(p.percent)))
          } else if (p.total > 0) {
            progressPercent.value = Math.round((p.step / p.total) * 100)
          }
          progressText.value = `${p.label}（${p.agent_name}）`
        },
        onResource: (r) => {
          resources.value = [r, ...resources.value.filter((x) => x.id !== r.id)]
        },
        onDone: (info) => {
          progressPercent.value = 100
          progressText.value = ''
          if (info?.fallback_mode) {
            ElMessage.warning(
              '当前为无模型 Key 的模板降级资源，配置 AI 模型 API Key 后可生成更高质量内容。',
            )
          } else if (info?.partial_failure) {
            const failed = info.errors
              ?.map((e) => e.agent_name ?? e.resource_type ?? '未知')
              .join('、') ?? '部分资源'
            ElMessage.warning(`${failed} 生成失败，其余资源已就绪`)
          } else {
            ElMessage.success('教学资源生成完成')
          }
          void loadResources()
        },
        onHeartbeat: (info) => {
          if (info.message) progressText.value = info.message
          if (typeof info.percent === 'number') {
            progressPercent.value = Math.max(0, Math.min(100, Math.round(info.percent)))
          }
        },
        onError: (msg) => {
          ElMessage.error(msg || '资源生成失败')
        },
      },
    )
  } catch {
    ElMessage.error('资源生成请求失败，请确认后端服务已启动')
  } finally {
    generating.value = false
  }
}

function openPreview(r: GeneratedResource) {
  previewResource.value = r
  previewEvidence.value = null
  previewVisible.value = true
  void loadPreviewEvidence(r.id)
}

async function loadPreviewEvidence(resourceId: number) {
  previewEvidenceLoading.value = true
  try {
    previewEvidence.value = await fetchResourceEvidence(resourceId)
  } catch {
    previewEvidence.value = null
  } finally {
    previewEvidenceLoading.value = false
  }
}

function resourceVerifyTag(resource: GeneratedResource): {
  label: string
  type: 'success' | 'warning' | 'danger' | 'info'
} {
  const meta = (resource.meta ?? {}) as Record<string, unknown>
  const tag = verificationDisplayTag(meta)
  return { label: tag.label, type: tag.type }
}

onMounted(loadResources)
</script>

<template>
  <main class="teacher-workbench">
    <section class="dashboard-hero">
      <div class="hero-copy">
        <div class="hero-kicker">
          <el-icon><MagicStick /></el-icon>
          AlgoPilot 教学资源工作台
        </div>
        <h1>教学资源智能生成</h1>
        <p>
          面向教师的多智能体资源生成工作台，按模块一键生成概念讲解、思维导图、
          分层题单、代码沙盒、轨迹动画与分层阅读等教学素材，支持聚焦补讲重点。
        </p>
        <div class="hero-meta">
          <span>已生成资源：{{ resources.length }} 份</span>
          <span>智能体：6 个角色 Agent</span>
        </div>
      </div>
      <div class="hero-actions">
        <el-button :loading="loading" :icon="RefreshRight" @click="loadResources">
          刷新列表
        </el-button>
      </div>
    </section>

    <section class="dashboard-section">
      <div class="section-heading">
        <div>
          <span class="section-eyebrow">GENERATE</span>
          <h2>生成教学资源</h2>
        </div>
        <span class="section-caption">选择模块并填写教学聚焦点后一键生成</span>
      </div>

      <div class="generate-panel">
        <div class="form-row">
          <label class="form-label">教学主题</label>
          <el-input
            v-model="topic"
            placeholder="如：数据结构与算法"
            clearable
          />
        </div>
        <div class="form-row">
          <label class="form-label">知识模块</label>
          <el-select
            v-model="selectedModule"
            placeholder="选择模块（可选）"
            clearable
            style="width: 100%"
            @change="applyModulePreset"
          >
            <el-option
              v-for="mod in moduleOptions"
              :key="mod.value"
              :label="mod.label"
              :value="mod.value"
            />
          </el-select>
        </div>
        <div class="form-row">
          <label class="form-label">教学聚焦点</label>
          <el-input
            v-model="focusHint"
            type="textarea"
            :rows="2"
            placeholder="如：针对链表指针更新错误，侧重三指针过程图解与边界检查"
            clearable
          />
        </div>

        <div class="type-grid">
          <div
            v-for="t in availableTypes"
            :key="t.key"
            class="type-card"
          >
            <div class="type-icon" :style="{ color: t.color, background: `${t.color}1a` }">
              <el-icon><component :is="t.icon" /></el-icon>
            </div>
            <div class="type-info">
              <strong>{{ t.label }}</strong>
              <span>{{ t.agentName }}</span>
            </div>
          </div>
        </div>

        <div v-if="generating" class="progress-bar">
          <div class="progress-info">
            <span>{{ progressText }}</span>
            <span>{{ progressPercent }}%</span>
          </div>
          <el-progress
            :percentage="progressPercent"
            :stroke-width="8"
            :show-text="false"
            :duration="0.5"
          />
        </div>

        <div class="generate-actions">
          <el-button
            type="primary"
            size="large"
            :loading="generating"
            :icon="MagicStick"
            @click="generateAll"
          >
            {{ generating ? '生成中...' : '一键生成全部教学资源' }}
          </el-button>
        </div>
      </div>
    </section>

    <section class="dashboard-section">
      <div class="section-heading">
        <div>
          <span class="section-eyebrow">RESOURCES</span>
          <h2>已生成教学资源</h2>
        </div>
        <span class="section-caption">点击卡片可预览内容</span>
      </div>

      <div v-if="loading" class="loading-card">
        <el-skeleton :rows="6" animated />
      </div>

      <div v-else-if="resources.length" class="resource-grid">
        <article
          v-for="r in resources"
          :key="r.id"
          class="resource-card"
          @click="openPreview(r)"
        >
          <div class="resource-header">
            <div class="resource-type-badge" :style="{ color: RESOURCE_TYPE_META[r.resource_type]?.color || '#3a8a9e' }">
              <el-icon><component :is="TYPE_ICONS[r.resource_type] || Document" /></el-icon>
              <span>{{ RESOURCE_TYPE_META[r.resource_type]?.label || r.resource_type }}</span>
            </div>
            <el-tag
              size="small"
              :type="resourceVerifyTag(r).type"
              effect="plain"
              class="resource-verify-tag"
            >
              {{ resourceVerifyTag(r).label }}
            </el-tag>
          </div>
          <h3 class="resource-title">{{ r.title }}</h3>
          <p class="resource-excerpt">{{ resourceSummary(r) }}</p>
          <div class="resource-footer">
            <span class="resource-agent">{{ r.agent_name }}</span>
            <span class="resource-date">{{ formatDate(r.created_at) }}</span>
            <el-button size="small" text :icon="View">预览</el-button>
          </div>
        </article>
      </div>

      <el-empty
        v-else
        description="暂无教学资源，选择模块后点击上方按钮生成"
        :image-size="100"
      />
    </section>

    <!-- 资源预览抽屉 -->
    <el-drawer
      v-model="previewVisible"
      size="min(860px, 94vw)"
      :title="previewResource?.title || '资源预览'"
      direction="rtl"
      destroy-on-close
      class="resource-preview-drawer"
    >
      <div v-if="previewResource" class="preview-content">
        <div class="preview-meta">
          <el-tag size="small" effect="plain">
            {{ RESOURCE_TYPE_META[previewResource.resource_type]?.label || previewResource.resource_type }}
          </el-tag>
          <el-tag size="small" type="info" effect="plain">
            {{ previewResource.agent_name }}
          </el-tag>
          <el-tag
            v-if="previewEvidence"
            size="small"
            :type="previewEvidence.final_decision === 'publish' ? 'success' : previewEvidence.final_decision === 'blocked' ? 'danger' : 'warning'"
            effect="plain"
          >
            {{ previewEvidence.final_decision === 'publish' ? '已发布' : previewEvidence.final_decision === 'blocked' ? '已屏蔽' : '待复核' }}
          </el-tag>
          <span class="preview-date">{{ formatDate(previewResource.created_at) }}</span>
        </div>
        <ResourceContentPreview
          :resource-type="previewResource.resource_type"
          :content="previewResource.content"
          :meta="previewResource.meta"
        />

        <!-- 信任证据面板 -->
        <el-card
          v-loading="previewEvidenceLoading"
          class="evidence-card"
          shadow="never"
        >
          <template #header>
            <div class="evidence-header">
              <span>信任证据链 · Trust Evidence</span>
              <el-tag
                v-if="previewEvidence"
                size="small"
                :type="previewEvidence.used_fallback ? 'warning' : 'success'"
                effect="plain"
              >
                {{ previewEvidence.used_fallback ? '模板降级' : 'LLM 生成' }}
              </el-tag>
            </div>
          </template>

          <div v-if="previewEvidence" class="evidence-body">
            <div class="evidence-row">
              <span class="evidence-label">校验状态</span>
              <el-tag
                size="small"
                :type="previewEvidence.verifier_status === 'passed' ? 'success' : previewEvidence.verifier_status === 'failed' ? 'danger' : 'warning'"
              >
                {{ previewEvidence.verifier_status === 'passed' ? '通过' : previewEvidence.verifier_status === 'failed' ? '未通过' : '告警' }}
              </el-tag>
              <span class="evidence-label">安全审查</span>
              <el-tag
                size="small"
                :type="previewEvidence.safety_status === 'passed' ? 'success' : previewEvidence.safety_status === 'failed' ? 'danger' : 'warning'"
              >
                {{ previewEvidence.safety_status === 'passed' ? '通过' : previewEvidence.safety_status === 'failed' ? '未通过' : '告警' }}
              </el-tag>
              <span class="evidence-label">重试次数</span>
              <span class="evidence-value">{{ previewEvidence.retry_count }}</span>
            </div>

            <div v-if="previewEvidence.fallback_reason" class="evidence-row">
              <span class="evidence-label">降级原因</span>
              <span class="evidence-value">{{ previewEvidence.fallback_reason }}</span>
            </div>

            <div class="evidence-row">
              <span class="evidence-label">内容哈希</span>
              <span class="evidence-value evidence-hash">{{ previewEvidence.content_hash }}</span>
              <span class="evidence-label">版本</span>
              <span class="evidence-value">v{{ previewEvidence.version }}</span>
            </div>

            <div v-if="previewEvidence.profile_summary" class="evidence-row evidence-summary">
              <span class="evidence-label">画像摘要</span>
              <span class="evidence-value">{{ previewEvidence.profile_summary }}</span>
            </div>

            <div v-if="previewEvidence.knowledge_chunks.length" class="evidence-section">
              <h4 class="evidence-section-title">知识库切片（{{ previewEvidence.knowledge_chunks.length }}）</h4>
              <div
                v-for="(chunk, idx) in previewEvidence.knowledge_chunks"
                :key="chunk.chunk_id || idx"
                class="knowledge-chunk"
              >
                <div class="chunk-head">
                  <span class="chunk-title">{{ chunk.title || chunk.chunk_id }}</span>
                  <span v-if="typeof chunk.relevance_score === 'number'" class="chunk-score">
                    相关度 {{ (chunk.relevance_score * 100).toFixed(0) }}%
                  </span>
                </div>
                <p v-if="chunk.snippet" class="chunk-snippet">{{ chunk.snippet }}</p>
                <p v-if="chunk.chapter_title || chunk.section_title" class="chunk-source">
                  {{ chunk.chapter_title }} · {{ chunk.section_title }}
                </p>
              </div>
            </div>

            <div v-if="previewEvidence.timeline.length" class="evidence-section">
              <h4 class="evidence-section-title">生成时间线</h4>
              <div class="timeline">
                <div
                  v-for="(t, idx) in previewEvidence.timeline"
                  :key="idx"
                  class="timeline-item"
                >
                  <span
                    class="timeline-dot"
                    :class="`timeline-dot--${t.status}`"
                  />
                  <div class="timeline-content">
                    <div class="timeline-head">
                      <span class="timeline-stage">{{ t.stage }}</span>
                      <span class="timeline-agent">{{ t.agent }}</span>
                      <el-tag
                        size="small"
                        :type="t.status === 'passed' ? 'success' : t.status === 'failed' ? 'danger' : 'warning'"
                      >
                        {{ t.status === 'passed' ? '通过' : t.status === 'failed' ? '失败' : '告警' }}
                      </el-tag>
                    </div>
                    <p v-if="t.detail" class="timeline-detail">{{ t.detail }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="previewEvidence.hallucination_risks.length" class="evidence-section">
              <h4 class="evidence-section-title evidence-warn">幻觉风险</h4>
              <ul class="risk-list">
                <li v-for="(risk, idx) in previewEvidence.hallucination_risks" :key="`risk-${idx}`">{{ risk }}</li>
              </ul>
            </div>

            <div v-if="previewEvidence.unsupported_claims.length" class="evidence-section">
              <h4 class="evidence-section-title evidence-warn">无证据支撑的声明</h4>
              <ul class="risk-list">
                <li v-for="(claim, idx) in previewEvidence.unsupported_claims" :key="`claim-${idx}`">{{ claim }}</li>
              </ul>
            </div>
          </div>

          <el-empty
            v-else-if="!previewEvidenceLoading"
            description="暂无信任证据数据"
            :image-size="80"
          />
        </el-card>
      </div>
    </el-drawer>
  </main>
</template>

<style scoped>
.teacher-workbench {
  width: min(1440px, 100%);
  margin: 0 auto;
  color: var(--alp-color-text);
}

.dashboard-hero {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 30px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 32%, var(--alp-color-border));
  border-radius: 18px;
  background:
    rgba(58, 138, 158, 0.2),
    rgba(14, 116, 144, 0.22),
    var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
}

.dashboard-hero::after {
  position: absolute;
  right: 8%;
  bottom: -90px;
  width: 260px;
  height: 260px;
  content: '';
  border: 1px solid rgba(34, 211, 238, 0.16);
  border-radius: 50%;
  box-shadow: 0 0 0 34px rgba(34, 211, 238, 0.04), 0 0 0 70px rgba(129, 140, 248, 0.03);
  pointer-events: none;
}

.hero-copy,
.hero-actions {
  position: relative;
  z-index: 1;
}

.hero-copy h1 {
  margin: 8px 0 10px;
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.15;
}

.hero-copy p {
  max-width: 760px;
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 15px;
  line-height: 1.8;
}

.hero-kicker,
.section-eyebrow {
  color: var(--alp-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 7px;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  margin-top: 18px;
  color: var(--alp-color-muted);
  font-size: 12px;
}

.hero-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.dashboard-section {
  margin-top: 28px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.section-heading h2 {
  margin: 4px 0 0;
  font-size: 20px;
}

.section-caption {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.generate-panel {
  padding: 24px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
}

.form-row {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  color: var(--alp-color-text);
  font-size: 13px;
  font-weight: 600;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 20px 0;
}

.type-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-sm);
  background: var(--alp-bg-surface-solid);
  transition: transform var(--alp-transition-fast), border-color var(--alp-transition-fast);
}

.type-card:hover {
  transform: translateY(-1px);
  border-color: var(--alp-color-primary);
}

.type-icon {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  place-items: center;
  border-radius: 10px;
  font-size: 18px;
}

.type-info strong {
  display: block;
  font-size: 13px;
}

.type-info span {
  display: block;
  color: var(--alp-color-muted);
  font-size: 11px;
}

.progress-bar {
  margin: 16px 0;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 24%, var(--alp-color-border));
  border-radius: var(--alp-radius-sm);
  background: color-mix(in srgb, var(--alp-color-primary) 6%, var(--alp-bg-surface));
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.generate-actions {
  display: flex;
  justify-content: center;
  padding-top: 4px;
}

.loading-card {
  padding: 24px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.resource-card {
  display: flex;
  flex-direction: column;
  padding: 18px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.resource-card:hover {
  transform: translateY(-2px);
  border-color: var(--alp-color-primary);
  box-shadow: var(--alp-shadow-card-hover);
}

.resource-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.resource-type-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
}

.resource-date {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.resource-title {
  margin: 0 0 8px;
  font-size: 15px;
  line-height: 1.4;
}

.resource-excerpt {
  display: -webkit-box;
  flex: 1;
  margin: 0 0 12px;
  overflow: hidden;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.resource-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px dashed var(--alp-color-border);
}

.resource-agent {
  color: var(--alp-color-muted);
  font-size: 11px;
}

/* 预览抽屉 */
.preview-content {
  padding: 0 4px;
}

.preview-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.preview-date {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.preview-body {
  font-size: 14px;
  line-height: 1.8;
  color: var(--alp-color-text);
  word-break: break-word;
}

.preview-body :deep(h1),
.preview-body :deep(h2),
.preview-body :deep(h3) {
  margin: 16px 0 8px;
  color: var(--alp-color-text);
}

.preview-body :deep(pre) {
  padding: 12px;
  overflow-x: auto;
  border-radius: var(--alp-radius-sm);
  background: var(--alp-bg-code-ish);
  font-size: 13px;
}

.preview-body :deep(code) {
  font-family: 'Cascadia Code', 'Fira Code', monospace;
}

.preview-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
}

.preview-body :deep(th),
.preview-body :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--alp-color-border);
}

@media (max-width: 1100px) {
  .type-grid,
  .resource-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .dashboard-hero,
  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .type-grid,
  .resource-grid {
    grid-template-columns: 1fr;
  }
}

.resource-verify-tag {
  flex-shrink: 0;
}

.evidence-card {
  margin-top: 20px;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
  background: var(--alp-bg-surface);
}

.evidence-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.evidence-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  font-size: 13px;
  line-height: 1.6;
}

.evidence-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.evidence-label {
  color: var(--alp-color-muted);
  font-size: 12px;
  min-width: 60px;
}

.evidence-value {
  color: var(--alp-color-text);
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
  word-break: break-all;
}

.evidence-hash {
  font-size: 11px;
  color: var(--alp-color-muted);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-summary .evidence-value {
  font-family: inherit;
  color: var(--alp-color-text);
}

.evidence-section {
  margin-top: 6px;
  padding-top: 12px;
  border-top: 1px dashed var(--alp-color-border);
}

.evidence-section-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.evidence-section-title.evidence-warn {
  color: var(--alp-color-warning);
}

.knowledge-chunk {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-left: 3px solid var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 5%, transparent);
  border-radius: 4px;
}

.chunk-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.chunk-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.chunk-score {
  font-size: 11px;
  color: var(--alp-color-primary);
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
}

.chunk-snippet {
  margin: 4px 0 2px;
  font-size: 12px;
  color: var(--alp-color-text-secondary);
  line-height: 1.5;
}

.chunk-source {
  margin: 0;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 6px;
}

.timeline-item {
  position: relative;
  display: flex;
  gap: 10px;
  padding-left: 14px;
}

.timeline-item::before {
  position: absolute;
  left: 4px;
  top: 18px;
  bottom: -12px;
  width: 1px;
  content: '';
  background: var(--alp-color-border);
}

.timeline-item:last-child::before {
  display: none;
}

.timeline-dot {
  position: absolute;
  left: 0;
  top: 6px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--alp-color-muted);
}

.timeline-dot--passed {
  background: var(--alp-color-success);
}

.timeline-dot--warning {
  background: var(--alp-color-warning);
}

.timeline-dot--failed {
  background: var(--alp-color-danger);
}

.timeline-content {
  flex: 1;
  min-width: 0;
}

.timeline-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.timeline-stage {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-text);
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
}

.timeline-agent {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.timeline-detail {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-text-secondary);
  line-height: 1.5;
}

.risk-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: var(--alp-color-text-secondary);
  line-height: 1.7;
}
</style>
