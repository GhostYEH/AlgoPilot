<script setup lang="ts">
import { computed, ref, toRef, watch } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'

const props = defineProps<{ sectionId: string }>()
const sectionIdRef = toRef(props, 'sectionId')

function maxStepForSection(id: string) {
  const m: Record<string, number> = {
    theory: 0,
    'valid-anagram': 4,
    intersection: 3,
    'happy-number': 4,
    'two-sum': 3,
    'four-sum-ii': 3,
    'ransom-note': 3,
    'three-sum': 4,
    'four-sum': 4,
    summary: 3,
  }
  return m[id] ?? 3
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

/** 理论基础：数组 / set / map 三套独立分步动画 */
const theoryArrayId = ref('ht-theory-array')
const theorySetId = ref('ht-theory-set')
const theoryMapId = ref('ht-theory-map')

const arrayTheory = useSteppedAnimation({
  sectionId: theoryArrayId,
  maxStepForSection: () => 3,
  stepMs: 900,
})
const setTheory = useSteppedAnimation({
  sectionId: theorySetId,
  maxStepForSection: () => 3,
  stepMs: 950,
})
const mapTheory = useSteppedAnimation({
  sectionId: theoryMapId,
  maxStepForSection: () => 3,
  stepMs: 900,
})

const ARRAY_HINTS = [
  '扫描 s，对字符 c 执行 count[c−\'a\']++',
  '继续累加各字母频次',
  '扫描 t 时 count[c−\'a\']--',
  '26 个槽位全为 0 → 异位词成立',
]
const SET_HINTS = [
  '空集合，准备 O(1) 查存在',
  'insert(2)：2 入集合',
  'insert(5)：5 入集合',
  'contains(2) 为真；重复插入不改变集合',
]
const MAP_HINTS = [
  '空 map：仅存 key→value 配对',
  'put(2,0)：值 2 对应下标 0',
  'put(7,1)：值 7 对应下标 1',
  'get(2) 均摊 O(1) 取下标',
]

watch(
  () => props.sectionId,
  (id) => {
    if (id !== 'theory') return
    arrayTheory.resetAnim()
    setTheory.resetAnim()
    mapTheory.resetAnim()
  },
)

const caption = computed(() => {
  const m: Record<string, string> = {
    theory: '定长数组 · 哈希集合 · 哈希映射 — 刷题三件套',
    'valid-anagram': '242：int[26] 计数，s 与 t 的 multiset 须一致',
    intersection: '349：较小数组建 set，遍历另一数组查存在',
    'happy-number': '202：set 记录平方和，重复出现则非快乐数',
    'two-sum': '1：先查 map[target−x]，再 put(x→i)',
    'four-sum-ii': '454：A+B 入 map，枚举 C+D 查 −(c+d)',
    'ransom-note': '383：magazine 计数，ransomNote 逐字符消耗',
    'three-sum': '15：排序 + 固定 i + 双指针（非哈希主解）',
    'four-sum': '18：排序 + 固定 k,i + 内层双指针',
    summary: '数组计数 · set 判重 · map 配对 · 双指针对照',
  }
  return m[props.sectionId] ?? '哈希表示意'
})

const stepHint = computed(() => {
  const s = props.sectionId
  const i = step.value
  if (s === 'valid-anagram') {
    return [
      '扫描 s="rat"：r→1, a→1, t→1',
      '扫描 t="tar"：逐字符 count--',
      'r,a,t 对应槽位均归零',
      '频次数组全 0 → return true',
      '242 核心：值域小用定长数组',
    ][i] ?? ''
  }
  if (s === 'intersection') {
    return [
      'nums2=[2,2] 较小 → 建 set {2}',
      '遍历 nums1=[1,2,2,1]，2 在 set 中',
      '结果去重得 [2]（顺序不限）',
      '值域未知时优先 unordered_set',
    ][i] ?? ''
  }
  if (s === 'happy-number') {
    return [
      'n=19 → 各位平方和 82，记入 set',
      '82→68→100，每次新和入 set',
      '100→1，和变为 1',
      'return true：到达快乐数',
      '若某和重复出现则陷入环 → false',
    ][i] ?? ''
  }
  if (s === 'two-sum') {
    return [
      'i=0, x=2：查 9−2 不在 map，再 put(2→0)',
      'i=1, x=7：查 9−7=2，map 命中 2→0',
      'return [0, 1]',
      '先查后存，避免同一下标用两次',
    ][i] ?? ''
  }
  if (s === 'four-sum-ii') {
    return [
      '枚举 A+B，map 统计和的出现次数',
      '枚举 C+D，计算 sum = c+d',
      '查 map 中 −sum 的次数并累加',
      '本题四数组独立，无需对四元组去重',
    ][i] ?? ''
  }
  if (s === 'ransom-note') {
    return [
      '统计 magazine="aaab"：a×3, b×1',
      'ransomNote="aab"：依次 count--',
      '全部够用 → return true',
      '某字符不足则立即 false',
    ][i] ?? ''
  }
  if (s === 'three-sum') {
    return [
      '排序：[-4,-1,-1,0,1,2]',
      '固定 i=1（−1），left=2, right=5',
      '−1+0+1=0 → 收集 [-1,0,1]',
      'left/right 去重后移动，继续搜',
      '同数组不重复三元组 → 双指针更稳',
    ][i] ?? ''
  }
  if (s === 'four-sum') {
    return [
      '排序后外层 k、i 固定两层',
      '内层 left/right 收拢四数和',
      '找到 target=0 的四元组',
      'k,i,left,right 四层去重',
      '与 454 不同：单数组 + 要去重',
    ][i] ?? ''
  }
  if (s === 'summary') {
    return [
      '值域小且连续 → 定长数组计数',
      '只要存在性 / 判环 → set',
      '需要配对信息 → map',
      '454 用 map；15/18 用排序+双指针',
    ][i] ?? ''
  }
  return ''
})

/* ---------- 理论：三列卡片数据 ---------- */
const THEORY_FREQ_LETTERS = ['a', 'b', 'c', 'd', 'e'] as const

function arrayFreqForStep(s: number) {
  const frames = [
  { counts: [0, 0, 0, 0, 0], hot: -1, op: 'init' as const },
  { counts: [1, 1, 0, 0, 0], hot: 2, op: 'inc' as const },
  { counts: [1, 1, 1, 0, 0], hot: 4, op: 'inc' as const },
  { counts: [0, 0, 0, 0, 0], hot: -1, op: 'zero' as const },
  ]
  return frames[Math.min(s, frames.length - 1)] ?? frames[0]
}

function setCellsForStep(s: number) {
  const frames: string[][] = [[], ['2'], ['2', '5'], ['2', '5']]
  return frames[Math.min(s, frames.length - 1)] ?? []
}

const setTryDup = computed(() => props.sectionId === 'theory' && setTheory.step.value === 3)

function mapEntriesForStep(s: number) {
  const frames: { key: string; val: string }[][] = [
    [],
    [{ key: '2', val: '0' }],
    [
      { key: '2', val: '0' },
      { key: '7', val: '1' },
    ],
    [
      { key: '2', val: '0' },
      { key: '7', val: '1' },
    ],
  ]
  return frames[Math.min(s, frames.length - 1)] ?? []
}

const mapLookupKey = computed(
  () => props.sectionId === 'theory' && mapTheory.step.value === 3,
)

const arrayStep = computed(() => arrayTheory.step.value)
const setStep = computed(() => setTheory.step.value)
const mapStep = computed(() => mapTheory.step.value)

const theoryArrayFrame = computed(() =>
  props.sectionId === 'theory' ? arrayFreqForStep(arrayStep.value) : null,
)
const theorySetCells = computed(() =>
  props.sectionId === 'theory' ? setCellsForStep(setStep.value) : [],
)
const theoryMapEntries = computed(() =>
  props.sectionId === 'theory' ? mapEntriesForStep(mapStep.value) : [],
)

/* ---------- 242 有效的字母异位词 ---------- */
const ANA_S = ['r', 'a', 't'] as const
const ANA_T = ['t', 'a', 'r'] as const
const ANA_LETTERS = ['r', 'a', 't'] as const

const ANA_FRAMES = [
  { counts: { r: 1, a: 1, t: 1 }, scanS: 2, scanT: -1, phase: 's' as const, done: false },
  { counts: { r: 1, a: 1, t: 0 }, scanS: 3, scanT: 0, phase: 't' as const, done: false },
  { counts: { r: 0, a: 0, t: 0 }, scanS: 3, scanT: 2, phase: 't' as const, done: false },
  { counts: { r: 0, a: 0, t: 0 }, scanS: 3, scanT: 3, phase: 'check' as const, done: false },
  { counts: { r: 0, a: 0, t: 0 }, scanS: 3, scanT: 3, phase: 'check' as const, done: true },
]

const anaFrame = computed(() => {
  if (props.sectionId !== 'valid-anagram') return null
  return ANA_FRAMES[Math.min(step.value, ANA_FRAMES.length - 1)] ?? ANA_FRAMES[0]
})

/* ---------- 349 交集 ---------- */
const INT_NUMS1 = ['1', '2', '2', '1'] as const
const INT_NUMS2 = ['2', '2'] as const

const intFrame = computed(() => {
  if (props.sectionId !== 'intersection') return null
  const s = step.value
  return {
    setCells: s >= 0 ? ['2'] : [],
    scanIdx: s === 1 ? 1 : s >= 2 ? 4 : -1,
    result: s >= 2 ? ['2'] : [],
    building: s === 0,
  }
})

/* ---------- 202 快乐数 ---------- */
/** 202：set 记录每次变换后的 n（非 1 时） */
const HAPPY_CHAIN = [
  { from: '19', to: '82', seen: [] as string[] },
  { from: '82', to: '68', seen: ['82'] },
  { from: '68', to: '100', seen: ['82', '68'] },
  { from: '100', to: '1', seen: ['82', '68', '100'] },
] as const

const happyFrame = computed(() => {
  if (props.sectionId !== 'happy-number') return null
  const s = Math.min(step.value, HAPPY_CHAIN.length - 1)
  const cur = HAPPY_CHAIN[s]!
  return {
    from: cur.from,
    to: cur.to,
    setSeen: cur.seen,
    done: s === HAPPY_CHAIN.length - 1,
  }
})

/* ---------- 1 两数之和 ---------- */
const TWO_SUM_NUMS = ['2', '7', '11', '15'] as const

const twoSumFrame = computed(() => {
  if (props.sectionId !== 'two-sum') return null
  const s = step.value
  const frames = [
    {
      active: 0,
      map: [{ k: '2', v: '0' }],
      lookup: '',
      found: false,
      result: [] as number[],
      op: 'put' as const,
    },
    {
      active: 1,
      map: [{ k: '2', v: '0' }],
      lookup: '2',
      found: true,
      result: [] as number[],
      op: 'get' as const,
    },
    {
      active: 1,
      map: [{ k: '2', v: '0' }],
      lookup: '2',
      found: true,
      result: [0, 1],
      op: 'get' as const,
    },
    {
      active: 1,
      map: [{ k: '2', v: '0' }],
      lookup: '2',
      found: true,
      result: [0, 1],
      op: 'get' as const,
    },
  ]
  return frames[Math.min(s, frames.length - 1)] ?? frames[0]
})

/* ---------- 454 四数相加 II ---------- */
const FSII_A = ['1', '2'] as const
const FSII_B = ['-2', '-1'] as const
const FSII_C = ['-1', '2'] as const
const FSII_D = ['0', '2'] as const

const fsiiFrame = computed(() => {
  if (props.sectionId !== 'four-sum-ii') return null
  const s = step.value
  return {
    mapEntries:
      s >= 0
        ? [
            { k: '-1', v: '1' },
            { k: '0', v: '2' },
            { k: '1', v: '1' },
          ]
        : [],
    cdPair: s >= 1 ? { c: '-1', d: '0', sum: '-1' } : null,
    lookup: s >= 2 ? '1' : '',
    count: s >= 2 ? 2 : s >= 1 ? 1 : 0,
    showAB: s === 0,
    showCD: s >= 1,
  }
})

/* ---------- 383 赎金信 ---------- */
const RANSOM_MAG = ['a', 'a', 'a', 'b'] as const
const RANSOM_NOTE = ['a', 'a', 'b'] as const

const ransomFrame = computed(() => {
  if (props.sectionId !== 'ransom-note') return null
  const s = step.value
  const freq = { a: 3, b: 1 }
  if (s >= 1) freq.a = 1
  if (s >= 2) {
    freq.a = 1
    freq.b = 0
  }
  return {
    freq,
    scanIdx: s === 1 ? 1 : s >= 2 ? 2 : -1,
    ok: s >= 2,
    counting: s === 0,
  }
})

/* ---------- 15 三数之和 ---------- */
const THREE_SUM_SORTED = ['-4', '-1', '-1', '0', '1', '2'] as const

const threeSumFrame = computed(() => {
  if (props.sectionId !== 'three-sum') return null
  const s = step.value
  return {
    sorted: s >= 0,
    nums: THREE_SUM_SORTED,
    i: s >= 1 ? 1 : -1,
    left: s >= 1 ? 2 : -1,
    right: s >= 1 ? 5 : -1,
    sum: s >= 2 ? 0 : null,
    triplet: s >= 2 ? ['-1', '0', '1'] : [],
    showPtr: s >= 1,
  }
})

/* ---------- 18 四数之和 ---------- */
const FOUR_SUM_SORTED = ['-2', '-1', '0', '0', '1', '2'] as const

const fourSumFrame = computed(() => {
  if (props.sectionId !== 'four-sum') return null
  const s = step.value
  return {
    sorted: s >= 0,
    nums: FOUR_SUM_SORTED,
    k: s >= 1 ? 0 : -1,
    i: s >= 1 ? 1 : -1,
    left: s >= 2 ? 2 : -1,
    right: s >= 2 ? 5 : -1,
    quad: s >= 3 ? ['-2', '-1', '1', '2'] : [],
    target: '0',
  }
})

const SUMMARY_GROUPS = [
  { title: '定长数组计数', tags: ['242 异位词', '383 赎金信'], color: 'blue' as const },
  { title: '哈希集合 set', tags: ['349 交集', '202 快乐数'], color: 'cyan' as const },
  { title: '哈希映射 map', tags: ['1 两数之和', '454 四数相加'], color: 'violet' as const },
  { title: '排序 + 双指针', tags: ['15 三数之和', '18 四数之和'], color: 'amber' as const },
]
</script>

<template>
  <!-- 理论基础：三列独立演示 -->
  <div v-if="sectionId === 'theory'" class="ht-theory-trio" role="img" :aria-label="caption">
    <p class="ht-theory-trio-hint">三种载体独立演示 · 可分别暂停或步进</p>

    <div class="ht-theory-grid">
      <article class="ht-theory-card ht-theory-card--array">
        <header class="ht-theory-card-head">
          <span class="ht-struct-tag">定长数组</span>
          <span class="ht-struct-badge">count[c−'a']</span>
        </header>
        <div class="ht-viz-stage">
          <div class="ht-freq-table">
            <span class="ht-freq-table-label">int[26] 示意（截取 a–e）</span>
            <div class="ht-freq-cols">
              <div
                v-for="(ch, idx) in THEORY_FREQ_LETTERS"
                :key="ch"
                class="ht-freq-col"
                :class="{
                  'ht-freq-col--hot': theoryArrayFrame?.hot === idx,
                  'ht-freq-col--zero': theoryArrayFrame?.op === 'zero',
                }"
              >
                <span class="learn-viz-cell ht-freq-letter">{{ ch }}</span>
                <span
                  class="ht-freq-bar"
                  :style="{
                    height: 8 + (theoryArrayFrame?.counts[idx] ?? 0) * 22 + 'px',
                  }"
                />
                <span class="ht-freq-num">{{ theoryArrayFrame?.counts[idx] ?? 0 }}</span>
              </div>
            </div>
          </div>
          <span
            v-if="theoryArrayFrame?.op === 'inc'"
            class="learn-viz-op learn-viz-op--push"
          >++</span>
          <span
            v-else-if="theoryArrayFrame?.op === 'zero'"
            class="learn-viz-op learn-viz-op--pop"
          >全 0 ✓</span>
        </div>
        <footer class="ht-card-foot">
          <p class="ht-mini-hint" aria-live="polite">{{ ARRAY_HINTS[arrayStep] }}</p>
          <div class="ht-mini-toolbar" role="group" aria-label="数组计数动画控制">
            <el-button size="small" round @click="arrayTheory.togglePlay">
              {{ arrayTheory.playing ? '暂停' : '播放' }}
            </el-button>
            <el-button size="small" round @click="arrayTheory.manualNext">下一步</el-button>
          </div>
        </footer>
      </article>

      <article class="ht-theory-card ht-theory-card--set">
        <header class="ht-theory-card-head">
          <span class="ht-struct-tag ht-struct-tag--set">unordered_set</span>
          <span class="ht-struct-badge ht-struct-badge--set">O(1) 查存在</span>
        </header>
        <div class="ht-viz-stage">
          <div class="ht-set-bucket" :class="{ 'ht-set-bucket--active': theorySetCells.length > 0 }">
            <span class="ht-set-label">集合</span>
            <div class="ht-set-lane">
              <span
                v-for="(v, i) in theorySetCells.filter(Boolean)"
                :key="'set' + v + i"
                class="learn-viz-cell"
                :class="{ 'learn-viz-cell--hot': i === theorySetCells.length - 1 && !setTryDup }"
              >{{ v }}</span>
              <span v-if="!theorySetCells.filter(Boolean).length" class="ht-set-empty">∅</span>
            </div>
          </div>
          <span v-if="setTryDup" class="learn-viz-op learn-viz-op--pop">2 已存在</span>
          <span v-else-if="setStep > 0 && setStep < 3" class="learn-viz-op learn-viz-op--push">insert</span>
        </div>
        <footer class="ht-card-foot">
          <p class="ht-mini-hint" aria-live="polite">{{ SET_HINTS[setStep] }}</p>
          <div class="ht-mini-toolbar" role="group" aria-label="集合动画控制">
            <el-button size="small" round @click="setTheory.togglePlay">
              {{ setTheory.playing ? '暂停' : '播放' }}
            </el-button>
            <el-button size="small" round @click="setTheory.manualNext">下一步</el-button>
          </div>
        </footer>
      </article>

      <article class="ht-theory-card ht-theory-card--map">
        <header class="ht-theory-card-head">
          <span class="ht-struct-tag ht-struct-tag--map">unordered_map</span>
          <span class="ht-struct-badge ht-struct-badge--map">key → value</span>
        </header>
        <div class="ht-viz-stage">
          <div class="ht-map-bucket" :class="{ 'ht-map-bucket--active': theoryMapEntries.length > 0 }">
            <span class="ht-map-label">映射</span>
            <div class="ht-map-entries">
              <div
                v-for="e in theoryMapEntries"
                :key="e.key"
                class="ht-map-entry"
                :class="{ 'ht-map-entry--hot': mapLookupKey && e.key === '2' }"
              >
                <span class="learn-viz-cell learn-viz-cell--hot">{{ e.key }}</span>
                <span class="ht-map-arrow" aria-hidden="true">→</span>
                <span class="learn-viz-cell">{{ e.val }}</span>
              </div>
              <span v-if="!theoryMapEntries.length" class="ht-set-empty">空 map</span>
            </div>
          </div>
          <span v-if="mapLookupKey" class="learn-viz-op">get(2) = 0</span>
          <span v-else-if="mapStep > 0 && mapStep < 3" class="learn-viz-op learn-viz-op--push">put</span>
        </div>
        <footer class="ht-card-foot">
          <p class="ht-mini-hint" aria-live="polite">{{ MAP_HINTS[mapStep] }}</p>
          <div class="ht-mini-toolbar" role="group" aria-label="映射动画控制">
            <el-button size="small" round @click="mapTheory.togglePlay">
              {{ mapTheory.playing ? '暂停' : '播放' }}
            </el-button>
            <el-button size="small" round @click="mapTheory.manualNext">下一步</el-button>
          </div>
        </footer>
      </article>
    </div>

    <section class="ht-theory-flow">
      <h4 class="ht-theory-flow-title">key → hash() → 表项</h4>
      <div class="ht-flow-row">
        <div class="ht-flow-chip">
          <span class="ht-flow-label">key</span>
          <span class="ht-flow-val">"abc"</span>
        </div>
        <span class="ht-flow-arrow" aria-hidden="true">→ hash() →</span>
        <div class="ht-flow-chip ht-flow-chip--accent">
          <span class="ht-flow-label">index</span>
          <span class="ht-flow-val">i</span>
        </div>
        <span class="ht-flow-arrow" aria-hidden="true">→</span>
        <div class="ht-flow-slot">
          <span class="ht-flow-label">table[i]</span>
          <span class="ht-flow-val">存取</span>
        </div>
      </div>
      <p class="ht-theory-flow-note">碰撞时同桶可拉链；刷题通常按均摊 O(1) 理解即可</p>
    </section>
  </div>

  <SteppedAnimShell
    v-else
    :caption="caption"
    :use-stepped="useStepped"
    :step-hint="stepHint"
    :step="step"
    :max-step="maxStep"
    :playing="playing"
    @toggle-play="togglePlay"
    @next="manualNext"
    @reset="resetAnim"
  >
    <!-- 242 -->
    <div v-if="sectionId === 'valid-anagram' && anaFrame" class="learn-viz-panel ht-ana-viz">
      <div class="ht-scan-block">
        <span class="ht-scan-label">s = "rat"</span>
        <div class="ht-scan-chars">
          <span
            v-for="(ch, i) in ANA_S"
            :key="'s' + i"
            class="learn-viz-cell ht-scan-char"
            :class="{
              'learn-viz-cell--hot': anaFrame.phase === 's' && i <= anaFrame.scanS,
              'learn-viz-cell--dim': anaFrame.phase !== 's' && i < 3,
            }"
          >{{ ch }}</span>
        </div>
      </div>
      <div class="ht-scan-block">
        <span class="ht-scan-label">t = "tar"</span>
        <div class="ht-scan-chars">
          <span
            v-for="(ch, i) in ANA_T"
            :key="'t' + i"
            class="learn-viz-cell ht-scan-char"
            :class="{
              'learn-viz-cell--hot': anaFrame.phase === 't' && i === anaFrame.scanT,
              'learn-viz-cell--dim': anaFrame.phase === 't' && i < anaFrame.scanT,
            }"
          >{{ ch }}</span>
        </div>
      </div>
      <span class="ht-scan-flow" aria-hidden="true">↓</span>
      <div class="ht-freq-panel">
        <span class="ht-freq-panel-label">count[26]</span>
        <div class="ht-freq-cols ht-freq-cols--compact">
          <div
            v-for="ch in ANA_LETTERS"
            :key="ch"
            class="ht-freq-col"
            :class="{ 'ht-freq-col--zero': anaFrame.done }"
          >
            <span class="learn-viz-cell ht-freq-letter">{{ ch }}</span>
            <span
              class="ht-freq-bar"
              :style="{ height: 8 + anaFrame.counts[ch] * 24 + 'px' }"
            />
            <span class="ht-freq-num">{{ anaFrame.counts[ch] }}</span>
          </div>
        </div>
        <p v-if="anaFrame.done" class="ht-result-ok">全 0 → true</p>
      </div>
    </div>

    <!-- 349 -->
    <div v-else-if="sectionId === 'intersection' && intFrame" class="learn-viz-grid learn-viz-grid--2 ht-int-viz">
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag learn-viz-tag--green">nums2（较小）</span>
          <span class="learn-viz-badge learn-viz-badge--green">建 set</span>
        </header>
        <div class="learn-viz-stage">
          <div class="ht-arr-row">
            <span
              v-for="(n, i) in INT_NUMS2"
              :key="'n2' + i"
              class="learn-viz-cell"
              :class="{ 'learn-viz-cell--hot': intFrame.building }"
            >{{ n }}</span>
          </div>
          <span class="ht-arr-arrow" aria-hidden="true">↓</span>
          <div class="ht-set-bucket ht-set-bucket--sm">
            <span class="ht-set-label">set</span>
            <div class="ht-set-lane">
              <span
                v-for="v in intFrame.setCells"
                :key="v"
                class="learn-viz-cell learn-viz-cell--hot"
              >{{ v }}</span>
            </div>
          </div>
        </div>
      </article>
      <span class="learn-viz-transfer" aria-hidden="true">→</span>
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag">nums1 遍历</span>
          <span class="learn-viz-badge">查 set</span>
        </header>
        <div class="learn-viz-stage">
          <div class="ht-arr-row">
            <span
              v-for="(n, i) in INT_NUMS1"
              :key="'n1' + i"
              class="learn-viz-cell"
              :class="{
                'learn-viz-cell--hot': i === intFrame.scanIdx,
                'learn-viz-cell--dim': intFrame.scanIdx >= 0 && i < intFrame.scanIdx,
              }"
            >{{ n }}</span>
          </div>
          <div v-if="intFrame.result.length" class="ht-result-row">
            <span class="ht-result-label">交集</span>
            <span
              v-for="r in intFrame.result"
              :key="r"
              class="learn-viz-pill learn-viz-pill--hot"
            >{{ r }}</span>
          </div>
        </div>
      </article>
    </div>

    <!-- 202 -->
    <div v-else-if="sectionId === 'happy-number' && happyFrame" class="learn-viz-panel ht-happy-viz">
      <div class="ht-happy-calc">
        <span class="learn-viz-cell learn-viz-cell--hot">{{ happyFrame.from }}</span>
        <span class="ht-happy-op" aria-hidden="true">各位²和 →</span>
        <span class="learn-viz-cell">{{ happyFrame.to }}</span>
      </div>
      <span class="ht-scan-flow" aria-hidden="true">↓</span>
      <div class="ht-set-bucket ht-set-bucket--wide">
        <span class="ht-set-label">unordered_set（已出现过的 n）</span>
        <div class="ht-set-lane">
          <span
            v-for="v in happyFrame.setSeen"
            :key="v"
            class="learn-viz-cell"
          >{{ v }}</span>
          <span
            v-if="!happyFrame.done && happyFrame.to !== '1'"
            class="learn-viz-cell learn-viz-cell--hot"
          >{{ happyFrame.to }}</span>
        </div>
      </div>
      <p v-if="happyFrame.done" class="ht-result-ok">n 变为 1 → 快乐数 ✓</p>
      <p v-else class="ht-happy-note">若新和已在 set 中 → 陷入环，返回 false</p>
    </div>

    <!-- 1 两数之和 -->
    <div v-else-if="sectionId === 'two-sum' && twoSumFrame" class="learn-viz-grid learn-viz-grid--2 ht-twosum-viz">
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag">nums · target = 9</span>
        </header>
        <div class="learn-viz-stage">
          <div class="ht-arr-row ht-arr-row--idx">
            <div v-for="(n, i) in TWO_SUM_NUMS" :key="'ts' + i" class="ht-idx-cell-wrap">
              <span
                class="learn-viz-cell"
                :class="{
                  'learn-viz-cell--hot': twoSumFrame.active === i,
                  'learn-viz-cell--dim': twoSumFrame.result.length && i !== twoSumFrame.active,
                }"
              >{{ n }}</span>
              <span class="ht-idx-tag">i={{ i }}</span>
            </div>
          </div>
          <p v-if="twoSumFrame.lookup" class="ht-lookup-line">
            查 <strong>9 − {{ TWO_SUM_NUMS[twoSumFrame.active] }} = {{ twoSumFrame.lookup }}</strong>
          </p>
        </div>
      </article>
      <span class="learn-viz-transfer" aria-hidden="true">⇄</span>
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag learn-viz-tag--violet">unordered_map</span>
          <span class="learn-viz-badge">先查后 put</span>
        </header>
        <div class="learn-viz-stage">
          <div class="ht-map-entries ht-map-entries--lg">
            <div
              v-for="e in twoSumFrame.map"
              :key="e.k"
              class="ht-map-entry"
              :class="{ 'ht-map-entry--hot': twoSumFrame.found && e.k === twoSumFrame.lookup }"
            >
              <span class="learn-viz-cell learn-viz-cell--hot">{{ e.k }}</span>
              <span class="ht-map-arrow" aria-hidden="true">→</span>
              <span class="learn-viz-cell">{{ e.v }}</span>
            </div>
            <span v-if="!twoSumFrame.map.length" class="ht-set-empty">空</span>
          </div>
          <div v-if="twoSumFrame.result.length" class="ht-result-row">
            <span class="ht-result-label">返回</span>
            <span class="learn-viz-pill learn-viz-pill--hot">[{{ twoSumFrame.result.join(', ') }}]</span>
          </div>
        </div>
      </article>
    </div>

    <!-- 454 -->
    <div v-else-if="sectionId === 'four-sum-ii' && fsiiFrame" class="learn-viz-panel ht-fsii-viz">
      <div v-if="fsiiFrame.showAB" class="ht-fsii-row">
        <span class="ht-fsii-label">A + B</span>
        <div class="ht-arr-row">
          <span v-for="a in FSII_A" :key="'a' + a" class="learn-viz-cell">{{ a }}</span>
          <span class="ht-fsii-plus" aria-hidden="true">+</span>
          <span v-for="b in FSII_B" :key="'b' + b" class="learn-viz-cell">{{ b }}</span>
        </div>
        <span class="ht-arr-arrow" aria-hidden="true">→ map</span>
      </div>
      <div class="ht-map-entries ht-map-entries--center">
        <div
          v-for="e in fsiiFrame.mapEntries"
          :key="e.k"
          class="ht-map-entry"
          :class="{ 'ht-map-entry--hot': fsiiFrame.lookup === e.k }"
        >
          <span class="learn-viz-cell learn-viz-cell--hot">{{ e.k }}</span>
          <span class="ht-map-arrow" aria-hidden="true">×</span>
          <span class="learn-viz-cell">{{ e.v }}</span>
        </div>
      </div>
      <div v-if="fsiiFrame.showCD" class="ht-fsii-row">
        <span class="ht-fsii-label">C + D</span>
        <div class="ht-arr-row">
          <span
            v-for="c in FSII_C"
            :key="'c' + c"
            class="learn-viz-cell"
            :class="{ 'learn-viz-cell--hot': fsiiFrame.cdPair?.c === c }"
          >{{ c }}</span>
          <span class="ht-fsii-plus" aria-hidden="true">+</span>
          <span
            v-for="d in FSII_D"
            :key="'d' + d"
            class="learn-viz-cell"
            :class="{ 'learn-viz-cell--hot': fsiiFrame.cdPair?.d === d }"
          >{{ d }}</span>
        </div>
        <span v-if="fsiiFrame.cdPair" class="ht-lookup-line">查 map[−({{ fsiiFrame.cdPair.sum }})] = map[{{ fsiiFrame.lookup }}]</span>
      </div>
      <div v-if="fsiiFrame.count > 0" class="ht-result-row">
        <span class="ht-result-label">累计计数</span>
        <span class="learn-viz-pill learn-viz-pill--hot">{{ fsiiFrame.count }}</span>
      </div>
    </div>

    <!-- 383 -->
    <div v-else-if="sectionId === 'ransom-note' && ransomFrame" class="learn-viz-grid learn-viz-grid--2 ht-ransom-viz">
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag learn-viz-tag--green">magazine</span>
          <span class="learn-viz-badge learn-viz-badge--green">计数</span>
        </header>
        <div class="learn-viz-stage">
          <div class="ht-scan-chars">
            <span
              v-for="(ch, i) in RANSOM_MAG"
              :key="'m' + i"
              class="learn-viz-cell ht-scan-char"
              :class="{ 'learn-viz-cell--hot': ransomFrame.counting }"
            >{{ ch }}</span>
          </div>
          <div class="ht-freq-inline">
            <span class="ht-freq-inline-item">a × {{ ransomFrame.freq.a }}</span>
            <span class="ht-freq-inline-item">b × {{ ransomFrame.freq.b }}</span>
          </div>
        </div>
      </article>
      <span class="learn-viz-transfer" aria-hidden="true">−1→</span>
      <article class="learn-viz-card">
        <header class="learn-viz-card-head">
          <span class="learn-viz-tag">ransomNote</span>
          <span class="learn-viz-badge">消耗</span>
        </header>
        <div class="learn-viz-stage">
          <div class="ht-scan-chars">
            <span
              v-for="(ch, i) in RANSOM_NOTE"
              :key="'r' + i"
              class="learn-viz-cell ht-scan-char"
              :class="{
                'learn-viz-cell--hot': i === ransomFrame.scanIdx,
                'learn-viz-cell--dim': ransomFrame.scanIdx >= 0 && i < ransomFrame.scanIdx,
              }"
            >{{ ch }}</span>
          </div>
          <p v-if="ransomFrame.ok" class="ht-result-ok">可以拼出 ✓</p>
        </div>
      </article>
    </div>

    <!-- 15 -->
    <div v-else-if="sectionId === 'three-sum' && threeSumFrame" class="learn-viz-panel ht-nsum-viz">
      <header class="ht-nsum-head">
        <span class="learn-viz-tag learn-viz-tag--violet">排序 + 双指针</span>
        <span class="ht-nsum-badge">和 = 0</span>
      </header>
      <div class="ht-arr-row ht-arr-row--idx">
        <div
          v-for="(n, idx) in threeSumFrame.nums"
          :key="'3s' + idx"
          class="ht-idx-cell-wrap"
          :class="{
            'ht-idx-cell-wrap--i': threeSumFrame.i === idx,
            'ht-idx-cell-wrap--l': threeSumFrame.left === idx,
            'ht-idx-cell-wrap--r': threeSumFrame.right === idx,
          }"
        >
          <span
            class="learn-viz-cell"
            :class="{
              'learn-viz-cell--hot':
                threeSumFrame.i === idx ||
                threeSumFrame.left === idx ||
                threeSumFrame.right === idx,
              'learn-viz-cell--dim': !threeSumFrame.sorted,
            }"
          >{{ n }}</span>
          <span v-if="threeSumFrame.i === idx" class="ht-ptr-tag ht-ptr-tag--i">i</span>
          <span v-if="threeSumFrame.left === idx" class="ht-ptr-tag ht-ptr-tag--l">L</span>
          <span v-if="threeSumFrame.right === idx" class="ht-ptr-tag ht-ptr-tag--r">R</span>
        </div>
      </div>
      <p v-if="threeSumFrame.sum === 0" class="ht-lookup-line">
        {{ threeSumFrame.triplet.join(' + ') }} = 0
      </p>
      <div v-if="threeSumFrame.triplet.length" class="ht-result-row">
        <span class="ht-result-label">三元组</span>
        <span
          v-for="t in threeSumFrame.triplet"
          :key="t"
          class="learn-viz-pill learn-viz-pill--hot"
        >{{ t }}</span>
      </div>
    </div>

    <!-- 18 -->
    <div v-else-if="sectionId === 'four-sum' && fourSumFrame" class="learn-viz-panel ht-nsum-viz">
      <header class="ht-nsum-head">
        <span class="learn-viz-tag learn-viz-tag--violet">四数之和</span>
        <span class="ht-nsum-badge">target = {{ fourSumFrame.target }}</span>
      </header>
      <div class="ht-arr-row ht-arr-row--idx">
        <div
          v-for="(n, idx) in fourSumFrame.nums"
          :key="'4s' + idx"
          class="ht-idx-cell-wrap"
          :class="{
            'ht-idx-cell-wrap--k': fourSumFrame.k === idx,
            'ht-idx-cell-wrap--i': fourSumFrame.i === idx,
            'ht-idx-cell-wrap--l': fourSumFrame.left === idx,
            'ht-idx-cell-wrap--r': fourSumFrame.right === idx,
          }"
        >
          <span
            class="learn-viz-cell"
            :class="{
              'learn-viz-cell--hot':
                fourSumFrame.k === idx ||
                fourSumFrame.i === idx ||
                fourSumFrame.left === idx ||
                fourSumFrame.right === idx,
            }"
          >{{ n }}</span>
          <span v-if="fourSumFrame.k === idx" class="ht-ptr-tag ht-ptr-tag--k">k</span>
          <span v-if="fourSumFrame.i === idx" class="ht-ptr-tag ht-ptr-tag--i">i</span>
          <span v-if="fourSumFrame.left === idx" class="ht-ptr-tag ht-ptr-tag--l">L</span>
          <span v-if="fourSumFrame.right === idx" class="ht-ptr-tag ht-ptr-tag--r">R</span>
        </div>
      </div>
      <div v-if="fourSumFrame.quad.length" class="ht-result-row">
        <span class="ht-result-label">四元组</span>
        <span
          v-for="q in fourSumFrame.quad"
          :key="q"
          class="learn-viz-pill learn-viz-pill--hot"
        >{{ q }}</span>
      </div>
    </div>

    <!-- 总结 -->
    <div v-else-if="sectionId === 'summary'" class="learn-viz-panel ht-summary-viz">
      <div class="ht-summary-grid">
        <article
          v-for="(g, gi) in SUMMARY_GROUPS"
          :key="g.title"
          class="ht-summary-card"
          :class="[
            `ht-summary-card--${g.color}`,
            { 'ht-summary-card--active': step === gi || step >= SUMMARY_GROUPS.length },
          ]"
        >
          <h4 class="ht-summary-title">{{ g.title }}</h4>
          <div class="ht-summary-tags">
            <span
              v-for="t in g.tags"
              :key="t"
              class="learn-viz-pill"
              :class="{ 'learn-viz-pill--hot': step === gi }"
            >{{ t }}</span>
          </div>
        </article>
      </div>
    </div>
  </SteppedAnimShell>
