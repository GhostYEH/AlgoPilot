<script setup lang="ts">
import { computed, toRef } from 'vue'
import SteppedAnimShell from '@/components/learning/SteppedAnimShell.vue'
import { useSteppedAnimation } from '@/composables/useSteppedAnimation'

const props = defineProps<{
  sectionId: string
}>()

const sectionIdRef = toRef(props, 'sectionId')

function maxStepForSection(id: string) {
  if (id === 'three-sum') return 8
  return 0
}

const { playing, step, useStepped, maxStep, togglePlay, manualNext, resetAnim } =
  useSteppedAnimation({ sectionId: sectionIdRef, maxStepForSection })

const THREE_SUM_UNSORTED = ['-1', '0', '1', '2', '-1', '-4'] as const
const THREE_SUM_SORTED = ['-4', '-1', '-1', '0', '1', '2'] as const

type SumCmp = 'lt' | 'eq' | 'gt'

interface ThreeSumFrame {
  nums: readonly string[]
  unsorted?: boolean
  i: number
  left: number
  right: number
  sum: number | null
  cmp: SumCmp | null
  move: 'left' | 'right' | 'both' | 'sort' | 'skip-i' | 'break' | null
  skipI: boolean
  triplet: string[]
  triplets: string[][]
  showSearchZone: boolean
}

const THREE_SUM_FRAMES: ThreeSumFrame[] = [
  {
    nums: THREE_SUM_UNSORTED,
    unsorted: true,
    i: -1,
    left: -1,
    right: -1,
    sum: null,
    cmp: null,
    move: 'sort',
    skipI: false,
    triplet: [],
    triplets: [],
    showSearchZone: false,
  },
  {
    nums: THREE_SUM_SORTED,
    i: -1,
    left: -1,
    right: -1,
    sum: null,
    cmp: null,
    move: null,
    skipI: false,
    triplet: [],
    triplets: [],
    showSearchZone: false,
  },
  {
    nums: THREE_SUM_SORTED,
    i: 0,
    left: 1,
    right: 5,
    sum: -3,
    cmp: 'lt',
    move: 'left',
    skipI: false,
    triplet: [],
    triplets: [],
    showSearchZone: true,
  },
  {
    nums: THREE_SUM_SORTED,
    i: 1,
    left: 2,
    right: 5,
    sum: 0,
    cmp: 'eq',
    move: null,
    skipI: false,
    triplet: ['-1', '-1', '2'],
    triplets: [['-1', '-1', '2']],
    showSearchZone: true,
  },
  {
    nums: THREE_SUM_SORTED,
    i: 1,
    left: 2,
    right: 5,
    sum: 0,
    cmp: 'eq',
    move: 'both',
    skipI: false,
    triplet: ['-1', '-1', '2'],
    triplets: [['-1', '-1', '2']],
    showSearchZone: true,
  },
  {
    nums: THREE_SUM_SORTED,
    i: 1,
    left: 3,
    right: 4,
    sum: 0,
    cmp: 'eq',
    move: null,
    skipI: false,
    triplet: ['-1', '0', '1'],
    triplets: [
      ['-1', '-1', '2'],
      ['-1', '0', '1'],
    ],
    showSearchZone: true,
  },
  {
    nums: THREE_SUM_SORTED,
    i: 2,
    left: -1,
    right: -1,
    sum: null,
    cmp: null,
    move: 'skip-i',
    skipI: true,
    triplet: [],
    triplets: [
      ['-1', '-1', '2'],
      ['-1', '0', '1'],
    ],
    showSearchZone: false,
  },
  {
    nums: THREE_SUM_SORTED,
    i: 4,
    left: -1,
    right: -1,
    sum: null,
    cmp: null,
    move: 'break',
    skipI: false,
    triplet: [],
    triplets: [
      ['-1', '-1', '2'],
      ['-1', '0', '1'],
    ],
    showSearchZone: false,
  },
  {
    nums: THREE_SUM_SORTED,
    i: -1,
    left: -1,
    right: -1,
    sum: null,
    cmp: null,
    move: null,
    skipI: false,
    triplet: [],
    triplets: [
      ['-1', '-1', '2'],
      ['-1', '0', '1'],
    ],
    showSearchZone: false,
  },
]

const threeSumFrame = computed(() => {
  if (props.sectionId !== 'three-sum') return null
  return THREE_SUM_FRAMES[Math.min(step.value, THREE_SUM_FRAMES.length - 1)] ?? null
})

