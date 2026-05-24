<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ChatDotRound, Delete, Promotion } from '@element-plus/icons-vue'
import { streamAiTutorChat, type ChatHistoryItem } from '@/api/aiTutor'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { suggestQuestionsForModule } from '@/modules/shared/aiTutorConfig'
import { sectionToAiContext } from '@/utils/buildLearnContext'
import { renderAiReplyHtml } from '@/utils/renderAiReply'

const props = defineProps<{
  moduleKey: string
  moduleTitle: string
  chapterTag: string
  moduleIntro: string
  section: LearnSection | null
}>()

interface UiMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
}

const input = ref('')
const loading = ref(false)
const messages = ref<UiMessage[]>([])
const listRef = ref<HTMLElement | null>(null)
let msgId = 0

const quickQuestions = computed(() =>
  props.section ? suggestQuestionsForModule(props.moduleKey, props.section) : [],
)

const sectionLabel = computed(() =>
  props.section ? props.section.title.replace(/^\d+\.\s*/, '') : '',
)

function scrollToBottom() {
  nextTick(() => {
    const el = listRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function clearChat() {
  messages.value = []
  input.value = ''
}

function focusPanel() {
  const el = document.querySelector('.ai-tutor-aside')
  el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

async function sendMessage(text?: string) {
  const content = (text ?? input.value).trim()
  if (!content || loading.value || !props.section) return

  input.value = ''
  messages.value.push({ id: ++msgId, role: 'user', content })
  scrollToBottom()
  loading.value = true

  const history: ChatHistoryItem[] = messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .slice(0, -1)
    .map((m) => ({ role: m.role, content: m.content }))

  const assistantId = ++msgId
  messages.value.push({ id: assistantId, role: 'assistant', content: '' })
  try {
    await streamAiTutorChat(
      {
        message: content,
        history,
        moduleKey: props.moduleKey,
        moduleTitle: props.moduleTitle,
        chapterTag: props.chapterTag,
        moduleIntro: props.moduleIntro,
        section: sectionToAiContext(props.section),
      },
      {
        onToken(chunk) {
          const row = messages.value.find((m) => m.id === assistantId)
          if (row) row.content += chunk
          scrollToBottom()
        },
      },
    )
    focusPanel()
  } catch {
    messages.value = messages.value.filter((m) => m.id !== assistantId)
  } finally {
    loading.value = false
  }
}

function onKeydown(e: Event | KeyboardEvent) {
  const ev = e as KeyboardEvent
  if (ev.key === 'Enter' && !ev.shiftKey) {
    ev.preventDefault()
    void sendMessage()
  }
}

watch(
  () => props.section?.id,
  () => {
    clearChat()
  },
)

/** 划词提问、外部快捷调用 */
async function askQuestion(message: string) {
  focusPanel()
  await sendMessage(message.trim())
}

defineExpose({
  askQuestion,
  sendMessage,
  focusPanel,
  isLoading: loading,
})
</script>

<template>
  <aside class="ai-tutor-aside" aria-label="AI 助教">
    <el-card shadow="never" class="ai-tutor-card">
      <template #header>
        <div class="ai-tutor-head">
          <div class="ai-tutor-title">
            <el-icon class="ai-tutor-icon"><ChatDotRound /></el-icon>
            <span>AI 助教</span>
          </div>
          <el-button
            v-if="messages.length"
            text
            type="info"
            size="small"
            :icon="Delete"
            title="清空对话"
            @click="clearChat"
          />
        </div>
      </template>

      <div ref="listRef" class="ai-tutor-messages">
        <div v-if="!messages.length" class="ai-tutor-welcome">
          <p class="welcome-lead">
            你好！我是你的算法学习助教，会结合<strong>当前页面</strong>的内容来回答。
          </p>
          <p v-if="sectionLabel" class="welcome-section">
            正在学习：<span class="section-name">{{ sectionLabel }}</span>
          </p>
          <p class="welcome-hint">
            可以问我概念、对比、复杂度，或做题思路；在左侧详解中<strong>划词</strong>后点「问一问」也可直接提问。
          </p>
        </div>

        <div
          v-for="msg in messages"
          :key="msg.id"
          class="msg-row"
          :class="msg.role === 'user' ? 'msg-row--user' : 'msg-row--assistant'"
        >
          <div class="msg-bubble">
            <span class="msg-role">{{ msg.role === 'user' ? '我' : '助教' }}</span>
            <p v-if="msg.role === 'user'" class="msg-text">{{ msg.content }}</p>
            <div
              v-else
              class="msg-text msg-text--md ai-md-body"
              v-html="renderAiReplyHtml(msg.content)"
            />
          </div>
        </div>

        <div v-if="loading" class="msg-row msg-row--assistant">
          <div class="msg-bubble msg-bubble--loading">
            <span class="msg-role">助教</span>
            <p class="msg-text">正在思考…</p>
          </div>
        </div>
      </div>

      <div v-if="quickQuestions.length && !loading" class="ai-tutor-quick">
        <span class="quick-label">快捷提问</span>
        <button
          v-for="(q, i) in quickQuestions"
          :key="i"
          type="button"
          class="quick-chip"
          :disabled="!section"
          @click="sendMessage(q)"
        >
          {{ q }}
        </button>
      </div>

      <div class="ai-tutor-input">
        <el-input
          v-model="input"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="输入问题，Enter 发送，Shift+Enter 换行"
          :disabled="loading || !section"
          @keydown="onKeydown"
        />
        <el-button
          type="primary"
          class="send-btn"
          :icon="Promotion"
          :loading="loading"
          :disabled="!input.trim() || !section"
          @click="sendMessage()"
        >
          发送
        </el-button>
      </div>
    </el-card>

  </aside>
</template>

<style scoped>
.ai-tutor-aside {
  flex: 0 0 300px;
  width: 300px;
  max-width: 100%;
}

.ai-tutor-card {
  position: sticky;
  top: 12px;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 88px);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-aside-gradient);
  border-radius: var(--alp-radius-card);
}

.ai-tutor-card :deep(.el-card__header) {
  padding: 12px 14px;
  border-bottom: 1px solid var(--alp-color-border);
}

.ai-tutor-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  padding: 12px 14px 14px;
  gap: 10px;
}

.ai-tutor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ai-tutor-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: var(--alp-color-text);
}

