<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import landscapeUrl from '@/assets/home-quote-landscape.png'

interface HitokotoSentence {
  hitokoto: string
  from?: string
  from_who?: string
  uuid?: string
}

const sentence = ref<HitokotoSentence | null>(null)
const loading = ref(false)

const fallbackSentences: HitokotoSentence[] = [
  { hitokoto: '用代码表达言语的魅力，用代码书写山河的壮丽。', from: '一言开发者中心', from_who: '一言' },
  { hitokoto: '不积跬步，无以至千里；不积小流，无以成江海。', from: '荀子·劝学' },
  { hitokoto: '纸上得来终觉浅，绝知此事要躬行。', from: '冬夜读书示子聿', from_who: '陆游' },
]

async function fetchHitokoto() {
  loading.value = true
  try {
    const response = await fetch('https://v1.hitokoto.cn/?encode=json')
    if (!response.ok) throw new Error('network error')
    const data = (await response.json()) as HitokotoSentence
    sentence.value = data
  } catch {
    // 网络异常时使用本地兜底句子，保证页面始终有内容
    const index = Math.floor(Math.random() * fallbackSentences.length)
    sentence.value = fallbackSentences[index]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void fetchHitokoto()
})
</script>

<template>
  <section class="hitokoto-bar" aria-label="一言">
    <img class="hitokoto-bar__landscape" :src="landscapeUrl" alt="" aria-hidden="true" />
    <div class="hitokoto-bar__inner">
      <span class="hitokoto-bar__quote" aria-hidden="true">“</span>
      <p v-if="sentence" class="hitokoto-bar__text">
        「{{ sentence.hitokoto }}」
        <span v-if="sentence.from_who || sentence.from" class="hitokoto-bar__from">
          —— {{ sentence.from_who || sentence.from }}
        </span>
      </p>
      <p v-else class="hitokoto-bar__text hitokoto-bar__text--loading">正在获取今日一言…</p>
      <button
        type="button"
        class="hitokoto-bar__refresh"
        :disabled="loading"
        title="换一句"
        @click="fetchHitokoto"
      >
        <el-icon><Refresh /></el-icon>
      </button>
    </div>
  </section>
</template>

<style scoped>
.hitokoto-bar {
  position: relative;
  margin-bottom: 16px;
  min-height: 64px;
  box-sizing: border-box;
  padding: 12px 34px;
  overflow: hidden;
  border: 1px solid #deeceb;
  border-radius: 15px;
  background: linear-gradient(104deg, #ffffff 0%, #fbfefe 68%, #eff9f8 100%);
  box-shadow: 0 5px 16px rgba(28, 89, 90, 0.035);
}

.hitokoto-bar__landscape { position: absolute; right: 0; bottom: 0; width: 50%; height: 100%; object-fit: cover; object-position: right center; opacity: .9; pointer-events: none; }

.hitokoto-bar__inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 14px;
  max-width: none;
  margin: 0;
}

.hitokoto-bar__quote { flex: 0 0 auto; color: #73c9c5; font-family: Georgia, serif; font-size: 43px; font-weight: 700; line-height: .6; transform: translateY(-2px); }

.hitokoto-bar__text {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
  text-align: left;
  letter-spacing: 0.02em;
}

.hitokoto-bar__text--loading {
  color: var(--color-text-muted);
  font-size: 13px;
}

.hitokoto-bar__from {
  display: inline-block;
  margin-left: 22px;
  color: var(--color-text-muted);
  font-size: 13px;
  white-space: nowrap;
}

.hitokoto-bar__refresh {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  cursor: pointer;
  transition: color 180ms ease, border-color 180ms ease, transform 320ms ease, background-color 180ms ease;
}

.hitokoto-bar__refresh:hover:not(:disabled) {
  color: var(--color-brand);
  border-color: var(--color-brand);
  background: var(--color-brand-soft);
  transform: rotate(180deg);
}

.hitokoto-bar__refresh:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

@media (max-width: 760px) {
  .hitokoto-bar {
    padding: 12px 14px;
  }

  .hitokoto-bar__landscape { width: 65%; opacity: .38; }

  .hitokoto-bar__text {
    font-size: 14px;
  }

  .hitokoto-bar__from {
    display: block;
    margin-left: 0;
    margin-top: 4px;
  }
}
</style>
