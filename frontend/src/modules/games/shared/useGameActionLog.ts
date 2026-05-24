import { ref } from 'vue'

export function useGameActionLog() {
  const actionLog = ref<string[]>([])

  function pushLog(text: string) {
    const t = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    actionLog.value = [`[${t}] ${text}`, ...actionLog.value].slice(0, 8)
  }

  function clearLog(initial?: string) {
    actionLog.value = []
    if (initial) pushLog(initial)
  }

  return { actionLog, pushLog, clearLog }
}
