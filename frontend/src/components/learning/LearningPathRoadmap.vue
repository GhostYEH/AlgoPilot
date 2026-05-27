<script setup lang="ts">

import { computed, onMounted, ref, watch } from 'vue'

import { Check, Lock, ArrowRight, Star, StarFilled, Guide } from '@element-plus/icons-vue'

import { MODULE_PHASE_LABELS, type ModulePhase } from '@/constants/modules'

import { MODULE_PHASE_GOALS, MODULE_PATH_HINTS } from '@/constants/modulePathHints'

import { buildLearningOverview, phaseLabel } from '@/utils/learningOverview'

import { loadFavoriteKeys, toggleFavorite } from '@/utils/learningBookmarks'

import { useModuleNavigation } from '@/composables/useModuleNavigation'

import { useLearningPathPlan, sortRowsByPlan } from '@/composables/useLearningPathPlan'

import { isLoggedIn } from '@/stores/auth'

import { fetchPersonaProfile, type PersonaProfile } from '@/api/orchestrator'

import LearningPathDagViz, {
  type DagEdgeDatum,
  type DagNodeDatum,
} from '@/components/learning/LearningPathDagViz.vue'

/** 模块 key → 画像维度（用于 DAG 节点着色） */
const MODULE_DIMENSION: Record<string, keyof PersonaProfile['dimensions']> = {
  array: 'knowledge_base',
  'linked-list': 'knowledge_base',
  'hash-table': 'knowledge_base',
  string: 'knowledge_base',
  'two-pointers': 'cognitive_style',
  'stack-queue': 'cognitive_style',
  'binary-tree': 'coding_ability',
  backtracking: 'coding_ability',
  greedy: 'coding_ability',
  dp: 'coding_ability',
  'monotonic-stack': 'error_preference',
  graph: 'learning_goals',
}



const props = defineProps<{

  highlightKey?: string

}>()



const emit = defineEmits<{

  replan: []

}>()



const { goModule } = useModuleNavigation()

const { plan, hasPlan, stepMap, recommendedNext, loadPlan, replan, loading } = useLearningPathPlan()



const overview = computed(() => buildLearningOverview())

const selectedKey = ref(props.highlightKey ?? overview.value.nextModule?.key ?? 'array')

const favRevision = ref(0)

const personaScores = ref<Record<string, number>>({})



onMounted(() => {

  if (isLoggedIn.value) {

    void fetchPersonaProfile()

      .then((p) => {

        personaScores.value = p.dimension_scores ?? {}

      })

      .catch(() => {

        personaScores.value = {}

      })

  }

  void loadPlan().then(() => {

    if (plan.value?.next_module_key) {

      selectedKey.value = props.highlightKey ?? plan.value.next_module_key

    }

  })

})



function scoreForModule(key: string): number {

  const dim = MODULE_DIMENSION[key]

  if (dim && personaScores.value[dim] != null) return personaScores.value[dim]

  const row = overview.value.rows.find((r) => r.key === key)

  if (row?.percent != null) return Math.max(2, Math.round(row.percent / 10))

  return 5

}



const dagNodes = computed((): DagNodeDatum[] => {

  const steps = plan.value?.steps ?? []

  if (!steps.length) {

    return overview.value.rows

      .filter((r) => r.available)

      .slice(0, 8)

      .map((r, i) => ({

        id: r.key,

        label: r.label,

        score: scoreForModule(r.key),

        rank: i + 1,

        isNext: r.key === plan.value?.next_module_key,

      }))

  }

  return steps.map((s) => ({

    id: s.module_key,

    label: overview.value.rows.find((r) => r.key === s.module_key)?.label ?? s.module_key,

    score: scoreForModule(s.module_key),

    isRemediation: !!s.is_remediation,

    isNext: s.module_key === plan.value?.next_module_key,

    rank: s.rank,

  }))

})



