<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Clock,
  Collection,
  DataLine,
  StarFilled,
  TrendCharts,
  Trophy,
} from '@element-plus/icons-vue'
import { MODULE_PATH_HINTS } from '@/constants/modulePathHints'
import { buildLearningOverview } from '@/utils/learningOverview'
import {
  loadFavoriteKeys,
  loadRecentVisits,
  toggleFavorite,
  type RecentVisit,
} from '@/utils/learningBookmarks'
import { useModuleNavigation } from '@/composables/useModuleNavigation'
import { isLoggedIn, getUser } from '@/stores/auth'
import { buildGameLearningOverview } from '@/utils/gameLearningOverview'
import { applyRemoteProgressPayload } from '@/utils/learningStorage'
import PersonaChatPanel from '@/components/persona/PersonaChatPanel.vue'
import RecommendedResourcesPanel from '@/components/learning/RecommendedResourcesPanel.vue'
import { buildActivityDays } from '@/utils/learningActivity'
import LearningProgressRing from '@/components/learning/LearningProgressRing.vue'
import LearningSectionDonut from '@/components/learning/LearningSectionDonut.vue'
import LearningModuleBarChart from '@/components/learning/LearningModuleBarChart.vue'
import LearningModuleRadar from '@/components/learning/LearningModuleRadar.vue'
import LearningActivityHeatmap from '@/components/learning/LearningActivityHeatmap.vue'
import LearningEvaluationPanel from '@/components/learning/LearningEvaluationPanel.vue'

const route = useRoute()
const router = useRouter()
const { goModule } = useModuleNavigation()

const activeTab = ref(
  typeof route.query.tab === 'string' ? route.query.tab : 'overview',
)

const overview = computed(() => buildLearningOverview())
const gameRevision = ref(0)
const gameOverview = computed(() => {
  void gameRevision.value
  return buildGameLearningOverview()
})
const favRevision = ref(0)

onMounted(async () => {
  if (!isLoggedIn.value) return
  try {
    const { fetchLearningProgress } = await import('@/api/learning')
    const r = await fetchLearningProgress()
    applyRemoteProgressPayload((r.payload || {}) as Record<string, unknown>)
    gameRevision.value++
  } catch {
    /* ignore */
  }
})

const favoriteRows = computed(() => {
  void favRevision.value
  const keys = new Set(loadFavoriteKeys())
  return overview.value.rows.filter((r) => keys.has(r.key) && r.available)
})

const recentVisits = computed(() => loadRecentVisits())

const inProgressRows = computed(() =>
  overview.value.inProgressModules.length > 0
    ? overview.value.inProgressModules
    : overview.value.rows.filter((r) => r.available && r.percent === 0 && r.hasProgressData).slice(0, 3),
)

const totalSectionsDone = computed(() =>
  overview.value.rows.reduce((acc, r) => acc + r.doneCount, 0),
)

const totalSections = computed(() =>
  overview.value.rows.reduce((acc, r) => acc + r.totalCount, 0),
)

const activityDays = computed(() => {
  const visitTs = recentVisits.value.map((v) => v.visitedAt)
  const gameTs = gameOverview.value.recentHistory.map((r) => r.clearedAt)
  return buildActivityDays([...visitTs, ...gameTs])
})

function onToggleFavorite(key: string) {
  toggleFavorite(key)
  favRevision.value += 1
}

