<script setup lang="ts">
import { computed } from 'vue'
import type { GameCodeLine, GameLevelShellMeta } from '@/modules/games/shared/gameShellMeta'
import { isCodeLineActive } from '@/modules/games/shared/gameShellMeta'

const props = withDefaults(
  defineProps<{
    meta: GameLevelShellMeta
    hint: string
    fail?: boolean
    won?: boolean
    stepIndex?: number
    stepTotal?: number
    stateValues?: Record<string, string | undefined>
    actionLog?: string[]
    showSteps?: boolean
    showSidebar?: boolean
  }>(),
  {
    fail: false,
    won: false,
    stepIndex: 0,
    stepTotal: undefined,
    stateValues: () => ({}),
    actionLog: () => [],
    showSteps: true,
    showSidebar: true,
  },
)

const emit = defineEmits<{ reset: [] }>()

const totalSteps = computed(() => props.stepTotal ?? props.meta.stepCount ?? 1)

const progressPercent = computed(() => {
  if (props.won) return 100
  if (totalSteps.value <= 0) return 0
  return Math.round((props.stepIndex / totalSteps.value) * 100)
})

const progressText = computed(
  () => `步骤 ${Math.min(props.stepIndex + 1, totalSteps.value)} / ${totalSteps.value}`,
)

const displayedRules = computed(
  () =>
    props.meta.rules ?? [
      '先阅读当前任务，再按高亮步骤或提示顺序操作。',
      '每次操作都会同步更新状态面板、伪代码高亮和操作日志。',
      '违反核心数据结构规则会触发失败提示；重置本关可重新挑战。',
      '通关条件是完成目标状态，而不是只点到最后一个按钮。',
    ],
)

function lineActive(line: GameCodeLine) {
  return isCodeLineActive(line, props.stepIndex)
}
</script>

<template>
  <div class="game-shell">
    <header class="game-shell__header">
      <div class="game-shell__header-main">
        <span class="game-shell__badge">{{ meta.badge }}</span>
        <span class="game-shell__lc">{{ meta.lc }}</span>
        <span class="game-shell__progress-text">{{ progressText }}</span>
      </div>
      <el-progress
        :percentage="progressPercent"
        :stroke-width="6"
        :show-text="false"
        color="var(--game-accent, #3a8a9e)"
        class="game-shell__progress-bar"
      />
      <div v-if="showSteps && totalSteps > 1" class="game-shell__step-rail" aria-label="步骤进度">
        <button
          v-for="i in totalSteps"
          :key="i - 1"
          type="button"
          class="game-shell__step-chip"
          :class="{
            'is-done': i - 1 < stepIndex || won,
            'is-current': i - 1 === stepIndex && !won,
          }"
          disabled
        >
          <span class="game-shell__step-num">{{ i }}</span>
        </button>
      </div>
    </header>

    <div class="game-shell__grid" :class="{ 'is-single': !showSidebar }">
      <section class="game-shell__play">
        <div class="game-shell__hint-box" :class="{ 'is-fail': fail, 'is-win': won }">
          <span class="game-shell__hint-label">{{ won ? '完成' : fail ? '再试一次' : '当前任务' }}</span>
          <p class="game-shell__hint-text">{{ hint }}</p>
        </div>

        <div class="game-shell__body">
          <slot />
        </div>

        <div v-if="$slots.actions" class="game-shell__actions">
          <slot name="actions" />
        </div>

        <div class="game-shell__play-footer">
          <slot name="play-footer">
            <el-button v-if="showSidebar" size="small" text @click="emit('reset')">重置本关</el-button>
          </slot>
        </div>

        <p v-if="won && $slots.win" class="alp-game-win">
          <slot name="win" />
        </p>
        <p v-else-if="won" class="alp-game-win">{{ hint }}</p>
      </section>

      <aside v-if="showSidebar" class="game-shell__sidebar">
        <div class="game-shell__panel game-shell__panel--code">
          <h3 class="game-shell__panel-title">伪代码对照</h3>
          <pre class="game-shell__code"><code><span
              v-for="(line, li) in meta.codeLines"
              :key="li"
              class="game-shell__code-line"
              :class="{ 'is-active': lineActive(line) }"
            >{{ line.text }}
</span></code></pre>
        </div>

        <div v-if="meta.stateKeys.length" class="game-shell__panel">
          <h3 class="game-shell__panel-title">状态面板</h3>
          <ul class="game-shell__state-list">
            <li
              v-for="s in meta.stateKeys"
              :key="s.key"
              class="game-shell__state-item"
              :style="{ '--state-color': s.color }"
            >
              <span class="game-shell__state-name">{{ s.label }}</span>
              <span class="game-shell__state-val">{{ stateValues[s.key] ?? '—' }}</span>
            </li>
          </ul>
        </div>

        <div class="game-shell__panel">
          <h3 class="game-shell__panel-title">游戏规则</h3>
          <ol class="game-shell__rules">
            <li v-for="rule in displayedRules" :key="rule">{{ rule }}</li>
          </ol>
        </div>

        <div class="game-shell__panel">
          <h3 class="game-shell__panel-title">算法要点</h3>
          <p class="game-shell__concept">{{ meta.concept }}</p>
          <p class="game-shell__invariant">
            <strong>不变量：</strong>{{ meta.invariant }}
          </p>
        </div>

        <div class="game-shell__panel">
          <h3 class="game-shell__panel-title">操作日志</h3>
          <ul v-if="actionLog.length" class="game-shell__log">
            <li v-for="(entry, i) in actionLog" :key="i">{{ entry }}</li>
          </ul>
          <p v-else class="game-shell__log-empty">尚无操作记录</p>
        </div>

        <slot name="sidebar-extra" />
      </aside>
    </div>

    <footer class="game-shell__footer">
      <span class="game-shell__footer-item">{{ meta.footer[0] }}</span>
      <span class="game-shell__footer-item">{{ meta.footer[1] }}</span>
    </footer>
  </div>
