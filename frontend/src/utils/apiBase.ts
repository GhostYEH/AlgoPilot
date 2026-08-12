/**
 * 开发环境默认走 Vite 代理 `/api`，避免直连失败；
 * 生产或显式配置时使用 VITE_API_BASE_URL；
 * 打包部署时前后端同源，使用相对路径。
 */
export function getApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '')
  if (fromEnv) return fromEnv
  // DEV 模式走 Vite 代理；生产/打包模式前后端同源，用相对路径
  if (import.meta.env.DEV) return ''
  return ''
}
