<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GameArrayBoard from '@/modules/games/shared/GameArrayBoard.vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('greedy-courier', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const jumps = [2, 3, 1, 1, 4]
const pos = ref(0)
const maxReach = ref(0)
const picked = ref<number[]>([])
const msg = ref('')
const won = ref(false)
const fail = ref(false)

const intervals = [
  { start: 1, end: 3 },
  { start: 3, end: 5 },
  { start: 2, end: 4 },
  { start: 5, end: 6 },
]

// 跳跃关：贪心最优下一步（在 (pos, pos+jumps[pos]] 内，最大化 i + jumps[i]）
const jumpGreedyNext = computed(() => {
  if (props.levelId !== 'jump' || won.value) return -1
  const cur = pos.value
  const range = cur + jumps[cur]!
  let best = -1
  let bestReach = -1
  for (let i = cur + 1; i <= Math.min(range, jumps.length - 1); i++) {
    const r = i + jumps[i]!
    if (r > bestReach) {
      bestReach = r
      best = i
    }
  }
  return best
})

// 区间关：贪心最优下一步（未选且 start >= lastEnd 中，end 最小）
const intervalGreedyNext = computed(() => {
  if (props.levelId === 'jump' || won.value) return -1
  const last = picked.value[picked.value.length - 1]
  const lastEnd = last !== undefined ? intervals[last]!.end : 0
  let best = -1
  let bestEnd = Number.POSITIVE_INFINITY
  for (let i = 0; i < intervals.length; i++) {
    if (picked.value.includes(i)) continue
    const iv = intervals[i]!
    if (iv.start < lastEnd) continue
    if (iv.end < bestEnd) {
      bestEnd = iv.end
      best = i
    }
  }
  return best
})

watch(
  () => props.levelId,
  () => {
    pos.value = 0
    maxReach.value = jumps[0] ?? 0
    picked.value = []
    msg.value =
      props.levelId === 'jump'
        ? '点击想跳到的目标格子（须在当前跳跃范围内），贪心选择能最大化 i+jumps[i] 的格子'
        : '按结束时间贪心：每步点击结束最早且不与已选重叠的区间'
    won.value = false
    fail.value = false
    clearLog('贪心快递员出发')
  },
  { immediate: true },
)

const stepIndex = computed(() => {
  if (won.value) return 2
  if (props.levelId === 'jump') return Math.min(pos.value, 2)
  return Math.min(picked.value.length, 2)
})

const stateValues = computed(() => {
  if (props.levelId === 'jump') {
    return {
      pos: `下标 ${pos.value}`,
      reach: `最远 ${maxReach.value}`,
    }
  }
  return {
    picked: picked.value.length
      ? picked.value.map((x) => `[${intervals[x]!.start},${intervals[x]!.end}]`).join(' ')
      : '无',
  }
})

function onJumpCell(i: number) {
  if (props.levelId !== 'jump' || won.value) return
  const cur = pos.value
  if (i === cur) {
    fail.value = true
    msg.value = '不能停留在原地，请选择跳跃范围内的下一格'
    return
  }
  if (i < cur) {
    fail.value = true
    msg.value = '不能往回跳，贪心只往前走'
    return
  }
  const range = cur + jumps[cur]!
  if (i > range) {
    fail.value = true
    msg.value = `位置 ${i} 超出当前跳跃范围 [${cur + 1}, ${range}]（jumps[${cur}]=${jumps[cur]}）`
    pushLog(`非法跳跃：${i} 超出范围`)
    return
  }
  // 贪心校验：必须选能最大化 i + jumps[i] 的格子
  const greedy = jumpGreedyNext.value
  if (greedy !== -1 && i !== greedy) {
    const greedyReach = greedy + jumps[greedy]!
    const curReach = i + jumps[i]!
    fail.value = true
    msg.value = `贪心应选位置 ${greedy}（可达 ${greedyReach}），你选的 ${i} 只能到 ${curReach}，应最大化 i+jumps[i]`
    pushLog(`非贪心选择：选 ${i}，应选 ${greedy}`)
    return
  }
  pos.value = i
  maxReach.value = Math.max(maxReach.value, i + jumps[i]!)
  fail.value = false
  msg.value = `跳到位置 ${i}，最远可达下标 ${maxReach.value}`
  pushLog(`跳跃到 ${i}，最远可达 ${maxReach.value}`)
  if (maxReach.value >= jumps.length - 1) {
    won.value = true
    msg.value = '能到终点！'
    pushLog('到达终点')
    emit('cleared')
    return
  }
  // 卡死判定：当前位置无法继续前进，且 maxReach 也无法到终点
  if (jumps[i] === 0 && maxReach.value < jumps.length - 1) {
    fail.value = true
    msg.value = `位置 ${i} 的 jumps=0，无法继续前进，且最远可达 ${maxReach.value} 不足到终点 ${jumps.length - 1}，本局卡死`
    pushLog('卡死：无法到达终点')
  }
}

