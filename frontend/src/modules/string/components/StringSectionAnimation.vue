<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { VideoPause, VideoPlay, RefreshRight, DArrowRight } from '@element-plus/icons-vue'

const props = defineProps<{
  sectionId: string
}>()

const STEP_MS = 880
/** 剑指 05 示意：尾部缓冲区写入 %20（读指针在空格原位置） */
const FILL_DEMO_CELLS = ['a', '□', 'c', '·', '·', '%', '2', '0'] as const

let tick: ReturnType<typeof setInterval> | null = null

const playing = ref(true)
const step = ref(0)

const label = computed(() => {
  const m: Record<string, string> = {
    theory: '语言差异：字符序列既可「原地改写」也可能「不可变」',
    'reverse-string': '对称交换：左右指针向中间收拢',
    'reverse-string-ii': '分段：每 2k 里反转前 k 个',
    'replace-space': '从后往前双指针：避免覆盖未读字符',
    'reverse-words': '整体反转 + 单词内再反转（示意）',
    'left-rotate': '三次反转：等价于把左段搬到右侧',
    kmp: '失配时模式串利用 next「跳到最长前缀」',
    'repeated-substring': '周期串：next 数组与长度的整除关系',
    summary: '字符串篇：双指针 · 反转族 · KMP',
  }
  return m[props.sectionId] ?? '本节知识点示意'
})

const maxStep = computed(() => {
  switch (props.sectionId) {
    case 'reverse-string':
      return 3
    case 'reverse-string-ii':
      return 3
    case 'replace-space':
      return 3
    case 'reverse-words':
      return 3
    case 'left-rotate':
      return 4
    case 'kmp':
      return 5
    case 'repeated-substring':
      return 3
    case 'theory':
    case 'summary':
      return 3
    default:
      return 3
  }
})

const useStepped = computed(() => maxStep.value > 0)

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'reverse-string') {
    const t = ['左右指针卡在首尾，准备交换对称位置', '交换最外侧一对字符', '交换内侧一对字符', '指针相遇，反转完成']
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'reverse-string-ii') {
    const t = [
      'k=2、2k=4：每组只反转前 2 个字符',
      '第 1 组 [a,b] 参与反转（高亮段）',
      '第 2 组 [e,f] 参与反转',
      '末尾不足 2k 时，剩余若 ≤k 则整段反转',
    ]
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'replace-space') {
    const t = [
      '先数空格，计算扩容后的总长度',
      '读指针、写指针从尾部对齐：先填末尾',
      '遇到空格则从写指针起依次落位：先写末尾的 0，再 2，再 %（整体仍是 %20）',
      '从左往右会覆盖未读区；从后往前才安全',
    ]
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'reverse-words') {
    const t = [
      '原串：单词内顺序不变，只调整单词先后顺序',
      '① 快慢指针去掉冗余空格',
      '② 整体反转（单词内也被反转）',
      '③ 对每个单词区间再反转 → 151 标准套路',
    ]
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'left-rotate') {
    const t = [
      '目标：把左段搬到右侧，相对顺序不变',
      '① 反转左半段（仅内部调序）',
      '② 反转右半段',
      '③ 反转整串 → 左段整体出现在右侧',
      '与「旋转数组」同一套三反转模板',
    ]
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'kmp') {
    const t = [
      '暴力：主串指针 i 每次回退',
      'aabaaf 前缀表（不减一）：0 1 0 1 2 0',
      '末位失配：看前一格前缀表值 2 → 跳到 b',
      'KMP：主串 i 不动，模式串 j 回退',
      '构造 next 为模式串自匹配',
      '整体 O(n+m)',
    ]
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'repeated-substring') {
    const t = [
      '重复串由最小单元铺满',
      's+s 掐头去尾后仍含 s',
      'KMP：len % (len - next[len-1]) == 0',
      '两套 next 定义勿混用公式',
    ]
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  return ''
})

