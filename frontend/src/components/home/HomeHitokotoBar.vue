<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

interface HitokotoSentence {
  hitokoto: string
  from?: string
  from_who?: string
  uuid?: string
}

const HITOKOTO_ENDPOINT = 'https://v1.hitokoto.cn/?c=e&c=i&c=k&encode=json&charset=utf-8&max_length=36'
const CACHE_KEY = 'algopilot:positive-hitokoto'
const CACHE_TTL = 30 * 60 * 1000

const fallbackSentences: HitokotoSentence[] = [
  { hitokoto: '不积跬步，无以至千里；不积小流，无以成江海。', from: '荀子·劝学' },
  { hitokoto: '纸上得来终觉浅，绝知此事要躬行。', from: '冬夜读书示子聿', from_who: '陆游' },
  { hitokoto: '追风赶月莫停留，平芜尽处是春山。', from: '华夏说' },
]

const positiveSignals = /学习|求知|成长|进步|努力|坚持|勇气|勇敢|希望|梦想|未来|光明|热爱|美好|明天|行动|前行|向前|出发|抵达|成功|力量|自信|勤奋|奋斗|千里|躬行|春山|星光|阳光|新生|创造|改变|超越/
const negativeSignals = /死亡|死去|绝望|痛苦|悲伤|孤独|遗憾|仇恨|憎恨|毁灭|放弃|失败|无望|黑暗|哭泣|离别|失去|自杀|杀死|坟墓|地狱|折磨|恐惧/

const sentence = ref<HitokotoSentence>(fallbackSentences[0])
const loading = ref(false)
let controller: AbortController | null = null

function isPositiveSentence(value: unknown): value is HitokotoSentence {
  if (!value || typeof value !== 'object') return false
  const candidate = value as HitokotoSentence
  const text = candidate.hitokoto?.trim()
  return Boolean(text && text.length <= 36 && positiveSignals.test(text) && !negativeSignals.test(text))
}

function useFallback() {
  const alternatives = fallbackSentences.filter((item) => item.hitokoto !== sentence.value.hitokoto)
  sentence.value = alternatives[Math.floor(Math.random() * alternatives.length)] ?? fallbackSentences[0]
}

function readCache(): HitokotoSentence | null {
  try {
    const cached = JSON.parse(sessionStorage.getItem(CACHE_KEY) ?? 'null') as { savedAt?: number; sentence?: unknown } | null
    if (!cached?.savedAt || Date.now() - cached.savedAt > CACHE_TTL) return null
    return isPositiveSentence(cached.sentence) ? cached.sentence : null
  } catch {
    return null
  }
}

function writeCache(value: HitokotoSentence) {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ savedAt: Date.now(), sentence: value }))
  } catch {
    // Storage can be unavailable in private browsing; the quote still works without caching.
  }
}

async function fetchHitokoto(force = false) {
  if (loading.value) return
  if (!force) {
    const cached = readCache()
    if (cached) {
      sentence.value = cached
      return
    }
  }

  controller?.abort()
  controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller?.abort(), 4500)
  loading.value = true

  try {
    const response = await fetch(HITOKOTO_ENDPOINT, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
    if (!response.ok) throw new Error(`Hitokoto request failed with ${response.status}`)
    const data: unknown = await response.json()
    if (!isPositiveSentence(data)) {
      useFallback()
      return
    }
    sentence.value = data
    writeCache(data)
  } catch {
    useFallback()
  } finally {
    window.clearTimeout(timeoutId)
    loading.value = false
  }
}

function refresh() {
  void fetchHitokoto(true)
}

onMounted(() => void fetchHitokoto())
onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <section class="hitokoto" aria-label="积极一言" :aria-busy="loading">
    <a
      class="hitokoto__text"
      :href="sentence.uuid ? `https://hitokoto.cn?uuid=${sentence.uuid}` : 'https://hitokoto.cn'"
      target="_blank"
      rel="noopener noreferrer"
      :title="`${sentence.hitokoto} · ${sentence.from_who || sentence.from || '一言'}`"
    >
      ，{{ sentence.hitokoto }}
    </a>
    <button type="button" class="hitokoto__refresh" :disabled="loading" aria-label="换一句积极一言" @click="refresh">
      <el-icon><Refresh /></el-icon>
    </button>
  </section>
</template>

<style scoped>
.hitokoto {
  display: flex;
  align-items: baseline;
  gap: 7px;
  min-width: 0;
  color: #102b31;
  font-size: 25px;
  font-weight: 780;
  line-height: 1.2;
  letter-spacing: -.025em;
}

.hitokoto__text {
  overflow: hidden;
  color: inherit;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hitokoto__text:hover,
.hitokoto__text:focus-visible {
  color: var(--color-brand);
}

.hitokoto__refresh {
  display: inline-grid;
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
  padding: 0;
  place-items: center;
  color: #829395;
  border: 0;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  transition: color 160ms ease, background-color 160ms ease, transform 240ms ease;
}

.hitokoto__refresh:hover:not(:disabled),
.hitokoto__refresh:focus-visible {
  color: var(--color-brand);
  background: var(--color-brand-soft);
  outline: none;
}

.hitokoto__refresh:hover:not(:disabled) { transform: rotate(180deg); }
.hitokoto__refresh:disabled { cursor: wait; opacity: .55; }

@media (max-width: 820px) {
  .hitokoto { width: 100%; }
}

@media (max-width: 520px) {
  .hitokoto { font-size: 21px; }
}

@media (prefers-reduced-motion: reduce) {
  .hitokoto__refresh { transition: none; }
}
</style>
