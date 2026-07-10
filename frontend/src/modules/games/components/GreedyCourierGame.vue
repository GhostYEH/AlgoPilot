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
  { start: 2, end: 4 },
  { start: 3, end: 5 },
  { start: 1, end: 2 },
]

watch(
  () => props.levelId,
  () => {
    pos.value = 0
    maxReach.value = jumps[0] ?? 0
    picked.value = []
    msg.value =
      props.levelId === 'jump'
        ? '点击当前位置，再点「跳跃」更新最远可达；当 maxReach ≥ 末下标即通关'
        : '按结束时间贪心：点击区间，已选区间不能重叠'
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
  if (i !== pos.value) {
    fail.value = true
    msg.value = `只能操作当前位置 ${pos.value}`
    return
  }
  fail.value = false
  msg.value = `选中位置 ${i}，点击「跳跃」`
  pushLog(`选中位置 ${i}`)
}

function doJump() {
  if (props.levelId !== 'jump' || won.value) return
  const reach = pos.value + jumps[pos.value]!
  maxReach.value = Math.max(maxReach.value, reach)
  pos.value = Math.min(pos.value + 1, jumps.length - 1)
  msg.value = `到达 ${pos.value}，最远可达下标 ${maxReach.value}`
  fail.value = false
  pushLog(`跳跃：最远可达 ${maxReach.value}`)
  if (maxReach.value >= jumps.length - 1) {
    won.value = true
    msg.value = '能到终点！'
    pushLog('到达终点')
    emit('cleared')
  }
}

function pickInterval(i: number) {
  if (won.value) return
  const last = picked.value[picked.value.length - 1]
  const lastEnd = last !== undefined ? intervals[last]!.end : 0
  if (intervals[i]!.start < lastEnd) {
    fail.value = true
    msg.value = '与上一区间重叠，贪心应选结束更早的'
    pushLog(`区间 ${i} 与已选重叠`)
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
      ? '点击当前位置，再点「跳跃」更新最远可达'
      : '按结束时间贪心选择区间'
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
          @select="onJumpCell"
        />
        <p class="meta">最远可达下标：{{ maxReach }} / 目标 {{ jumps.length - 1 }}</p>
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
    <template v-if="levelId === 'jump'" #actions>
      <el-button type="primary" size="large" :disabled="won" @click="doJump">从当前格跳跃</el-button>
    </template>
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
  border-color: #22d3ee;
}
.interval-btn.picked {
  border-color: #22c55e;
  background: color-mix(in srgb, #22c55e 15%, transparent);
}
.iv-label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: var(--alp-color-muted);
  margin-bottom: 4px;
}
</style>
