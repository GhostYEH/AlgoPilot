import request from '@/utils/request'

export interface UserInfo {
  id: number
  username: string
  email?: string | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

export function registerApi(data: {
  username: string
  password: string
  email?: string
}) {
  return request.post<unknown, TokenResponse>('/api/auth/register', data)
}

export function loginApi(data: { username: string; password: string }) {
  return request.post<unknown, TokenResponse>('/api/auth/login', data)
}
