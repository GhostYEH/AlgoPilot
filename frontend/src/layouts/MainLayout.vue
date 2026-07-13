<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Grid, Reading, FolderOpened, User, QuestionFilled, Cpu, Moon, Sunny, ArrowDown, DataLine, Bell, Document, Setting, Tickets, TrendCharts } from '@element-plus/icons-vue'
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
  <el-container class="main-shell" :class="{ 'teacher-shell': isTeacher }">
    <aside v-if="isTeacher" class="teacher-sidebar">
      <button class="teacher-brand" type="button" @click="goHome"><span>AP</span><strong>AlgoPilot</strong></button>
      <el-menu :default-active="activeMenu" router class="teacher-menu">
        <el-menu-item index="/teacher-dashboard"><el-icon><DataLine /></el-icon><span>教师看板</span></el-menu-item>
        <el-menu-item index="/student-roster"><el-icon><User /></el-icon><span>班级管理</span></el-menu-item>
        <el-menu-item index="/oj-analytics"><el-icon><TrendCharts /></el-icon><span>学情分析</span></el-menu-item>
        <el-menu-item index="/teacher-workbench"><el-icon><Document /></el-icon><span>资源工作台</span></el-menu-item>
        <el-menu-item index="/oj-admin"><el-icon><Tickets /></el-icon><span>OJ 管理</span></el-menu-item>
        <el-menu-item index="/teacher-guide"><el-icon><QuestionFilled /></el-icon><span>教师指南</span></el-menu-item>
      </el-menu>
      <div class="teacher-profile"><el-avatar :size="36">{{ displayName }}</el-avatar><div><strong>{{ getUser()?.username || '教师' }}</strong><span>授课教师</span></div><el-icon><Setting /></el-icon></div>
    </aside>
    <el-header height="var(--alp-header-height, 60px)" class="app-header" :class="{ 'teacher-header': isTeacher }">
      <div v-if="!isTeacher" class="header-brand" @click="goHome">
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

        <el-menu-item v-if="!isTeacher" index="/help" @mouseenter="prefetchRoute('/help')">
          <el-icon><QuestionFilled /></el-icon>
          <span>帮助中心</span>
        </el-menu-item>
      </el-menu>

      <div v-if="isTeacher" class="teacher-context">
        <el-dropdown trigger="click"><button type="button">高二（3）班 <el-icon><ArrowDown /></el-icon></button><template #dropdown><el-dropdown-menu><el-dropdown-item>高二（3）班</el-dropdown-item><el-dropdown-item>高二（5）班</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
        <span class="context-divider" />
        <el-dropdown trigger="click"><button type="button">数据结构与算法 <el-icon><ArrowDown /></el-icon></button><template #dropdown><el-dropdown-menu><el-dropdown-item>数据结构与算法</el-dropdown-item><el-dropdown-item>算法设计基础</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
      </div>

      <div class="header-actions">
        <span v-if="isTeacher" class="term-range">本学期 · 实时数据</span>
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
          <span v-if="!isTeacher" class="user-name">{{ getUser()?.username }}</span>
          <el-badge v-if="isTeacher" :value="3"><el-button circle size="small" aria-label="消息通知"><el-icon><Bell /></el-icon></el-button></el-badge>
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
  gap: 20px;
  padding: 0 max(18px, var(--alp-layout-padding-x));
  border-bottom: 1px solid var(--alp-color-border);
  background: var(--alp-bg-header);
  backdrop-filter: blur(12px);
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

.logo-mark {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 5px;
  border: 0;
  background: var(--alp-color-primary);
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
  color: var(--alp-color-text);
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
  color: var(--alp-color-primary) !important;
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

.teacher-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 30;
  display: flex;
  width: 196px;
  flex-direction: column;
  box-sizing: border-box;
  background: #06264a;
  color: #fff;
}

.teacher-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--alp-header-height, 60px);
  padding: 0 22px;
  border: 0;
  background: #fff;
  color: #102442;
  cursor: pointer;
}

.teacher-brand span {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 7px;
  background: #1677ff;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.teacher-brand strong { font-size: 17px; }
.teacher-menu { flex: 1; padding: 16px 7px; border: 0; background: transparent; }
.teacher-menu :deep(.el-menu-item) { height: 46px; margin-bottom: 5px; border-radius: 5px; color: #d7e5f5; }
.teacher-menu :deep(.el-menu-item:hover) { background: #0b396a; color: #fff; }
.teacher-menu :deep(.el-menu-item.is-active) { background: #1268da; color: #fff; }
.teacher-menu :deep(.el-icon) { font-size: 17px; }
.teacher-profile { display: grid; grid-template-columns: 36px minmax(0,1fr) 18px; align-items: center; gap: 9px; padding: 18px 14px; border-top: 1px solid rgba(255,255,255,.12); }
.teacher-profile div { display: flex; min-width: 0; flex-direction: column; }
.teacher-profile strong { overflow: hidden; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.teacher-profile span { margin-top: 3px; color: #9fb5cd; font-size: 10px; }
.teacher-header { margin-left: 196px; background: var(--alp-bg-surface); }
.teacher-header .header-menu { display: none; }
.teacher-context { display: flex; align-items: center; gap: 18px; flex: 1; }
.teacher-context button { display: flex; align-items: center; gap: 7px; padding: 8px 2px; border: 0; background: transparent; color: var(--alp-color-text); font-size: 13px; font-weight: 600; cursor: pointer; }
.context-divider { width: 1px; height: 23px; background: var(--alp-color-border); }
.term-range { color: var(--alp-color-text-secondary); font-size: 12px; }
.teacher-shell .app-main { margin-left: 196px; width: calc(100% - 196px); background: var(--alp-bg-shell); }

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
  .teacher-brand strong, .teacher-menu :deep(.el-menu-item span), .teacher-profile div, .teacher-profile > .el-icon { display: none; }
  .teacher-menu { padding-inline: 7px; }
  .teacher-menu :deep(.el-menu-item) { justify-content: center; padding: 0; }
  .teacher-menu :deep(.el-icon) { margin: 0; }
  .teacher-profile { display: flex; justify-content: center; padding-inline: 0; }
  .teacher-header { margin-left: 68px; }
  .teacher-shell .app-main { margin-left: 68px; width: calc(100% - 68px); }
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
