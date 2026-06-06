import { computed, provide, type ComputedRef, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import type AiTutorPanel from '@/components/learning/AiTutorPanel.vue'
import { AI_TUTOR_BRIDGE_KEY } from './aiTutorBridge'

type PanelInstance = InstanceType<typeof AiTutorPanel> | null

function panelLoading(panelRef: Ref<PanelInstance>): ComputedRef<boolean> {
  return computed(() => {
    const exposed = panelRef.value as { isLoading?: boolean } | null
    return exposed?.isLoading === true
  })
}

/** 在学习页挂载：将右侧 AiTutorPanel 的 ref 桥接给划词提问等子组件 */
export function useProvideAiTutorFromPanel(panelRef: Ref<PanelInstance>) {
  provide(AI_TUTOR_BRIDGE_KEY, {
    ask: (message: string) => {
      if (!panelRef.value) {
        console.warn('[AiTutorBridge] panelRef.value is null')
        ElMessage.warning('AI 助教尚未就绪，请稍后再试')
        return
      }
      console.log('[AiTutorBridge] askQuestion:', message)
      void panelRef.value.askQuestion(message)
    },
    loading: panelLoading(panelRef),
  })
}
