<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Medal, TrendCharts } from '@element-plus/icons-vue'
import type {
  ActivityFeedItem,
  LeaderboardEntry,
  PlatformStat,
} from '@/utils/homeDashboard'

const props = defineProps<{
  stats: PlatformStat[]
  acBoard: LeaderboardEntry[]
  streakBoard: LeaderboardEntry[]
  feed: ActivityFeedItem[]
}>()

const displayStats = ref<PlatformStat[]>([])

function animateStats(target: PlatformStat[]) {
  displayStats.value = target.map((s) => ({ ...s, value: 0 }))
  const start = performance.now()
  const duration = 900
  function frame(now: number) {
    const t = Math.min(1, (now - start) / duration)
    const ease = 1 - (1 - t) ** 3
    displayStats.value = target.map((s) => ({
      ...s,
      value: Math.round(s.value * ease),
    }))
    if (t < 1) requestAnimationFrame(frame)
  }
  requestAnimationFrame(frame)
}

onMounted(() => animateStats(props.stats))
watch(
  () => props.stats,
  (v) => animateStats(v),
  { deep: true },
)

function avatarStyle(hue: number) {
  return {
    background: `hsl(${hue} 70% 42%)`,
  }
}
</script>

<template>
  <div class="community-panel">
    <div class="platform-stats">
      <div v-for="s in displayStats" :key="s.key" class="platform-stat">
        <span class="stat-num">
          {{ s.value.toLocaleString() }}<small v-if="s.suffix">{{ s.suffix }}</small>
        </span>
        <span class="stat-lbl">{{ s.label }}</span>
      </div>
    </div>

    <div class="boards-row">
      <div class="board">
        <div class="board-head">
          <el-icon><Medal /></el-icon>
          <span>本周 AC 榜</span>
        </div>
        <ul class="board-list">
          <li v-for="e in acBoard" :key="e.rank" class="board-item">
            <span class="rank" :data-rank="e.rank">{{ e.rank }}</span>
            <span class="avatar" :style="avatarStyle(e.avatarHue)">{{ e.name.slice(0, 1) }}</span>
            <span class="name">{{ e.name }}</span>
            <span class="score">{{ e.score }} {{ e.unit }}</span>
          </li>
        </ul>
        <el-empty v-if="!acBoard.length" description="暂无真实排行数据" :image-size="42" />
      </div>
      <div class="board">
        <div class="board-head">
          <el-icon><TrendCharts /></el-icon>
          <span>连续打卡榜</span>
        </div>
        <ul class="board-list">
          <li v-for="e in streakBoard" :key="e.rank" class="board-item">
            <span class="rank" :data-rank="e.rank">{{ e.rank }}</span>
            <span class="avatar" :style="avatarStyle(e.avatarHue)">{{ e.name.slice(0, 1) }}</span>
            <span class="name">{{ e.name }}</span>
            <span class="score">{{ e.score }} {{ e.unit }}</span>
          </li>
        </ul>
        <el-empty v-if="!streakBoard.length" description="暂无真实打卡数据" :image-size="42" />
      </div>
    </div>

    <div class="feed">
      <div class="board-head">
        <span>学习动态</span>
        <el-tag size="small" type="info" effect="plain" round>数据库</el-tag>
      </div>
      <ul class="feed-list">
        <li v-for="item in feed" :key="item.id" class="feed-item">
          <strong>{{ item.user }}</strong>
          <span>{{ item.action }}</span>
          <time>{{ item.time }}</time>
        </li>
      </ul>
      <el-empty v-if="!feed.length" description="暂无公开学习动态" :image-size="42" />
    </div>
  </div>
</template>

<style scoped>
.community-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.platform-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.platform-stat {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: rgba(15, 23, 42, 0.4);
}

.stat-num {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--alp-color-primary);
  line-height: 1.2;
}

.stat-num small {
  font-size: 12px;
  font-weight: 500;
  color: var(--alp-color-muted);
}

.stat-lbl {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.boards-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.board,
.feed {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: rgba(15, 23, 42, 0.35);
}

.board-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.board-list,
.feed-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.board-item {
  display: grid;
  grid-template-columns: 22px 24px 1fr auto;
  align-items: center;
  gap: 6px;
  padding: 5px 0;
  font-size: 12px;
}

.rank {
  font-weight: 700;
  color: var(--alp-color-muted);
  text-align: center;
}

.rank[data-rank='1'] {
  color: #fbbf24;
}
.rank[data-rank='2'] {
  color: #94a3b8;
}
.rank[data-rank='3'] {
  color: #d97706;
}

.avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}

.name {
  color: var(--alp-color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.score {
  color: var(--alp-color-primary);
  font-weight: 600;
  white-space: nowrap;
}

.feed-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 6px;
  padding: 6px 0;
  font-size: 12px;
  border-bottom: 1px dashed rgba(51, 65, 85, 0.5);
}

.feed-item:last-child {
  border-bottom: none;
}

.feed-item strong {
  color: var(--alp-color-text);
}

.feed-item span {
  color: var(--alp-color-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.feed-item time {
  color: var(--alp-color-muted);
  font-size: 11px;
  white-space: nowrap;
}

@media (max-width: 1100px) {
  .boards-row {
    grid-template-columns: 1fr;
  }
}
</style>
