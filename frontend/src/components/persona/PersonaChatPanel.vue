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
import { invalidatePersonaCache } from '@/composables/usePersonaGate'
import { usePersonaStore } from '@/stores/pinia/persona'
import PersonaRadarChart from '@/components/persona/PersonaRadarChart.vue'
import PersonaEvidenceChain from '@/components/persona/PersonaEvidenceChain.vue'

interface UiMsg {
  id: number
  role: 'user' | 'assistant'
  content: string
}

const ICEBREAKER_PROMPTS = [
  '你好！欢迎加入算法智能学习平台 🎓 我是你的**学习画像 Agent**。先聊聊：你目前是大几、什么专业？对数据结构（数组、链表等）熟悉到什么程度？',
  '很棒！第二个问题：你平时写代码报错时，**最怕遇到哪种情况**？比如边界越界、递归写不对、还是看不懂题意？',
  '最后一个问题：你的**学习目标**是什么（课内及格 / 蓝桥杯 / 考研 / 就业面试）？遇到 WA 或 TLE 时，你一般会坚持多久？',
]

const input = ref('')
const loading = ref(false)
const syncing = ref(false)
const messages = ref<UiMsg[]>([])
const listRef = ref<HTMLElement | null>(null)
const profile = ref<PersonaProfile | null>(null)
const profileLoading = ref(false)
const profileError = ref(false)
const { replan: replanPath } = useLearningPathPlan()
const personaStore = usePersonaStore()
let msgId = 0
const profileUpdateHintShown = ref(false)
const showRadar = ref(false)
const icebreakerDone = ref(false)
const autoFlowRunning = ref(false)
const personaFallbackMode = ref(false)
const personaFallbackReason = ref('')

const emit = defineEmits<{
  profileReady: [profile: PersonaProfile]
}>()

const userTurnCount = computed(
  () => messages.value.filter((m) => m.role === 'user').length,
)

const showProfileNudge = computed(
  () => userTurnCount.value >= 3 && !profile.value?.updated_at && !autoFlowRunning.value,
)

