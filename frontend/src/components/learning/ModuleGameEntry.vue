<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Trophy, VideoPlay, ArrowRight, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import {
  getDetectiveGame,
  getModuleGame,
  getModuleGameLevelForSection,
  type ModuleGameMeta,
  type GameLevelMeta,
} from '@/modules/games/gameRegistry'
import { clearedCount, isLevelCleared, getGameHistory, type GameClearRecord } from '@/modules/games/gameProgress'

const props = withDefaults(
  defineProps<{
    moduleKey: string
    sectionId?: string
    variant?: 'default' | 'summary' | 'detective-only'
  }>(),
  { variant: 'default' },
)

const router = useRouter()
const route = useRoute()
const levelClearedTick = ref(0)

const moduleGame = computed(() => getModuleGame(props.moduleKey))
const chapterLevel = computed(() =>
  getModuleGameLevelForSection(props.moduleKey, props.sectionId),
)
const showDetective = computed(
  () =>
    props.variant === 'detective-only' ||
    props.variant === 'summary' ||
    props.sectionId === 'summary',
)
const detectiveGame = computed(() => getDetectiveGame())

const moduleProgressText = computed(() => {
  levelClearedTick.value
  const g = moduleGame.value
  if (!g) return ''
  return `${clearedCount(g.id, g.levels.length)}/${g.levels.length} 关`
})

/** 算法侦探各关卡通关状态 */
const detectiveLevelStatus = computed(() => {
  levelClearedTick.value
  const g = detectiveGame.value
  return g.levels.map((lv: GameLevelMeta) => ({
    id: lv.id,
    title: lv.title,
    goal: lv.goal,
    cleared: isLevelCleared(g.id, lv.id),
  }))
})

const detectiveClearedCount = computed(() => {
  levelClearedTick.value
  const g = detectiveGame.value
  return clearedCount(g.id, g.levels.length)
})

/** 算法侦探最近闯关记录 */
const detectiveRecentHistory = computed(() => {
  levelClearedTick.value
  const g = detectiveGame.value
  const history: GameClearRecord[] = getGameHistory()
  return history
    .filter((r) => r.gameId === g.id)
    .slice(0, 5)
    .map((r) => ({
      ...r,
      timeLabel: formatTime(r.clearedAt),
    }))
})

function formatTime(ts: number): string {
  const diff = Date.now() - ts
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} 小时前`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day} 天前`
  return new Date(ts).toLocaleDateString()
}

function goPlay(game: ModuleGameMeta) {
  const query: Record<string, string> = {}
  if (props.moduleKey && game.moduleKey !== '_global') {
    query.from = props.moduleKey
    const level = chapterLevel.value
    if (level && game.levels.some((lv) => lv.id === level.id)) {
      query.level = level.id
    }
    if (typeof route.query.section === 'string') {
      query.section = route.query.section
    } else if (props.sectionId) {
      query.section = props.sectionId
    }
  }
  if (props.variant === 'detective-only') {
    query.from = 'my-learning'
  }
  router.push({
    name: 'module-game-play',
    params: { gameId: game.id },
    query,
  })
}
</script>

