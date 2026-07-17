<script setup lang="ts">
import type { LeaderboardEntry, PlatformStat } from '@/utils/homeDashboard'

defineProps<{
  stats: PlatformStat[]
  acBoard: LeaderboardEntry[]
  streakBoard: LeaderboardEntry[]
}>()
</script>

<template>
  <div class="community-summary">
    <dl class="community-summary__stats">
      <div v-for="stat in stats" :key="stat.key">
        <dt>{{ stat.label }}</dt>
        <dd>{{ stat.value.toLocaleString() }}<small>{{ stat.suffix }}</small></dd>
      </div>
    </dl>

    <div class="community-summary__boards">
      <section>
        <h3>本周通过</h3>
        <ol v-if="acBoard.length">
          <li v-for="entry in acBoard.slice(0, 3)" :key="entry.rank">
            <span>{{ entry.rank }}. {{ entry.name }}</span>
            <strong>{{ entry.score }} {{ entry.unit }}</strong>
          </li>
        </ol>
        <p v-else>暂时没有真实排行数据。</p>
      </section>

      <section>
        <h3>连续学习</h3>
        <ol v-if="streakBoard.length">
          <li v-for="entry in streakBoard.slice(0, 3)" :key="entry.rank">
            <span>{{ entry.rank }}. {{ entry.name }}</span>
            <strong>{{ entry.score }} {{ entry.unit }}</strong>
          </li>
        </ol>
        <p v-else>暂时没有真实打卡数据。</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.community-summary {
  border-top: 1px solid var(--color-border);
}

.community-summary__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
}

.community-summary__stats > div {
  padding: 14px 12px 14px 0;
  border-right: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.community-summary__stats > div:nth-child(2n) {
  padding-left: 14px;
  border-right: 0;
}

.community-summary__stats dt {
  color: var(--color-text-muted);
  font-size: 10px;
}

.community-summary__stats dd {
  margin: 3px 0 0;
  color: var(--color-text-primary);
  font-size: 18px;
  font-weight: 680;
  font-variant-numeric: tabular-nums;
}

.community-summary__stats small {
  margin-left: 2px;
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 500;
}

.community-summary__boards {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.community-summary__boards section {
  min-width: 0;
  padding: 16px 14px 0 0;
  border-right: 1px solid var(--color-border);
}

.community-summary__boards section:last-child {
  padding-right: 0;
  padding-left: 14px;
  border-right: 0;
}

.community-summary__boards h3 {
  margin: 0 0 8px;
  color: var(--color-text-secondary);
  font-size: 11px;
}

.community-summary__boards ol {
  margin: 0;
  padding: 0;
  list-style: none;
}

.community-summary__boards li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 0;
  color: var(--color-text-secondary);
  font-size: 10px;
}

.community-summary__boards li span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-summary__boards li strong {
  color: var(--color-text-primary);
  white-space: nowrap;
}

.community-summary__boards p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 10px;
  line-height: 1.6;
}

@media (max-width: 420px) {
  .community-summary__boards {
    grid-template-columns: 1fr;
  }

  .community-summary__boards section,
  .community-summary__boards section:last-child {
    padding: 14px 0;
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .community-summary__boards section:last-child {
    border-bottom: 0;
  }
}
</style>
