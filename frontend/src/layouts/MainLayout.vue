<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Grid, Reading, FolderOpened, User, QuestionFilled, Cpu, Moon, Sunny } from '@element-plus/icons-vue'
import { useTheme } from '@/composables/useTheme'
import { providePersonaUi } from '@/composables/usePersonaUiProvider'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { recordModuleVisit } from '@/utils/learningBookmarks'
import { isLoggedIn, getUser, logout } from '@/stores/auth'
import PageTransition from '@/components/layout/PageTransition.vue'
import { prefetchRoute } from '@/router/prefetch'

const route = useRoute()
const router = useRouter()
const { isDark, toggleTheme } = useTheme()
const { settings: personaUi } = providePersonaUi()
const showAdvancedNav = computed(() => personaUi.value.graphDetail !== 'minimal')

const ROUTE_TO_MODULE: Record<string, string> = Object.fromEntries(
  Object.entries(MODULE_ROUTE_NAMES).map(([key, name]) => [name as string, key]),
)

watch(
  () => route.name,
  (name) => {
    if (typeof name !== 'string') return
    const moduleKey = ROUTE_TO_MODULE[name]
    if (!moduleKey) return
    const mod = ALGORITHM_MODULES.find((m) => m.key === moduleKey)
    if (mod) recordModuleVisit(moduleKey, mod.label)
  },
  { immediate: true },
)

/** 顶部菜单与路由 path 对齐（子路由相对父级 /） */
const activeMenu = computed(() => {
  const p = route.path
  if (p === '/' || p === '') return '/'
  return p
})

function goHome() {
  router.push({ name: 'home' })
}

const displayName = computed(() => {
  const u = getUser()
  return u?.username?.slice(0, 1).toUpperCase() || '学'
})

function goLogin() {
  router.push({ name: 'login', query: { redirect: route.fullPath } })
}

function goRegister() {
  router.push({ name: 'register' })
}

function onLogout() {
  logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <el-container class="main-shell">
    <el-header height="var(--alp-header-height, 60px)" class="app-header">
      <div class="header-brand" @click="goHome">
        <div class="logo-mark" aria-hidden="true">AP</div>
        <div class="brand-text">
          <span class="brand-title">AlgoPilot</span>
          <span class="brand-sub">讯飞星火 Spark · iFlytek TTS</span>
        </div>
      </div>

      <el-menu
        mode="horizontal"
        class="header-menu"
        :ellipsis="false"
        :default-active="activeMenu"
        router
        background-color="transparent"
      >
        <el-menu-item index="/" @mouseenter="prefetchRoute('/')">
          <el-icon><Grid /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/learning-path" @mouseenter="prefetchRoute('/learning-path')">
          <el-icon><Reading /></el-icon>
          <span>学习路径</span>
        </el-menu-item>
        <el-menu-item index="/resources" @mouseenter="prefetchRoute('/resources')">
          <el-icon><FolderOpened /></el-icon>
          <span>资源库</span>
        </el-menu-item>
        <el-menu-item index="/practice" @mouseenter="prefetchRoute('/practice')">
          <el-icon><Cpu /></el-icon>
          <span>在线 OJ</span>
        </el-menu-item>
        <el-menu-item
          v-if="showAdvancedNav"
          index="/agent-workbench"
          @mouseenter="prefetchRoute('/agent-workbench')"
        >
          <span>多智能体</span>
        </el-menu-item>
        <el-menu-item index="/my-learning" @mouseenter="prefetchRoute('/my-learning')">
          <el-icon><User /></el-icon>
          <span>我的学习</span>
        </el-menu-item>
        <el-menu-item index="/help" @mouseenter="prefetchRoute('/help')">
          <el-icon><QuestionFilled /></el-icon>
          <span>帮助中心</span>
        </el-menu-item>
      </el-menu>

      <div class="header-actions">
        <el-tooltip :content="isDark ? '切换浅色' : '切换深色'" placement="bottom">
          <el-button circle size="small" class="theme-btn" @click="toggleTheme">
            <el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon>
          </el-button>
        </el-tooltip>
        <template v-if="!isLoggedIn">
          <el-button type="primary" plain round size="small" @click="goLogin">登录</el-button>
          <el-button round size="small" @click="goRegister">注册</el-button>
        </template>
        <template v-else>
          <span class="user-name">{{ getUser()?.username }}</span>
          <el-dropdown trigger="click">
            <el-avatar :size="32" class="user-avatar">{{ displayName }}</el-avatar>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push({ name: 'my-learning' })">我的学习</el-dropdown-item>
                <el-dropdown-item divided @click="onLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </div>
    </el-header>

    <el-main class="app-main">
      <router-view v-slot="{ Component, route: childRoute }">
        <PageTransition v-if="Component" :route="childRoute">
          <component :is="Component" />
        </PageTransition>
      </router-view>
    </el-main>
  </el-container>
</template>

<style scoped>
.main-shell {
  min-height: 100vh;
  flex-direction: column;
  background: var(--alp-bg-shell);
}

.app-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 var(--alp-layout-padding-x);
  border-bottom: 1px solid var(--alp-color-border);
  background: var(--alp-bg-header);
  backdrop-filter: blur(14px);
  position: sticky;
  top: 0;
  z-index: 20;
  min-width: 0;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
}

