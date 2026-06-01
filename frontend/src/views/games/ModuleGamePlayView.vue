<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, House, Loading, Trophy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { getGameById, getGameComponent, type ModuleGameMeta } from '@/modules/games/gameRegistry'
import {
  clearedCount,
  isLevelCleared,
  markLevelCleared,
} from '@/modules/games/gameProgress'
import { getGameTags } from '@/modules/games/shared/gameShellMeta'
import { isLoggedIn } from '@/stores/auth'
import { applyRemoteProgressPayload } from '@/utils/learningStorage'

const props = defineProps<{ gameId: string }>()

const route = useRoute()
const router = useRouter()

function initialLevelId(gameId: string): string {
  const g = getGameById(gameId)
  if (!g) return ''
  const q = route.query.level as string | undefined
  if (q && g.levels.some((l) => l.id === q)) return q
  return g.levels[0]?.id ?? ''
}

const activeLevelId = ref(initialLevelId(props.gameId))
const levelClearedTick = ref(0)
const game = computed<ModuleGameMeta | undefined>(() => getGameById(props.gameId))
const GameComponent = computed(() => getGameComponent(props.gameId))

const moduleMeta = computed(() =>
  ALGORITHM_MODULES.find((m) => m.key === game.value?.moduleKey),
)

const currentLevel = computed(() =>
  game.value?.levels.find((l) => l.id === activeLevelId.value),
)

const progressText = computed(() => {
  levelClearedTick.value
  const g = game.value
  if (!g) return '0/0'
  return `${clearedCount(g.id, g.levels.length)}/${g.levels.length}`
})

const progressPercent = computed(() => {
  const g = game.value
  if (!g || !g.levels.length) return 0
  levelClearedTick.value
  return Math.round((clearedCount(g.id, g.levels.length) / g.levels.length) * 100)
})

const accent = computed(() => moduleMeta.value?.accent ?? '#38bdf8')

const gameTags = computed(() => (game.value ? getGameTags(game.value.id) : []))

function levelDone(gameId: string, levelId: string) {
  levelClearedTick.value
  return isLevelCleared(gameId, levelId)
}

function selectLevel(id: string) {
  activeLevelId.value = id
  router.replace({
    name: 'module-game-play',
    params: { gameId: props.gameId },
    query: { ...route.query, level: id },
  })
}

function onLevelCleared() {
  const g = game.value
  const lid = activeLevelId.value
  if (!g || !lid) return
  const lv = currentLevel.value
  const isNew = !isLevelCleared(g.id, lid)
  markLevelCleared(g.id, lid, {
    gameTitle: g.title,
    levelTitle: lv?.title,
    moduleKey: g.moduleKey,
  })
  if (isNew) {
    if (isLoggedIn.value) {
      ElMessage.success('关卡通过！本次游戏结果已写入学习记忆，并用于更新掌握度评估。')
    } else {
      ElMessage.warning('关卡通过！登录后可同步学习记录，用于更新掌握度评估。')
    }
  }
  levelClearedTick.value++
  const idx = g.levels.findIndex((l) => l.id === lid)
  if (idx >= 0 && idx < g.levels.length - 1) {
    selectLevel(g.levels[idx + 1]!.id)
  }
}

function goBack() {
  const from = route.query.from as string | undefined
  if (from === 'my-learning') {
    router.push({ name: 'my-learning', query: { tab: 'games' } })
    return
  }
  const mk = game.value?.moduleKey
  if (mk && mk !== '_global') {
    const routeName = MODULE_ROUTE_NAMES[mk]
    if (routeName) {
      router.push({ name: routeName, query: route.query.section ? { section: route.query.section } : {} })
      return
    }
  }
  router.push({ name: 'home' })
}

