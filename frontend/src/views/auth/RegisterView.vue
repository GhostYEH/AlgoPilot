<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { Lock, Message, User } from '@element-plus/icons-vue'

import AuthPageFrame from '@/components/auth/AuthPageFrame.vue'
import { registerApi } from '@/api/auth'
import {
  confirmPasswordRules,
  emailOptionalRules,
  passwordRules,
  usernameRules,
} from '@/utils/authFormRules'
import { setSession, syncLearningProgressAfterAuth } from '@/stores/auth'
import { needsOnboarding } from '@/composables/usePersonaGate'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const registerRole = ref<'student' | 'teacher'>('student')

const form = reactive({
  username: '',
  password: '',
  password2: '',
  email: '',
})

const rules: FormRules = {
  username: usernameRules,
  password: passwordRules,
  password2: confirmPasswordRules(() => form.password),
  email: emailOptionalRules,
}

async function submitForm() {
  if (loading.value) return

  const inst = formRef.value
  if (!inst) {
    ElMessage.error('页面未就绪，请刷新后重试')
    return
  }

  try {
    await inst.validate()
  } catch {
    ElMessage.warning('请按提示修正表单内容')
    return
  }

  loading.value = true
  try {
    const res = await registerApi({
      username: form.username.trim(),
      password: form.password,
      email: form.email.trim() || undefined,
      role: registerRole.value,
    })
    setSession(res.access_token, res.user)
    await syncLearningProgressAfterAuth()
    ElMessage.success('注册成功')

    if (res.user.role === 'teacher') {
      await router.replace({ name: 'teacher-dashboard' })
    } else {
      const redir = route.query.redirect as string | undefined
      if (redir && redir.startsWith('/') && !(await needsOnboarding())) {
        await router.replace(redir)
      } else if (await needsOnboarding()) {
        await router.replace({ name: 'learning-path', query: { onboarding: '1' } })
      } else {
        await router.replace('/')
      }
    }
  } catch {
    /* axios 拦截器 */
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthPageFrame variant="register">
    <div class="auth-card">
      <span class="auth-card-kicker">Sign Up</span>
      <h2 class="auth-card-title">创建账号</h2>
      <p class="auth-card-sub">注册后即可在数组、链表等模块中自动同步小节完成进度。</p>

      <div class="role-switch">
        <button
          type="button"
          class="role-btn"
          :class="{ active: registerRole === 'student' }"
          @click="registerRole = 'student'"
        >
          <el-icon :size="16"><User /></el-icon>
          学生注册
        </button>
        <button
          type="button"
          class="role-btn"
          :class="{ active: registerRole === 'teacher' }"
          @click="registerRole = 'teacher'"
        >
          <el-icon :size="16"><User /></el-icon>
          教师注册
        </button>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        require-asterisk-position="right"
        class="auth-form"
        @submit.prevent="submitForm"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            :prefix-icon="User"
            autocomplete="username"
            maxlength="64"
            size="large"
            placeholder="字母、数字、下划线，3–64 位"
            clearable
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            :prefix-icon="Lock"
            type="password"
            show-password
            autocomplete="new-password"
            maxlength="128"
            size="large"
            placeholder="至少 6 位"
            clearable
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="password2">
          <el-input
            v-model="form.password2"
            :prefix-icon="Lock"
            type="password"
            show-password
            autocomplete="new-password"
            maxlength="128"
            size="large"
            placeholder="再次输入密码"
            clearable
          />
        </el-form-item>
        <el-form-item label="邮箱（可选）" prop="email">
          <el-input
            v-model="form.email"
            :prefix-icon="Message"
            type="email"
            autocomplete="email"
            maxlength="255"
            size="large"
            placeholder="用于找回密码等扩展功能"
            clearable
            @keyup.enter="submitForm"
          />
        </el-form-item>
        <el-form-item class="btn-row">
          <el-button
            type="primary"
            native-type="button"
            size="large"
            class="submit"
            :loading="loading"
            round
            @click="submitForm"
          >
            {{ registerRole === 'teacher' ? '教师注册并登录' : '注册并登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-card-footer">
        <span class="muted">已有账号？</span>
        <router-link class="link" :to="{ name: 'login', query: route.query }">去登录</router-link>
        <span class="sep">·</span>
        <router-link class="link" :to="{ name: 'home' }">返回首页</router-link>
      </div>
    </div>
  </AuthPageFrame>
</template>

<style scoped>
.role-switch {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.role-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  background: transparent;
  color: var(--alp-color-muted);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition:
    border-color 0.2s,
    color 0.2s,
    background 0.2s;
}

.role-btn:hover {
  border-color: var(--alp-color-primary);
  color: var(--alp-color-primary);
}

.role-btn.active {
  border-color: var(--alp-color-primary);
  color: var(--alp-color-primary);
  background: var(--alp-color-primary-soft);
}
</style>
