import { onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { synthesizeTtsAudio } from '@/api/tts'

let activeAudio: HTMLAudioElement | null = null
let activeObjectUrl: string | null = null

function stopPlayback() {
  if (activeAudio) {
    activeAudio.pause()
    activeAudio.src = ''
    activeAudio = null
  }
  if (activeObjectUrl) {
    URL.revokeObjectURL(activeObjectUrl)
    activeObjectUrl = null
  }
}

/** 教案「AI 朗读」→ 后端科大讯飞 TTS 合成 MP3 并播放 */
export function useArticleTts() {
  const reading = ref(false)

  async function readArticle(markdownOrHtml: string, _title?: string) {
    const plain = markdownOrHtml
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 2800)

    if (!plain) {
      ElMessage.warning('暂无正文可朗读')
      return
    }

    reading.value = true
    stopPlayback()

    try {
      const blob = await synthesizeTtsAudio({ text: plain })
      activeObjectUrl = URL.createObjectURL(blob)
      activeAudio = new Audio(activeObjectUrl)
      activeAudio.onended = () => stopPlayback()
      activeAudio.onerror = () => {
        ElMessage.error('音频播放失败')
        stopPlayback()
      }
      await activeAudio.play()
      ElMessage.success('正在播放（科大讯飞语音合成）')
    } catch {
      stopPlayback()
    } finally {
      reading.value = false
    }
  }

  onUnmounted(stopPlayback)

  return { reading, readArticle }
}
