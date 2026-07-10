<script setup lang="ts">
/**
 * 数组各小节「直觉示意」纯 CSS 动画（与全局暗色 / 终端风变量一致）。
 * prefers-reduced-motion：关闭循环动画，保留静态关键帧。
 */
defineProps<{
  sectionId: string
}>()

const spiralDelays = [0, 0.1, 0.2, 0.7, 0.8, 0.3, 0.6, 0.5, 0.4]
</script>

<template>
  <div class="anim-root">
    <p class="anim-note">以下为示意动画，帮助建立直觉；具体边界以题面与代码为准。</p>

    <div v-if="sectionId === 'theory'" class="panel" role="img" aria-label="数组删除示意">
      <p class="panel-title">连续存储：删除中间元素后，后续元素前移覆盖</p>
      <div class="theory-row">
        <span class="cell">a</span>
        <span class="cell">b</span>
        <span class="cell cell-x">x</span>
        <span class="cell cell-slide">c</span>
      </div>
    </div>

    <div v-else-if="sectionId === 'binary-search'" class="panel" role="img" aria-label="二分区间收拢示意">
      <p class="panel-title">二分：维护有效区间，每次大约排除一半</p>
      <div class="bin-visual">
        <span class="bin-label bin-l">L</span>
        <div class="bin-track">
          <div class="bin-fill" />
          <span class="bin-mid">mid</span>
        </div>
        <span class="bin-label bin-r">R</span>
      </div>
    </div>

    <div v-else-if="sectionId === 'remove-element'" class="panel" role="img" aria-label="快慢指针示意">
      <p class="panel-title">快慢指针：快指针扫描，慢指针指向下一个写入位置</p>
      <div class="ptr-track">
        <div class="ptr-cells">
          <span v-for="i in 7" :key="i" class="pcell" />
        </div>
        <div class="ptr-slow">慢</div>
        <div class="ptr-fast">快</div>
      </div>
    </div>

    <div v-else-if="sectionId === 'sorted-squares'" class="panel" role="img" aria-label="双端指针示意">
      <p class="panel-title">有序平方：较大平方值总在两端之一产生</p>
      <div class="sq-row">
        <span class="sq-end sq-i">i</span>
        <span class="sq-gap" />
        <span class="sq-end sq-j">j</span>
      </div>
      <p class="sq-cap">两端比较 → 结果从后往前填</p>
    </div>

    <div v-else-if="sectionId === 'min-subarray'" class="panel" role="img" aria-label="滑动窗口示意">
      <p class="panel-title">滑动窗口：右端扩展，满足条件时左端收缩</p>
      <div class="win-track">
        <span v-for="i in 8" :key="i" class="wcell" />
        <div class="win-box" />
      </div>
    </div>

    <div v-else-if="sectionId === 'spiral'" class="panel" role="img" aria-label="螺旋填格顺序示意">
      <p class="panel-title">螺旋矩阵：按圈遍历，统一拐角规则</p>
      <div class="spiral-grid">
        <span
          v-for="(d, idx) in spiralDelays"
          :key="idx"
          class="sg"
          :style="{ animationDelay: `${d}s` }"
        />
      </div>
    </div>

    <div v-else-if="sectionId === 'summary'" class="panel" role="img" aria-label="知识主线">
      <p class="panel-title">数组篇四条主线</p>
      <div class="flow-line">
        <span class="flow-node">二分</span>
        <span class="flow-arrow">→</span>
        <span class="flow-node">双指针</span>
        <span class="flow-arrow">→</span>
        <span class="flow-node">滑窗</span>
        <span class="flow-arrow">→</span>
        <span class="flow-node">模拟</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.anim-root {
  margin: 0;
  padding: 16px 18px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  box-shadow: var(--alp-shadow-card);
}

.anim-note {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--alp-color-muted);
}

.panel-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-text);
}

/* 理论 */
.theory-row {
  display: flex;
  gap: 6px;
  align-items: flex-end;
}

.cell {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  background: var(--alp-nav-index-bg);
  border-radius: 8px;
  font-weight: 600;
  color: var(--alp-nav-index-fg);
  border: 1px solid var(--alp-color-border);
}

.cell-x {
  animation: cell-vanish 2.8s ease-in-out infinite;
}

.cell-slide {
  animation: cell-shift 2.8s ease-in-out infinite;
}

@keyframes cell-vanish {
  0%,
  18% {
    opacity: 1;
    transform: scale(1);
  }
  28%,
  100% {
    opacity: 0.25;
    transform: scale(0.65);
  }
}

@keyframes cell-shift {
  0%,
  28% {
    transform: translateX(0);
  }
  42%,
  100% {
    transform: translateX(-42px);
  }
}

/* 二分 */
.bin-visual {
  display: flex;
  align-items: center;
  gap: 8px;
  width: min(100%, 420px);
}

.bin-label {
  font-size: 12px;
  font-weight: 800;
  color: var(--alp-color-primary);
  width: 18px;
  text-align: center;
  animation: bin-nudge 2.6s ease-in-out infinite;
}

.bin-r {
  animation-delay: 0.1s;
}

.bin-track {
  flex: 1;
  position: relative;
  height: 36px;
  display: flex;
  align-items: center;
}

