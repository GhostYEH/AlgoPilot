<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  sectionId: string
}>()

const label = computed(() => {
  const m: Record<string, string> = {
    theory: '单链：结点通过 next 指针依次串联（示意，非真实内存地址）',
    'remove-elements': '删除指定值：跳过目标结点，前驱直接连向后继',
    'design-list': '虚拟头结点 dummy：便于在头部统一插入 / 删除',
    reverse: '反转：依次把 next 指向前驱（三指针思路的抽象）',
    'swap-pairs': '两两交换：交换的是结点指针，不是只换数值',
    'remove-nth-from-end': '快慢指针：快针先拉开间距，再同速走到底',
    intersection: '相交：对齐长度后同速走，首次相同的即交点（指针相等）',
    cycle: '环形：快二慢一必在环上相遇；再从头与相遇点同速找入口',
    summary: '链表篇：dummy、反转、双指针（倒数 / 相交 / 环）',
  }
  return m[props.sectionId] ?? '本节知识点示意'
})
</script>

<template>
  <figure
    class="ll-anim"
    role="img"
    :aria-label="label"
  >
    <figcaption class="ll-anim-caption">{{ label }}</figcaption>

    <!-- 理论基础：结点链 + 流动箭头 -->
    <div v-if="sectionId === 'theory'" class="panel theory">
      <div class="row">
        <span class="node">1</span>
        <span class="arrow-flow" aria-hidden="true">
          <span class="arrow-shaft" />
          <span class="arrow-head">▶</span>
        </span>
        <span class="node">2</span>
        <span class="arrow-flow" aria-hidden="true">
          <span class="arrow-shaft" />
          <span class="arrow-head">▶</span>
        </span>
        <span class="node">3</span>
        <span class="nil">∅</span>
      </div>
    </div>

    <!-- 移除元素：中间结点淡出，长箭头跳过 -->
    <div v-else-if="sectionId === 'remove-elements'" class="panel remove">
      <div class="row">
        <span class="node">1</span>
        <span class="dash">—</span>
        <span class="node ghost">6</span>
        <span class="dash">—</span>
        <span class="node">3</span>
        <span class="arrow-skip" aria-hidden="true">⇢</span>
      </div>
    </div>

    <!-- 设计链表：dummy + 表头 -->
    <div v-else-if="sectionId === 'design-list'" class="panel design">
      <div class="row">
        <span class="node dummy">D</span>
        <span class="arrow-mini">→</span>
        <span class="node slide-head">head</span>
        <span class="arrow-mini">→</span>
        <span class="node">···</span>
      </div>
    </div>

    <!-- 反转：整行方向周期性翻转 -->
    <div v-else-if="sectionId === 'reverse'" class="panel reverse">
      <div class="flip-row">
        <span class="node">1</span>
        <span class="rev-arr">«</span>
        <span class="node">2</span>
        <span class="rev-arr">«</span>
        <span class="node">3</span>
      </div>
    </div>

    <!-- 两两交换 -->
    <div v-else-if="sectionId === 'swap-pairs'" class="panel swap">
      <div class="swap-row">
        <span class="node a">A</span>
        <span class="node b">B</span>
        <span class="gap" />
        <span class="node c">C</span>
        <span class="node d">D</span>
      </div>
    </div>

    <!-- 快慢指针删倒数第 n 个 -->
    <div v-else-if="sectionId === 'remove-nth-from-end'" class="panel twoptr">
      <div class="track">
        <span v-for="i in 6" :key="i" class="slot">{{ i }}</span>
      </div>
      <div class="markers">
        <span class="tag slow">slow</span>
        <span class="tag fast">fast</span>
      </div>
    </div>

    <!-- 相交 -->
    <div v-else-if="sectionId === 'intersection'" class="panel meet">
      <svg class="meet-svg" viewBox="0 0 200 72" xmlns="http://www.w3.org/2000/svg">
        <path
          class="path-a"
          d="M 8 12 C 40 12, 50 58, 100 58"
          fill="none"
          stroke="var(--alp-color-primary, #2563eb)"
          stroke-width="2.5"
          stroke-linecap="round"
        />
        <path
          class="path-b"
          d="M 192 12 C 160 12, 150 58, 100 58"
          fill="none"
          stroke="#64748b"
          stroke-width="2.5"
          stroke-linecap="round"
        />
        <circle class="pulse-dot" cx="100" cy="58" r="5" fill="#4a8a5e" />
      </svg>
    </div>

    <!-- 环形：双点绕同一圆轨道，快圈速为慢的 2 倍 -->
    <div v-else-if="sectionId === 'cycle'" class="panel ring">
      <div class="ring-stage" aria-hidden="true">
        <div class="ring-orbit" />
        <div class="ring-runner ring-runner--slow">
          <span class="ring-dot ring-dot--slow" />
        </div>
        <div class="ring-runner ring-runner--fast">
          <span class="ring-dot ring-dot--fast" />
        </div>
      </div>
    </div>

    <!-- 总结：关键词呼吸高亮 -->
    <div v-else-if="sectionId === 'summary'" class="panel summary">
      <div class="pill-row">
        <span class="pill">dummy</span>
        <span class="pill">反转</span>
        <span class="pill">双指针</span>
        <span class="pill">相交</span>
        <span class="pill">环</span>
      </div>
    </div>
  </figure>
