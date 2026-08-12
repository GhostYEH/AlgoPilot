import type { InjectionKey, Ref } from 'vue'
import { inject, ref } from 'vue'

export const traceHighlightLineKey: InjectionKey<Ref<number>> = Symbol('traceHighlightLine')

export function useTraceHighlightLine() {
  return inject(traceHighlightLineKey, ref(0))
}
