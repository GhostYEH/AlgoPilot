import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
} from 'axios'
import { ElMessage } from 'element-plus'

import router from '@/router'
import { ACCESS_TOKEN_KEY, USER_JSON_KEY } from '@/constants/authStorage'
import { clearRefs } from '@/stores/auth'
import { getApiBaseUrl } from '@/utils/apiBase'

/**
 * Axios 实例：统一 baseURL、拦截器
 * 对接：鉴权 Bearer、学习进度等
 */
const baseURL = getApiBaseUrl()

const service: AxiosInstance = axios.create({
  baseURL,
  // 默认 30s：覆盖大多数 DB 查询场景，避免与后端 LLM 90s 超时不匹配导致误判
  // 涉及 LLM 长任务的端点（画像同步、评估、路径重排、OJ 挣扎）应在调用处显式覆盖 timeout
  timeout: 30000,
})

service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const t = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (t) {
      config.headers.Authorization = `Bearer ${t}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

service.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => {
    const status = error?.response?.status as number | undefined
    const detail = error?.response?.data?.detail
    const path = router.currentRoute.value.path

    const formatDetail = (): string => {
      if (Array.isArray(detail)) {
        return (
          detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('；') || '请求失败'
        )
      }
      if (detail !== undefined && detail !== null) return String(detail)
      return error.message || '请求失败'
    }

    if (status === 401) {
      if (path === '/login' || path === '/register') {
        ElMessage.error({ message: formatDetail(), offset: 60 })
        return Promise.reject(error)
      }
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(USER_JSON_KEY)
      clearRefs()
      ElMessage.warning({ message: '登录已过期，请重新登录', offset: 60 })
      void router.replace({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
      return Promise.reject(error)
    }

    ElMessage.error({ message: formatDetail(), offset: 60 })
    return Promise.reject(error)
  },
)

export default service
