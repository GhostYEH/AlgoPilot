<script setup lang="ts">
import { Clock, Collection, RefreshRight, Star } from '@element-plus/icons-vue'
import type { RecentVisit } from '@/utils/learningBookmarks'
import type { ReviewItem, TrainingProblem } from '@/utils/homeDashboard'

defineProps<{
  daily: TrainingProblem | null
  targeted: TrainingProblem[]
  review: ReviewItem[]
  recent: RecentVisit[]
}>()

const emit = defineEmits<{
  openProblem: [slug: string]
  openModule: [key: string]
}>()

function diffType(d: string) {
  const x = d.toLowerCase()
  if (x === 'easy') return 'success'
  if (x === 'hard') return 'danger'
  return 'warning'
}
</script>

<template>
  <div class="training-grid">
    <div class="training-card daily-card">
      <div class="tc-head">
        <el-icon><Star /></el-icon>
        <span>每日一题</span>
        <el-tag size="small" effect="dark" round>打卡</el-tag>
      </div>
      <template v-if="daily">
        <h3 class="tc-title">{{ daily.title }}</h3>
        <div class="tc-meta">
          <el-tag :type="diffType(daily.difficulty)" size="small" effect="plain">
            {{ daily.difficulty }}
          </el-tag>
          <span><el-icon><Clock /></el-icon> 约 {{ daily.etaMin }} 分钟</span>
        </div>
        <p class="tc-reason">{{ daily.reason }}</p>
        <el-button type="primary" size="small" @click="emit('openProblem', daily.slug)">
          开始今日题目
        </el-button>
      </template>
      <p v-else class="tc-empty">OJ 题目加载中或暂无可用题目</p>
    </div>

    <div class="training-card">
      <div class="tc-head">
        <el-icon><Collection /></el-icon>
        <span>今日靶向训练</span>
      </div>
      <ul v-if="targeted.length" class="target-list">
        <li v-for="p in targeted" :key="p.slug" class="target-item">
          <button type="button" class="target-btn" @click="emit('openProblem', p.slug)">
            <span class="target-title">{{ p.title }}</span>
            <span class="target-meta">
              <el-tag :type="diffType(p.difficulty)" size="small" effect="plain">
                {{ p.difficulty }}
              </el-tag>
              <span>约 {{ p.etaMin }} 分钟</span>
            </span>
            <span class="target-reason">{{ p.reason }}</span>
          </button>
        </li>
      </ul>
      <p v-else class="tc-empty">完成章节学习后，将按薄弱项推荐题目</p>
    </div>

    <div class="training-card">
      <div class="tc-head">
        <el-icon><RefreshRight /></el-icon>
        <span>待复习</span>
      </div>
      <ul v-if="review.length" class="review-list">
        <li v-for="r in review" :key="r.moduleKey" class="review-item">
          <button type="button" class="review-btn" @click="emit('openModule', r.moduleKey)">
            <span class="review-mod">{{ r.moduleLabel }}</span>
            <span class="review-sec">{{ r.sectionLabel }}</span>
            <el-tag size="small" type="warning" effect="plain">{{ r.dueLabel }}</el-tag>
          </button>
        </li>
      </ul>
      <p v-else class="tc-empty">暂无进行中模块，开始任意章节后将提示复习</p>
    </div>

    <div class="training-card recent-card">
      <div class="tc-head">
        <span>最近访问</span>
      </div>
      <ul v-if="recent.length" class="recent-list">
        <li v-for="v in recent" :key="v.moduleKey">
          <button type="button" class="recent-btn" @click="emit('openModule', v.moduleKey)">
            {{ v.label }}
          </button>
        </li>
      </ul>
      <p v-else class="tc-empty">从左侧地图进入模块后，会记录在此方便继续学习</p>
    </div>
  </div>
</template>

<style scoped>
.training-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.training-card {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  min-height: 160px;
  display: flex;
  flex-direction: column;
}

.daily-card {
  background: linear-gradient(160deg, rgba(56, 189, 248, 0.12), transparent 55%),
    var(--alp-bg-surface);
  border-color: rgba(56, 189, 248, 0.35);
}

.tc-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.tc-head .el-icon {
  color: var(--alp-color-primary);
}

.tc-title {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--alp-color-text);
}

.tc-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.tc-meta .el-icon {
  vertical-align: -2px;
}

.tc-reason {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--alp-color-muted);
  flex: 1;
}

.tc-empty {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.target-list,
.review-list,
.recent-list {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
}

.target-btn,
.review-btn,
.recent-btn {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  padding: 8px 6px;
  border-radius: 8px;
  transition: background var(--alp-transition-fast);
}

.target-btn:hover,
.review-btn:hover,
.recent-btn:hover {
  background: var(--alp-color-primary-soft);
}

.target-item + .target-item {
  border-top: 1px dashed var(--alp-color-border);
}

.target-title {
  display: block;
  font-weight: 600;
  font-size: 13px;
  color: var(--alp-color-text);
}

.target-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.target-reason {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: var(--alp-color-primary);
}

.review-item + .review-item {
  border-top: 1px dashed var(--alp-color-border);
}

.review-mod {
  display: block;
  font-weight: 600;
  font-size: 13px;
}

.review-sec {
  display: block;
  font-size: 12px;
  color: var(--alp-color-muted);
  margin: 4px 0;
}

.recent-btn {
  font-size: 13px;
  color: var(--alp-color-text);
}

@media (max-width: 1200px) {
  .training-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .training-grid {
    grid-template-columns: 1fr;
  }
}
</style>
