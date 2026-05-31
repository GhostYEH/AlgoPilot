import type { Component } from 'vue'
import {
  ChatDotRound,
  Cpu,
  Guide,
  Reading,
  Connection,
  Collection,
} from '@element-plus/icons-vue'

export type HelpTabId = 'guide' | 'faq' | 'competition'

export interface HelpQuickLink {
  key: string
  title: string
  desc: string
  icon: Component
  route: { name: string; query?: Record<string, string> }
}

export interface HelpGuideStep {
  step: number
  title: string
  desc: string
  route?: { name: string; query?: Record<string, string> }
  routeLabel?: string
}

export interface HelpFaqItem {
  id: string
  category: string
  question: string
  answer: string
}

export interface HelpCompetitionSection {
  title: string
  items: string[]
}

export const HELP_TABS: Array<{ id: HelpTabId; label: string }> = [
  { id: 'guide', label: '使用指南' },
  { id: 'faq', label: '常见问题' },
  { id: 'competition', label: '赛题说明' },
]

export const HELP_QUICK_LINKS: HelpQuickLink[] = [
  {
    key: 'path',
    title: '学习路径',
    desc: '按阶段规划 11 个算法模块，Agent 可自动重排顺序。',
    icon: Guide,
    route: { name: 'learning-path' },
  },
  {
    key: 'oj',
    title: '在线 OJ',
    desc: 'Python 3 / C++ 在线编写与判题，含代码追踪可视化。',
    icon: Cpu,
    route: { name: 'practice-list' },
  },
  {
    key: 'persona',
    title: '学习画像',
    desc: '对话式构建 6 维画像，驱动个性化资源与路径推荐。',
    icon: ChatDotRound,
    route: { name: 'my-learning', query: { tab: 'persona' } },
  },
  {
    key: 'agents',
    title: '多智能体',
    desc: '查看 Doc / Quiz / Code 等 Agent 协作流水线与 DAG 演示。',
    icon: Connection,
    route: { name: 'agent-workbench' },
  },
  {
    key: 'resources',
    title: '资源库',
    desc: '多智能体生成讲解文档、思维导图、题单与代码案例。',
    icon: Collection,
    route: { name: 'resources' },
  },
  {
    key: 'home',
    title: '算法地图',
    desc: '首页交互式知识地图，快速进入各模块学习与小游戏。',
    icon: Reading,
    route: { name: 'home' },
  },
]

export const HELP_GUIDE_STEPS: HelpGuideStep[] = [
  {
    step: 1,
    title: '注册并登录账号',
    desc: '在右上角完成注册 / 登录。登录后学习小节进度、游戏记录与收藏会同步至云端数据库，换设备也可继续学习。',
    route: { name: 'register' },
    routeLabel: '前往注册',
  },
  {
    step: 2,
    title: '构建学习画像',
    desc: '进入「我的学习 → 学习画像」，与学习画像 Agent 对话，描述你的专业背景、目标岗位与薄弱知识点。系统会自动提取 6 维画像并用于后续推荐。',
    route: { name: 'my-learning', query: { tab: 'persona' } },
    routeLabel: '打开学习画像',
  },
  {
    step: 3,
    title: '规划学习路径',
    desc: '在「学习路径」页查看 Agent 根据画像与模块完成度生成的推荐顺序。可一键规划或重新规划，也可从首页算法地图直接进入某个模块。',
    route: { name: 'learning-path' },
    routeLabel: '查看学习路径',
  },
  {
    step: 4,
    title: '按模块系统学习',
    desc: '每个模块包含讲解小节、动画演示、配套 OJ 题单与闯关小游戏。完成小节后进度自动累计，可在「我的学习」查看总进度与进行中模块。',
    route: { name: 'learn-array' },
    routeLabel: '从数组模块开始',
  },
  {
    step: 5,
    title: '在线刷题与代码追踪',
    desc: '在「在线 OJ」选择题目，支持 Python 3 / C++ 双语言提交。做题页提供数据结构提示、AI 助手与代码执行追踪可视化，帮助理解算法过程。',
    route: { name: 'practice-list' },
    routeLabel: '进入 OJ 题库',
  },
  {
    step: 6,
    title: '生成个性化资源',
    desc: '登录后在「资源库」输入主题与聚焦提示，多智能体流水线将协同生成讲解文档、思维导图、练习题单、拓展阅读、代码案例与视频脚本，并经过校验闭环后落库。',
    route: { name: 'resources' },
    routeLabel: '打开资源库',
  },
]

