<script setup lang="ts">
import { ref, toRef } from 'vue'
import { Collection } from '@element-plus/icons-vue'
import type { ProblemDetail } from '@/api/oj'
import { useOjAssistantHints } from '@/composables/useOjAssistantHints'
import { renderAiReplyHtml } from '@/utils/renderAiReply'

const props = defineProps<{
  problem: ProblemDetail
  language: 'python' | 'cpp'
}>()

const problemRef = toRef(props, 'problem')
const languageRef = toRef(props, 'language')
const emptyCode = ref('')

const { dsLoading, dsReply, fetchDsHint } = useOjAssistantHints(
  problemRef,
  languageRef,
  emptyCode,
)
</script>

<template>
  <el-card shadow="never" class="oj-agent-card oj-agent-card--ds">
    <template #header>
      <div class="oj-agent-head">
        <span class="oj-agent-title">
          <el-icon><Collection /></el-icon>
          数据结构提示
        </span>
      </div>
    </template>
    <p class="oj-agent-desc">分析本题需要哪些数据结构，并简述 STL/容器常用操作。</p>
    <el-button
      type="primary"
      size="small"
      class="oj-agent-btn"
      :loading="dsLoading"
      @click="fetchDsHint"
    >
      分析本题结构
    </el-button>
    <div v-loading="dsLoading" class="oj-agent-body">
      <p v-if="!dsReply && !dsLoading" class="oj-agent-placeholder">点击上方按钮获取分析</p>
      <div
        v-else-if="dsReply"
        class="oj-agent-reply ai-md-body"
        v-html="renderAiReplyHtml(dsReply)"
      />
    </div>
  </el-card>
</template>

<style scoped src="./oj-agent-card.css"></style>