const threeSumCaption = '15 三数之和：排序 + 固定 i + left/right 收拢'

const threeSumStepHint = computed(() => {
  const hints = [
    '原数组乱序：nums = [-1,0,1,2,-1,-4]，先升序排序',
    '排序得 [-4,-1,-1,0,1,2]；外层 for 枚举固定下标 i',
    'i=0：sum = -4+(-1)+2 = -3 < 0，和太小 → left++',
    'i=1，L=2，R=5：-1+(-1)+2 = 0，记入三元组 [-1,-1,2]',
    '找到解后：跳过 left/right 重复值，再 L++、R-- 继续搜',
    'i=1，L=3，R=4：-1+0+1 = 0，记入 [-1,0,1]',
    'i=2：nums[2]==nums[1]，与 nums[i-1] 相同 → continue 去重',
    'i=4 时 nums[i]=1>0，可提前 break（后续和必 > 0）',
    '答案 [[-1,-1,2],[-1,0,1]]；时间 O(n²)，不计排序空间 O(1)',
  ]
  return hints[Math.min(step.value, hints.length - 1)] ?? ''
})

const moveOpLabel = computed(() => {
  const m = threeSumFrame.value?.move
  if (m === 'sort') return 'sort ↑'
  if (m === 'left') return 'left++ →'
  if (m === 'right') return '← right--'
  if (m === 'both') return 'L++, R--'
  if (m === 'skip-i') return 'continue'
  if (m === 'break') return 'break'
  return ''
})

const sumLine = computed(() => {
  const f = threeSumFrame.value
  if (!f || f.sum === null || f.i < 0) return ''
  const a = f.nums[f.i]
  const b = f.left >= 0 ? f.nums[f.left] : '?'
  const c = f.right >= 0 ? f.nums[f.right] : '?'
  const cmp =
    f.cmp === 'lt' ? '< 0' : f.cmp === 'eq' ? '= 0 ✓' : f.cmp === 'gt' ? '> 0' : ''
  return `${a} + ${b} + ${c} = ${f.sum} ${cmp}`
})

function inSearchZone(idx: number, f: ThreeSumFrame) {
  if (!f.showSearchZone || f.left < 0 || f.right < 0) return false
  return idx > f.i && idx >= f.left && idx <= f.right
}

const staticLabel = computed(() => {
  const m: Record<string, string> = {
    theory: '三种双指针：同向快慢 · 相向对撞 · 排序后左右收拢',
    'remove-element': '快慢指针：fast 探路，slow 指向下一个写入位置',
    'reverse-string': '相向指针：两端向中间交换',
    'replace-space': '从后往前填充：i 写新串，j 读旧串',
    'reverse-words': '先去空格 → 全串反转 → 逐词区间反转',
    'reverse-list': '三指针反转：pre ← cur，再整体右移',
    'remove-nth-from-end': '快指针先拉开 n+1 步，再与慢指针同速',
    intersection: '对齐长度后同速走，或交替拼接消去差值',
    cycle: '快二慢一在环上相遇；再与头指针同速找入口',
    'four-sum': '再套一层 k，内层仍是 left / right',
    summary: '双指针篇：数组 · 字符串 · 链表 · N 数之和',
  }
  return m[props.sectionId] ?? '本节双指针示意'
})
</script>

