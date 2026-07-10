<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  CopyDocument,
  MagicStick,
  TrendCharts,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getModuleLearnConfig,
  type ModuleLearnConfig,
} from '@/modules/shared/moduleRegistry'
import type { LearnSection } from '@/modules/shared/learningTypes'
import { isLoggedIn } from '@/stores/auth'
import { applyRemoteProgressPayload } from '@/utils/learningStorage'
import { schedulePushLearningProgress } from '@/utils/learningRemoteSync'
import { schedulePersonaLearningPatch } from '@/utils/personaLearningSync'
import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'
import InlineOjPractice from '@/components/oj/InlineOjPractice.vue'
import OjDsHintCard from '@/components/oj/OjDsHintCard.vue'
import OjCodeHintCard from '@/components/oj/OjCodeHintCard.vue'
import LearnSectionBody from '@/components/learning/LearnSectionBody.vue'
import ModuleGameEntry from '@/components/learning/ModuleGameEntry.vue'
import SelectableLearnText from '@/components/learning/SelectableLearnText.vue'
import SectionDirectoryAside from '@/components/learning/SectionDirectoryAside.vue'
import RecommendedResourcesPanel from '@/components/learning/RecommendedResourcesPanel.vue'
import { useProvideAiTutorFromPanel } from '@/composables/useProvideAiTutorFromPanel'

const props = defineProps<{
  moduleKey: string
}>()

const router = useRouter()
const route = useRoute()

const aiTutorRef = ref<InstanceType<typeof AiTutorPanel> | null>(null)
const inlineOjRef = ref<InstanceType<typeof InlineOjPractice> | null>(null)
useProvideAiTutorFromPanel(aiTutorRef)

const config = computed<ModuleLearnConfig | undefined>(() => getModuleLearnConfig(props.moduleKey))

function sectionFromQuery(cfg: ModuleLearnConfig): string {
  const sec = route.query.section
  if (typeof sec === 'string' && cfg.sections.some((s) => s.id === sec)) return sec
  return cfg.sections[0]?.id ?? ''
}

const initialCfg = getModuleLearnConfig(props.moduleKey)
const activeSection = ref(initialCfg ? sectionFromQuery(initialCfg) : '')
const doneMap = ref<Record<string, boolean>>({})

const AnimComponent = computed(() => {
  const cfg = config.value
  if (!cfg) return null
  return defineAsyncComponent(cfg.animationComponent) as Component
})

const sections = computed(() => config.value?.sections ?? [])
const current = computed(() => sections.value.find((s) => s.id === activeSection.value))

const sectionIndex = computed(() => sections.value.findIndex((s) => s.id === activeSection.value))

const progressPercent = computed(() => {
  const total = config.value?.sectionCount ?? 1
  const done = sections.value.filter((s) => doneMap.value[s.id]).length
  return Math.round((done / total) * 100)
})

const prevSection = computed(() => {
  const i = sectionIndex.value
  return i > 0 ? sections.value[i - 1] : null
})

const nextSection = computed(() => {
  const i = sectionIndex.value
  return i >= 0 && i < sections.value.length - 1 ? sections.value[i + 1] : null
})

const sectionDone = computed(() => !!doneMap.value[activeSection.value])

const sectionExtraTables = computed(() => {
  const id = current.value?.id
  if (!id) return []
  return (config.value?.extraTables ?? []).filter((t) => t.sectionId === id)
})

/** 栈队列：左演示、右详解（理论基础仍全宽三列 + 下方正文） */
const useStackQueueSideLayout = computed(
  () => props.moduleKey === 'stack-queue' && current.value?.id !== 'theory',
)

function difficultyType(d: LearnSection['difficulty']) {
  if (d === '入门') return 'success'
  if (d === '基础') return 'primary'
  return 'warning'
}

function shortTitle(s: LearnSection) {
  return s.title.replace(/^\d+\.\s*/, '')
}

