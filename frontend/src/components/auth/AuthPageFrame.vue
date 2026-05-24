<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Cpu, DataLine, TrendCharts } from '@element-plus/icons-vue'

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
        kicker: 'Create Account',
        title: '注册账号，进度云端同步',
        desc: '完成注册后，数组、链表等模块的小节完成度将自动保存到服务端，换设备也能接着学。',
      }
    : {
        kicker: 'Welcome Back',
        title: '登录后继续你的算法路径',
        desc: '同步学习进度、衔接多智能体推荐与资源生成能力，在同一账号下延续训练节奏。',
      },
)

const features = [
  { icon: TrendCharts, text: '章节进度本机 + 云端双备份' },
  { icon: DataLine, text: '学习路径与力扣题单串联' },
  { icon: Cpu, text: '暗色终端风，专注刷题与复盘' },
]

function goHome() {
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="auth-shell">
    <div class="auth-bg" aria-hidden="true">
      <span class="auth-orb auth-orb-a" />
      <span class="auth-orb auth-orb-b" />
      <span class="auth-grid" />
    </div>

    <header class="auth-top">
      <button type="button" class="brand" @click="goHome">
        <span class="logo" aria-hidden="true">AL</span>
        <span class="brand-text">
          <span class="brand-title">算法智能学习平台</span>
          <span class="brand-sub">软件杯 · 个性化学习</span>
        </span>
      </button>
      <el-button class="home-btn" type="primary" plain round size="small" @click="goHome">
        返回首页
      </el-button>
    </header>

    <main class="auth-main">
      <aside class="auth-hero">
        <p class="hero-kicker">{{ hero.kicker }}</p>
        <h1 class="hero-title">{{ hero.title }}</h1>
        <p class="hero-desc">{{ hero.desc }}</p>

        <ul class="hero-features">
          <li v-for="(f, i) in features" :key="i">
            <span class="feature-icon">
              <el-icon :size="18"><component :is="f.icon" /></el-icon>
            </span>
            <span>{{ f.text }}</span>
          </li>
        </ul>

        <div class="hero-code" aria-hidden="true">
          <span class="code-line"><span class="code-kw">const</span> session = <span class="code-fn">await</span> auth.login()</span>
          <span class="code-line"><span class="code-fn">syncProgress</span>(session.user)</span>
          <span class="code-line code-dim">// 数组 · 链表 · 哈希 · 字符串</span>
        </div>
      </aside>

      <section class="auth-panel">
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.auth-shell {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: var(--alp-color-text);
  background: var(--alp-bg-page);
}

.auth-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.auth-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.55;
}

.auth-orb-a {
  width: 420px;
  height: 420px;
  top: -120px;
  left: -80px;
  background: rgba(56, 189, 248, 0.22);
}

.auth-orb-b {
  width: 380px;
  height: 380px;
  bottom: -100px;
  right: 10%;
  background: rgba(129, 140, 248, 0.18);
}

.auth-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.06) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 20%, transparent 75%);
}

.auth-top {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px var(--alp-layout-padding-x, 24px);
  border-bottom: 1px solid var(--alp-color-border);
  background: var(--alp-bg-header);
  backdrop-filter: blur(14px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  border: none;
  background: none;
  padding: 0;
  text-align: left;
  color: inherit;
  font: inherit;
}

.brand:focus-visible {
  outline: 2px solid var(--alp-color-primary);
  outline-offset: 4px;
  border-radius: 8px;
}

.logo {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--alp-color-primary), var(--alp-color-accent));
  color: #0f172a;
  font-weight: 800;
  font-size: 14px;
  display: grid;
  place-items: center;
  letter-spacing: 0.5px;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(56, 189, 248, 0.35);
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.brand-title {
  font-weight: 600;
  font-size: 15px;
}

.brand-sub {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.home-btn {
  flex-shrink: 0;
}

.auth-main {
  position: relative;
  z-index: 1;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 480px);
  gap: clamp(24px, 5vw, 64px);
  align-items: center;
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
  padding: clamp(28px, 5vh, 56px) var(--alp-layout-padding-x, 24px) 48px;
  box-sizing: border-box;
}

.auth-hero {
  padding-right: 12px;
}

.hero-kicker {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--alp-color-primary);
}

.hero-title {
  margin: 0 0 14px;
  font-size: clamp(1.75rem, 3.5vw, 2.25rem);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.03em;
  max-width: 14ch;
}

.hero-desc {
  margin: 0 0 28px;
  font-size: 15px;
  color: var(--alp-color-muted);
  line-height: 1.7;
  max-width: 42ch;
}

.hero-features {
  margin: 0 0 32px;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-features li {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--alp-color-text);
}

.feature-icon {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--alp-color-primary-soft);
  border: 1px solid rgba(56, 189, 248, 0.25);
  color: var(--alp-color-primary);
  flex-shrink: 0;
}

.hero-code {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-code-ish);
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
  font-size: 12px;
  line-height: 1.55;
  max-width: 360px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.code-line {
  display: block;
}

.code-kw {
  color: #c084fc;
}

.code-fn {
  color: var(--alp-color-primary);
}

.code-dim {
  color: var(--alp-color-muted);
}

.auth-panel {
  display: flex;
  justify-content: center;
  width: 100%;
}

@media (max-width: 900px) {
  .auth-main {
    grid-template-columns: 1fr;
    gap: 28px;
    align-items: start;
  }

  .auth-hero {
    text-align: center;
    padding-right: 0;
  }

  .hero-title {
    max-width: none;
    margin-left: auto;
    margin-right: auto;
  }

  .hero-desc {
    margin-left: auto;
    margin-right: auto;
  }

  .hero-features {
    align-items: center;
  }

  .hero-code {
    margin: 0 auto;
  }
}

@media (max-width: 480px) {
  .brand-sub {
    display: none;
  }

  .hero-code {
    display: none;
  }
}
</style>
