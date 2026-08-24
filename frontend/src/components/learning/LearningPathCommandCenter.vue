<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Aim,
  ArrowRight,
  ChatDotRound,
  Check,
  Clock,
  Collection,
  Filter,
  Lock,
  Refresh,
  Search,
  TrendCharts,
  VideoPlay,
} from '@element-plus/icons-vue'

import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'
import ConceptKnowledgeGraph from '@/components/learning/ConceptKnowledgeGraph.vue'
import RecommendedResourcesPanel from '@/components/learning/RecommendedResourcesPanel.vue'
import { getConceptsForModule } from '@/constants/conceptGraph'
import { MODULE_PATH_HINTS } from '@/constants/modulePathHints'
import {
  ALGORITHM_MODULES,
  MODULE_PHASE_LABELS,
  type ModulePhase,
} from '@/constants/modules'
import { useLearningPathPlan } from '@/composables/useLearningPathPlan'
import { useModuleNavigation } from '@/composables/useModuleNavigation'
import { getModuleLearnConfig } from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { isLoggedIn } from '@/stores/auth'
import { buildLearningOverview, type ModuleProgressRow } from '@/utils/learningOverview'

type StatusFilter = 'all' | 'mastered' | 'progress' | 'not-started'

const FALLBACK_MODULE_PREREQUISITES: Record<string, string[]> = {
  'linked-list': ['array'],
  'hash-table': ['array'],
  string: ['array'],
  'two-pointers': ['array', 'linked-list'],
  'stack-queue': ['array', 'linked-list'],
  sorting: ['array'],
  'binary-tree': ['stack-queue'],
  backtracking: ['binary-tree'],
  greedy: ['array', 'sorting'],
  dp: ['array'],
  'monotonic-stack': ['stack-queue'],
  graph: ['binary-tree', 'stack-queue'],
}

const props = defineProps<{
  highlightKey?: string
}>()

const emit = defineEmits<{
  replan: []
}>()

const router = useRouter()
const { goModule } = useModuleNavigation()
const { plan, stepMap, replan, loading } = useLearningPathPlan()
const overview = computed(() => buildLearningOverview())

const query = ref('')
const statusFilter = ref<StatusFilter>('all')
const phaseFilter = ref<'all' | ModulePhase>('all')
const onlyMyPath = ref(true)
const selectedKey = ref(props.highlightKey ?? plan.value?.next_module_key ?? overview.value.nextModule?.key ?? 'array')
const aiVisible = ref(false)

watch(
  () => props.highlightKey,
  (value) => {
    if (value) selectedKey.value = value
  },
)

watch(
  () => plan.value?.next_module_key,
  (value) => {
    if (!props.highlightKey && value) selectedKey.value = value
  },
  { immediate: true },
)

const orderedRows = computed(() => {
  const byKey = new Map(overview.value.rows.map((row) => [row.key, row]))
  const preferred = plan.value?.ordered_keys?.length
    ? plan.value.ordered_keys
    : ALGORITHM_MODULES.map((module) => module.key)
  const keys = [...new Set([...preferred, ...ALGORITHM_MODULES.map((module) => module.key)])]
  return keys.map((key) => byKey.get(key)).filter((row): row is ModuleProgressRow => !!row)
})

const effectiveNextKey = computed(
  () => plan.value?.next_module_key ?? overview.value.nextModule?.key ?? orderedRows.value[0]?.key,
)

function statusOf(row: ModuleProgressRow): Exclude<StatusFilter, 'all'> {
  if (row.percent >= 100) return 'mastered'
  if (row.percent > 0 || row.key === effectiveNextKey.value) return 'progress'
  return 'not-started'
}

function statusLabel(row: ModuleProgressRow) {
  const status = statusOf(row)
  if (status === 'mastered') return '已掌握'
  if (status === 'progress') return row.percent > 0 ? `进行中 ${row.percent}%` : '建议下一步'
  return '未开始'
}

const filteredRows = computed(() => {
  const needle = query.value.trim().toLowerCase()
  const pathKeys = new Set(plan.value?.ordered_keys ?? [])
  return orderedRows.value.filter((row) => {
    if (onlyMyPath.value && pathKeys.size && !pathKeys.has(row.key)) return false
    if (phaseFilter.value !== 'all' && row.phase !== phaseFilter.value) return false
    if (statusFilter.value !== 'all' && statusOf(row) !== statusFilter.value) return false
    if (needle && !`${row.label} ${row.key}`.toLowerCase().includes(needle)) return false
    return true
  })
})

