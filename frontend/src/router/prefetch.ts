/**
 * 路由 chunk 预加载：顶栏 hover / 首页快捷入口可提前拉取，缩短首次进入等待。
 */
const prefetchByPath: Record<string, () => Promise<unknown>> = {
  '/': () => import('@/views/HomeView.vue'),
  '/playground': () => import('@/views/playground/StlPlaygroundView.vue'),
  '/learning-path': () => import('@/views/LearningPathView.vue'),
  '/resources': () => import('@/views/ResourceLibraryView.vue'),
  '/practice': () => import('@/views/practice/PracticeListView.vue'),
  '/my-learning': () => import('@/views/MyLearningView.vue'),
  '/agent-workbench': () => import('@/views/AgentWorkbenchView.vue'),
  '/teacher-dashboard': () => import('@/views/TeacherDashboardView.vue'),
  '/a3-demo': () => import('@/views/A3DemoDashboard.vue'),
  '/help': () => import('@/views/HelpCenterView.vue'),
  '/learn/array': () => import('@/views/learn/ArrayModuleView.vue'),
  '/learn/hash-table': () => import('@/views/learn/HashTableModuleView.vue'),
  '/learn/string': () => import('@/views/learn/StringModuleView.vue'),
  '/learn/two-pointers': () => import('@/views/learn/TwoPointersModuleView.vue'),
  '/learn/linked-list': () => import('@/views/learn/GenericModuleLearnView.vue'),
  '/learn/stack-queue': () => import('@/views/learn/GenericModuleLearnView.vue'),
  '/learn/binary-tree': () => import('@/views/learn/GenericModuleLearnView.vue'),
  '/learn/backtracking': () => import('@/views/learn/GenericModuleLearnView.vue'),
  '/learn/greedy': () => import('@/views/learn/GenericModuleLearnView.vue'),
  '/learn/dp': () => import('@/views/learn/GenericModuleLearnView.vue'),
  '/learn/monotonic-stack': () => import('@/views/learn/GenericModuleLearnView.vue'),
  '/learn/graph': () => import('@/views/learn/GenericModuleLearnView.vue'),
}

const prefetched = new Set<string>()

export function prefetchRoute(path: string) {
  const normalized = path === '' ? '/' : path.replace(/\/+$/, '') || '/'
  if (prefetched.has(normalized)) return
  const loader = prefetchByPath[normalized]
  if (!loader) return
  prefetched.add(normalized)
  void loader()
}

/** 空闲时预加载常用页，不阻塞首屏 */
export function prefetchCommonRoutesIdle() {
  const run = () => {
    prefetchRoute('/learning-path')
    prefetchRoute('/practice')
    prefetchRoute('/learn/array')
  }
  if (typeof requestIdleCallback === 'function') {
    requestIdleCallback(run, { timeout: 2500 })
  } else {
    setTimeout(run, 1200)
  }
}