</template>

<style scoped>
.ht-theory-trio {
  width: 100%;
  margin: 0;
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.ht-theory-trio-hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--alp-color-muted);
  text-align: center;
  line-height: 1.5;
}

.ht-theory-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  width: 100%;
}

@media (max-width: 960px) {
  .ht-theory-grid {
    grid-template-columns: 1fr;
    max-width: 420px;
    margin: 0 auto;
  }
}

.ht-theory-card {
  --ht-cell: 40px;
  --ht-cell-gap: 10px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 14px 12px 12px;
  border-radius: 12px;
  background: var(--alp-bg-code-ish, rgba(15, 23, 42, 0.55));
  border: 1px solid var(--alp-color-border);
  overflow: hidden;
}

.ht-theory-card-head {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px 8px;
  margin-bottom: 10px;
}

.ht-viz-stage {
  position: relative;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 200px;
  padding: 8px 4px;
  box-sizing: border-box;
}

.ht-struct-tag {
  font-size: 14px;
  font-weight: 700;
  color: var(--alp-color-primary, #3a8a9e);
}

.ht-struct-tag--set {
  color: #6aa878;
}

.ht-struct-tag--map {
  color: #c4b5fd;
}

.ht-struct-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 35%, transparent);
}

.ht-struct-badge--set {
  color: #6aa878;
  background: color-mix(in srgb, #6aa878 12%, transparent);
  border-color: color-mix(in srgb, #6aa878 35%, transparent);
}

.ht-struct-badge--map {
  color: #c4b5fd;
  background: color-mix(in srgb, #7a6e9e 12%, transparent);
  border-color: color-mix(in srgb, #7a6e9e 35%, transparent);
}

.ht-card-foot {
  flex-shrink: 0;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--alp-color-border);
}

.ht-mini-hint {
  margin: 0 0 8px;
  font-size: 11px;
  line-height: 1.45;
  color: var(--alp-color-muted);
  min-height: 2.2em;
}

.ht-mini-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

/* 频次柱 */
.ht-freq-table-label,
.ht-freq-panel-label {
  display: block;
  width: 100%;
  margin-bottom: 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-muted);
  text-align: center;
}

.ht-freq-cols {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 12px;
  width: 100%;
}

.ht-freq-cols--compact {
  gap: 16px;
}

.ht-freq-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 36px;
}

.ht-freq-col--hot .ht-freq-bar {
  background: #6aa878;
}

.ht-freq-col--zero .ht-freq-bar {
  background: var(--alp-color-muted);
  opacity: 0.35;
}

.ht-freq-letter {
  font-size: 14px !important;
  min-width: 32px !important;
  height: 32px !important;
}

.ht-freq-bar {
  width: 20px;
  min-height: 4px;
  border-radius: 4px 4px 2px 2px;
  background: var(--alp-color-primary);
  transition: height 0.35s ease;
}

.ht-freq-num {
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--alp-color-muted);
}

