/** A3 比赛演示页 — 静态文案与 fallback 数据 */

export const A3_POSITIONING =
  'AlgoPilot：面向高校《数据结构与算法》课程的个性化多模态学习资源生成与多智能体协同学习系统'

export const A3_SUBTITLE =
  '六维画像驱动 · 可信资源生成 · OJ Trace 诊断 · 学习路径自适应闭环'

export const A3_FEATURES = [
  {
    key: 'persona',
    title: '对话式画像',
    desc: 'ProfilingAgent 六维动态学生画像，随学随新',
    icon: '⏳',
    done: true,
  },
  {
    key: 'resources',
    title: '多智能体资源生成',
    desc: '8 类多模态资源 · RAG → 生成 ⇄ 校验闭环',
    icon: '⚙️',
    done: true,
  },
  {
    key: 'path',
    title: '个性化路径规划',
    desc: 'LearningPathAgent DAG 拓扑 + 掌握度动态调整',
    icon: '💡',
    done: true,
  },
  {
    key: 'tutor',
    title: '智能辅导',
    desc: 'TutorAgent / OJ 诊断 / Trace 可视化调试',
    icon: '🎓',
    done: true,
  },
  {
    key: 'mastery',
    title: '学习效果评估',
    desc: 'MasteryAgent 可解释掌握度 + 薄弱技能',
    icon: '📈',
    done: true,
  },
  {
    key: 'safety',
    title: '防幻觉与安全过滤',
    desc: 'ContentVerifier + SafetyAgent 结构化证据链',
    icon: '🛡️',
    done: true,
  },
] as const

export interface A3DemoStep {
  key: string
  title: string
  desc: string
  icon: string
  route: Record<string, unknown>
}

export const A3_DEMO_STEPS: A3DemoStep[] = [
  {
    key: 'persona',
    title: '对话画像',
    desc: '破冰对话 · 六维画像抽取',
    icon: '⏳',
    route: { name: 'learning-path', query: { onboarding: '1' } },
  },
  {
    key: 'path',
    title: 'DAG 路径',
    desc: 'PlannerAgent · 先修 DAG 排序',
    icon: '💡',
    route: { name: 'learning-path' },
  },
  {
    key: 'resource',
    title: '多 Agent 资源',
    desc: 'generate-all · 8 类资源并行',
    icon: '⚙️',
    route: { name: 'agent-workbench' },
  },
  {
    key: 'oj',
    title: 'OJ Trace',
    desc: 'AST 静态扫描 + 轨迹破案',
    icon: '🔬',
    route: { name: 'practice-list' },
  },
  {
    key: 'eval',
    title: '学习评估',
    desc: 'MasteryAgent · 掌握度证据链',
    icon: '📈',
    route: { name: 'my-learning', query: { tab: 'evaluation' } },
  },
  {
    key: 'replan',
    title: '路径重排',
    desc: '受挫降级 · 巩固节点插入',
    icon: '🔄',
    route: { name: 'learning-path' },
  },
]

/** Agent 工作台 catalog 加载失败时的静态 Pipeline */
export const DEMO_RESOURCE_PIPELINE = [
  { stage: 'retrieve', agent: 'KnowledgeRetriever', label: '课程知识库检索' },
  { stage: 'generate', agent: 'ConceptAgent', label: '概念讲解生成' },
  { stage: 'verify', agent: 'ContentVerifierAgent', label: '防幻觉校验' },
  { stage: 'safety', agent: 'SafetyAgent', label: '内容安全审查' },
  { stage: 'persist', agent: 'Orchestrator', label: '资源落库' },
] as const

export interface A3ShowcaseAgent {
  id: string
  role: string
  layer: string
  resourceType?: string
  status?: 'idle' | 'running' | 'done' | 'error'
  recentLog?: string
}

export const A3_SHOWCASE_AGENTS: A3ShowcaseAgent[] = [
  { id: 'ConceptAgent', role: '概念讲解文档', layer: 'resource', resourceType: 'document', status: 'done', recentLog: '链表概念文档已生成，校验通过' },
  { id: 'GraphAgent', role: '知识思维导图', layer: 'resource', resourceType: 'mindmap', status: 'done', recentLog: '树与二叉树思维导图已生成' },
  { id: 'QuizAgent', role: '个性化题单', layer: 'resource', resourceType: 'exercises', status: 'done', recentLog: '3 道精练题已组卷' },
  { id: 'ScenarioAgent', role: '剧本沙盒', layer: 'resource', resourceType: 'code_case', status: 'done', recentLog: '双域分离沙盒已生成' },
  { id: 'TraceAgent', role: '执行轨迹动画', layer: 'resource', resourceType: 'trace_animation', status: 'done', recentLog: '轨迹录制完成，12 步' },
  { id: 'ReadingAgent', role: '分层阅读', layer: 'resource', resourceType: 'reading', status: 'done', recentLog: '三层阅读材料已策展' },
]