const dagEdges = computed((): DagEdgeDatum[] => {

  const edges: DagEdgeDatum[] = []

  for (const s of plan.value?.steps ?? []) {

    for (const dep of s.prerequisites ?? []) {

      edges.push({ source: dep, target: s.module_key })

    }

  }

  if (!edges.length && dagNodes.value.length > 1) {

    for (let i = 0; i < dagNodes.value.length - 1; i++) {

      edges.push({ source: dagNodes.value[i].id, target: dagNodes.value[i + 1].id })

    }

  }

  return edges

})



const remediationAnchorId = computed(() => {

  const rem = remediationStep.value

  if (!rem) return null

  return rem.prerequisites?.[0] ?? null

})



watch(

  () => props.highlightKey,

  (key) => {

    if (key) selectedKey.value = key

  },

)



watch(recommendedNext, (mod) => {

  if (!props.highlightKey && mod && hasPlan.value) {

    selectedKey.value = mod.key

  }

})



const selectedRow = computed(() =>

  overview.value.rows.find((r) => r.key === selectedKey.value),

)



const selectedHint = computed(() => MODULE_PATH_HINTS[selectedKey.value])

const selectedStepReason = computed(() => stepMap.value.get(selectedKey.value)?.reason)



const phases = computed(() => {

  const order: ModulePhase[] = ['foundation', 'technique', 'tree', 'advanced']

  const keys = plan.value?.ordered_keys ?? []

  return order.map((phase) => {

    const rows = overview.value.rows.filter((r) => r.phase === phase)

    const modules = keys.length ? sortRowsByPlan(rows, keys) : rows

    return {

      phase,

      label: MODULE_PHASE_LABELS[phase],

      goal: MODULE_PHASE_GOALS[phase],

      modules,

    }

  })

})



const orderedStepsPreview = computed(() => {

  if (!plan.value?.steps?.length) return []

  return [...plan.value.steps].sort((a, b) => a.rank - b.rank).slice(0, 8)

})



const remediationStep = computed(

  () => plan.value?.steps?.find((s) => s.is_remediation) ?? null,

)



const nextLabel = computed(() => {

  const key = plan.value?.next_module_key ?? recommendedNext.value?.key

  if (!key) return ''

  return overview.value.rows.find((r) => r.key === key)?.label ?? key

})



function selectModule(key: string) {

  selectedKey.value = key

}



function statusFor(key: string, available: boolean): string {

  const row = overview.value.rows.find((r) => r.key === key)

  if (!row) return 'idle'

  if (key === selectedKey.value) return 'active'

  if (!available) return 'planned'

  if (row.percent === 100) return 'done'

  if (row.percent > 0) return 'in-progress'

  return 'idle'

}



function rankFor(key: string): number | null {

  const step = stepMap.value.get(key)

  return step?.rank ?? null

}



const favSet = computed(() => {

  void favRevision.value

  return new Set(loadFavoriteKeys())

})



function onToggleFavorite(key: string) {

  toggleFavorite(key)

  favRevision.value += 1

}



async function onReplan() {

  emit('replan')

  await replan()

}

</script>



