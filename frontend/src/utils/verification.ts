/** 资源校验证据 — 与后端 ResourceVerificationResult 对齐 */

export type VerifyStatus = 'passed' | 'warning' | 'failed'

export interface GroundedChunkRef {
  id: string
  title?: string
  snippet?: string
}

export interface ResourceVerification {
  resource_id?: number
  resource_type?: string
  course_id?: string
  chapter_id?: string
  verifier_status?: VerifyStatus
  safety_status?: VerifyStatus
  grounded_chunks?: GroundedChunkRef[]
  hallucination_risks?: string[]
  unsupported_claims?: string[]
  sensitive_risks?: string[]
  prompt_injection_risks?: string[]
  retry_count?: number
  skip_reason?: string
  final_decision?: 'publish' | 'draft' | 'blocked'
  risk_label?: string
  evidence_count?: number
  created_at?: string
}

export function getResourceVerification(meta: Record<string, unknown> | undefined): ResourceVerification | null {
  if (!meta) return null
  const v = meta.verification
  if (v && typeof v === 'object') return v as ResourceVerification
  const panel = meta.safety_panel as Record<string, unknown> | undefined
  if (panel?.verification && typeof panel.verification === 'object') {
    return panel.verification as ResourceVerification
  }
  return null
}

export function verificationDisplayTag(meta: Record<string, unknown>): {
  label: string
  type: 'success' | 'warning' | 'danger' | 'info'
  riskLabel: string
} {
  const v = getResourceVerification(meta)
  if (v?.risk_label) {
    const risk = v.risk_label
    if (risk === '无风险' || v.final_decision === 'publish') {
      return { label: '内容校验通过', type: 'success', riskLabel: risk }
    }
    if (v.final_decision === 'blocked' || v.safety_status === 'failed') {
      return { label: '安全审查未通过', type: 'danger', riskLabel: risk }
    }
    return { label: '内容校验告警', type: 'warning', riskLabel: risk }
  }
  if (meta?.verified === true || meta?.status === 'published') {
    return { label: '已校验', type: 'success', riskLabel: '无风险' }
  }
  if (meta?.status === 'draft') {
    return { label: '待校验', type: 'warning', riskLabel: '待复核' }
  }
  return { label: '未校验', type: 'info', riskLabel: '未校验' }
}
