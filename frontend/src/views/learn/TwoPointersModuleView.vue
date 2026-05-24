<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  CopyDocument,
  TrendCharts,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  TWO_POINTERS_CURRICULUM_INTRO,
  TWO_POINTERS_SECTIONS,
  TWO_POINTERS_SECTION_COUNT,
  TWO_POINTER_PATTERN_GUIDE,
  HASH_VS_TWO_POINTERS_COMPARE,
  type TwoPointersSection,
} from '@/modules/twoPointers/twoPointersCurriculum'
import { loadSectionDone, toggleSectionDone } from '@/modules/twoPointers/twoPointersProgress'
import TwoPointersSectionAnimation from '@/modules/twoPointers/components/TwoPointersSectionAnimation.vue'
import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'
import InlineOjPractice from '@/components/oj/InlineOjPractice.vue'
import LearnSectionBody from '@/components/learning/LearnSectionBody.vue'
import ModuleGameEntry from '@/components/learning/ModuleGameEntry.vue'
import SelectableLearnText from '@/components/learning/SelectableLearnText.vue'
import SectionDirectoryAside from '@/components/learning/SectionDirectoryAside.vue'
import { useProvideAiTutorFromPanel } from '@/composables/useProvideAiTutorFromPanel'
import { isLoggedIn } from '@/stores/auth'
import { applyRemoteProgressPayload } from '@/utils/learningStorage'
import { schedulePushLearningProgress } from '@/utils/learningRemoteSync'

const router = useRouter()
const route = useRoute()

const aiTutorRef = ref<InstanceType<typeof AiTutorPanel> | null>(null)
useProvideAiTutorFromPanel(aiTutorRef)

const activeSection = ref(TWO_POINTERS_SECTIONS[0]?.id ?? 'theory')
const doneMap = ref<Record<string, boolean>>({})

const current = computed(() => TWO_POINTERS_SECTIONS.find((s) => s.id === activeSection.value))

const sectionIndex = computed(() =>
  TWO_POINTERS_SECTIONS.findIndex((s) => s.id === activeSection.value),
)

const progressPercent = computed(() => {
  const done = TWO_POINTERS_SECTIONS.filter((s) => doneMap.value[s.id]).length
  return Math.round((done / TWO_POINTERS_SECTION_COUNT) * 100)
})

const prevSection = computed(() => {
  const i = sectionIndex.value
  return i > 0 ? TWO_POINTERS_SECTIONS[i - 1] : null
})

const nextSection = computed(() => {
  const i = sectionIndex.value
  return i >= 0 && i < TWO_POINTERS_SECTIONS.length - 1 ? TWO_POINTERS_SECTIONS[i + 1] : null
})

const sectionDone = computed(() => !!doneMap.value[activeSection.value])

function difficultyType(d: TwoPointersSection['difficulty']) {
  if (d === '入门') return 'success'
  if (d === '基础') return 'primary'
  return 'warning'
}

function pointerKindLabel(k: TwoPointersSection['pointerKind']) {
  if (k === 'fast-slow') return '快慢'
  if (k === 'opposite') return '相向'
  if (k === 'sorted-lr') return '排序+左右'
  if (k === 'mixed') return '综合'
  return ''
}

function shortTitle(s: TwoPointersSection) {
  return s.title.replace(/^\d+\.\s*/, '')
}