export const A3_ALL_AGENTS: A3ShowcaseAgent[] = [
  { id: 'ProfilingAgent', role: '六维动态画像', layer: 'profiling', status: 'done', recentLog: '画像已同步，置信度 0.82' },
  { id: 'LearningPathAgent', role: 'DAG 路径规划', layer: 'path', status: 'done', recentLog: '路径已调整，插入巩固节点' },
  { id: 'KnowledgeRetriever', role: 'BM25 课程知识库', layer: 'safety', status: 'done', recentLog: '命中 5 条知识库切片' },
  { id: 'SkillRouter', role: 'SkillCard 路由', layer: 'eval', status: 'done', recentLog: '匹配 SkillCard: linked-list-pointer' },
  { id: 'ContentVerifierAgent', role: '防幻觉校验', layer: 'safety', status: 'done', recentLog: '校验通过，引用 3 条证据' },
  { id: 'SafetyAgent', role: '内容安全审查', layer: 'safety', status: 'done', recentLog: '安全审查通过，无敏感词' },
  { id: 'MasteryAgent', role: '掌握度评估', layer: 'eval', status: 'done', recentLog: '掌握度 62 · improving' },
  { id: 'StudentMemory', role: '学习记忆', layer: 'memory', status: 'done', recentLog: '错因已记录，画像已 patch' },
  ...A3_SHOWCASE_AGENTS,
]

/** 《数据结构与算法》章节卡片（与课程知识库 manifest 对齐） */
export const A3_COURSE_CHAPTERS = [
  { id: 'ch01-introduction-complexity', title: '绪论与复杂度分析', difficulty: '入门' },
  { id: 'ch02-linear-list', title: '线性表', difficulty: '入门' },
  { id: 'ch03-stack-queue', title: '栈与队列', difficulty: '入门' },
  { id: 'ch04-string', title: '字符串', difficulty: '入门' },
  { id: 'ch05-tree-binary-tree', title: '树与二叉树', difficulty: '标准' },
  { id: 'ch06-graph', title: '图论', difficulty: '标准' },
  { id: 'ch07-search', title: '查找', difficulty: '标准' },
  { id: 'ch10-greedy', title: '贪心', difficulty: '进阶' },
  { id: 'ch11-dynamic-programming', title: '动态规划', difficulty: '进阶' },
  { id: 'ch12-backtracking', title: '回溯', difficulty: '进阶' },
  { id: 'ch13-heap-union-find', title: '堆与并查集', difficulty: '进阶' },
  { id: 'ch14-comprehensive-project', title: '综合项目', difficulty: '综合' },
] as const

export const MOCK_VERIFICATION_SUMMARY = {
  passed: 6,
  warning: 1,
  failed: 0,
  evidenceTotal: 24,
  riskLabel: '无风险',
  skipReason: '',
}

export interface PersonaDimensionScore {
  key: string
  label: string
  score: number
  confidence: 'low' | 'medium' | 'high'
}

export const MOCK_PERSONA_DIMENSIONS: PersonaDimensionScore[] = [
  { key: 'knowledge_base', label: '知识基础', score: 72, confidence: 'high' },
  { key: 'cognitive_style', label: '认知风格', score: 85, confidence: 'high' },
  { key: 'coding_ability', label: '代码实操', score: 45, confidence: 'medium' },
  { key: 'learning_goals', label: '学习目标', score: 90, confidence: 'high' },
  { key: 'error_preference', label: '易错点偏好', score: 55, confidence: 'medium' },
  { key: 'grit_level', label: '抗挫折心理', score: 60, confidence: 'low' },
]

export const MOCK_PERSONA_OVERALL_CONFIDENCE = 0.82

export interface OjTraceDemoData {
  problemTitle: string
  problemSlug: string
  errorCode: string
  language: string
  verdict: string
  errorType: string
  failedCase: string
  traceSteps: Array<{ line: number; desc: string; isBug: boolean }>
  aiDiagnosis: string
  suggestedFix: string
}

