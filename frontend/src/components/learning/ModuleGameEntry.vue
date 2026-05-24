<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Trophy, VideoPlay, ArrowRight } from '@element-plus/icons-vue'
import { getDetectiveGame, getModuleGame, type ModuleGameMeta } from '@/modules/games/gameRegistry'
import { clearedCount } from '@/modules/games/gameProgress'

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

function goPlay(game: ModuleGameMeta) {
  const query: Record<string, string> = {}
  if (props.moduleKey && game.moduleKey !== '_global') {
    query.from = props.moduleKey
    if (typeof route.query.section === 'string') {
      query.section = route.query.section
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
    <div class="alp-game-panel" style="--game-accent: #a78bfa">
      <div class="alp-game-panel__head">
        <div>
          <h3 class="alp-game-panel__title">毕业挑战 · {{ detectiveGame.title }}</h3>
          <p class="alp-game-panel__tagline">{{ detectiveGame.tagline }}</p>
        </div>
        <el-icon :size="20" color="#a78bfa"><Trophy /></el-icon>
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
</style>
