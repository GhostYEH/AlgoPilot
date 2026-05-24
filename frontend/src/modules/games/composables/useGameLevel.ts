import { ref, watch, type Ref } from 'vue'

export function useGameLevel(
  levelId: () => string,
  reset: () => void,
) {
  const msg = ref('')
  const won = ref(false)
  const fail = ref(false)

  watch(levelId, () => {
    reset()
    msg.value = ''
    won.value = false
    fail.value = false
  }, { immediate: true })

  function win(text: string, emit: () => void) {
    won.value = true
    fail.value = false
    msg.value = text
    emit()
  }

  function hint(text: string) {
    fail.value = false
    msg.value = text
  }

  function error(text: string) {
    fail.value = true
    msg.value = text
  }

  return { msg, won, fail, win, hint, error }
}

export function shakeRef(key: Ref<number>) {
  key.value++
}