const _KMP_PREFIX_AABAAF = [0, 1, 0, 1, 2, 0] as const
const _KMP_PATTERN = ['a', 'a', 'b', 'a', 'a', 'f'] as const
void _KMP_PREFIX_AABAAF
void _KMP_PATTERN

/** 344：可变的字符展示 */
const revChars = ref(['h', 'e', 'l', 'l', 'o'])

watch(
  () => [props.sectionId, step.value] as const,
  () => {
    if (props.sectionId !== 'reverse-string') return
    const base = ['h', 'e', 'l', 'l', 'o']
    const a = [...base]
    if (step.value >= 1) {
      ;[a[0], a[4]] = [a[4], a[0]]
    }
    if (step.value >= 2) {
      ;[a[1], a[3]] = [a[3], a[1]]
    }
    revChars.value = a
  },
  { immediate: true },
)

/** 541：k=2, 2k=4 高亮组 */
const segHighlight = computed(() => {
  const i = step.value
  // indices 0-7, highlight "first k of each 2k block"
  const hot = new Set<number>()
  if (i === 1) {
    hot.add(0)
    hot.add(1)
  } else if (i === 2) {
    hot.add(4)
    hot.add(5)
  } else if (i === 3) {
    hot.add(6)
    hot.add(7)
  }
  return hot
})

const segLetters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

/** 已落到最终位置的字符下标（自两端向里，与分步序号一致） */
function revSettledIdx(idx: number, n: number, s: number): boolean {
  return s > 0 && (idx < s || idx > n - 1 - s)
}

/** 当前轮到交换或已汇合的左右指针位置 */
const revPairIdx = computed(() => {
  const n = revChars.value.length
  const s = step.value
  if (s >= 3) return { lo: Math.floor(n / 2), hi: Math.floor((n - 1) / 2) }
  return { lo: s, hi: n - 1 - s }
})

/** 58-II 三反转：abc | defgh → 演示 */
const rotStages = computed(() => {
  const i = step.value
  const left = 'abc'
  const right = 'defgh'
  if (i <= 0) return { mode: 'split' as const, left, right, note: '初始划分' }
  if (i === 1) return { mode: 'split' as const, left: 'cba', right, note: '① 反左段' }
  if (i === 2) return { mode: 'split' as const, left: 'cba', right: 'hgfed', note: '② 反右段' }
  if (i === 3) return { mode: 'merged' as const, text: 'defghabc', note: '③ 反整体 → 左旋转结果' }
  return { mode: 'merged' as const, text: 'defghabc', note: '与力扣 189「轮转数组」同一套三反转模板' }
})

function clearTick() {
  if (tick) {
    clearInterval(tick)
    tick = null
  }
}

function armTick() {
  clearTick()
  if (!useStepped.value || !playing.value) return
  const m = maxStep.value
  if (m <= 0) return
  tick = setInterval(() => {
    step.value = step.value >= m ? 0 : step.value + 1
  }, STEP_MS)
}

function togglePlay() {
  playing.value = !playing.value
  armTick()
}

function manualNext() {
  const m = maxStep.value
  step.value = step.value >= m ? 0 : step.value + 1
}

function resetAnim() {
  step.value = 0
  if (props.sectionId === 'reverse-string') {
    revChars.value = ['h', 'e', 'l', 'l', 'o']
  }
  armTick()
}

watch(
  () => props.sectionId,
  () => {
    resetAnim()
  },
)

watch([playing, useStepped, maxStep], armTick)

onMounted(() => {
  playing.value = true
  armTick()
})

onUnmounted(() => {
  clearTick()
})
</script>

