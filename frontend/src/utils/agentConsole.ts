/** 将后端 SSE / agent_logs 事件转为终端友好文案 */

export type AgentLogStatus = 'pending' | 'running' | 'done' | 'error' | 'success' | 'warn'

export interface AgentConsoleLine {
  id: string
  icon: string
  agent: string
  message: string
  status: AgentLogStatus
  ts: number
  indent: number
}

let _seq = 0
export function nextLogId(): string {
  _seq += 1
  return `log-${Date.now()}-${_seq}`
}

export const AGENT_ICONS: Record<string, string> = {
  ProfilingAgent: '⏳',
  ConceptAgent: '⚙️',
  GraphAgent: '🎨',
  QuizAgent: '📝',
  ScenarioAgent: '🎭',
  TraceAgent: '🎬',
  DocAgent: '⚙️',
  MindMapAgent: '🎨',
  CodeAgent: '🎭',
  VideoAgent: '🎬',
  KnowledgeRetriever: '🔍',
  ContentVerifierAgent: '✅',
  ContentSafety: '🛡️',
  SafetyAgent: '🛡️',
  Orchestrator: '✨',
  System: '✨',
  LearningPathAgent: '💡',
  PlannerAgent: '💡',
  OjDiagnosisAgent: '🔬',
  EvaluationAgent: '🚑',
  EvaluatorAgent: '🚑',
}

const FRIENDLY_AGENT_MSG: Record<string, string> = {
  ProfilingAgent: '正在解析您的 6 维动态学情画像…',
  ConceptAgent: '正在流式铸造个性化 Markdown 算法视听教案…',
  GraphAgent: '正在拓扑化核心知识点并绘制 Mermaid 思维导图…',
  QuizAgent: '正在根据易错点偏好动态组卷（3 道精练题）…',
  ScenarioAgent: '正在编写代入感剧本并注入 // TODO 实操框架…',
  TraceAgent: '正在编译标准题解并注入 trace_runner 录制轨迹动画…',
  KnowledgeRetriever: 'BM25 检索课程知识库，对齐防幻觉切片…',
  ContentVerifierAgent: '对照知识库执行防幻觉校验闭环…',
  ContentSafety: '内容安全过滤与脱敏…',
  SafetyAgent: '内容安全审查：涉政敏感、学术幻觉、Prompt 注入…',
  LearningPathAgent: '评估薄弱点后正在重构学习路径…',
  PlannerAgent: '评估完成：检测到薄弱点，正在重构学习路径…',
  OjDiagnosisAgent: '边界测例 → 判题 → 轨迹诊断并发分析中…',
  EvaluationAgent: '学情评估：监测连续作答失败并联动路径降级…',
  EvaluatorAgent: '学情评估：监测连续作答失败并联动路径降级…',
}

export function iconForAgent(agent: string): string {
  if (AGENT_ICONS[agent]) return AGENT_ICONS[agent]
  for (const [key, icon] of Object.entries(AGENT_ICONS)) {
    if (agent.includes(key.replace('Agent', ''))) return icon
  }
  return '🤖'
}

export function friendlyAgentMessage(agent: string, fallback?: string): string {
  return FRIENDLY_AGENT_MSG[agent] ?? fallback ?? `${agent} 协同工作中…`
}

export function lineFromWorkflow(w: {
  stage: string
  agent: string
  status: string
  detail: string
}): AgentConsoleLine {
  const status = mapWorkflowStatus(w.status)
  const msg =
    w.detail ||
    (status === 'running'
      ? friendlyAgentMessage(w.agent, `${w.stage} 执行中…`)
      : `${w.stage} · ${w.status}`)
  return {
    id: nextLogId(),
    icon: iconForAgent(w.agent),
    agent: w.agent,
    message: `[${w.stage}] ${msg}`,
    status,
    ts: Date.now(),
    indent: w.agent === 'KnowledgeRetriever' ? 0 : 1,
  }
}

export function lineFromProgress(p: {
  step: number
  total: number
  resource_type: string
  agent_name: string
  label: string
  percent?: number
}): AgentConsoleLine {
  return {
    id: nextLogId(),
    icon: iconForAgent(p.agent_name),
    agent: p.agent_name,
    message: friendlyAgentMessage(
      p.agent_name,
      `[${p.step}/${p.total}] ${p.label}（${p.resource_type}）`,
    ),
    status: 'running',
    ts: Date.now(),
    indent: 1,
  }
}

