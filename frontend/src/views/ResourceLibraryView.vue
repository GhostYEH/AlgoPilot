<script setup lang="ts">
import { computed, onMounted, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Document,
  MagicStick,
  Search,
  Star,
  Delete,
  Share,
  EditPen,
  Reading,
  Monitor,
  VideoCamera,
  Box,
  CircleCheck,
  Clock,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteResource,
  fetchResources,
  resourceVerifyTag,
  RESOURCE_TYPE_META,
  setResourceFavorite,
  streamGenerateAllResources,
  streamGenerateResource,
  type GeneratedResource,
} from '@/api/orchestrator'
import { isLoggedIn } from '@/stores/auth'
import ResourceContentPreview from '@/components/resources/ResourceContentPreview.vue'

const TYPE_ICONS: Record<string, Component> = {
  document: Document,
  mindmap: Share,
  exercises: EditPen,
  reading: Reading,
  code_case: Monitor,
  video_script: VideoCamera,
}

const route = useRoute()
const router = useRouter()

const resources = ref<GeneratedResource[]>([])
const loading = ref(false)
const batchLoading = ref(false)
const generatingType = ref<string | null>(null)
const progressPercent = ref(0)
const progressText = ref('')
const topic = ref('数据结构与算法')
const focusHint = ref('')
const activeId = ref<number | null>(null)
const workflowLogs = ref<string[]>([])
const logFullscreen = ref(false)
const searchQuery = ref('')
const filterType = ref('')
const filterVerified = ref('')
const page = ref(1)
const pageSize = ref(8)

const activeResource = computed(() =>
  resources.value.find((r) => r.id === activeId.value) ?? null,
)

const filteredResources = computed(() => {
  let list = [...resources.value]
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      (r) =>
        r.title.toLowerCase().includes(q) ||
        r.agent_name.toLowerCase().includes(q) ||
        r.content.toLowerCase().includes(q),
    )
  }
  if (filterType.value) list = list.filter((r) => r.resource_type === filterType.value)
  if (filterVerified.value === 'verified') {
    list = list.filter((r) => r.meta?.verified === true || r.meta?.status === 'published')
  }
  if (filterVerified.value === 'draft') {
    list = list.filter((r) => r.meta?.status === 'draft' || r.meta?.verified === false)
  }
  if (filterVerified.value === 'favorite') {
    list = list.filter((r) => r.meta?.favorited === true)
  }
  return list
})

const pagedResources = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredResources.value.slice(start, start + pageSize.value)
})

const typeCards = computed(() =>
  Object.entries(RESOURCE_TYPE_META).map(([type, meta]) => ({
    type,
    ...meta,
    icon: TYPE_ICONS[type] ?? Document,
    latest: resources.value.find((r) => r.resource_type === type),
    generating: generatingType.value === type || (batchLoading.value && !generatingType.value),
  })),
)

const generatedCount = computed(() => typeCards.value.filter((c) => c.latest).length)

watch([searchQuery, filterType, filterVerified], () => {
  page.value = 1
})

watch(
  () => route.query.highlight,
  (val) => {
    const id = Number(val)
    if (!Number.isNaN(id) && id > 0) activeId.value = id
  },
)

function applyHighlightFromRoute() {
  const id = Number(route.query.highlight)
  if (!Number.isNaN(id) && id > 0) activeId.value = id
}

async function loadList() {
  if (!isLoggedIn.value) return
  try {
    resources.value = await fetchResources()
    applyHighlightFromRoute()
  } catch {
    resources.value = []
  }
}

onMounted(loadList)

function handleStreamError(_msg: string) {
  progressText.value = ''
}

async function onGenerateOne(type: string) {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后生成资源')
    void router.push({ name: 'login', query: { redirect: '/resources' } })
    return
  }
  loading.value = true
  generatingType.value = type
  workflowLogs.value = []
  progressPercent.value = 0
  progressText.value = `正在调用 ${RESOURCE_TYPE_META[type]?.agentName ?? 'Agent'}…`
  try {
    await streamGenerateResource(
      {
        resource_type: type,
        topic: topic.value,
        focus_hint: focusHint.value,
      },
      {
        onProgress(p) {
          if (typeof p.percent === 'number') progressPercent.value = p.percent
        },
        onWorkflow(w) {
          workflowLogs.value.push(
            `[${w.agent}] ${w.stage} · ${w.status} ${w.detail}${w.percent != null ? ` (${w.percent}%)` : ''}`,
          )
          if (typeof w.percent === 'number') progressPercent.value = w.percent
        },
        onResource(r) {
          resources.value = [r, ...resources.value.filter((x) => x.id !== r.id)]
          activeId.value = r.id
          const tag = resourceVerifyTag(r.meta ?? {})
          ElMessage.success(
            tag.type === 'warning'
              ? `${r.agent_name} 已保存为草稿（待校验，仅供参考）`
              : `${r.agent_name} 已生成并校验`,
          )
        },
        onError: handleStreamError,
      },
    )
  } finally {
    loading.value = false
    generatingType.value = null
    progressText.value = ''
    progressPercent.value = 0
  }
}