<template>
  <figure class="str-anim" role="img" :aria-label="label">
    <figcaption class="str-anim-caption">{{ label }}</figcaption>

    <div v-if="useStepped" class="anim-toolbar" role="group" aria-label="演示控制">
      <el-button-group size="small">
        <el-button
          :icon="playing ? VideoPause : VideoPlay"
          @click="togglePlay"
        >
          {{ playing ? '暂停' : '播放' }}
        </el-button>
        <el-button :icon="DArrowRight" @click="manualNext">下一步</el-button>
        <el-button :icon="RefreshRight" @click="resetAnim">重置</el-button>
      </el-button-group>
      <span class="anim-toolbar-meta">帧 {{ step + 1 }} / {{ maxStep + 1 }}</span>
    </div>
    <p v-if="useStepped && stepHint" class="step-desc" aria-live="polite" aria-atomic="true">{{ stepHint }}</p>

    <!-- 理论：可变 vs 不可变 -->
    <div v-if="sectionId === 'theory'" class="panel theory">
      <div class="lang-row">
        <span class="chip chip-cpp">C++</span>
        <span class="chip-arrow">⇄</span>
        <span class="chip chip-mut">可原地</span>
      </div>
      <div class="lang-row">
        <span class="chip chip-java">Java</span>
        <span class="chip-arrow">→</span>
        <span class="chip chip-im">String 不可变</span>
      </div>
      <div class="lang-row">
        <span class="chip chip-py">Python</span>
        <span class="chip-arrow">→</span>
        <span class="chip chip-im">str 不可变</span>
      </div>
    </div>

    <!-- 344 反转：分步 + 指针（不用额外弹跳动画，避免与分步状态打架） -->
    <div v-else-if="sectionId === 'reverse-string'" class="panel rev">
      <div class="rev-line">
        <span
          v-for="(ch, idx) in revChars"
          :key="idx"
          class="ch"
          :class="{
            'ch-pair':
              step < 3 && (idx === revPairIdx.lo || idx === revPairIdx.hi),
            'ch-done': revSettledIdx(idx, revChars.length, step),
          }"
        >
          {{ ch }}
        </span>
      </div>
      <div class="ptr-row">
        <span class="ptr ptr-l" :style="{ opacity: step >= 3 ? 0.45 : 1 }">L={{ revPairIdx.lo }}</span>
        <span class="ptr-gap" />
        <span class="ptr ptr-r" :style="{ opacity: step >= 3 ? 0.45 : 1 }">R={{ revPairIdx.hi }}</span>
      </div>
    </div>

    <!-- 541 分段 -->
    <div v-else-if="sectionId === 'reverse-string-ii'" class="panel seg">
      <div class="seg-bar" aria-hidden="true">
        <span
          v-for="(c, idx) in segLetters"
          :key="idx"
          class="seg-ch"
          :class="{
            'seg-hot': segHighlight.has(idx) && step === 1,
            'seg-hot2': segHighlight.has(idx) && step === 2,
            'seg-hot3': segHighlight.has(idx) && step === 3,
          }"
        >
          {{ c }}
        </span>
      </div>
      <p class="seg-hint">示例串 8 字符；k=2、2k=4。高亮为「本步要反转的前 k 个」。</p>
    </div>

    <!-- 替换空格：从尾到头 -->
    <div v-else-if="sectionId === 'replace-space'" class="panel fill">
      <div class="fill-visual">
        <div class="fill-track">
          <span
            v-for="(cell, idx) in FILL_DEMO_CELLS"
            :key="idx"
            class="fill-cell"
            :class="{
              'fill-read': step >= 1 && idx === 1,
              'fill-write': step >= 2 && idx >= 5,
              pulse: playing && step >= 2 && idx >= 5,
            }"
          >
            {{ cell }}
          </span>
        </div>
        <div class="fill-arrows" aria-hidden="true">
          <span class="w-reader" :class="{ dim: step < 1 }">读 i →</span>
          <span class="w-writer" :class="{ dim: step < 2 }">← 写 j</span>
        </div>
      </div>
    </div>

    <!-- 151 单词反转 -->
    <div v-else-if="sectionId === 'reverse-words'" class="panel words">
      <div :key="`words-${step}`" class="words-root">
        <div v-if="step === 0" class="words-stage">
          <span class="w">the</span>
          <span class="w">sky</span>
          <span class="w">is</span>
          <span class="w">blue</span>
        </div>
        <div v-else-if="step === 1" class="words-stage words-mono">
          <span class="w">the·sky·is·blue</span>
        </div>
        <div v-else-if="step === 2" class="words-stage words-mono">
          <span class="w w-rev">eulb·si·yks·eht</span>
        </div>
        <div v-else class="words-stage">
          <span class="w w-final">blue</span>
          <span class="w w-final">is</span>
          <span class="w w-final">sky</span>
          <span class="w w-final">the</span>
        </div>
      </div>
    </div>

    <!-- 左旋转：三反转 -->
    <div v-else-if="sectionId === 'left-rotate'" class="panel rot3">
      <div v-if="rotStages.mode === 'split'" class="rot-line">
        <span class="rot-a">{{ rotStages.left }}</span>
        <span class="rot-sep">|</span>
        <span class="rot-b">{{ rotStages.right }}</span>
      </div>
      <div v-else class="rot-line rot-merged">
        <span class="rot-full">{{ rotStages.text }}</span>
      </div>
      <p class="rot-note">{{ rotStages.note }}</p>
      <div class="rot-steps">
        <span class="step" :class="{ on: step >= 1 }">① 反左</span>
        <span class="step" :class="{ on: step >= 2 }">② 反右</span>
        <span class="step" :class="{ on: step >= 3 }">③ 反整体</span>
      </div>
    </div>

    <!-- KMP：失配跳转 -->
    <div v-else-if="sectionId === 'kmp'" class="panel kmp">
      <div class="kmp-text">
        <span class="k-label">主串</span>
        <span class="k-main">a a b a a a c</span>
        <span class="k-label">模式</span>
        <span class="k-pat">a a b a f</span>
      </div>
      <div class="kmp-phases">
        <div v-if="step === 0" class="kmp-row">
          <span class="k-badge k-warn">暴力匹配</span>
          <span class="k-mini">主串指针 i 会回退，已匹配前缀被反复比较</span>
        </div>
        <div v-else-if="step === 1" class="kmp-row">
          <span class="k-badge">KMP 切入点</span>
          <span class="k-mini">先预处理 next；失配时只动模式串 j，主串 i 不回退</span>
        </div>
        <div v-else-if="step === 2" class="kmp-row">
          <span class="k-badge k-warn">在末位失配</span>
          <span class="k-mini">暴力会回退主串；KMP 不回退 i</span>
        </div>
        <div v-else-if="step === 3" class="kmp-row">
          <span class="k-badge">j ← next[j]</span>
          <span class="k-mini">利用已匹配前缀的最长边框</span>
        </div>
        <div v-else class="kmp-row">
          <span class="k-badge k-ok">继续匹配</span>
          <span class="k-mini">主串指针保持，模式串滑到可衔接位置</span>
        </div>
      </div>
      <div class="kmp-jump">
        <span class="j-label">失配 → j 回退</span>
        <span class="j-arrow">↩</span>
      </div>
    </div>

    <!-- 459 周期 -->
    <div v-else-if="sectionId === 'repeated-substring'" class="panel period">
      <div class="period-row">
        <span class="unit unit-a">ab</span>
        <span class="unit unit-b">ab</span>
        <span class="unit unit-c">ab</span>
      </div>
      <p class="period-cap">len − next[len−1] 给出候选周期；再结合整除关系判断重复子串</p>
    </div>

    <!-- 总结 -->
    <div v-else-if="sectionId === 'summary'" class="panel sum">
      <div class="sum-pills">
        <span class="sp">双指针</span>
        <span class="sp">反转</span>
        <span class="sp">KMP</span>
        <span class="sp">周期</span>
      </div>
    </div>
  </figure>
