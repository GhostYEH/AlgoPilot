<script setup lang="ts">
import { computed } from 'vue'
import SelectableLearnText from '@/components/learning/SelectableLearnText.vue'
import type { LearnSection } from '@/modules/shared/learningTypes'

const props = withDefaults(
  defineProps<{
    section: LearnSection
    /** 动画下方正文：全宽 + 分主题三列（与理论基础三动画对齐） */
    belowViz?: boolean
    /** 动画左侧：右栏详解（栈队列等分步课） */
    sideViz?: boolean
  }>(),
  { belowViz: false, sideViz: false },
)

const hasTopics = computed(() => (props.section.topicBlocks?.length ?? 0) > 0)
const recallLabel = computed(() => (hasTopics.value ? '本章脉络（速记）' : '核心要点'))
</script>

<template>
  <SelectableLearnText :section-id="section.id">
  <div
    class="learn-section-body"
    :class="{
      'learn-section-body--below-viz': belowViz,
      'learn-section-body--side-viz': sideViz,
    }"
  >
    <p v-if="section.overview" class="section-overview">{{ section.overview }}</p>

    <template v-if="hasTopics">
      <el-divider content-position="left">
        <span class="divider-label">分主题详解</span>
      </el-divider>
      <div class="topic-blocks">
        <section
          v-for="(block, bi) in section.topicBlocks"
          :key="bi"
          class="topic-block"
        >
          <h3 class="topic-block-title">
            <span class="topic-block-index">{{ bi + 1 }}</span>
            {{ block.title }}
          </h3>
          <p v-if="block.intro" class="topic-block-intro">{{ block.intro }}</p>
          <ul class="topic-point-list">
            <li v-for="(p, pi) in block.points" :key="pi">{{ p }}</li>
          </ul>
        </section>
      </div>
    </template>

    <template v-if="section.points.length">
      <el-divider content-position="left">
        <span class="divider-label">{{ recallLabel }}</span>
      </el-divider>
      <div class="recall-panel" :class="{ 'recall-panel--solo': !hasTopics }">
        <ul class="recall-list">
          <li v-for="(p, idx) in section.points" :key="idx">{{ p }}</li>
        </ul>
      </div>
    </template>
  </div>
  </SelectableLearnText>
</template>

<style scoped>
.learn-section-body {
  max-width: 52rem;
}

.learn-section-body--below-viz {
  max-width: none;
  width: 100%;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--alp-color-border);
}

.learn-section-body--side-viz {
  max-width: none;
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 0 0 0 4px;
}

.learn-section-body--side-viz .section-overview {
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.learn-section-body--side-viz .topic-blocks {
  gap: 0.75rem;
}

.learn-section-body--side-viz .topic-block {
  padding: 0.75rem 0.875rem;
}

.learn-section-body--side-viz .el-divider {
  margin: 1rem 0 0.75rem;
}

.learn-section-body--below-viz .topic-blocks {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

@media (max-width: 960px) {
  .learn-section-body--below-viz .topic-blocks {
    grid-template-columns: 1fr;
  }
}

.section-overview {
  margin: 0 0 1.25rem;
  padding: 0.875rem 1rem;
  font-size: 0.9375rem;
  line-height: 1.75;
  color: var(--alp-color-text, #e2e8f0);
  background: color-mix(in srgb, var(--alp-color-primary, #409eff) 8%, transparent);
  border-left: 3px solid var(--alp-color-primary, #409eff);
  border-radius: 0 8px 8px 0;
}

.topic-blocks {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.topic-block {
  padding: 1rem 1.125rem;
  border-radius: 10px;
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.35));
  border: 1px solid var(--alp-color-border, rgba(148, 163, 184, 0.2));
}

.topic-block-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.625rem;
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.4;
  color: var(--alp-color-text, #f1f5f9);
}

.topic-block-index {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.375rem;
  height: 1.375rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--alp-color-primary, #38bdf8);
  background: color-mix(in srgb, var(--alp-color-primary, #38bdf8) 14%, transparent);
  border-radius: 6px;
}

.topic-block-intro {
  margin: 0 0 0.5rem;
  font-size: 0.8125rem;
  line-height: 1.65;
  color: var(--alp-color-muted, #94a3b8);
}

.topic-point-list {
  margin: 0;
  padding: 0 0 0 1.125rem;
  list-style: disc;
  font-size: 0.875rem;
  line-height: 1.7;
  color: var(--alp-color-text, #cbd5e1);
}

.topic-point-list li {
  margin: 0.35rem 0;
  padding: 0;
}

.topic-point-list li::marker {
  color: var(--alp-color-primary, #38bdf8);
}

.recall-panel {
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: var(--alp-bg-code-ish, rgba(15, 23, 42, 0.45));
  border: 1px dashed color-mix(in srgb, var(--alp-color-primary, #38bdf8) 35%, transparent);
}

.recall-panel--solo {
  border-style: solid;
  border-color: var(--alp-color-border, rgba(148, 163, 184, 0.2));
  background: transparent;
  padding: 0;
}

.recall-panel--solo .recall-list {
  display: grid;
  gap: 0.625rem;
}

.recall-panel--solo .recall-list li {
  padding: 0.6875rem 0.875rem 0.6875rem 2rem;
  border-radius: 10px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.recall-list {
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 0.875rem;
  line-height: 1.65;
  color: var(--alp-color-text, #e2e8f0);
}

.recall-list li {
  position: relative;
  margin: 0;
  padding: 0.4rem 0 0.4rem 1rem;
  border-bottom: 1px solid var(--alp-color-border, rgba(148, 163, 184, 0.12));
}

.recall-list li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.recall-list li:first-child {
  padding-top: 0;
}

.recall-panel--solo .recall-list li {
  border-bottom: none;
}

.recall-panel--solo .recall-list li::before {
  content: '';
  position: absolute;
  left: 0.875rem;
  top: 1.05em;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--alp-color-primary);
  box-shadow: 0 0 0 3px var(--alp-color-primary-soft, rgba(56, 189, 248, 0.2));
  transform: translateY(-50%);
}
</style>
