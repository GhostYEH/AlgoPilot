<script setup lang="ts">
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import PageTransition from '@/components/layout/PageTransition.vue'
</script>

<template>
  <el-config-provider :locale="zhCn">
    <router-view v-slot="{ Component, route }">
      <PageTransition v-if="Component" :route="route" shell>
        <component :is="Component" />
      </PageTransition>
    </router-view>
  </el-config-provider>
</template>
