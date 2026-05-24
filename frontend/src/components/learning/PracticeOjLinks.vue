<script setup lang="ts">
import { Cpu, Link } from '@element-plus/icons-vue'
import type { PracticeLink } from '@/modules/shared/learningTypes'
import { leetcodeCnUrl } from '@/modules/shared/learningTypes'
import { practicePath } from '@/api/oj'

defineProps<{
  main?: PracticeLink
  related?: PracticeLink[]
}>()
</script>

<template>
  <div v-if="main" class="practice-main">
    <div class="practice-actions">
      <router-link :to="practicePath(main.slug)" class="oj-link">
        <el-button type="primary" size="small">
          <el-icon><Cpu /></el-icon>
          站内 OJ 练习
        </el-button>
      </router-link>
      <el-link
        type="info"
        :href="leetcodeCnUrl(main.slug)"
        target="_blank"
        rel="noopener"
        class="lc-link"
      >
        <el-icon><Link /></el-icon>
        <template v-if="main.id > 0">力扣 {{ main.id }} · </template>{{ main.title }}
      </el-link>
    </div>
  </div>

  <div v-if="related?.length" class="related">
    <template v-for="r in related" :key="r.slug + r.id">
      <router-link :to="practicePath(r.slug)" class="related-oj">{{ r.title }} · OJ</router-link>
      <el-link
        type="primary"
        :href="leetcodeCnUrl(r.slug)"
        target="_blank"
        rel="noopener"
        class="related-link"
      >
        {{ r.id > 0 ? `${r.id}. ` : '' }}{{ r.title }}（力扣）
      </el-link>
    </template>
  </div>
</template>

<style scoped>
.practice-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.oj-link {
  text-decoration: none;
}
.lc-link {
  font-size: 14px;
}
.related {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.related-oj {
  font-size: 13px;
  color: var(--el-color-primary);
  text-decoration: none;
}
.related-oj:hover {
  text-decoration: underline;
}
.related-link {
  font-size: 13px;
}
</style>