</template>

<style scoped>
.game-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
  width: 100%;
}

.game-shell__header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: color-mix(in srgb, var(--game-accent, #3a8a9e) 8%, var(--alp-bg-soft-block));
}

.game-shell__header-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.game-shell__badge {
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
  color: var(--game-accent, #3a8a9e);
  background: color-mix(in srgb, var(--game-accent, #3a8a9e) 16%, transparent);
  border-radius: 999px;
}

.game-shell__lc {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.game-shell__progress-text {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  color: var(--game-accent, #3a8a9e);
}

.game-shell__progress-bar {
  width: 100%;
}

.game-shell__step-rail {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.game-shell__step-chip {
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  cursor: default;
}

.game-shell__step-num {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.game-shell__step-chip.is-done {
  border-color: color-mix(in srgb, #4a8a5e 50%, transparent);
  background: color-mix(in srgb, #4a8a5e 14%, transparent);
}

.game-shell__step-chip.is-done .game-shell__step-num {
  color: #8ab896;
}

.game-shell__step-chip.is-current {
  border-color: var(--game-accent, #3a8a9e);
  background: color-mix(in srgb, var(--game-accent, #3a8a9e) 22%, transparent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--game-accent, #3a8a9e) 25%, transparent);
}

.game-shell__step-chip.is-current .game-shell__step-num {
  color: #6a9eb0;
}

.game-shell__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(260px, 0.85fr);
  gap: 16px;
  align-items: start;
  flex: 1;
}

.game-shell__grid.is-single {
  grid-template-columns: 1fr;
}

.game-shell__play {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.game-shell__hint-box {
  padding: 12px 14px;
  border-radius: 10px;
  border-left: 4px solid var(--game-accent, #3a8a9e);
  background: color-mix(in srgb, var(--game-accent, #3a8a9e) 6%, var(--alp-bg-surface-solid, #0f172a));
}

.game-shell__hint-box.is-fail {
  border-left-color: #9e5a5a;
  background: color-mix(in srgb, #9e5a5a 8%, transparent);
}

.game-shell__hint-box.is-win {
  border-left-color: #4a8a5e;
  background: color-mix(in srgb, #4a8a5e 10%, transparent);
}

.game-shell__hint-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--alp-color-muted);
  margin-bottom: 4px;
}

.game-shell__hint-box.is-fail .game-shell__hint-label {
  color: #fca5a5;
}

.game-shell__hint-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.game-shell__body {
  min-height: 120px;
}

.game-shell__body :deep(.workbench) {
  padding: 14px;
  border-radius: 12px;
  border: 1px dashed color-mix(in srgb, var(--game-accent, #3a8a9e) 35%, var(--alp-color-border));
  background: color-mix(in srgb, var(--game-accent, #3a8a9e) 4%, transparent);
}

.game-shell__body :deep(.workbench-head) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.game-shell__body :deep(.workbench-title) {
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.game-shell__body :deep(.workbench-snap) {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 6px;
  background: var(--alp-bg-soft-block);
  color: #6a9eb0;
  font-family: ui-monospace, monospace;
}

.game-shell__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.game-shell__play-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.game-shell__sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.game-shell__panel {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.5));
}

.game-shell__panel-title {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--alp-color-muted);
}

.game-shell__code {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #0c1222;
  overflow-x: auto;
  font-size: 11px;
  line-height: 1.65;
  font-family: ui-monospace, 'Cascadia Code', monospace;
}

.game-shell__code-line {
  display: block;
  color: #94a3b8;
  padding: 1px 4px;
  border-radius: 3px;
}

.game-shell__code-line.is-active {
  color: #e2e8f0;
  background: color-mix(in srgb, var(--game-accent, #3a8a9e) 18%, transparent);
}

.game-shell__state-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.game-shell__state-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.game-shell__state-name {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  background: var(--state-color);
  color: #0f172a;
}

.game-shell__state-val {
  font-size: 12px;
  font-weight: 500;
  color: var(--alp-color-text);
  text-align: right;
}

.game-shell__concept {
  margin: 0 0 8px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.game-shell__rules {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.game-shell__rules li {
  font-size: 12px;
  line-height: 1.55;
  color: var(--alp-color-text);
}

.game-shell__invariant {
  margin: 0;
  font-size: 11px;
  line-height: 1.55;
  color: var(--alp-color-muted);
}

.game-shell__invariant strong {
  color: var(--game-accent, #3a8a9e);
  font-weight: 600;
}

.game-shell__log {
  margin: 0;
  padding: 0;
  list-style: none;
  max-height: 140px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.game-shell__log li {
  font-size: 11px;
  line-height: 1.45;
  padding: 6px 8px;
  border-radius: 6px;
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-muted);
  font-family: ui-monospace, monospace;
}

.game-shell__log-empty {
  margin: 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  font-style: italic;
}

.game-shell__footer {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px dashed var(--alp-color-border);
  font-size: 11px;
  color: var(--alp-color-muted);
}

.game-shell__footer-item::before {
  content: '◆ ';
  color: var(--game-accent, #3a8a9e);
  font-size: 8px;
}

@media (max-width: 960px) {
  .game-shell__grid:not(.is-single) {
    grid-template-columns: 1fr;
  }

  .game-shell__progress-text {
    margin-left: 0;
  }
}
</style>