</template>

<style scoped>
.str-anim {
  margin: 0;
  padding: 14px 16px 12px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.str-anim-caption {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
  line-height: 1.45;
}

.anim-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.anim-toolbar-meta {
  font-size: 11px;
  color: var(--alp-color-muted);
  font-weight: 600;
}

.step-desc {
  margin: 0 0 10px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--alp-color-muted);
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--alp-bg-code-ish);
  border: 1px dashed var(--alp-color-border);
}

.anim-note {
  margin: 0 0 10px;
  font-size: 11px;
  color: var(--alp-color-muted);
}

.panel {
  min-height: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.theory {
  gap: 6px;
}

.lang-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.chip {
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 700;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid);
  color: var(--alp-color-text);
}

.chip-cpp {
  color: #0369a1;
  border-color: #7dd3fc;
}
.chip-java {
  color: #b45309;
  border-color: #fcd34d;
}
.chip-py {
  color: #15803d;
  border-color: #86efac;
}
.chip-mut {
  animation: chip-pulse 2.4s ease-in-out infinite;
}
.chip-im {
  opacity: 0.85;
}

.chip-arrow {
  color: #64748b;
  font-size: 12px;
}

@keyframes chip-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(14, 165, 233, 0);
  }
  50% {
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.2);
  }
}

