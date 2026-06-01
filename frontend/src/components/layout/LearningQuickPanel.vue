<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, TrendCharts, Clock, StarFilled, Collection } from '@element-plus/icons-vue'
import { buildLearningOverview } from '@/utils/learningOverview'
import { loadFavoriteKeys } from '@/utils/learningBookmarks'
import { isLoggedIn } from '@/stores/auth'

const router = useRouter()

const overview = computed(() => buildLearningOverview())

const recentModules = computed(() => {
  return overview.value.inProgressModules.slice(0, 3)
})

const favoriteCount = computed(() => loadFavoriteKeys().length)

function goMyLearning() {
  router.push({ name: 'my-learning' })
}

function goModule(key: string) {
  router.push({ name: 'my-learning', query: { module: key } })
}
</script>

<template>
  <div class="learning-quick-panel">
    <div class="panel-header">
      <span class="panel-title">学习进度概览</span>
      <el-button type="primary" text size="small" @click="goMyLearning">
        详情 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
      </el-button>
    </div>

    <div class="progress-overview">
      <div class="progress-ring-mini">
        <svg viewBox="0 0 36 36" class="ring-svg">
          <circle
            class="ring-bg"
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke="var(--alp-color-border)"
            stroke-width="3"
          />
          <circle
            class="ring-fg"
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke="var(--alp-color-primary)"
            stroke-width="3"
            stroke-linecap="round"
            :stroke-dasharray="`${overview.overallPercent} 100`"
            transform="rotate(-90 18 18)"
          />
        </svg>
        <span class="ring-pct">{{ overview.overallPercent }}%</span>
      </div>
      <div class="progress-stats">
        <div class="stat-item">
          <el-icon><TrendCharts /></el-icon>
          <span>{{ overview.completedModules }} 模块完成</span>
        </div>
        <div class="stat-item">
          <el-icon><Collection /></el-icon>
          <span>{{ overview.trackedModules }} 模块跟踪</span>
        </div>
        <div class="stat-item">
          <el-icon><Clock /></el-icon>
          <span>{{ overview.rows.reduce((s, r) => s + r.doneCount, 0) }} 小节完成</span>
        </div>
      </div>
    </div>

    <div class="recent-section" v-if="recentModules.length">
      <span class="section-label">
        <el-icon><Clock /></el-icon>
        进行中
      </span>
      <div class="recent-list">
        <div
          v-for="mod in recentModules"
          :key="mod.key"
          class="recent-item"
          role="button"
          tabindex="0"
          @click="goModule(mod.key)"
          @keydown.enter.prevent="goModule(mod.key)"
        >
          <span class="recent-name" :style="{ color: mod.accent }">{{ mod.label }}</span>
          <el-progress
            :percentage="mod.percent"
            :stroke-width="4"
            :show-text="false"
            :color="mod.accent"
            style="width: 60px"
          />
          <span class="recent-pct">{{ mod.percent }}%</span>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <el-button size="small" @click="router.push({ name: 'learning-path' })">
        学习路径
      </el-button>
      <el-button size="small" @click="router.push({ name: 'my-learning', query: { tab: 'favorites' } })">
        <el-icon><StarFilled /></el-icon>
        收藏 {{ favoriteCount }}
      </el-button>
      <el-button size="small" @click="router.push({ name: 'my-learning', query: { tab: 'games' } })">
        小游戏
      </el-button>
    </div>

    <el-alert
      v-if="!isLoggedIn"
      type="info"
      :closable="false"
      show-icon
      class="login-hint"
    >
      登录后可云端同步进度
    </el-alert>
  </div>
</template>

<style scoped>
.learning-quick-panel {
  width: 280px;
  padding: 12px 14px;
  background: var(--alp-bg-surface);
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.progress-overview {
  display: flex;
  gap: 14px;
  padding: 12px;
  border-radius: 10px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  margin-bottom: 12px;
}

.progress-ring-mini {
  position: relative;
  width: 52px;
  height: 52px;
  flex-shrink: 0;
}

.ring-svg {
  width: 100%;
  height: 100%;
}

.ring-pct {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-primary);
}

.progress-stats {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.stat-item .el-icon {
  font-size: 14px;
  color: var(--alp-color-primary);
}

.recent-section {
  margin-bottom: 12px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  margin-bottom: 8px;
}

.section-label .el-icon {
  font-size: 13px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  cursor: pointer;
  transition: background 0.2s;
}

.recent-item:hover,
.recent-item:focus-visible {
  background: var(--alp-color-primary-soft);
  outline: none;
}

.recent-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recent-pct {
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-text);
  font-variant-numeric: tabular-nums;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.quick-actions :deep(.el-button) {
  font-size: 12px;
}

.login-hint {
  margin-top: 8px;
  font-size: 12px;
}
</style>