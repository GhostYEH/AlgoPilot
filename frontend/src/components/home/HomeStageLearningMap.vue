<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowRight, Check, Lightning, Promotion, CollectionTag, Opportunity } from '@element-plus/icons-vue'
import { ALGORITHM_MODULES, MODULE_PHASE_LABELS, type ModulePhase } from '@/constants/modules'
import { getModuleLearnConfig } from '@/modules/shared/moduleRegistry'
import { getModuleProgressPercent } from '@/utils/moduleProgressSummary'

const props = defineProps<{ activeKey: string; overallPercent: number }>()
const emit = defineEmits<{ preview: [key: string]; open: [key: string] }>()

const phaseSummary: Record<ModulePhase, string> = {
  foundation: '数组、链表、哈希与字符串',
  technique: '双指针、栈队列与排序',
  tree: '递归、树结构与搜索空间',
  advanced: '贪心、动态规划与图论',
}

function sectionTitle(title: string) {
  return title.replace(/^\d+[.、]\s*/, '')
}

const phaseGroups = computed(() =>
  (Object.keys(MODULE_PHASE_LABELS) as ModulePhase[]).map((phase) => ({
    phase,
    label: MODULE_PHASE_LABELS[phase],
    summary: phaseSummary[phase],
    modules: ALGORITHM_MODULES.filter((module) => module.phase === phase).map((module) => {
      const progress = getModuleProgressPercent(module.key)
      const config = getModuleLearnConfig(module.key)
      const doneMap = config?.loadSectionDone() ?? {}
      const completedCount = Object.values(doneMap).filter(Boolean).length
      const sections = (config?.sections ?? []).slice(0, 4).map((section, index) => ({
        id: section.id,
        title: sectionTitle(section.title),
        done: Boolean(doneMap[section.id]),
        status: doneMap[section.id]
          ? '已完成'
          : progress > 0 && index === completedCount
            ? '正在学习'
            : progress > 0
              ? '待复习'
              : '未开始',
      }))
      return {
        ...module,
        progress,
        sections,
        hiddenSectionCount: Math.max(0, (config?.sections.length ?? 0) - sections.length),
      }
    }),
  })),
)

const activePhase = computed(
  () => ALGORITHM_MODULES.find((module) => module.key === props.activeKey)?.phase ?? 'foundation',
)
const expandedPhases = ref<ModulePhase[]>([activePhase.value])

watch(activePhase, (phase) => {
  if (!expandedPhases.value.includes(phase)) expandedPhases.value = [...expandedPhases.value, phase]
})

function phaseIsOpen(phase: ModulePhase) {
  return expandedPhases.value.includes(phase)
}

function togglePhase(phase: ModulePhase) {
  expandedPhases.value = phaseIsOpen(phase)
    ? expandedPhases.value.filter((item) => item !== phase)
    : [...expandedPhases.value, phase]
}

function statusLabel(progress: number, active: boolean) {
  if (progress === 100) return '已完成'
  if (active) return '正在学习'
  if (progress > 0) return '待复习'
  return '未开始'
}

function stepNumber(key: string) {
  return String(ALGORITHM_MODULES.findIndex((module) => module.key === key) + 1).padStart(2, '0')
}

const phaseIcons = { foundation: CollectionTag, technique: Lightning, tree: Opportunity, advanced: Promotion }
</script>