const groupedRows = computed(() => {
  const phases: ModulePhase[] = ['foundation', 'technique', 'tree', 'advanced']
  return phases
    .map((phase) => ({
      phase,
      label: MODULE_PHASE_LABELS[phase],
      rows: filteredRows.value.filter((row) => row.phase === phase),
      hours: filteredRows.value
        .filter((row) => row.phase === phase)
        .reduce((sum, row) => sum + (MODULE_PATH_HINTS[row.key]?.estHours ?? 0), 0),
    }))
    .filter((group) => group.rows.length)
})

const selectedRow = computed(
  () => overview.value.rows.find((row) => row.key === selectedKey.value) ?? overview.value.rows[0],
)
const selectedHint = computed(() => MODULE_PATH_HINTS[selectedKey.value])
const selectedStep = computed(() => stepMap.value.get(selectedKey.value))
const selectedConceptIds = computed(() =>
  getConceptsForModule(selectedKey.value).map((concept) => concept.id),
)
const tutorSection = computed<LearnSection>(() => {
  const configured = getModuleLearnConfig(selectedKey.value)?.sections[0]
  if (configured) return configured
  const hint = selectedHint.value
  return {
    id: `${selectedKey.value}-path-overview`,
    title: `${selectedRow.value?.label ?? ''}学习路径`,
    subtitle: hint?.summary ?? '',
    difficulty: '基础',
    estMinutes: Math.max(30, (hint?.estHours ?? 1) * 60),
    keywords: getConceptsForModule(selectedKey.value).map((concept) => concept.label),
    overview: hint?.summary,
    points: hint?.goals ?? [],
  }
})
const completedCount = computed(() => overview.value.rows.filter((row) => row.percent >= 100).length)
const inProgressCount = computed(() => overview.value.rows.filter((row) => statusOf(row) === 'progress').length)
const totalHours = computed(() =>
  filteredRows.value.reduce((sum, row) => sum + (MODULE_PATH_HINTS[row.key]?.estHours ?? 0), 0),
)
const selectedRank = computed(() => {
  const index = (plan.value?.ordered_keys ?? orderedRows.value.map((row) => row.key)).indexOf(selectedKey.value)
  return index >= 0 ? index + 1 : 1
})

const prerequisiteRows = computed(() =>
  (selectedStep.value?.prerequisites ?? FALLBACK_MODULE_PREREQUISITES[selectedKey.value] ?? [])
    .map((key) => overview.value.rows.find((row) => row.key === key))
    .filter((row): row is ModuleProgressRow => !!row),
)

const downstreamRows = computed(() =>
  overview.value.rows
    .filter((row) => {
      const plannedPrerequisites = stepMap.value.get(row.key)?.prerequisites
      const prerequisites = plannedPrerequisites ?? FALLBACK_MODULE_PREREQUISITES[row.key] ?? []
      return prerequisites.includes(selectedKey.value)
    })
    .filter((row): row is ModuleProgressRow => !!row),
)

function selectModule(key: string) {
  selectedKey.value = key
}

function resetFilters() {
  query.value = ''
  statusFilter.value = 'all'
  phaseFilter.value = 'all'
  onlyMyPath.value = true
}

async function handleReplan() {
  await replan({ trigger: 'universe', triggerLabel: '路径指挥台手动重排' })
  emit('replan')
}

function startPractice() {
  void router.push({ name: 'practice-list', query: { module: selectedKey.value } })
}
</script>

