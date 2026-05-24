import type { FormItemRule } from 'element-plus'

export const usernameRules: FormItemRule[] = [
  { required: true, message: '请输入用户名', trigger: 'blur' },
  { min: 3, max: 64, message: '用户名为 3–64 个字符', trigger: 'blur' },
  {
    pattern: /^[a-zA-Z0-9_]+$/,
    message: '仅支持英文字母、数字与下划线',
    trigger: 'blur',
  },
]

export const passwordRules: FormItemRule[] = [
  { required: true, message: '请输入密码', trigger: 'blur' },
  { min: 6, max: 128, message: '密码长度为 6–128 位', trigger: 'blur' },
]

export function confirmPasswordRules(getPassword: () => string): FormItemRule[] {
  return [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== getPassword()) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ]
}

export const emailOptionalRules: FormItemRule[] = [
  {
    validator: (_rule, value, callback) => {
      const v = typeof value === 'string' ? value.trim() : ''
      if (!v) {
        callback()
        return
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
        callback(new Error('邮箱格式不正确'))
        return
      }
      callback()
    },
    trigger: 'blur',
  },
]
