<script setup lang="ts">
import { ref } from 'vue'
import { CircleCheck, Expand, Fold } from '@element-plus/icons-vue'

export interface SectionNavItem {
  id: string
  title: string
  subtitle: string
}

defineProps<{
  sections: SectionNavItem[]
  activeSection: string
  doneMap: Record<string, boolean>
  sectionIndex: number
  sectionCount: number
  ariaLabel?: string
}>()

const emit = defineEmits<{
  select: [id: string]
}>()

const collapsed = ref(false)

function shortTitle(s: SectionNavItem) {
  return s.title.replace(/^\d+\.\s*/, '')
}
</script>

<template>
  <div class="section-aside-col" :class="{ 'is-collapsed': collapsed }">
    <div class="aside-sticky section-directory">
      <div class="aside-head">
        <div v-show="!collapsed" class="aside-head-text">
          <span class="aside-title">章节目录</span>
          <span class="aside-sub">{{ sectionIndex + 1 }} / {{ sectionCount }}</span>
        </div>
        <el-button
          class="aside-collapse-btn"
          :icon="collapsed ? Expand : Fold"
          circle
          size="small"
          text
          bg
          :title="collapsed ? '展开目录' : '收起目录'"
          :aria-label="collapsed ? '展开章节目录' : '收起章节目录'"
          @click="collapsed = !collapsed"
        />
      </div>

      <div v-show="!collapsed" class="section-nav-body">
        <nav class="section-nav" :aria-label="ariaLabel ?? '章节目录'">
          <button
            v-for="(s, i) in sections"
            :key="s.id"
            type="button"
            class="nav-btn"
            :class="{ active: activeSection === s.id, done: doneMap[s.id] }"
            @click="emit('select', s.id)"
          >
            <span class="nav-idx">{{ i + 1 }}</span>
            <span class="nav-text">
              <span class="nav-line">{{ shortTitle(s) }}</span>
              <span class="nav-sub">{{ s.subtitle }}</span>
            </span>
            <el-icon v-if="doneMap[s.id]" class="nav-check" :size="16"><CircleCheck /></el-icon>
          </button>
        </nav>
      </div>

      <nav v-show="collapsed" class="section-nav-mini" :aria-label="ariaLabel ?? '章节目录'">
        <button
          v-for="(s, i) in sections"
          :key="s.id"
          type="button"
          class="mini-nav-btn"
          :class="{ active: activeSection === s.id, done: doneMap[s.id] }"
          :title="shortTitle(s)"
          :aria-current="activeSection === s.id ? 'step' : undefined"
          @click="emit('select', s.id)"
        >
          {{ i + 1 }}
        </button>
      </nav>
    </div>

  </div>
</template>