<template>
  <section class="command-center" aria-label="个性化学习路径指挥台">
    <header class="command-header">
      <div>
        <div class="title-line">
          <h2>路径指挥台</h2>
          <span class="recommendation-mark">个性化推荐</span>
        </div>
        <p>{{ plan?.summary || '根据学习进度与知识依赖，为你规划可执行的算法学习路径。' }}</p>
      </div>
      <div class="path-metrics" aria-label="路径概要">
        <div>
          <span>总进度</span>
          <strong>{{ overview.overallPercent }}%</strong>
        </div>
        <div class="metric-progress" aria-hidden="true">
          <i :style="{ width: `${overview.overallPercent}%` }" />
        </div>
        <div>
          <span>预计总时长</span>
          <strong>{{ totalHours }}h</strong>
        </div>
        <div>
          <span>已掌握</span>
          <strong>{{ completedCount }}/{{ overview.rows.length }}</strong>
        </div>
      </div>
    </header>

    <div class="command-toolbar">
      <el-input v-model="query" clearable class="search-control" placeholder="搜索模块或知识点">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="statusFilter" class="toolbar-select" aria-label="学习状态">
        <el-option label="全部状态" value="all" />
        <el-option label="已掌握" value="mastered" />
        <el-option label="进行中" value="progress" />
        <el-option label="未开始" value="not-started" />
      </el-select>
      <el-select v-model="phaseFilter" class="toolbar-select" aria-label="学习阶段">
        <el-option label="全部阶段" value="all" />
        <el-option v-for="(label, key) in MODULE_PHASE_LABELS" :key="key" :label="label" :value="key" />
      </el-select>
      <el-switch v-model="onlyMyPath" inline-prompt active-text="我的路径" inactive-text="全部模块" />
      <span class="toolbar-spacer" />
      <el-button :loading="loading" :disabled="!isLoggedIn" @click="handleReplan">
        <el-icon><Refresh /></el-icon>
        重新规划
      </el-button>
      <el-button text @click="resetFilters">重置筛选</el-button>
    </div>

    <div class="workspace-grid">
      <aside class="filter-rail">
        <div class="rail-label"><el-icon><Collection /></el-icon>我的视图</div>
        <button class="view-row is-active" type="button" @click="resetFilters">
          <el-icon><Aim /></el-icon>
          <span>主路径</span>
          <b>{{ filteredRows.length }}</b>
        </button>
        <button class="view-row" type="button" @click="statusFilter = 'progress'">
          <el-icon><TrendCharts /></el-icon>
          <span>正在学习</span>
          <b>{{ inProgressCount }}</b>
        </button>
        <div class="rail-divider" />
        <div class="rail-label"><el-icon><Filter /></el-icon>快速筛选</div>
        <button
          v-for="(label, key) in MODULE_PHASE_LABELS"
          :key="key"
          type="button"
          class="filter-row"
          :class="{ 'is-active': phaseFilter === key }"
          @click="phaseFilter = phaseFilter === key ? 'all' : key"
        >
          <span>{{ label }}</span>
          <b>{{ overview.rows.filter((row) => row.phase === key).length }}</b>
        </button>
        <div class="rail-note">
          <el-icon><Clock /></el-icon>
          当前筛选约需 <strong>{{ totalHours }} 小时</strong>
        </div>
      </aside>

      <main class="path-workspace">
        <div v-if="groupedRows.length" class="path-canvas">
          <section v-for="group in groupedRows" :key="group.phase" class="phase-lane">
            <header>
              <strong>{{ group.label }}</strong>
              <span>{{ group.rows.length }} 个模块 · {{ group.hours }}h</span>
            </header>
            <div class="lane-track">
              <template v-for="(row, index) in group.rows" :key="row.key">
                <button
                  type="button"
                  class="module-node"
                  :class="[
                    `is-${statusOf(row)}`,
                    { 'is-selected': row.key === selectedKey, 'is-next': row.key === effectiveNextKey },
                  ]"
                  @click="selectModule(row.key)"
                >
                  <span class="node-status" aria-hidden="true">
                    <el-icon v-if="statusOf(row) === 'mastered'"><Check /></el-icon>
                    <el-icon v-else-if="statusOf(row) === 'not-started'"><Lock /></el-icon>
                    <span v-else>{{ row.percent || selectedRank }}</span>
                  </span>
                  <span class="node-copy">
                    <strong>{{ row.label }}</strong>
                    <small>{{ statusLabel(row) }}</small>
                  </span>
                <span v-if="row.key === effectiveNextKey" class="next-badge">下一步</span>
                </button>
                <el-icon v-if="index < group.rows.length - 1" class="path-arrow"><ArrowRight /></el-icon>
              </template>
            </div>
          </section>
        </div>
        <el-empty v-else description="没有匹配的学习模块">
          <el-button @click="resetFilters">清除筛选</el-button>
        </el-empty>

        <section class="dependency-section">
          <div class="subsection-heading">
            <div>
              <h3>概念依赖图谱</h3>
              <p>查看「{{ selectedRow?.label }}」的概念、先修关系与关联题目。</p>
            </div>
            <span>{{ selectedConceptIds.length }} 个核心概念</span>
          </div>
          <ConceptKnowledgeGraph
            :module-key="selectedKey"
            :highlight-path-ids="selectedConceptIds"
            :navigate-on-click="false"
            height="350px"
          />
        </section>
      </main>

      <aside v-if="selectedRow" class="inspector-panel">
        <div class="inspector-topline">
          <span>{{ MODULE_PHASE_LABELS[selectedRow.phase] }}</span>
          <span>{{ statusLabel(selectedRow) }}</span>
        </div>
        <div class="inspector-title">
          <div class="inspector-icon"><el-icon><VideoPlay /></el-icon></div>
          <div>
            <h3>{{ selectedRow.label }}</h3>
            <p>路径第 {{ selectedRank }} 站 · 预计 {{ selectedHint?.estHours ?? 0 }} 小时</p>
          </div>
        </div>

        <section class="inspector-section">
          <h4>为什么学它</h4>
          <p>{{ selectedStep?.reason || selectedHint?.summary }}</p>
        </section>

        <section class="inspector-section">
          <h4>本模块目标</h4>
          <ul>
            <li v-for="goal in selectedHint?.goals ?? []" :key="goal">
              <el-icon><Check /></el-icon><span>{{ goal }}</span>
            </li>
          </ul>
        </section>

        <section class="inspector-section relation-summary">
          <h4>依赖关系</h4>
          <div>
            <span>先修知识</span>
            <button
              v-for="row in prerequisiteRows"
              :key="row.key"
              type="button"
              @click="selectModule(row.key)"
            >{{ row.label }} · {{ statusLabel(row) }}</button>
            <small v-if="!prerequisiteRows.length">这是当前路径的基础节点</small>
          </div>
          <div>
            <span>后续去向</span>
            <button
              v-for="row in downstreamRows"
              :key="row.key"
              type="button"
              @click="selectModule(row.key)"
            >{{ row.label }}</button>
            <small v-if="!downstreamRows.length">完成后将解锁更高阶模块</small>
          </div>
        </section>

        <section class="inspector-section evidence-block">
          <h4>掌握证据</h4>
          <div class="evidence-row">
            <strong>{{ selectedRow.doneCount }}/{{ selectedRow.totalCount || '—' }}</strong>
            <span>学习章节</span>
          </div>
          <div class="evidence-row">
            <strong>{{ selectedRow.percent }}%</strong>
            <span>当前进度</span>
          </div>
        </section>

        <RecommendedResourcesPanel
          v-if="isLoggedIn"
          :module-key="selectedKey"
          :limit="2"
          title="学习资源"
        />

        <div class="action-stack">
          <el-button type="primary" @click="goModule(selectedKey)">
            <el-icon><VideoPlay /></el-icon>
            {{ selectedRow.percent > 0 ? '继续学习' : '开始学习' }}
          </el-button>
          <el-button @click="startPractice">开始练习</el-button>
          <el-button @click="aiVisible = true">
            <el-icon><ChatDotRound /></el-icon>
            询问 AI
          </el-button>
        </div>
      </aside>
    </div>

    <el-drawer v-model="aiVisible" :title="`${selectedRow?.label ?? ''} · AI 学习助手`" size="min(520px, 94vw)">
      <AiTutorPanel
        v-if="selectedRow"
        :module-key="selectedKey"
        :module-title="selectedRow.label"
        chapter-tag="路径指挥台"
        :module-intro="selectedHint?.summary ?? ''"
        :section="tutorSection"
      />
    </el-drawer>
  </section>