async function onGenerateAll() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    return
  }
  batchLoading.value = true
  workflowLogs.value = []
  progressPercent.value = 0
  progressText.value = 'DAG Pipeline：检索 → 生成 ⇄ 校验 → 安全 → 落库…'
  try {
    await streamGenerateAllResources(
      { topic: topic.value, focus_hint: focusHint.value },
      {
        onProgress(p) {
          progressText.value = `[${p.step}/${p.total}] ${p.agent_name} · ${p.label}`
          if (typeof p.percent === 'number') progressPercent.value = p.percent
        },
        onWorkflow(w) {
          workflowLogs.value.push(`[${w.agent}] ${w.stage} · ${w.status} ${w.detail}`)
        },
        onCollaboration(log) {
          for (const row of log) {
            workflowLogs.value.push(`[协作] ${row.agent} · ${row.action}: ${row.detail}`)
          }
        },
        onResource(r) {
          resources.value = [r, ...resources.value.filter((x) => x.id !== r.id)]
        },
        onDone() {
          ElMessage.success('六类资源已全部生成（含校验闭环）')
          progressPercent.value = 100
        },
        onError: handleStreamError,
      },
    )
    await loadList()
  } finally {
    batchLoading.value = false
    progressText.value = ''
  }
}

async function onDelete(r: GeneratedResource) {
  await ElMessageBox.confirm(`确定删除「${r.title}」？`, '删除资源')
  await deleteResource(r.id)
  resources.value = resources.value.filter((x) => x.id !== r.id)
  if (activeId.value === r.id) activeId.value = null
  ElMessage.success('已删除')
}

async function onToggleFavorite(r: GeneratedResource) {
  const next = !r.meta?.favorited
  const updated = await setResourceFavorite(r.id, next)
  resources.value = resources.value.map((x) => (x.id === updated.id ? updated : x))
}

function openResource(r: GeneratedResource) {
  activeId.value = r.id
}

function verifyTag(meta: Record<string, unknown>) {
  return resourceVerifyTag(meta)
}
</script>

