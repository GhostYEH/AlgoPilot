<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { Lock, User, Lightning } from '@element-plus/icons-vue'

import AuthPageFrame from '@/components/auth/AuthPageFrame.vue'
import { loginApi } from '@/api/auth'
import { passwordRules, usernameRules } from '@/utils/authFormRules'
import { setSession, syncLearningProgressAfterAuth } from '@/stores/auth'
import { needsOnboarding } from '@/composables/usePersonaGate'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const loginRole = ref<'student' | 'teacher'>('student')

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: usernameRules,
  password: passwordRules,
}

async function finishLogin(user: { role: string }) {
  if (user.role === 'teacher') {
    await router.replace({ name: 'teacher-dashboard' })
    return
  }

  const redirect = route.query.redirect as string | undefined
  const shouldOnboard = await needsOnboarding()
  if (redirect?.startsWith('/') && !shouldOnboard) {
    await router.replace(redirect)
  } else if (shouldOnboard) {
    await router.replace({ name: 'learning-path', query: { onboarding: '1' } })
  } else {
    await router.replace('/')
  }
}

async function authenticate(username: string, password: string, successMessage: string) {
  const res = await loginApi({ username, password, role: loginRole.value })
  setSession(res.access_token, res.user)
  await syncLearningProgressAfterAuth()
  ElMessage.success({ message: successMessage, offset: 60 })
  await finishLogin(res.user)
}

async function submitForm() {
  if (loading.value) return

  const instance = formRef.value
  if (!instance) {
    ElMessage.error({ message: '页面尚未准备好，请刷新后重试', offset: 60 })
    return
  }

  try {
    await instance.validate()
  } catch {
    ElMessage.warning({ message: '请检查用户名和密码', offset: 60 })
    return
  }

  loading.value = true
  try {
    await authenticate(form.username.trim(), form.password, '登录成功')
  } catch {
    // 登录错误由 axios 拦截器统一提示。
  } finally {
    loading.value = false
  }
}

async function loginAsDemo() {
  if (loading.value) return

  const demoUsername = loginRole.value === 'teacher' ? 'teacher_demo' : 'demo'
  loading.value = true
  try {
    await authenticate(demoUsername, '123456', '已使用测试账号登录')
  } catch {
    // 登录错误由 axios 拦截器统一提示。
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthPageFrame variant="login">
    <div class="auth-card">
      <div class="auth-heading">
        <h2 class="auth-card-title">欢迎回来</h2>
        <p class="auth-card-sub">选择身份并登录，继续你的学习进度。</p>
      </div>

      <div class="role-switch" role="group" aria-label="选择登录身份">
        <button
          type="button"
          class="role-btn"
          :class="{ active: loginRole === 'student' }"
          :aria-pressed="loginRole === 'student'"
          :disabled="loading"
          @click="loginRole = 'student'"
        >
          学生
        </button>
        <button
          type="button"
          class="role-btn"
          :class="{ active: loginRole === 'teacher' }"
          :aria-pressed="loginRole === 'teacher'"
          :disabled="loading"
          @click="loginRole = 'teacher'"
        >
          教师
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
            placeholder="请输入用户名"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            :prefix-icon="Lock"
            type="password"
            show-password
            autocomplete="current-password"
            maxlength="128"
            size="large"
            placeholder="请输入密码"
            clearable
          />
        </el-form-item>

        <el-form-item class="btn-row">
          <el-button
            type="primary"
            native-type="submit"
            size="large"
            class="submit"
            :loading="loading"
          >
            {{ loginRole === 'teacher' ? '教师登录' : '学生登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="secondary-action">
        <div class="action-divider"><span>或</span></div>
        <button type="button" class="demo-btn" :disabled="loading" @click="loginAsDemo">
          <el-icon :size="16"><Lightning /></el-icon>
          测试账号一键登录
        </button>
        <p class="demo-hint">
          {{ loginRole === 'teacher' ? 'teacher_demo' : 'demo' }} / 123456
        </p>
      </div>

      <div class="auth-card-footer">
        <span class="muted">还没有账号？</span>
        <router-link class="link" :to="{ name: 'register', query: route.query }">立即注册</router-link>
      </div>
    </div>
  </AuthPageFrame>
</template>

<style scoped>
.auth-heading {
  margin-bottom: 28px;
}

.role-switch {
  display: flex;
  gap: 4px;
  margin-bottom: 26px;
  padding: 4px;
  border-radius: 10px;
  background: #f0f4f2;
}

.role-btn {
  flex: 1;
  min-height: 40px;
  border: 0;
  border-radius: 7px;
  color: #60706b;
  background: transparent;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: color 160ms ease, background-color 160ms ease, box-shadow 160ms ease;
}

.role-btn:hover:not(:disabled) {
  color: #2e6b62;
}

.role-btn.active {
  color: #204f48;
  background: #fff;
  box-shadow: 0 1px 3px rgba(21, 33, 30, 0.1);
}

.role-btn:disabled {
  cursor: wait;
  opacity: 0.65;
}

.role-btn:focus-visible,
.demo-btn:focus-visible {
  outline: 2px solid #2e6b62;
  outline-offset: 2px;
}

.secondary-action {
  margin-top: 22px;
  text-align: center;
}

.action-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  color: #7b8884;
  font-size: 12px;
}

.action-divider::before,
.action-divider::after {
  content: '';
  height: 1px;
  flex: 1;
  background: #e0e6e3;
}

.demo-btn {
  width: 100%;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 16px;
  border: 1px solid #b9cbc5;
  border-radius: 9px;
  color: #285e56;
  background: #f6faf8;
  font: inherit;
  font-size: 14px;
  font-weight: 650;
  cursor: pointer;
  transition: border-color 160ms ease, background-color 160ms ease;
}

.demo-btn:hover:not(:disabled) {
  border-color: #2e6b62;
  background: #edf5f2;
}

.demo-btn:disabled {
  cursor: wait;
  opacity: 0.6;
}

.demo-hint {
  margin: 8px 0 0;
  color: #71807b;
  font-family: var(--alp-font-mono);
  font-size: 12px;
}

@media (prefers-reduced-motion: reduce) {
  .role-btn,
  .demo-btn {
    transition: none;
  }
}
</style>
