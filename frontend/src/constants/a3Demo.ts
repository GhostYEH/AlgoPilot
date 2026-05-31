/** A3 比赛演示页 — 静态文案与 fallback 数据 */

export const A3_POSITIONING =
  'AlgoPilot：面向高校《数据结构与算法》课程的个性化多模态学习资源生成与多智能体协同学习系统'

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

export const A3_DEMO_STEPS = [
  {
    title: '构建学生画像',
    desc: '破冰对话 · 六维画像抽取',
    route: { name: 'learning-path' as const, query: { onboarding: '1' } },
  },
  {
    title: '生成学习路径',
    desc: 'PlannerAgent · 先修 DAG 排序',
    route: { name: 'learning-path' as const },
  },
  {
    title: '生成多模态资源',
    desc: 'generate-all · 8 类资源并行',
    route: { name: 'agent-workbench' as const },
  },
  {
    title: 'OJ 提交与 Trace 诊断',
    desc: 'AST 静态扫描 + 轨迹破案',
    route: { name: 'practice-list' as const },
  },
  {
    title: '学习效果评估',
    desc: 'MasteryAgent · 掌握度证据链',
    route: { name: 'my-learning' as const, query: { tab: 'evaluation' } },
  },
  {
    title: '动态调整路径',
    desc: '受挫降级 · 巩固节点插入',
    route: { name: 'learning-path' as const },
  },
] as const

/** Agent 工作台 catalog 加载失败时的静态 Pipeline */
export const DEMO_RESOURCE_PIPELINE = [
  { stage: 'retrieve', agent: 'KnowledgeRetriever', label: '课程知识库检索' },
  { stage: 'generate', agent: 'ConceptAgent', label: '概念讲解生成' },
  { stage: 'verify', agent: 'ContentVerifierAgent', label: '防幻觉校验' },
  { stage: 'safety', agent: 'SafetyAgent', label: '内容安全审查' },
  { stage: 'persist', agent: 'Orchestrator', label: '资源落库' },
] as const

export const A3_SHOWCASE_AGENTS = [
  { id: 'ProfilingAgent', role: '六维动态画像', layer: 'profiling' },
  { id: 'LearningPathAgent', role: 'DAG 路径规划', layer: 'path' },
  { id: 'KnowledgeRetriever', role: 'BM25 课程知识库', layer: 'safety' },
  { id: 'SkillRouter', role: 'SkillCard 路由', layer: 'eval' },
  { id: 'ConceptAgent', role: '概念讲解文档', layer: 'resource' },
  { id: 'QuizAgent', role: '个性化题单', layer: 'resource' },
  { id: 'TraceAgent', role: '执行轨迹动画', layer: 'resource' },
  { id: 'PptAgent', role: 'PPT 胶片预览', layer: 'resource' },
  { id: 'VideoScriptAgent', role: '短视频分镜', layer: 'resource' },
  { id: 'ContentVerifierAgent', role: '防幻觉校验', layer: 'safety' },
  { id: 'SafetyAgent', role: '内容安全审查', layer: 'safety' },
  { id: 'MasteryAgent', role: '掌握度评估', layer: 'eval' },
] as const

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