</template>

<style scoped>
.command-center {
  color: var(--alp-color-text);
  background: var(--alp-bg-surface);
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-lg);
  overflow: hidden;
  scroll-margin-top: calc(var(--alp-header-height) + 12px);
}

.command-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 22px 18px;
  border-bottom: 1px solid var(--alp-color-border);
}

.title-line { display: flex; align-items: center; gap: 10px; }
.title-line h2 { margin: 0; font-size: 21px; font-weight: 720; }
.recommendation-mark { color: var(--alp-color-primary); font-size: 12px; font-weight: 650; }
.command-header p { margin: 5px 0 0; color: var(--alp-color-muted); font-size: 13px; }

.path-metrics { display: flex; align-items: center; gap: 22px; min-width: 430px; }
.path-metrics > div:not(.metric-progress) { display: grid; gap: 3px; }
.path-metrics span { color: var(--alp-color-muted); font-size: 11px; }
.path-metrics strong { font-size: 16px; font-variant-numeric: tabular-nums; }
.metric-progress { width: 110px; height: 5px; overflow: hidden; border-radius: 4px; background: var(--alp-bg-soft-block); }
.metric-progress i { display: block; height: 100%; border-radius: inherit; background: var(--alp-color-primary); }

.command-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-muted);
}
.search-control { width: min(320px, 28vw); }
.toolbar-select { width: 126px; }
.toolbar-spacer { flex: 1; }

