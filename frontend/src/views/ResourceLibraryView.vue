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
  Postcard,
  Download,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteResource,
  downloadPptxResource,
  fetchResources,
  resourceVerifyTag,
  RESOURCE_TYPE_META,
  setResourceFavorite,
  streamGenerateAllResources,
  streamGenerateResource,
  type GeneratedResource,
} from '@/api/orchestrator'
import { isLoggedIn } from '@/stores/auth'
import { usePersonaUi } from '@/composables/usePersonaUiProvider'
import { fuzzyFilter } from '@/utils/fuzzySearch'
import { normalizeResourceSources, relevanceLabel } from '@/utils/resourceSources'
import ResourceContentPreview from '@/components/resources/ResourceContentPreview.vue'
import SafetyValidationPanel from '@/components/resources/SafetyValidationPanel.vue'
import TrustEvidenceDrawer from '@/components/resources/TrustEvidenceDrawer.vue'
import { ALGORITHM_MODULES, generationPresetForModule } from '@/constants/modules'
import resourceLibraryHero from '@/assets/resource-library-hero.png'

const personaUi = usePersonaUi()
const showWorkflowDetail = computed(() => personaUi.value.graphDetail !== 'minimal')

const TYPE_ICONS: Record<string, Component> = {
  document: Document,
  mindmap: Share,
  exercises: EditPen,
  reading: Reading,
  code_case: Monitor,
  trace_animation: VideoCamera,
  ppt: Postcard,
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
const selectedModule = ref('')
const activeId = ref<number | null>(null)
const workflowLogs = ref<string[]>([])
const logFullscreen = ref(false)
const searchQuery = ref('')
const filterType = ref('')
const filterVerified = ref('')
const page = ref(1)
const pageSize = ref(8)
const batchFallbackNotice = ref('')

const evidenceVisible = ref(false)
const evidenceResource = ref<GeneratedResource | null>(null)

function openEvidence(r: GeneratedResource) {
  evidenceResource.value = r
  evidenceVisible.value = true
}

const activeResource = computed(() =>
  resources.value.find((r) => r.id === activeId.value) ?? null,
)
const activeSources = computed(() => normalizeResourceSources(activeResource.value))
const activeContentVerification = computed(() => {
  const raw = activeResource.value?.meta?.content_verification
  return raw && typeof raw === 'object'
    ? (raw as {
        passed?: boolean
        warnings?: string[]
        grounded_terms?: string[]
        unsupported_claims?: string[]
      })
    : null
})

const filteredResources = computed(() => {
  let list = [...resources.value]
  const q = searchQuery.value.trim()
  if (q) {
    list = fuzzyFilter(list, q, ['title', 'agent_name', 'content', 'resource_type'])
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
  loading.value = true
  try {
    resources.value = await fetchResources()
    applyHighlightFromRoute()
  } catch {
    resources.value = []
    ElMessage.warning('资源列表加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (typeof route.query.topic === 'string' && route.query.topic.trim()) {
    topic.value = route.query.topic
  }
  if (
    typeof route.query.module === 'string' &&
    ALGORITHM_MODULES.some((item) => item.key === route.query.module)
  ) {
    selectedModule.value = route.query.module
  }
  void loadList()
})

function handleStreamError(msg: string) {
  progressText.value = ''
  ElMessage.error(msg || '资源生成失败，请检查 LLM 是否已配置')
}

function applyModulePreset(moduleKey: string) {
  const preset = generationPresetForModule(moduleKey)
  if (!preset) return
  topic.value = preset.topic
  focusHint.value = preset.focusHint
}

function generationInputReady(): boolean {
  if (!selectedModule.value) {
    ElMessage.warning('请先选择课程模块，再生成学习资源')
    return false
  }
  if (!topic.value.trim()) {
    ElMessage.warning('请填写与课程模块一致的课程主题')
    return false
  }
  return true
}

async function onGenerateOne(type: string) {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后生成资源')
    void router.push({ name: 'login', query: { redirect: '/resources' } })
    return
  }
  if (!generationInputReady()) return
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
        module_key: selectedModule.value || undefined,
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
  if (!generationInputReady()) return
  batchLoading.value = true
  workflowLogs.value = []
  progressPercent.value = 0
  batchFallbackNotice.value = ''
  progressText.value = 'DAG Pipeline：检索 → 生成 ⇄ 校验 → 安全 → 落库…'
  try {
    await streamGenerateAllResources(
      {
        topic: topic.value,
        module_key: selectedModule.value || undefined,
        focus_hint: focusHint.value,
      },
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
          if (isTemplateFallback(r.meta)) {
            batchFallbackNotice.value =
              '当前为无模型 Key 的模板降级资源，配置 AI 模型 API Key 后可生成更高质量内容。'
          }
          if (r.meta?.reused) {
            workflowLogs.value.push(`[复用] ${r.agent_name} · ${r.title}`)
          }
        },
        onDone(info) {
          const reused = info?.reused_count ?? 0
          if (info?.fallback_mode) {
            batchFallbackNotice.value =
              '当前为无模型 Key 的模板降级资源，配置 AI 模型 API Key 后可生成更高质量内容。'
            ElMessage.warning('已使用 TemplateFallbackAgent 模板降级完成批量生成（非大模型输出）')
          } else if (reused > 0) {
            ElMessage.success(`完成：${reused} 项画像未变已复用，其余已生成/校验`)
          } else {
            ElMessage.success('个性化资源已全部生成（含校验闭环）')
          }
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

const pptDownloadingId = ref<number | null>(null)

async function onDownloadPptx(r: GeneratedResource) {
  if (r.resource_type !== 'ppt') {
    ElMessage.warning('仅课程讲义 PPT 支持下载')
    return
  }
  pptDownloadingId.value = r.id
  try {
    await downloadPptxResource({ id: r.id, title: r.title })
    ElMessage.success('PPT 已开始下载')
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'PPT 下载失败'
    ElMessage.error(msg)
  } finally {
    pptDownloadingId.value = null
  }
}

function isTemplateFallback(meta: Record<string, unknown> | undefined): boolean {
  return meta?.fallback === true || meta?.generated_by === 'TemplateFallbackAgent'
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
        <div class="hero-copy">
          <span class="hero-kicker">PERSONAL LEARNING ARCHIVE</span>
          <el-page-header title="个性化资源库" @back="router.push({ name: 'home' })" />
          <p class="page-desc">
            八位智能体围绕你的学习画像协同工作，把当前课程整理成讲解、图谱、练习、代码、动画、阅读、课件与视频脚本。
          </p>
          <div class="hero-stats" aria-label="资源库概览">
            <div><strong>8</strong><span>协作智能体</span></div>
            <div><strong>{{ generatedCount }}</strong><span>类型已就绪</span></div>
            <div><strong>{{ resources.length }}</strong><span>资源已归档</span></div>
          </div>
        </div>
        <img
          :src="resourceLibraryHero"
          class="hero-illustration"
          alt="由文档、知识节点、代码和视频素材组成的智能资源库插图"
        />
      </div>

      <el-alert v-if="!isLoggedIn" type="warning" show-icon :closable="false" class="login-alert">
        登录后可生成并保存资源到云端
      </el-alert>

      <el-alert
        v-if="batchFallbackNotice"
        type="warning"
        show-icon
        :closable="true"
        class="fallback-alert"
        :title="batchFallbackNotice"
        description="当前内容由课程知识库模板整理，并非大模型原创；展示前仍会经过格式与内容校验。"
        @close="batchFallbackNotice = ''"
      />

      <div class="gen-panel">
        <div class="gen-panel-inner">
          <el-row :gutter="12" class="gen-row">
            <el-col :xs="24" :md="7">
              <label class="field-label">课程模块</label>
              <el-select
                v-model="selectedModule"
                aria-label="课程模块"
                size="large"
                clearable
                filterable
                placeholder="选择模块（含排序算法）"
                style="width: 100%"
                @change="applyModulePreset"
              >
                <el-option
                  v-for="item in ALGORITHM_MODULES"
                  :key="item.key"
                  :label="item.label"
                  :value="item.key"
                />
              </el-select>
            </el-col>
            <el-col :xs="24" :md="7">
              <label class="field-label">课程主题</label>
              <el-input v-model="topic" aria-label="课程主题" placeholder="如：数据结构与算法" size="large" />
            </el-col>
            <el-col :xs="24" :md="6">
              <label class="field-label">生成侧重</label>
              <el-input
                v-model="focusHint"
                aria-label="生成侧重"
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

      <div v-if="workflowLogs.length && showWorkflowDetail" class="workflow-toolbar">
        <span class="muted small">Workflow / 协作日志（{{ workflowLogs.length }} 条）</span>
        <el-button link type="primary" @click="logFullscreen = true">全屏查看</el-button>
      </div>
      <el-scrollbar
        v-if="workflowLogs.length && showWorkflowDetail && !logFullscreen"
        max-height="120"
        class="workflow-log"
      >
        <div v-for="(line, i) in workflowLogs" :key="i" class="log-line">{{ line }}</div>
      </el-scrollbar>
      <el-drawer v-model="logFullscreen" title="Workflow 全屏日志" size="90%" direction="btt">
        <div v-for="(line, i) in workflowLogs" :key="i" class="log-line">{{ line }}</div>
      </el-drawer>

      <div class="agents-section">
        <div class="section-head">
          <div>
            <h3 class="section-title">智能体矩阵</h3>
            <p class="section-caption">先由核心智能体建立知识骨架，再并行生成可学习、可练习、可演示的资源。</p>
          </div>
          <span class="section-badge">{{ generatedCount }} / 8 已生成</span>
        </div>
        <div class="type-grid">
          <div
            v-for="card in typeCards"
            :key="card.type"
            class="type-card"
            :class="{ 'is-generating': card.generating, 'has-resource': !!card.latest }"
            :style="{ '--card-accent': card.color }"
          >
            <div class="type-card-body">
              <div class="type-card-head">
                <div class="type-icon-wrap">
                  <el-icon :size="20"><component :is="card.icon" /></el-icon>
                </div>
                <div class="type-meta">
                  <span class="type-agent">{{ card.agentName }}</span>
                  <span class="type-label-tag">{{ card.label }}</span>
                </div>
                <span class="type-state">{{ card.latest ? 'READY' : 'IDLE' }}</span>
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
                    :style="{ background: RESOURCE_TYPE_META[r.resource_type]?.color ?? '#3a8a9e' }"
                  />
                  <span class="res-agent">{{ r.agent_name }}</span>
                  <el-tag size="small" :type="verifyTag(r.meta ?? {}).type" effect="plain">
                    {{ verifyTag(r.meta ?? {}).label }}
                  </el-tag>
                  <el-tag v-if="isTemplateFallback(r.meta)" size="small" type="warning" effect="plain">
                    模板降级
                  </el-tag>
                </div>
                <span class="res-title">{{ r.title }}</span>
                <span v-if="r.explain" class="res-explain">💡 {{ r.explain }}</span>
                <span class="res-time">{{ r.created_at }}</span>
                <div class="res-actions" @click.stop>
                  <el-button
                    link
                    type="primary"
                    @click="openEvidence(r)"
                  >
                    🔗 证据
                  </el-button>
                  <el-button
                    v-if="r.resource_type === 'ppt'"
                    link
                    type="primary"
                    :icon="Download"
                    :loading="pptDownloadingId === r.id"
                    @click="onDownloadPptx(r)"
                  >
                    下载
                  </el-button>
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
              size="small"
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
              <div v-if="activeResource.explain" class="preview-explain">
                <span class="preview-explain-label">💡 推荐原因</span>
                <p class="preview-explain-text">{{ activeResource.explain }}</p>
              </div>
              <section class="course-sources">
                <div class="course-sources-head">
                  <div>
                    <h4>课程来源</h4>
                    <p>本资源由课程知识库检索结果约束生成，并经内容校验智能体检查。</p>
                  </div>
                  <el-tag
                    size="small"
                    :type="activeContentVerification?.passed ? 'success' : 'warning'"
                    effect="plain"
                  >
                    {{ activeContentVerification?.passed ? '校验通过' : '待复核' }}
                  </el-tag>
                </div>
                <div v-if="activeSources.length" class="source-list">
                  <article
                    v-for="source in activeSources"
                    :key="source.chunk_id"
                    class="source-item"
                  >
                    <div class="source-title-row">
                      <strong>{{ source.chapter_title || '课程知识库' }}</strong>
                      <el-tag size="small" effect="plain">
                        相关度 {{ relevanceLabel(source.relevance_score) }}
                      </el-tag>
                    </div>
                    <p class="source-section">知识点：{{ source.section_title || source.module_id || '课程模块' }}</p>
                    <p class="source-excerpt">{{ source.excerpt || '该旧资源未保存来源摘要。' }}</p>
                    <code class="source-id">source id: {{ source.chunk_id }}</code>
                  </article>
                </div>
                <div v-else class="source-empty">
                  该资源为旧版数据，未保存详细来源；生成依据模块：
                  {{ String(activeResource.meta?.module_key ?? '课程通用知识库') }}
                </div>
                <div v-if="activeContentVerification" class="verifier-summary">
                  <p v-if="activeContentVerification.grounded_terms?.length">
                    <strong>有依据术语：</strong>{{ activeContentVerification.grounded_terms.join('、') }}
                  </p>
                  <p v-if="activeContentVerification.warnings?.length">
                    <strong>校验提醒：</strong>{{ activeContentVerification.warnings.join('；') }}
                  </p>
                  <p v-if="activeContentVerification.unsupported_claims?.length">
                    <strong>缺少依据：</strong>{{ activeContentVerification.unsupported_claims.join('；') }}
                  </p>
                </div>
              </section>
              <SafetyValidationPanel
                :meta="activeResource.meta"
                :resource-type="activeResource.resource_type"
              />
              <div class="preview-evidence-row">
                <el-button
                  v-if="activeResource.resource_type === 'ppt'"
                  type="primary"
                  size="small"
                  :icon="Download"
                  :loading="pptDownloadingId === activeResource.id"
                  @click="onDownloadPptx(activeResource!)"
                >
                  下载 PPT (.pptx)
                </el-button>
                <el-button type="primary" plain size="small" @click="openEvidence(activeResource!)">
                  🔗 可信证据链
                </el-button>
              </div>
            </el-card>
            <div v-else class="preview-placeholder">
              <el-icon :size="36"><Document /></el-icon>
              <p>点击左侧条目预览内容</p>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
    <TrustEvidenceDrawer
      v-model:visible="evidenceVisible"
      :resource="evidenceResource"
    />
  </div>
</template>

<style scoped>
.resource-page {
  animation: fade-in 0.35s ease;
  --resource-ink: #0b2f35;
  --resource-teal: #0b9c96;
  --resource-line: color-mix(in srgb, var(--alp-color-border) 78%, transparent);
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
  overflow: hidden;
  border-radius: 22px;
  border: 1px solid var(--resource-line);
  background: color-mix(in srgb, var(--alp-bg-surface-muted) 94%, white);
  box-shadow: 0 24px 70px rgba(20, 78, 86, 0.08);
}

.page-card :deep(.el-card__body) {
  padding: clamp(18px, 2.4vw, 34px);
}

.page-header {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
  min-height: 256px;
  margin: calc(clamp(18px, 2.4vw, 34px) * -1) calc(clamp(18px, 2.4vw, 34px) * -1) 18px;
  padding: clamp(28px, 4vw, 54px) clamp(24px, 4.5vw, 64px);
  overflow: hidden;
  background:
    radial-gradient(circle at 72% 26%, rgba(85, 214, 209, 0.15), transparent 28%),
    linear-gradient(112deg, #f7fcfc 0%, #fbfefe 48%, #eff9fb 100%);
  border-bottom: 1px solid rgba(11, 156, 150, 0.1);
}

.page-header::after {
  content: '';
  position: absolute;
  inset: auto -8% -64% 30%;
  height: 190px;
  border-radius: 50%;
  border: 1px solid rgba(11, 156, 150, 0.12);
  transform: rotate(-7deg);
  pointer-events: none;
}

.hero-copy {
  position: relative;
  z-index: 2;
  align-self: center;
}

.hero-kicker {
  display: block;
  margin-bottom: 12px;
  color: var(--resource-teal);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.page-header :deep(.el-page-header__left) {
  margin-right: 14px;
}

.page-header :deep(.el-page-header__title) {
  color: var(--resource-ink);
  font-size: clamp(24px, 2.4vw, 34px);
  font-weight: 750;
  letter-spacing: -0.04em;
}

.hero-illustration {
  position: absolute;
  z-index: 1;
  right: -1.5%;
  top: 50%;
  width: min(58%, 720px);
  height: 118%;
  object-fit: cover;
  object-position: right center;
  transform: translateY(-50%);
  mix-blend-mode: multiply;
  pointer-events: none;
  user-select: none;
}

.page-desc {
  color: var(--alp-color-muted);
  line-height: 1.75;
  margin: 14px 0 0;
  max-width: 56ch;
  font-size: 14px;
}

.hero-stats {
  display: flex;
  gap: 22px;
  margin-top: 22px;
}

.hero-stats > div {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.hero-stats strong {
  color: var(--resource-ink);
  font-size: 18px;
  font-variant-numeric: tabular-nums;
}

.hero-stats span {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.login-alert {
  margin-bottom: 16px;
}

.gen-panel {
  position: relative;
  z-index: 3;
  padding: 18px 20px;
  margin: 0 0 26px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--alp-bg-surface-solid) 94%, transparent);
  border: 1px solid var(--resource-line);
  box-shadow: 0 12px 32px rgba(22, 74, 82, 0.07);
}

.field-label {
  display: block;
  font-size: 12px;
  color: #536b6d;
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
  border: none;
  background: linear-gradient(135deg, #0b9c96, #0b83a9);
  box-shadow: 0 8px 20px rgba(11, 156, 150, 0.2);
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
  margin-bottom: 34px;
  padding: clamp(18px, 2.5vw, 28px);
  border: 1px solid var(--resource-line);
  border-radius: 18px;
  background:
    linear-gradient(145deg, rgba(11, 156, 150, 0.035), transparent 42%),
    var(--alp-bg-surface-solid);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 20px;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 750;
  color: var(--alp-color-text);
  letter-spacing: -0.02em;
}

.section-caption {
  margin: 6px 0 0;
  color: var(--alp-color-muted);
  font-size: 12px;
  line-height: 1.55;
}

.section-badge {
  flex: 0 0 auto;
  font-size: 11px;
  padding: 5px 11px;
  border-radius: 999px;
  background: var(--alp-color-primary-soft);
  color: #08716f;
  font-weight: 700;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.type-card {
  grid-column: span 2;
}

.type-card:nth-child(-n + 2) {
  grid-column: span 3;
}

.type-card {
  position: relative;
  min-height: 172px;
  border-radius: 14px;
  background: var(--alp-bg-surface-solid);
  border: 1px solid color-mix(in srgb, var(--card-accent) 18%, var(--resource-line));
  overflow: hidden;
  transition:
    transform var(--alp-transition-fast),
    box-shadow var(--alp-transition-fast),
    border-color var(--alp-transition-fast),
    filter var(--alp-transition-fast);
}

.type-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 30px color-mix(in srgb, var(--card-accent) 11%, transparent);
  border-color: color-mix(in srgb, var(--card-accent) 40%, transparent);
}

.type-card.is-generating {
  border-color: color-mix(in srgb, var(--card-accent) 60%, transparent);
  box-shadow: 0 0 20px color-mix(in srgb, var(--card-accent) 15%, transparent);
}

.type-card-body {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 17px 18px 16px;
}

.type-card-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

.type-icon-wrap {
  width: 42px;
  height: 42px;
  border-radius: 12px;
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
  font-size: 14px;
  font-weight: 750;
  color: var(--alp-color-text);
  margin-bottom: 4px;
}

.type-label-tag {
  display: inline-block;
  color: color-mix(in srgb, var(--card-accent) 68%, var(--resource-ink));
  font-size: 11px;
  font-weight: 650;
}

.type-state {
  margin-left: auto;
  padding: 3px 6px;
  color: color-mix(in srgb, var(--card-accent) 58%, var(--resource-ink));
  background: color-mix(in srgb, var(--card-accent) 9%, transparent);
  border-radius: 5px;
  font: 700 9px/1.2 ui-monospace, monospace;
  letter-spacing: 0.08em;
}

.type-desc {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: #5a7072;
  min-height: 38px;
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
  margin-top: auto;
}

.type-actions :deep(.el-button--primary) {
  --el-button-bg-color: #066f6d;
  --el-button-border-color: #066f6d;
  --el-button-hover-bg-color: #075f5e;
  --el-button-hover-border-color: #075f5e;
  background-color: #066f6d;
  border-color: #066f6d;
}

.resources-section {
  padding: clamp(18px, 2.5vw, 28px);
  border: 1px solid var(--resource-line);
  border-radius: 18px;
  background: var(--alp-bg-surface-solid);
}

@media (max-width: 1080px) {
  .page-header {
    grid-template-columns: minmax(0, 1fr) 320px;
  }

  .hero-illustration {
    right: -13%;
    width: 62%;
    opacity: 0.78;
  }

  .type-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .type-card,
  .type-card:nth-child(-n + 2) {
    grid-column: span 1;
  }
}

@media (max-width: 760px) {
  .page-card :deep(.el-card__body) {
    padding: 14px;
  }

  .page-header {
    display: block;
    min-height: 300px;
    margin: -14px -14px 14px;
    padding: 28px 20px 130px;
  }

  .hero-illustration {
    top: auto;
    right: -7%;
    bottom: -18%;
    width: 82%;
    height: 64%;
    transform: none;
    object-position: right bottom;
    opacity: 0.7;
  }

  .hero-stats {
    gap: 14px;
    flex-wrap: wrap;
  }

  .gen-panel,
  .agents-section,
  .resources-section {
    padding: 16px;
    border-radius: 14px;
  }

  .type-grid {
    grid-template-columns: 1fr;
  }

  .section-head {
    align-items: flex-start;
  }
}

@media (prefers-reduced-motion: reduce) {
  .resource-page,
  .type-card,
  .progress-dot.active {
    animation: none;
    transition: none;
  }
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
  color: #5a7072;
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

.res-explain {
  display: block;
  font-size: 11px;
  color: var(--el-color-warning-dark-2, #b45309);
  line-height: 1.4;
  margin-top: 2px;
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

.course-sources {
  margin-top: 16px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 28%, var(--alp-color-border));
  border-radius: 10px;
  background: color-mix(in srgb, var(--alp-color-primary) 5%, var(--alp-bg-soft-block));
}

.course-sources-head,
.source-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.course-sources-head h4 {
  margin: 0 0 4px;
  font-size: 14px;
  color: var(--alp-color-text);
}

.course-sources-head p,
.source-section,
.source-excerpt,
.verifier-summary p {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
}

.course-sources-head p,
.source-section,
.source-excerpt {
  color: var(--alp-color-muted);
}

.source-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.source-item {
  padding: 10px 12px;
  border: 1px solid var(--alp-color-border);
  border-radius: 8px;
  background: var(--alp-bg-surface-solid);
}

.source-title-row strong {
  font-size: 13px;
  color: var(--alp-color-text);
}

.source-section {
  margin-top: 5px;
  color: var(--alp-color-primary);
}

.source-excerpt {
  margin-top: 4px;
}

.source-id {
  display: inline-block;
  margin-top: 6px;
  font-size: 10px;
  color: var(--alp-color-muted);
  word-break: break-all;
}

.source-empty {
  margin-top: 10px;
  padding: 10px;
  border-radius: 8px;
  background: var(--alp-bg-surface-solid);
  color: var(--alp-color-muted);
  font-size: 12px;
}

.verifier-summary {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--alp-color-border);
  color: var(--alp-color-muted);
}

.preview-placeholder p {
  margin: 0;
}

.draft-alert {
  margin-top: 10px;
  width: 100%;
}

.preview-explain {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color-warning-light-9) 60%, transparent);
  border: 1px solid color-mix(in srgb, var(--el-color-warning-light-7) 50%, transparent);
}

.preview-explain-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-warning-dark-2, #b45309);
  margin-bottom: 4px;
}

.preview-explain-text {
  margin: 0;
  font-size: 12px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.refs {
  margin-top: 12px;
  font-size: 11px;
  color: var(--alp-color-muted);
  padding-top: 10px;
  border-top: 1px solid var(--alp-color-border);
}

.preview-evidence-row {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