function selectSection(id: string) {
  activeSection.value = id
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goHome() {
  router.push({ name: 'home' })
}

function goGenerateResources() {
  const topic =
    props.moduleKey === 'sorting'
      ? '排序算法专题：归并、快速排序、堆排序与稳定性'
      : '图论 BFS DFS ch06-graph'
  router.push({
    name: 'resources',
    query: { topic, module: props.moduleKey },
  })
}

function setSectionDone(done: boolean | string | number) {
  const cfg = config.value
  if (!cfg) return
  const id = activeSection.value
  const v = done === true || done === 'true'
  doneMap.value = cfg.toggleSectionDone(id, v, doneMap.value)
  schedulePushLearningProgress()
  if (v) {
    schedulePersonaLearningPatch({
      event_type: 'section_done',
      module_key: props.moduleKey,
      detail: id,
    })
  }
}

async function copySectionLink() {
  const cfg = config.value
  if (!cfg) return
  const path = router.resolve({
    name: cfg.routeName,
    query: { section: activeSection.value },
  }).href
  const url = `${window.location.origin}${path}`
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('已复制本节链接')
  } catch {
    ElMessage.warning('复制失败，请手动复制地址栏')
  }
}

onMounted(async () => {
  const cfg = config.value
  if (!cfg) {
    router.replace({ name: 'home' })
    return
  }
  doneMap.value = cfg.loadSectionDone()

  if (isLoggedIn.value) {
    try {
      const { fetchLearningProgress } = await import('@/api/learning')
      const r = await fetchLearningProgress()
      applyRemoteProgressPayload((r.payload || {}) as Record<string, unknown>)
      doneMap.value = cfg.loadSectionDone()
    } catch {
      /* ignore */
    }
  }

  if (route.query.section !== activeSection.value) {
    router.replace({ name: cfg.routeName, query: { section: activeSection.value } })
  }
})

watch(
  () => props.moduleKey,
  () => {
    const cfg = config.value
    if (!cfg) return
    activeSection.value = sectionFromQuery(cfg)
    doneMap.value = cfg.loadSectionDone()
  },
)

watch(activeSection, (id) => {
  const cfg = config.value
  if (!cfg || route.query.section === id) return
  router.replace({ name: cfg.routeName, query: { section: id } })
})

watch(
  () => route.query.section,
  (sec) => {
    if (
      typeof sec === 'string' &&
      sections.value.some((s) => s.id === sec) &&
      sec !== activeSection.value
    ) {
      activeSection.value = sec
    }
  },
)
</script>

