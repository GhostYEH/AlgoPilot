<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  List,
  Reading,
  Histogram,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { HashSectionKind, HashTableSection } from '@/modules/hashTable/hashTableCurriculum'
import type { LearnSection } from '@/modules/shared/learningTypes'
import HashTableSectionAnimation from '@/modules/hashTable/components/HashTableSectionAnimation.vue'
import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'
import InlineOjPractice from '@/components/oj/InlineOjPractice.vue'
import LearnSectionBody from '@/components/learning/LearnSectionBody.vue'
import SelectableLearnText from '@/components/learning/SelectableLearnText.vue'
import { useProvideAiTutorFromPanel } from '@/composables/useProvideAiTutorFromPanel'
import ModuleGameEntry from '@/components/learning/ModuleGameEntry.vue'
import {
  HASH_TABLE_CURRICULUM_INTRO,
  HASH_TABLE_SECTIONS,
  HASH_STRUCTURE_GUIDE,
  HASH_VS_TWOPOINTERS_COMPARE,
  HASH_SECTION_IDS,
} from '@/modules/hashTable/hashTableCurriculum'

const router = useRouter()
const route = useRoute()

const aiTutorRef = ref<InstanceType<typeof AiTutorPanel> | null>(null)
useProvideAiTutorFromPanel(aiTutorRef)

const activeSection = ref(HASH_TABLE_SECTIONS[0]?.id ?? 'theory')

const current = computed(() => HASH_TABLE_SECTIONS.find((s) => s.id === activeSection.value))

const currentLearnSection = computed(() =>
  current.value ? asLearnSection(current.value) : null,
)

function asLearnSection(s: HashTableSection): LearnSection {
  return {
    id: s.id,
    title: s.title,
    subtitle: s.goal,
    difficulty: '基础',
    estMinutes: 25,
    keywords: s.kind === 'theory' ? ['哈希表'] : s.kind === 'two-pointers' ? ['双指针'] : ['哈希'],
    points: s.points,
    overview: s.overview,
    topicBlocks: s.topicBlocks,
    complexityHint: s.complexity,
    main: s.main,
    related: s.related,
  }
}

const sectionIndex = computed(() =>
  HASH_TABLE_SECTIONS.findIndex((s) => s.id === activeSection.value),
)

const progressPercent = computed(() => {
  const n = HASH_TABLE_SECTIONS.length
  if (n <= 0) return 0
  return Math.round(((sectionIndex.value + 1) / n) * 100)
})

const isFirst = computed(() => sectionIndex.value <= 0)
const isLast = computed(() => sectionIndex.value >= HASH_TABLE_SECTIONS.length - 1)

const kindLabel = (k: HashSectionKind) => {
  const map: Record<HashSectionKind, string> = {
    theory: '理论',
    practice: '刷题',
    'two-pointers': '双指针',
    summary: '总结',
  }
  return map[k] ?? k
}

const kindTagType = (k: HashSectionKind): 'info' | 'success' | 'warning' | 'primary' => {
  if (k === 'theory') return 'info'
  if (k === 'practice') return 'success'
  if (k === 'two-pointers') return 'warning'
  return 'primary'
}

function goHome() {
  router.push({ name: 'home' })
}

function onMenuSelect(index: string) {
  activeSection.value = index
}

function goPrev() {
  if (isFirst.value) return
  activeSection.value = HASH_TABLE_SECTIONS[sectionIndex.value - 1]!.id
}

function goNext() {
  if (isLast.value) return
  activeSection.value = HASH_TABLE_SECTIONS[sectionIndex.value + 1]!.id
}

function onJumpSelect(id: string) {
  activeSection.value = id
}

async function copySectionLink() {
  const id = activeSection.value
  const url = new URL(window.location.href)
  url.searchParams.set('section', id)
  try {
    await navigator.clipboard.writeText(url.toString())
    ElMessage.success('本节链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制地址栏')
  }
}

onMounted(() => {
  const q = route.query.section
  if (typeof q === 'string' && HASH_SECTION_IDS.includes(q)) {
    activeSection.value = q
  } else if (typeof q === 'string' && q.length > 0) {
    activeSection.value = 'theory'
  }
  if (route.query.section !== activeSection.value) {
    router.replace({ path: route.path, query: { ...route.query, section: activeSection.value } })
  }
})