<template>
  <div class="resource-page">
    <el-card shadow="never" class="page-card">
      <div class="page-header">
        <el-page-header title="个性化资源库" @back="router.push({ name: 'home' })" />
        <p class="page-desc">
          多智能体协同生成讲解文档、思维导图、题单、拓展阅读、代码案例与视频脚本；内容由编排层调度，基于你的学习画像。
        </p>
      </div>

      <el-alert v-if="!isLoggedIn" type="warning" show-icon :closable="false" class="login-alert">
        登录后可生成并保存资源到云端
      </el-alert>

      <div class="gen-panel">
        <div class="gen-panel-inner">
          <el-row :gutter="12" class="gen-row">
            <el-col :xs="24" :md="10">
              <label class="field-label">课程主题</label>
              <el-input v-model="topic" placeholder="如：数据结构与算法" size="large" />
            </el-col>
            <el-col :xs="24" :md="10">
              <label class="field-label">生成侧重</label>
              <el-input
                v-model="focusHint"
                placeholder="如：主攻链表与双指针"
                size="large"
              />
            </el-col>
            <el-col :xs="24" :md="4" class="gen-btn-col">
              <el-button
                type="primary"
                size="large"
                :icon="MagicStick"
                :loading="batchLoading"
                :disabled="!isLoggedIn"
                class="gen-all-btn"
                @click="onGenerateAll"
              >
                一键生成全部
              </el-button>
            </el-col>
          </el-row>
        </div>

        <div v-if="progressText || (loading || batchLoading)" class="progress-block">
          <div class="progress-header">
            <span class="progress-dot" :class="{ active: loading || batchLoading }" />
            <p class="progress-line">{{ progressText || '准备中…' }}</p>
          </div>
          <el-progress
            v-if="loading || batchLoading"
            :percentage="progressPercent"
            :stroke-width="10"
            striped
            striped-flow
            class="main-progress"
          />
        </div>
      </div>

      <div v-if="workflowLogs.length" class="workflow-toolbar">
        <span class="muted small">Workflow / 协作日志（{{ workflowLogs.length }} 条）</span>
        <el-button link type="primary" @click="logFullscreen = true">全屏查看</el-button>
      </div>
      <el-scrollbar v-if="workflowLogs.length && !logFullscreen" max-height="120" class="workflow-log">
        <div v-for="(line, i) in workflowLogs" :key="i" class="log-line">{{ line }}</div>
      </el-scrollbar>
      <el-drawer v-model="logFullscreen" title="Workflow 全屏日志" size="90%" direction="btt">
        <div v-for="(line, i) in workflowLogs" :key="i" class="log-line">{{ line }}</div>
      </el-drawer>

      <div class="agents-section">
        <div class="section-head">
          <h3 class="section-title">智能体矩阵</h3>
          <span class="section-badge">{{ generatedCount }} / 6 已生成</span>
        </div>
        <div class="type-grid">
          <div
            v-for="card in typeCards"
            :key="card.type"
            class="type-card"
            :class="{ 'is-generating': card.generating, 'has-resource': !!card.latest }"
            :style="{ '--card-accent': card.color }"
          >
            <div class="type-card-accent" />
            <div class="type-card-body">
              <div class="type-card-head">
                <div class="type-icon-wrap">
                  <el-icon :size="20"><component :is="card.icon" /></el-icon>
                </div>
                <div class="type-meta">
                  <span class="type-agent">{{ card.agentName }}</span>
                  <el-tag size="small" effect="dark" class="type-label-tag">{{ card.label }}</el-tag>
                </div>
              </div>
              <p class="type-desc">
                <el-icon v-if="card.latest" class="status-icon done"><CircleCheck /></el-icon>
                <el-icon v-else class="status-icon pending"><Clock /></el-icon>
                {{ card.latest ? card.latest.title : '尚未生成' }}
              </p>
              <div class="type-actions">
                <el-button
                  size="small"
                  type="primary"
                  :loading="card.generating && !batchLoading"
                  :disabled="!isLoggedIn || (loading && generatingType !== card.type) || batchLoading"
                  @click="onGenerateOne(card.type)"
                >
                  {{ card.generating ? '生成中…' : '生成' }}
                </el-button>
                <el-button
                  v-if="card.latest"
                  size="small"
                  link
                  type="primary"
                  @click="openResource(card.latest!)"
                >
                  查看
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="resources-section">
        <div class="section-head">
          <h3 class="section-title">已生成资源</h3>
          <span v-if="resources.length" class="section-badge">{{ filteredResources.length }} 条</span>
        </div>

        <el-row v-if="resources.length" :gutter="8" class="filter-row">
          <el-col :xs="24" :md="8">
            <el-input
              v-model="searchQuery"
              :prefix-icon="Search"
              placeholder="搜索标题 / Agent / 内容"
              clearable
            />
          </el-col>
          <el-col :xs="12" :md="5">
            <el-select v-model="filterType" placeholder="类型" clearable style="width: 100%">
              <el-option
                v-for="(meta, t) in RESOURCE_TYPE_META"
                :key="t"
                :label="meta.label"
                :value="t"
              />
            </el-select>
          </el-col>
          <el-col :xs="12" :md="5">
            <el-select v-model="filterVerified" placeholder="状态" clearable style="width: 100%">
              <el-option label="已校验" value="verified" />
              <el-option label="待校验草稿" value="draft" />
              <el-option label="收藏" value="favorite" />
            </el-select>
          </el-col>
        </el-row>

        <div v-if="resources.length === 0" class="empty-state">
          <div class="empty-icon-wrap">
            <el-icon :size="48"><Box /></el-icon>
          </div>
          <p class="empty-title">暂无资源</p>
          <p class="empty-desc">
            {{ isLoggedIn ? '输入主题后点击上方「一键生成全部」，或选择单个智能体生成' : '请先登录，再使用智能体生成个性化学习资源' }}
          </p>
        </div>
        <el-empty v-else-if="filteredResources.length === 0" description="无匹配结果" />

        <el-row v-else :gutter="16" class="resource-layout">
          <el-col :xs="24" :md="8">
            <div class="res-list">
              <div
                v-for="r in pagedResources"
                :key="r.id"
                class="res-item"
                :class="{ active: r.id === activeId }"
                @click="openResource(r)"
              >
                <div class="res-item-top">
                  <span
                    class="res-type-dot"
                    :style="{ background: RESOURCE_TYPE_META[r.resource_type]?.color ?? '#38bdf8' }"
                  />
                  <span class="res-agent">{{ r.agent_name }}</span>
                  <el-tag size="small" :type="verifyTag(r.meta ?? {}).type" effect="plain">
                    {{ verifyTag(r.meta ?? {}).label }}
                  </el-tag>
                </div>
                <span class="res-title">{{ r.title }}</span>
                <span class="res-time">{{ r.created_at }}</span>
                <div class="res-actions" @click.stop>
                  <el-button
                    link
                    :type="r.meta?.favorited ? 'warning' : 'default'"
                    :icon="Star"
                    @click="onToggleFavorite(r)"
                  />
                  <el-button link type="danger" :icon="Delete" @click="onDelete(r)" />
                </div>
              </div>
            </div>
            <el-pagination
              v-model:current-page="page"
              :page-size="pageSize"
              :total="filteredResources.length"
              layout="prev, pager, next"
              small
              class="pager"
            />
          </el-col>
          <el-col :xs="24" :md="16">
            <el-card v-if="activeResource" shadow="never" class="preview-card">
              <template #header>
                <div class="preview-head">
                  <el-icon><Document /></el-icon>
                  <span class="preview-title">{{ activeResource.title }}</span>
                  <el-tag size="small">{{ activeResource.agent_name }}</el-tag>
                  <el-tag
                    size="small"
                    :type="verifyTag(activeResource.meta ?? {}).type"
                    effect="plain"
                  >
                    {{ verifyTag(activeResource.meta ?? {}).label }}
                  </el-tag>
                  <el-alert
                    v-if="activeResource.meta?.status === 'draft'"
                    type="warning"
                    :closable="false"
                    show-icon
                    title="内容待校验，仅供参考"
                    class="draft-alert"
                  />
                </div>
              </template>
              <ResourceContentPreview
                :resource-type="activeResource.resource_type"
                :content="activeResource.content"
                :meta="activeResource.meta"
              />
              <p
                v-if="
                  Array.isArray(activeResource.meta?.knowledge_refs) &&
                  (activeResource.meta.knowledge_refs as string[]).length
                "
                class="refs"
              >
                知识库依据：{{ (activeResource.meta.knowledge_refs as string[]).join('、') }}
              </p>
            </el-card>
            <div v-else class="preview-placeholder">
              <el-icon :size="36"><Document /></el-icon>
              <p>点击左侧条目预览内容</p>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.resource-page {
  animation: fade-in 0.35s ease;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-card {
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-muted);
}