.rev-line {
  display: flex;
  gap: 4px;
}

.ch {
  display: grid;
  place-items: center;
  width: 28px;
  height: 30px;
  border-radius: 6px;
  background: #fff;
  border: 2px solid #94a3b8;
  font-weight: 700;
  font-size: 14px;
  color: #334155;
  transition:
    border-color 0.25s,
    background 0.25s,
    transform 0.25s;
}

.ch-pair {
  border-color: var(--alp-color-primary, #0ea5e9);
  background: #e0f2fe;
  transform: scale(1.06);
}

.ch-done {
  border-color: #86efac;
  background: #ecfdf5;
}

.ptr-row {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 240px;
  position: relative;
  height: 22px;
}

.ptr-gap {
  flex: 1;
}

.ptr {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 6px;
  color: #fff;
}

.ptr-l {
  background: #2563eb;
}

.ptr-r {
  background: #ea580c;
}

.seg-bar {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
  justify-content: center;
}

.seg-ch {
  width: 26px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #e2e8f0;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  transition:
    box-shadow 0.25s,
    border-color 0.25s,
    color 0.25s;
}

.seg-hot {
  border-color: #38bdf8;
  color: #0369a1;
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.28);
}

.seg-hot2 {
  border-color: #a78bfa;
  color: #5b21b6;
  box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.35);
}

.seg-hot3 {
  border-color: #f97316;
  color: #9a3412;
  box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.28);
}

.seg-hint {
  margin: 0;
  font-size: 11px;
  color: #64748b;
  text-align: center;
  max-width: 320px;
}

.fill-visual {
  width: 100%;
  max-width: 260px;
}

