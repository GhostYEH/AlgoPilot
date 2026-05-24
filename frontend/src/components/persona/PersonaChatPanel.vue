<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound, Promotion, Refresh } from '@element-plus/icons-vue'
import {
  fetchPersonaHistory,
  fetchPersonaProfile,
  PROFILE_DIMENSION_LABELS,
  streamPersonaChat,
  syncPersonaFromStored,
  type ChatHistoryItem,
  type PersonaDimensions,
  type PersonaProfile,
} from '@/api/orchestrator'
import { renderAiReplyHtml } from '@/utils/renderAiReply'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'
import PersonaRadarChart from '@/components/persona/PersonaRadarChart.vue'

interface UiMsg {
  id: number
  role: 'user' | 'assistant'
  content: string
}

const input = ref('')
const loading = ref(false)
const syncing = ref(false)
const messages = ref<UiMsg[]>([])
const listRef = ref<HTMLElement | null>(null)
const profile = ref<PersonaProfile | null>(null)
const { replan: replanPath } = useLearningPathPlan()
let msgId = 0
const profileUpdateHintShown = ref(false)

const userTurnCount = computed(
  () => messages.value.filter((m) => m.role === 'user').length,
)

const showProfileNudge = computed(
  () => userTurnCount.value >= 5 && !profileUpdateHintShown.value,
)