export const HELP_FAQ: HelpFaqItem[] = [
  {
    id: 'faq-login',
    category: '账号与同步',
    question: '不登录可以使用平台吗？',
    answer:
      '可以浏览首页、学习路径、模块讲解与 OJ 题库。登录后可云端保存小节进度、游戏记录、收藏与学习画像，并在「我的学习」中查看完整统计与同步状态。',
  },
  {
    id: 'faq-sync',
    category: '账号与同步',
    question: '学习进度如何同步？',
    answer:
      '登录后进入「我的学习」会自动拉取云端进度并合并本地数据。在各模块完成小节后进度实时写入本地，并在有网络时同步至后端数据库。',
  },
  {
    id: 'faq-persona',
    category: '多智能体',
    question: '学习画像 Agent 是做什么的？',
    answer:
      '通过自然语言对话提取你的知识基础、学习目标、认知风格、薄弱点、学习节奏、兴趣方向与偏好模态共 7 个维度。画像更新后可触发学习路径 Agent 重新排序推荐模块。',
  },
  {
    id: 'faq-path',
    category: '多智能体',
    question: '学习路径 Agent 如何推荐顺序？',
    answer:
      '综合你的画像维度、各模块完成度与阶段目标（基础结构 → 解题技巧 → 树与搜索 → 进阶算法），输出有序模块列表及每步推荐理由。可在学习路径页一键规划或重新规划。',
  },
  {
    id: 'faq-resources',
    category: '多智能体',
    question: '资源库中的内容是如何生成的？',
    answer:
      '编排层依次执行 BM25 知识检索 → 角色 Agent 生成 → ContentVerifierAgent 校验 → 安全过滤 → 落库。支持单类型生成或批量生成六种资源类型，生成过程可在工作流日志中查看。',
  },
  {
    id: 'faq-oj-lang',
    category: '在线 OJ',
    question: 'OJ 支持哪些编程语言？',
    answer: '当前支持 Python 3 与 C++ 在线编写与判题。题目与学习路径中的配套题单同步，部分题目提供代码执行追踪与数据结构可视化辅助理解。',
  },
  {
    id: 'faq-oj-offline',
    category: '在线 OJ',
    question: '判题失败或后端离线怎么办？',
    answer:
      '请确认后端服务已启动（默认 http://127.0.0.1:9000）。后端离线时仍可浏览离线题库与题目描述，但提交判题功能不可用。例行维护期间请提前保存代码。',
  },
  {
    id: 'faq-modules',
    category: '学习模块',
    question: '目前有哪些算法模块？',
    answer:
      '已上线 12 个模块：数组、链表、哈希表、字符串、双指针、栈与队列、二叉树、回溯、贪心、动态规划、单调栈、图论。每个模块含讲解、动画、OJ 题单与闯关小游戏。',
  },
  {
    id: 'faq-game',
    category: '学习模块',
    question: '模块小游戏有什么作用？',
    answer:
      '小游戏以互动方式巩固核心概念（如哈希开锁、双指针竞速、回溯迷宫等）。完成游戏可在「我的学习 → 游戏闯关」查看记录，部分模块完成游戏可解锁成就。',
  },
  {
    id: 'faq-env',
    category: '部署与环境',
    question: '如何本地启动完整环境？',
    answer:
      '后端：cd backend，激活虚拟环境后 uvicorn main:app --reload --port 9000。前端：cd frontend，npm install && npm run dev。也可在仓库根目录运行 start.bat 一键启动。需在 backend/.env 配置 JWT_SECRET 与 SPARK_API_PASSWORD 等。',
  },
]

export const HELP_COMPETITION: HelpCompetitionSection[] = [
  {
    title: '赛题背景',
    items: [
      '本项目面向「中国软件杯」A3 赛道 — 算法智能学习平台，主题为多智能体个性化学习系统。',
      '平台将大语言模型与多 Agent 编排结合，覆盖学习画像构建、路径规划、资源生成、内容校验与在线判题等完整链路。',
      '目标用户为算法初学者与面试备考者，提供从知识讲解到实战刷题的一站式体验。',
    ],
  },
  {
    title: '核心能力亮点',
    items: [
      '多智能体协同：DocAgent、MindMapAgent、QuizAgent、CodeAgent 等角色 Agent 分工协作，编排层统一调度。',
      '个性化学习路径：基于 6 维画像与模块进度动态重排推荐顺序，而非固定课表。',
      'RAG + 校验闭环：BM25 检索知识库切片，ContentVerifierAgent 校验生成内容后再落库发布。',
      '可视化学习体验：算法动画、代码执行追踪、模块闯关小游戏与交互式知识地图。',
      '在线 OJ 判题：Python / C++ 双语言支持，题目与学习路径深度联动。',
    ],
  },
  {
    title: '技术架构概览',
    items: [
      '前端：Vue 3 + TypeScript + Vite + Element Plus，暗色 IDE 风格 UI。',
      '后端：FastAPI + SQLAlchemy + MySQL，JWT 鉴权，SiliconFlow 大模型接入。',
      '智能体层：Orchestrator 编排 DAG，支持流式资源生成与协作日志追踪。',
      '判题层：独立 OJ 服务，支持多语言沙箱执行与测试用例比对。',
    ],
  },
  {
    title: '评审与演示建议',
    items: [
      '建议演示路径：注册登录 → 构建画像 → 规划路径 → 进入模块学习 → OJ 刷题 → 资源库生成 → 多智能体工作台 DAG 演示。',
      '重点展示 Agent 协作流水线各阶段输入/输出，以及画像变化对学习路径推荐的影响。',
      '可在首页查看学习热力图、技能雷达与平台统计等数据可视化面板。',
    ],
  },
]

export const FAQ_CATEGORIES = [...new Set(HELP_FAQ.map((item) => item.category))]

export function faqByCategory(category: string): HelpFaqItem[] {
  return HELP_FAQ.filter((item) => item.category === category)
}
