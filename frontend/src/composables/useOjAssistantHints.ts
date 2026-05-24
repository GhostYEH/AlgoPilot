import { ref, watch, type Ref } from 'vue'
import type { ProblemDetail } from '@/api/oj'
import { postOjAssistant } from '@/api/ojAssistant'
import {
  formatSampleInput,
  formatSampleOutput,
} from '@/utils/ojSampleFormat'

export function useOjAssistantHints(
  problem: Ref<ProblemDetail | null | undefined>,
  language: Ref<'python' | 'cpp'>,
  userCode: Ref<string>,
) {
  const dsLoading = ref(false)
  const codeLoading = ref(false)
  const dsReply = ref('')
  const codeReply = ref('')

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
    dsLoading.value = true
    dsReply.value = ''
    try {
      const { reply } = await postOjAssistant({
        ...baseParams(),
        mode: 'ds_hint',
        userCode: '',
      })
      dsReply.value = reply
    } catch {
      /* toast in api */
    } finally {
      dsLoading.value = false
    }
  }

  async function fetchCodeHint() {
    if (!problem.value) return
    codeLoading.value = true
    codeReply.value = ''
    try {
      const { reply } = await postOjAssistant({
        ...baseParams(),
        mode: 'code_hint',
        userCode: userCode.value,
      })
      codeReply.value = reply
    } catch {
      /* toast in api */
    } finally {
      codeLoading.value = false
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
    dsReply,
    codeReply,
    fetchDsHint,
    fetchCodeHint,
  }
}