.ai-tutor-icon {
  font-size: 18px;
  color: var(--alp-color-primary);
}

.ai-tutor-messages {
  flex: 1;
  min-height: 200px;
  max-height: min(420px, calc(100vh - 320px));
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
}

.ai-tutor-welcome {
  font-size: 13px;
  line-height: 1.6;
  color: var(--alp-color-muted);
}

.welcome-lead {
  margin: 0 0 8px;
  color: var(--alp-color-text);
}

.welcome-section {
  margin: 0 0 8px;
}

.section-name {
  color: var(--alp-color-primary);
  font-weight: 500;
}

.welcome-hint {
  margin: 0;
  font-size: 12px;
}

.msg-row {
  display: flex;
  margin-bottom: 10px;
}

.msg-row--user {
  justify-content: flex-end;
}

.msg-bubble {
  max-width: 92%;
  padding: 8px 10px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.55;
}

.msg-row--user .msg-bubble {
  background: var(--alp-color-primary-soft);
  border: 1px solid rgba(56, 189, 248, 0.35);
}

.msg-row--assistant .msg-bubble {
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.msg-bubble--loading .msg-text {
  opacity: 0.7;
  font-style: italic;
}

.msg-role {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-muted);
  margin-bottom: 4px;
}

.msg-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--alp-color-text);
}

.msg-text--md {
  white-space: normal;
}

.msg-text--md :deep(.ai-md-p) {
  margin: 0 0 0.5em;
  line-height: 1.6;
}

.msg-text--md :deep(.ai-md-p:last-child) {
  margin-bottom: 0;
}

.msg-text--md :deep(.ai-md-h) {
  margin: 0.75em 0 0.35em;
  font-size: 0.92em;
  font-weight: 600;
  line-height: 1.45;
  color: var(--alp-color-primary);
}

.msg-text--md :deep(.ai-md-h:first-child),
.msg-text--md :deep(.ai-md-ul:first-child),
.msg-text--md :deep(.ai-md-ol:first-child) {
  margin-top: 0;
}

.msg-text--md :deep(.ai-md-ul),
.msg-text--md :deep(.ai-md-ol) {
  margin: 0.35em 0 0.5em;
  padding-left: 1.15em;
  line-height: 1.55;
}

.msg-text--md :deep(.ai-md-li),
.msg-text--md :deep(li) {
  margin: 0.2em 0;
}

.msg-text--md :deep(.ai-md-code) {
  padding: 0.1em 0.35em;
  font-size: 0.88em;
  font-family: ui-monospace, Consolas, monospace;
  background: var(--alp-bg-code-ish);
  border-radius: 4px;
  color: #7dd3fc;
}

.msg-text--md :deep(.ai-md-pre) {
  margin: 0.5em 0;
  padding: 0.5em 0.65em;
  overflow-x: auto;
  font-size: 0.82em;
  line-height: 1.5;
  background: var(--alp-bg-code-ish);
  border: 1px solid var(--alp-color-border);
  border-radius: 6px;
}

.msg-text--md :deep(.ai-md-pre--streaming) {
  border-style: dashed;
  opacity: 0.95;
}

.msg-text--md :deep(.ai-md-pre code) {
  font-family: ui-monospace, Consolas, monospace;
  color: var(--alp-color-text);
}

.msg-text--md :deep(strong) {
  font-weight: 600;
  color: var(--alp-color-text);
}

.ai-tutor-quick {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.quick-label {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.quick-chip {
  text-align: left;
  padding: 6px 10px;
  font-size: 12px;
  line-height: 1.45;
  color: var(--alp-color-text);
  background: var(--alp-bg-nav);
  border: 1px solid var(--alp-color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: background var(--alp-transition-fast);
}

.quick-chip:hover:not(:disabled) {
  background: var(--alp-bg-nav-hover);
  border-color: rgba(56, 189, 248, 0.35);
}

.quick-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-tutor-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-tutor-input :deep(.el-textarea__inner) {
  font-size: 13px;
  background: var(--alp-bg-code-ish);
  color: var(--alp-color-text);
  box-shadow: none;
}

.send-btn {
  align-self: flex-end;
}

@media (max-width: 1280px) {
  .ai-tutor-aside {
    flex: none;
    width: 100%;
  }

  .ai-tutor-card {
    position: relative;
    top: 0;
    max-height: none;
  }

  .ai-tutor-messages {
    max-height: 280px;
  }
}
</style>
