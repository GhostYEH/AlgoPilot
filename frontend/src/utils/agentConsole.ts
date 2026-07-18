/** 将后端 SSE / agent_logs 事件转为终端友好文案 */

export type AgentLogStatus = 'pending' | 'running' | 'done' | 'error' | 'success' | 'warn'

export type LogTier = 'system' | 'agent' | 'detail'

export function inferLogTier(agent: string, status: string, message: string): LogTier {
  if (agent === 'System' || agent === 'Orchestrator') return 'system'
  if (status === 'running' || /BM25|检索|dispatch/i.test(message)) return 'detail'
  return 'agent'
}

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
  ScenarioAgent: '🎭',
  TraceAgent: '🎬',
  ReadingAgent: '📚',
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
  ASTAnalyzerAgent: '🔬',
  ASTAnalyzer: '🔬',
  OjDiagnosisAgent: '🔬',
  EvaluationAgent: '📊',
  EvaluatorAgent: '🚑',
  MasteryAgent: '📈',
  EventBus: '🔗',
  StudentMemory: '🧠',
  SkillRouter: '🎯',
}

const FRIENDLY_AGENT_MSG: Record<string, string> = {
  ProfilingAgent: '正在解析您的 6 维动态学情画像…',
  ConceptAgent: '正在分离业务域叙事与结构域学术剖析（Domain/Structure JSON）…',
  GraphAgent: '正在拓扑化核心知识点并绘制 Mermaid 思维导图…',
  ScenarioAgent: '正在编写业务域剧本 + 结构域 TODO 沙盒（双域分离）…',
  TraceAgent: '正在编译标准题解并注入 trace_runner 录制轨迹动画…',
  ReadingAgent: '正在策展基础、进阶、挑战三层拓展阅读材料…',
  KnowledgeRetriever: 'BM25 检索课程知识库，对齐防幻觉切片…',
  ContentVerifierAgent: '对照知识库执行防幻觉校验闭环…',
  ContentSafety: '内容安全过滤与脱敏…',
  SafetyAgent: '内容安全审查通过，未发现事实性幻觉，准许下发资源…',
  LearningPathAgent: '评估薄弱点后正在重构学习路径…',
  PlannerAgent: '评估完成：检测到薄弱点，正在重构学习路径…',
  ASTAnalyzerAgent:
    '静态抽象语法树扫描通过，未发现死循环特征，移交动态沙箱…',
  OjDiagnosisAgent: '边界测例 → 判题 → 轨迹诊断并发分析中…',
  EvaluatorAgent: '监测 OJ 连续失败并联动 Planner 插入降级巩固关卡…',
  EventBus: '学习事件总线：编排多智能体协同闭环…',
  MasteryAgent: '基于学习行为重算章节掌握度…',
  StudentMemory: '写入错因记忆，支撑画像随学随新…',
  SkillRouter: '根据错因模式推荐 SkillCard…',
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
  resource_type?: string
  agent_name?: string
  label?: string
  percent?: number
  parallel?: boolean
}): AgentConsoleLine {
  const agentName = p.agent_name || 'Orchestrator'
  const label = p.label || p.resource_type || '任务初始化'
  const tag = p.parallel ? ' [并行]' : ''
  return {
    id: nextLogId(),
    icon: iconForAgent(agentName),
    agent: agentName,
    message: friendlyAgentMessage(
      agentName,
      `[${p.step}/${p.total}] ${label}${p.resource_type ? `（${p.resource_type}）` : ''}${tag}`,
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

export function linesFromAgentLogs(
  logs: Array<{ agent: string; action: string; detail?: string; status?: string }>,
): AgentConsoleLine[] {
  return logs.map((entry) => lineFromAgentLog(entry))
}

export function linesFromEventLogs(
  logs: Array<{ agent: string; action: string; detail?: string; status?: string }>,
): AgentConsoleLine[] {
  return [
    systemLine('EventBus · 学习事件链已触发', 'running'),
    ...linesFromAgentLogs(logs),
  ]
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

export function astAnalyzerScanningLine(): AgentConsoleLine {
  return {
    id: nextLogId(),
    icon: '🔬',
    agent: 'ASTAnalyzerAgent',
    message: '正在执行静态抽象语法树扫描（死循环 / 越界 / 野指针）…',
    status: 'running',
    ts: Date.now(),
    indent: 0,
  }
}

export function astAnalyzerLine(passed: boolean, reason?: string): AgentConsoleLine {
  return {
    id: nextLogId(),
    icon: '🔬',
    agent: 'ASTAnalyzerAgent',
    message: passed
      ? '静态抽象语法树扫描通过，未发现死循环特征，移交动态沙箱…'
      : reason ?? '静态分析拦截：高风险代码已熔断',
    status: passed ? 'success' : 'error',
    ts: Date.now(),
    indent: 0,
  }
}

export function diagnosisBootstrapLines(): AgentConsoleLine[] {
  return [
    systemLine('AI 诊断管线已启动 — 多智能体协同模式', 'running'),
    astAnalyzerLine(true),
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

export function traceBootstrapLines(): AgentConsoleLine[] {
  return [
    systemLine('可视化调试管线 — 静动结合双轨诊断', 'running'),
    astAnalyzerScanningLine(),
  ]
}

function mapWorkflowStatus(status: string): AgentLogStatus {
  if (status === 'running' || status === 'retry') return 'running'
  if (status === 'error' || status === 'failed') return 'error'
  if (status === 'warn') return 'warn'
  if (status === 'success') return 'success'
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
      message: '评估完成：结合 error_preference 与 learning_goals 调度个性化资源 Agent…',
      status: 'running',
      ts: Date.now(),
      indent: 0,
    },
  ]
}

export const CORE_RESOURCE_TAB_META = [
  { key: 'document', label: '自适应学案', icon: '📘', agent: 'ConceptAgent' },
  { key: 'mindmap', label: '知识思维导图', icon: '🗺️', agent: 'GraphAgent' },
  { key: 'code_case', label: '剧情实操沙盒', icon: '🎭', agent: 'ScenarioAgent' },
  { key: 'trace_animation', label: '执行轨迹回放', icon: '🎬', agent: 'TraceAgent' },
  { key: 'reading', label: '分层拓展阅读', icon: '📚', agent: 'ReadingAgent' },
] as const