export function lineFromCollaboration(row: {
  agent: string
  action: string
  detail: string
  role?: string
  status?: string
}): AgentConsoleLine {
  return {
    id: nextLogId(),
    icon: iconForAgent(row.agent),
    agent: row.agent,
    message: `${row.action}${row.detail ? ` → ${row.detail}` : ''}`,
    status: row.status === 'warn' || row.status === 'retry' ? 'warn' : 'done',
    ts: Date.now(),
    indent: 2,
  }
}

export function lineFromAgentLog(entry: {
  agent: string
  role?: string
  action: string
  detail?: string
  status?: string
}): AgentConsoleLine {
  return {
    id: nextLogId(),
    icon: iconForAgent(entry.agent),
    agent: entry.agent,
    message: entry.detail ? `${entry.action} · ${entry.detail}` : entry.action,
    status: mapWorkflowStatus(entry.status ?? 'done'),
    ts: Date.now(),
    indent: entry.agent === 'KnowledgeRetriever' ? 0 : 1,
  }
}

export function systemLine(message: string, status: AgentLogStatus = 'success'): AgentConsoleLine {
  return {
    id: nextLogId(),
    icon: '✨',
    agent: 'System',
    message,
    status,
    ts: Date.now(),
    indent: 0,
  }
}

export function diagnosisBootstrapLines(): AgentConsoleLine[] {
  return [
    systemLine('AI 诊断管线已启动 — 多智能体协同模式', 'running'),
    {
      id: nextLogId(),
      icon: '⏳',
      agent: 'ProfilingAgent',
      message: '正在解析您的 6 维动态学情画像…',
      status: 'running',
      ts: Date.now(),
      indent: 0,
    },
    {
      id: nextLogId(),
      icon: '🔬',
      agent: 'OjDiagnosisAgent',
      message: 'generate_edge_case → 判题 → trace_runner 串行前置…',
      status: 'running',
      ts: Date.now(),
      indent: 1,
    },
  ]
}

export function linesFromAgentLogs(
  logs: Array<{ agent: string; action: string; detail?: string; status?: string }>,
): AgentConsoleLine[] {
  return logs.map((entry) => ({
    id: nextLogId(),
    icon: iconForAgent(entry.agent),
    agent: entry.agent,
    message: entry.detail ? `${entry.action} · ${entry.detail}` : entry.action,
    status: mapWorkflowStatus(entry.status ?? 'done'),
    ts: Date.now(),
    indent: entry.agent === 'EvaluationAgent' || entry.agent === 'EvaluatorAgent' ? 0 : 1,
  }))
}

function mapWorkflowStatus(status: string): AgentLogStatus {
  if (status === 'running' || status === 'retry') return 'running'
  if (status === 'error') return 'error'
  if (status === 'warn') return 'warn'
  if (status === 'skipped') return 'done'
  return 'done'
}

export function resourceBootstrapLines(topic: string): AgentConsoleLine[] {
  return [
    systemLine(`Orchestrator 已接收任务：「${topic}」`, 'running'),
    {
      id: nextLogId(),
      icon: '⏳',
      agent: 'ProfilingAgent',
      message: '正在解析您的 6 维动态学情画像…',
      status: 'done',
      ts: Date.now(),
      indent: 0,
    },
    {
      id: nextLogId(),
      icon: '💡',
      agent: 'PlannerAgent',
      message: '评估完成：结合 error_preference 与 learning_goals 调度五类资源 Agent…',
      status: 'running',
      ts: Date.now(),
      indent: 0,
    },
  ]
}

export const CORE_RESOURCE_TAB_META = [
  { key: 'document', label: '自适应教案', icon: '📘', agent: 'ConceptAgent' },
  { key: 'mindmap', label: '知识思维导图', icon: '🗺️', agent: 'GraphAgent' },
  { key: 'exercises', label: '个性化自测题', icon: '📝', agent: 'QuizAgent' },
  { key: 'code_case', label: '剧情实操沙盒', icon: '🎭', agent: 'ScenarioAgent' },
  { key: 'trace_animation', label: '执行轨迹回放', icon: '🎬', agent: 'TraceAgent' },
] as const
