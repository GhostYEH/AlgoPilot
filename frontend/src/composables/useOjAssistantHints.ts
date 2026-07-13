import { ref, watch, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { ProblemDetail } from '@/api/oj'
import { streamOjAssistant } from '@/api/ojAssistant'
import { fetchSystemHealth } from '@/api/health'
import {
  formatSampleInput,
  formatSampleOutput,
} from '@/utils/ojSampleFormat'

let _llmCache: { ok: boolean; ts: number } | null = null

async function _checkLlm(): Promise<boolean> {
  const now = Date.now()
  if (_llmCache && now - _llmCache.ts < 60_000) return _llmCache.ok
  const h = await fetchSystemHealth()
  const ok = h?.llm_configured === true
  _llmCache = { ok, ts: now }
  return ok
}

export function useOjAssistantHints(
  problem: Ref<ProblemDetail | null | undefined>,
  language: Ref<'python' | 'cpp'>,
  userCode: Ref<string>,
) {
  const dsLoading = ref(false)
  const codeLoading = ref(false)
  const dsReply = ref('')
  const codeReply = ref('')
  /** 流式中：用于卡片显示“AI 正在输出”光标 */
  const dsStreaming = ref(false)
  const codeStreaming = ref(false)

  function buildSamplesText(): string {
    const p = problem.value
    if (!p?.samples?.length) return ''
    return p.samples
      .map((s, i) => {
        const inp = formatSampleInput(s)
        const out = formatSampleOutput(s)
        return `【样例 ${i + 1}】\n输入：${inp}\n输出：${out}`
      })
      .join('\n\n')
  }

  function baseParams() {
    const p = problem.value!
    return {
      problemSlug: p.slug,
      problemTitle: p.title,
      problemDescription: p.description,
      difficulty: p.difficulty,
      judgeMode: p.judge_mode ?? 'stdio',
      entryMethod: p.entry?.method ?? null,
      language: language.value,
      samplesText: buildSamplesText(),
    }
  }

  async function fetchDsHint() {
    if (!problem.value) return
    if (!(await _checkLlm())) {
      ElMessage.warning('AI 未配置，请在 .env 中配置 AI 模型 API Key')
      return
    }
    dsLoading.value = true
    dsStreaming.value = true
    dsReply.value = ''
    try {
      await streamOjAssistant(
        { ...baseParams(), mode: 'ds_hint', userCode: '' },
        {
          onToken: (chunk) => {
            dsReply.value += chunk
          },
          onDone: (full) => {
            if (full) dsReply.value = full
          },
          onError: () => {
            /* toast in api */
          },
        },
      )
    } catch {
      /* toast in api */
    } finally {
      dsLoading.value = false
      dsStreaming.value = false
    }
  }

  async function fetchCodeHint() {
    if (!problem.value) return
    if (!(await _checkLlm())) {
      ElMessage.warning('AI 未配置，请在 .env 中配置 AI 模型 API Key')
      return
    }
    codeLoading.value = true
    codeStreaming.value = true
    codeReply.value = ''
    try {
      await streamOjAssistant(
        { ...baseParams(), mode: 'code_hint', userCode: userCode.value },
        {
          onToken: (chunk) => {
            codeReply.value += chunk
          },
          onDone: (full) => {
            if (full) codeReply.value = full
          },
          onError: () => {
            /* toast in api */
          },
        },
      )
    } catch {
      /* toast in api */
    } finally {
      codeLoading.value = false
      codeStreaming.value = false
    }
  }

  watch(
    () => problem.value?.slug,
    () => {
      dsReply.value = ''
      codeReply.value = ''
    },
  )

  return {
    dsLoading,
    codeLoading,
    dsStreaming,
    codeStreaming,
    dsReply,
    codeReply,
    fetchDsHint,
    fetchCodeHint,
  }
}
