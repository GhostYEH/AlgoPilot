<script setup lang="ts">
import { computed } from 'vue'
import {
  Aim,
  ArrowRight,
  Check,
  Collection,
  Connection,
  DataAnalysis,
} from '@element-plus/icons-vue'
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

const phaseMeta: Record<ModulePhase, { summary: string; icon: typeof Collection }> = {
  foundation: { summary: '掌握高频数据结构', icon: Collection },
  technique: { summary: '建立通用解题模型', icon: Aim },
  tree: { summary: '理解递归与搜索空间', icon: Connection },
  advanced: { summary: '挑战综合算法问题', icon: DataAnalysis },
}

const phaseGroups = computed(() =>
  (Object.keys(MODULE_PHASE_LABELS) as ModulePhase[]).map((phase, index) => {
    const modules = ALGORITHM_MODULES.filter((module) => module.phase === phase).map((module) => ({
      ...module,
      progress: getModuleProgressPercent(module.key),
    }))
    const average = modules.length
      ? Math.round(modules.reduce((total, module) => total + module.progress, 0) / modules.length)
      : 0

    return {
      phase,
      index: index + 1,
      label: MODULE_PHASE_LABELS[phase],
      average,
      modules,
      ...phaseMeta[phase],
    }
  }),
)

const activeModule = computed(() => {
  const module = ALGORITHM_MODULES.find((item) => item.key === props.activeKey) ?? ALGORITHM_MODULES[0]
  return module ? { ...module, progress: getModuleProgressPercent(module.key) } : null
})

function stepNumber(key: string): string {
  const index = ALGORITHM_MODULES.findIndex((module) => module.key === key)
  return String(index + 1).padStart(2, '0')
}
</script>

<template>
  <section class="stage-map" aria-labelledby="stage-map-title">
    <header class="stage-map__header">
      <div class="stage-map__heading">
        <div class="stage-map__title-row">
          <h2 id="stage-map-title">阶段层学习地图</h2>
          <span>{{ ALGORITHM_MODULES.length }} 个学习模块</span>
        </div>
        <p>沿着四个阶段循序推进，点击任意知识点进入对应的详细学习界面。</p>
      </div>
      <div class="stage-map__overall" aria-label="总学习进度">
        <div><span>总进度</span><strong>{{ overallPercent }}%</strong></div>
        <div class="stage-map__overall-track" aria-hidden="true">
          <i :style="{ width: `${overallPercent}%` }" />
        </div>
      </div>
    </header>

    <div class="stage-map__canvas">
      <ol class="stage-map__phases">
        <li v-for="group in phaseGroups" :key="group.phase" class="stage-map__phase">
          <header class="stage-map__phase-head">
            <span class="stage-map__phase-number">阶段 {{ group.index }}</span>
            <el-icon aria-hidden="true"><component :is="group.icon" /></el-icon>
            <div>
              <h3>{{ group.label }}</h3>
              <p>{{ group.summary }}</p>
            </div>
            <strong>{{ group.average }}%</strong>
          </header>

          <ol class="stage-map__nodes">
            <li v-for="module in group.modules" :key="module.key">
              <button
                type="button"
                class="stage-map__node"
                :class="{
                  'is-active': module.key === activeKey,
                  'is-done': module.progress === 100,
                  'is-progress': module.progress > 0 && module.progress < 100,
                }"
                :aria-current="module.key === activeKey ? 'step' : undefined"
                :aria-label="`${module.label}，已完成 ${module.progress}%，点击进入学习`"
                @mouseenter="emit('preview', module.key)"
                @focus="emit('preview', module.key)"
                @click="emit('open', module.key)"
              >
                <span class="stage-map__node-marker" aria-hidden="true">
                  <el-icon v-if="module.progress === 100"><Check /></el-icon>
                  <span v-else>{{ stepNumber(module.key) }}</span>
                </span>
                <span class="stage-map__node-copy">
                  <strong>{{ module.label }}</strong>
                  <small>{{ module.progress === 100 ? '已完成' : module.progress > 0 ? '继续学习' : '开始学习' }}</small>
                </span>
                <span class="stage-map__node-progress">
                  <b>{{ module.progress }}%</b>
                  <i aria-hidden="true"><em :style="{ width: `${module.progress}%` }" /></i>
                </span>
                <el-icon class="stage-map__node-arrow" aria-hidden="true"><ArrowRight /></el-icon>
              </button>
            </li>
          </ol>
        </li>
      </ol>
    </div>

    <footer v-if="activeModule" class="stage-map__footer" aria-live="polite">
      <div class="stage-map__current">
        <span>当前选中</span>
        <strong>{{ activeModule.label }}</strong>
        <small>{{ MODULE_PHASE_LABELS[activeModule.phase] }} · 第 {{ stepNumber(activeModule.key) }} 个模块</small>
      </div>
      <div class="stage-map__current-progress">
        <span>模块进度</span>
        <strong>{{ activeModule.progress }}%</strong>
      </div>
      <button type="button" class="stage-map__open" @click="emit('open', activeModule.key)">
        进入{{ activeModule.label }}
        <el-icon aria-hidden="true"><ArrowRight /></el-icon>
      </button>
    </footer>
  </section>