watch(activeSection, (id) => {
  if (route.query.section !== id) {
    router.replace({ path: route.path, query: { ...route.query, section: id } })
  }
})

watch(
  () => route.query.section,
  (q) => {
    if (typeof q === 'string' && HASH_SECTION_IDS.includes(q) && q !== activeSection.value) {
      activeSection.value = q
    }
  },
)

</script>

<template>
  <div class="module-learn-shell hash-table-page">
    <header class="page-head">
      <el-page-header title="哈希表学习模块" @back="goHome">
        <template #extra>
          <div class="head-extra">
            <el-tag type="info" effect="plain" size="small">哈希表篇</el-tag>
            <div class="head-progress">
              <span class="progress-label">章节进度</span>
              <el-progress
                :percentage="progressPercent"
                :stroke-width="8"
                :show-text="false"
                class="progress-bar"
                striped
                striped-flow
                color="var(--alp-color-primary)"
              />
              <span class="progress-num">{{ sectionIndex + 1 }} / {{ HASH_TABLE_SECTIONS.length }}</span>
            </div>
          </div>
        </template>
      </el-page-header>
    </header>

    <p class="intro">{{ HASH_TABLE_CURRICULUM_INTRO }}</p>

    <el-alert type="info" :closable="false" show-icon class="attrib">
      <template #title>
        支持用地址栏参数 <code class="inline-code">?section=</code> 定位小节（如
        <code class="inline-code">two-sum</code>）。
      </template>
    </el-alert>

    <div class="module-body">
      <aside class="aside">
        <div class="aside-head">
          <el-icon class="aside-icon"><List /></el-icon>
          <span>章节目录</span>
        </div>
        <el-scrollbar class="aside-scroll">
          <el-menu :default-active="activeSection" class="side-menu" @select="onMenuSelect">
            <el-menu-item v-for="s in HASH_TABLE_SECTIONS" :key="s.id" :index="s.id">
              <div class="menu-row">
                <span class="menu-label">{{ s.menuLabel }}</span>
                <el-tag :type="kindTagType(s.kind)" size="small" effect="plain" class="menu-tag">
                  {{ kindLabel(s.kind) }}
                </el-tag>
              </div>
            </el-menu-item>
          </el-menu>
        </el-scrollbar>
      </aside>

      <main class="main">
        <div class="main-toolbar">
          <div class="toolbar-left">
            <el-button :disabled="isFirst" :icon="ArrowLeft" @click="goPrev">上一节</el-button>
            <el-button :disabled="isLast" @click="goNext">
              下一节
              <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </div>
          <div class="toolbar-center">
            <span class="toolbar-hint">快速跳转</span>
            <el-select
              :model-value="activeSection"
              filterable
              placeholder="选择小节"
              class="jump-select"
              @update:model-value="onJumpSelect"
            >
              <el-option
                v-for="s in HASH_TABLE_SECTIONS"
                :key="s.id"
                :label="s.menuLabel"
                :value="s.id"
              />
            </el-select>
          </div>
          <el-button text type="primary" @click="copySectionLink">复制本节链接</el-button>
        </div>

        <Transition name="ht-section" mode="out-in">
          <el-card v-if="current" :key="activeSection" shadow="never" class="content-card">
            <template #header>
              <div class="card-head">
                <div class="card-head-text">
                  <div class="card-title-row">
                    <span class="card-title">{{ current.title }}</span>
                    <el-tag :type="kindTagType(current.kind)" size="small" effect="light">
                      {{ kindLabel(current.kind) }}
                    </el-tag>
                  </div>
                  <p class="card-goal">{{ current.goal }}</p>
                </div>
              </div>
            </template>

            <ModuleGameEntry module-key="hash-table" :section-id="current.id" />

            <div class="content-visual">
              <HashTableSectionAnimation :key="current.id" :section-id="current.id" />
            </div>

            <SelectableLearnText :section-id="current.id">
            <p v-if="current.complexity" class="complexity">
              <el-icon><Histogram /></el-icon>
              <span>{{ current.complexity }}</span>
            </p>

            <LearnSectionBody :section="asLearnSection(current)" />

            <template v-if="current.id === 'theory'">
              <el-divider content-position="left">刷题载体速查</el-divider>
              <p class="table-hint">对照「数组 / set / map」选型，下列为常见刷题语境下的取舍。</p>
              <div class="table-wrap">
                <el-table :data="HASH_STRUCTURE_GUIDE" stripe border class="guide-table" size="small">
                  <el-table-column prop="structure" label="结构" min-width="120" />
                  <el-table-column prop="scene" label="适用场景" min-width="200" />
                  <el-table-column prop="pros" label="优势直觉" min-width="160" />
                  <el-table-column prop="examples" label="本章例题" min-width="140" />
                </el-table>
              </div>
            </template>

            <template v-if="current.id === 'summary'">
              <el-divider content-position="left">454 与 15 / 18 易混对照</el-divider>
              <p class="table-hint">需注意：四数相加 II 是哈希计数模板；三数之和、四数之和以排序 + 双指针为主。</p>
              <div class="table-wrap">
                <el-table :data="HASH_VS_TWOPOINTERS_COMPARE" stripe border class="guide-table" size="small">
                  <el-table-column prop="dimension" label="维度" width="100" />
                  <el-table-column prop="fourSumIi" label="454 四数相加 II" min-width="200" />
                  <el-table-column prop="threeOrFourSum" label="15 / 18 三数、四数之和" min-width="220" />
                </el-table>
              </div>
            </template>

            <template v-if="current.id === 'theory'">
              <el-divider content-position="left">后续扩展</el-divider>
              <p class="hint">
                <el-icon><Reading /></el-icon>
                可在此接入「多智能体」生成个性化题单、或对接题库统计哈希篇完成度。
              </p>
            </template>
            </SelectableLearnText>

            <div class="card-footer-nav">
              <el-button :disabled="isFirst" size="small" @click="goPrev">← 上一节</el-button>
              <el-button :disabled="isLast" size="small" type="primary" plain @click="goNext">下一节 →</el-button>
            </div>
          </el-card>
        </Transition>

        <section v-if="current?.main" class="inline-oj-zone">
          <el-divider content-position="left">主刷题 · 在线练习</el-divider>
          <InlineOjPractice :main="current.main" :related="current.related" />
        </section>
      </main>

      <AiTutorPanel
        ref="aiTutorRef"
        module-key="hash-table"
        module-title="哈希表学习模块"
        chapter-tag="哈希表篇"
        :module-intro="HASH_TABLE_CURRICULUM_INTRO"
        :section="currentLearnSection"
      />
    </div>
  </div>
