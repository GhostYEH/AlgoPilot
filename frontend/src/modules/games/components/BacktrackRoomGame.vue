<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('backtrack-room', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const SIZE = 4
const board = ref<number[]>(Array(SIZE * SIZE).fill(0))
const perm = ref<number[]>([])
const used = ref<boolean[]>([false, false, false, false])
const msg = ref('')
const won = ref(false)
const fail = ref(false)

watch(
  () => props.levelId,
  () => {
    board.value = Array(SIZE * SIZE).fill(0)
    perm.value = []
    used.value = [false, false, false, false]
    msg.value =
      props.levelId === 'n4'
        ? '点击格子放皇后；冲突格会提示。放满 4 个通关'
        : '全排列：按顺序点 1→2→3，已用数字会变灰'
    won.value = false
    fail.value = false
    clearLog('密室回溯开始')
  },
  { immediate: true },
)

const stepIndex = computed(() => {
  if (won.value) return props.levelId === 'n4' ? 3 : 2
  if (props.levelId === 'n4') return Math.min(board.value.filter(Boolean).length, 3)
  return Math.min(perm.value.length, 2)
})

const stateValues = computed(() => ({
  queens:
    props.levelId === 'n4'
      ? `${board.value.filter(Boolean).length} / ${SIZE}`
      : perm.value.join('') || '空',
  perm: perm.value.join(' → ') || '—',
}))

function conflict(r: number, c: number) {
  for (let i = 0; i < board.value.length; i++) {
    if (!board.value[i]) continue
    const br = Math.floor(i / SIZE)
    const bc = i % SIZE
    if (bc === c || br === r || Math.abs(br - r) === Math.abs(bc - c)) return true
  }
  return false
}

function toggleCell(i: number) {
  if (won.value) return
  if (props.levelId === 'n4') {
    const r = Math.floor(i / SIZE)
    const c = i % SIZE
    if (board.value[i]) {
      board.value[i] = 0
      msg.value = '移除皇后'
      pushLog(`移除 (${r},${c})`)
      return
    }
    if (conflict(r, c)) {
      fail.value = true
      msg.value = '冲突！该位置受同行/列/对角攻击'
      pushLog(`冲突位置 (${r},${c})`)
      return
    }
    board.value[i] = 1
    fail.value = false
    const queens = board.value.filter(Boolean).length
    pushLog(`放置皇后 (${r},${c})`)
    if (queens === SIZE) {
      won.value = true
      msg.value = '4 皇后放置成功！'
      pushLog('通关')
      emit('cleared')
    } else {
      msg.value = `已放 ${queens} / ${SIZE} 个皇后`
    }
    return
  }

  const v = (i % SIZE) + 1
  if (used.value[v - 1]) return
  if (perm.value.length > 0 && v <= perm.value[perm.value.length - 1]!) {
    fail.value = true
    msg.value = '排列必须按序尝试分支'
    return
  }
  used.value[v - 1] = true
  perm.value.push(v)
  fail.value = false
  msg.value = `当前排列：${perm.value.join('')}`
  pushLog(`选择 ${v}`)
  if (perm.value.length === 3) {
    won.value = true
    pushLog('全排列完成')
    emit('cleared')
  }
}

function undo() {
  if (props.levelId === 'n4') {
    let idx = -1
    for (let i = board.value.length - 1; i >= 0; i--) {
      if (board.value[i]) {
        idx = i
        break
      }
    }
    if (idx >= 0) board.value[idx] = 0
    msg.value = '回溯：移除一个皇后'
    pushLog('回溯移除皇后')
  } else if (perm.value.length) {
    const v = perm.value.pop()!
    used.value[v - 1] = false
    msg.value = `回溯，当前：${perm.value.join('') || '空'}`
    pushLog(`回溯，撤销 ${v}`)
  }
  fail.value = false
}

function doReset() {
  board.value = Array(SIZE * SIZE).fill(0)
  perm.value = []
  used.value = [false, false, false, false]
  won.value = false
  fail.value = false
  msg.value =
    props.levelId === 'n4'
      ? '点击格子放皇后；冲突格会提示。放满 4 个通关'
      : '全排列：按顺序点 1→2→3'
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
      <div v-if="levelId === 'n4'" class="workbench-head">
        <span class="workbench-title">4×4 棋盘</span>
        <code class="workbench-snap">已放 {{ board.filter(Boolean).length }} 皇后</code>
      </div>
      <div v-if="levelId === 'n4'" class="grid">
        <button
          v-for="(cell, i) in board"
          :key="i"
          type="button"
          class="cell"
          :class="{ queen: cell, 'is-alt': (Math.floor(i / 4) + (i % 4)) % 2 === 1 }"
          @click="toggleCell(i)"
        >
          {{ cell ? '♛' : '' }}
        </button>
      </div>
      <div v-else class="perm-area">
        <p class="perm-hint">按 1 → 2 → 3 顺序点击，构建全排列</p>
        <div class="perm-grid">
          <button
            v-for="n in 3"
            :key="n"
            type="button"
            class="perm-btn"
            :class="{ used: used[n - 1], next: perm.length === n - 1 }"
            :disabled="used[n - 1]"
            @click="toggleCell(n - 1)"
          >
            {{ n }}
          </button>
        </div>
        <p v-if="perm.length" class="perm-trail">路径：{{ perm.join(' → ') }}</p>
      </div>
    </div>
    <template #actions>
      <el-button @click="undo">撤销 (回溯)</el-button>
    </template>
  </GamePlayShell>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(4, 56px);
  gap: 6px;
  margin: 0 auto;
  width: fit-content;
}
.cell {
  width: 56px;
  height: 56px;
  border: 2px solid var(--alp-color-border);
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  cursor: pointer;
  font-size: 24px;
  transition: transform 0.12s, border-color 0.12s;
}
.cell.is-alt {
  background: color-mix(in srgb, var(--alp-color-border) 30%, transparent);
}
.cell:hover {
  transform: scale(1.04);
  border-color: #38bdf8;
}
.cell.queen {
  background: color-mix(in srgb, #f472b6 25%, transparent);
  border-color: #f472b6;
}
.perm-area {
  text-align: center;
}
.perm-hint {
  font-size: 13px;
  color: var(--alp-color-muted);
  margin: 0 0 16px;
}
.perm-grid {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 12px;
}
.perm-btn {
  width: 72px;
  height: 72px;
  border-radius: 14px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  font-size: 28px;
  font-weight: 700;
  cursor: pointer;
}
.perm-btn.used {
  opacity: 0.35;
  cursor: not-allowed;
}
.perm-btn.next {
  border-color: #fbbf24;
  box-shadow: 0 0 0 3px color-mix(in srgb, #fbbf24 30%, transparent);
}
.perm-trail {
  font-size: 14px;
  color: var(--game-accent, #38bdf8);
  margin: 0;
}
</style>
