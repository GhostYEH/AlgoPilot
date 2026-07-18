/**
 * 可视化调试 · steps[].vars 标准协议
 *
 * 每个变量快照 TraceVarSnapshot = { type, value, refs? }
 *
 * | type        | value 形状 | 说明 |
 * |-------------|-----------|------|
 * | none        | null      | 空 |
 * | int/float/bool/str | 标量 | 标量 |
 * | sequence    | unknown[] + view_hint | 线性 STL（vector/stack/queue/deque） |
 * | associative | {key,value}[] + view_hint | 关联 STL（map/set/unordered_*） |
 * | list        | number[]  | 一维数组（兼容） |
 * | matrix      | MatrixValue | 二维数组 / DP 表 |
 * | linked_list | LinkedListGraph | 链表（节点图，不展平） |
 * | node_ref    | { node, nodes } | 指向链表中某节点（curr/head） |
 * | tree        | TreeGraph | 二叉树节点图 |
 * | dict        | Record<string, unknown> | 字典 |
 * | other       | string    | 兜底 |
 *
 * changed: 本步相对上一步发生变化的变量名。
 * 矩阵单元格高亮由前端对比连续两步的 matrix.cells 计算。
 */

export type TraceVerdict = 'OK' | 'RE' | 'TLE' | 'CE'

export interface MatrixValue {
  rows: number
  cols: number
  cells: (number | string | null)[][]
}

export interface LinkedListNodeData {
  id: string
  val: number | string
  next: string | null
}

export interface LinkedListGraph {
  head: string | null
  nodes: Record<string, LinkedListNodeData>
}

export interface NodeRefValue {
  node: string | null
  nodes: Record<string, LinkedListNodeData>
}

export interface TreeNodeData {
  id: string
  val: number | string
  left: string | null
  right: string | null
}

export interface TreeGraph {
  root: string | null
  nodes: Record<string, TreeNodeData>
}

export type TraceVarValue =
  | null
  | boolean
  | number
  | string
  | number[]
  | MatrixValue
  | LinkedListGraph
  | NodeRefValue
  | TreeGraph
  | Record<string, unknown>

export interface TraceVarSnapshot {
  type: string
  value: TraceVarValue
  /** 线性/关联容器的 STL 形态提示（sequence / associative） */
  view_hint?: string
  /** 可选：标量指针变量指向的数组下标或链表 node id */
  refs?: Record<string, string | number>
}

export interface TraceStep {
  line: number
  vars: Record<string, TraceVarSnapshot>
  changed: string[]
}

export interface TraceNarrationLine {
  step_index: number
  /** 旁白正文（API 可能返回 narration 或 text） */
  text: string
  narration?: string
  /** AI 诊断：关键 bug 步，前端标红展示 */
  critical?: boolean
}

export interface StaticAuditRejection {
  status: 'rejected'
  agent: string
  reason: string
  findings?: Array<{ level: string; code: string; message: string; line?: number | null }>
}

export interface TraceResponse {
  verdict: TraceVerdict
  message: string
  user_line_count: number
  steps: TraceStep[]
  result_preview: string | null
  narrations?: TraceNarrationLine[]
  /** ASTAnalyzer 静态熔断时返回 */
  static_audit?: StaticAuditRejection | null
}

export interface AiEdgeCaseInfo {
  reason: string
  category: string
  input_preview: string
  expected_preview: string
  source: string
}

export interface AiComplexityReport {
  input_size_n: number
  total_steps: number
  meaningful_steps: number
  estimated_complexity: string
  report: string
  alternative_hint: string
  source: string
}

export interface AiGuidedHint {
  level: 1 | 2 | 3 | number
  title: string
  content: string
}

export interface AiGuidedDiagnosis {
  bug_step_index: number
  bug_line?: number | null
  title: string
  root_cause: string
  actual_state: string
  expected_state: string
  invariant: string
  observation_question: string
  hints: AiGuidedHint[]
  fix_direction: string
  verification: string
  confidence: 'high' | 'medium' | 'low'
  source: string
}

export interface SkillCardBrief {
  id: string
  name: string
  chapter_id?: string
  description?: string
}

export interface RecommendedResourceHint {
  resource_type: string
  topic?: string
  reason?: string
  chapter_id?: string
}

/** OJ Trace 智能辅导闭环载荷（可选，旧客户端可忽略） */
export interface OjTutoringPayload {
  course_id?: string
  chapter_id?: string
  skill_id?: string
  module_key?: string
  matched_skill?: SkillCardBrief | null
  error_pattern?: string
  error_pattern_label?: string
  bug_step_index?: number
  trace_summary?: string
  hint_level?: number
  layered_hints?: string[]
  recommended_resources?: RecommendedResourceHint[]
  memory_event_id?: number | null
  mastery_update_summary?: string
  path_adjustment_hint?: string
  /** 是否写入 StudentMemory */
  memory_recorded?: boolean
  /** 是否重算 Mastery 掌握度 */
  mastery_updated?: boolean
  /** 是否成功 patch 六维画像 */
  persona_updated?: boolean
  /** @deprecated 等价于 persona_updated，不代表 memory_recorded */
  profile_updated?: boolean
  persona_patch_summary?: string
  persona_patch_warning?: string
}

export interface AiDiagnoseResponse {
  edge_case: AiEdgeCaseInfo
  edge_verdict: string
  edge_message: string
  trace: TraceResponse
  complexity: AiComplexityReport
  summary: string
  diagnosis?: AiGuidedDiagnosis | null
  tutoring?: OjTutoringPayload | null
}

/** AI 轨迹诊断：定位 bug 起源步（POST /diagnose） */
export interface TraceBugDiagnoseResponse {
  bug_step_index: number
  diagnosis_title: string
  detailed_analysis: string
  source?: string
  error_type?: string
  error_type_label?: string
  why_failed?: string
  fix_suggestion?: string
  recommended_knowledge_points?: string[]
  intervention_suggestion?: string
  variable_evidence?: string[]
  tutoring?: OjTutoringPayload | null
}

export interface VarChangeItem {
  step_index: number
  line: number
  variable_name: string
  before: string
  after: string
}

export interface TraceStepBrief {
  step_index: number
  line: number
  changed_vars: string[]
  var_summary: Record<string, string>
  is_error_step: boolean
}

export interface TraceDiagnosisReport {
  error_type: string
  error_category: string
  error_category_label: string
  failed_test_point: string
  key_variable_changes: VarChangeItem[]
  error_step: TraceStepBrief | null
  possible_cause: string
  why_failed: string
  fix_suggestion: string
  recommended_knowledge_points: string[]
  intervention_suggestion: string
  learning_intervention_generated: boolean
  recommended_resources: RecommendedResourceHint[]
  path_rearrange_triggered: boolean
  trace_steps: TraceStepBrief[]
  source: string
  diagnosis_confidence: 'high' | 'medium' | 'low' | string
  evidence_summary: string
  trace_case_reproduced: boolean
  tutoring?: OjTutoringPayload | null
}
