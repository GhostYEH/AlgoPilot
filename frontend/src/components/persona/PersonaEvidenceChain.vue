<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Document, Refresh } from '@element-plus/icons-vue'
import {
  EVIDENCE_DIMENSION_FOR_EVENT,
  EVIDENCE_SOURCE_META,
  PROFILE_DIMENSION_LABELS,
  type LearningEvidenceBrief,
  type PersonaDimensions,
  type PersonaProfile,
} from '@/api/orchestrator'
import { fetchMemorySummary } from '@/api/memory'

const props = withDefaults(
  defineProps<{
    profile: PersonaProfile | null
    loading?: boolean
    error?: boolean
    /** 是否额外拉取 memory summary（learning_memory_summary） */
    fetchMemory?: boolean
  }>(),
  {
    loading: false,
    error: false,
    fetchMemory: true,
  },
)

const emit = defineEmits<{
  retry: []
}>()

const memorySummary = ref('')
const memoryLoading = ref(false)
const memoryExpanded = ref<string[]>([])
const dimensionExpanded = ref<string[]>([])

const dimensionKeys = Object.keys(PROFILE_DIMENSION_LABELS) as (keyof PersonaDimensions)[]

const recentEvidence = computed(() => (props.profile?.recent_evidence ?? []).slice(0, 3))

const dimensionEvidence = computed(() => props.profile?.dimension_evidence ?? {})

const updateReason = computed(() => (props.profile?.update_reason ?? '').trim())

const dimensionsWithEvidence = computed(() =>
  dimensionKeys.filter((k) => (dimensionEvidence.value[k]?.length ?? 0) > 0),
)

const hasAnyEvidence = computed(
  () =>
    !!updateReason.value ||
    recentEvidence.value.length > 0 ||
    dimensionsWithEvidence.value.length > 0 ||
    !!memorySummary.value.trim(),
)

const showEmpty = computed(
  () => !props.loading && !props.error && !hasAnyEvidence.value && !memoryLoading.value,
)

function sourceMeta(eventType: string) {
  return (
    EVIDENCE_SOURCE_META[eventType] ?? {
      label: eventType || '学习行为',
      tagType: 'info' as const,
    }
  )
}

function dimensionLabel(key: string) {
  return PROFILE_DIMENSION_LABELS[key as keyof PersonaDimensions] ?? key
}

function affectedDimension(item: LearningEvidenceBrief) {
  const key = EVIDENCE_DIMENSION_FOR_EVENT[item.event_type]
  return key ? dimensionLabel(key) : ''
}

function formatTime(iso: string | null | undefined) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso.slice(0, 16)
    return d.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso.slice(0, 16)
  }
}

function snippetsForDimension(key: keyof PersonaDimensions, max = 2) {
  return (dimensionEvidence.value[key] ?? []).slice(0, max)
}

function scoreFor(key: keyof PersonaDimensions) {
  return props.profile?.dimension_scores?.[key]
}

async function loadMemorySummary() {
  if (!props.fetchMemory) return
  memoryLoading.value = true
  try {
    const data = await fetchMemorySummary()
    memorySummary.value = data.learning_memory_summary ?? ''
  } catch {
    memorySummary.value = ''
  } finally {
    memoryLoading.value = false
  }
}

watch(
  () => props.profile?.updated_at,
  () => {
    if (props.profile) void loadMemorySummary()
  },
  { immediate: true },
)
</script>