onMounted(async () => {
  if (!game.value) {
    router.replace({ name: 'home' })
    return
  }
  const qLevel = route.query.level as string | undefined
  const valid = game.value.levels.some((l) => l.id === qLevel)
  activeLevelId.value = valid ? qLevel! : game.value.levels[0]!.id

  if (isLoggedIn.value) {
    try {
      const { fetchLearningProgress } = await import('@/api/learning')
      const r = await fetchLearningProgress()
      applyRemoteProgressPayload((r.payload || {}) as Record<string, unknown>)
      levelClearedTick.value++
    } catch {
      /* ignore */
    }
  }
})

watch(
  () => props.gameId,
  () => {
    const g = getGameById(props.gameId)
    if (!g) {
      router.replace({ name: 'home' })
      return
    }
    activeLevelId.value = g.levels[0]!.id
  },
)

watch(
  () => game.value?.title,
  (t) => {
    if (t) document.title = `${t} · 互动闯关 · 算法智能学习平台`
  },
  { immediate: true },
)
</script>

<template>
  <div v-if="game" class="game-play-page" :style="{ '--game-accent': accent }">
    <header class="game-play-header">
      <div class="header-left">
        <el-button text :icon="ArrowLeft" class="back-btn" @click="goBack">返回学习</el-button>
        <el-button text :icon="House" @click="router.push({ name: 'home' })">首页</el-button>
      </div>
      <div class="header-center">
        <span class="game-badge">互动闯关</span>
        <h1 class="game-title">{{ game.title }}</h1>
        <p class="game-tagline">{{ game.tagline }}</p>
      </div>
      <div class="header-right">
        <span class="stars">{{ '★'.repeat(game.stars) }}{{ '☆'.repeat(3 - game.stars) }}</span>
        <div class="progress-wrap">
          <span class="progress-num">{{ progressText }} 关</span>
          <el-progress
            :percentage="progressPercent"
            :stroke-width="8"
            :show-text="false"
            color="var(--game-accent)"
            style="width: 120px"
          />
        </div>
      </div>
    </header>

    <div class="game-play-body">
      <aside class="level-rail" aria-label="关卡列表">
        <h2 class="rail-title">关卡</h2>
        <button
          v-for="(lv, i) in game.levels"
          :key="lv.id"
          type="button"
          class="level-btn"
          :class="{
            'is-active': activeLevelId === lv.id,
            'is-done': levelDone(game.id, lv.id),
          }"
          @click="selectLevel(lv.id)"
        >
          <span class="level-index">{{ i + 1 }}</span>
          <span class="level-name">{{ lv.title }}</span>
          <el-icon v-if="levelDone(game.id, lv.id)" class="level-trophy"><Trophy /></el-icon>
        </button>
      </aside>

      <main class="game-stage">
        <div class="stage-head">
          <div class="stage-head__row">
            <h2 class="stage-title">{{ currentLevel?.title }}</h2>
          </div>
          <p class="stage-goal">{{ currentLevel?.goal }}</p>
          <p v-if="moduleMeta" class="stage-module">
            关联模块：{{ moduleMeta.label }}
          </p>
          <div v-if="gameTags.length" class="stage-tags">
            <span v-for="tag in gameTags" :key="tag" class="stage-tag">{{ tag }}</span>
          </div>
        </div>
        <div class="stage-canvas">
          <div v-if="!GameComponent" class="stage-loading">
            <el-icon class="is-loading" :size="32"><Loading /></el-icon>
            <p>游戏加载中…</p>
          </div>
          <Suspense v-else-if="activeLevelId">
            <component
              :is="GameComponent"
              :key="`${game.id}-${activeLevelId}`"
              :level-id="activeLevelId"
              @cleared="onLevelCleared"
            />
            <template #fallback>
              <div class="stage-loading">
                <el-icon class="is-loading" :size="32"><Loading /></el-icon>
                <p>关卡准备中…</p>
              </div>
            </template>
          </Suspense>
          <p v-else class="stage-loading">请选择关卡</p>
        </div>
      </main>
    </div>
  </div>

  <div v-else class="game-play-missing">
    <el-empty description="未找到该小游戏">
      <el-button type="primary" @click="router.push({ name: 'home' })">回首页</el-button>
    </el-empty>
  </div>
