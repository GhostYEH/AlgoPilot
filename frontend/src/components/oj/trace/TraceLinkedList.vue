<script setup lang="ts">
import { computed } from 'vue'
import TraceVizLegend from '@/components/oj/trace/TraceVizLegend.vue'
import type { LinkedListGraph } from '@/types/codeTrace'
import { orphanNodeIds, orderedFromHead } from '@/utils/traceLinkedList'

const props = defineProps<{
  name: string
  graph: LinkedListGraph
  pointerLabels?: Record<string, string[]>
  hotNodes?: Set<string>
  hotEdges?: Set<string>
  hotPointers?: Set<string>
  varChanged?: boolean
}>()

const mainChain = computed(() => orderedFromHead(props.graph))
const orphans = computed(() => orphanNodeIds(props.graph))

function edgeHot(fromId: string) {
  const to = props.graph.nodes[fromId]?.next ?? null
  const key = `${fromId}->${to ?? 'null'}`
  return props.hotEdges?.has(key) ?? false
}

function nodeHot(id: string) {
  return props.hotNodes?.has(id) ?? false
}

function ptrHot(name: string) {
  return props.hotPointers?.has(name) ?? false
}
</script>

<template>
  <div class="trace-ll" :class="{ 'trace-ll--hot': varChanged }">
    <div class="trace-ll-label">
      {{ name }}
      <span class="tag">链表</span>
    </div>
    <TraceVizLegend variant="linked_list" />

    <div v-if="!Object.keys(graph.nodes).length" class="trace-ll-empty">空链表</div>

    <div v-else class="trace-ll-stage">
      <p class="trace-ll-section-title">主链（head 出发）</p>
      <div class="trace-ll-chain" role="list">
        <template v-for="(id, idx) in mainChain" :key="id">
          <div class="trace-ll-node-wrap" role="listitem">
            <div v-if="pointerLabels?.[id]?.length" class="trace-ll-ptrs">
              <span
                v-for="p in pointerLabels[id]"
                :key="p"
                class="trace-ll-ptr"
                :class="{ 'trace-ll-ptr--hot': ptrHot(p) }"
              >{{ p }}</span>
            </div>
            <div
              class="trace-ll-node"
              :class="{
                'trace-ll-node--has-ptr': pointerLabels?.[id]?.length,
                'trace-ll-node--hot': nodeHot(id),
              }"
            >
              {{ graph.nodes[id]?.val ?? '?' }}
            </div>
          </div>
          <div
            v-if="idx < mainChain.length - 1"
            class="trace-ll-arrow-wrap"
            :class="{ 'trace-ll-arrow-wrap--hot': edgeHot(id) }"
          >
            <span class="trace-ll-arrow" aria-hidden="true">→</span>
          </div>
        </template>
        <span class="trace-ll-null">∅</span>
      </div>

      <div v-if="orphans.length" class="trace-ll-orphans">
        <p class="trace-ll-section-title">其它节点（next 已改 / 已断开）</p>
        <div class="trace-ll-orphan-row">
          <div
            v-for="id in orphans"
            :key="id"
            class="trace-ll-node-wrap trace-ll-node-wrap--orphan"
          >
            <div v-if="pointerLabels?.[id]?.length" class="trace-ll-ptrs">
              <span
                v-for="p in pointerLabels[id]"
                :key="p"
                class="trace-ll-ptr trace-ll-ptr--hot"
              >{{ p }}</span>
            </div>
            <div class="trace-ll-node trace-ll-node--hot">
              {{ graph.nodes[id]?.val ?? '?' }}
            </div>
            <span class="trace-ll-next-hint">
              next → {{ graph.nodes[id]?.next ?? 'null' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.trace-ll {
  margin-bottom: 14px;
}

.trace-ll-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.trace-ll--hot .trace-ll-label {
  color: var(--el-color-primary);
}

.tag {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.trace-ll-stage {
  padding: 12px 10px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.trace-ll-section-title {
  margin: 0 0 8px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.trace-ll-chain {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 4px;
  padding-bottom: 8px;
}

.trace-ll-node-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.trace-ll-ptrs {
  position: absolute;
  bottom: 100%;
  margin-bottom: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  z-index: 2;
}

.trace-ll-ptr {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: #38bdf8;
  color: #0f172a;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.trace-ll-ptr--hot {
  background: #fbbf24;
  animation: ptr-pulse 0.55s ease;
}

.trace-ll-node {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  transition:
    border-color 0.25s,
    box-shadow 0.25s,
    transform 0.25s;
}

.trace-ll-node--has-ptr {
  border-color: #38bdf8;
  box-shadow: 0 0 0 2px color-mix(in srgb, #38bdf8 35%, transparent);
}

.trace-ll-node--hot {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--el-color-primary) 40%, transparent);
  animation: node-pulse 0.55s ease;
}

.trace-ll-arrow-wrap {
  padding: 0 4px;
  transition: transform 0.2s;
}

.trace-ll-arrow-wrap--hot .trace-ll-arrow {
  color: var(--el-color-primary);
  animation: edge-pulse 0.55s ease;
}

.trace-ll-arrow {
  font-size: 20px;
  color: var(--el-text-color-secondary);
}

.trace-ll-null {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  font-family: ui-monospace, Consolas, monospace;
  margin-left: 4px;
}

.trace-ll-orphans {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--alp-color-border);
}

.trace-ll-orphan-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.trace-ll-node-wrap--orphan {
  opacity: 0.92;
}

.trace-ll-next-hint {
  margin-top: 4px;
  font-size: 10px;
  font-family: ui-monospace, Consolas, monospace;
  color: var(--el-text-color-secondary);
}

.trace-ll-empty {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

@keyframes node-pulse {
  0% {
    transform: scale(1);
  }
  45% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes ptr-pulse {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

@keyframes edge-pulse {
  0%,
  100% {
    transform: scaleX(1);
  }
  50% {
    transform: scaleX(1.25);
  }
}
</style>
