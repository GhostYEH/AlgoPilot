<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Grid, Reading, FolderOpened, User, QuestionFilled, Cpu, Moon, Sunny, ArrowDown, DataLine, Document, Setting, Tickets, TrendCharts, Box } from '@element-plus/icons-vue'
import { useTheme } from '@/composables/useTheme'
import { providePersonaUi } from '@/composables/usePersonaUiProvider'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { recordModuleVisit } from '@/utils/learningBookmarks'
import { isLoggedIn, isTeacher, getUser, logout } from '@/stores/auth'
import PageTransition from '@/components/layout/PageTransition.vue'
import LearningQuickPanel from '@/components/layout/LearningQuickPanel.vue'
import BrandLogo from '@/components/common/BrandLogo.vue'
import LiquidGlass from '@/components/common/LiquidGlass.vue'
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
  <el-container class="main-shell" :class="{ 'teacher-shell': isTeacher }">
    <aside v-if="isTeacher" class="teacher-sidebar">
      <button class="teacher-brand" type="button" aria-label="返回教师首页" @click="goHome">
        <BrandLogo size="teacher" />
      </button>
      <el-menu :default-active="activeMenu" router class="teacher-menu">
        <el-menu-item index="/teacher-dashboard"><el-icon><DataLine /></el-icon><span>教师看板</span></el-menu-item>
        <el-menu-item index="/student-roster"><el-icon><User /></el-icon><span>班级管理</span></el-menu-item>
        <el-menu-item index="/oj-analytics"><el-icon><TrendCharts /></el-icon><span>学情分析</span></el-menu-item>
        <el-menu-item index="/teacher-workbench"><el-icon><Document /></el-icon><span>资源工作台</span></el-menu-item>
        <el-menu-item index="/oj-admin"><el-icon><Tickets /></el-icon><span>OJ 管理</span></el-menu-item>
        <el-menu-item index="/playground"><el-icon><Box /></el-icon><span>STL 沙盒</span></el-menu-item>
        <el-menu-item index="/teacher-guide"><el-icon><QuestionFilled /></el-icon><span>教师指南</span></el-menu-item>
      </el-menu>
      <div class="teacher-profile"><el-avatar :size="36">{{ displayName }}</el-avatar><div><strong>{{ getUser()?.username || '教师' }}</strong><span>授课教师</span></div><el-icon><Setting /></el-icon></div>
    </aside>
    <el-header height="var(--alp-header-height, 60px)" class="app-header" :class="{ 'teacher-header': isTeacher }">
      <LiquidGlass
        v-if="!isTeacher"
        tag="button"
        class="header-brand header-brand-liquid"
        :displacement-scale="18"
        :blur-amount="14"
        :elasticity="0.12"
        :corner-radius="13"
        padding="5px 9px"
        aria-label="返回 AlgoPilot 首页"
        @click="goHome"
      >
        <BrandLogo size="nav" />
      </LiquidGlass>

      <el-menu
        mode="horizontal"
        class="header-menu"
        :ellipsis="false"
        :default-active="activeMenu"
        router
        background-color="transparent"
      >
        <template v-if="!isTeacher">
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
          <el-menu-item index="/playground" @mouseenter="prefetchRoute('/playground')">
            <el-icon><Box /></el-icon>
            <span>STL 沙盒</span>
          </el-menu-item>
          <li class="header-dropdown-item" role="menuitem">
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
          </li>
        </template>

        <el-menu-item v-if="!isTeacher" index="/help" @mouseenter="prefetchRoute('/help')">
          <el-icon><QuestionFilled /></el-icon>
          <span>帮助中心</span>
        </el-menu-item>
      </el-menu>

      <div v-if="isTeacher" class="teacher-context">
        <el-dropdown trigger="click"><button type="button">数据结构与算法 <el-icon><ArrowDown /></el-icon></button><template #dropdown><el-dropdown-menu><el-dropdown-item>数据结构与算法</el-dropdown-item><el-dropdown-item>算法设计基础</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
      </div>

      <div class="header-actions">
        <span v-if="isTeacher" class="term-range">本学期 · 实时数据</span>
        <el-tooltip :content="isDark ? '切换浅色' : '切换深色'" placement="bottom">
          <LiquidGlass
            tag="button"
            class="theme-btn theme-liquid-button"
            :displacement-scale="16"
            :blur-amount="12"
            :elasticity="0.2"
            :corner-radius="999"
            padding="0"
            :aria-label="isDark ? '切换浅色模式' : '切换深色模式'"
            @click="toggleTheme"
          >
            <el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon>
          </LiquidGlass>
        </el-tooltip>
        <template v-if="!isLoggedIn">
          <el-button type="primary" plain round size="small" @click="goLogin">登录</el-button>
          <el-button round size="small" @click="goRegister">注册</el-button>
        </template>
        <template v-else>
          <span v-if="!isTeacher" class="user-name">{{ getUser()?.username }}</span>
          <el-dropdown trigger="click">
            <LiquidGlass
              tag="button"
              class="avatar-liquid-button"
              :displacement-scale="14"
              :blur-amount="12"
              :elasticity="0.16"
              :corner-radius="999"
              padding="2px"
              aria-label="打开用户菜单"
            >
              <el-avatar :size="32" class="user-avatar">{{ displayName }}</el-avatar>
            </LiquidGlass>
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
  gap: 20px;
  padding: 0 max(18px, var(--alp-layout-padding-x));
  border-bottom: 1px solid var(--alp-color-border);
  background: var(--alp-bg-header);
  position: sticky;
  top: 0;
  z-index: 20;
  min-width: 0;
  box-shadow: none;
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

