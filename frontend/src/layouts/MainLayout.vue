<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Grid, Reading, FolderOpened, User, QuestionFilled, Cpu, Moon, Sunny, ArrowDown, DataLine, MagicStick } from '@element-plus/icons-vue'
import { useTheme } from '@/composables/useTheme'
import { providePersonaUi } from '@/composables/usePersonaUiProvider'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { recordModuleVisit } from '@/utils/learningBookmarks'
import { isLoggedIn, isTeacher, getUser, logout } from '@/stores/auth'
import PageTransition from '@/components/layout/PageTransition.vue'
import LearningQuickPanel from '@/components/layout/LearningQuickPanel.vue'
import { prefetchRoute } from '@/router/prefetch'

const route = useRoute()
const router = useRouter()
const { isDark, toggleTheme } = useTheme()
providePersonaUi()

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

const activeMenu = computed(() => {
  const p = route.path
  if (p === '/' || p === '') return '/'
  return p
})

function goHome() {
  router.push({ name: isTeacher.value ? 'teacher-dashboard' : 'home' })
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
  router.push({ name: 'login' })
}

const isMyLearningActive = computed(() => route.path.startsWith('/my-learning'))
</script>

<template>
  <el-container class="main-shell">
    <el-header height="var(--alp-header-height, 60px)" class="app-header">
      <div class="header-brand" @click="goHome">
        <div class="logo-mark" aria-hidden="true">AP</div>
        <div class="brand-text">
          <span class="brand-title">AlgoPilot</span>
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
        <template v-if="isTeacher">
          <el-menu-item index="/teacher-dashboard" @mouseenter="prefetchRoute('/teacher-dashboard')">
            <el-icon><DataLine /></el-icon>
            <span>教学看板</span>
          </el-menu-item>
          <el-menu-item index="/student-roster" @mouseenter="prefetchRoute('/student-roster')">
            <el-icon><User /></el-icon>
            <span>学情管理</span>
          </el-menu-item>
          <el-menu-item index="/oj-analytics" @mouseenter="prefetchRoute('/oj-analytics')">
            <el-icon><Cpu /></el-icon>
            <span>OJ 学情</span>
          </el-menu-item>
          <el-menu-item index="/oj-admin" @mouseenter="prefetchRoute('/oj-admin')">
            <el-icon><Cpu /></el-icon>
            <span>OJ 管理</span>
          </el-menu-item>
          <el-menu-item index="/teacher-workbench" @mouseenter="prefetchRoute('/teacher-workbench')">
            <el-icon><MagicStick /></el-icon>
            <span>资源工作台</span>
          </el-menu-item>
        </template>
        <template v-else>
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
            index="/agent-workbench"
            @mouseenter="prefetchRoute('/agent-workbench')"
          >
            <el-icon><Cpu /></el-icon>
            <span>多智能体</span>
          </el-menu-item>

          <el-dropdown
            trigger="hover"
            placement="bottom-start"
            :popper-class="isMyLearningActive ? 'nav-dropdown nav-dropdown--active' : 'nav-dropdown'"
            @mouseenter="prefetchRoute('/my-learning')"
          >
            <div
              class="nav-dropdown-trigger"
              :class="{ 'is-active': isMyLearningActive }"
              role="button"
              tabindex="0"
            >
              <el-icon><User /></el-icon>
              <span>我的学习</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <LearningQuickPanel />
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>

        <el-menu-item v-if="isTeacher" index="/teacher-guide" @mouseenter="prefetchRoute('/teacher-guide')">
          <el-icon><QuestionFilled /></el-icon>
          <span>教师指南</span>
        </el-menu-item>
        <el-menu-item v-else index="/help" @mouseenter="prefetchRoute('/help')">
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
                <el-dropdown-item v-if="isTeacher" @click="router.push({ name: 'teacher-dashboard' })">教学看板</el-dropdown-item>
                <el-dropdown-item v-else @click="router.push({ name: 'my-learning' })">我的学习</el-dropdown-item>
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
  gap: 24px;
  padding: 0 max(18px, var(--alp-layout-padding-x));
  border-bottom: 1px solid var(--alp-color-border);
  background: var(--alp-bg-header);
  backdrop-filter: blur(16px) saturate(1.02);
  position: sticky;
  top: 0;
  z-index: 20;
  min-width: 0;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.03);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity var(--alp-transition-fast);
}

