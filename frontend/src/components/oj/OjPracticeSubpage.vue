<script setup lang="ts">
import { computed } from 'vue'
import { Check, Clock, DataAnalysis, Star } from '@element-plus/icons-vue'
import type { ProblemDetail } from '@/api/oj'
import type { OjPracticeRecord } from '@/utils/ojPracticeHistory'

const props = defineProps<{
  page: 'history' | 'favorite' | 'statistics'
  problem: ProblemDetail
  records: OjPracticeRecord[]
  favorite: boolean
}>()

const emit = defineEmits<{ toggleFavorite: []; back: [] }>()
const problemRecords = computed(() => props.records.filter((item) => item.slug === props.problem.slug).reverse())
const accepted = computed(() => problemRecords.value.filter((item) => item.verdict === 'AC').length)
const acceptanceRate = computed(() => problemRecords.value.length
  ? Math.round((accepted.value / problemRecords.value.length) * 100)
  : 0)
const lastAttempt = computed(() => problemRecords.value[0])

function verdictLabel(value: string) {
  return ({ AC: '通过', WA: '答案错误', TLE: '超时', RE: '运行错误', CE: '编译错误' } as Record<string, string>)[value] ?? value
}

function verdictType(value: string) {
  return value === 'AC' ? 'success' : value === 'WA' ? 'warning' : 'danger'
}

function formatTime(value: number) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <section class="practice-subpage">
    <header class="subpage-head">
      <div>
        <span class="subpage-context">#{{ problem.lc_id || '—' }} {{ problem.title }}</span>
        <h2>{{ page === 'history' ? '提交记录' : page === 'favorite' ? '题目收藏' : '练习统计' }}</h2>
      </div>
      <el-button @click="emit('back')">返回练习</el-button>
    </header>

    <template v-if="page === 'history'">
      <div v-if="problemRecords.length" class="history-list">
        <article v-for="(item, index) in problemRecords" :key="`${item.at}-${index}`" class="history-row">
          <span class="history-index">{{ problemRecords.length - index }}</span>
          <el-tag :type="verdictType(item.verdict)" effect="plain">{{ verdictLabel(item.verdict) }}</el-tag>
          <time :datetime="new Date(item.at).toISOString()">{{ formatTime(item.at) }}</time>
          <span class="history-source">{{ index === 0 ? '最近一次' : '历史提交' }}</span>
        </article>
      </div>
      <el-empty v-else description="还没有运行或提交记录">
        <el-button type="primary" @click="emit('back')">开始第一次练习</el-button>
      </el-empty>
    </template>

    <template v-else-if="page === 'favorite'">
      <div class="favorite-panel">
        <el-icon class="favorite-icon" :class="{ active: favorite }"><Star /></el-icon>
        <h3>{{ favorite ? '这道题已加入收藏' : '收藏这道题，稍后继续练习' }}</h3>
        <p>收藏状态会保存在当前浏览器中，你可以随时回来查看题目与最近练习结果。</p>
        <el-button :type="favorite ? 'default' : 'primary'" @click="emit('toggleFavorite')">
          {{ favorite ? '取消收藏' : '加入收藏' }}
        </el-button>
      </div>
    </template>

    <template v-else>
      <div class="stats-strip">
        <div><el-icon><Clock /></el-icon><span>尝试次数</span><strong>{{ problemRecords.length }}</strong></div>
        <div><el-icon><Check /></el-icon><span>通过次数</span><strong>{{ accepted }}</strong></div>
        <div><el-icon><DataAnalysis /></el-icon><span>通过率</span><strong>{{ acceptanceRate }}%</strong></div>
      </div>
      <div class="stats-detail">
        <div><span>最近结果</span><el-tag v-if="lastAttempt" :type="verdictType(lastAttempt.verdict)">{{ verdictLabel(lastAttempt.verdict) }}</el-tag><strong v-else>暂无</strong></div>
        <div><span>最近练习</span><strong>{{ lastAttempt ? formatTime(lastAttempt.at) : '尚未开始' }}</strong></div>
        <div><span>当前状态</span><strong>{{ accepted ? '已通过，可继续优化' : problemRecords.length ? '继续定位问题' : '等待首次提交' }}</strong></div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.practice-subpage { height: 100%; overflow: auto; padding: 28px clamp(20px, 4vw, 56px); box-sizing: border-box; background: var(--alp-bg-surface); color: var(--alp-color-text); }
.subpage-head { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid var(--alp-color-border); }
.subpage-context { color: var(--alp-color-muted); font-size: 13px; }
.subpage-head h2 { margin: 5px 0 0; font-size: 22px; }
.history-list { margin-top: 18px; border: 1px solid var(--alp-color-border); border-radius: var(--alp-radius-card); overflow: hidden; }
.history-row { display: grid; grid-template-columns: 42px 110px minmax(150px, 1fr) 80px; align-items: center; gap: 12px; min-height: 54px; padding: 0 16px; }
.history-row + .history-row { border-top: 1px solid var(--alp-color-border); }
.history-index, .history-source, .history-row time { color: var(--alp-color-muted); font-size: 12px; }
.favorite-panel { max-width: 560px; margin: 56px auto; text-align: center; }
.favorite-icon { font-size: 44px; color: var(--alp-color-muted); }
.favorite-icon.active { color: var(--el-color-warning); }
.favorite-panel h3 { margin: 16px 0 8px; }
.favorite-panel p { margin: 0 auto 20px; color: var(--alp-color-muted); line-height: 1.7; }
.stats-strip { display: flex; margin-top: 22px; border: 1px solid var(--alp-color-border); border-radius: var(--alp-radius-card); overflow: hidden; }
.stats-strip > div { flex: 1; display: grid; grid-template-columns: 24px 1fr; gap: 5px 10px; padding: 20px; }
.stats-strip > div + div { border-left: 1px solid var(--alp-color-border); }
.stats-strip .el-icon { grid-row: 1 / 3; align-self: center; color: var(--alp-color-primary); font-size: 20px; }
.stats-strip span, .stats-detail span { color: var(--alp-color-muted); font-size: 12px; }
.stats-strip strong { font-size: 24px; }
.stats-detail { margin-top: 18px; }
.stats-detail > div { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 48px; border-bottom: 1px solid var(--alp-color-border); }
.stats-detail strong { font-size: 13px; }
@media (max-width: 700px) { .subpage-head { align-items: flex-start; } .history-row { grid-template-columns: 32px 90px 1fr; } .history-source { display: none; } .stats-strip { flex-direction: column; } .stats-strip > div + div { border-left: 0; border-top: 1px solid var(--alp-color-border); } }
</style>