.workspace-grid { display: grid; grid-template-columns: 190px minmax(0, 1fr) 320px; min-height: 720px; }
.filter-rail { padding: 16px 12px; border-right: 1px solid var(--alp-color-border); background: var(--alp-bg-aside-gradient); }
.rail-label { display: flex; align-items: center; gap: 7px; padding: 0 8px 8px; color: var(--alp-color-muted); font-size: 11px; font-weight: 650; }
.view-row, .filter-row {
  width: 100%; display: flex; align-items: center; gap: 9px; border: 0; border-radius: var(--alp-radius-sm);
  padding: 9px 10px; color: var(--alp-color-text-secondary); background: transparent; cursor: pointer; text-align: left;
}
.view-row span, .filter-row span { flex: 1; }
.view-row b, .filter-row b { color: var(--alp-color-muted); font-size: 11px; font-weight: 500; }
.view-row:hover, .filter-row:hover { background: var(--alp-bg-hover); color: var(--alp-color-text); }
.view-row.is-active, .filter-row.is-active { color: var(--alp-color-primary); background: var(--alp-color-primary-soft); font-weight: 650; }
.rail-divider { height: 1px; margin: 14px 8px; background: var(--alp-color-border); }
.rail-note { display: flex; flex-wrap: wrap; align-items: center; gap: 5px; margin: 18px 8px 0; color: var(--alp-color-muted); font-size: 11px; line-height: 1.5; }
.rail-note strong { color: var(--alp-color-text-secondary); }

.path-workspace { min-width: 0; padding: 16px; background: var(--alp-bg-main-panel); }
.path-canvas { border: 1px solid var(--alp-color-border); border-radius: var(--alp-radius-card); overflow: hidden; }
.phase-lane + .phase-lane { border-top: 1px solid var(--alp-color-border); }
.phase-lane > header { display: flex; justify-content: space-between; padding: 10px 14px; background: var(--alp-bg-surface-muted); }
.phase-lane > header strong { color: var(--alp-color-primary); font-size: 12px; }
.phase-lane > header span { color: var(--alp-color-muted); font-size: 11px; }
.lane-track { display: flex; align-items: center; gap: 8px; min-height: 104px; padding: 16px 18px; overflow-x: auto; }
.path-arrow { flex: 0 0 auto; color: var(--alp-color-muted); }
.module-node {
  position: relative; display: flex; align-items: center; gap: 9px; min-width: 150px; padding: 12px;
  border: 1px solid var(--alp-color-border-strong); border-radius: var(--alp-radius-card); color: var(--alp-color-text);
  background: var(--alp-bg-surface); cursor: pointer; text-align: left; transition: border-color .16s ease, box-shadow .16s ease;
}
.module-node:hover { border-color: var(--alp-color-primary); }
.module-node.is-selected { border-color: var(--alp-color-primary); box-shadow: var(--alp-shadow-glow); }
.module-node.is-mastered { border-color: color-mix(in srgb, var(--alp-color-success) 42%, var(--alp-color-border)); }
.module-node.is-not-started { color: var(--alp-color-text-secondary); background: var(--alp-bg-surface-muted); }
.node-status { display: grid; place-items: center; flex: 0 0 24px; height: 24px; border-radius: 50%; color: var(--alp-color-muted); background: var(--alp-bg-soft-block); font-size: 10px; }
.is-mastered .node-status { color: white; background: var(--alp-color-success); }
.is-progress .node-status { color: var(--alp-color-primary); border: 2px solid currentColor; background: transparent; }
.node-copy { display: grid; gap: 3px; }
.node-copy strong { font-size: 13px; }
.node-copy small { color: var(--alp-color-muted); font-size: 10px; }
.next-badge { position: absolute; top: -9px; right: 8px; padding: 2px 6px; border-radius: 3px; color: white; background: var(--alp-color-primary); font-size: 9px; font-weight: 700; }

