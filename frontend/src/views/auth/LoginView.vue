<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'

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

async function submitForm() {
  if (loading.value) return

  const inst = formRef.value
  if (!inst) {
    ElMessage.error({ message: '页面未就绪，请刷新后重试', offset: 60 })
    return
  }

  try {
    await inst.validate()
  } catch {
    ElMessage.warning({ message: '请按提示修正用户名或密码', offset: 60 })
    return
  }

  loading.value = true
  try {
    const res = await loginApi({
      username: form.username.trim(),
      password: form.password,
      role: loginRole.value,
    })
    setSession(res.access_token, res.user)
    await syncLearningProgressAfterAuth()
    ElMessage.success({ message: '登录成功', offset: 60 })

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
    /* 错误由 axios 拦截器提示 */
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthPageFrame variant="login">
    <div class="auth-card">
      <span class="auth-card-kicker">Sign In</span>
      <h2 class="auth-card-title">登录账号</h2>
      <p class="auth-card-sub">使用账号登录后，学习进度会同步到服务端保存。</p>

      <div class="role-switch">
        <button
          type="button"
          class="role-btn"
          :class="{ active: loginRole === 'student' }"
          @click="loginRole = 'student'"
        >
          <el-icon :size="16"><User /></el-icon>
          学生登录
        </button>
        <button
          type="button"
          class="role-btn"
          :class="{ active: loginRole === 'teacher' }"
          @click="loginRole = 'teacher'"
        >
          <el-icon :size="16"><User /></el-icon>
          教师登录
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
            @keyup.enter="submitForm"
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
            placeholder="至少 6 位"
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
            {{ loginRole === 'teacher' ? '教师登录' : '学生登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-card-footer">
        <span class="muted">还没有账号？</span>
        <router-link class="link" :to="{ name: 'register', query: route.query }">立即注册</router-link>
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