/* set / map 桶 */
.ht-set-bucket,
.ht-map-bucket {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: 2px dashed var(--alp-color-border);
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.45));
}

.ht-set-bucket--active,
.ht-map-bucket--active {
  border-color: color-mix(in srgb, var(--alp-color-primary) 45%, transparent);
}

.ht-set-bucket--sm {
  padding: 8px;
}

.ht-set-bucket--wide {
  max-width: 100%;
}

.ht-set-label,
.ht-map-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.ht-set-lane {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: var(--ht-cell, 40px);
}

.ht-set-empty {
  font-size: 13px;
  color: var(--alp-color-muted);
  opacity: 0.6;
}

.ht-map-entries {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  align-items: center;
}

.ht-map-entries--lg {
  gap: 10px;
}

.ht-map-entries--center {
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
}

.ht-map-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 8px;
}

.ht-map-entry--hot {
  background: color-mix(in srgb, var(--alp-color-primary) 12%, transparent);
  border-radius: 8px;
}

.ht-map-arrow {
  font-size: 14px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

/* 理论底部流程 */
.ht-theory-flow {
  margin-top: 16px;
  padding: 14px;
  border-radius: 12px;
  background: var(--alp-bg-code-ish, rgba(15, 23, 42, 0.45));
  border: 1px solid var(--alp-color-border);
}

.ht-theory-flow-title {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  color: var(--alp-color-text);
}

.ht-flow-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.ht-flow-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid);
}