<template>
  <div v-if="moduleGame && variant === 'default'" class="alp-game-entry">
    <div class="alp-game-panel">
      <div class="alp-game-panel__head">
        <div>
          <h3 class="alp-game-panel__title">互动小游戏 · {{ moduleGame.title }}</h3>
          <p class="alp-game-panel__tagline">
            {{ moduleGame.tagline }} — 点击进入独立闯关页面
          </p>
          <p v-if="chapterLevel" class="alp-game-panel__tagline">
            本章推荐关卡：{{ chapterLevel.title }} · {{ chapterLevel.goal }}
          </p>
        </div>
        <span class="alp-game-stars">{{ '★'.repeat(moduleGame.stars) }}{{ '☆'.repeat(3 - moduleGame.stars) }}</span>
      </div>
      <el-button type="primary" :icon="VideoPlay" @click="goPlay(moduleGame)">
        进入游戏（{{ moduleProgressText }}）
        <el-icon class="entry-arrow"><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>

  <div v-if="showDetective" class="alp-game-entry alp-game-entry--summary">
    <div class="alp-game-panel" style="--game-accent: var(--alp-color-accent)">
      <div class="alp-game-panel__head">
        <div>
          <h3 class="alp-game-panel__title">毕业挑战 · {{ detectiveGame.title }}</h3>
          <p class="alp-game-panel__tagline">{{ detectiveGame.tagline }}</p>
        </div>
        <el-icon :size="20" color="#9c7a3d"><Trophy /></el-icon>
      </div>

      <!-- 关卡通关状态 -->
      <div class="detective-levels">
        <div class="detective-levels__head">
          <span class="detective-levels__label">闯关进度</span>
          <span class="detective-levels__count">{{ detectiveClearedCount }}/{{ detectiveGame.levels.length }}</span>
        </div>
        <el-progress
          :percentage="Math.round((detectiveClearedCount / detectiveGame.levels.length) * 100)"
          :stroke-width="6"
          :show-text="false"
          color="#9c7a3d"
          class="detective-progress"
        />
        <ul class="detective-level-list">
          <li
            v-for="lv in detectiveLevelStatus"
            :key="lv.id"
            class="detective-level-item"
            :class="{ 'detective-level-item--cleared': lv.cleared }"
          >
            <el-icon v-if="lv.cleared" :size="14" class="detective-level-icon cleared"><CircleCheck /></el-icon>
            <el-icon v-else :size="14" class="detective-level-icon uncleared"><CircleClose /></el-icon>
            <span class="detective-level-title">{{ lv.title }}</span>
            <span class="detective-level-goal">{{ lv.goal }}</span>
          </li>
        </ul>
      </div>

      <!-- 最近通关记录 -->
      <div v-if="detectiveRecentHistory.length" class="detective-history">
        <span class="detective-history__label">最近通关</span>
        <ul class="detective-history-list">
          <li v-for="rec in detectiveRecentHistory" :key="rec.levelId" class="detective-history-item">
            <el-icon :size="12" color="#34d399"><CircleCheck /></el-icon>
            <span class="detective-history-title">{{ rec.levelTitle }}</span>
            <span class="detective-history-time">{{ rec.timeLabel }}</span>
          </li>
        </ul>
      </div>

      <el-button type="primary" plain :icon="VideoPlay" @click="goPlay(detectiveGame)">
        进入算法侦探
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.entry-arrow {
  margin-left: 4px;
}

/* 闯关进度 */
.detective-levels {
  margin: 12px 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(var(--alp-color-accent-rgb),0.06);
  border: 1px solid rgba(var(--alp-color-accent-rgb),0.12);
}

.detective-levels__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.detective-levels__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-accent);
  letter-spacing: 0.05em;
}

.detective-levels__count {
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-accent);
  font-family: 'Cascadia Code', ui-monospace, Consolas, monospace;
}

.detective-progress {
  margin-bottom: 10px;
}

.detective-level-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detective-level-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.3);
  border: 1px solid transparent;
  transition: border-color 0.2s, background 0.2s;
}

.detective-level-item--cleared {
  border-color: rgba(52, 211, 153, 0.2);
  background: rgba(52, 211, 153, 0.04);
}

.detective-level-icon {
  flex-shrink: 0;
}

.detective-level-icon.cleared {
  color: #34d399;
}

.detective-level-icon.uncleared {
  color: #475569;
}

.detective-level-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  white-space: nowrap;
}

.detective-level-goal {
  font-size: 11px;
  color: var(--alp-color-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-left: auto;
  max-width: 50%;
}

/* 最近通关记录 */
.detective-history {
  margin: 10px 0 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(52, 211, 153, 0.04);
  border: 1px solid rgba(52, 211, 153, 0.1);
}

.detective-history__label {
  font-size: 11px;
  font-weight: 600;
  color: #34d399;
  letter-spacing: 0.05em;
}

.detective-history-list {
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detective-history-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.detective-history-title {
  color: var(--alp-color-text);
  font-weight: 500;
}

.detective-history-time {
  color: var(--alp-color-muted);
  margin-left: auto;
  font-size: 11px;
}
</style>
