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
          path: 'a3-demo',
          name: 'a3-demo',
          component: () => import('@/views/A3DemoDashboard.vue'),
          meta: { title: '比赛演示', public: true },
        },
        {
          path: 'teacher-dashboard',
          name: 'teacher-dashboard',
          component: () => import('@/views/TeacherDashboardView.vue'),
          meta: { title: '教师看板', requiresTeacher: true },
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
  if (to.meta.requiresTeacher && !isTeacher.value) {
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

export default router
