<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

/** 演示树 1(2(4,5), 3) */
const NODES = [
  { id: '1', label: '1', cx: 55, cy: 14, r: 9 },
  { id: '2', label: '2', cx: 35, cy: 38, r: 8 },
  { id: '3', label: '3', cx: 75, cy: 38, r: 8 },
  { id: '4', label: '4', cx: 25, cy: 58, r: 7 },
  { id: '5', label: '5', cx: 45, cy: 58, r: 7 },
] as const

const EDGES: [string, string][] = [
  ['1', '2'],
  ['1', '3'],
  ['2', '4'],
  ['2', '5'],
]

const CARDS = [
  {
    key: 'preorder',
    title: '前序',
    lc: 144,
    rule: '根 → 左 → 右',
    formula: '先 visit 根，再左子树，再右子树',
    order: ['1', '2', '4', '5', '3'] as string[],
    accent: '#38bdf8',
  },
  {
    key: 'inorder',
    title: '中序',
    lc: 94,
    rule: '左 → 根 → 右',
    formula: '左子树走完再 visit 根',
    order: ['4', '2', '5', '1', '3'] as string[],
    accent: '#c4b5fd',
  },
  {
    key: 'postorder',
    title: '后序',
    lc: 145,
    rule: '左 → 右 → 根',
    formula: '左右子树都处理完再 visit 根',
    order: ['4', '5', '2', '3', '1'] as string[],
    accent: '#4ade80',
  },
] as const

const tick = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => {
    tick.value = (tick.value + 1) % 5
  }, 850)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function nodeState(order: readonly string[], id: string) {
  const idx = order.indexOf(id)
  if (idx < 0) return 'bt-mini-node'
  const cur = order[Math.min(tick.value, order.length - 1)]
  if (id === cur) return 'bt-mini-node bt-mini-node--hot'
  if (idx < tick.value) return 'bt-mini-node bt-mini-node--done'
  return 'bt-mini-node'
}

function visitTrail(order: readonly string[]) {
  return order.slice(0, tick.value + 1).join(' → ')
}

function pos(id: string) {
  return NODES.find((n) => n.id === id)!
}
</script>

<template>
  <figure class="traversal-board" role="img" aria-label="前序、中序、后序遍历对照">
    <figcaption class="board-caption">
      同一棵演示树 · 三种 DFS 访问顺序（自动轮播高亮当前结点）
    </figcaption>

    <div class="card-row">
      <article
        v-for="card in CARDS"
        :key="card.key"
        class="traverse-card"
        :style="{ '--card-accent': card.accent }"
      >
        <header class="card-head">
          <h3 class="card-title">{{ card.title }}</h3>
          <span class="lc-tag">LeetCode {{ card.lc }}</span>
        </header>
        <p class="card-rule">{{ card.rule }}</p>
        <p class="card-formula">{{ card.formula }}</p>

        <svg viewBox="0 0 110 72" class="mini-tree" aria-hidden="true">
          <line
            v-for="([a, b], i) in EDGES"
            :key="i"
            :x1="pos(a).cx"
            :y1="pos(a).cy + pos(a).r - 2"
            :x2="pos(b).cx"
            :y2="pos(b).cy - pos(b).r + 2"
            class="mini-edge"
          />
          <g v-for="n in NODES" :key="n.id">
            <circle :cx="n.cx" :cy="n.cy" :r="n.r" :class="nodeState(card.order, n.id)" />
            <text :x="n.cx" :y="n.cy + 3.5" class="mini-lbl" text-anchor="middle">{{ n.label }}</text>
          </g>
        </svg>

        <p class="trail">
          <span class="trail-label">当前</span>
          {{ visitTrail(card.order) }}
        </p>
        <p class="output">
          输出
          <code>[{{ card.order.join(', ') }}]</code>
        </p>
      </article>
    </div>
  </figure>
</template>

<style scoped>
.traversal-board {
  margin: 0;
  padding: 14px 16px 12px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.board-caption {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  text-align: center;
  line-height: 1.45;
}

.card-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.traverse-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 10px;
  border-radius: 12px;
  background: var(--alp-bg-code-ish, rgba(15, 23, 42, 0.55));
  border: 1px solid var(--alp-color-border);
  border-top: 3px solid var(--card-accent, #38bdf8);
  min-width: 0;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--card-accent);
}

.lc-tag {
  font-size: 10px;
  font-weight: 600;
  color: var(--alp-color-muted);
  background: color-mix(in srgb, var(--card-accent) 12%, transparent);
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--card-accent) 30%, transparent);
  white-space: nowrap;
}

.card-rule {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-text);
  letter-spacing: 0.02em;
}

.card-formula {
  margin: 0;
  font-size: 11px;
  line-height: 1.4;
  color: var(--alp-color-muted);
  min-height: 2.5em;
}

.mini-tree {
  width: 100%;
  height: auto;
  display: block;
}

.mini-edge {
  stroke: var(--alp-color-border);
  stroke-width: 1.5;
}

.bt-mini-node {
  fill: var(--alp-bg-surface-solid);
  stroke: var(--alp-color-border);
  stroke-width: 1.5;
  transition:
    fill 0.32s ease,
    stroke 0.32s ease;
}

.mini-lbl {
  font-size: 8px;
  font-weight: 700;
  fill: var(--alp-color-text);
  pointer-events: none;
}

.bt-mini-node--hot {
  fill: color-mix(in srgb, var(--card-accent) 22%, var(--alp-bg-surface-solid));
  stroke: var(--card-accent);
  stroke-width: 2;
}

.bt-mini-node--done {
  fill: color-mix(in srgb, #22c55e 14%, var(--alp-bg-surface-solid));
  stroke: #22c55e;
}

.trail {
  margin: 0;
  font-size: 10px;
  line-height: 1.35;
  color: var(--alp-color-muted);
  word-break: break-all;
}

.trail-label {
  font-weight: 700;
  color: var(--card-accent);
  margin-right: 3px;
}

.output {
  margin: 0;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.output code {
  font-size: 10px;
  font-weight: 600;
  color: var(--card-accent);
  background: var(--alp-bg-surface-solid);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--alp-color-border);
}

@media (max-width: 720px) {
  .card-row {
    grid-template-columns: 1fr;
    max-width: 360px;
    margin: 0 auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  .bt-mini-node {
    transition: none;
  }
}
</style>