.ht-flow-chip--accent {
  border-color: color-mix(in srgb, var(--alp-color-primary) 50%, transparent);
  background: color-mix(in srgb, var(--alp-color-primary) 10%, transparent);
}

.ht-flow-label {
  font-size: 10px;
  color: var(--alp-color-muted);
}

.ht-flow-val {
  font-size: 13px;
  font-weight: 700;
  font-family: ui-monospace, monospace;
  color: var(--alp-color-primary);
}

.ht-flow-slot {
  padding: 10px 14px;
  border-radius: 8px;
  border: 2px dashed color-mix(in srgb, var(--alp-color-primary) 40%, transparent);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.ht-flow-arrow {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.ht-theory-flow-note {
  margin: 10px 0 0;
  font-size: 11px;
  text-align: center;
  color: var(--alp-color-muted);
  line-height: 1.45;
}

/* 刷题区通用 */
.ht-scan-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.ht-scan-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.ht-scan-chars {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.ht-scan-char {
  min-width: 36px !important;
  height: 36px !important;
  font-size: 15px !important;
}

.ht-scan-flow {
  font-size: 18px;
  color: var(--alp-color-muted);
  line-height: 1;
}

.ht-ana-viz {
  flex-direction: column;
  gap: 12px;
}

.ht-freq-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.35));
  border: 1px solid var(--alp-color-border);
}