</template>

<style scoped>
.page-head :deep(.el-page-header__header) {
  flex-wrap: wrap;
  gap: 8px;
}

.head-extra {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  min-width: 0;
}

.head-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  width: min(280px, 100%);
}

.progress-label {
  font-size: 12px;
  color: var(--alp-color-muted);
  flex-shrink: 0;
}

.progress-bar {
  flex: 1;
  min-width: 80px;
}

.progress-num {
  font-size: 12px;
  color: var(--alp-color-muted);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.intro {
  animation: htIntroFade 0.55s ease backwards;
}

@keyframes htIntroFade {
  from {
    opacity: 0;
    transform: translateY(4px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.module-body {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-height: 480px;
  width: 100%;
}

.aside {
  flex: 0 0 var(--alp-aside-width, 248px);
  width: var(--alp-aside-width, 248px);
  border-right: 1px solid var(--alp-color-border);
  background: var(--alp-bg-aside-gradient);
  position: sticky;
  top: 12px;
  align-self: flex-start;
  max-height: calc(100vh - 88px);
  display: flex;
  flex-direction: column;
  border-radius: 12px 0 0 12px;
}

.aside-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
  border-bottom: 1px solid var(--alp-color-border);
}

.aside-scroll {
  flex: 1;
  min-height: 0;
}

.side-menu {
  border-right: none;
  background: transparent;
  padding: 4px 0 12px;
}

.menu-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  min-width: 0;
}

.menu-label {
  font-size: 13px;
  line-height: 1.35;
  white-space: normal;
  text-align: left;
  flex: 1;
  min-width: 0;
}

.menu-tag {
  flex-shrink: 0;
}

.main {
  flex: 1;
  min-width: 0;
  padding: 14px 18px 20px;
  border-radius: 0 12px 12px 0;
}

.main-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 12px;
  margin-bottom: 14px;
  padding: 10px 12px;
  background: var(--alp-bg-surface-muted);
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
}

.toolbar-left {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: center;
  min-width: 200px;
}

.toolbar-hint {
  font-size: 12px;
  color: var(--alp-color-muted);
  flex-shrink: 0;
}

.jump-select {
  width: min(320px, 100%);
}

.card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-head-text {
  flex: 1;
  min-width: 0;
}

.card-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
}