</template>

<style scoped>
.stage-map {
  margin-top: 18px;
  overflow: hidden;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
  background: var(--alp-bg-surface-solid);
}

.stage-map__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
  padding: 24px 26px 20px;
  border-bottom: 1px solid var(--alp-color-border);
}

.stage-map__heading { min-width: 0; }
.stage-map__title-row { display: flex; align-items: center; gap: 12px; }
.stage-map__title-row h2 { margin: 0; font-size: 20px; line-height: 1.35; letter-spacing: -0.02em; }
.stage-map__title-row span {
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(var(--alp-color-primary-rgb), 0.09);
  color: var(--alp-color-primary);
  font-size: 11px;
  font-weight: 650;
}
.stage-map__heading > p { margin: 6px 0 0; color: var(--alp-color-muted); font-size: 13px; }

.stage-map__overall { width: min(280px, 30vw); flex: 0 0 auto; }
.stage-map__overall > div:first-child { display: flex; align-items: baseline; justify-content: space-between; }
.stage-map__overall span { color: var(--alp-color-muted); font-size: 12px; }
.stage-map__overall strong { color: var(--alp-color-primary); font-size: 18px; font-variant-numeric: tabular-nums; }
.stage-map__overall-track { height: 6px; margin-top: 8px; overflow: hidden; border-radius: 999px; background: var(--alp-bg-soft-block); }
.stage-map__overall-track i { display: block; height: 100%; border-radius: inherit; background: var(--alp-color-primary); transition: width 220ms cubic-bezier(0.22, 1, 0.36, 1); }

.stage-map__canvas { padding: 0 10px; }
.stage-map__phases { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 0; padding: 0; list-style: none; }
.stage-map__phase { min-width: 0; padding: 22px 14px 24px; border-inline-end: 1px solid var(--alp-color-border); }
.stage-map__phase:last-child { border-inline-end: 0; }