.bin-fill {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 10px;
  margin-top: -5px;
  border-radius: 5px;
  background: linear-gradient(
    90deg,
    var(--alp-color-primary-soft),
    var(--alp-color-primary),
    var(--alp-color-primary-soft)
  );
  opacity: 0.9;
  animation: bin-shrink 2.6s ease-in-out infinite;
  transform-origin: center center;
}

.bin-mid {
  position: relative;
  z-index: 1;
  margin: 0 auto;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--alp-bg-surface-solid);
  color: var(--alp-color-primary);
  border: 1px solid var(--alp-color-border);
  animation: mid-pulse 2.6s ease-in-out infinite;
}

@keyframes bin-shrink {
  0%,
  100% {
    transform: scaleX(1);
  }
  50% {
    transform: scaleX(0.38);
  }
}

@keyframes bin-nudge {
  0%,
  100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(3px);
  }
}

@keyframes mid-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(34, 211, 238, 0.35);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(34, 211, 238, 0);
  }
}

/* 快慢指针 */
.ptr-track {
  position: relative;
  padding-top: 30px;
}

.ptr-cells {
  display: flex;
  gap: 5px;
}

.pcell {
  width: 28px;
  height: 22px;
  border-radius: 4px;
  background: rgba(51, 65, 85, 0.9);
  border: 1px solid var(--alp-color-border);
}

.ptr-slow,
.ptr-fast {
  position: absolute;
  top: 0;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 7px;
  border-radius: 4px;
  color: #0f172a;
}

.ptr-slow {
  left: 0;
  background: rgba(52, 211, 153, 0.95);
  animation: slow-move 3.2s ease-in-out infinite;
}

.ptr-fast {
  left: 0;
  background: var(--alp-color-primary);
  animation: fast-move 3.2s linear infinite;
}

@keyframes slow-move {
  0%,
  100% {
    transform: translateX(0);
  }
  40% {
    transform: translateX(33px);
  }
  75% {
    transform: translateX(66px);
  }
}

@keyframes fast-move {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(198px);
  }
}

/* 有序平方 */
.sq-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(100%, 360px);
}

.sq-end {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #0f172a;
  animation: sq-pulse 1.6s ease-in-out infinite alternate;
}

.sq-i {
  background: linear-gradient(145deg, var(--alp-color-accent), rgba(129, 140, 248, 0.75));
}

.sq-j {
  background: linear-gradient(145deg, var(--alp-color-primary), rgba(34, 211, 238, 0.75));
}

.sq-gap {
  flex: 1;
  height: 4px;
  margin: 0 12px;
  background: linear-gradient(90deg, transparent, var(--alp-color-border), transparent);
}

.sq-cap {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
}

@keyframes sq-pulse {
  from {
    transform: scale(1);
  }
  to {
    transform: scale(1.06);
  }
}

/* 滑动窗口 */
.win-track {
  position: relative;
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.wcell {
  width: 26px;
  height: 28px;
  border-radius: 4px;
  background: rgba(51, 65, 85, 0.9);
  border: 1px solid var(--alp-color-border);
}

.win-box {
  position: absolute;
  left: 0;
  top: 0;
  width: 86px;
  height: 36px;
  border-radius: 6px;
  border: 2px solid var(--alp-color-primary);
  background: var(--alp-color-primary-soft);
  pointer-events: none;
  animation: win-slide 2.8s ease-in-out infinite;
}

@keyframes win-slide {
  0%,
  100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(92px);
  }
}

/* 螺旋 */
.spiral-grid {
  display: grid;
  grid-template-columns: repeat(3, 36px);
  gap: 6px;
  width: fit-content;
}

.sg {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--alp-nav-index-bg);
  border: 1px solid var(--alp-color-border);
  animation: sg-pop 2.4s ease-in-out infinite;
}

@keyframes sg-pop {
  0%,
  10% {
    background: var(--alp-nav-index-bg);
    transform: scale(1);
  }
  14% {
    background: var(--alp-color-primary);
    transform: scale(1.06);
  }
  22%,
  100% {
    background: rgba(34, 211, 238, 0.35);
    transform: scale(1);
  }
}

/* 小结 */
.flow-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.flow-node {
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--alp-bg-nav-active);
  border: 1px solid rgba(34, 211, 238, 0.35);
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-primary);
  animation: flow-glow 2.2s ease-in-out infinite;
}

.flow-node:nth-child(3) {
  animation-delay: 0.2s;
}
.flow-node:nth-child(5) {
  animation-delay: 0.4s;
}
.flow-node:nth-child(7) {
  animation-delay: 0.6s;
}

.flow-arrow {
  color: var(--alp-color-muted);
  font-weight: 700;
}

@keyframes flow-glow {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(34, 211, 238, 0);
  }
  50% {
    box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.2);
  }
}

@media (prefers-reduced-motion: reduce) {
  .cell-x,
  .cell-slide,
  .bin-fill,
  .bin-label,
  .bin-mid,
  .ptr-slow,
  .ptr-fast,
  .sq-end,
  .win-box,
  .sg,
  .flow-node {
    animation: none !important;
  }

  .cell-x {
    opacity: 0.25;
  }

  .cell-slide {
    transform: translateX(-42px);
  }

  .bin-fill {
    transform: scaleX(0.38);
  }

  .ptr-fast {
    transform: translateX(120px);
  }

  .ptr-slow {
    transform: translateX(66px);
  }

  .win-box {
    transform: translateX(46px);
  }

  .sg {
    background: rgba(34, 211, 238, 0.35);
  }
}
</style>