<template>
  <SteppedAnimShell
    v-if="sectionId === 'three-sum' && threeSumFrame"
    :caption="threeSumCaption"
    :use-stepped="useStepped"
    :step-hint="threeSumStepHint"
    :step="step"
    :max-step="maxStep"
    :playing="playing"
    @toggle-play="togglePlay"
    @next="manualNext"
    @reset="resetAnim"
  >
    <div
      v-if="threeSumFrame"
      class="learn-viz-panel tp-3sum-viz"
    >
      <header class="tp-3sum-head">
        <span class="learn-viz-tag learn-viz-tag--violet">排序 + 双指针</span>
        <span class="tp-3sum-badge">target = 0</span>
        <span
          v-if="moveOpLabel"
          class="learn-viz-op"
          :class="{
            'learn-viz-op--push': threeSumFrame.move === 'sort' || threeSumFrame.move === 'left',
            'learn-viz-op--pop':
              threeSumFrame.move === 'right' ||
              threeSumFrame.move === 'both' ||
              threeSumFrame.move === 'break',
          }"
        >{{ moveOpLabel }}</span>
      </header>

      <div
        v-if="threeSumFrame.unsorted"
        class="tp-3sum-sort-banner"
        aria-hidden="true"
      >
        <span class="tp-3sum-sort-from">乱序</span>
        <span class="tp-3sum-sort-arrow">→ sort →</span>
        <span class="tp-3sum-sort-to">升序</span>
      </div>

      <div class="tp-3sum-arr-block">
        <div
          class="tp-3sum-idx-row"
          aria-hidden="true"
        >
          <div
            v-for="(_, idx) in threeSumFrame.nums"
            :key="'ix' + idx"
            class="tp-3sum-idx-cell"
          >
            <span class="tp-3sum-idx-tag">{{ idx }}</span>
          </div>
        </div>

        <div class="tp-3sum-arr-row tp-3sum-arr-row--cells">
          <div
            v-for="(n, idx) in threeSumFrame.nums"
            :key="'3s' + idx"
            class="tp-3sum-cell-wrap"
            :class="{
              'tp-3sum-cell-wrap--i': threeSumFrame.i === idx,
              'tp-3sum-cell-wrap--l': threeSumFrame.left === idx,
              'tp-3sum-cell-wrap--r': threeSumFrame.right === idx,
              'tp-3sum-cell-wrap--zone': inSearchZone(idx, threeSumFrame),
              'tp-3sum-cell-wrap--skip': threeSumFrame.skipI && idx === 2,
            }"
          >
            <span
              class="learn-viz-cell"
              :class="{
                'learn-viz-cell--hot':
                  threeSumFrame.i === idx ||
                  threeSumFrame.left === idx ||
                  threeSumFrame.right === idx,
                'learn-viz-cell--dim':
                  threeSumFrame.unsorted === false &&
                  threeSumFrame.i >= 0 &&
                  idx > threeSumFrame.i &&
                  !inSearchZone(idx, threeSumFrame) &&
                  threeSumFrame.left >= 0 &&
                  (idx < threeSumFrame.left || idx > threeSumFrame.right),
                'learn-viz-cell--ghost': threeSumFrame.skipI && idx === 2,
              }"
            >{{ n }}</span>
            <span v-if="threeSumFrame.i === idx" class="tp-ptr-tag tp-ptr-tag--i">i</span>
            <span v-if="threeSumFrame.left === idx" class="tp-ptr-tag tp-ptr-tag--l">L</span>
            <span v-if="threeSumFrame.right === idx" class="tp-ptr-tag tp-ptr-tag--r">R</span>
            <span
              v-if="threeSumFrame.skipI && idx === 2"
              class="tp-skip-badge"
            >== nums[i-1]</span>
          </div>
        </div>

        <div
          v-if="threeSumFrame.showSearchZone"
          class="tp-3sum-zone-bracket"
          aria-hidden="true"
        >
          <span class="tp-3sum-zone-label">left … right 搜索区间</span>
        </div>
      </div>

      <p v-if="sumLine" class="tp-3sum-sum-line">{{ sumLine }}</p>
      <p v-else-if="threeSumFrame.move === 'break'" class="tp-3sum-sum-line tp-3sum-sum-line--warn">
        nums[i] &gt; 0 → 提前结束外层循环
      </p>

      <div v-if="threeSumFrame.triplet.length" class="tp-3sum-found">
        <span class="tp-3sum-found-label">本步解</span>
        <span
          v-for="t in threeSumFrame.triplet"
          :key="'t' + t"
          class="learn-viz-pill learn-viz-pill--hot"
        >{{ t }}</span>
      </div>

      <div v-if="threeSumFrame.triplets.length" class="tp-3sum-results">
        <span class="tp-3sum-results-label">已收集</span>
        <div
          v-for="(trip, ti) in threeSumFrame.triplets"
          :key="'trip' + ti"
          class="tp-3sum-trip-row"
        >
          <span
            v-for="v in trip"
            :key="ti + v"
            class="learn-viz-pill"
            :class="{ 'learn-viz-pill--hot': step >= 3 && ti === threeSumFrame.triplets.length - 1 }"
          >{{ v }}</span>
        </div>
      </div>

      <footer class="tp-3sum-legend">
        <span><i class="tp-leg tp-leg--i" />固定 i</span>
        <span><i class="tp-leg tp-leg--l" />left</span>
        <span><i class="tp-leg tp-leg--r" />right</span>
        <span class="tp-3sum-legend-note">去重：nums[i]==nums[i−1] 则 continue</span>
      </footer>
    </div>
  </SteppedAnimShell>

  <figure
    v-else
    class="tp-anim"
    role="img"
    :aria-label="staticLabel"
  >
    <figcaption class="tp-anim-caption">{{ staticLabel }}</figcaption>

    <div v-if="sectionId === 'theory'" class="panel summary">
      <div class="pill-row">
        <span class="pill">快慢</span>
        <span class="pill">相向</span>
        <span class="pill">排序+LR</span>
      </div>
    </div>

    <div v-else-if="sectionId === 'remove-element'" class="panel twoptr">
      <div class="track">
        <span v-for="(v, i) in ['3', '2', '2', '3']" :key="i" class="slot">{{ v }}</span>
      </div>
      <div class="markers">
        <span class="tag slow">slow</span>
        <span class="tag fast">fast</span>
      </div>
    </div>

    <div v-else-if="sectionId === 'replace-space'" class="panel fill">
      <div class="char-row">
        <span v-for="(ch, i) in ['a', ' ', 'b']" :key="i" class="node" :class="{ dim: i === 1 }">{{ ch }}</span>
      </div>
      <span class="arrow-mini">i, j 从尾部 →</span>
      <span class="node hot">%20</span>
    </div>

    <div v-else-if="sectionId === 'reverse-words'" class="panel words">
      <span class="stage hot">trim</span>
      <span class="arrow-mini">→</span>
      <span class="stage hot">全串反转</span>
      <span class="arrow-mini">→</span>
      <span class="stage hot">逐词反转</span>
    </div>

    <div v-else-if="sectionId === 'reverse-string'" class="panel meet-str">
      <span class="node hot">h</span>
      <span class="node">e</span>
      <span class="node">l</span>
      <span class="node hot">o</span>
      <span class="ptr l">L</span>
      <span class="ptr r">R</span>
    </div>

    <div v-else-if="sectionId === 'reverse-list'" class="panel reverse">
      <div class="flip-row">
        <span class="node">1</span>
        <span class="rev-arr">«</span>
        <span class="node">2</span>
        <span class="rev-arr">«</span>
        <span class="node">3</span>
      </div>
    </div>

    <div v-else-if="sectionId === 'four-sum'" class="panel nsum">
      <span class="tag k">k</span>
      <span
        v-for="(v, i) in ['1', '0', '-1', '0', '-2']"
        :key="i"
        class="node"
        :class="{ hot: i >= 1 && i <= 3 }"
      >{{ v }}</span>
      <span class="tag l">L</span>
      <span class="tag r">R</span>
    </div>

    <div v-else-if="sectionId === 'remove-nth-from-end'" class="panel twoptr">
      <div class="track">
        <span v-for="i in 6" :key="i" class="slot">{{ i }}</span>
      </div>
      <div class="markers">
        <span class="tag slow">slow</span>
        <span class="tag fast">fast</span>
      </div>
    </div>

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
        <circle class="pulse-dot" cx="100" cy="58" r="5" fill="#22c55e" />
      </svg>
    </div>

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

    <div v-else-if="sectionId === 'summary'" class="panel summary">
      <div class="pill-row">
        <span class="pill">27</span>
        <span class="pill">344</span>
        <span class="pill">206</span>
        <span class="pill">15</span>
        <span class="pill">142</span>
      </div>
    </div>
  </figure>