<template>

  <div class="roadmap">

    <el-alert

      v-if="hasPlan"

      type="success"

      :closable="false"

      show-icon

      class="agent-banner"

    >

      <template #title>

        <span class="agent-banner-title">{{ plan?.agent_name }} · 已个性化重排</span>

      </template>

      <p class="agent-banner-summary">{{ plan?.summary }}</p>

      <p v-if="plan?.rationale" class="agent-banner-rationale">{{ plan.rationale }}</p>

    </el-alert>



    <el-alert

      v-if="plan?.remediation_inserted && remediationStep"

      type="warning"

      :closable="false"

      show-icon

      class="agent-banner remediation-banner"

    >

      <template #title>🚑 EvaluatorAgent → PlannerAgent 学情降级</template>

      检测到连续作答受挫，已临时插播巩固关卡「{{ overview.rows.find((r) => r.key === remediationStep?.module_key)?.label ?? remediationStep?.module_key }}」：{{ remediationStep?.reason }}

    </el-alert>



    <el-alert

      v-else-if="isLoggedIn"

      type="info"

      :closable="false"

      show-icon

      class="agent-banner"

    >

      <template #title>学习路径 Agent</template>

      登录后可根据学习画像与进度自动重排模块顺序。

      <el-button type="primary" size="small" :loading="loading" class="banner-btn" @click="onReplan">

        生成个性化路径

      </el-button>

    </el-alert>



    <div v-if="orderedStepsPreview.length" class="steps-preview">

      <span class="steps-label"><el-icon><Guide /></el-icon> 推荐顺序</span>

      <el-tag

        v-for="s in orderedStepsPreview"

        :key="s.module_key"

        size="small"

        effect="plain"

        class="step-tag"

        :type="s.module_key === plan?.next_module_key ? 'primary' : 'info'"

      >

        {{ s.rank }}. {{ overview.rows.find((r) => r.key === s.module_key)?.label ?? s.module_key }}

        <span v-if="s.difficulty" class="step-diff">· {{ s.difficulty }}</span>

        <span v-if="s.is_remediation" class="step-rem">巩固</span>

      </el-tag>

    </div>



    <section v-if="dagNodes.length" class="dag-canvas-section">

      <span class="steps-label">个性化路径图谱 · 随画像动态演化</span>

      <LearningPathDagViz

        :key="`${plan?.updated_at ?? 'default'}-${plan?.remediation_inserted ? 'rem' : 'base'}`"

        :nodes="dagNodes"

        :edges="dagEdges"

        :remediation-anchor-id="remediationAnchorId"

        :height="300"

      />

    </section>



    <div class="overview-strip">

      <div class="stat-card">

        <span class="stat-label">路径总进度</span>

        <strong class="stat-value">{{ overview.overallPercent }}%</strong>

        <el-progress

          :percentage="overview.overallPercent"

          :stroke-width="8"

          :show-text="false"

          striped

        />

      </div>

      <div class="stat-card">

        <span class="stat-label">已跟踪模块</span>

        <strong class="stat-value">{{ overview.trackedModules }}</strong>

        <span class="stat-sub">已完成 {{ overview.completedModules }} 个</span>

      </div>

      <div class="stat-card stat-card--accent" v-if="nextLabel">

        <span class="stat-label">{{ hasPlan ? '路径 Agent 建议' : '建议下一步' }}</span>

        <strong class="stat-value stat-value--sm">{{ nextLabel }}</strong>

        <el-button

          type="primary"

          size="small"

          text

          bg

          @click="goModule(plan?.next_module_key ?? recommendedNext?.key ?? 'array')"

        >

          继续学习

          <el-icon class="el-icon--right"><ArrowRight /></el-icon>

        </el-button>

      </div>

      <div v-if="isLoggedIn && hasPlan" class="stat-card stat-card--action">

        <el-button type="primary" plain :loading="loading" @click="onReplan">重新规划路径</el-button>

      </div>

    </div>



    <div class="roadmap-body">

      <div class="timeline-panel">

        <section

          v-for="block in phases"

          :key="block.phase"

          class="phase-block"

        >

          <header class="phase-header">

            <h3 class="phase-title">{{ block.label }}</h3>

            <p class="phase-goal">{{ block.goal }}</p>

          </header>



          <ol class="node-list">

            <li

              v-for="(row, idx) in block.modules"

              :key="row.key"

              class="node-item"

            >

              <div v-if="idx > 0" class="node-connector" aria-hidden="true" />



              <button

                type="button"

                class="path-node"

                :class="[`status-${statusFor(row.key, row.available)}`]"

                :style="{ '--node-accent': row.accent }"

                :aria-current="row.key === selectedKey ? 'step' : undefined"

                @click="selectModule(row.key)"

              >

                <span v-if="rankFor(row.key)" class="node-rank">{{ rankFor(row.key) }}</span>

                <span class="node-ring">

                  <svg

                    v-if="row.hasProgressData"

                    class="progress-ring"

                    viewBox="0 0 36 36"

                    aria-hidden="true"

                  >

                    <circle class="ring-bg" cx="18" cy="18" r="15.5" pathLength="100" />

                    <circle

                      class="ring-fg"

                      cx="18"

                      cy="18"

                      r="15.5"

                      pathLength="100"

                      :stroke-dasharray="`${row.percent} 100`"

                    />

                  </svg>

                </span>

                <span class="node-core">

                  <el-icon v-if="statusFor(row.key, row.available) === 'done'" class="node-icon">

                    <Check />

                  </el-icon>

                  <el-icon

                    v-else-if="!row.available"

                    class="node-icon node-icon--muted"

                  >

                    <Lock />

                  </el-icon>

                  <span v-else class="node-glyph">{{ row.label.charAt(0) }}</span>

                </span>

              </button>



              <div class="node-info">

                <button

                  type="button"

                  class="node-title-btn"

                  @click="selectModule(row.key)"

                >

                  {{ row.label }}

                </button>

                <span v-if="stepMap.get(row.key)?.reason" class="node-reason">

                  {{ stepMap.get(row.key)?.reason }}

                </span>

                <span v-if="row.hasProgressData" class="node-pct">{{ row.percent }}%</span>

                <span v-else-if="!row.available" class="node-pct node-pct--muted">规划中</span>

                <span v-else class="node-pct node-pct--muted">未开始</span>

              </div>

            </li>

          </ol>

        </section>

      </div>



      <aside class="detail-panel">

        <template v-if="selectedRow">

          <div class="detail-head">

            <h3 class="detail-title" :style="{ color: selectedRow.accent }">

              {{ selectedRow.label }}

            </h3>

            <el-tag v-if="rankFor(selectedRow.key)" size="small" type="primary" effect="plain">

              路径第 {{ rankFor(selectedRow.key) }} 步

            </el-tag>

            <el-tag size="small" effect="plain">{{ phaseLabel(selectedRow.phase) }}</el-tag>

          </div>



          <p v-if="selectedStepReason" class="detail-agent-reason">

            <strong>路径 Agent：</strong>{{ selectedStepReason }}

          </p>



          <p v-if="selectedHint" class="detail-summary">{{ selectedHint.summary }}</p>



          <div v-if="selectedRow.hasProgressData" class="detail-progress">

            <div class="progress-row">

              <span>小节完成</span>

              <strong>{{ selectedRow.doneCount }} / {{ selectedRow.totalCount }}</strong>

            </div>

            <el-progress

              :percentage="selectedRow.percent"

              :stroke-width="10"

              :color="selectedRow.accent"

            />

          </div>



          <ul v-if="selectedHint?.goals.length" class="goal-list">

            <li v-for="(g, i) in selectedHint.goals" :key="i">{{ g }}</li>

          </ul>



          <p v-if="selectedHint" class="est-hours">

            预估学习 {{ selectedHint.estHours }} 小时

          </p>



          <div class="detail-actions">

            <el-button

              v-if="selectedRow.available"

              type="primary"

              @click="goModule(selectedRow.key)"

            >

              {{ selectedRow.percent > 0 ? '继续学习' : '开始学习' }}

            </el-button>

            <el-button v-else disabled>内容规划中</el-button>

            <el-button

              :icon="favSet.has(selectedRow.key) ? StarFilled : Star"

              @click="onToggleFavorite(selectedRow.key)"

            >

              {{ favSet.has(selectedRow.key) ? '已收藏' : '收藏' }}

            </el-button>

          </div>

        </template>

      </aside>

    </div>

  </div>