function selectSection(id: string) {
  activeSection.value = id
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goHome() {
  router.push({ name: 'home' })
}

function setSectionDone(done: boolean | string | number) {
  const id = activeSection.value
  const v = done === true || done === 'true'
  doneMap.value = toggleSectionDone(id, v, doneMap.value)
  schedulePushLearningProgress()
}

async function copySectionLink() {
  const path = router.resolve({
    name: 'learn-two-pointers',
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
  doneMap.value = loadSectionDone()
  if (isLoggedIn.value) {
    try {
      const { fetchLearningProgress } = await import('@/api/learning')
      const r = await fetchLearningProgress()
      applyRemoteProgressPayload((r.payload || {}) as Record<string, unknown>)
      doneMap.value = loadSectionDone()
    } catch {
      /* 未登录或网络错误时由拦截器提示 */
    }
  }
  const sec = route.query.section as string | undefined
  if (sec && TWO_POINTERS_SECTIONS.some((s) => s.id === sec)) {
    activeSection.value = sec
  } else {
    router.replace({ name: 'learn-two-pointers', query: { section: activeSection.value } })
  }
})

watch(activeSection, (id) => {
  if (route.query.section === id) return
  router.replace({ name: 'learn-two-pointers', query: { section: id } })
})

watch(
  () => route.query.section,
  (sec) => {
    if (
      typeof sec === 'string' &&
      TWO_POINTERS_SECTIONS.some((s) => s.id === sec) &&
      sec !== activeSection.value
    ) {
      activeSection.value = sec
    }
  },
)
</script>

<template>
  <div class="module-learn-shell">
    <div class="top-bar">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ name: 'home' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>双指针学习</el-breadcrumb-item>
        <el-breadcrumb-item v-if="current">{{ shortTitle(current) }}</el-breadcrumb-item>
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
        <h1 class="hero-title">双指针学习模块</h1>
        <p class="hero-intro">{{ TWO_POINTERS_CURRICULUM_INTRO }}</p>
        <div class="hero-tags">
          <el-tag type="info" effect="plain" size="small">双指针篇</el-tag>
          <el-tag type="success" effect="plain" size="small">共 {{ TWO_POINTERS_SECTION_COUNT }} 节</el-tag>
        </div>
      </div>
    </div>

    <div class="module-layout-row layout-row">
      <SectionDirectoryAside
        :sections="TWO_POINTERS_SECTIONS"
        :active-section="activeSection"
        :done-map="doneMap"
        :section-index="sectionIndex"
        :section-count="TWO_POINTERS_SECTION_COUNT"
        aria-label="双指针章节"
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
            <el-tag v-if="current.pointerKind" type="warning" effect="plain" round size="small">
              {{ pointerKindLabel(current.pointerKind) }}
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

          <ModuleGameEntry module-key="two-pointers" :section-id="current.id" />

          <div class="content-visual">
            <Transition name="tp-anim-fade" mode="out-in">
              <TwoPointersSectionAnimation :key="current.id" :section-id="current.id" />
            </Transition>
          </div>

          <LearnSectionBody v-if="current" :section="current" />

          <SelectableLearnText v-if="current" :section-id="current.id">
          <template v-if="current.id === 'theory'">
            <el-divider content-position="left">
              <span class="divider-label">三种形态速查</span>
            </el-divider>
            <p class="table-hint">与 总结篇一致：先选对指针形态，再套具体题目的移动规则。</p>
            <div class="table-wrap">
              <el-table :data="TWO_POINTER_PATTERN_GUIDE" stripe border size="small" class="guide-table">
                <el-table-column prop="pattern" label="形态" width="120" />
                <el-table-column prop="when" label="适用场景" min-width="200" />
                <el-table-column prop="move" label="移动规则" min-width="200" />
                <el-table-column prop="examples" label="本篇例题" min-width="140" />
              </el-table>
            </div>
          </template>

          <template v-if="current.id === 'summary'">
            <el-divider content-position="left">
              <span class="divider-label">哈希 vs 双指针</span>
            </el-divider>
            <p class="table-hint">需注意：454 用哈希；15/18 用排序+双指针；两数之和若返回下标则不宜排序双指针。</p>
            <div class="table-wrap">
              <el-table :data="HASH_VS_TWO_POINTERS_COMPARE" stripe border size="small" class="guide-table">
                <el-table-column prop="dimension" label="维度" width="140" />
                <el-table-column prop="hashSide" label="哈希思路" min-width="200" />
                <el-table-column prop="twoPointerSide" label="双指针思路" min-width="220" />
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

        </el-card>

        <section v-if="current?.main" class="inline-oj-zone">
          <el-divider content-position="left">
            <span class="divider-label">主刷题 · 在线练习</span>
          </el-divider>
          <InlineOjPractice :main="current.main" :related="current.related" />
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

      <AiTutorPanel
        ref="aiTutorRef"
        module-key="two-pointers"
        module-title="双指针学习模块"
        chapter-tag="双指针篇"
        :module-intro="TWO_POINTERS_CURRICULUM_INTRO"
        :section="current ?? null"
      />
    </div>
  </div>
</template>

<style scoped>
.tp-anim-fade-enter-active,
.tp-anim-fade-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}

.tp-anim-fade-enter-from,
.tp-anim-fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

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
</style>
