<script setup lang="ts">
import { computed } from 'vue'
import {
  ArrowDown,
  ArrowUp,
  Close,
  Guide,
  Sort,
} from '@element-plus/icons-vue'
import type { PathReplanDiffItem, PathReplanDiffResult } from '@/utils/pathReplanDiff'

const props = defineProps<{
  diff: PathReplanDiffResult | null
}>()

const emit = defineEmits<{
  dismiss: []
}>()

const visibleItems = computed(() =>
  (props.diff?.items ?? []).filter((i) => i.status !== 'removed' || i.beforeRank),
)

const changedItems = computed(() =>
  visibleItems.value.filter((i) => i.status !== 'unchanged'),
)

const unchangedItems = computed(() =>
  visibleItems.value.filter((i) => i.status === 'unchanged'),
)

function statusTagType(status: PathReplanDiffItem['status']) {
  if (status === 'added') return 'success'
  if (status === 'remediation') return 'warning'
  if (status === 'moved_up') return 'primary'
  if (status === 'moved_down') return 'info'
  if (status === 'removed') return 'danger'
  return 'info'
}

function statusLabel(item: PathReplanDiffItem) {
  switch (item.status) {
    case 'added':
      return '新增'
    case 'remediation':
      return '巩固'
    case 'moved_up':
      return '提前'
    case 'moved_down':
      return '延后'
    case 'removed':
      return '移出'
    default:
      return '不变'
  }
}

function rankText(rank: number | null) {
  return rank != null ? `#${rank}` : '—'
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso.slice(0, 16)
  }
}
</script>

<template>
  <el-card v-if="diff" shadow="never" class="replan-diff-card">
    <div class="diff-head">
      <el-icon><Sort /></el-icon>
      <div class="diff-head-text">
        <strong>动态路径重排对比</strong>
        <span class="diff-meta">{{ diff.triggerLabel }} · {{ formatTime(diff.at) }}</span>
      </div>
      <el-button :icon="Close" text circle size="small" aria-label="关闭" @click="emit('dismiss')" />
    </div>

    <el-empty
      v-if="!diff.hasChanges"
      description="本次评估后路径无需调整。"
      :image-size="64"
    />

    <template v-else>
      <p class="diff-explanation">{{ diff.explanation }}</p>

      <div v-if="diff.evidence.length" class="evidence-block">
        <span class="block-label">调整依据</span>
        <ul class="evidence-list">
          <li v-for="(line, idx) in diff.evidence" :key="idx">{{ line }}</li>
        </ul>
      </div>

      <div class="compare-grid">
        <div class="compare-col">
          <span class="col-title">调整前</span>
          <ol class="path-order">
            <li
              v-for="(key, idx) in diff.beforeKeys"
              :key="'b-' + key"
              :class="{ muted: !diff.afterKeys.includes(key) }"
            >
              <span class="rank">{{ idx + 1 }}</span>
              {{ visibleItems.find((i) => i.moduleKey === key)?.label ?? key }}
            </li>
            <li v-if="!diff.beforeKeys.length" class="empty-order">暂无已保存路径</li>
          </ol>
        </div>
        <div class="compare-col">
          <span class="col-title">调整后</span>
          <ol class="path-order">
            <li
              v-for="(key, idx) in diff.afterKeys"
              :key="'a-' + key"
            >
              <span class="rank">{{ idx + 1 }}</span>
              {{ visibleItems.find((i) => i.moduleKey === key)?.label ?? key }}
            </li>
          </ol>
        </div>
      </div>

      <div v-if="changedItems.length" class="changes-block">
        <span class="block-label">
          <el-icon><Guide /></el-icon>
          变更明细
        </span>
        <ul class="change-list">
          <li v-for="item in changedItems" :key="item.moduleKey">
            <el-tag size="small" :type="statusTagType(item.status)" effect="plain">
              {{ statusLabel(item) }}
            </el-tag>
            <span class="change-label">{{ item.label }}</span>
            <span class="change-rank">
              {{ rankText(item.beforeRank) }}
              →
              {{ rankText(item.afterRank) }}
            </span>
            <el-icon v-if="item.status === 'moved_up'" class="change-arrow up"><ArrowUp /></el-icon>
            <el-icon v-else-if="item.status === 'moved_down'" class="change-arrow down">
              <ArrowDown />
            </el-icon>
            <span v-if="item.reason" class="change-reason">{{ item.reason }}</span>
          </li>
        </ul>
      </div>

      <div v-if="unchangedItems.length" class="unchanged-block">
        <span class="block-label muted">未变化节点</span>
        <div class="unchanged-tags">
          <el-tag
            v-for="item in unchangedItems"
            :key="'u-' + item.moduleKey"
            size="small"
            type="info"
            effect="plain"
          >
            {{ item.label }}
          </el-tag>
        </div>
      </div>

      <el-alert
        v-if="diff.remediationInserted"
        type="warning"
        :closable="false"
        show-icon
        title="已插入学情巩固节点"
        class="remediation-alert"
      />
    </template>
  </el-card>
</template>

<style scoped>
.replan-diff-card {
  margin-bottom: 18px;
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 35%, var(--alp-color-border));
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
}

.diff-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}

.diff-head .el-icon {
  color: var(--el-color-primary);
  font-size: 20px;
  margin-top: 2px;
}

.diff-head-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.diff-head-text strong {
  font-size: 15px;
}

.diff-meta {
  font-size: 12px;
  color: var(--alp-color-muted);
}

.diff-explanation {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--alp-color-text);
}

.block-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.evidence-block {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--alp-bg-soft-block);
  border: 1px solid var(--alp-color-border);
}

.evidence-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.55;
  color: var(--alp-color-muted);
}

.compare-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
}

@media (max-width: 640px) {
  .compare-grid {
    grid-template-columns: 1fr;
  }
}

.compare-col {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
}

.col-title {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--alp-color-muted);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.path-order {
  margin: 0;
  padding-left: 0;
  list-style: none;
  font-size: 13px;
}

.path-order li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.path-order li.muted {
  opacity: 0.45;
  text-decoration: line-through;
}

.path-order .rank {
  font-size: 11px;
  color: var(--alp-color-muted);
  min-width: 22px;
}

.empty-order {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.changes-block {
  margin-bottom: 8px;
}

.change-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.change-list li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  margin-bottom: 6px;
  border-radius: 8px;
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-surface);
  font-size: 13px;
}

.change-label {
  font-weight: 600;
}

.change-rank {
  font-size: 11px;
  color: var(--alp-color-muted);
  font-variant-numeric: tabular-nums;
}

.change-arrow {
  font-size: 14px;
}

.change-arrow.up {
  color: var(--el-color-primary);
}

.change-arrow.down {
  color: var(--el-color-info);
}

.change-reason {
  flex: 1 1 100%;
  font-size: 12px;
  color: var(--alp-color-muted);
  line-height: 1.45;
}

.remediation-alert {
  margin-top: 8px;
}

.unchanged-block {
  margin-bottom: 10px;
}

.block-label.muted {
  color: var(--alp-color-muted);
  font-weight: 500;
}

.unchanged-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