</template>



<style scoped>

.roadmap {

  display: flex;

  flex-direction: column;

  gap: 20px;

}



.agent-banner {

  margin-bottom: 0;

}



.agent-banner-title {

  font-weight: 600;

}



.agent-banner-summary {

  margin: 6px 0 0;

  font-size: 13px;

  line-height: 1.5;

}



.agent-banner-rationale {

  margin: 4px 0 0;

  font-size: 12px;

  color: var(--alp-color-muted);

  line-height: 1.55;

}



.banner-btn {

  margin-top: 8px;

}



.steps-preview {

  display: flex;

  flex-wrap: wrap;

  align-items: center;

  gap: 8px;

  padding: 10px 12px;

  border-radius: var(--alp-radius-card);

  background: var(--alp-bg-soft-block);

  border: 1px solid var(--alp-color-border);

}

.dag-canvas-section {

  display: flex;

  flex-direction: column;

  gap: 10px;

  margin-top: 4px;

}

.step-diff {

  opacity: 0.75;

  font-size: 10px;

}

.step-rem {

  margin-left: 4px;

  font-size: 10px;

  color: #d97706;

  font-weight: 600;

}

.remediation-banner {

  margin-top: 8px;

}



.steps-label {

  display: flex;

  align-items: center;

  gap: 4px;

  font-size: 12px;

  font-weight: 600;

  color: var(--alp-color-primary);

}