</template>

<style scoped>
.game-play-page {
  min-height: 100vh;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  background: radial-gradient(
      ellipse 80% 50% at 50% -20%,
      color-mix(in srgb, var(--game-accent) 18%, transparent),
      transparent
    ),
    var(--alp-bg-shell);
  border-radius: 0;
  overflow: hidden;
}

.game-play-header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--alp-color-border);
  background: color-mix(in srgb, var(--game-accent) 6%, var(--alp-bg-surface-solid, #0f172a));
}

.header-left {
  display: flex;
  gap: 4px;
}

.back-btn {
  font-weight: 600;
}

.header-center {
  text-align: center;
  min-width: 0;
}

.game-badge {
  display: inline-block;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--game-accent);
  background: color-mix(in srgb, var(--game-accent) 14%, transparent);
  border-radius: 999px;
  margin-bottom: 6px;
}

.game-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--alp-color-text);
}

.game-tagline {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--alp-color-muted);
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.stars {
  font-size: 12px;
  color: #fbbf24;
  letter-spacing: 2px;
}

.progress-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-num {
  font-size: 12px;
  color: var(--alp-color-muted);
  white-space: nowrap;
}

.game-play-body {
  flex: 1;
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: 0;
}

.level-rail {
  padding: 16px 12px;
  border-right: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.5));
}

.rail-title {
  margin: 0 0 12px 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.level-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin-bottom: 6px;
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--alp-color-text);
  cursor: pointer;
  text-align: left;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.level-btn:hover {
  background: var(--alp-bg-soft-block);
}

.level-btn.is-active {
  border-color: color-mix(in srgb, var(--game-accent) 50%, transparent);
  background: color-mix(in srgb, var(--game-accent) 12%, transparent);
}

.level-btn.is-done .level-index {
  background: color-mix(in srgb, #22c55e 25%, transparent);
  color: #86efac;
}

.level-index {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  border-radius: 6px;
  background: var(--alp-bg-soft-block);
}

.level-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.3;
}

.level-trophy {
  color: #fbbf24;
  font-size: 16px;
}

.game-stage {
  display: flex;
  flex-direction: column;
  min-height: 480px;
  padding: 20px 24px 28px;
}

.stage-head {
  margin-bottom: 20px;
}

.stage-title {
  margin: 0 0 8px;
  font-size: 1.25rem;
  font-weight: 600;
}

.stage-goal {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--alp-color-muted);
  max-width: 52rem;
}

.stage-head__row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stage-module {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--game-accent);
}

.stage-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.stage-tag {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  color: var(--alp-color-muted);
  border: 1px solid var(--alp-color-border);
  border-radius: 999px;
  background: var(--alp-bg-soft-block);
}

.stage-canvas {
  flex: 1;
  padding: 24px;
  border-radius: 14px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.45));
  min-height: 420px;
  display: flex;
  flex-direction: column;
}

.stage-canvas > :deep(*) {
  flex: 1;
  min-height: 0;
}

.stage-canvas :deep(.alp-game-hint) {
  font-size: 14px;
}

.stage-canvas :deep(.alp-game-cell) {
  min-width: 44px;
  height: 44px;
  font-size: 15px;
}

.stage-canvas :deep(.alp-game-stack) {
  min-height: 200px;
}

.stage-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 280px;
  color: var(--alp-color-muted);
  font-size: 14px;
}

.game-play-missing {
  padding: 48px 24px;
}

@media (max-width: 768px) {
  .game-play-header {
    grid-template-columns: 1fr;
    text-align: left;
  }

  .header-center {
    text-align: left;
  }

  .header-right {
    align-items: flex-start;
  }

  .game-play-body {
    grid-template-columns: 1fr;
  }

  .level-rail {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    border-right: none;
    border-bottom: 1px solid var(--alp-color-border);
  }

  .rail-title {
    width: 100%;
  }

  .level-btn {
    width: auto;
    flex: 1 1 auto;
    min-width: 120px;
  }
}
</style>
