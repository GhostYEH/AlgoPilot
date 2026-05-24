# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / "src/components/string/StringSectionAnimation.vue"
old = target.read_text(encoding="utf-8", errors="replace")
style_start = old.find("<style scoped>")
styles = old[style_start:] if style_start >= 0 else ""

script_template = r'''<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { VideoPause, VideoPlay, RefreshRight, DArrowRight } from '@element-plus/icons-vue'

const props = defineProps<{
  sectionId: string
}>()

const STEP_MS = 880
const FILL_DEMO_CELLS = ['a', '□', 'c', '·', '·', '%', '2', '0'] as const

let tick: ReturnType<typeof setInterval> | null = null
let motionMql: MediaQueryList | null = null

const playing = ref(true)
const step = ref(0)
const reduceMotion = ref(false)

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

const steppedSections = new Set([
  'reverse-string',
  'reverse-string-ii',
  'replace-space',
  'reverse-words',
  'left-rotate',
  'kmp',
  'repeated-substring',
])

const useStepped = computed(() => steppedSections.has(props.sectionId))

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
    default:
      return 0
  }
})

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'reverse-string') {
    const t = ['左右指针卡在首尾', '交换最外侧一对', '交换内侧一对', '指针相遇，完成']
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'reverse-string-ii') {
    const t = ['k=2、2k=4', '第 1 组 [a,b] 反转', '第 2 组 [e,f] 反转', '末尾不足 2k 的处理']
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'replace-space') {
    const t = ['先扩容', '双指针从尾对齐', '空格写入 %20', '从后往前才安全']
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'reverse-words') {
    const t = ['原串词序', '① 去冗余空格', '② 整体反转', '③ 逐词反转']
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'left-rotate') {
    const t = ['划分左右段', '① 反左段', '② 反右段', '③ 反整体', '等同 189 轮转']
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'kmp') {
    const t = [
      '暴力：主串 i 回退',
      'aabaaf 前缀表：0 1 0 1 2 0',
      '失配看前一格 → 跳到 b',
      'KMP：i 不动，j 回退',
      '构造 next 为自匹配',
      '整体 O(n+m)',
    ]
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  if (s === 'repeated-substring') {
    const t = ['最小单元重复', 's+s 掐头去尾', 'KMP 周期整除', '两套 next 勿混用']
    return t[Math.min(i, t.length - 1)] ?? ''
  }
  return ''
})

const KMP_PREFIX_AABAAF = [0, 1, 0, 1, 2, 0] as const
const KMP_PATTERN = ['a', 'a', 'b', 'a', 'a', 'f'] as const

const revChars = ref(['h', 'e', 'l', 'l', 'o'])

watch(
  () => [props.sectionId, step.value] as const,
  () => {
    if (props.sectionId !== 'reverse-string') return
    const base = ['h', 'e', 'l', 'l', 'o']
    const a = [...base]
    if (step.value >= 1) [a[0], a[4]] = [a[4], a[0]]
    if (step.value >= 2) [a[1], a[3]] = [a[3], a[1]]
    revChars.value = a
  },
  { immediate: true },
)

const segHighlight = computed(() => {
  const hot = new Set<number>()
  if (step.value === 1) { hot.add(0); hot.add(1) }
  else if (step.value === 2) { hot.add(4); hot.add(5) }
  else if (step.value === 3) { hot.add(6); hot.add(7) }
  return hot
})

const segLetters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

function revSettledIdx(idx: number, n: number, s: number) {
  return s > 0 && (idx < s || idx > n - 1 - s)
}

const revPairIdx = computed(() => {
  const n = revChars.value.length
  const s = step.value
  if (s >= 3) return { lo: Math.floor(n / 2), hi: Math.floor((n - 1) / 2) }
  return { lo: s, hi: n - 1 - s }
})

const rotStages = computed(() => {
  const i = step.value
  const left = 'abc'
  const right = 'defgh'
  if (i <= 0) return { mode: 'split' as const, left, right, note: '初始' }
  if (i === 1) return { mode: 'split' as const, left: 'cba', right, note: '① 反左' }
  if (i === 2) return { mode: 'split' as const, left: 'cba', right: 'hgfed', note: '② 反右' }
  if (i === 3) return { mode: 'merged' as const, text: 'defghabc', note: '③ 反整体' }
  return { mode: 'merged' as const, text: 'defghabc', note: '左旋转结果' }
})

function clearTick() {
  if (tick) { clearInterval(tick); tick = null }
}

function armTick() {
  clearTick()
  if (!useStepped.value || reduceMotion.value || !playing.value) return
  const m = maxStep.value
  if (m <= 0) return
  tick = setInterval(() => { step.value = step.value >= m ? 0 : step.value + 1 }, STEP_MS)
}

function onMotionMqlChange() {
  reduceMotion.value = motionMql?.matches ?? false
  if (reduceMotion.value) { playing.value = false; clearTick() } else armTick()
}

function togglePlay() { playing.value = !playing.value; armTick() }
function manualNext() { const m = maxStep.value; step.value = step.value >= m ? 0 : step.value + 1 }
function resetAnim() {
  step.value = 0
  if (props.sectionId === 'reverse-string') revChars.value = ['h', 'e', 'l', 'l', 'o']
  armTick()
}

watch(() => props.sectionId, resetAnim)
watch([playing, reduceMotion, useStepped, maxStep], armTick)

onMounted(() => {
  motionMql = window.matchMedia?.('(prefers-reduced-motion: reduce)') ?? null
  reduceMotion.value = motionMql?.matches ?? false
  if (reduceMotion.value) playing.value = false
  motionMql?.addEventListener('change', onMotionMqlChange)
  armTick()
})

onUnmounted(() => {
  motionMql?.removeEventListener('change', onMotionMqlChange)
  motionMql = null
  clearTick()
})
</script>

<template>
  <figure class="str-anim" role="img" :aria-label="label">
    <figcaption class="str-anim-caption">{{ label }}</figcaption>
    <div v-if="useStepped" class="anim-toolbar" role="group" aria-label="演示控制">
      <el-button-group size="small">
        <el-button :disabled="reduceMotion" :icon="playing ? VideoPause : VideoPlay" @click="togglePlay">
          {{ playing ? '暂停' : '播放' }}
        </el-button>
        <el-button :icon="DArrowRight" @click="manualNext">下一步</el-button>
        <el-button :icon="RefreshRight" @click="resetAnim">重置</el-button>
      </el-button-group>
      <span class="anim-toolbar-meta">帧 {{ step + 1 }} / {{ maxStep + 1 }}</span>
    </motion>
    <p v-if="useStepped && stepHint" class="step-desc">{{ stepHint }}</p>
    <p v-if="!useStepped" class="anim-note">循环示意；系统「减少动态效果」下为静态画面。</p>

    <div v-if="sectionId === 'theory'" class="panel theory">
      <div class="lang-row"><span class="chip chip-c">C</span><span class="chip-arrow">→</span><span class="chip chip-im">char[] + '\\0'</span></div>
      <div class="lang-row"><span class="chip chip-cpp">C++</span><span class="chip-arrow">⇄</span><span class="chip chip-mut">string 可原地</span></div>
      <div class="lang-row"><span class="chip chip-java">Java</span><span class="chip-arrow">→</span><span class="chip chip-im">String 不可变</span></div>
      <div class="lang-row"><span class="chip chip-py">Python</span><span class="chip-arrow">→</span><span class="chip chip-im">str 不可变</span></div>
      <p class="theory-foot">关键步骤勿滥用 reverse/split；erase 在循环中为 O(n²)。</p>
    </motion>

    <div v-else-if="sectionId === 'reverse-string'" class="panel rev">
      <motion class="rev-line">
        <span v-for="(ch, idx) in revChars" :key="idx" class="ch" :class="{ 'ch-pair': step < 3 && (idx === revPairIdx.lo || idx === revPairIdx.hi), 'ch-done': revSettledIdx(idx, revChars.length, step) }">{{ ch }}</span>
      </motion>
      <div class="ptr-row"><span class="ptr ptr-l">L={{ revPairIdx.lo }}</span><span class="ptr-gap" /><span class="ptr ptr-r">R={{ revPairIdx.hi }}</span></div>
    </motion>

    <div v-else-if="sectionId === 'reverse-string-ii'" class="panel seg">
      <div class="seg-bar">
        <span v-for="(c, idx) in segLetters" :key="idx" class="seg-ch" :class="{ 'seg-hot': segHighlight.has(idx) && step === 1, 'seg-hot2': segHighlight.has(idx) && step === 2, 'seg-hot3': segHighlight.has(idx) && step === 3 }">{{ c }}</span>
      </motion>
      <p class="seg-hint">k=2、2k=4；高亮为每段前 k 个</p>
    </motion>

    <div v-else-if="sectionId === 'replace-space'" class="panel fill">
      <div class="fill-track">
        <span v-for="(cell, idx) in FILL_DEMO_CELLS" :key="idx" class="fill-cell" :class="{ 'fill-read': step >= 1 && idx === 1, 'fill-write': step >= 2 && idx >= 5 }">{{ cell }}</span>
      </motion>
    </motion>

    <div v-else-if="sectionId === 'reverse-words'" class="panel words">
      <div v-if="step === 0" class="words-stage"><span class="w">the</span><span class="w">sky</span><span class="w">is</span><span class="w">blue</span></motion>
      <div v-else-if="step === 1" class="words-stage words-mono"><span class="w">the·sky·is·blue</span></motion>
      <motion v-else-if="step === 2" class="words-stage words-mono"><span class="w w-rev">eulb·si·yks·eht</span></motion>
      <div v-else class="words-stage"><span class="w w-final">blue</span><span class="w w-final">is</span><span class="w w-final">sky</span><span class="w w-final">the</span></motion>
    </motion>

    <div v-else-if="sectionId === 'left-rotate'" class="panel rot3">
      <div v-if="rotStages.mode === 'split'" class="rot-line"><span class="rot-a">{{ rotStages.left }}</span><span class="rot-sep">|</span><span class="rot-b">{{ rotStages.right }}</span></motion>
      <div v-else class="rot-line rot-merged"><span class="rot-full">{{ rotStages.text }}</span></motion>
      <p class="rot-note">{{ rotStages.note }}</p>
    </motion>

    <motion v-else-if="sectionId === 'kmp'" class="panel kmp">
      <div v-if="step === 1" class="kmp-prefix">
        <span class="k-label">前缀表 aabaaf</span>
        <div class="kmp-prefix-row">
          <span v-for="(ch, i) in KMP_PATTERN" :key="'c'+i" class="kp-ch">{{ ch }}</span>
        </motion>
        <div class="kmp-prefix-row">
          <span v-for="(v, i) in KMP_PREFIX_AABAAF" :key="'n'+i" class="kp-num">{{ v }}</span>
        </motion>
      </motion>
      <div v-else class="kmp-text">
        <span class="k-label">主串</span><span class="k-main">aabaabaafa</span>
        <span class="k-label">模式</span><span class="k-pat">aabaaf</span>
      </motion>
      <p class="k-mini">{{ stepHint }}</p>
    </motion>

    <div v-else-if="sectionId === 'repeated-substring'" class="panel period">
      <template v-if="step === 0"><motion class="period-row"><span class="unit">ab</span><span class="unit">ab</span><span class="unit">ab</span></motion></template>
      <template v-else-if="step === 1"><p class="period-cap mono">(ababab+ababab).slice(1,-1) 含 ababab</p></template>
      <template v-else-if="step === 2"><p class="period-cap mono">len % (len - next[len-1]) == 0</p></template>
      <p v-else class="period-cap">结合 next 定义选用对应公式</p>
    </motion>

    <div v-else-if="sectionId === 'summary'" class="panel sum">
      <div class="sum-pills"><span class="sp">双指针</span><span class="sp">反转</span><span class="sp">KMP</span><span class="sp">周期</span></motion>
    </motion>
  </figure>
</template>

'''