function scrollBottom() {
  nextTick(() => {
    const el = listRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function loadProfile() {
  profileLoading.value = true
  profileError.value = false
  try {
    profile.value = await fetchPersonaProfile()
    if (profile.value) personaStore.setProfile(profile.value)
    if (profile.value?.updated_at && profile.value.dimensions) {
      showRadar.value = true
      icebreakerDone.value = true
    }
    personaFallbackMode.value = !!profile.value?.fallback
    personaFallbackReason.value = profile.value?.fallback_reason ?? ''
  } catch {
    profile.value = null
    profileError.value = true
  } finally {
    profileLoading.value = false
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
    if (hist.length > 0) icebreakerDone.value = true
  } catch {
    /* ignore */
  }
}

function pushAssistant(text: string) {
  messages.value.push({ id: ++msgId, role: 'assistant', content: text })
  scrollBottom()
}

async function startIcebreaker() {
  if (messages.value.length > 0 || icebreakerDone.value) return
  for (const prompt of ICEBREAKER_PROMPTS) {
    pushAssistant(prompt)
    await new Promise((r) => setTimeout(r, 400))
  }
}

onMounted(async () => {
  await loadProfile()
  await loadHistory()
  if (messages.value.length === 0 && !profile.value?.updated_at) {
    await startIcebreaker()
  }
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
        onDone(_full, meta) {
          personaFallbackMode.value = !!meta?.fallback
          personaFallbackReason.value = meta?.fallback_reason ?? ''
        },
      },
    )
  } finally {
    loading.value = false
    if (userTurnCount.value >= 3 && !profile.value?.updated_at) {
      void autoCompleteProfileFlow()
    } else if (userTurnCount.value >= 5 && !profileUpdateHintShown.value) {
      profileUpdateHintShown.value = true
      ElMessage.info('对话已较充分，可点击「从对话更新画像」同步六维画像')
    }
  }
}

async function autoCompleteProfileFlow() {
  if (autoFlowRunning.value || profile.value?.updated_at) return
  autoFlowRunning.value = true
  icebreakerDone.value = true
  try {
    pushAssistant(
      '感谢你的分享！正在根据对话抽取 **六维学习画像** 并生成专属学习路径，请稍候…',
    )
    const { profile: p } = await syncPersonaFromStored()
    profile.value = p
    personaFallbackMode.value = !!p.fallback
    personaFallbackReason.value = p.fallback_reason ?? ''
    showRadar.value = true
    invalidatePersonaCache()
    emit('profileReady', p)
    ElMessage.success('六维画像已生成，雷达图已更新')
    try {
      await replanPath({ trigger: 'persona', triggerLabel: '画像更新后重排' })
      ElMessage.success('PlannerAgent 已根据画像生成千人千面学习路径')
    } catch {
      ElMessage.warning('路径规划稍后可在「学习路径」页重试')
    }
  } catch {
    ElMessage.warning('画像同步失败，请手动点击「从对话更新画像」')
  } finally {
    autoFlowRunning.value = false
  }
}

async function onSyncProfile() {
  if (syncing.value) return
  try {
    await ElMessageBox.confirm(
      '将根据当前对话抽取六维画像并写入数据库。是否继续？',
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
    personaFallbackMode.value = !!p.fallback
    personaFallbackReason.value = p.fallback_reason ?? ''
    showRadar.value = true
    invalidatePersonaCache()
    emit('profileReady', p)
    ElMessage.success(message)
    try {
      await ElMessageBox.confirm(
        '画像已更新。是否立即调用 PlannerAgent 重排模块顺序？',
        '重排学习路径',
        { confirmButtonText: '重排', cancelButtonText: '稍后' },
      )
      await replanPath({ trigger: 'persona', triggerLabel: '画像更新后重排' })
      ElMessage.success('学习路径已根据新画像重排')
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
    score: profile.value?.dimension_scores?.[key],
  }))
</script>

<template>
  <div class="persona-layout">
    <div class="persona-chat">
      <el-alert
        v-if="personaFallbackMode || profile?.fallback"
        type="warning"
        :closable="false"
        show-icon
        class="fallback-banner"
        title="当前为离线画像引导模式"
        :description="
          personaFallbackReason ||
          profile?.fallback_reason ||
          '未连接大模型，正在使用 TemplatePersonaFallbackAgent 规则模板追问，非 AI 深度分析。'
        "
      />
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
          <span class="chat-role">{{ m.role === 'user' ? '你' : (personaFallbackMode || profile?.fallback ? '离线引导' : '画像 Agent') }}</span>
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
          :disabled="loading || autoFlowRunning"
          @keydown.enter.exact.prevent="send"
        />
        <el-button
          type="primary"
          :icon="Promotion"
          :loading="loading"
          :disabled="autoFlowRunning"
          @click="send"
        >
          发送
        </el-button>
      </div>
      <el-alert
        v-if="showProfileNudge"
        type="info"
        :closable="false"
        show-icon
        title="已完成 3 轮破冰对话，回复后将自动抽取画像并生成路径"
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
        <span>学习画像 · 6 维</span>
      </div>
      <p v-if="profile?.summary" class="dims-summary">{{ profile.summary }}</p>
      <p v-else class="dims-summary muted">完成 3 轮破冰对话后将自动生成画像</p>
      <PersonaRadarChart
        v-if="profile?.dimensions && showRadar"
        :dimensions="profile.dimensions"
        :scores="profile.dimension_scores"
        animated
      />
      <p v-else-if="autoFlowRunning" class="dims-summary muted">画像抽取中…</p>

      <ul v-if="profile?.dimensions && profile.updated_at" class="dims-list">
        <li v-for="d in dimensionEntries(profile.dimensions)" :key="d.key">
          <span class="dims-label">
            {{ d.label }}
            <em v-if="d.score" class="dims-score">{{ d.score }}/10</em>
          </span>
          <el-tag v-if="d.confidence === 'explicit'" size="small" type="success" effect="plain">
            明确
          </el-tag>
          <el-tag v-else-if="d.confidence === 'inferred'" size="small" type="info" effect="plain">
            推断
          </el-tag>
          <span class="dims-value">{{ d.value }}</span>
        </li>
      </ul>
      <p v-if="profile?.coverage_missing?.length" class="dims-missing muted">
        待补全：{{
          profile.coverage_missing
            .map((k) => PROFILE_DIMENSION_LABELS[k as keyof PersonaDimensions] ?? k)
            .join('、')
        }}
      </p>
      <p v-if="profile?.updated_at" class="dims-time">更新于 {{ profile.updated_at }}</p>
    </aside>

    <PersonaEvidenceChain
      class="persona-evidence-full"
      :profile="profile"
      :loading="profileLoading"
      :error="profileError"
      @retry="loadProfile"
    />
  </div>
</template>

<style scoped>
.persona-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 16px;
  min-height: 420px;
}

.persona-evidence-full {
  grid-column: 1 / -1;
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

.fallback-banner {
  margin-bottom: 4px;
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

.dims-score {
  font-style: normal;
  font-weight: 500;
  color: var(--alp-color-muted);
  margin-left: 4px;
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