.header-brand:focus-visible {
  outline: 2px solid var(--alp-color-primary);
  outline-offset: 4px;
  border-radius: 6px;
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
  font-weight: 500;
  font-size: 14px;
  border-bottom-color: transparent !important;
  letter-spacing: 0;
  transition:
    color var(--alp-transition-fast),
    background var(--alp-transition-fast);
}

.header-menu :deep(.el-menu-item:hover) {
  /* Keep the hover cue text-only, matching the simplified navigation treatment. */
  color: var(--alp-color-primary) !important;
  background: var(--alp-bg-nav-hover) !important;
}

.header-menu :deep(.el-menu-item.is-active) {
  color: #0b7477 !important;
  border-bottom-color: transparent !important;
  background: var(--alp-bg-nav-active) !important;
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
  color: var(--alp-color-primary);
  background: var(--alp-bg-nav-active);
}

.nav-dropdown-trigger:hover {
  color: var(--alp-color-primary);
  background: var(--alp-bg-nav-hover);
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
  outline: 2px solid var(--alp-color-primary);
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
  padding: 18px var(--alp-layout-padding-x) 28px;
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

@media (min-width: 1800px) {
  .app-header { gap: 24px; padding-inline: 24px; }
  .header-menu { gap: 9px; }
  .header-menu :deep(.el-menu-item), .nav-dropdown-trigger { height: 44px; padding-inline: 12px; font-size: 15px; }
  .header-menu :deep(.el-menu-item .el-icon), .nav-dropdown-trigger > .el-icon:first-child { font-size: 17px; }
  .header-actions { gap: 12px; }
  .user-name { max-width: 150px; font-size: 14px; }
  .app-main { padding: 22px clamp(24px, 1.8vw, 38px) 34px; }
}

.header-dropdown-item {
  display: flex;
  align-items: center;
  margin: 0;
  padding: 0;
  list-style: none;
}

.teacher-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 30;
  display: flex;
  width: 196px;
  flex-direction: column;
  box-sizing: border-box;
  background: var(--alp-bg-surface-solid);
  color: var(--alp-color-text);
  border-right: 1px solid var(--alp-color-border);
  height: 100dvh;
  overflow: hidden;
  overscroll-behavior: contain;
}

.teacher-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--alp-header-height, 60px);
  padding: 0 22px;
  border: 0;
  background: transparent;
  color: var(--alp-color-text);
  cursor: pointer;
  border-bottom: 1px solid var(--alp-color-border);
}