<template>
  <el-card shadow="never" class="evidence-card" v-loading="loading || memoryLoading">
    <div class="evidence-head">
      <el-icon><Document /></el-icon>
      <span>为什么这样评估？ · 画像证据链</span>
      <el-button
        v-if="error"
        size="small"
        :icon="Refresh"
        text
        type="primary"
        @click="emit('retry')"
      >
        重试
      </el-button>
    </div>

    <el-alert
      v-if="error && !loading"
      type="error"
      :closable="false"
      show-icon
      title="画像证据加载失败"
      description="请检查网络或稍后重试。"
      class="evidence-alert"
    />

    <el-empty
      v-else-if="showEmpty"
      description="暂无学习证据，完成一次资源学习或 OJ 诊断后将自动更新。"
    />

    <template v-else-if="!loading">
      <div v-if="updateReason" class="update-reason">
        <span class="section-label">最近更新原因</span>
        <p class="reason-text">{{ updateReason }}</p>
      </div>

      <section v-if="recentEvidence.length" class="evidence-section">
        <span class="section-label">最近学习证据（{{ recentEvidence.length }}）</span>
        <ul class="recent-list">
          <li v-for="item in recentEvidence" :key="item.id || item.at + item.event_type">
            <div class="recent-meta">
              <el-tag size="small" :type="sourceMeta(item.event_type).tagType" effect="plain">
                {{ sourceMeta(item.event_type).label }}
              </el-tag>
              <span class="recent-time">{{ formatTime(item.at) }}</span>
              <el-tag v-if="affectedDimension(item)" size="small" type="info" effect="plain">
                影响 {{ affectedDimension(item) }}
              </el-tag>
            </div>
            <div class="recent-event">
              {{ item.event_label || item.event_type }}
              <span v-if="item.problem_slug" class="recent-slug"> · {{ item.problem_slug }}</span>
            </div>
            <p v-if="item.summary" class="recent-summary">{{ item.summary }}</p>
          </li>
        </ul>
      </section>

      <section v-if="dimensionsWithEvidence.length" class="evidence-section">
        <span class="section-label">各维度证据摘录</span>
        <el-collapse v-model="dimensionExpanded" class="dim-collapse">
          <el-collapse-item
            v-for="key in dimensionsWithEvidence"
            :key="key"
            :name="key"
          >
            <template #title>
              <span class="dim-title">
                {{ PROFILE_DIMENSION_LABELS[key] }}
                <em v-if="scoreFor(key)" class="dim-score">{{ scoreFor(key) }}/10</em>
              </span>
              <el-tag
                v-if="snippetsForDimension(key).length"
                size="small"
                type="info"
                effect="plain"
                class="dim-count"
              >
                {{ snippetsForDimension(key).length }} 条
              </el-tag>
            </template>
            <ul class="dim-snippets">
              <li v-for="(snippet, idx) in snippetsForDimension(key)" :key="idx">
                {{ snippet }}
              </li>
            </ul>
          </el-collapse-item>
        </el-collapse>
      </section>

      <el-collapse
        v-if="memorySummary.trim()"
        v-model="memoryExpanded"
        class="memory-collapse"
      >
        <el-collapse-item name="memory" title="学习记忆摘要">
          <pre class="memory-pre">{{ memorySummary }}</pre>
        </el-collapse-item>
      </el-collapse>
    </template>
  </el-card>
</template>

<style scoped>
.evidence-card {
  margin-top: 16px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
}

.evidence-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 12px;
}

.evidence-head .el-button {
  margin-left: auto;
}

.evidence-alert {
  margin-bottom: 0;
}

.section-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-primary);
  margin-bottom: 8px;
}

.update-reason {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.reason-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.evidence-section {
  margin-bottom: 16px;
}

.recent-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.recent-list li {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.recent-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.recent-time {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.recent-event {
  font-size: 13px;
  font-weight: 500;
  color: var(--alp-color-text);
}

.recent-slug {
  font-weight: 400;
  color: var(--alp-color-muted);
}

.recent-summary {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--alp-color-muted);
}

.dim-collapse :deep(.el-collapse-item__header) {
  font-size: 13px;
}

.dim-title {
  flex: 1;
}

.dim-score {
  font-style: normal;
  font-weight: 500;
  color: var(--alp-color-muted);
  margin-left: 6px;
  font-size: 11px;
}

.dim-count {
  margin-right: 8px;
}

.dim-snippets {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.dim-snippets li {
  margin-bottom: 6px;
}

.dim-empty.muted {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.memory-collapse {
  margin-top: 4px;
}

.memory-pre {
  margin: 0;
  white-space: pre-wrap;
  font-size: 11px;
  line-height: 1.55;
  color: var(--alp-color-muted);
  font-family: inherit;
}

.muted {
  color: var(--alp-color-muted);
}
</style>
