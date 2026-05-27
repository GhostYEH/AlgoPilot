<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, toRef, watch } from 'vue'
import type { AgentConsoleLine, AgentLogStatus } from '@/utils/agentConsole'
import { useAgentLogStream } from '@/composables/useAgentLogStream'

const props = withDefaults(
  defineProps<{
    lines: AgentConsoleLine[]
    active?: boolean
    title?: string
    subtitle?: string
    progress?: number
    mode?: 'resource' | 'diagnosis' | 'idle'
    /** 活跃时逐字打字机 + 逐行滚屏 */
    streamTyping?: boolean
  }>(),
  {
    active: false,
    title: 'Agent Synergy Terminal',
    subtitle: 'multi-agent orchestrator · live stream',
    progress: 0,
    mode: 'idle',
    streamTyping: true,
  },
)

type DisplayLine = AgentConsoleLine & { typedMessage?: string; typingDone?: boolean }

const scrollRef = ref<HTMLElement | null>(null)
const cursorVisible = ref(true)
let cursorTimer: number | undefined

const sourceLines = toRef(props, 'lines')
const streamEnabled = computed(() => props.streamTyping && props.active)
const { visibleLines } = useAgentLogStream(sourceLines, {
  enabled: streamEnabled,
  lineIntervalMs: 420,
  charIntervalMs: 16,
})

const displayLines = computed((): DisplayLine[] => {
  if (props.streamTyping && props.active) return visibleLines.value
  return props.lines
})

const displayCount = computed(() => displayLines.value.length)

watch(
  () => displayCount.value,
  async () => {
    await nextTick()
    const el = scrollRef.value
    if (el) el.scrollTop = el.scrollHeight
  },
)

watch(
  () => props.active,
  (on) => {
    if (cursorTimer) window.clearInterval(cursorTimer)
    if (!on) return
    cursorTimer = window.setInterval(() => {
      cursorVisible.value = !cursorVisible.value
    }, 530)
  },
  { immediate: true },
)

onUnmounted(() => {
  if (cursorTimer) window.clearInterval(cursorTimer)
})

const statusClass = (s: AgentLogStatus) => `line--${s}`

const modeBadge = computed(() => {
  if (props.mode === 'resource') return 'RESOURCE PIPELINE'
  if (props.mode === 'diagnosis') return 'AI DIAGNOSIS'
  return 'STANDBY'
})

const treeConnectors = computed(() => [...new Set(displayLines.value.map((l) => l.agent))].slice(0, 8))

function lineMessage(line: DisplayLine): string {
  if (props.streamTyping && props.active && !line.typingDone) {
    return line.typedMessage ?? ''
  }
  return line.message
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour12: false })
}
</script>

<template>
  <div class="agent-console" :class="{ 'agent-console--live': active }">
    <div class="console-scanlines" aria-hidden="true" />
    <div class="console-chrome">
      <div class="console-dots" aria-hidden="true">
        <span class="dot dot--r" />
        <span class="dot dot--y" />
        <span class="dot dot--g" />
      </div>
      <div class="console-title-block">
        <span class="console-title">{{ title }}</span>
        <span class="console-sub">{{ subtitle }}</span>
      </div>
      <span class="mode-badge">{{ modeBadge }}</span>
    </div>

    <div v-if="active && progress > 0" class="console-progress">
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: `${Math.min(100, progress)}%` }" />
      </div>
      <span class="progress-pct">{{ Math.round(progress) }}%</span>
    </div>

    <aside v-if="displayLines.length" class="agent-tree" aria-label="活跃 Agent">
      <div v-for="agent in treeConnectors" :key="agent" class="tree-node">
        <span class="tree-pulse" :class="{ live: active }" />
        <span class="tree-label">{{ agent }}</span>
      </div>
    </aside>

    <div ref="scrollRef" class="console-body">
      <div v-if="!displayLines.length" class="console-empty">
        <span class="empty-glyph">▸</span>
        <p>等待 Orchestrator 下发协同任务…</p>
        <p class="empty-hint">
          触发「可视化调试 / AI 诊断」后，ASTAnalyzerAgent 将先执行静态扫描，再移交 trace_runner / GDB 动态沙箱
        </p>
      </div>

      <transition-group name="log-line" tag="div" class="log-stream">
        <div
          v-for="line in displayLines"
          :key="line.id"
          class="log-line"
          :class="[statusClass(line.status), { 'log-line--typing': streamTyping && active && !line.typingDone }]"
          :style="{ paddingLeft: `${12 + line.indent * 18}px` }"
        >
          <span class="log-ts">{{ formatTime(line.ts) }}</span>
          <span class="log-icon">{{ line.icon }}</span>
          <span class="log-agent">[{{ line.agent }}]</span>
          <span class="log-msg">{{ lineMessage(line) }}</span>
          <span v-if="line.status === 'running'" class="log-spinner" aria-hidden="true" />
        </div>
      </transition-group>

      <div v-if="active" class="console-cursor-line">
        <span class="log-prompt">alp@orchestrator $</span>
        <span class="cursor" :class="{ off: !cursorVisible }">▊</span>
      </div>
    </div>

    <footer class="console-footer">
      <span>agents online: {{ treeConnectors.length }}</span>
      <span>events: {{ displayCount }}</span>
      <span v-if="active" class="live-tag">● LIVE</span>
    </footer>
  </div>