.teacher-menu { flex: 1; padding: 16px 7px; border: 0; background: transparent; overflow-y: auto; }
.teacher-menu :deep(.el-menu-item) { height: 46px; margin-bottom: 4px; border-radius: 6px; color: var(--alp-color-text-secondary) !important; transition: color var(--alp-transition-fast), background var(--alp-transition-fast); }
.teacher-menu :deep(.el-menu-item:hover) { background: var(--alp-bg-nav-hover); color: var(--alp-color-primary) !important; }
.teacher-menu :deep(.el-menu-item.is-active) { background: var(--alp-bg-nav-active); color: var(--alp-color-primary) !important; font-weight: 600; position: relative; }
.teacher-menu :deep(.el-menu-item.is-active)::before { content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 3px; height: 60%; border-radius: 0 3px 3px 0; background: var(--alp-color-primary); }
.teacher-menu :deep(.el-icon) { font-size: 17px; }
.teacher-profile { display: grid; grid-template-columns: 36px minmax(0,1fr) 18px; align-items: center; gap: 9px; padding: 18px 14px; border-top: 1px solid var(--alp-color-border); }
.teacher-profile div { display: flex; min-width: 0; flex-direction: column; }
.teacher-profile strong { overflow: hidden; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; color: var(--alp-color-text); }
.teacher-profile span { margin-top: 3px; color: var(--alp-color-muted); font-size: 10px; }
.teacher-header { margin-left: 196px; background: var(--alp-bg-header); }
.teacher-header .header-menu { display: none; }
.teacher-context { display: flex; align-items: center; gap: 18px; flex: 1; }
.teacher-context button { display: flex; align-items: center; gap: 7px; padding: 8px 2px; border: 0; background: transparent; color: var(--alp-color-text); font-size: 13px; font-weight: 600; cursor: pointer; }
.context-divider { width: 1px; height: 23px; background: var(--alp-color-border); }
.term-range { color: var(--alp-color-text-secondary); font-size: 12px; }
.teacher-shell {
  height: 100dvh;
  min-height: 0;
  overflow: hidden;
}

.teacher-shell .app-main {
  height: calc(100dvh - var(--alp-header-height, 60px));
  min-height: 0;
  margin-left: 196px;
  width: calc(100% - 196px);
  overflow-x: clip;
  overflow-y: auto;
  overscroll-behavior: contain;
  background: var(--alp-bg-shell);
}

.app-main:has(.practice-problem-page) {
  height: calc(100vh - var(--alp-header-height, 60px));
  padding: 0;
  overflow: hidden;
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
  .teacher-sidebar { width: 68px; }
  .teacher-brand { justify-content: center; padding: 0; }
  .teacher-brand :deep(.brand-logo__text), .teacher-menu :deep(.el-menu-item span), .teacher-profile div, .teacher-profile > .el-icon { display: none; }
  .teacher-menu { padding-inline: 7px; }
  .teacher-menu :deep(.el-menu-item) { justify-content: center; padding: 0; }
  .teacher-menu :deep(.el-icon) { margin: 0; }
  .teacher-profile { display: flex; justify-content: center; padding-inline: 0; }
  .teacher-header { margin-left: 68px; }
  .teacher-shell .app-main { margin-left: 68px; width: calc(100% - 68px); }
  .header-menu :deep(.el-menu-item span) {
    display: none;
  }

  .nav-dropdown-trigger span {
    display: none;
  }
}

@media (max-width: 600px) {
  .teacher-sidebar { display: none; }
  .teacher-header { margin-left: 0; }
  .teacher-shell .app-main { margin-left: 0; width: 100%; }
  .teacher-context { gap: 8px; }
  .teacher-context button { max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .term-range { display: none; }
  .app-header {
    gap: 8px;
    padding: 0 12px;
  }

  .header-brand :deep(.brand-logo__title) {
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
  .header-brand :deep(.brand-logo__title) {
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