.card-goal {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.55;
}

.main-lc {
  flex-shrink: 0;
  font-weight: 500;
}

.table-hint {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.55;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
  border-radius: 8px;
}

.guide-table {
  min-width: 520px;
}

.related-link {
  font-size: 14px;
  transition:
    color 0.2s ease,
    transform 0.2s ease;
}

.related-link:hover {
  transform: translateX(2px);
}

.card-footer-nav {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px dashed var(--alp-color-border);
}

/* —— 章节切换过渡 —— */
.ht-section-enter-active,
.ht-section-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}

.ht-section-enter-from,
.ht-section-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* —— 要点依次浮现（换节后重播） —— */
.points-item {
  animation: htPointIn 0.48s ease backwards;
  animation-delay: var(--ht-stagger, 0s);
}

@keyframes htPointIn {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* —— 理论节：流程与碰撞示意 —— */
.theory-viz {
  margin: 0 0 18px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.viz-lead {
  margin: 0 0 14px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.55;
}

.viz-block + .viz-block {
  margin-top: 18px;
}

.viz-title {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.viz-flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 6px;
}

.viz-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid);
  min-width: 72px;
  animation: htChipIdle 3.2s ease-in-out infinite;
}

.viz-chip-key {
  animation-delay: 0s;
}

.viz-chip-fn {
  animation-delay: 0.25s;
}

.viz-chip-idx {
  animation-delay: 0.5s;
}

.viz-chip-label {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.viz-chip-val {
  font-size: 13px;
  font-weight: 600;
  font-family: ui-monospace, monospace;
  color: var(--alp-color-primary);
}

@keyframes htChipIdle {
  0%,
  100% {
    transform: translateY(0);
    box-shadow: 0 0 0 0 rgba(56, 189, 248, 0);
  }

  40% {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.18);
  }
}

.viz-connector {
  display: flex;
  align-items: center;
  gap: 0;
  min-width: 28px;
  flex: 1 1 40px;
  max-width: 72px;
}

.viz-connector-short {
  max-width: 48px;
}

.viz-line {
  flex: 1;
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(
    90deg,
    rgba(56, 189, 248, 0.25),
    var(--alp-color-primary)
  );
  background-size: 200% 100%;
  animation: htLineShine 1.8s ease-in-out infinite;
}

.viz-arrowhead {
  font-size: 10px;
  line-height: 1;
  color: var(--alp-color-primary);
  animation: htArrowPulse 1.2s ease-in-out infinite;
}

@keyframes htLineShine {
  0% {
    background-position: 100% 0;
  }

  100% {
    background-position: 0 0;
  }
}

@keyframes htArrowPulse {
  0%,
  100% {
    opacity: 0.45;
    transform: translateX(0);
  }

  50% {
    opacity: 1;
    transform: translateX(2px);
  }
}

.viz-slot {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 2px dashed rgba(56, 189, 248, 0.45);
  background: var(--alp-bg-code-ish);
  animation: htSlotBreathe 2.4s ease-in-out infinite;
}

.viz-slot-label {
  font-size: 11px;
  color: var(--alp-color-muted);
  width: 100%;
}

.viz-slot-bracket {
  font-weight: 700;
  color: var(--alp-color-primary);
}

.viz-slot-core {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

@keyframes htSlotBreathe {
  0%,
  100% {
    border-color: rgba(56, 189, 248, 0.35);
  }

  50% {
    border-color: var(--alp-color-primary);
  }
}

.viz-collision {
  padding: 12px;
  border-radius: 8px;
  background: var(--alp-bg-code-ish);
  border: 1px solid var(--alp-color-border);
}

.viz-bucket-head {
  display: inline-block;
  margin-bottom: 10px;
  padding: 4px 12px;
  border-radius: 6px;
  background: var(--alp-bg-surface-muted);
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.viz-chain {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0;
}

.viz-node {
  padding: 8px 14px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.18), var(--alp-bg-surface-solid));
  border: 1px solid rgba(56, 189, 248, 0.35);
  animation: htChainNode 2.4s ease-in-out infinite;
}

.viz-node-b {
  animation-delay: 0.35s;
}

.viz-node-tag {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-primary);
}

