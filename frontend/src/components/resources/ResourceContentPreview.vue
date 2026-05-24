<script setup lang="ts">
import { computed } from 'vue'
import { renderAiReplyHtml } from '@/utils/renderAiReply'

const props = defineProps<{
  resourceType: string
  content: string
  meta?: Record<string, unknown>
}>()

const parsed = computed(() => {
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