# Fix accidental motion tags in template string
script_template = script_template.replace('</motion>', '</div>').replace('<motion ', '<motion ').replace('<motion ', '<div ').replace('</motion>', '</motion>')
# second pass: motion -> div for tags
import re
script_template = re.sub(r'</motion>', '</div>', script_template)
script_template = re.sub(r'<motion(\s)', r'<div\1', script_template)

extra_style = """
.chip-c { color: #7c2d12; border-color: #fdba74; }
.theory-foot { margin: 0; font-size: 11px; color: #64748b; text-align: center; max-width: 300px; }
.kmp-prefix { display: flex; flex-direction: column; gap: 6px; align-items: center; }
.kmp-prefix-row { display: flex; gap: 4px; }
.kp-ch, .kp-num { width: 24px; height: 26px; display: grid; place-items: center; border-radius: 4px; font-size: 11px; font-weight: 700; }
.kp-ch { background: #e0f2fe; border: 1px solid #7dd3fc; }
.kp-num { background: #fef3c7; border: 1px solid #fcd34d; color: #92400e; }
.period-cap.mono { font-family: ui-monospace, monospace; font-size: 10px; }
"""

if "@media (prefers-reduced-motion" in styles:
    styles = styles.replace("@media (prefers-reduced-motion", extra_style + "\n@media (prefers-reduced-motion")
else:
    styles += extra_style

target.write_text(script_template + "\n" + styles, encoding="utf-8")
print("restored", target, "bytes", target.stat().st_size)
