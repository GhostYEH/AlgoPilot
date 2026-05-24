/**
 * 开发环境默认走 Vite 代理 `/api`，避免直连失败；
 * 生产或显式配置时使用 VITE_API_BASE_URL。
 */
export function getApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '')
  if (fromEnv) return fromEnv
  if (import.meta.env.DEV) return ''
  return 'http://127.0.0.1:9000'
}