function scrollBottom() {
  nextTick(() => {
    const el = listRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function loadProfile() {
  try {
    profile.value = await fetchPersonaProfile()
  } catch {
    profile.value = null
  }
}

async function loadHistory() {
  try {
    const hist = await fetchPersonaHistory()
    messages.value = hist.map((h) => ({
      id: ++msgId,
      role: h.role,
      content: h.content,
    }))
  } catch {
    /* ignore */
  }
}

onMounted(async () => {
  await loadProfile()
  await loadHistory()
})

function toHistory(): ChatHistoryItem[] {
  return messages.value.map((m) => ({ role: m.role, content: m.content }))
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  input.value = ''
  messages.value.push({ id: ++msgId, role: 'user', content: text })
  scrollBottom()
  loading.value = true
  const assistantId = ++msgId
  messages.value.push({ id: assistantId, role: 'assistant', content: '' })

  const history = toHistory().slice(0, -2)

  try {
    await streamPersonaChat(
      { message: text, history },
      {
        onToken(chunk) {
          const row = messages.value.find((m) => m.id === assistantId)
          if (row) row.content += chunk
          scrollBottom()
        },
      },
    )
  } finally {
    loading.value = false
    if (userTurnCount.value >= 5 && !profileUpdateHintShown.value) {
      profileUpdateHintShown.value = true
      ElMessage.info('对话已超 5 轮，建议点击「从对话更新画像」同步七维画像')
    }
  }
}

async function onSyncProfile() {
  if (syncing.value) return
  try {
    await ElMessageBox.confirm(
      '将根据当前对话抽取七维画像并写入数据库。是否继续？',
      '更新学习画像',
      { type: 'info' },
    )
  } catch {
    return
  }
  syncing.value = true
  try {
    const { profile: p, message } = await syncPersonaFromStored()
    profile.value = p
    ElMessage.success(message)
    try {
      await ElMessageBox.confirm(
        '画像已更新。是否立即调用学习路径 Agent 重排模块顺序？',
        '重排学习路径',
        { confirmButtonText: '重排', cancelButtonText: '稍后' },
      )
      await replanPath()
      ElMessage.success('学习路径 Agent 已根据新画像重排路线')
    } catch {
      /* 用户取消或路径规划失败 */
    }
  } catch {
    /* request interceptor shows error */
  } finally {
    syncing.value = false
  }
}

const dimensionEntries = (dims: PersonaDimensions) =>
  (Object.keys(PROFILE_DIMENSION_LABELS) as (keyof PersonaDimensions)[]).map((key) => ({
    key,
    label: PROFILE_DIMENSION_LABELS[key],
    value: dims[key] || '待补充',
    confidence: profile.value?.dimension_confidence?.[key] ?? '',
  }))
</script>

<template>
  <div class="persona-layout">
    <div class="persona-chat">
      <div ref="listRef" class="chat-list">
        <p v-if="messages.length === 0" class="chat-empty">
          与<strong>学习画像 Agent</strong>对话，描述你的专业、目标与薄弱点，无需填表。
        </p>
        <div
          v-for="m in messages"
          :key="m.id"
          class="chat-row"
          :class="m.role === 'user' ? 'chat-row--user' : 'chat-row--bot'"
        >
          <span class="chat-role">{{ m.role === 'user' ? '你' : '画像 Agent' }}</span>
          <div
            v-if="m.role === 'assistant'"
            class="chat-bubble ai-md-body"
            v-html="renderAiReplyHtml(m.content || '…')"
          />
          <div v-else class="chat-bubble">{{ m.content }}</div>
        </div>
      </div>
      <div class="chat-input-row">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          placeholder="例如：我是大一计科，想准备蓝桥杯，数组和链表比较薄弱…"
          :disabled="loading"
          @keydown.enter.exact.prevent="send"
        />
        <el-button type="primary" :icon="Promotion" :loading="loading" @click="send">发送</el-button>
      </div>
      <el-alert
        v-if="showProfileNudge"
        type="info"
        :closable="false"
        show-icon
        title="对话已较充分，建议更新画像以便资源推荐与路径规划"
        class="nudge-alert"
      />
      <div class="chat-actions">
        <el-button :icon="Refresh" :loading="syncing" @click="onSyncProfile">
          从对话更新画像（JSON 入库）
        </el-button>
      </div>
    </div>

    <aside class="persona-dims">
      <div class="dims-head">
        <el-icon><ChatDotRound /></el-icon>
        <span>学习画像 · 7 维</span>
      </div>
      <p v-if="profile?.summary" class="dims-summary">{{ profile.summary }}</p>
      <p v-else class="dims-summary muted">对话后点击「从对话更新画像」写入数据库</p>
      <PersonaRadarChart v-if="profile?.dimensions" :dimensions="profile.dimensions" />

      <ul v-if="profile?.dimensions" class="dims-list">
        <li v-for="d in dimensionEntries(profile.dimensions)" :key="d.key">
          <span class="dims-label">{{ d.label }}</span>
          <el-tag v-if="d.confidence === 'explicit'" size="small" type="success" effect="plain">明确</el-tag>
          <el-tag v-else-if="d.confidence === 'inferred'" size="small" type="info" effect="plain">推断</el-tag>
          <span class="dims-value">{{ d.value }}</span>
        </li>
      </ul>
      <p v-if="profile?.coverage_missing?.length" class="dims-missing muted">
        待补全：{{ profile.coverage_missing.map((k) => PROFILE_DIMENSION_LABELS[k as keyof PersonaDimensions] ?? k).join('、') }}
      </p>
      <p v-if="profile?.updated_at" class="dims-time">更新于 {{ profile.updated_at }}</p>
    </aside>
  </div>
</template>

<style scoped>
.persona-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 16px;
  min-height: 420px;
}

@media (max-width: 900px) {
  .persona-layout {
    grid-template-columns: 1fr;
  }
}

.persona-chat {
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  padding: 12px;
  background: var(--alp-bg-soft-block);
}

.chat-list {
  flex: 1;
  min-height: 260px;
  max-height: 360px;
  overflow-y: auto;
  padding: 8px;
}

.chat-empty {
  color: var(--alp-color-muted);
  font-size: 13px;
  line-height: 1.6;
}

.chat-row {
  margin-bottom: 12px;
}

.chat-role {
  font-size: 11px;
  color: var(--alp-color-muted);
  display: block;
  margin-bottom: 4px;
}

.chat-bubble {
  display: inline-block;
  max-width: 95%;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.55;
}

.chat-row--user .chat-bubble {
  background: var(--alp-color-primary);
  color: #fff;
}

.chat-row--bot .chat-bubble {
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
}

.chat-input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chat-input-row .el-textarea {
  flex: 1;
}

.persona-dims {
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  padding: 14px;
  background: var(--alp-bg-surface);
}

.dims-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  margin-bottom: 10px;
}

.dims-summary {
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.dims-summary.muted {
  color: var(--alp-color-muted);
}

.dims-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.dims-list li {
  margin-bottom: 10px;
}

.dims-label {
  display: block;
  font-size: 11px;
  color: var(--alp-color-primary);
  font-weight: 600;
}

.dims-value {
  font-size: 12px;
  color: var(--alp-color-text);
  line-height: 1.45;
}

.dims-time {
  font-size: 11px;
  color: var(--alp-color-muted);
  margin-top: 12px;
}
</style>