.logo-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--alp-color-primary), var(--alp-color-accent));
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  display: grid;
  place-items: center;
  letter-spacing: 0.5px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.brand-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--alp-color-text);
}

.brand-sub {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.header-menu {
  flex: 1;
  min-width: 0;
  border-bottom: none !important;
  height: var(--alp-header-height, 60px) !important;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
}

.header-menu::-webkit-scrollbar {
  display: none;
}

.header-menu :deep(.el-menu-item) {
  font-weight: 500;
  border-bottom-color: transparent !important;
}

.header-menu :deep(.el-menu-item.is-active) {
  color: var(--alp-color-primary) !important;
  border-bottom-color: var(--alp-color-primary) !important;
  background: transparent !important;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  min-width: 0;
}

.user-name {
  font-size: 13px;
  color: var(--alp-color-text, #334155);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-avatar {
  background: var(--alp-color-primary-soft);
  color: var(--alp-color-primary);
  font-size: 13px;
}

.app-main {
  flex: 1;
  width: 100%;
  padding: var(--alp-layout-padding-y) var(--alp-layout-padding-x) 32px;
  box-sizing: border-box;
  position: relative;
  overflow-x: clip;
}

/* OJ / 学习页刷题：两侧提示负边距外延，允许横向滚动而非裁切 */
.app-main:has(.practice-problem-page),
.app-main:has(.oj-practice-shell--outside) {
  overflow-x: auto;
}

/* 首页：禁止外层滚动，仅右侧内容区滚动 */
.app-main:has(.home-layout) {
  overflow: hidden;
  height: calc(100vh - var(--alp-header-height, 60px));
  max-height: calc(100vh - var(--alp-header-height, 60px));
  display: flex;
  flex-direction: column;
}

.app-main:has(.home-layout) :deep(.page-transition-root) {
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.app-main:has(.home-layout) :deep(.page-transition-root > *) {
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

@media (max-width: 960px) {
  .brand-sub {
    display: none;
  }

  .header-menu :deep(.el-menu-item span) {
    display: none;
  }
}

@media (max-width: 600px) {
  .app-header {
    gap: 8px;
    padding: 0 12px;
  }

  .logo-mark {
    width: 34px;
    height: 34px;
    border-radius: 9px;
  }

  .brand-title {
    max-width: 72px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .header-menu {
    flex: 1 1 72px;
  }

  .header-menu :deep(.el-menu-item) {
    padding: 0 10px;
  }

  .header-actions {
    gap: 6px;
  }

  .header-actions :deep(.el-button) {
    padding-left: 9px;
    padding-right: 9px;
  }
}
</style>