.ht-arr-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.ht-arr-row--idx {
  gap: 12px 14px;
}

.ht-idx-cell-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.ht-idx-cell-wrap--i .learn-viz-cell,
.ht-idx-cell-wrap--k .learn-viz-cell {
  border-color: #7a6e9e;
  background: color-mix(in srgb, #7a6e9e 18%, transparent);
}

.ht-idx-cell-wrap--l .learn-viz-cell {
  border-color: #6aa878;
  background: color-mix(in srgb, #6aa878 15%, transparent);
}

.ht-idx-cell-wrap--r .learn-viz-cell {
  border-color: #f87171;
  background: color-mix(in srgb, #f87171 15%, transparent);
}

.ht-idx-tag {
  font-size: 9px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.ht-ptr-tag {
  position: absolute;
  top: -14px;
  font-size: 9px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
}

.ht-ptr-tag--i,
.ht-ptr-tag--k {
  color: #7a6e9e;
  background: color-mix(in srgb, #7a6e9e 20%, transparent);
}

.ht-ptr-tag--l {
  color: #6aa878;
  background: color-mix(in srgb, #6aa878 20%, transparent);
}

.ht-ptr-tag--r {
  color: #f87171;
  background: color-mix(in srgb, #f87171 20%, transparent);
}

.ht-arr-arrow {
  font-size: 16px;
  color: var(--alp-color-muted);
}

.ht-result-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}

.ht-result-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.ht-result-ok {
  margin: 8px 0 0;
  font-size: 13px;
  font-weight: 700;
  color: #6aa878;
}

.ht-lookup-line {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--alp-color-muted);
  text-align: center;
}

.ht-lookup-line strong {
  color: var(--alp-color-primary);
}

.ht-happy-viz {
  flex-direction: column;
  gap: 12px;
}

.ht-happy-calc {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.ht-happy-op {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.ht-happy-note {
  margin: 0;
  font-size: 11px;
  color: var(--alp-color-muted);
  text-align: center;
}

.ht-fsii-viz {
  flex-direction: column;
  gap: 14px;
}

.ht-fsii-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.ht-fsii-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.ht-fsii-plus,
.ht-fsii-eq {
  font-size: 14px;
  font-weight: 700;
  color: var(--alp-color-muted);
}

.ht-freq-inline {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.ht-freq-inline-item {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--alp-color-primary);
}

.ht-nsum-viz {
  flex-direction: column;
  gap: 12px;
}

.ht-nsum-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.ht-nsum-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  color: #c4b5fd;
  background: color-mix(in srgb, #7a6e9e 14%, transparent);
  border: 1px solid color-mix(in srgb, #7a6e9e 35%, transparent);
}

/* 总结 */
.ht-summary-viz {
  padding: 8px !important;
}

.ht-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

@media (max-width: 640px) {
  .ht-summary-grid {
    grid-template-columns: 1fr;
  }
}

.ht-summary-card {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface-solid, rgba(15, 23, 42, 0.4));
  opacity: 0.55;
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.ht-summary-card--active {
  opacity: 1;
  transform: scale(1.02);
}

.ht-summary-card--blue {
  border-color: color-mix(in srgb, var(--alp-color-primary) 40%, transparent);
}

.ht-summary-card--cyan {
  border-color: color-mix(in srgb, #6aa878 40%, transparent);
}

.ht-summary-card--violet {
  border-color: color-mix(in srgb, #7a6e9e 40%, transparent);
}

.ht-summary-card--amber {
  border-color: color-mix(in srgb, #9c8540 40%, transparent);
}

.ht-summary-title {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--alp-color-text);
}

.ht-summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

@media (prefers-reduced-motion: reduce) {
  .ht-freq-bar,
  .ht-summary-card {
    transition: none;
  }
}
</style>
