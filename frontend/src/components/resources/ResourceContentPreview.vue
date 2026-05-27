<script setup lang="ts">
import { computed } from 'vue'
import DomainStructurePanels from '@/components/resources/DomainStructurePanels.vue'
import {
  looksLikeUnparsedDomainJson,
  parseDomainStructureContent,
} from '@/utils/domainStructureContent'
import { renderAiReplyHtml } from '@/utils/renderAiReply'

const props = defineProps<{
  resourceType: string
  content: string
  meta?: Record<string, unknown>
}>()

const parsed = computed(() => {
  if (props.resourceType === 'document' || props.resourceType === 'code_case') {
    return null
  }
  try {
    return JSON.parse(props.content) as Record<string, unknown>
  } catch {
    return null
  }
})

const isQuiz = computed(
  () => props.resourceType === 'exercises' || props.meta?.format === 'quiz_json',
)
const isMindmap = computed(
  () => props.resourceType === 'mindmap' || props.meta?.format === 'mindmap_json',
)
const domainStructure = computed(() => parseDomainStructureContent(props.content))
const isDocOrScenario = computed(
  () => props.resourceType === 'document' || props.resourceType === 'code_case',
)
const isDomainStructure = computed(
  () =>
    !!domainStructure.value &&
    (isDocOrScenario.value || props.meta?.format === 'domain_structure_json'),
)
const unparsedDomainJson = computed(
  () => isDocOrScenario.value && looksLikeUnparsedDomainJson(props.content),
)
const legacyMarkdown = computed(
  () =>
    isDocOrScenario.value &&
    !domainStructure.value &&
    !unparsedDomainJson.value &&
    !!props.content.trim(),
)
const domainStructureMode = computed((): 'document' | 'scenario' =>
  props.resourceType === 'code_case' ? 'scenario' : 'document',
)
</script>

<template>
  <div v-if="isQuiz && parsed?.questions" class="quiz-preview">
    <div
      v-for="(q, i) in (parsed.questions as Array<Record<string, string>>)"
      :key="i"
      class="quiz-item"
    >
      <div class="quiz-type">{{ q.type || '题目' }}</div>
      <strong>{{ i + 1 }}. {{ q.stem }}</strong>
      <ul v-if="Array.isArray(q.options) && q.options.length">
        <li v-for="(o, j) in q.options" :key="j">{{ o }}</li>
      </ul>
      <p v-if="q.hint" class="hint">提示：{{ q.hint }}</p>
    </div>
  </div>

  <div v-else-if="isMindmap && parsed" class="mindmap-json">
    <p><strong>根节点：</strong>{{ parsed.root }}</p>
    <ul v-if="Array.isArray(parsed.nodes)">
      <li v-for="(n, i) in (parsed.nodes as Array<Record<string, string>>)" :key="i">
        {{ n.label }} <span class="muted">({{ n.parent }})</span>
      </li>
    </ul>
    <pre class="raw-json">{{ props.content }}</pre>
  </div>

  <DomainStructurePanels
    v-else-if="isDomainStructure"
    :content="content"
    :mode="domainStructureMode"
  />

  <el-alert
    v-else-if="unparsedDomainJson"
    type="warning"
    :closable="false"
    show-icon
    title="双域 JSON 解析失败"
    description="内容似为 Domain/Structure 结构但格式不完整。请重新生成资源，或联系管理员检查 Agent 输出。"
  />

  <div
    v-else-if="legacyMarkdown"
    class="preview-body ai-md-body"
    v-html="renderAiReplyHtml(content)"
  />

  <div v-else class="preview-body ai-md-body" v-html="renderAiReplyHtml(content)" />
</template>

<style scoped>
.quiz-item {
  margin-bottom: 14px;
  padding: 10px;
  border: 1px solid var(--alp-color-border);
  border-radius: 8px;
}

.quiz-type {
  font-size: 10px;
  color: var(--alp-color-primary);
  margin-bottom: 4px;
}

.hint {
  font-size: 12px;
  color: var(--alp-color-muted);
  margin: 6px 0 0;
}

.mindmap-json .muted {
  color: var(--alp-color-muted);
  font-size: 11px;
}

.raw-json {
  margin-top: 10px;
  font-size: 11px;
  max-height: 200px;
  overflow: auto;
  background: var(--alp-bg-soft-block);
  padding: 8px;
  border-radius: 6px;
}

.preview-body {
  line-height: 1.6;
  font-size: 14px;
}
</style>