function pickInterval(i: number) {
  if (props.levelId === 'jump' || won.value) return
  if (picked.value.includes(i)) {
    fail.value = true
    msg.value = '该区间已选过'
    return
  }
  const last = picked.value[picked.value.length - 1]
  const lastEnd = last !== undefined ? intervals[last]!.end : 0
  if (intervals[i]!.start < lastEnd) {
    fail.value = true
    msg.value = `区间 [${intervals[i]!.start},${intervals[i]!.end}] 与已选重叠（lastEnd=${lastEnd}），贪心应选 start ≥ lastEnd 的区间`
    pushLog(`区间 ${i} 与已选重叠`)
    return
  }
  // 贪心校验：必须选 end 最小的合法区间
  const greedy = intervalGreedyNext.value
  if (greedy !== -1 && i !== greedy) {
    fail.value = true
    msg.value = `贪心应选结束最早的区间 [${intervals[greedy]!.start},${intervals[greedy]!.end}]（end=${intervals[greedy]!.end}），你选的 end=${intervals[i]!.end}，应按 end 升序选`
    pushLog(`非贪心选择：选 ${i}，应选 ${greedy}`)
    return
  }
  picked.value.push(i)
  fail.value = false
  msg.value = `已选 ${picked.value.length} 个：${picked.value.map((x) => `[${intervals[x]!.start},${intervals[x]!.end}]`).join(' ')}`
  pushLog(`选择区间 [${intervals[i]!.start},${intervals[i]!.end}]`)
  if (picked.value.length >= 3) {
    won.value = true
    pushLog('选满 3 个不重叠区间')
    emit('cleared')
    return
  }
  // 卡死判定：若剩余可选项不足凑齐 3 个，提示卡死
  const newLastEnd = intervals[i]!.end
  const remaining = intervals.filter((_, idx) => !picked.value.includes(idx) && intervals[idx]!.start >= newLastEnd).length
  if (remaining < 3 - picked.value.length) {
    fail.value = true
    msg.value = `已选 ${picked.value.length} 个，但剩余仅 ${remaining} 个可合法选择，凑不齐 3 个，本局卡死`
    pushLog('卡死：剩余可选不足')
  }
}

function doReset() {
  pos.value = 0
  maxReach.value = jumps[0] ?? 0
  picked.value = []
  won.value = false
  fail.value = false
  msg.value =
    props.levelId === 'jump'
      ? '点击想跳到的目标格子（须在当前跳跃范围内），贪心选择能最大化 i+jumps[i] 的格子'
      : '按结束时间贪心：每步点击结束最早且不与已选重叠的区间'
  clearLog('已重置')
}
</script>

<template>
  <GamePlayShell
    v-if="shellMeta"
    :meta="shellMeta"
    :hint="msg"
    :fail="fail"
    :won="won"
    :step-index="stepIndex"
    :state-values="stateValues"
    :action-log="actionLog"
    @reset="doReset"
  >
    <div class="workbench">
      <template v-if="levelId === 'jump'">
        <div class="workbench-head">
          <span class="workbench-title">跳跃覆盖</span>
          <code class="workbench-snap">[{{ jumps.join(', ') }}]</code>
        </div>
        <GameArrayBoard
          :values="jumps"
          :pointers="{ pos: pos, reach: maxReach }"
          :active-index="pos"
          clickable
          @select="onJumpCell"
        />
        <p class="meta">点击想跳到的格子（须在 (pos, pos+jumps[pos]] 范围内，贪心选最大化 i+jumps[i] 的格子）。最远可达下标：{{ maxReach }} / 目标 {{ jumps.length - 1 }}</p>
      </template>
      <template v-else>
        <div class="workbench-head">
          <span class="workbench-title">会议室调度</span>
        </div>
        <div class="interval-grid">
          <button
            v-for="(iv, i) in intervals"
            :key="i"
            type="button"
            class="interval-btn"
            :class="{ picked: picked.includes(i) }"
            @click="pickInterval(i)"
          >
            <span class="iv-label">区间 {{ i + 1 }}</span>
            [{{ iv.start }}, {{ iv.end }}]
          </button>
        </div>
        <p class="meta">贪心策略：每次选结束时间最早且不与已选重叠的区间</p>
      </template>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.meta {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--alp-color-muted);
}
.interval-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.interval-btn {
  padding: 18px 16px;
  border-radius: 12px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.12s, transform 0.12s;
}
.interval-btn:hover {
  transform: translateY(-2px);
  border-color: #3a8a9e;
}
.interval-btn.picked {
  border-color: #4a8a5e;
  background: color-mix(in srgb, #4a8a5e 15%, transparent);
}
.iv-label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: var(--alp-color-muted);
  margin-bottom: 4px;
}
</style>
