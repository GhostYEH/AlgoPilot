<script setup lang="ts">
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import CustomCursor from '@/components/common/CustomCursor.vue'
import PageTransition from '@/components/layout/PageTransition.vue'
</script>

<template>
  <el-config-provider :locale="zhCn">
    <CustomCursor />
    <router-view v-slot="{ Component, route }">
      <PageTransition v-if="Component" :route="route" shell>
        <component :is="Component" />
      </PageTransition>
      <div v-else class="app-loading-fallback">
        <p>页面加载中…</p>
      </div>
    </router-view>
  </el-config-provider>
</template>

<style scoped>
.app-loading-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  color: var(--el-text-color-secondary, #909399);
}
</style>