.page-header {
  margin-bottom: 20px;
}

.page-desc {
  color: var(--alp-color-muted);
  line-height: 1.7;
  margin: 12px 0 0;
  max-width: 72ch;
  font-size: 14px;
}

.login-alert {
  margin-bottom: 16px;
}

.gen-panel {
  padding: 20px;
  margin-bottom: 24px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.field-label {
  display: block;
  font-size: 12px;
  color: var(--alp-color-muted);
  margin-bottom: 6px;
  font-weight: 500;
}

.gen-btn-col {
  display: flex;
  align-items: flex-end;
}

.gen-all-btn {
  width: 100%;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.progress-block {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--alp-color-border);
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.progress-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--alp-color-muted);
  flex-shrink: 0;
}

.progress-dot.active {
  background: var(--alp-color-primary);
  box-shadow: 0 0 8px var(--alp-color-primary);
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.progress-line {
  font-size: 13px;
  color: var(--alp-color-primary);
  margin: 0;
}

.main-progress :deep(.el-progress-bar__outer) {
  background: rgba(15, 23, 42, 0.8);
  border-radius: 6px;
}

.main-progress :deep(.el-progress-bar__inner) {
  border-radius: 6px;
}

.workflow-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.muted {
  color: var(--alp-color-muted);
}

.small {
  font-size: 12px;
}

.workflow-log {
  margin-bottom: 20px;
  padding: 10px 12px;
  background: var(--alp-bg-code-ish);
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
}

.log-line {
  font-size: 11px;
  font-family: ui-monospace, monospace;
  color: var(--alp-color-muted);
  line-height: 1.6;
}

.agents-section {
  margin-bottom: 28px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.section-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--alp-color-primary-soft);
  color: var(--alp-color-primary);
  font-weight: 500;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.type-card {
  position: relative;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface-solid);
  border: 1px solid var(--alp-color-border);
  overflow: hidden;
  transition:
    transform var(--alp-transition-fast),
    box-shadow var(--alp-transition-fast),
    border-color var(--alp-transition-fast);
}

