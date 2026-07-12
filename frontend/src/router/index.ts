import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import { learnRoutes } from '@/router/learnRoutes'
import { gamePlayRoutes } from '@/router/gameRoutes'
import { prefetchCommonRoutesIdle } from '@/router/prefetch'
import {
  needsOnboarding,
  ONBOARDING_ALLOWED_ROUTE_NAMES,
} from '@/composables/usePersonaGate'
import { isLoggedIn, isTeacher } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { title: '登录', public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { title: '注册', public: true },
    },
    ...gamePlayRoutes,
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/HomeView.vue'),
          meta: { title: '首页' },
        },
        ...learnRoutes,
        {
          path: 'learning-path',
          name: 'learning-path',
          component: () => import('@/views/LearningPathView.vue'),
          meta: { title: '学习路径' },
        },
        {
          path: 'onboarding',
          redirect: { name: 'learning-path', query: { onboarding: '1' } },
        },
        {
          path: 'resources',
          name: 'resources',
          component: () => import('@/views/ResourceLibraryView.vue'),
          meta: { title: '资源库' },
        },
        {
          path: 'my-learning',
          name: 'my-learning',
          component: () => import('@/views/MyLearningView.vue'),
          meta: { title: '我的学习' },
        },
        {
          path: 'agent-workbench',
          name: 'agent-workbench',
          component: () => import('@/views/AgentWorkbenchView.vue'),
          meta: { title: '多智能体工作台' },
        },
        {
          path: 'teacher-dashboard',
          name: 'teacher-dashboard',
          component: () => import('@/views/TeacherDashboardView.vue'),
          meta: { title: '教师教学看板' },
        },
        {
          path: 'student-roster',
          name: 'student-roster',
          component: () => import('@/views/StudentRosterView.vue'),
          meta: { title: '学情管理' },
        },
        {
          path: 'oj-analytics',
          name: 'oj-analytics',
          component: () => import('@/views/OjAnalyticsView.vue'),
          meta: { title: 'OJ 学情分析' },
        },
        {
          path: 'teacher-workbench',
          name: 'teacher-workbench',
          component: () => import('@/views/TeacherWorkbenchView.vue'),
          meta: { title: '教学资源工作台' },
        },
        {
          path: 'teacher-guide',
          name: 'teacher-guide',
          component: () => import('@/views/TeacherGuideView.vue'),
          meta: { title: '教师指南' },
        },
        {
          path: 'help',
          name: 'help',
          component: () => import('@/views/HelpCenterView.vue'),
          meta: { title: '帮助中心' },
        },
        {
          path: 'playground',
          name: 'stl-playground',
          component: () => import('@/views/playground/StlPlaygroundView.vue'),
          meta: { title: 'STL 沙盒', public: true, transition: 'page-instant' },
        },
        {
          path: 'practice',
          name: 'practice-list',
          component: () => import('@/views/practice/PracticeListView.vue'),
          meta: { title: '在线 OJ', transition: 'page-instant' },
        },
        {
          path: 'practice/:slug',
          name: 'practice-problem',
          component: () => import('@/views/practice/PracticeProblemView.vue'),
          meta: { title: '做题', transition: 'page-instant' },
        },
        {
          path: 'oj-admin',
          name: 'oj-admin',
          component: () => import('@/views/practice/OjAdminView.vue'),
          meta: { title: 'OJ 题目管理' },
        },
      ],
    },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  if (!isLoggedIn.value) {
    if (to.meta.public) return true
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  // 已登录用户访问登录/注册页时重定向到首页，避免陈旧 URL 导致账号切换异常
  if (to.name === 'login' || to.name === 'register') {
    return { name: isTeacher.value ? 'teacher-dashboard' : 'home' }
  }
  // 教师访问学生专属页面时重定向到教师看板
  if (isTeacher.value) {
    const studentOnlyNames = new Set(['home', 'learning-path', 'my-learning'])
    if (studentOnlyNames.has(typeof to.name === 'string' ? to.name : '')) {
      return { name: 'teacher-dashboard' }
    }
    return true
  }
  // 学生访问教师专属页面时重定向到首页
  const teacherOnlyNames = new Set([
    'teacher-dashboard',
    'oj-admin',
    'student-roster',
    'oj-analytics',
    'teacher-workbench',
    'teacher-guide',
  ])
  if (teacherOnlyNames.has(typeof to.name === 'string' ? to.name : '')) {
    return { name: 'home' }
  }
  const routeName = typeof to.name === 'string' ? to.name : ''
  if (ONBOARDING_ALLOWED_ROUTE_NAMES.has(routeName)) return true
  if (to.name === 'learning-path' && to.query.onboarding === '1') return true
  // 学习与练习页面无需完成画像即可访问（打包后可能未配置 LLM，用户无法完成 onboarding）
  if (routeName.startsWith('learn-') || routeName.startsWith('practice-')) return true
  if (await needsOnboarding()) {
    return {
      name: 'learning-path',
      query: { onboarding: '1', redirect: to.fullPath },
    }
  }
  return true
})

router.afterEach((to) => {
  if (to.name === 'module-game-play') return
  const title = (to.meta.title as string) || ''
  document.title = title ? `${title} · 算法智能学习平台` : '算法智能学习平台'
})

if (typeof window !== 'undefined') {
  prefetchCommonRoutesIdle()
}

// 懒加载 chunk 失败时（部署后旧 hash 失效）自动刷新一次，避免永久白屏
router.onError((error, to) => {
  if (
    error instanceof Error &&
    /Loading chunk|Failed to fetch dynamically imported module|Importing a module script failed/.test(
      error.message,
    )
  ) {
    if (typeof window !== 'undefined') {
      const reloadKey = `alp-chunk-reload-${to.fullPath}`
      if (!sessionStorage.getItem(reloadKey)) {
        sessionStorage.setItem(reloadKey, '1')
        window.location.assign(to.fullPath)
        return
      }
      sessionStorage.removeItem(reloadKey)
    }
  }
  // eslint-disable-next-line no-console
  console.error('[router] navigation error:', error)
})

export default router