<template>
  <div v-if="config" class="module-learn-shell">
    <div class="top-bar">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ name: 'home' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>{{ config.breadcrumb }}</el-breadcrumb-item>
        <el-breadcrumb-item v-if="current">{{ current.title.replace(/^\d+\.\s*/, '') }}</el-breadcrumb-item>
      </el-breadcrumb>
      <div class="top-actions">
        <span class="progress-label">学习进度</span>
        <el-progress
          :percentage="progressPercent"
          :stroke-width="8"
          striped
          striped-flow
          color="var(--alp-color-primary)"
          style="width: 140px"
        />
        <el-button size="small" :icon="CopyDocument" @click="copySectionLink">复制本节链接</el-button>
      </div>
    </div>

    <div class="hero">
      <div class="hero-main">
        <el-button text type="primary" class="back-btn" :icon="ArrowLeft" @click="goHome">返回首页</el-button>
        <h1 class="hero-title">{{ config.heroTitle }}</h1>
        <p class="hero-intro">{{ config.intro }}</p>
        <div class="hero-tags">
          <el-tag type="info" effect="plain" size="small">{{ config.chapterTag }}</el-tag>
          <el-tag type="success" effect="plain" size="small">共 {{ config.sectionCount }} 节</el-tag>
          <el-tag v-if="moduleKey === 'graph'" type="warning" effect="plain" size="small">
            skill: graph-bfs-dfs
          </el-tag>
        </div>
        <div v-if="moduleKey === 'graph' || moduleKey === 'sorting'" class="hero-actions">
          <el-button type="primary" plain size="small" :icon="MagicStick" @click="goGenerateResources">
            生成个性化资源
          </el-button>
          <el-button size="small" @click="router.push({ name: 'agent-workbench' })">
            多智能体工作台
          </el-button>
        </div>
      </div>
    </div>

    <div class="module-layout-row layout-row">
      <SectionDirectoryAside
        class="section-aside-col"
        :sections="sections"
        :active-section="activeSection"
        :done-map="doneMap"
        :section-index="sectionIndex"
        :section-count="config.sectionCount"
        :aria-label="config.breadcrumb"
        @select="selectSection"
      />

      <div class="module-layout-main">
        <el-card v-if="current" shadow="never" class="content-card">
          <div class="content-head">
            <div>
              <h2 class="content-title">{{ current.title }}</h2>
              <p class="content-sub">{{ current.subtitle }}</p>
            </div>
            <div class="content-actions">
              <el-switch
                :model-value="sectionDone"
                active-text="已学习"
                inline-prompt
                @update:model-value="setSectionDone"
              />
            </div>
          </div>

          <div class="meta-row">
            <el-tag :type="difficultyType(current.difficulty)" effect="light" round>
              {{ current.difficulty }}
            </el-tag>
            <span class="meta-item">
              <el-icon><TrendCharts /></el-icon>
              约 {{ current.estMinutes }} 分钟
            </span>
            <el-tag
              v-for="kw in current.keywords"
              :key="kw"
              size="small"
              effect="plain"
              class="kw-tag"
            >
              {{ kw }}
            </el-tag>
          </div>

          <ModuleGameEntry :module-key="moduleKey" :section-id="current.id" />

          <div
            v-if="useStackQueueSideLayout"
            class="content-viz-split"
          >
            <div class="content-visual content-visual--split">
              <Transition :name="config.animTransitionClass" mode="out-in">
                <component
                  :is="AnimComponent"
                  v-if="AnimComponent && current"
                  :key="current.id"
                  :section-id="current.id"
                />
              </Transition>
            </div>
            <LearnSectionBody
              v-if="current"
              :section="current"
              side-viz
            />
          </div>

          <template v-else>
            <div
              class="content-visual"
              :class="{ 'content-visual--sq-theory': moduleKey === 'stack-queue' && current?.id === 'theory' }"
            >
              <Transition :name="config.animTransitionClass" mode="out-in">
                <component
                  :is="AnimComponent"
                  v-if="AnimComponent && current"
                  :key="current.id"
                  :section-id="current.id"
                />
              </Transition>
            </div>

            <LearnSectionBody
              v-if="current"
              :section="current"
              :below-viz="moduleKey === 'stack-queue' && current.id === 'theory'"
            />
          </template>

          <SelectableLearnText v-if="current" :section-id="current.id" class="learn-extras-selectable">
          <template v-for="block in sectionExtraTables" :key="block.title">
              <el-divider content-position="left">
                <span class="divider-label">{{ block.title }}</span>
              </el-divider>
              <p v-if="block.hint" class="table-hint">{{ block.hint }}</p>
              <div class="table-wrap">
                <el-table :data="block.data" stripe border size="small" class="guide-table">
                  <el-table-column
                    v-for="col in block.columns"
                    :key="col.prop"
                    :prop="col.prop"
                    :label="col.label"
                    :width="col.width"
                    :min-width="col.minWidth"
                  />
                </el-table>
              </div>
          </template>

          <template v-if="current.pitfalls?.length">
            <el-divider content-position="left">
              <span class="divider-label">易错点</span>
            </el-divider>
            <div class="pitfall-group">
              <el-alert
                v-for="(t, idx) in current.pitfalls"
                :key="idx"
                :title="t"
                type="warning"
                show-icon
                :closable="false"
                class="pitfall-alert"
              />
            </div>
          </template>

          <template v-if="current.checklist?.length">
            <el-divider content-position="left">
              <span class="divider-label">本节自检</span>
            </el-divider>
            <ol class="checklist">
              <li v-for="(c, idx) in current.checklist" :key="idx">{{ c }}</li>
            </ol>
          </template>

          <p v-if="current.complexityHint" class="complexity">
            <strong>复杂度与范围直觉：</strong>{{ current.complexityHint }}
          </p>
          </SelectableLearnText>

          <template v-if="current.codeSketch">
            <el-divider content-position="left">
              <span class="divider-label">实现骨架</span>
            </el-divider>
            <pre class="code-sketch" aria-label="本节核心代码骨架">{{ current.codeSketch }}</pre>
          </template>

        </el-card>

        <section v-if="current?.main" class="inline-oj-zone">
          <el-divider content-position="left">
            <span class="divider-label">刷题 · 在线练习</span>
          </el-divider>
          <div class="inline-oj-editor">
            <InlineOjPractice
              ref="inlineOjRef"
              :main="current.main"
              :related="current.related"
              class="inline-oj-center"
            />
          </div>
          <div class="inline-oj-hints">
            <OjDsHintCard
              v-if="inlineOjRef?.problem"
              class="inline-oj-hint inline-oj-hint--ds"
              :problem="inlineOjRef.problem"
              :language="inlineOjRef.language"
            />
            <OjCodeHintCard
              v-if="inlineOjRef?.problem"
              class="inline-oj-hint inline-oj-hint--code"
              :problem="inlineOjRef.problem"
              :language="inlineOjRef.language"
              :user-code="inlineOjRef.code ?? ''"
            />
          </div>
        </section>

        <div v-if="current" class="pager">
          <el-button :disabled="!prevSection" @click="prevSection && selectSection(prevSection.id)">
            <el-icon><ArrowLeft /></el-icon>
            上一节
          </el-button>
          <span v-if="prevSection" class="pager-hint">{{ shortTitle(prevSection) }}</span>
          <span class="pager-spacer" />
          <span v-if="nextSection" class="pager-hint">{{ shortTitle(nextSection) }}</span>
          <el-button :disabled="!nextSection" @click="nextSection && selectSection(nextSection.id)">
            下一节
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>

      <div class="module-layout-side">
        <RecommendedResourcesPanel
          v-if="moduleKey === 'graph' && isLoggedIn"
          class="graph-rec-panel"
          module-key="graph"
          title="图论 · 个性化资源推荐（ch06-graph / graph-bfs-dfs）"
        />

        <AiTutorPanel
          ref="aiTutorRef"
          :module-key="moduleKey"
          :module-title="config.heroTitle"
          :chapter-tag="config.chapterTag"
          :module-intro="config.intro"
          :section="current ?? null"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.table-hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.table-wrap {
  margin-bottom: 8px;
}