.header-brand:hover {
  opacity: 0.85;
}

.logo-mark {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 6px;
  border: 0;
  background: #1687f8;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  display: grid;
  place-items: center;
  letter-spacing: 0;
  box-shadow: none;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.brand-title {
  font-weight: 600;
  font-size: 17px;
  color: #1687f8;
  letter-spacing: 0;
}

.brand-sub {
  font-size: 11px;
  color: var(--alp-color-muted);
  letter-spacing: 0;
}

.header-menu {
  flex: 1;
  min-width: 0;
  border-bottom: none !important;
  height: var(--alp-header-height, 60px) !important;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  display: flex;
  align-items: center;
  gap: 7px;
}

.header-menu::-webkit-scrollbar {
  display: none;
}

.header-menu :deep(.el-menu-item) {
  height: 40px;
  margin: 0;
  padding: 0 9px;
  border-radius: 6px;
  color: var(--alp-color-text-secondary) !important;
  font-weight: 600;
  font-size: 14px;
  border-bottom-color: transparent !important;
  letter-spacing: 0;
  transition:
    color var(--alp-transition-fast),
    background var(--alp-transition-fast);
}

.header-menu :deep(.el-menu-item:hover) {
  /* Keep the hover cue text-only, matching the simplified navigation treatment. */
  color: #409eff !important;
  background: transparent !important;
}

.header-menu :deep(.el-menu-item.is-active) {
  color: #409eff !important;
  border-bottom-color: transparent !important;
  background: transparent !important;
}

.nav-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 40px;
  margin: 0;
  padding: 0 9px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  color: var(--alp-color-text-secondary);
  cursor: pointer;
  transition: color var(--alp-transition-fast), background var(--alp-transition-fast);
}

.nav-dropdown-trigger.is-active {
  color: #409eff;
  background: transparent;
}

.nav-dropdown-trigger:hover {
  color: #409eff;
  background: transparent;
}

.arrow-icon {
  font-size: 10px;
  transition: transform 0.2s;
}

.nav-dropdown-trigger:hover .arrow-icon,
.nav-dropdown-trigger:focus-visible .arrow-icon {
  transform: rotate(180deg);
}

.header-menu :deep(.el-menu-item:focus-visible),
.nav-dropdown-trigger:focus-visible {
  outline: 2px solid #409eff;
  outline-offset: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  min-width: 0;
}

.header-actions :deep(.theme-btn) {
  transition: transform var(--alp-transition-fast), box-shadow var(--alp-transition-fast);
}

.header-actions :deep(.theme-btn:hover) {
  transform: translateY(-1px);
  box-shadow: var(--alp-shadow-glow);
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
  background: var(--alp-bg-code-ish);
  border: 1px solid rgba(var(--alp-color-primary-rgb), 0.36);
  color: var(--alp-color-text);
  font-size: 13px;
  box-shadow: none;
  transition: transform var(--alp-transition-fast), box-shadow var(--alp-transition-fast);
}

.user-avatar:hover {
  transform: translateY(-1px);
  box-shadow: var(--alp-shadow-glow);
}

.app-main {
  flex: 1;
  width: 100%;
  padding: 22px var(--alp-layout-padding-x) 34px;
  box-sizing: border-box;
  position: relative;
  overflow-x: clip;
  scroll-behavior: smooth;
}

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

  .nav-dropdown-trigger span {
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
    padding: 0 9px;
  }

  .nav-dropdown-trigger {
    padding: 0 9px;
  }

  .header-actions {
    gap: 6px;
  }

  .header-actions :deep(.el-button) {
    padding-left: 9px;
    padding-right: 9px;
  }
}

@media (max-width: 420px) {
  .brand-title {
    display: none;
  }
}
</style>

<style>
.nav-dropdown {
  padding: 8px 0;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.nav-dropdown .el-dropdown-menu__item {
  padding: 0;
  line-height: normal;
}

.nav-dropdown--active {
  /* active state marker */
}
</style>
