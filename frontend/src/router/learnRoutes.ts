import type { RouteRecordRaw } from 'vue-router'
import { MODULE_LEARN_CONFIGS } from '@/modules/shared/moduleRegistry'

/** 由 moduleRegistry 驱动的通用学习页路由 */
export const registryLearnRoutes: RouteRecordRaw[] = Object.values(MODULE_LEARN_CONFIGS).map(
  (cfg) => ({
    path: `learn/${cfg.key}`,
    name: cfg.routeName,
    component: () => import('@/views/learn/GenericModuleLearnView.vue'),
    props: { moduleKey: cfg.key },
    meta: { title: cfg.breadcrumb },
  }),
)

/** 具独立 UI 或交互的学习页（暂未纳入 registry） */
export const specializedLearnRoutes: RouteRecordRaw[] = [
  {
    path: 'learn/array',
    name: 'learn-array',
    component: () => import('@/views/learn/ArrayModuleView.vue'),
    meta: { title: '数组学习' },
  },
  {
    path: 'learn/hash-table',
    name: 'learn-hash-table',
    component: () => import('@/views/learn/HashTableModuleView.vue'),
    meta: { title: '哈希表学习' },
  },
  {
    path: 'learn/string',
    name: 'learn-string',
    component: () => import('@/views/learn/StringModuleView.vue'),
    meta: { title: '字符串学习' },
  },
  {
    path: 'learn/two-pointers',
    name: 'learn-two-pointers',
    component: () => import('@/views/learn/TwoPointersModuleView.vue'),
    meta: { title: '双指针学习' },
  },
]

export const learnRoutes: RouteRecordRaw[] = [
  ...specializedLearnRoutes,
  ...registryLearnRoutes,
]
