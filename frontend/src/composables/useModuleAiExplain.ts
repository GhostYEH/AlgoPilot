import { ref, watch, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { streamAiTutorChat, type AiTutorChatParams } from '@/api/aiTutor'
import { fetchSystemHealth } from '@/api/health'
import type { AiTutorSectionPayload } from '@/utils/buildLearnContext'

let _llmCache: { ok: boolean; ts: number } | null = null

async function _checkLlm(): Promise<boolean> {
  const now = Date.now()
  if (_llmCache && now - _llmCache.ts < 60_000) return _llmCache.ok
  const h = await fetchSystemHealth()
  const ok = h?.llm_configured === true
  _llmCache = { ok, ts: now }
  return ok
}

export interface ModuleExplainContext {
  moduleKey: string
  moduleLabel: string
  moduleIntro: string
  goals: string[]
  estHours: number
}

/**
 * 模块级 AI 解释（学习路径抽屉用）：按钮触发的流式输出，
 * 风格与 OJ 助教双卡（数据结构提示 / 代码分析）一致。
 */
export function useModuleAiExplain(moduleCtx: Ref<ModuleExplainContext | null>) {
  const loading = ref(false)
  const streaming = ref(false)
  const reply = ref('')

  function buildParams(): AiTutorChatParams | null {
    const ctx = moduleCtx.value
    if (!ctx) return null
    // 构造最小章节上下文：以「概述」作为占位 section，让后端 tutor_chat 能正常调度
    const section: AiTutorSectionPayload = {
      id: 'overview',
      title: `${ctx.moduleLabel} · 概述`,
      subtitle: '核心思想与应用场景',
      difficulty: '入门',
      est_minutes: Math.max(15, Math.round(ctx.estHours * 60)),
      keywords: [],
      overview: ctx.moduleIntro,
      points: ctx.goals,
      topic_blocks: [],
      pitfalls: [],
      checklist: [],
      complexity_hint: null,
      code_sketch: null,
    }
    return {
      message: `请用简洁清晰的语言向初学者解释「${ctx.moduleLabel}」这个算法/数据结构：1) 核心思想与定义；2) 典型应用场景；3) 初学者最常犯的 2-3 个错误；4) 一道典型入门例题（力扣题号+题名）和解题思路。回复使用 Markdown，控制在 400 字以内。`,
      history: [],
      moduleKey: ctx.moduleKey,
      moduleTitle: ctx.moduleLabel,
      chapterTag: '算法知识宇宙',
      moduleIntro: ctx.moduleIntro,
      section,
    }
  }

  async function explain() {
    if (loading.value) return
    const params = buildParams()
    if (!params) return
    if (!(await _checkLlm())) {
      ElMessage.warning('AI 未配置，请在 .env 中配置 AI 模型 API Key')
      return
    }
    loading.value = true
    streaming.value = true
    reply.value = ''
    try {
      await streamAiTutorChat(params, {
        onToken: (chunk) => {
          reply.value += chunk
        },
        onDone: (full) => {
          if (full) reply.value = full
        },
        onError: () => {
          /* toast in api */
        },
      })
    } catch {
      /* toast in api */
    } finally {
      loading.value = false
      streaming.value = false
    }
  }

  function reset() {
    reply.value = ''
    loading.value = false
    streaming.value = false
  }

  // 切换模块时清空已有解释
  watch(
    () => moduleCtx.value?.moduleKey,
    () => reset(),
  )

  return {
    loading,
    streaming,
    reply,
    explain,
    reset,
  }
}
