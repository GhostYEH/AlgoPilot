<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GamePlayShell from '@/modules/games/shared/GamePlayShell.vue'
import { getGameShellMeta } from '@/modules/games/shared/gameShellMeta'
import { useGameActionLog } from '@/modules/games/shared/useGameActionLog'

const props = defineProps<{ levelId: string }>()
const emit = defineEmits<{ cleared: [] }>()

const shellMeta = computed(() => getGameShellMeta('hash-locker', props.levelId)!)
const { actionLog, pushLog, clearLog } = useGameActionLog()

const BUCKET_SIZE = 7
const initialQueueLen = ref(4)
const buckets = ref<string[][]>([])
const queue = ref<{ key: number; label: string }[]>([])
const current = ref<{ key: number; label: string } | null>(null)
const msg = ref('')
const won = ref(false)
const fail = ref(false)
const rehashPhase = ref(0)

const stepIndex = computed(() => {
  if (won.value) return initialQueueLen.value + (props.levelId === 'rehash' ? 3 : 0)
  const done = initialQueueLen.value - queue.value.length + (rehashPhase.value > 0 ? initialQueueLen.value : 0)
  return Math.min(done, (shellMeta.value?.stepCount ?? 4) - 1)
})

const stateValues = computed(() => ({
  mod: String(buckets.value.length),
  key: current.value ? String(current.value.key) : '—',
  phase: props.levelId === 'rehash' ? `阶段 ${rehashPhase.value + 1}/2` : '入桶',
}))

watch(() => props.levelId, reset, { immediate: true })

function reset() {
  rehashPhase.value = 0
  won.value = false
  fail.value = false
  buckets.value = Array.from({ length: BUCKET_SIZE }, () => [])
  if (props.levelId === 'basic') {
    // 不同 key 散列到不同桶，演示无冲突入桶（10%7=3, 20%7=6, 15%7=1, 25%7=4）
    queue.value = [
      { key: 10, label: '包裹#10' },
      { key: 20, label: '包裹#20' },
      { key: 15, label: '包裹#15' },
      { key: 25, label: '包裹#25' },
    ]
  } else {
    // chain / rehash：相同取模制造冲突（12/19/26/33 % 7 均为 5）
    queue.value = [
      { key: 12, label: '包裹#12' },
      { key: 19, label: '包裹#19' },
      { key: 26, label: '包裹#26' },
      { key: 33, label: '包裹#33' },
    ]
    if (props.levelId === 'rehash') {
      queue.value.push({ key: 40, label: '包裹#40' }, { key: 47, label: '包裹#47' })
    }
  }
  initialQueueLen.value = queue.value.length
  current.value = queue.value[0] ?? null
  msg.value = current.value ? `请放入桶 ${current.value.key % buckets.value.length}` : ''
  clearLog('快递柜已就绪，按 key % 桶数入桶')
}

function startRehashPhase() {
  rehashPhase.value = 1
  buckets.value = Array.from({ length: 14 }, () => [])
  queue.value = [
    { key: 12, label: '包裹#12' },
    { key: 19, label: '包裹#19' },
    { key: 26, label: '包裹#26' },
    { key: 33, label: '包裹#33' },
    { key: 40, label: '包裹#40' },
    { key: 47, label: '包裹#47' },
  ]
  current.value = queue.value[0]!
  msg.value = '表满 → 已 rehash 到 14 桶，请重新放入全部包裹'
  pushLog('触发 rehash：7 桶 → 14 桶')
}

function pickBucket(i: number) {
  if (!current.value || won.value) return
  const mod = buckets.value.length
  const expect = current.value.key % mod
  if (i !== expect) {
    fail.value = true
    msg.value = `错误：${current.value.key} % ${mod} = ${expect}，不是 ${i}`
    pushLog(`入桶错误：选了桶 ${i}`)
    return
  }
  const chain = buckets.value[i]!
  if (props.levelId === 'chain' && chain.length > 0) {
    chain.push(current.value.label)
    msg.value = '冲突：拉链到桶尾'
    pushLog(`${current.value.label} 拉链到桶 ${i}`)
  } else if (chain.length > 0 && props.levelId === 'basic') {
    fail.value = true
    msg.value = '该桶已有元素，请用「拉链法」关练习冲突'
    return
  } else {
    chain.push(current.value.label)
    pushLog(`${current.value.label} → 桶 ${i}`)
  }
  fail.value = false
  queue.value.shift()
  current.value = queue.value[0] ?? null

  if (!current.value) {
    if (props.levelId === 'rehash' && rehashPhase.value === 0) {
      startRehashPhase()
      return
    }
    won.value = true
    msg.value = props.levelId === 'rehash' ? 'rehash 后全部入桶完成！' : '全部入桶完成！'
    pushLog('全部包裹入桶完成')
    emit('cleared')
    return
  }
  msg.value = `下一包裹 ${current.value.label} → 桶 ${current.value.key % mod}`
}

const pendingQueue = computed(() => queue.value.map((q) => q.label))
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
    @reset="reset"
  >
    <div class="workbench">
      <div class="workbench-head">
        <span class="workbench-title">哈希桶阵列</span>
        <code class="workbench-snap">{{ buckets.length }} 桶 · 待处理 {{ pendingQueue.length }} 件</code>
      </div>
      <div v-if="current" class="current-pkg">
        <span class="pkg-label">当前包裹</span>
        <strong>{{ current.label }}</strong>
        <span class="pkg-formula">{{ current.key }} % {{ buckets.length }} = {{ current.key % buckets.length }}</span>
      </div>
      <div class="bucket-grid">
        <button
          v-for="(b, i) in buckets"
          :key="i"
          type="button"
          class="bucket"
          :class="{ 'is-target': current && current.key % buckets.length === i }"
          @click="pickBucket(i)"
        >
          <span class="bucket-id">桶 {{ i }}</span>
          <span v-for="(item, j) in b" :key="j" class="pkg">{{ item }}</span>
          <span v-if="!b.length" class="bucket-empty">空</span>
        </button>
      </div>
      <div v-if="queue.length" class="queue-preview">
        <span class="queue-label">排队中：</span>
        <span v-for="q in queue" :key="q.key" class="queue-chip">{{ q.label }}</span>
      </div>
    </div>
  </GamePlayShell>
</template>

<style scoped>
.current-pkg {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  background: color-mix(in srgb, #9c8540 12%, transparent);
  border: 1px solid color-mix(in srgb, #9c8540 35%, transparent);
}

.pkg-label {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.pkg-formula {
  margin-left: auto;
  font-size: 12px;
  font-family: ui-monospace, monospace;
  color: #6a9eb0;
}

.bucket-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 10px;
}

.bucket {
  min-height: 72px;
  padding: 8px;
  border-radius: 10px;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.12s, transform 0.12s;
}

.bucket:hover {
  transform: translateY(-2px);
  border-color: #3a8a9e;
}

.bucket.is-target {
  border-color: #9c8540;
  box-shadow: 0 0 0 2px color-mix(in srgb, #9c8540 30%, transparent);
}

.bucket-id {
  display: block;
  font-size: 10px;
  font-weight: 700;
  color: var(--alp-color-muted);
  margin-bottom: 4px;
}

.pkg {
  display: block;
  font-size: 11px;
  margin-top: 2px;
}

.bucket-empty {
  font-size: 11px;
  color: var(--alp-color-muted);
  font-style: italic;
}

.queue-preview {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  font-size: 12px;
}

.queue-label {
  color: var(--alp-color-muted);
}

.queue-chip {
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}
</style>
