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
  fetchResources,
  RESOURCE_TYPE_META,
  streamGenerateAllResources,
  type GeneratedResource,
} from '@/api/orchestrator'
import { ALGORITHM_MODULES } from '@/constants/modules'

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
          if (p.total > 0) {
            progressPercent.value = Math.round((p.step / p.total) * 100)
          }
          progressText.value = `${p.label}（${p.agent_name}）`
        },
        onResource: (r) => {
          resources.value = [r, ...resources.value.filter((x) => x.id !== r.id)]
        },
        onDone: (info) => {
          if (info?.partial_failure) {
            ElMessage.warning('部分资源生成失败，已展示成功生成的资源')
          } else {
            ElMessage.success('教学资源生成完成')
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
    progressText.value = ''
    progressPercent.value = 0
  }
}

function openPreview(r: GeneratedResource) {
  previewResource.value = r
  previewVisible.value = true
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
            <span class="resource-date">{{ formatDate(r.created_at) }}</span>
          </div>
          <h3 class="resource-title">{{ r.title }}</h3>
          <p class="resource-excerpt">{{ r.content.slice(0, 120) }}{{ r.content.length > 120 ? '...' : '' }}</p>
          <div class="resource-footer">
            <span class="resource-agent">{{ r.agent_name }}</span>
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
      size="640px"
      :title="previewResource?.title || '资源预览'"
      direction="rtl"
    >
      <div v-if="previewResource" class="preview-content">
        <div class="preview-meta">
          <el-tag size="small" effect="plain">
            {{ RESOURCE_TYPE_META[previewResource.resource_type]?.label || previewResource.resource_type }}
          </el-tag>
          <el-tag size="small" type="info" effect="plain">
            {{ previewResource.agent_name }}
          </el-tag>
          <span class="preview-date">{{ formatDate(previewResource.created_at) }}</span>
        </div>
        <div class="preview-body" v-html="previewResource.content" />
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
  filter: brightness(1.04);
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
  transition: transform 0.2s ease, border-color 0.2s ease, filter var(--alp-transition-fast);
}

.resource-card:hover {
  transform: translateY(-2px);
  border-color: var(--alp-color-primary);
  box-shadow: var(--alp-shadow-card-hover);
  filter: brightness(1.06);
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
  flex: 1;
  margin: 0 0 12px;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.6;
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
</style>