.type-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--alp-shadow-card-hover);
  border-color: color-mix(in srgb, var(--card-accent) 40%, transparent);
}

.type-card.is-generating {
  border-color: color-mix(in srgb, var(--card-accent) 60%, transparent);
  box-shadow: 0 0 20px color-mix(in srgb, var(--card-accent) 15%, transparent);
}

.type-card.has-resource .type-card-accent {
  opacity: 1;
}

.type-card-accent {
  height: 3px;
  background: linear-gradient(90deg, var(--card-accent), color-mix(in srgb, var(--card-accent) 50%, transparent));
  opacity: 0.7;
}

.type-card-body {
  padding: 14px 16px 16px;
}

.type-card-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

.type-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--card-accent) 14%, transparent);
  color: var(--card-accent);
  flex-shrink: 0;
}

.type-meta {
  flex: 1;
  min-width: 0;
}

.type-agent {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--card-accent);
  margin-bottom: 4px;
}

.type-label-tag {
  --el-tag-bg-color: color-mix(in srgb, var(--card-accent) 18%, transparent);
  --el-tag-border-color: color-mix(in srgb, var(--card-accent) 30%, transparent);
  --el-tag-text-color: var(--card-accent);
}

.type-desc {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: var(--alp-color-muted);
  min-height: 40px;
  margin: 0 0 12px;
  line-height: 1.5;
}

.status-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.status-icon.done {
  color: #10b981;
}

.status-icon.pending {
  color: var(--alp-color-muted);
}

.type-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.resources-section {
  padding-top: 8px;
  border-top: 1px solid var(--alp-color-border);
}

.filter-row {
  margin-bottom: 14px;
}

.resource-layout {
  margin-top: 4px;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px dashed var(--alp-color-border);
}

.empty-icon-wrap {
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--alp-color-primary-soft);
  color: var(--alp-color-primary);
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--alp-color-text);
  margin: 0 0 8px;
}

.empty-desc {
  font-size: 13px;
  color: var(--alp-color-muted);
  margin: 0;
  max-width: 36ch;
  margin-inline: auto;
  line-height: 1.6;
}

.res-list {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  max-height: 520px;
  overflow-y: auto;
  background: var(--alp-bg-surface-solid);
}

.res-item {
  padding: 12px 14px;
  border-bottom: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition: background var(--alp-transition-fast);
}

.res-item:last-child {
  border-bottom: none;
}

.res-item:hover {
  background: var(--alp-bg-nav-hover);
}

.res-item.active {
  background: var(--alp-bg-nav-active);
  border-left: 3px solid var(--alp-color-primary);
  padding-left: 11px;
}

.res-item-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.res-type-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.res-agent {
  flex: 1;
  font-size: 11px;
  color: var(--alp-color-primary);
  font-weight: 500;
}

.res-title {
  font-size: 13px;
  display: block;
  color: var(--alp-color-text);
  line-height: 1.4;
}

.res-time {
  font-size: 10px;
  color: var(--alp-color-muted);
  margin-top: 2px;
  display: block;
}

.res-actions {
  margin-top: 6px;
}

.pager {
  margin-top: 10px;
  justify-content: center;
}

.preview-card {
  min-height: 360px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid);
}

.preview-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.preview-title {
  font-weight: 600;
  flex: 1;
  min-width: 0;
}

.preview-placeholder {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-radius: var(--alp-radius-card);
  border: 1px dashed var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-muted);
  font-size: 14px;
}

.preview-placeholder p {
  margin: 0;
}

.draft-alert {
  margin-top: 10px;
  width: 100%;
}

.refs {
  margin-top: 12px;
  font-size: 11px;
  color: var(--alp-color-muted);
  padding-top: 10px;
  border-top: 1px solid var(--alp-color-border);
}
</style>
