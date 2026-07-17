<script setup lang="ts">
import { ArrowRight } from '@element-plus/icons-vue'
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

function difficultyLabel(difficulty: string) {
  if (difficulty.toLowerCase() === 'easy') return '简单'
  if (difficulty.toLowerCase() === 'hard') return '困难'
  return '中等'
}
</script>

<template>
  <div class="training-list">
    <section class="training-list__primary">
      <span class="training-list__label">今日练习</span>
      <template v-if="daily">
        <h3>{{ daily.title }}</h3>
        <p>{{ difficultyLabel(daily.difficulty) }} · 约 {{ daily.etaMin }} 分钟</p>
        <button type="button" @click="emit('openProblem', daily.slug)">
          开始练习
          <el-icon><ArrowRight /></el-icon>
        </button>
      </template>
      <p v-else class="training-list__empty">题库暂未返回可用题目。</p>
    </section>

    <section>
      <div class="training-list__head">
        <span class="training-list__label">薄弱项练习</span>
        <small>{{ targeted.length ? `${targeted.length} 道` : '' }}</small>
      </div>
      <ul v-if="targeted.length">
        <li v-for="problem in targeted" :key="problem.slug">
          <button type="button" @click="emit('openProblem', problem.slug)">
            <span>
              <strong>{{ problem.title }}</strong>
              <small>{{ problem.reason }} · {{ difficultyLabel(problem.difficulty) }}</small>
            </span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </li>
      </ul>
      <p v-else class="training-list__empty">完成章节学习后，将按薄弱项推荐题目。</p>
    </section>

    <section>
      <div class="training-list__head">
        <span class="training-list__label">待复习</span>
        <small>{{ review.length ? `${review.length} 项` : '' }}</small>
      </div>
      <ul v-if="review.length">
        <li v-for="item in review" :key="item.moduleKey">
          <button type="button" @click="emit('openModule', item.moduleKey)">
            <span>
              <strong>{{ item.moduleLabel }}</strong>
              <small>{{ item.sectionLabel }} · {{ item.dueLabel }}</small>
            </span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </li>
      </ul>
      <p v-else class="training-list__empty">目前没有进行中的模块需要复习。</p>
    </section>

    <section>
      <div class="training-list__head">
        <span class="training-list__label">最近访问</span>
        <small>{{ recent.length ? `${recent.length} 个模块` : '' }}</small>
      </div>
      <ul v-if="recent.length">
        <li v-for="item in recent.slice(0, 4)" :key="item.moduleKey">
          <button type="button" @click="emit('openModule', item.moduleKey)">
            <span>
              <strong>{{ item.label }}</strong>
              <small>返回该模块继续学习</small>
            </span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </li>
      </ul>
      <p v-else class="training-list__empty">进入任意学习模块后，这里会保留最近访问记录。</p>
    </section>
  </div>
</template>

<style scoped>
.training-list {
  display: grid;
  grid-template-columns: minmax(190px, 0.75fr) repeat(3, minmax(0, 1fr));
  border-top: 1px solid var(--color-border);
}

.training-list > section {
  min-width: 0;
  padding: 18px 16px 2px;
  border-right: 1px solid var(--color-border);
}

.training-list > section:first-child {
  padding-left: 0;
}

.training-list > section:last-child {
  padding-right: 0;
  border-right: 0;
}

.training-list__primary h3 {
  margin: 10px 0 5px;
  color: var(--color-text-primary);
  font-size: 16px;
}

.training-list__primary p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 11px;
}

.training-list__primary > button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 16px;
  padding: 8px 12px;
  color: #fff;
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  border: 0;
  border-radius: var(--radius-sm);
  background: var(--color-brand);
  cursor: pointer;
}

.training-list__primary > button:hover {
  background: var(--color-brand-hover);
}

.training-list__label {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 650;
}

.training-list__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.training-list__head small {
  color: var(--color-text-muted);
  font-size: 10px;
}

.training-list ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.training-list li + li {
  border-top: 1px solid var(--color-border);
}

.training-list li button {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 14px;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 5px;
  color: var(--color-text-primary);
  text-align: left;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.training-list li button:hover {
  color: var(--color-brand);
  background: var(--color-bg-subtle);
}

.training-list li span {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.training-list li strong {
  overflow: hidden;
  font-size: 12px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.training-list li small {
  overflow: hidden;
  margin-top: 2px;
  color: var(--color-text-muted);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.training-list li .el-icon {
  color: var(--color-text-muted);
  font-size: 11px;
}

.training-list__empty {
  margin: 10px 0 0;
  color: var(--color-text-muted);
  font-size: 11px;
  line-height: 1.6;
}

@media (max-width: 1180px) {
  .training-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .training-list > section,
  .training-list > section:first-child,
  .training-list > section:last-child {
    padding: 16px;
    border-right: 1px solid var(--color-border);
    border-bottom: 1px solid var(--color-border);
  }

  .training-list > section:nth-child(2n) {
    border-right: 0;
  }

  .training-list > section:nth-last-child(-n + 2) {
    border-bottom: 0;
  }
}

@media (max-width: 620px) {
  .training-list {
    grid-template-columns: 1fr;
  }

  .training-list > section,
  .training-list > section:first-child,
  .training-list > section:last-child {
    padding: 16px 0;
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .training-list > section:last-child {
    border-bottom: 0;
  }
}
</style>