.fill-track {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.fill-cell {
  width: 22px;
  height: 26px;
  border-radius: 4px;
  background: #f1f5f9;
  border: 1px dashed #cbd5e1;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  transition:
    border-color 0.25s,
    background 0.25s;
}

.fill-read {
  border-color: #2563eb;
  border-style: solid;
  background: #dbeafe;
}

.fill-write {
  border-color: #ea580c;
  border-style: solid;
  background: #ffedd5;
}

.fill-cell.pulse {
  animation: fill-pulse 2s ease-in-out infinite;
}

@keyframes fill-pulse {
  0%,
  100% {
    opacity: 0.75;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

.fill-arrows {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
}

.w-reader {
  color: #2563eb;
}
.w-writer {
  color: #ea580c;
}
.dim {
  opacity: 0.35;
}

.words-root {
  width: 100%;
  display: flex;
  justify-content: center;
  min-height: 44px;
  align-items: center;
}

.words-stage {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
  min-height: 40px;
  align-items: center;
}

.words-mono .w-rev {
  font-family: ui-monospace, monospace;
  letter-spacing: 0.04em;
}

.w {
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 13px;
  background: #fff;
  border: 1px solid #e2e8f0;
  animation: word-pop 0.35s ease;
}

.w-final {
  border-color: #86efac;
  background: #f0fdf4;
}

@keyframes word-pop {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.rot-line {
  display: flex;
  gap: 8px;
  align-items: center;
  font-family: ui-monospace, monospace;
  font-weight: 700;
  font-size: 15px;
}

.rot-sep {
  color: #94a3b8;
  font-weight: 400;
}

.rot-a {
  padding: 4px 8px;
  border-radius: 6px;
  background: #e0f2fe;
  border: 1px solid #7dd3fc;
}

.rot-b {
  padding: 4px 8px;
  border-radius: 6px;
  background: #fef3c7;
  border: 1px solid #fcd34d;
}

.rot-merged {
  justify-content: center;
}

.rot-full {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 16px;
  letter-spacing: 0.06em;
  background: linear-gradient(90deg, #e0f2fe 0%, #fef3c7 100%);
  border: 2px solid #38bdf8;
  color: #0f172a;
}

.rot-note {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.rot-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  font-size: 11px;
  color: #64748b;
}

.step {
  padding: 2px 6px;
  border-radius: 4px;
  background: #f8fafc;
  border: 1px solid transparent;
  transition:
    border-color 0.2s,
    background 0.2s;
}

.step.on {
  border-color: #38bdf8;
  background: #e0f2fe;
  color: #0369a1;
  font-weight: 700;
}

.kmp-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  letter-spacing: 0.06em;
  align-self: stretch;
}

.k-label {
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.k-main {
  color: #64748b;
}

.k-pat {
  color: #0f172a;
  font-weight: 700;
  border-bottom: 2px solid #38bdf8;
}

.kmp-phases {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kmp-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
}

.k-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #334155;
}

.k-badge.k-warn {
  background: #fef3c7;
  color: #92400e;
}

.k-badge.k-ok {
  background: #dcfce7;
  color: #166534;
}

.k-mini {
  font-size: 11px;
  color: #64748b;
  max-width: 280px;
  line-height: 1.45;
}

.kmp-jump {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
}

.j-arrow {
  font-size: 20px;
  animation: jump-bounce 1.4s ease-in-out infinite;
}

@keyframes jump-bounce {
  0%,
  100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-8px);
  }
}

.period-row {
  display: flex;
  gap: 6px;
}

.period-cap {
  margin: 0;
  font-size: 11px;
  color: #64748b;
  text-align: center;
  max-width: 300px;
  line-height: 1.45;
}

.unit {
  padding: 6px 12px;
  border-radius: 8px;
  font-weight: 800;
  font-size: 14px;
  background: #fff;
  border: 2px solid #c4b5fd;
  color: #5b21b6;
  animation: unit-breathe 2.4s ease-in-out infinite;
}

.unit-b {
  animation-delay: 0.15s;
}
.unit-c {
  animation-delay: 0.3s;
}

@keyframes unit-breathe {
  0%,
  100% {
    transform: scale(1);
    box-shadow: none;
  }
  50% {
    transform: scale(1.04);
    box-shadow: 0 2px 10px rgba(139, 92, 246, 0.25);
  }
}

.sum-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.sp {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #fff;
  border: 1px solid #e2e8f0;
  animation: sp-glow 2.6s ease-in-out infinite;
}

.sp:nth-child(2) {
  animation-delay: 0.15s;
}
.sp:nth-child(3) {
  animation-delay: 0.3s;
}
.sp:nth-child(4) {
  animation-delay: 0.45s;
}

@keyframes sp-glow {
  0%,
  100% {
    border-color: #e2e8f0;
  }
  50% {
    border-color: #818cf8;
    color: #4338ca;
  }
}

@media (prefers-reduced-motion: reduce) {
  .chip-mut,
  .fill-cell.pulse,
  .j-arrow,
  .unit,
  .sp,
  .w {
    animation: none !important;
  }
}
</style>