.dependency-section { margin-top: 16px; }
.subsection-heading { display: flex; justify-content: space-between; align-items: end; gap: 14px; margin-bottom: 10px; }
.subsection-heading h3 { margin: 0; font-size: 16px; }
.subsection-heading p { margin: 4px 0 0; color: var(--alp-color-muted); font-size: 12px; }
.subsection-heading > span { color: var(--alp-color-muted); font-size: 11px; }

.inspector-panel { padding: 18px; border-left: 1px solid var(--alp-color-border); background: var(--alp-bg-surface); }
.inspector-topline { display: flex; justify-content: space-between; color: var(--alp-color-primary); font-size: 11px; font-weight: 650; }
.inspector-title { display: flex; gap: 11px; align-items: center; padding: 16px 0; border-bottom: 1px solid var(--alp-color-border); }
.inspector-icon { display: grid; place-items: center; width: 40px; height: 40px; border-radius: var(--alp-radius-card); color: var(--alp-color-primary); background: var(--alp-color-primary-soft); font-size: 19px; }
.inspector-title h3 { margin: 0; font-size: 19px; }
.inspector-title p { margin: 4px 0 0; color: var(--alp-color-muted); font-size: 11px; }
.inspector-section { padding: 14px 0; border-bottom: 1px solid var(--alp-color-border); }
.inspector-section h4 { margin: 0 0 9px; font-size: 12px; }
.inspector-section > p { margin: 0; color: var(--alp-color-text-secondary); font-size: 12px; line-height: 1.65; }
.inspector-section ul { display: grid; gap: 7px; margin: 0; padding: 0; list-style: none; }
.inspector-section li { display: flex; align-items: flex-start; gap: 7px; color: var(--alp-color-text-secondary); font-size: 11px; line-height: 1.5; }
.inspector-section li .el-icon { margin-top: 2px; color: var(--alp-color-success); }
.relation-summary > div { display: grid; gap: 5px; margin-top: 9px; }
.relation-summary div > span { color: var(--alp-color-muted); font-size: 10px; }
.relation-summary button { border: 0; padding: 0; color: var(--alp-color-primary); background: transparent; cursor: pointer; text-align: left; font-size: 11px; }
.relation-summary small { color: var(--alp-color-muted); font-size: 11px; }
.evidence-block { display: grid; grid-template-columns: 1fr 1fr; column-gap: 12px; }
.evidence-block h4 { grid-column: 1 / -1; }
.evidence-row { display: grid; gap: 2px; padding: 9px; background: var(--alp-bg-surface-muted); border-radius: var(--alp-radius-sm); }
.evidence-row strong { font-size: 15px; }
.evidence-row span { color: var(--alp-color-muted); font-size: 10px; }
.action-stack { display: grid; gap: 8px; padding-top: 16px; }
.action-stack .el-button { width: 100%; margin: 0; }

@media (max-width: 1280px) {
  .workspace-grid { grid-template-columns: 170px minmax(0, 1fr) 290px; }
  .path-metrics { min-width: 380px; }
}

@media (max-width: 1080px) {
  .command-header { align-items: flex-start; }
  .path-metrics { min-width: 0; }
  .workspace-grid { grid-template-columns: 160px minmax(0, 1fr); }
  .inspector-panel { grid-column: 1 / -1; border-top: 1px solid var(--alp-color-border); border-left: 0; }
}

@media (max-width: 760px) {
  .command-header { flex-direction: column; }
  .path-metrics { width: 100%; flex-wrap: wrap; gap: 14px; }
  .command-toolbar { flex-wrap: wrap; }
  .search-control { width: 100%; }
  .toolbar-select { flex: 1; }
  .workspace-grid { grid-template-columns: 1fr; }
  .filter-rail { display: none; }
  .path-workspace { padding: 10px; }
  .lane-track { align-items: stretch; }
}
</style>
