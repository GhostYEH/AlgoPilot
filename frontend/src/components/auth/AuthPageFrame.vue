<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '@/components/common/BrandLogo.vue'

const LoginGlobe = defineAsyncComponent({
  loader: () => import('@/components/auth/LoginGlobe.vue'),
  suspensible: false,
})

const props = withDefaults(
  defineProps<{
    variant?: 'login' | 'register'
  }>(),
  { variant: 'login' },
)

const router = useRouter()

const hero = computed(() =>
  props.variant === 'register'
    ? {
        title: '建立自己的学习档案',
        desc: '保存章节进度、练习记录与学习路径，换一台设备也能接着学。',
        note: '完成注册后即可开始',
      }
    : {
        title: '从上次停下的地方继续',
        desc: '登录后，你的章节进度、练习记录与学习路径会保持同步。',
        note: '登录只需要几秒钟',
      },
)

function goHome() {
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="auth-shell">
    <header class="auth-top">
      <button type="button" class="brand" aria-label="返回算法智能学习平台首页" @click="goHome">
        <BrandLogo size="auth" :show-subtitle="true" />
      </button>

    </header>

    <main class="auth-main">
      <aside class="auth-hero">
        <div class="hero-content">
          <p class="hero-context">算法学习，不必每次从头开始</p>
          <h1 class="hero-title">{{ hero.title }}</h1>
          <p class="hero-desc">{{ hero.desc }}</p>
        </div>

        <div v-if="variant === 'login'" class="hero-visual">
          <LoginGlobe />
        </div>

        <div class="continuity-note">
          <span class="status-dot" aria-hidden="true" />
          <div>
            <strong>学习记录持续同步</strong>
            <span>{{ hero.note }}</span>
          </div>
        </div>
      </aside>

      <section class="auth-panel" :aria-label="variant === 'login' ? '账号登录' : '注册账号'">
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.auth-shell {
  --auth-ink: #15211e;
  --auth-muted: #5d6b67;
  --auth-primary: #2e6b62;
  --auth-primary-hover: #24584f;
  --auth-tint: #edf4f1;
  --auth-line: #d8e1dd;
  --auth-surface: #ffffff;
  min-height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  isolation: isolate;
  color-scheme: light;
  color: var(--auth-ink);
  background: #fbfcfa;
}

.auth-shell::before {
  content: '';
  position: fixed;
  inset: -42px;
  z-index: 0;
  pointer-events: none;
  background-image: url('@/assets/auth-background.webp');
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  transform: translate3d(-12px, -8px, 0) scale(1.04);
  animation: authBackgroundDrift 28s ease-in-out infinite alternate;
  will-change: transform;
}

@keyframes authBackgroundDrift {
  to {
    transform: translate3d(12px, 8px, 0) scale(1.04);
  }
}

.auth-top {
  position: relative;
  z-index: 1;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 clamp(20px, 3vw, 48px);
  border-bottom: 1px solid var(--auth-line);
  background: rgba(255, 255, 255, 0.88);
  box-sizing: border-box;
}

.brand {
  border: 0;
  font: inherit;
  cursor: pointer;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  padding: 0;
  color: var(--auth-ink);
  background: transparent;
  text-align: left;
}

.auth-main {
  position: relative;
  z-index: 1;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(360px, 0.92fr) minmax(480px, 1.08fr);
  min-height: 0;
}

.auth-hero {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: clamp(18px, 3vh, 32px);
  padding: clamp(64px, 9vh, 104px) clamp(44px, 7vw, 112px) clamp(44px, 7vh, 72px);
  border-right: 1px solid var(--auth-line);
  background: rgba(237, 244, 241, 0.86);
}

.hero-content {
  max-width: 490px;
}

.hero-context {
  margin: 0 0 24px;
  color: var(--auth-primary);
  font-size: 14px;
  font-weight: 650;
}

.hero-title {
  max-width: 10ch;
  margin: 0 0 22px;
  color: var(--auth-ink);
  font-size: clamp(2.25rem, 4.2vw, 4rem);
  font-weight: 720;
  line-height: 1.12;
  letter-spacing: -0.035em;
  text-wrap: balance;
}

.hero-desc {
  max-width: 38ch;
  margin: 0;
  color: var(--auth-muted);
  font-size: 16px;
  line-height: 1.8;
  text-wrap: pretty;
}

.hero-visual {
  min-height: 280px;
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: clamp(-18px, -2vh, -8px) clamp(-28px, -2vw, 0px) clamp(-24px, -2vh, -8px);
  pointer-events: auto;
}

.continuity-note {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  color: var(--auth-ink);
}

.status-dot {
  width: 8px;
  height: 8px;
  margin-top: 7px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--auth-primary);
}

.continuity-note div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.continuity-note strong {
  font-size: 13px;
  font-weight: 650;
}

.continuity-note span:last-child {
  color: var(--auth-muted);
  font-size: 12px;
}

.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(40px, 7vh, 72px) clamp(28px, 7vw, 96px);
  background: rgba(255, 255, 255, 0.82);
}

.brand:focus-visible {
  outline: 2px solid var(--auth-primary);
  outline-offset: 3px;
}

@media (max-width: 880px) {
  .auth-main {
    grid-template-columns: 1fr;
  }

  .auth-hero {
    min-height: auto;
    padding: 42px clamp(24px, 7vw, 64px);
    border-right: 0;
    border-bottom: 1px solid var(--auth-line);
  }

  .hero-title {
    max-width: 14ch;
    margin-bottom: 14px;
    font-size: 2.35rem;
  }

  .hero-context {
    margin-bottom: 14px;
  }

  .continuity-note {
    display: none;
  }

  .hero-visual {
    min-height: 300px;
    margin: 0;
  }

  .auth-panel {
    align-items: flex-start;
    padding-top: 48px;
  }
}

@media (max-width: 560px) {
  .auth-shell::before {
    background-size: 100% 100%;
  }

  .auth-top {
    height: 64px;
    padding: 0 18px;
  }

  .auth-hero {
    padding: 30px 22px 32px;
  }

  .hero-context {
    display: none;
  }

  .hero-title {
    margin-bottom: 10px;
    font-size: 1.85rem;
  }

  .hero-desc {
    font-size: 14px;
    line-height: 1.7;
  }

  .hero-visual {
    display: none;
  }

  .auth-panel {
    padding: 34px 22px 48px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth-shell::before {
    animation: none;
    transform: scale(1.03);
  }
}

</style>