.step-tag {

  cursor: default;

}



.overview-strip {

  display: grid;

  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));

  gap: 14px;

}



.stat-card {

  padding: 14px 16px;

  border-radius: var(--alp-radius-card);

  background: var(--alp-bg-soft-block);

  border: 1px solid var(--alp-color-border);

}



.stat-card--accent {

  border-color: rgba(56, 189, 248, 0.35);

  background: var(--alp-color-primary-soft);

}



.stat-card--action {

  display: flex;

  align-items: center;

  justify-content: center;

}



.stat-label {

  display: block;

  font-size: 12px;

  color: var(--alp-color-muted);

  margin-bottom: 4px;

}



.stat-value {

  font-size: 22px;

  color: var(--alp-color-text);

}



.stat-value--sm {

  font-size: 16px;

  display: block;

  margin-bottom: 8px;

}



.stat-sub {

  display: block;

  margin-top: 6px;

  font-size: 12px;

  color: var(--alp-color-muted);

}



.roadmap-body {

  display: grid;

  grid-template-columns: 1fr minmax(280px, 340px);

  gap: 20px;

  align-items: start;

}



.timeline-panel {

  padding: 16px;

  border-radius: var(--alp-radius-card);

  background: var(--alp-bg-soft-block);

  border: 1px solid var(--alp-color-border);

}



.phase-block + .phase-block {

  margin-top: 24px;

  padding-top: 20px;

  border-top: 1px dashed var(--alp-color-border);

}



.phase-header {

  margin-bottom: 14px;

}



.phase-title {

  margin: 0 0 4px;

  font-size: 15px;

  font-weight: 600;

  color: var(--alp-color-text);

}



.phase-goal {

  margin: 0;

  font-size: 12px;

  color: var(--alp-color-muted);

  line-height: 1.5;

}



.node-list {

  list-style: none;

  margin: 0;

  padding: 0;

  display: flex;

  flex-wrap: wrap;

  gap: 8px 12px;

}



.node-item {

  position: relative;

  display: flex;

  flex-direction: column;

  align-items: center;

  width: 96px;

}



.node-connector {

  display: none;

}



.path-node {

  position: relative;

  width: 44px;

  height: 44px;

  padding: 0;

  border: none;

  background: transparent;

  cursor: pointer;

  border-radius: 50%;

  transition: transform var(--alp-transition-fast);

}



.path-node:hover {

  transform: scale(1.06);

}



.node-rank {

  position: absolute;

  top: -6px;

  right: -6px;

  z-index: 2;

  min-width: 16px;

  height: 16px;

  padding: 0 4px;

  border-radius: 8px;

  background: var(--alp-color-primary);

  color: #fff;

  font-size: 10px;

  font-weight: 700;

  line-height: 16px;

  text-align: center;

}