.stage-map__phase-head {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  min-height: 68px;
  padding: 0 4px 16px;
  border-bottom: 1px solid var(--alp-color-border);
}
.stage-map__phase-number { grid-column: 1 / -1; color: var(--alp-color-muted); font-size: 11px; font-weight: 600; }
.stage-map__phase-head > .el-icon { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 10px; background: rgba(var(--alp-color-primary-rgb), 0.09); color: var(--alp-color-primary); font-size: 18px; }
.stage-map__phase-head h3 { margin: 0; font-size: 15px; line-height: 1.35; }
.stage-map__phase-head p { margin: 2px 0 0; overflow: hidden; color: var(--alp-color-muted); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.stage-map__phase-head > strong { color: var(--alp-color-text-secondary); font-size: 12px; font-variant-numeric: tabular-nums; }

.stage-map__nodes { position: relative; display: grid; gap: 10px; margin: 0; padding: 16px 0 0; list-style: none; }
.stage-map__nodes::before { content: ''; position: absolute; top: 16px; bottom: 20px; left: 25px; width: 1px; background: var(--alp-color-border-strong); }
.stage-map__nodes li { position: relative; z-index: 1; }

.stage-map__node {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 48px 16px;
  align-items: center;
  gap: 9px;
  width: 100%;
  min-height: 66px;
  padding: 9px 10px 9px 5px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: var(--alp-bg-surface-solid);
  color: var(--alp-color-text);
  text-align: left;
  cursor: pointer;
  transition: background-color 160ms ease, border-color 160ms ease, transform 160ms cubic-bezier(0.22, 1, 0.36, 1);
}
.stage-map__node:hover { border-color: var(--alp-color-border-strong); background: var(--alp-bg-surface-muted); transform: translateY(-1px); }
.stage-map__node.is-active { border-color: rgba(var(--alp-color-primary-rgb), 0.45); background: rgba(var(--alp-color-primary-rgb), 0.07); }
.stage-map__node:focus-visible { outline: 2px solid var(--alp-color-primary); outline-offset: 2px; }

.stage-map__node-marker { display: grid; width: 42px; height: 42px; place-items: center; border: 1px solid var(--alp-color-border-strong); border-radius: 50%; background: var(--alp-bg-surface-solid); color: var(--alp-color-muted); font-size: 11px; font-weight: 700; font-variant-numeric: tabular-nums; }
.stage-map__node.is-progress .stage-map__node-marker,
.stage-map__node.is-active .stage-map__node-marker { border-color: var(--alp-color-primary); color: var(--alp-color-primary); }
.stage-map__node.is-done .stage-map__node-marker { border-color: var(--alp-color-success); background: var(--alp-color-success); color: #fff; }
.stage-map__node-marker .el-icon { font-size: 17px; }

.stage-map__node-copy { display: flex; min-width: 0; flex-direction: column; }
.stage-map__node-copy strong { overflow: hidden; font-size: 13px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.stage-map__node-copy small { margin-top: 3px; color: var(--alp-color-muted); font-size: 10px; }
.stage-map__node-progress { display: flex; flex-direction: column; gap: 5px; align-items: flex-end; }
.stage-map__node-progress b { color: var(--alp-color-text-secondary); font-size: 10px; font-weight: 600; font-variant-numeric: tabular-nums; }
.stage-map__node-progress > i { display: block; width: 42px; height: 3px; overflow: hidden; border-radius: 999px; background: var(--alp-bg-soft-block); }
.stage-map__node-progress em { display: block; height: 100%; border-radius: inherit; background: var(--alp-color-primary); }
.stage-map__node-arrow { color: var(--alp-color-muted); font-size: 13px; transition: transform 160ms ease, color 160ms ease; }
.stage-map__node:hover .stage-map__node-arrow,
.stage-map__node.is-active .stage-map__node-arrow { color: var(--alp-color-primary); transform: translateX(2px); }

.stage-map__footer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 110px auto;
  align-items: center;
  gap: 24px;
  padding: 16px 26px;
  border-top: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-muted);
}
.stage-map__current { display: grid; grid-template-columns: auto minmax(0, auto) 1fr; align-items: baseline; gap: 10px; min-width: 0; }
.stage-map__current > span,
.stage-map__current-progress > span { color: var(--alp-color-muted); font-size: 11px; }
.stage-map__current > strong { font-size: 15px; }
.stage-map__current > small { overflow: hidden; color: var(--alp-color-muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.stage-map__current-progress { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.stage-map__current-progress strong { color: var(--alp-color-primary); font-size: 16px; font-variant-numeric: tabular-nums; }
.stage-map__open { display: inline-flex; min-height: 38px; align-items: center; justify-content: center; gap: 7px; padding: 0 16px; border: 0; border-radius: 8px; background: var(--alp-color-primary); color: #fff; font: inherit; font-size: 13px; font-weight: 650; cursor: pointer; transition: background-color 160ms ease, transform 160ms ease; }
.stage-map__open:hover { background: var(--el-color-primary-dark-2); transform: translateY(-1px); }
.stage-map__open:active { transform: translateY(0); }

@media (max-width: 1180px) {
  .stage-map__phases { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stage-map__phase:nth-child(2) { border-inline-end: 0; }
  .stage-map__phase:nth-child(-n + 2) { border-bottom: 1px solid var(--alp-color-border); }
}

@media (max-width: 700px) {
  .stage-map__header { align-items: stretch; flex-direction: column; gap: 16px; padding: 20px 18px 18px; }
  .stage-map__title-row { align-items: flex-start; flex-direction: column; gap: 7px; }
  .stage-map__title-row h2 { font-size: 18px; }
  .stage-map__overall { width: 100%; }
  .stage-map__canvas { padding: 0; }
  .stage-map__phases { grid-template-columns: 1fr; }
  .stage-map__phase,
  .stage-map__phase:nth-child(2) { padding: 20px 16px; border-inline-end: 0; border-bottom: 1px solid var(--alp-color-border); }
  .stage-map__phase:last-child { border-bottom: 0; }
  .stage-map__footer { grid-template-columns: minmax(0, 1fr) auto; gap: 14px; padding: 15px 18px; }
  .stage-map__current { grid-template-columns: auto 1fr; }
  .stage-map__current > small { grid-column: 1 / -1; }
  .stage-map__current-progress { display: none; }
  .stage-map__open { padding: 0 12px; }
}

@media (prefers-reduced-motion: reduce) {
  .stage-map__node,
  .stage-map__node-arrow,
  .stage-map__open,
  .stage-map__overall-track i { transition: none; }
}
</style>