.viz-chain-link {
  width: 32px;
  height: 4px;
  margin: 0 2px;
  border-radius: 2px;
  background: linear-gradient(
    90deg,
    rgba(56, 189, 248, 0.35),
    var(--alp-color-primary)
  );
  background-size: 200% 100%;
  animation: htLineShine 1.4s ease-in-out infinite;
}

@keyframes htChainNode {
  0%,
  100% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.03);
  }
}

.viz-note {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

/* —— 两数之和：数组 + map 联动高亮 —— */
.twosum-viz {
  margin: 0 0 18px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.twosum-stage {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 18px;
}

.twosum-nums {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.twosum-cell {
  min-width: 42px;
  padding: 8px 10px;
  text-align: center;
  font-size: 15px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  border-radius: 8px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid);
  color: var(--alp-color-text);
  transition:
    transform 0.28s ease,
    box-shadow 0.28s ease,
    border-color 0.28s ease;
}

.twosum-cell--active {
  border-color: var(--alp-color-primary);
  transform: scale(1.06);
  box-shadow: 0 4px 14px rgba(56, 189, 248, 0.28);
  z-index: 1;
}

.twosum-cell--pair {
  background: linear-gradient(145deg, rgba(56, 189, 248, 0.22), var(--alp-bg-surface-solid));
  border-color: rgba(56, 189, 248, 0.55);
  animation: htPairGlow 0.85s ease-in-out infinite alternate;
}

@keyframes htPairGlow {
  from {
    box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.2);
  }

  to {
    box-shadow: 0 0 0 6px rgba(56, 189, 248, 0.08);
  }
}

.twosum-mapbox {
  flex: 1;
  min-width: 200px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px dashed rgba(56, 189, 248, 0.35);
  background: var(--alp-bg-code-ish);
}

.twosum-map-title {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.twosum-map-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  font-family: ui-monospace, monospace;
}

.twosum-map-pulse {
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.4;
  opacity: 0.5;
  transition: opacity 0.35s ease;
}

.twosum-map-pulse--on {
  opacity: 1;
  color: var(--alp-color-primary);
  font-weight: 600;
  animation: htTextBlink 1.1s ease-in-out infinite;
}

.twosum-map-row {
  padding: 4px 0;
  color: var(--alp-color-text);
}

.twosum-map-row--glow {
  color: var(--alp-color-primary);
  font-weight: 600;
  animation: htMapRowPulse 1s ease-in-out infinite alternate;
}

@keyframes htTextBlink {
  0%,
  100% {
    opacity: 0.75;
  }

  50% {
    opacity: 1;
  }
}

@keyframes htMapRowPulse {
  from {
    transform: translateX(0);
  }

  to {
    transform: translateX(3px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .ht-section-enter-active,
  .ht-section-leave-active {
    transition: none;
  }

  .ht-section-enter-from,
  .ht-section-leave-to {
    opacity: 1;
    transform: none;
  }

  .intro {
    animation: none;
  }

  .points-item,
  .viz-chip,
  .viz-line,
  .viz-arrowhead,
  .viz-slot,
  .viz-node,
  .viz-node-b,
  .viz-chain-link,
  .twosum-cell--pair,
  .twosum-map-pulse--on,
  .twosum-map-row--glow {
    animation: none !important;
  }

  .twosum-cell {
    transition: none;
  }

  .twosum-cell--active {
    transform: none;
  }

  .twosum-map-pulse {
    transition: none;
  }

  .related-link {
    transition: none;
  }

  .related-link:hover {
    transform: none;
  }
}

@media (max-width: 900px) {
  .toolbar-center {
    flex-basis: 100%;
    justify-content: flex-start;
  }

  .jump-select {
    flex: 1;
    width: auto;
    min-width: 0;
  }
}

@media (max-width: 768px) {
  .module-body {
    flex-direction: column;
    align-items: stretch;
  }

  .aside {
    position: relative;
    top: 0;
    width: 100% !important;
    flex: none;
    max-height: 280px;
    border-right: none;
    border-bottom: 1px solid var(--alp-color-border);
    border-radius: 12px 12px 0 0;
  }

  .main {
    border-radius: 0 0 12px 12px;
  }

  .head-extra {
    align-items: flex-start;
    width: 100%;
  }

  .head-progress {
    width: 100%;
  }

  .guide-table {
    min-width: 100%;
  }
}
</style>