</template>

<style scoped>
.ll-anim {
  margin: 0;
  padding: 14px 16px 12px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.ll-anim-caption {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  line-height: 1.45;
}

.panel {
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}

.node {
  display: inline-grid;
  place-items: center;
  min-width: 34px;
  height: 34px;
  padding: 0 8px;
  border-radius: 8px;
  background: var(--alp-bg-surface-solid);
  border: 2px solid var(--alp-color-border);
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-text);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.node.dummy {
  border-style: dashed;
  color: var(--alp-color-primary, #2563eb);
  border-color: var(--alp-color-primary, #2563eb);
}

.node.ghost {
  animation: fade-skip 2.4s ease-in-out infinite;
}

.nil {
  font-size: 14px;
  color: #94a3b8;
  margin-left: 2px;
}

@keyframes fade-skip {
  0%,
  35% {
    opacity: 1;
    transform: scale(1);
  }
  50%,
  65% {
    opacity: 0.2;
    transform: scale(0.85);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.arrow-flow {
  display: inline-flex;
  align-items: center;
  gap: 0;
  color: var(--alp-color-primary, #2563eb);
}

.arrow-shaft {
  width: 18px;
  height: 2px;
  background: currentColor;
  transform-origin: left center;
  animation: shaft-pulse 1.6s ease-in-out infinite;
}

.arrow-head {
  font-size: 10px;
  margin-left: -2px;
  animation: head-blink 1.6s ease-in-out infinite;
}

@keyframes shaft-pulse {
  0%,
  100% {
    opacity: 0.45;
    transform: scaleX(0.75);
  }
  50% {
    opacity: 1;
    transform: scaleX(1);
  }
}

@keyframes head-blink {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.dash {
  color: #cbd5e1;
  font-weight: 600;
}

.arrow-skip {
  font-size: 22px;
  color: var(--alp-color-primary, #2563eb);
  margin-left: 4px;
  animation: skip-bounce 2.4s ease-in-out infinite;
}

@keyframes skip-bounce {
  0%,
  100% {
    transform: translateX(0);
  }
  40% {
    transform: translateX(6px);
  }
}

.arrow-mini {
  color: #64748b;
  font-size: 14px;
}

.slide-head {
  animation: head-pop 2.5s ease-in-out infinite;
}

@keyframes head-pop {
  0%,
  100% {
    transform: translateY(0);
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
  }
  50% {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
  }
}

.flip-row {
  display: flex;
  align-items: center;
  gap: 8px;
  animation: flip-dir 3.2s ease-in-out infinite;
}

.rev-arr {
  color: var(--alp-color-primary, #2563eb);
  font-size: 16px;
  font-weight: 800;
}

@keyframes flip-dir {
  0%,
  45% {
    flex-direction: row;
  }
  50%,
  95% {
    flex-direction: row-reverse;
  }
  100% {
    flex-direction: row;
  }
}

.swap-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.swap-row .a {
  animation: swap-a 2.8s ease-in-out infinite;
}

.swap-row .b {
  animation: swap-b 2.8s ease-in-out infinite;
}

.gap {
  width: 16px;
}

@keyframes swap-a {
  0%,
  15% {
    transform: translateX(0);
  }
  35%,
  65% {
    transform: translateX(42px);
  }
  85%,
  100% {
    transform: translateX(0);
  }
}

@keyframes swap-b {
  0%,
  15% {
    transform: translateX(0);
  }
  35%,
  65% {
    transform: translateX(-42px);
  }
  85%,
  100% {
    transform: translateX(0);
  }
}

.track {
  display: flex;
  gap: 4px;
}

.slot {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #e2e8f0;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  display: grid;
  place-items: center;
}

.twoptr {
  flex-direction: column;
  gap: 8px;
}

.markers {
  position: relative;
  width: 100%;
  max-width: 200px;
  height: 24px;
  margin-top: 2px;
}

.tag {
  position: absolute;
  left: 0;
  top: 0;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  will-change: transform;
}

.tag.slow {
  background: #2563eb;
  animation: ptr-slow 4s ease-in-out infinite;
}

.tag.fast {
  background: #ea580c;
  animation: ptr-fast 4s ease-in-out infinite;
}

@keyframes ptr-slow {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(168px);
  }
}

@keyframes ptr-fast {
  0% {
    transform: translateX(0);
  }
  22% {
    transform: translateX(112px);
  }
  100% {
    transform: translateX(168px);
  }
}

.meet-svg {
  width: 100%;
  max-width: 280px;
  height: auto;
  display: block;
}

.path-a,
.path-b {
  stroke-dasharray: 120;
  stroke-dashoffset: 120;
  animation: draw-line 2.4s ease forwards infinite;
}

.path-b {
  animation-delay: 0.15s;
}

@keyframes draw-line {
  0% {
    stroke-dashoffset: 120;
  }
  45%,
  100% {
    stroke-dashoffset: 0;
  }
}

.pulse-dot {
  animation: meet-pulse 1.8s ease-in-out infinite;
}

@keyframes meet-pulse {
  0%,
  100% {
    opacity: 0.65;
  }
  50% {
    opacity: 1;
  }
}

.ring-stage {
  position: relative;
  width: 108px;
  height: 108px;
}

.ring-orbit {
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  border: 2px dashed #cbd5e1;
  background: rgba(255, 255, 255, 0.5);
}

.ring-runner {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 0;
  height: 0;
}

.ring-dot {
  display: block;
  width: 10px;
  height: 10px;
  margin-left: -5px;
  margin-top: -42px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
}

.ring-dot--slow {
  background: #2563eb;
}

.ring-dot--fast {
  background: #9e6e4a;
  width: 9px;
  height: 9px;
  margin-left: -4.5px;
}

.ring-runner--slow {
  animation: ring-spin 8s linear infinite;
}

.ring-runner--fast {
  animation: ring-spin 4s linear infinite;
}

@keyframes ring-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.pill {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #475569;
  animation: pill-glow 2.8s ease-in-out infinite;
}

.pill:nth-child(2) {
  animation-delay: 0.2s;
}
.pill:nth-child(3) {
  animation-delay: 0.4s;
}
.pill:nth-child(4) {
  animation-delay: 0.6s;
}
.pill:nth-child(5) {
  animation-delay: 0.8s;
}

@keyframes pill-glow {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
    border-color: #e2e8f0;
  }
  50% {
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
    border-color: #93c5fd;
  }
}

@media (prefers-reduced-motion: reduce) {
  .arrow-shaft,
  .arrow-head,
  .node.ghost,
  .arrow-skip,
  .slide-head,
  .flip-row,
  .swap-row .a,
  .swap-row .b,
  .tag.slow,
  .tag.fast,
  .path-a,
  .path-b,
  .pulse-dot,
  .pill,
  .ring-runner--slow,
  .ring-runner--fast {
    animation: none !important;
  }

  .path-a,
  .path-b {
    stroke-dashoffset: 0;
  }
}
</style>