function formatVisitTime(ts: number) {
  const d = new Date(ts)
  const now = Date.now()
  const diff = now - ts
  if (diff < 60_000) return '刚刚'
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function openRecent(visit: RecentVisit) {
  goModule(visit.moduleKey)
}

function onTabChange(name: string | number) {
  activeTab.value = String(name)
  router.replace({ query: { ...route.query, tab: String(name) } })
}
</script>

<template>
  <el-card shadow="never" class="page-card">
    <el-page-header title="我的学习" @back="router.push({ name: 'home' })" />
    <el-divider />

    <p class="muted">
      汇总学习进度、小游戏闯关与收藏。登录后小节进度与游戏记录会同步至云端数据库。
    </p>

    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-tile">
          <el-icon class="stat-icon"><TrendCharts /></el-icon>
          <strong>{{ overview.overallPercent }}%</strong>
          <span>总进度</span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-tile">
          <el-icon class="stat-icon"><DataLine /></el-icon>
          <strong>{{ overview.completedModules }}</strong>
          <span>已完成模块</span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-tile">
          <el-icon class="stat-icon"><Collection /></el-icon>
          <strong>{{ totalSectionsDone }}</strong>
          <span>已完成小节</span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-tile">
          <el-icon class="stat-icon"><Clock /></el-icon>
          <strong>{{ favoriteRows.length }}</strong>
          <span>收藏模块</span>
        </div>
      </el-col>
    </el-row>

    <template v-if="!isLoggedIn">
      <el-alert
        title="登录后可云端保存学习进度"
        type="info"
        show-icon
        :closable="false"
        class="alert-block"
      />
      <div class="actions">
        <el-button
          type="primary"
          @click="router.push({ name: 'login', query: { redirect: route.fullPath } })"
        >
          登录
        </el-button>
        <el-button @click="router.push({ name: 'register' })">注册</el-button>
      </div>
    </template>

    <el-descriptions v-else title="账号与同步" :column="2" border class="desc-block">
      <el-descriptions-item label="当前用户">{{ getUser()?.username }}</el-descriptions-item>
      <el-descriptions-item label="小节进度">
        {{ totalSectionsDone }} / {{ totalSections }} 节
      </el-descriptions-item>
    </el-descriptions>

    <el-tabs v-model="activeTab" class="learn-tabs" @tab-change="onTabChange">
      <el-tab-pane label="学习概览" name="overview">
        <el-row :gutter="16" class="viz-row">
          <el-col :span="24" :md="8">
            <div class="viz-card">
              <h3 class="section-title viz-title">总进度</h3>
              <LearningProgressRing
                :percent="overview.overallPercent"
                :sublabel="`${overview.completedModules} 个模块已完成`"
              />
            </div>
          </el-col>
          <el-col :span="24" :md="8">
            <div class="viz-card">
              <h3 class="section-title viz-title">阶段分布</h3>
              <LearningSectionDonut :rows="overview.rows" />
            </div>
          </el-col>
          <el-col :span="24" :md="8">
            <div class="viz-card">
              <h3 class="section-title viz-title">学习活跃度</h3>
              <LearningActivityHeatmap :days="activityDays" />
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="16" class="viz-row">
          <el-col :span="24" :lg="14">
            <div class="viz-card">
              <h3 class="section-title viz-title">模块进度</h3>
              <LearningModuleBarChart :rows="overview.rows" @select="goModule" />
            </div>
          </el-col>
          <el-col :span="24" :lg="10">
            <div class="viz-card">
              <h3 class="section-title viz-title">掌握雷达</h3>
              <LearningModuleRadar :rows="overview.rows" />
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :xs="24" :md="14">
            <h3 class="section-title">进行中</h3>
            <div v-if="inProgressRows.length" class="module-grid">
              <div
                v-for="row in inProgressRows"
                :key="row.key"
                class="module-card hover-card"
                role="button"
                tabindex="0"
                @click="goModule(row.key)"
                @keydown.enter.prevent="goModule(row.key)"
              >
                <div class="card-top">
                  <span class="card-name" :style="{ color: row.accent }">{{ row.label }}</span>
                  <el-tag size="small" type="primary" effect="plain">{{ row.percent }}%</el-tag>
                </div>
                <el-progress
                  :percentage="row.percent"
                  :stroke-width="6"
                  :show-text="false"
                  :color="row.accent"
                />
                <p class="card-meta">
                  {{ row.doneCount }} / {{ row.totalCount }} 节
                </p>
              </div>
            </div>
            <el-empty v-else description="暂无进行中的模块，从学习路径开始吧">
              <el-button type="primary" @click="router.push({ name: 'learning-path' })">
                查看学习路径
              </el-button>
            </el-empty>

            <h3 class="section-title">掌握情况</h3>
            <div class="tag-groups">
              <div>
                <div class="tag-label">掌握较好</div>
                <el-tag
                  v-for="r in overview.strongModules"
                  :key="r.key"
                  class="mini-tag"
                  type="success"
                  effect="plain"
                >
                  {{ r.label }} {{ r.percent }}%
                </el-tag>
                <span v-if="!overview.strongModules.length" class="empty-hint">继续学习以积累掌握模块</span>
              </div>
              <div>
                <div class="tag-label">建议加强</div>
                <el-tag
                  v-for="r in overview.weakModules"
                  :key="r.key"
                  class="mini-tag"
                  type="warning"
                  effect="plain"
                >
                  {{ r.label }} {{ r.percent }}%
                </el-tag>
                <span v-if="!overview.weakModules.length" class="empty-hint">暂无薄弱项，保持节奏即可</span>
              </div>
            </div>
          </el-col>

          <el-col :xs="24" :md="10">
            <h3 class="section-title">全部模块</h3>
            <el-scrollbar max-height="420px">
              <div
                v-for="row in overview.rows"
                :key="row.key"
                class="list-row"
                role="button"
                tabindex="0"
                @click="goModule(row.key)"
                @keydown.enter.prevent="goModule(row.key)"
              >
                <span class="list-name">{{ row.label }}</span>
                <el-progress
                  v-if="row.hasProgressData"
                  :percentage="row.percent"
                  :stroke-width="4"
                  :show-text="false"
                  style="width: 80px"
                  :color="row.accent"
                />
                <span v-else class="list-muted">{{ row.available ? '未开始' : '规划中' }}</span>
              </div>
            </el-scrollbar>
          </el-col>
        </el-row>
        <RecommendedResourcesPanel v-if="isLoggedIn" class="overview-rec" />
      </el-tab-pane>

      <el-tab-pane label="效果评估" name="evaluation">
        <LearningEvaluationPanel />
      </el-tab-pane>

      <el-tab-pane label="收藏" name="favorites">
        <div v-if="favoriteRows.length" class="module-grid">
          <div
            v-for="row in favoriteRows"
            :key="row.key"
            class="module-card hover-card"
          >
            <div class="card-top">
              <span class="card-name" :style="{ color: row.accent }">{{ row.label }}</span>
              <el-button
                text
                :icon="StarFilled"
                @click.stop="onToggleFavorite(row.key)"
              />
            </div>
            <p class="card-desc">
              {{ MODULE_PATH_HINTS[row.key]?.summary ?? '算法学习模块' }}
            </p>
            <el-button type="primary" size="small" @click="goModule(row.key)">进入学习</el-button>
          </div>
        </div>
        <el-empty v-else description="暂无收藏，在学习路径页可收藏模块" />
      </el-tab-pane>

      <el-tab-pane label="小游戏" name="games">
        <el-row :gutter="16" class="stats-row">
          <el-col :xs="12" :sm="8">
            <div class="stat-tile">
              <el-icon class="stat-icon"><Trophy /></el-icon>
              <strong>{{ gameOverview.totalLevelsCleared }}</strong>
              <span>已通关卡</span>
            </div>
          </el-col>
          <el-col :xs="12" :sm="8">
            <div class="stat-tile">
              <strong>{{ gameOverview.overallPercent }}%</strong>
              <span>小游戏总完成度</span>
            </div>
          </el-col>
        </el-row>

        <h3 class="section-title">各模块闯关</h3>
        <div v-if="gameOverview.rows.some((r) => r.cleared > 0)" class="module-grid">
          <div
            v-for="row in gameOverview.rows.filter((r) => r.cleared > 0)"
            :key="row.gameId"
            class="module-card"
          >
            <div class="card-top">
              <span class="card-name">{{ row.title }}</span>
              <el-tag size="small" type="success" effect="plain">
                {{ row.cleared }}/{{ row.total }}
              </el-tag>
            </div>
            <el-progress :percentage="row.percent" :stroke-width="6" :show-text="false" />
            <p class="card-meta">{{ row.moduleLabel }}</p>
            <el-button
              type="primary"
              size="small"
              @click="
                router.push({
                  name: 'module-game-play',
                  params: { gameId: row.gameId },
                  query: { from: 'my-learning' },
                })
              "
            >
              进入游戏
            </el-button>
          </div>
        </div>
        <el-empty v-else description="尚未通关任何小游戏，进入学习模块即可开始">
          <el-button type="primary" @click="router.push({ name: 'home' })">去学习</el-button>
        </el-empty>

        <h3 class="section-title">通关记录</h3>
        <div v-if="gameOverview.recentHistory.length" class="history-list">
          <div
            v-for="rec in gameOverview.recentHistory"
            :key="`${rec.gameId}-${rec.levelId}-${rec.clearedAt}`"
            class="history-item"
          >
            <div>
              <span class="history-title">{{ rec.gameTitle }} · {{ rec.levelTitle }}</span>
              <span class="history-time">{{ formatVisitTime(rec.clearedAt) }}</span>
            </div>
            <el-tag size="small" effect="plain">{{ rec.moduleKey === '_global' ? '毕业挑战' : rec.moduleKey }}</el-tag>
          </div>
        </div>
        <el-empty v-else description="通关后会显示在这里（登录账号自动云端保存）" />
      </el-tab-pane>

      <el-tab-pane label="最近学习" name="history">
        <div v-if="recentVisits.length" class="history-list">
          <div
            v-for="visit in recentVisits"
            :key="`${visit.moduleKey}-${visit.visitedAt}`"
            class="history-item"
            role="button"
            tabindex="0"
            @click="openRecent(visit)"
            @keydown.enter.prevent="openRecent(visit)"
          >
            <div>
              <span class="history-title">{{ visit.label }}</span>
              <span class="history-time">{{ formatVisitTime(visit.visitedAt) }}</span>
            </div>
            <el-button text type="primary" size="small">继续</el-button>
          </div>
        </div>
        <el-empty v-else description="暂无访问记录，进入任意学习模块后将自动记录" />
      </el-tab-pane>

      <el-tab-pane label="学习画像" name="persona">
        <el-alert
          v-if="!isLoggedIn"
          type="warning"
          show-icon
          :closable="false"
          class="persona-login-alert"
        >
          登录后可使用流式画像对话，并将 JSON 画像写入数据库
          <el-button type="primary" link @click="router.push({ name: 'login' })">去登录</el-button>
        </el-alert>
        <PersonaChatPanel v-else />
        <div v-if="isLoggedIn" class="persona-viz">
          <h3 class="section-title">模块掌握概览</h3>
          <LearningModuleRadar :rows="overview.rows" />
        </div>
        <div v-if="isLoggedIn" class="persona-hints">
          <span class="muted">本地进度参考：</span>
          <el-tag
            v-for="r in overview.weakModules.slice(0, 3)"
            :key="r.key"
            type="warning"
            effect="plain"
            size="small"
          >
            待加强：{{ r.label }}
          </el-tag>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<style scoped>
.page-card {
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
}

.muted {
  color: var(--alp-color-muted);
  line-height: 1.6;
  margin-bottom: 16px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 10px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  text-align: center;
}

.stat-icon {
  font-size: 20px;
  color: var(--alp-color-primary);
}

.stat-tile strong {
  font-size: 20px;
  color: var(--alp-color-text);
}

.stat-tile span {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.alert-block {
  margin-bottom: 12px;
}

.desc-block {
  margin-bottom: 16px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.learn-tabs {
  margin-top: 8px;
}

.viz-row {
  margin-bottom: 16px;
}

.viz-card {
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  height: 100%;
  margin-bottom: 12px;
}

.viz-title {
  margin-top: 0 !important;
}

.persona-viz {
  margin-top: 20px;
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.section-title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.section-title:not(:first-child) {
  margin-top: 24px;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 8px;
}

.module-card {
  padding: 14px 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition:
    transform var(--alp-transition-fast),
    border-color var(--alp-transition-fast),
    box-shadow var(--alp-transition-fast);
}

.module-card:hover,
.module-card:focus-visible {
  transform: translateY(-2px);
  border-color: rgba(56, 189, 248, 0.35);
  box-shadow: var(--alp-shadow-card-hover);
  outline: none;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.card-name {
  font-weight: 600;
  font-size: 15px;
}

.card-meta,
.card-desc {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.hover-card {
  /* alias */
}

.tag-groups {
  display: grid;
  gap: 14px;
}

.tag-label {
  font-size: 12px;
  color: var(--alp-color-muted);
  margin-bottom: 6px;
}

.mini-tag {
  margin: 0 6px 6px 0;
}

.empty-hint {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.list-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background var(--alp-transition-fast);
}

.list-row:hover,
.list-row:focus-visible {
  background: var(--alp-color-primary-soft);
  outline: none;
}

.list-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: var(--alp-color-text);
}

.list-muted {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition: background var(--alp-transition-fast);
}

.history-item:hover,
.history-item:focus-visible {
  background: var(--alp-color-primary-soft);
  outline: none;
}

.history-title {
  display: block;
  font-weight: 600;
  color: var(--alp-color-text);
}

.history-time {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.persona-login-alert {
  margin-bottom: 12px;
}

.persona-hints {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.persona-card {
  background: var(--alp-bg-persona);
  border: 1px solid var(--alp-border-persona);
  border-radius: var(--alp-radius-card);
}

.card-kicker {
  font-size: 12px;
  color: var(--alp-color-primary);
  font-weight: 600;
  letter-spacing: 0.06em;
}

.persona-title {
  margin: 6px 0 8px;
  font-size: 20px;
  color: var(--alp-color-text);
}

.persona-desc {
  margin: 0 0 12px;
  color: var(--alp-color-muted);
  line-height: 1.6;
  font-size: 14px;
}

.persona-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.persona-input {
  margin-bottom: 12px;
}
</style>
