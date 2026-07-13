<script setup lang="ts">
import { toRef } from 'vue'
import { Guide, Lock } from '@element-plus/icons-vue'
import type { ProblemDetail } from '@/api/oj'
import { useOjAssistantHints } from '@/composables/useOjAssistantHints'
import { renderAiReplyHtml } from '@/utils/renderAiReply'

const props = defineProps<{
  problem: ProblemDetail
  language: 'python' | 'cpp'
  userCode: string
}>()

const problemRef = toRef(props, 'problem')
const languageRef = toRef(props, 'language')
const userCodeRef = toRef(props, 'userCode')

const { codeLoading, codeStreaming, codeReply, fetchCodeHint } = useOjAssistantHints(
  problemRef,
  languageRef,
  userCodeRef,
)
</script>

<template>
  <el-card shadow="never" class="oj-agent-card oj-agent-card--hint oj-agent-card--dual">
    <template #header>
      <div class="oj-agent-head">
        <span class="oj-agent-title">
          <el-icon><Guide /></el-icon>
          AI 思路提示
        </span>
        <span v-if="codeStreaming" class="oj-stream-badge">AI 输出中…</span>
      </div>
    </template>
    <div class="oj-agent-actions">
      <p class="oj-agent-desc">
        根据你<strong>当前代码</strong>提示下一步怎么做，<strong>不会</strong>给出代码。
      </p>
      <el-button
        type="primary"
        size="small"
        class="oj-agent-btn"
        :loading="codeLoading"
        @click="fetchCodeHint"
      >
        分析我的代码
      </el-button>
    </div>
    <div class="oj-agent-body" :class="{ 'is-blurred': !codeReply && !codeLoading }">
      <!-- 模糊遮罩：未点击分析时覆盖占位预览 -->
      <div v-if="!codeReply && !codeLoading" class="oj-blur-overlay" @click="fetchCodeHint">
        <el-icon class="oj-blur-icon"><Lock /></el-icon>
        <span class="oj-blur-tip">点击「分析我的代码」解锁 AI 思路</span>
        <span class="oj-blur-sub">将根据你的代码给出下一步建议（不给代码）</span>
      </div>
      <!-- 占位预览文字（被模糊覆盖） -->
      <div v-if="!codeReply && !codeLoading" class="oj-blur-preview" aria-hidden="true">
        <h3 class="ai-md-h">下一步思路建议</h3>
        <ol class="ai-md-ol">
          <li>先确认输入规模与边界情况，例如空数组、单元素、负数等。</li>
          <li>检查你当前代码中循环的终止条件是否覆盖所有情况。</li>
          <li>考虑使用双指针或哈希表优化当前 O(n²) 的双重循环。</li>
          <li>对照样例手推一遍你的算法流程，定位逻辑偏差。</li>
        </ol>
        <p class="ai-md-p">提示：如果输入为空，你的循环还会执行吗？</p>
      </div>
      <!-- 流式输出实时渲染 -->
      <div v-if="codeLoading || codeReply" class="oj-stream-area">
        <div
          v-if="codeStreaming"
          class="oj-stream-text"
        >{{ codeReply }}<span class="oj-stream-cursor" /></div>
        <div
          v-else-if="codeReply"
          class="oj-agent-reply ai-md-body"
          v-html="renderAiReplyHtml(codeReply)"
        />
      </div>
    </div>
  </el-card>
</template>

<style scoped src="./oj-agent-card.css"></style>
