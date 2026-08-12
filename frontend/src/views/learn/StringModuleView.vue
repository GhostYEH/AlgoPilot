<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  CopyDocument,
  Reading,
  TrendCharts,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  STRING_CURRICULUM_INTRO,
  STRING_SECTIONS,
  STRING_SECTION_COUNT,
  type StringSection,
  type StringPracticeLink,
} from '@/modules/string/stringCurriculum'
import { loadSectionDone, toggleSectionDone } from '@/modules/string/stringProgress'
import StringSectionAnimation from '@/modules/string/components/StringSectionAnimation.vue'
import AiTutorPanel from '@/components/learning/AiTutorPanel.vue'
import InlineOjPractice from '@/components/oj/InlineOjPractice.vue'
import LearnSectionBody from '@/components/learning/LearnSectionBody.vue'
import ModuleGameEntry from '@/components/learning/ModuleGameEntry.vue'
import SelectableLearnText from '@/components/learning/SelectableLearnText.vue'
import { stableAnimationWindow as vStableAnimationWindow } from '@/directives/stableAnimationWindow'
import SectionDirectoryAside from '@/components/learning/SectionDirectoryAside.vue'
import { useProvideAiTutorFromPanel } from '@/composables/useProvideAiTutorFromPanel'
import { isLoggedIn } from '@/stores/auth'
import { applyRemoteProgressPayload } from '@/utils/learningStorage'
import { schedulePushLearningProgress } from '@/utils/learningRemoteSync'
import { schedulePersonaLearningPatch } from '@/utils/personaLearningSync'

const router = useRouter()
const route = useRoute()

const aiTutorRef = ref<InstanceType<typeof AiTutorPanel> | null>(null)
useProvideAiTutorFromPanel(aiTutorRef)

const activeSection = ref(STRING_SECTIONS[0]?.id ?? 'theory')
const doneMap = ref<Record<string, boolean>>({})

const current = computed(() => STRING_SECTIONS.find((s) => s.id === activeSection.value))

const sectionIndex = computed(() =>
  STRING_SECTIONS.findIndex((s) => s.id === activeSection.value),
)

const progressPercent = computed(() => {
  const done = STRING_SECTIONS.filter((s) => doneMap.value[s.id]).length
  return Math.round((done / STRING_SECTION_COUNT) * 100)
})

const prevSection = computed(() => {
  const i = sectionIndex.value
  return i > 0 ? STRING_SECTIONS[i - 1] : null
})

const nextSection = computed(() => {
  const i = sectionIndex.value
  return i >= 0 && i < STRING_SECTIONS.length - 1 ? STRING_SECTIONS[i + 1] : null
})

const sectionDone = computed(() => !!doneMap.value[activeSection.value])

function difficultyType(d: StringSection['difficulty']) {
  if (d === '入门') return 'success'
  if (d === '基础') return 'primary'
  return 'warning'
}

function shortTitle(s: StringSection) {
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
  if (v) {
    schedulePersonaLearningPatch({
      event_type: 'section_done',
      module_key: 'string',
      detail: id,
    })
  }
}

function practiceLinkLabel(p: StringPracticeLink) {
  if (p.badge) return p.badge
  return `力扣 ${p.id}`
}

async function copySectionLink() {
  const path = router.resolve({
    name: 'learn-string',
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
  if (sec && STRING_SECTIONS.some((s) => s.id === sec)) {
    activeSection.value = sec
  } else {
    router.replace({ name: 'learn-string', query: { section: activeSection.value } })
  }
})

watch(activeSection, (id) => {
  if (route.query.section === id) return
  router.replace({ name: 'learn-string', query: { section: id } })
})

watch(
  () => route.query.section,
  (sec) => {
    if (typeof sec === 'string' && STRING_SECTIONS.some((s) => s.id === sec) && sec !== activeSection.value) {
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
        <el-breadcrumb-item>字符串学习</el-breadcrumb-item>
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
          style="width: 160px"
        />
        <el-button size="small" :icon="CopyDocument" @click="copySectionLink">复制本节链接</el-button>
      </div>
    </div>

    <div class="hero">
      <div class="hero-main">
        <el-button text type="primary" class="back-btn" :icon="ArrowLeft" @click="goHome">返回首页</el-button>
        <h1 class="hero-title">字符串学习模块</h1>
        <p class="hero-intro">{{ STRING_CURRICULUM_INTRO }}</p>
        <div class="hero-tags">
          <el-tag type="info" effect="plain" size="small">字符串篇</el-tag>
          <el-tag type="success" effect="plain" size="small">共 {{ STRING_SECTION_COUNT }} 节</el-tag>
        </div>
      </div>
    </div>

    <div class="module-layout-row layout-row">
      <SectionDirectoryAside
        :sections="STRING_SECTIONS"
        :active-section="activeSection"
        :done-map="doneMap"
        :section-index="sectionIndex"
        :section-count="STRING_SECTION_COUNT"
        aria-label="字符串章节"
        @select="selectSection"
      />

      <div class="module-layout-main">
        <el-card v-if="current" shadow="never" class="content-card">
          <Transition name="section-swap" mode="out-in">
            <div :key="activeSection" class="section-body">
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

              <ModuleGameEntry module-key="string" :section-id="current.id" />

              <div
                class="content-visual"
                v-stable-animation-window="`string:${current.id}`"
              >
                <StringSectionAnimation :section-id="current.id" />
              </div>

              <LearnSectionBody :section="current" />

              <SelectableLearnText :section-id="current.id">
              <template v-if="current.pitfalls?.length">
                <el-divider content-position="left">
                  <span class="divider-label">易错点</span>
                </el-divider>
                <TransitionGroup name="alert-stagger" tag="div" class="pitfall-group">
                  <el-alert
                    v-for="(t, idx) in current.pitfalls"
                    :key="`${idx}-${t.slice(0, 24)}`"
                    :title="t"
                    type="warning"
                    show-icon
                    :closable="false"
                    class="pitfall-alert"
                  />
                </TransitionGroup>
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

              <template v-if="current.id === 'theory'">
                <el-divider content-position="left">
                  <span class="divider-label">后续扩展</span>
                </el-divider>
                <p class="hint">
                  <el-icon><Reading /></el-icon>
                  可在此接入多智能体生成个性化题单、或对接题库统计字符串篇完成度（本地会保存进度；登录后将尝试同步到服务端）。
                </p>
              </template>
            </div>
          </Transition>
        </el-card>

        <section v-if="current?.main" class="inline-oj-zone">
          <el-divider content-position="left">
            <span class="divider-label">主刷题 · 在线练习</span>
          </el-divider>
          <InlineOjPractice
            :main="current.main"
            :related="current.related"
            :link-label="practiceLinkLabel"
          />
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
        <AiTutorPanel
          ref="aiTutorRef"
          module-key="string"
          module-title="字符串学习模块"
          chapter-tag="字符串篇"
          :module-intro="STRING_CURRICULUM_INTRO"
          :section="current ?? null"
        />
      </div>
    </div>
  </div>
</template>