.guide-table {
  width: 100%;
}

.sq-anim-fade-enter-active,
.sq-anim-fade-leave-active,
.bt-anim-fade-enter-active,
.bt-anim-fade-leave-active,
.bk-anim-fade-enter-active,
.bk-anim-fade-leave-active,
.gr-anim-fade-enter-active,
.gr-anim-fade-leave-active,
.dp-anim-fade-enter-active,
.dp-anim-fade-leave-active,
.ms-anim-fade-enter-active,
.ms-anim-fade-leave-active,
.ll-anim-fade-enter-active,
.ll-anim-fade-leave-active,
.graph-anim-fade-enter-active,
.graph-anim-fade-leave-active,
.sorting-anim-fade-enter-active,
.sorting-anim-fade-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}

.sq-anim-fade-enter-from,
.sq-anim-fade-leave-to,
.bt-anim-fade-enter-from,
.bt-anim-fade-leave-to,
.bk-anim-fade-enter-from,
.bk-anim-fade-leave-to,
.gr-anim-fade-enter-from,
.gr-anim-fade-leave-to,
.dp-anim-fade-enter-from,
.dp-anim-fade-leave-to,
.ms-anim-fade-enter-from,
.ms-anim-fade-leave-to,
.ll-anim-fade-enter-from,
.ll-anim-fade-leave-to,
.graph-anim-fade-enter-from,
.graph-anim-fade-leave-to,
.sorting-anim-fade-enter-from,
.sorting-anim-fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.graph-rec-panel {
  margin-top: 16px;
}

.inline-oj-zone {
  margin-top: 16px;
}

/* OJ 编译器整行显示，充分利用横向空间 */
.inline-oj-editor {
  width: 100%;
  margin-top: 8px;
}

.inline-oj-editor .inline-oj-center {
  min-width: 0;
  width: 100%;
}

/* 两个提示卡片：在 OJ 编译器下方，左右两栏 */
.inline-oj-hints {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
  width: 100%;
}

.inline-oj-hint {
  max-height: 320px;
  overflow: hidden;
}

.inline-oj-hint :deep(.oj-agent-card) {
  height: 100%;
  max-height: inherit;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.inline-oj-hint :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.inline-oj-hint :deep(.oj-agent-body) {
  flex: 1;
  min-height: 80px;
  max-height: none;
  overflow-y: auto;
}

@media (max-width: 1100px) {
  .inline-oj-hints {
    grid-template-columns: 1fr;
  }

  .inline-oj-hint {
    max-height: 280px;
  }
}
</style>