</template>

<style scoped>
.agent-console {
  --term-bg: #0a0e17;
  --term-border: color-mix(in srgb, #38bdf8 35%, #1e293b);
  --term-glow: color-mix(in srgb, #38bdf8 25%, transparent);
  --term-text: #e2e8f0;
  --term-muted: #64748b;
  --term-accent: #38bdf8;
  --term-success: #4ade80;
  --term-warn: #fbbf24;
  --term-error: #f87171;

  position: relative;
  border-radius: 16px;
  border: 1px solid var(--term-border);
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%, var(--term-glow), transparent 55%),
    linear-gradient(165deg, #0f172a 0%, var(--term-bg) 45%, #020617 100%);
  box-shadow:
    0 0 0 1px color-mix(in srgb, #38bdf8 8%, transparent),
    0 24px 48px color-mix(in srgb, #000 45%, transparent),
    inset 0 1px 0 color-mix(in srgb, #fff 6%, transparent);
  overflow: hidden;
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
}

.console-scanlines {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 4;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.14) 2px,
    rgba(0, 0, 0, 0.14) 4px
  );
  opacity: 0.45;
  mix-blend-mode: overlay;
}

.console-scanlines::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(56, 189, 248, 0.04) 48%,
    rgba(56, 189, 248, 0.08) 50%,
    rgba(56, 189, 248, 0.04) 52%,
    transparent 100%
  );
  background-size: 100% 220%;
  animation: crt-scan 6s linear infinite;
}

@keyframes crt-scan {
  0% {
    background-position: 0 -100%;
  }
  100% {
    background-position: 0 200%;
  }
}

.agent-console--live {
  animation: console-pulse 2.4s ease-in-out infinite;
}

@keyframes console-pulse {
  0%,
  100% {
    box-shadow:
      0 0 0 1px color-mix(in srgb, #38bdf8 12%, transparent),
      0 24px 48px color-mix(in srgb, #000 45%, transparent),
      0 0 40px color-mix(in srgb, #38bdf8 8%, transparent);
  }
  50% {
    box-shadow:
      0 0 0 1px color-mix(in srgb, #38bdf8 22%, transparent),
      0 24px 48px color-mix(in srgb, #000 45%, transparent),
      0 0 56px color-mix(in srgb, #a78bfa 12%, transparent);
  }
}

.console-chrome {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid color-mix(in srgb, #fff 8%, transparent);
  background: color-mix(in srgb, #000 25%, transparent);
}

.console-dots {
  display: flex;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot--r {
  background: #ff5f57;
}
.dot--y {
  background: #febc2e;
}
.dot--g {
  background: #28c840;
}

.console-title-block {
  flex: 1;
  min-width: 0;
}

.console-title {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: var(--term-accent);
  letter-spacing: 0.04em;
}

.console-sub {
  font-size: 10px;
  color: var(--term-muted);
}

.mode-badge {
  font-size: 9px;
  letter-spacing: 0.12em;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid color-mix(in srgb, var(--term-accent) 40%, transparent);
  color: var(--term-accent);
}

.console-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  border-bottom: 1px solid color-mix(in srgb, #fff 5%, transparent);
}

.progress-track {
  flex: 1;
  height: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, #fff 8%, transparent);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #38bdf8, #a78bfa);
  transition: width 0.45s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 0 12px #38bdf8;
}

.progress-pct {
  font-size: 11px;
  color: var(--term-accent);
  min-width: 36px;
  text-align: right;
}

.agent-tree {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 16px;
  border-bottom: 1px dashed color-mix(in srgb, #fff 8%, transparent);
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--term-muted);
  padding: 2px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, #fff 4%, transparent);
}

.tree-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--term-muted);
}

.tree-pulse.live {
  background: var(--term-success);
  animation: pulse-dot 1.2s infinite;
}

@keyframes pulse-dot {
  50% {
    opacity: 0.35;
    transform: scale(1.3);
  }
}

.console-body {
  min-height: 220px;
  max-height: min(420px, 50vh);
  overflow-y: auto;
  padding: 14px 0;
  scrollbar-width: thin;
  scrollbar-color: #334155 transparent;
}

.console-empty {
  padding: 24px 20px;
  color: var(--term-muted);
  font-size: 12px;
  line-height: 1.65;
}

.empty-glyph {
  color: var(--term-accent);
  margin-right: 6px;
}

.empty-hint {
  margin-top: 8px;
  font-size: 11px;
  opacity: 0.75;
}

.log-stream {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.log-line {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px;
  padding: 6px 16px 6px 12px;
  font-size: 12px;
  line-height: 1.55;
  border-left: 2px solid transparent;
  animation: line-in 0.35s ease-out both;
}

@keyframes line-in {
  from {
    opacity: 0;
    transform: translateX(-6px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.log-line.line--running {
  border-left-color: var(--term-accent);
  background: color-mix(in srgb, #38bdf8 6%, transparent);
}

.log-line.line--done {
  border-left-color: color-mix(in srgb, var(--term-success) 50%, transparent);
}

.log-line.line--success {
  border-left-color: var(--term-success);
  background: color-mix(in srgb, #4ade80 5%, transparent);
}

.log-line.line--warn {
  border-left-color: var(--term-warn);
}

.log-line.line--error {
  border-left-color: var(--term-error);
}

.log-line--typing .log-msg {
  color: #a5f3fc;
}

.log-line--typing .log-msg::after {
  content: '▋';
  margin-left: 2px;
  color: var(--term-accent);
  animation: blink 0.9s step-end infinite;
}

.log-ts {
  font-size: 10px;
  color: var(--term-muted);
  flex-shrink: 0;
}

.log-icon {
  flex-shrink: 0;
}

.log-agent {
  color: var(--term-accent);
  font-weight: 600;
  flex-shrink: 0;
}

.log-msg {
  color: var(--term-text);
  flex: 1;
  min-width: 0;
}

.log-spinner {
  width: 10px;
  height: 10px;
  border: 2px solid color-mix(in srgb, var(--term-accent) 30%, transparent);
  border-top-color: var(--term-accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.console-cursor-line {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--term-muted);
}

.log-prompt {
  color: var(--term-success);
  margin-right: 8px;
}

.cursor {
  color: var(--term-accent);
}

.cursor.off {
  opacity: 0;
}

.console-footer {
  display: flex;
  gap: 16px;
  padding: 8px 16px;
  font-size: 10px;
  color: var(--term-muted);
  border-top: 1px solid color-mix(in srgb, #fff 6%, transparent);
  background: color-mix(in srgb, #000 20%, transparent);
}

.live-tag {
  color: var(--term-success);
  animation: blink 1.4s step-end infinite;
}

@keyframes blink {
  50% {
    opacity: 0.4;
  }
}

.log-line-enter-active {
  transition: all 0.3s ease-out;
}

.log-line-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
</style>