.node-ring {

  position: absolute;

  inset: 0;

  border-radius: 50%;

  background: var(--alp-bg-surface-solid);

  border: 2px solid rgba(148, 163, 184, 0.35);

  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);

}



.progress-ring {

  position: absolute;

  inset: -2px;

  width: calc(100% + 4px);

  height: calc(100% + 4px);

  transform: rotate(-90deg);

}



.ring-bg {

  fill: none;

  stroke: rgba(148, 163, 184, 0.2);

  stroke-width: 2.5;

}



.ring-fg {

  fill: none;

  stroke: var(--node-accent, var(--alp-color-primary));

  stroke-width: 2.5;

  stroke-linecap: round;

}



.node-core {

  position: relative;

  z-index: 1;

  display: flex;

  align-items: center;

  justify-content: center;

  width: 30px;

  height: 30px;

  margin: 7px auto 0;

  border-radius: 50%;

  background: rgba(15, 23, 42, 0.9);

}



.node-glyph {

  font-size: 13px;

  font-weight: 700;

  color: var(--node-accent, var(--alp-color-primary));

}



.node-icon {

  font-size: 16px;

  color: #4ade80;

}



.node-icon--muted {

  color: var(--alp-color-muted);

  font-size: 14px;

}



.node-info {

  margin-top: 6px;

  text-align: center;

  min-width: 0;

}



.node-title-btn {

  display: block;

  width: 100%;

  padding: 0;

  border: none;

  background: none;

  font-size: 12px;

  font-weight: 600;

  color: var(--alp-color-text);

  cursor: pointer;

  line-height: 1.3;

}



.node-reason {

  display: block;

  font-size: 10px;

  color: var(--alp-color-muted);

  line-height: 1.3;

  margin: 2px 0;

}



.node-title-btn:hover {

  color: var(--alp-color-primary);

}



.node-pct {

  display: block;

  font-size: 10px;

  color: var(--node-accent, var(--alp-color-primary));

  font-variant-numeric: tabular-nums;

}



.node-pct--muted {

  color: var(--alp-color-muted);

}



.status-active .node-ring {

  border-color: var(--node-accent, var(--alp-color-primary));

  box-shadow: 0 0 0 3px color-mix(in srgb, var(--node-accent, #38bdf8) 22%, transparent);

}



.status-planned .node-ring {

  border-style: dashed;

  opacity: 0.85;

}



.detail-panel {

  padding: 18px;

  border-radius: var(--alp-radius-card);

  background: var(--alp-bg-surface);

  border: 1px solid var(--alp-color-border);

  position: sticky;

  top: 12px;

}



.detail-head {

  display: flex;

  align-items: center;

  flex-wrap: wrap;

  gap: 8px;

  margin-bottom: 12px;

}



.detail-title {

  margin: 0;

  font-size: 18px;

  flex: 1;

  min-width: 120px;

}



.detail-agent-reason {

  margin: 0 0 12px;

  padding: 8px 10px;

  border-radius: 8px;

  background: var(--alp-color-primary-soft);

  font-size: 12px;

  line-height: 1.5;

  color: var(--alp-color-text);

}



.detail-summary {

  margin: 0 0 14px;

  font-size: 13px;

  color: var(--alp-color-muted);

  line-height: 1.6;

}



.detail-progress {

  margin-bottom: 14px;

}



.progress-row {

  display: flex;

  justify-content: space-between;

  font-size: 12px;

  color: var(--alp-color-muted);

  margin-bottom: 6px;

}



.goal-list {

  margin: 0 0 12px;

  padding-left: 18px;

  font-size: 13px;

  color: var(--alp-color-text);

  line-height: 1.7;

}



.est-hours {

  margin: 0 0 16px;

  font-size: 12px;

  color: var(--alp-color-muted);

}



.detail-actions {

  display: flex;

  flex-wrap: wrap;

  gap: 8px;

}



@media (max-width: 900px) {

  .roadmap-body {

    grid-template-columns: 1fr;

  }



  .detail-panel {

    position: static;

  }

}

</style>


