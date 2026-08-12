<script setup lang="ts">
import { computed } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'

const props = withDefaults(
  defineProps<{
    route: RouteLocationNormalizedLoaded
    /**
     * 顶层路由壳（App.vue）：仅在「登录/注册 ↔ 主布局」之间过渡，
     * 避免子路由切换时重复播放整页动画。
     */
    shell?: boolean
  }>(),
  { shell: false },
)

/** 路由 meta.transition 可覆盖；公开认证页默认 page-auth */
const transitionName = computed(() => {
  if (props.shell) return 'page-fade-slide'

  const custom = props.route.meta.transition
  if (typeof custom === 'string' && custom.length > 0) return custom
  if (props.route.meta.public) return 'page-auth'
  if (props.route.path.startsWith('/learn/')) return 'page-learn'
  if (props.route.path.startsWith('/practice')) return 'page-instant'
  return 'page-fade-slide'
})

const routeKey = computed(() =>
  props.shell
    ? (props.route.matched[0]?.path ?? props.route.path)
    : props.route.path,
)
</script>

<template>
  <Transition
    :name="transitionName"
    :mode="transitionName === 'page-instant' ? 'default' : 'out-in'"
    appear
  >
    <div :key="routeKey" class="page-transition-root">
      <slot />
    </div>
  </Transition>
</template>

<style scoped>
.page-transition-root {
  width: 100%;
  min-height: 0;
}
</style>
