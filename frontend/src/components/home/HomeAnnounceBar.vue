<script setup lang="ts">
import { Bell } from '@element-plus/icons-vue'
import { HOME_ANNOUNCEMENTS } from '@/utils/homeDashboard'

const typeMap = {
  info: 'info',
  warning: 'warning',
  success: 'success',
} as const
</script>

<template>
  <div class="announce-bar" role="region" aria-label="平台公告">
    <el-icon class="announce-icon" :size="16"><Bell /></el-icon>
    <div class="announce-track">
      <div class="announce-inner">
        <span v-for="item in HOME_ANNOUNCEMENTS" :key="item.id" class="announce-item">
          <el-tag :type="typeMap[item.type]" size="small" effect="dark" round>公告</el-tag>
          {{ item.text }}
        </span>
        <span
          v-for="item in HOME_ANNOUNCEMENTS"
          :key="`${item.id}-dup`"
          class="announce-item"
          aria-hidden="true"
        >
          <el-tag :type="typeMap[item.type]" size="small" effect="dark" round>公告</el-tag>
          {{ item.text }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.announce-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: rgba(15, 23, 42, 0.45);
  overflow: hidden;
}

.announce-icon {
  color: var(--alp-color-primary);
  flex-shrink: 0;
}

.announce-track {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent);
}

.announce-inner {
  display: flex;
  gap: 48px;
  width: max-content;
  animation: announce-scroll 42s linear infinite;
}

.announce-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--alp-color-muted);
  white-space: nowrap;
}

@keyframes announce-scroll {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}
</style>