</template>

<style scoped>
.tp-3sum-viz {
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.tp-3sum-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.tp-3sum-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  color: #c4b5fd;
  background: color-mix(in srgb, #a78bfa 14%, transparent);
  border: 1px solid color-mix(in srgb, #a78bfa 35%, transparent);
}

.tp-3sum-sort-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 6px 12px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--alp-color-primary) 8%, transparent);
  border: 1px dashed color-mix(in srgb, var(--alp-color-primary) 35%, transparent);
  font-size: 12px;
  font-weight: 600;
}

.tp-3sum-sort-from {
  color: var(--alp-color-muted);
}

.tp-3sum-sort-arrow {
  color: var(--alp-color-primary);
  font-weight: 800;
}

.tp-3sum-sort-to {
  color: #4ade80;
}

.tp-3sum-arr-block {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.tp-3sum-idx-row,
.tp-3sum-arr-row--cells {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: center;
  gap: 12px 14px;
}

.tp-3sum-idx-cell {
  width: 40px;
  text-align: center;
}

.tp-3sum-idx-tag {
  font-size: 9px;
  font-weight: 700;
  color: var(--alp-color-muted);
  font-variant-numeric: tabular-nums;
}

.tp-3sum-cell-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 40px;
}

.tp-3sum-cell-wrap--i .learn-viz-cell {
  border-color: #a78bfa;
  background: color-mix(in srgb, #a78bfa 18%, transparent);
}

.tp-3sum-cell-wrap--l .learn-viz-cell {
  border-color: #4ade80;
  background: color-mix(in srgb, #4ade80 15%, transparent);
}

.tp-3sum-cell-wrap--r .learn-viz-cell {
  border-color: #f87171;
  background: color-mix(in srgb, #f87171 15%, transparent);
}

.tp-3sum-cell-wrap--zone::after {
  content: '';
  position: absolute;
  inset: -4px -6px auto;
  height: calc(100% + 8px);
  border-radius: 10px;
  border: 1px dashed color-mix(in srgb, #22d3ee 50%, transparent);
  pointer-events: none;
  z-index: 0;
}

.tp-3sum-cell-wrap--skip .learn-viz-cell {
  opacity: 0.45;
}

.tp-ptr-tag {
  position: absolute;
  top: -14px;
  font-size: 9px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
  z-index: 1;
}

.tp-ptr-tag--i {
  color: #a78bfa;
  background: color-mix(in srgb, #a78bfa 20%, transparent);
}

.tp-ptr-tag--l {
  color: #4ade80;
  background: color-mix(in srgb, #4ade80 20%, transparent);
}

.tp-ptr-tag--r {
  color: #f87171;
  background: color-mix(in srgb, #f87171 20%, transparent);
}

.tp-skip-badge {
  position: absolute;
  bottom: -16px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-size: 8px;
  font-weight: 700;
  color: #fbbf24;
}

.tp-3sum-zone-bracket {
  width: min(100%, 320px);
  padding: 4px 12px;
  text-align: center;
  border-top: 1px solid color-mix(in srgb, #22d3ee 30%, transparent);
}

.tp-3sum-zone-label {
  font-size: 10px;
  font-weight: 600;
  color: #22d3ee;
}

.tp-3sum-sum-line {
  margin: 0;
  width: 100%;
  text-align: center;
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--alp-color-text);
}

.tp-3sum-sum-line--warn {
  color: #fbbf24;
}

.tp-3sum-found,
.tp-3sum-results {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
}

.tp-3sum-found-label,
.tp-3sum-results-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.tp-3sum-trip-row {
  display: flex;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.tp-3sum-legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid var(--alp-color-border);
  font-size: 10px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.tp-leg {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
  margin-right: 4px;
  vertical-align: middle;
}

.tp-leg--i {
  background: #a78bfa;
}

.tp-leg--l {
  background: #4ade80;
}

.tp-leg--r {
  background: #f87171;
}

.tp-3sum-legend-note {
  flex: 1 1 100%;
  text-align: center;
  font-weight: 500;
  opacity: 0.9;
}

/* ---------- 其余小节静态动画 ---------- */
.tp-anim {
  margin: 0;
  padding: 14px 16px 12px;
  border-radius: var(--alp-radius-card, 12px);
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
  overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.tp-anim-caption {
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

.arrow-mini {
  color: #64748b;
  font-size: 14px;
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
  background: #f97316;
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

.char-row {
  display: flex;
  gap: 6px;
}
.node.dim {
  opacity: 0.35;
}
.node.hot {
  border-color: var(--alp-color-primary, #2563eb);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}
.fill,
.words,
.meet-str,
.nsum {
  flex-wrap: wrap;
  gap: 8px;
}
.stage {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}
.stage.hot {
  background: rgba(37, 99, 235, 0.12);
  border-color: #93c5fd;
  color: #1d4ed8;
}
.meet-str {
  position: relative;
  padding-bottom: 20px;
}
.ptr {
  position: absolute;
  bottom: 0;
  font-size: 10px;
  font-weight: 700;
  color: #2563eb;
}
.ptr.l {
  left: 8%;
}
.ptr.r {
  right: 8%;
}
.nsum {
  position: relative;
  padding-top: 18px;
}
.nsum .tag {
  position: absolute;
  top: 0;
  font-size: 10px;
  font-weight: 700;
  color: #ea580c;
}
.nsum .tag.l {
  left: 28%;
}
.nsum .tag.r {
  right: 18%;
}
.nsum .tag.k {
  left: 0;
  color: #7c3aed;
}

@media (prefers-reduced-motion: reduce) {
  .flip-row,
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