<template>
  <section class="learning-map" aria-labelledby="learning-map-title">
    <header class="learning-map__head">
      <div>
        <h2 id="learning-map-title">学习路径</h2>
        <p>共 {{ ALGORITHM_MODULES.length }} 个模块，当前学习进度 {{ overallPercent }}%。</p>
      </div>
      <button type="button" @click="emit('open', activeKey)">
        打开当前模块
        <el-icon><ArrowRight /></el-icon>
      </button>
    </header>

    <ol class="learning-map__phases">
      <li
        v-for="group in phaseGroups"
        :key="group.phase"
        class="learning-map__phase"
        :class="{ 'is-current': group.modules.some((module) => module.key === activeKey), 'is-open': phaseIsOpen(group.phase) }"
      >
        <header>
          <button type="button" :aria-expanded="phaseIsOpen(group.phase)" @click="togglePhase(group.phase)">
            <span class="learning-map__phase-copy">
              <span class="learning-map__phase-mark"><el-icon><component :is="phaseIcons[group.phase]" /></el-icon></span>
              <span>
                <h3>{{ group.label }}</h3>
                <p>{{ group.summary }}</p>
              </span>
            </span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </header>

        <ol>
          <li v-for="module in group.modules" :key="module.key">
            <button
              type="button"
              class="learning-map__module"
              :class="{ 'is-active': module.key === activeKey, 'is-done': module.progress === 100, 'has-progress': module.progress > 0 && module.progress < 100 }"
              :aria-current="module.key === activeKey ? 'step' : undefined"
              @mouseenter="emit('preview', module.key)"
              @focus="emit('preview', module.key)"
              @click="emit('open', module.key)"
            >
              <span class="learning-map__index">
                <el-icon v-if="module.progress === 100"><Check /></el-icon>
                <template v-else>{{ stepNumber(module.key) }}</template>
              </span>
              <span class="learning-map__copy">
                <strong>{{ module.label }}</strong>
                <small>{{ statusLabel(module.progress, module.key === activeKey) }}</small>
              </span>
              <span v-if="module.key === activeKey || (module.progress > 0 && module.progress < 100)" class="learning-map__progress">
                {{ module.progress }}%
              </span>
              <el-icon class="learning-map__arrow"><ArrowRight /></el-icon>
            </button>

            <div v-if="module.key === activeKey && module.sections.length" class="learning-map__sections">
              <div v-for="section in module.sections" :key="section.id" class="learning-map__section">
                <span class="learning-map__section-dot" :class="{ 'is-done': section.done }">
                  <el-icon v-if="section.done"><Check /></el-icon>
                </span>
                <span class="learning-map__section-copy">
                  <strong>{{ section.title }}</strong>
                  <small>{{ section.status }}</small>
                </span>
                <span class="learning-map__section-status">{{ section.done ? '100%' : section.status }}</span>
              </div>
              <span v-if="module.hiddenSectionCount" class="learning-map__more">
                还有 {{ module.hiddenSectionCount }} 个小节 · 进入模块查看
              </span>
            </div>
          </li>
        </ol>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.learning-map {
  margin-top: 16px;
  overflow: visible;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: var(--color-bg-surface);
  box-shadow: 0 6px 18px rgba(28, 89, 90, 0.035);
}
.learning-map__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 12px 26px 8px;
  border-bottom: 0;
}
.learning-map__head h2 { margin: 0; color: var(--color-text-primary); font-size: 20px; font-weight: 750; }
.learning-map__head p:not(.learning-map__eyebrow) { margin: 5px 0 0; color: var(--color-text-muted); font-size: 12px; }
.learning-map__head > button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 2px;
  color: var(--color-brand);
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  border: 0;
  background: transparent;
  cursor: pointer;
}
.learning-map__head > button .el-icon { transition: transform 180ms ease; }
.learning-map__head > button:hover .el-icon { transform: translateX(3px); }
.learning-map__phases {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0;
  gap: 14px;
  padding: 0 26px 16px;
  list-style: none;
}
.learning-map__phase { min-width: 0; padding: 14px 12px 10px; border: 1px solid #e4eeee; border-radius: 14px; background: #fff; box-shadow: 0 3px 12px rgba(28, 89, 90, .025); }
.learning-map__phase.is-current { background: #fff; box-shadow: 0 3px 12px rgba(28, 89, 90, .025); }
.learning-map__phase > header { min-height: 48px; padding: 0 4px 9px; border-bottom: 1px solid var(--color-border); }
.learning-map__phase > header > button {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 14px;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 0;
  color: inherit;
  text-align: left;
  border: 0;
  background: transparent;
}
.learning-map__phase > header > button > .el-icon { display: none; color: var(--color-text-muted); font-size: 11px; }
.learning-map__phase-copy { display: flex; align-items: center; gap: 9px; }
.learning-map__phase-mark {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  color: #49a861;
  font-size: 19px;
  font-weight: 800;
  border-radius: 50%;
  background: #eff9e9;
}
.learning-map__phase:nth-child(2) .learning-map__phase-mark { color: #218dc8; background: #e7f5fd; }
.learning-map__phase:nth-child(3) .learning-map__phase-mark { color: #158a86; background: #e5f7f4; }
.learning-map__phase:nth-child(4) .learning-map__phase-mark { color: #8660ce; background: #f0eaff; }
.learning-map__phase h3 { margin: 0; color: var(--color-text-primary); font-size: 15px; font-weight: 750; }
.learning-map__phase header p { margin: 4px 0 0; color: var(--color-text-muted); font-size: 11px; line-height: 1.45; }
.learning-map__phase > ol { display: grid; gap: 3px; margin: 0; padding: 7px 0 0; list-style: none; }
.learning-map__module {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) auto 14px;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 52px;
  padding: 7px 8px;
  color: var(--color-text-primary);
  text-align: left;
  border: 1px solid transparent;
  border-radius: 11px;
  background: transparent;
  cursor: pointer;
  transition: background-color 180ms ease, border-color 180ms ease, transform 180ms ease;
}
.learning-map__module:hover { background: var(--color-bg-subtle); transform: translateX(2px); }
.learning-map__module.is-active { border-color: #8ed7d2; background: #f1fbfa; box-shadow: none; }
.learning-map__module.is-done { color: var(--color-text-secondary); }
.learning-map__index {
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 800;
  border: 1px solid var(--color-border);
  border-radius: 50%;
}
.learning-map__module.is-done .learning-map__index { color: var(--color-success); border-color: color-mix(in srgb, var(--color-success) 48%, var(--color-border)); }
.learning-map__module.is-active .learning-map__index,
.learning-map__module.has-progress .learning-map__index { color: var(--color-brand); border-color: var(--color-brand); box-shadow: 0 0 0 4px rgba(15, 133, 136, 0.07); }
.learning-map__copy, .learning-map__section-copy { display: flex; min-width: 0; flex-direction: column; }
.learning-map__copy strong { overflow: hidden; font-size: 12px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.learning-map__copy small, .learning-map__section-copy small { margin-top: 2px; color: var(--color-text-muted); font-size: 10px; }
.learning-map__module.is-active .learning-map__copy strong { color: var(--color-brand-dark); }
.learning-map__progress { color: var(--color-brand); font-size: 10px; font-weight: 750; font-variant-numeric: tabular-nums; }
.learning-map__arrow { color: var(--color-text-muted); font-size: 11px; opacity: 0; transition: opacity 180ms ease, transform 180ms ease; }
.learning-map__module:hover .learning-map__arrow, .learning-map__module.is-active .learning-map__arrow { opacity: 1; transform: translateX(2px); }
.learning-map__sections { display: grid; gap: 2px; margin: 0 8px 8px 46px; padding: 8px 10px 7px; border-left: 1px solid #b9dedb; border-radius: 0 10px 10px 0; background: rgba(239, 249, 248, 0.75); }
.learning-map__section { display: grid; grid-template-columns: 14px minmax(0, 1fr) auto; align-items: center; gap: 6px; min-width: 0; padding: 5px 0; }
.learning-map__section-dot {
  display: grid;
  width: 12px;
  height: 12px;
  place-items: center;
  color: #fff;
  font-size: 8px;
  border: 1px solid #b9d7d5;
  border-radius: 50%;
  background: #fff;
}
.learning-map__section-dot.is-done { border-color: var(--color-brand); background: var(--color-brand); }
.learning-map__section-copy strong { overflow: hidden; color: var(--color-text-primary); font-size: 10px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.learning-map__section-status { color: var(--color-brand); font-size: 9px; white-space: nowrap; }
.learning-map__more { padding-top: 5px; color: var(--color-text-muted); font-size: 9px; border-top: 1px solid rgba(185, 222, 219, 0.72); }

@media (min-width: 1800px) {
  .learning-map { margin-top: 20px; }
  .learning-map__head { gap: 28px; padding: 16px 30px 11px; }
  .learning-map__head h2 { font-size: 22px; }
  .learning-map__head p:not(.learning-map__eyebrow), .learning-map__head > button { font-size: 13px; }
  .learning-map__phases { gap: 18px; padding: 0 30px 20px; }
  .learning-map__phase { padding: 17px 15px 13px; }
  .learning-map__phase > header { min-height: 54px; padding-bottom: 11px; }
  .learning-map__phase-copy { gap: 11px; }
  .learning-map__phase-mark { width: 32px; height: 32px; font-size: 21px; }
  .learning-map__phase h3 { font-size: 16px; }
  .learning-map__phase header p { font-size: 12px; }
  .learning-map__phase > ol { gap: 4px; padding-top: 9px; }
  .learning-map__module { grid-template-columns: 34px minmax(0,1fr) auto 16px; gap: 10px; min-height: 58px; padding: 8px 10px; }
  .learning-map__index { width: 29px; height: 29px; font-size: 11px; }
  .learning-map__copy strong { font-size: 13px; }
  .learning-map__copy small, .learning-map__section-copy small, .learning-map__progress { font-size: 11px; }
  .learning-map__sections { gap: 3px; margin: 1px 10px 10px 52px; padding: 10px 12px 9px; }
  .learning-map__section { padding: 6px 0; }
  .learning-map__section-copy strong { font-size: 11px; }
  .learning-map__section-status, .learning-map__more { font-size: 10px; }
}

@media (max-width: 1120px) {
  .learning-map__phases { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .learning-map__phase:nth-child(2) { border-right: 0; }
  .learning-map__phase:nth-child(-n + 2) { border-bottom: 1px solid var(--color-border); }
}
@media (max-width: 680px) {
  .learning-map__head { padding: 19px 17px 16px; }
  .learning-map__phases { grid-template-columns: 1fr; padding-inline: 0; }
  .learning-map__phase, .learning-map__phase:nth-child(2) { padding: 18px 14px; border-right: 0; border-bottom: 1px solid var(--color-border); }
  .learning-map__phase:last-child { border-bottom: 0; }
  .learning-map__phase > header { min-height: 0; }
  .learning-map__phase > header > button { cursor: pointer; }
  .learning-map__phase > header > button > .el-icon { display: block; transition: transform 180ms ease; }
  .learning-map__phase.is-open > header > button > .el-icon { transform: rotate(90deg); }
  .learning-map__phase:not(.is-open) > ol { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .learning-map__module, .learning-map__arrow, .learning-map__head > button .el-icon { transition: none; }
}
</style>
