<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, QuestionFilled, Reading, Trophy } from '@element-plus/icons-vue'
import {
  FAQ_CATEGORIES,
  HELP_COMPETITION,
  HELP_FAQ,
  HELP_GUIDE_STEPS,
  HELP_QUICK_LINKS,
  HELP_TABS,
  faqByCategory,
  type HelpTabId,
} from '@/constants/helpContent'

const route = useRoute()
const router = useRouter()

const activeTab = ref<HelpTabId>('guide')
const expandedFaq = ref<string[]>([])

function tabFromQuery(): HelpTabId | null {
  const q = route.query.tab
  if (typeof q === 'string' && HELP_TABS.some((t) => t.id === q)) {
    return q as HelpTabId
  }
  return null
}

function syncTabFromRoute() {
  const fromQuery = tabFromQuery()
  if (fromQuery) {
    activeTab.value = fromQuery
    return
  }
  if (route.hash === '#faq') {
    activeTab.value = 'faq'
  } else if (route.hash === '#competition') {
    activeTab.value = 'competition'
  }
}

onMounted(() => {
  syncTabFromRoute()
  expandedFaq.value = HELP_FAQ.slice(0, 2).map((item) => item.id)
})

watch(() => route.query.tab, syncTabFromRoute)
watch(() => route.hash, syncTabFromRoute)

function onTabChange(name: string | number) {
  const tab = String(name) as HelpTabId
  activeTab.value = tab
  router.replace({ query: { ...route.query, tab } })
}

function goTo(link: { name: string; query?: Record<string, string> }) {
  router.push(link)
}
</script>

<template>
  <el-card shadow="never" class="page-card">
    <el-page-header title="帮助中心" @back="router.push({ name: 'home' })" />
    <el-divider />

    <p class="muted">
      汇集平台使用指南、常见问题与软件杯 A3 赛题说明。如需快速上手，可从下方入口直达各功能模块。
    </p>

    <el-row :gutter="16" class="quick-row">
      <el-col
        v-for="link in HELP_QUICK_LINKS"
        :key="link.key"
        :xs="24"
        :sm="12"
        :lg="8"
      >
        <div
          class="quick-card hover-card"
          role="button"
          tabindex="0"
          @click="goTo(link.route)"
          @keydown.enter.prevent="goTo(link.route)"
        >
          <el-icon class="quick-icon"><component :is="link.icon" /></el-icon>
          <div class="quick-body">
            <div class="quick-title">{{ link.title }}</div>
            <p class="quick-desc">{{ link.desc }}</p>
          </div>
          <el-icon class="quick-arrow"><ArrowRight /></el-icon>
        </div>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" class="help-tabs" @tab-change="onTabChange">
      <el-tab-pane label="使用指南" name="guide">
        <div class="section-head">
          <el-icon class="section-icon"><Reading /></el-icon>
          <div>
            <h3 class="section-title">六步上手流程</h3>
            <p class="section-sub">按顺序完成以下步骤，即可体验完整的个性化学习闭环。</p>
          </div>
        </div>

        <el-timeline class="guide-timeline">
          <el-timeline-item
            v-for="step in HELP_GUIDE_STEPS"
            :key="step.step"
            :timestamp="`步骤 ${step.step}`"
            placement="top"
            type="primary"
            hollow
          >
            <div class="guide-step">
              <h4 class="guide-step-title">{{ step.title }}</h4>
              <p class="guide-step-desc">{{ step.desc }}</p>
              <el-button
                v-if="step.route"
                type="primary"
                link
                @click="goTo(step.route)"
              >
                {{ step.routeLabel ?? '立即前往' }}
                <el-icon class="btn-arrow"><ArrowRight /></el-icon>
              </el-button>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-tab-pane>

      <el-tab-pane label="常见问题" name="faq">
        <div class="section-head">
          <el-icon class="section-icon"><QuestionFilled /></el-icon>
          <div>
            <h3 class="section-title">常见问题</h3>
            <p class="section-sub">共 {{ HELP_FAQ.length }} 条，按主题分类整理。</p>
          </div>
        </div>

        <div v-for="category in FAQ_CATEGORIES" :key="category" class="faq-group">
          <h4 class="faq-category">{{ category }}</h4>
          <el-collapse v-model="expandedFaq" class="faq-collapse">
            <el-collapse-item
              v-for="item in faqByCategory(category)"
              :key="item.id"
              :name="item.id"
              :title="item.question"
            >
              <p class="faq-answer">{{ item.answer }}</p>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-tab-pane>

      <el-tab-pane label="赛题说明" name="competition">
        <div class="section-head">
          <el-icon class="section-icon"><Trophy /></el-icon>
          <div>
            <h3 class="section-title">软件杯 A3 赛题说明</h3>
            <p class="section-sub">算法智能学习平台 — 多智能体个性化学习系统。</p>
          </div>
        </div>

        <el-alert
          title="中国软件杯 · A3 赛道"
          type="info"
          show-icon
          :closable="false"
          class="comp-alert"
        >
          本平台以多 Agent 编排驱动个性化学习全流程，涵盖画像、路径、资源生成与在线判题。
        </el-alert>

        <div v-for="section in HELP_COMPETITION" :key="section.title" class="comp-section">
          <h4 class="comp-title">{{ section.title }}</h4>
          <ul class="comp-list">
            <li v-for="(line, idx) in section.items" :key="idx">{{ line }}</li>
          </ul>
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

.quick-row {
  margin-bottom: 24px;
}

.quick-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 16px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  height: calc(100% - 16px);
}

.quick-card:hover,
.quick-card:focus-visible {
  border-color: var(--alp-color-primary);
  background: rgba(56, 189, 248, 0.06);
  outline: none;
}

.quick-icon {
  font-size: 22px;
  color: var(--alp-color-primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.quick-body {
  flex: 1;
  min-width: 0;
}

.quick-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--alp-color-text);
  margin-bottom: 4px;
}

.quick-desc {
  margin: 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.55;
}

.quick-arrow {
  color: var(--alp-color-muted);
  flex-shrink: 0;
  margin-top: 4px;
  transition: transform 0.2s;
}

.quick-card:hover .quick-arrow {
  transform: translateX(3px);
  color: var(--alp-color-primary);
}

.help-tabs {
  margin-top: 4px;
}

.section-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-icon {
  font-size: 24px;
  color: var(--alp-color-primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.section-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.section-sub {
  margin: 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.5;
}

.guide-timeline {
  padding-left: 4px;
}

.guide-step-title {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.guide-step-desc {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.65;
}

.btn-arrow {
  margin-left: 2px;
}

.faq-group {
  margin-bottom: 20px;
}

.faq-category {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--alp-color-primary);
}

.faq-collapse {
  border: none;
}

.faq-answer {
  margin: 0;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.65;
}

.comp-alert {
  margin-bottom: 20px;
}

.comp-section {
  margin-bottom: 22px;
  padding: 16px 18px;
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.comp-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--alp-color-text);
}

.comp-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: var(--alp-color-muted);
  line-height: 1.75;
}

.comp-list li + li {
  margin-top: 6px;
}
</style>
