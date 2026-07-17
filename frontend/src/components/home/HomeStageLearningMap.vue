<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowRight, Check } from '@element-plus/icons-vue'
import {
  ALGORITHM_MODULES,
  MODULE_PHASE_LABELS,
  type ModulePhase,
} from '@/constants/modules'
import { getModuleProgressPercent } from '@/utils/moduleProgressSummary'

const props = defineProps<{
  activeKey: string
  overallPercent: number
}>()

const emit = defineEmits<{
  preview: [key: string]
  open: [key: string]
}>()

const phaseSummary: Record<ModulePhase, string> = {
  foundation: '数组、链表、哈希与字符串',
  technique: '双指针、栈队列与排序',
  tree: '递归、树结构与搜索空间',
  advanced: '贪心、动态规划与图论',
}

const phaseGroups = computed(() =>
  (Object.keys(MODULE_PHASE_LABELS) as ModulePhase[]).map((phase) => ({
    phase,
    label: MODULE_PHASE_LABELS[phase],
    summary: phaseSummary[phase],
    modules: ALGORITHM_MODULES.filter((module) => module.phase === phase).map((module) => ({
      ...module,
      progress: getModuleProgressPercent(module.key),
    })),
  })),
)

const activePhase = computed(
  () => ALGORITHM_MODULES.find((module) => module.key === props.activeKey)?.phase ?? 'foundation',
)
const expandedPhases = ref<ModulePhase[]>([activePhase.value])

watch(activePhase, (phase) => {
  if (!expandedPhases.value.includes(phase)) {
    expandedPhases.value = [...expandedPhases.value, phase]
  }
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
        :class="{
          'is-current': group.modules.some((module) => module.key === activeKey),
          'is-open': phaseIsOpen(group.phase),
        }"
      >
        <header>
          <button
            type="button"
            :aria-expanded="phaseIsOpen(group.phase)"
            @click="togglePhase(group.phase)"
          >
            <span>
              <h3>{{ group.label }}</h3>
              <p>{{ group.summary }}</p>
            </span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </header>

        <ol>
          <li v-for="module in group.modules" :key="module.key">
            <button
              type="button"
              class="learning-map__module"
              :class="{
                'is-active': module.key === activeKey,
                'is-done': module.progress === 100,
                'has-progress': module.progress > 0 && module.progress < 100,
              }"
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
              <span
                v-if="module.key === activeKey || (module.progress > 0 && module.progress < 100)"
                class="learning-map__progress"
              >
                {{ module.progress }}%
              </span>
              <el-icon class="learning-map__arrow"><ArrowRight /></el-icon>
            </button>
          </li>
        </ol>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.learning-map {
  margin-top: 28px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-surface);
}

.learning-map__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 24px 18px;
  border-bottom: 1px solid var(--color-border);
}

.learning-map__head h2 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
}

.learning-map__head p {
  margin: 4px 0 0;
  color: var(--color-text-muted);
  font-size: 12px;
}

.learning-map__head > button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 2px;
  color: var(--color-brand);
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.learning-map__phases {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0;
  padding: 0;
  list-style: none;
}

.learning-map__phase {
  min-width: 0;
  padding: 20px 16px 22px;
  border-right: 1px solid var(--color-border);
}

.learning-map__phase:last-child {
  border-right: 0;
}

.learning-map__phase.is-current {
  background: var(--color-brand-soft);
  box-shadow: inset 3px 0 0 var(--color-brand);
}

.learning-map__phase > header {
  min-height: 58px;
  padding: 0 4px 14px;
  border-bottom: 1px solid var(--color-border);
}

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

.learning-map__phase > header > button > .el-icon {
  display: none;
  color: var(--color-text-muted);
  font-size: 11px;
}

.learning-map__phase h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 15px;
}

.learning-map__phase header p {
  margin: 4px 0 0;
  color: var(--color-text-muted);
  font-size: 11px;
  line-height: 1.45;
}

.learning-map__phase > ol {
  display: grid;
  gap: 3px;
  margin: 0;
  padding: 12px 0 0;
  list-style: none;
}

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
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  transition: background-color 160ms ease, border-color 160ms ease;
}

.learning-map__module:hover {
  background: var(--color-bg-subtle);
}

.learning-map__module.is-active {
  border-color: var(--color-border-strong);
  background: var(--color-bg-surface);
}

.learning-map__module.is-done {
  color: var(--color-text-secondary);
}

.learning-map__index {
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
  border: 1px solid var(--color-border);
  border-radius: 50%;
}

.learning-map__module.is-done .learning-map__index {
  color: var(--color-success);
  border-color: color-mix(in srgb, var(--color-success) 48%, var(--color-border));
}

.learning-map__module.is-active .learning-map__index,
.learning-map__module.has-progress .learning-map__index {
  color: var(--color-brand);
  border-color: var(--color-brand);
}

.learning-map__copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.learning-map__copy strong {
  overflow: hidden;
  font-size: 12px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.learning-map__copy small {
  margin-top: 2px;
  color: var(--color-text-muted);
  font-size: 10px;
}

.learning-map__module.is-active .learning-map__copy strong {
  color: var(--color-brand-dark);
}

.learning-map__progress {
  color: var(--color-brand);
  font-size: 10px;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

.learning-map__arrow {
  color: var(--color-text-muted);
  font-size: 11px;
  opacity: 0;
  transition: opacity 160ms ease, transform 160ms ease;
}

.learning-map__module:hover .learning-map__arrow,
.learning-map__module.is-active .learning-map__arrow {
  opacity: 1;
  transform: translateX(2px);
}

@media (max-width: 1120px) {
  .learning-map__phases {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .learning-map__phase:nth-child(2) {
    border-right: 0;
  }

  .learning-map__phase:nth-child(-n + 2) {
    border-bottom: 1px solid var(--color-border);
  }
}

@media (max-width: 680px) {
  .learning-map__head {
    padding: 19px 17px 16px;
  }

  .learning-map__phases {
    grid-template-columns: 1fr;
  }

  .learning-map__phase,
  .learning-map__phase:nth-child(2) {
    padding: 18px 14px;
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .learning-map__phase:last-child {
    border-bottom: 0;
  }

  .learning-map__phase > header {
    min-height: 0;
  }

  .learning-map__phase > header > button {
    cursor: pointer;
  }

  .learning-map__phase > header > button > .el-icon {
    display: block;
    transition: transform 160ms ease;
  }

  .learning-map__phase.is-open > header > button > .el-icon {
    transform: rotate(90deg);
  }

  .learning-map__phase:not(.is-open) > ol {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .learning-map__module,
  .learning-map__arrow {
    transition: none;
  }
}
</style>
