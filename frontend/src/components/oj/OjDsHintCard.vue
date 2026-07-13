<script setup lang="ts">
import { ref, toRef } from 'vue'
import { Collection, Lock } from '@element-plus/icons-vue'
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

const { dsLoading, dsStreaming, dsReply, fetchDsHint } = useOjAssistantHints(
  problemRef,
  languageRef,
  emptyCode,
)
</script>

<template>
  <el-card shadow="never" class="oj-agent-card oj-agent-card--ds oj-agent-card--dual">
    <template #header>
      <div class="oj-agent-head">
        <span class="oj-agent-title">
          <el-icon><Collection /></el-icon>
          数据结构提示
        </span>
        <span v-if="dsStreaming" class="oj-stream-badge">AI 输出中…</span>
      </div>
    </template>
    <div class="oj-agent-actions">
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
    </div>
    <div class="oj-agent-body" :class="{ 'is-blurred': !dsReply && !dsLoading }">
      <!-- 模糊遮罩：未点击分析时覆盖占位预览 -->
      <div v-if="!dsReply && !dsLoading" class="oj-blur-overlay" @click="fetchDsHint">
        <el-icon class="oj-blur-icon"><Lock /></el-icon>
        <span class="oj-blur-tip">点击「分析本题结构」解锁 AI 分析</span>
        <span class="oj-blur-sub">将分析本题所需数据结构与容器操作</span>
      </div>
      <!-- 占位预览文字（被模糊覆盖） -->
      <div v-if="!dsReply && !dsLoading" class="oj-blur-preview" aria-hidden="true">
        <h3 class="ai-md-h">推荐数据结构</h3>
        <p class="ai-md-p">本题主要考察线性结构的增删查改操作，可考虑使用顺序表或链表实现。</p>
        <ul class="ai-md-ul">
          <li><code class="ai-md-code">vector</code>：尾插 O(1)，随机访问 O(1)</li>
          <li><code class="ai-md-code">list</code>：任意位置插入/删除 O(1)</li>
          <li><code class="ai-md-code">unordered_map</code>：哈希计数 O(1) 均摊</li>
        </ul>
        <p class="ai-md-p">复杂度直觉：时间 O(n)，空间 O(n)。</p>
      </div>
      <!-- 流式输出实时渲染（流式时显示纯文本 + 光标；完成后显示 markdown） -->
      <div v-if="dsLoading || dsReply" class="oj-stream-area">
        <div
          v-if="dsStreaming"
          class="oj-stream-text"
        >{{ dsReply }}<span class="oj-stream-cursor" /></div>
        <div
          v-else-if="dsReply"
          class="oj-agent-reply ai-md-body"
          v-html="renderAiReplyHtml(dsReply)"
        />
      </div>
    </div>
  </el-card>
</template>

<style scoped src="./oj-agent-card.css"></style>