export const MOCK_OJ_TRACE: OjTraceDemoData = {
  problemTitle: '反转链表',
  problemSlug: 'reverse-linked-list',
  errorCode: `class Solution:
    def reverseList(self, head):
        prev = None
        curr = head
        while curr:
            curr.next = prev
            prev = curr
            curr = curr.next  # Bug: curr 已被修改
        return prev`,
  language: 'python',
  verdict: 'WA',
  errorType: '指针丢失',
  failedCase: '输入: [1,2,3,4,5] → 期望: [5,4,3,2,1] → 实际: [1]',
  traceSteps: [
    { line: 3, desc: 'prev = None, curr → 1', isBug: false },
    { line: 5, desc: 'curr.next 指向 prev (None)', isBug: false },
    { line: 6, desc: 'prev 移动到 curr (1)', isBug: false },
    { line: 7, desc: 'curr = curr.next → 但 curr.next 已被改为 None', isBug: true },
    { line: 4, desc: 'while 循环退出，curr = None', isBug: false },
    { line: 8, desc: 'return prev → 仅返回节点 1', isBug: false },
  ],
  aiDiagnosis: '第 7 行：在修改 curr.next 之前未保存 next 指针，导致链表断裂。应在修改前执行 next_temp = curr.next，循环末尾用 curr = next_temp 推进。',
  suggestedFix: '在 while 循环开头保存 next_temp = curr.next，修改指针后用 curr = next_temp 推进。',
}

export interface LearningEvalDemoData {
  overallScore: number
  level: string
  levelLabel: string
  trend: string
  trendLabel: string
  confidence: string
  dimensions: Array<{ key: string; label: string; score: number }>
  weakSkills: string[]
  pushStrategy: string
  pathAdjustment: string
  suggestedReplan: boolean
}

export const MOCK_LEARNING_EVAL: LearningEvalDemoData = {
  overallScore: 58,
  level: 'improving',
  levelLabel: '提升中',
  trend: 'rising',
  trendLabel: '上升',
  confidence: 'medium',
  dimensions: [
    { key: 'knowledge_retention', label: '知识留存', score: 65 },
    { key: 'problem_solving', label: '解题能力', score: 42 },
    { key: 'code_quality', label: '代码质量', score: 55 },
    { key: 'learning_velocity', label: '学习速度', score: 70 },
    { key: 'error_correction', label: '纠错能力', score: 38 },
    { key: 'transfer_ability', label: '迁移能力', score: 50 },
  ],
  weakSkills: ['链表指针操作', 'DP 状态设计', '递归边界处理'],
  pushStrategy: 'consolidate',
  pathAdjustment: '检测到链表章节连续 2 次 WA，建议插入巩固节点 ch02-linear-list-review，并推荐 TraceAgent 可视化调试资源',
  suggestedReplan: true,
}

export interface RecommendedResourceDemo {
  id: number
  title: string
  resourceType: string
  agentName: string
  chapterId: string
  reason: string
  verified: boolean
}

export const MOCK_RECOMMENDED_RESOURCES: RecommendedResourceDemo[] = [
  {
    id: 1,
    title: '链表指针操作 · 概念精讲',
    resourceType: 'document',
    agentName: 'ConceptAgent',
    chapterId: 'ch02-linear-list',
    reason: '画像显示代码实操能力偏弱(45分)，链表章节连续出错，需要强化指针操作理解',
    verified: true,
  },
  {
    id: 2,
    title: '反转链表 · 执行轨迹回放',
    resourceType: 'trace_animation',
    agentName: 'TraceAgent',
    chapterId: 'ch02-linear-list',
    reason: 'OJ Trace 诊断发现指针丢失错误，可视化调试可帮助理解指针变化过程',
    verified: true,
  },
  {
    id: 3,
    title: '动态规划 · 知识思维导图',
    resourceType: 'mindmap',
    agentName: 'GraphAgent',
    chapterId: 'ch11-dynamic-programming',
    reason: '画像显示 DP 刚入门，认知风格为视觉型，思维导图有助于构建知识框架',
    verified: true,
  },
  {
    id: 4,
    title: '栈与队列 · 个性化自测题',
    resourceType: 'exercises',
    agentName: 'QuizAgent',
    chapterId: 'ch03-stack-queue',
    reason: '学习路径显示栈与队列为下一章节，提前组卷帮助预习检测',
    verified: true,
  },
]
