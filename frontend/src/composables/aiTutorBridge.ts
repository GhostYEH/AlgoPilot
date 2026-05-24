import { inject, provide, type InjectionKey, type Ref } from 'vue'

export interface AiTutorBridge {
  /** 向右侧 AI 助教提问（已格式化或原始问题） */
  ask: (message: string) => void | Promise<void>
  /** 是否正在等待 AI 回复 */
  loading: Ref<boolean>
}

export const AI_TUTOR_BRIDGE_KEY: InjectionKey<AiTutorBridge> = Symbol('aiTutorBridge')

export function provideAiTutorBridge(bridge: AiTutorBridge) {
  provide(AI_TUTOR_BRIDGE_KEY, bridge)
}

export function useAiTutorBridge(): AiTutorBridge | null {
  return inject(AI_TUTOR_BRIDGE_KEY, null)
}

/** 将划词内容格式化为发给助教的问题 */
export function formatSelectionQuestion(selectedText: string): string {
  const maxQuote = 360
  let quote = selectedText.trim().replace(/\s+/g, ' ')
  if (quote.length > maxQuote) quote = `${quote.slice(0, maxQuote)}…`
  return `我在学习当前小节时，对下面这句话不太理解，请结合本节内容用通俗的话解释一下，并举例说明（若合适）：\n\n「${quote}」`
}
