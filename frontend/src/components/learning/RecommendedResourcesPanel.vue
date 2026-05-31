<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { MagicStick, Document } from '@element-plus/icons-vue'
import {
  fetchRecommendedResources,
  RESOURCE_TYPE_META,
  resourceVerifyTag,
  type GeneratedResource,
} from '@/api/orchestrator'
import { verificationDisplayTag } from '@/utils/verification'
import { isLoggedIn } from '@/stores/auth'

const props = defineProps<{
  moduleKey?: string
  limit?: number
  title?: string
}>()

const router = useRouter()
const items = ref<GeneratedResource[]>([])
const loading = ref(false)

async function load() {
  if (!isLoggedIn.value) {
    items.value = []
    return
  }
  loading.value = true
  try {
    items.value = await fetchRecommendedResources({
      module_key: props.moduleKey,
      limit: props.limit ?? 4,
    })
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => [props.moduleKey, isLoggedIn.value], load)

function openResource(r: GeneratedResource) {
  router.push({ name: 'resources', query: { highlight: String(r.id) } })
}

function typeLabel(type: string) {
  return RESOURCE_TYPE_META[type]?.label ?? type
}
</script>

<template>
  <div v-if="isLoggedIn" class="rec-panel">
    <div class="rec-head">
      <el-icon><MagicStick /></el-icon>
      <span>{{ title ?? '为你推荐的学习资源' }}</span>
      <el-button v-if="items.length" type="primary" link @click="router.push({ name: 'resources' })">
        资源库
      </el-button>
    </div>
    <el-skeleton v-if="loading" :rows="2" animated />
    <el-empty v-else-if="!items.length" description="暂无生成资源，可前往资源库一键生成" :image-size="56">
      <el-button type="primary" plain size="small" @click="router.push({ name: 'resources' })">
        去生成
      </el-button>
    </el-empty>
    <div v-else class="rec-list">
      <div
        v-for="r in items"
        :key="r.id"
        class="rec-item"
        role="button"
        tabindex="0"
        @click="openResource(r)"
        @keyup.enter="openResource(r)"
      >
        <el-icon class="rec-icon"><Document /></el-icon>
        <div class="rec-body">
          <div class="rec-title">{{ r.title }}</div>
          <div class="rec-meta">
            <el-tag size="small" effect="plain">{{ typeLabel(r.resource_type) }}</el-tag>
            <span class="agent">{{ r.agent_name }}</span>
            <el-tag
              size="small"
              :type="resourceVerifyTag(r.meta ?? {}).type"
              effect="plain"
            >
              {{ verificationDisplayTag(r.meta ?? {}).riskLabel }}
            </el-tag>
            <span v-if="r.meta?.chapter_id" class="chapter">{{ r.meta.chapter_id }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rec-panel {
  margin-top: 12px;
}

.rec-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 10px;
  color: var(--alp-color-text);
}

.rec-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rec-item {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--alp-radius-card);
  border: 1px solid var(--alp-color-border);
  background: var(--alp-bg-soft-block);
  cursor: pointer;
  transition: border-color 0.15s;
}

.rec-item:hover {
  border-color: var(--alp-color-primary);
}

.rec-icon {
  color: var(--alp-color-primary);
  margin-top: 2px;
}

.rec-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--alp-color-text);
  line-height: 1.4;
}

.rec-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.rec-meta .chapter {
  font-size: 11px;
  color: var(--alp-color-muted);
}

.agent {
  font-size: 11px;
  color: var(--alp-color-muted);
}
</style>
