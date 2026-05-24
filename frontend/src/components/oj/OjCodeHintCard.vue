<script setup lang="ts">
import { toRef } from 'vue'
import { Guide } from '@element-plus/icons-vue'
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

const { codeLoading, codeReply, fetchCodeHint } = useOjAssistantHints(
  problemRef,
  languageRef,
  userCodeRef,
)
</script>

<template>
  <el-card shadow="never" class="oj-agent-card oj-agent-card--hint">
    <template #header>
      <div class="oj-agent-head">
        <span class="oj-agent-title">
          <el-icon><Guide /></el-icon>
          AI 思路提示
        </span>
      </div>
    </template>
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
    <div v-loading="codeLoading" class="oj-agent-body">
      <p v-if="!codeReply && !codeLoading" class="oj-agent-placeholder">
        先写一点代码再点，或空代码也会给第一步思路
      </p>
      <div
        v-else-if="codeReply"
        class="oj-agent-reply ai-md-body"
        v-html="renderAiReplyHtml(codeReply)"
      />
    </div>
  </el-card>
</template>

<style scoped src="./oj-agent-card.css"></style>
