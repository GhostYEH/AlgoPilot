import type { RouteRecordRaw } from 'vue-router'

/** 小游戏独立全屏页（不在学习页弹窗内） */
export const gamePlayRoutes: RouteRecordRaw[] = [
  {
    path: '/play/:gameId',
    name: 'module-game-play',
    component: () => import('@/views/games/ModuleGamePlayView.vue'),
    props: true,
    meta: { title: '互动闯关', fullscreenGame: true },
  },
]
