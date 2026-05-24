import { ElMessage } from 'element-plus'
import type { JudgeResponse, Verdict } from '@/api/oj'

const VERDICT_LABEL: Record<Verdict, string> = {
  AC: '通过',
  WA: '答案错误',
  TLE: '超时',
  RE: '运行错误',
  CE: '编译错误',
}

export function formatOjAxiosError(error: unknown): string {
  const e = error as {
    response?: { status?: number; data?: { detail?: unknown } }
    message?: string
    code?: string
  }
  const detail = e?.response?.data?.detail
  if (Array.isArray(detail)) {
    return (
      detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('；') || '判题请求失败'
    )
  }
  if (detail !== undefined && detail !== null) return String(detail)
  if (
    e?.code === 'ERR_NETWORK' ||
    e?.message?.includes('Network Error') ||
    e?.message?.includes('timeout')
  ) {
    return '判题服务未连接，请在 backend 目录启动：uvicorn main:app --port 9000'
  }
  return e?.message || '判题请求失败'
}

export function showJudgeResultMessage(result: JudgeResponse, mode: 'run' | 'submit') {
  if (result.verdict === 'AC') {
    ElMessage.success(mode === 'submit' ? '全部测例通过' : '样例全部通过')
    return
  }
  if (result.compile_error) {
    ElMessage.error(`编译错误：${result.compile_error.slice(0, 160)}`)
    return
  }
  ElMessage.warning(`${VERDICT_LABEL[result.verdict]}：${result.passed}/${result.total} 通过`)
}
