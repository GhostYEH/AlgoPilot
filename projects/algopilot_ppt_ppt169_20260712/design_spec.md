# AlgoPilot - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | AlgoPilot（算法领航员） |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 24 |
| **Design Style** | 70% cool-corporate + 25% tech-neon (restrained) + 5% editorial |
| **Target Audience** | 软件杯评委（高校计算机教授、企业技术专家、教育行业评委） |
| **Use Case** | 比赛路演答辩 — 展示项目完整性、技术创新性、教育应用价值 |
| **Delivery Purpose** | `presentation` — 一页一观点，适合答辩路演节奏 |
| **Content Strategy** | balanced — 忠实呈现项目全貌，核心创新点重点展开 |
| **Created Date** | 2026-07-12 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top/bottom 50px |
| **Content Area** | 1160×620 |

---

## III. Visual Theme

### Theme Style

- **Mode**: narrative — 痛点驱动 → 方案递进 → 技术展开 → 价值收束
- **Visual style**: custom hybrid: cool-corporate dominant, restrained tech-neon accent, editorial whitespace
- **Theme**: Light theme (dark on light)
- **Tone**: Professional, technical, credible, innovative — enterprise AI product presentation

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F7F8FA` | Page background — cool off-white, calm breathing space |
| **Secondary bg** | `#EDF0F5` | Card background, section background |
| **Primary** | `#1B2A4A` | Title decorations, key sections, headers, navigation bars |
| **Accent** | `#2D7DD2` | Data highlights, key information, link text, icon fills |
| **Secondary accent** | `#4A9FE5` | Secondary emphasis, gradient transitions, chart secondary series |
| **Body text** | `#1E2024` | Main body text |
| **Secondary text** | `#6B7280` | Captions, annotations, footnotes |
| **Tertiary text** | `#9CA3AF` | Supplementary info, page numbers, footers |
| **Border/divider** | `#D1D5DB` | Card borders, divider lines |
| **Success** | `#10B981` | Positive indicators — test passed, mastery achieved |
| **Warning** | `#EF4444` | Error/issue markers — OJ failure, weak points |

### AI Image Strategy

- **Image Rendering**: `vector-illustration` — clean geometric shapes, flat fills, restrained
- **Image Palette**: `cool-corporate` — controlled, professional color behavior

### Gradient Strategy

- No full-canvas gradients
- Subtle linear gradient for section divider pages only (primary → secondary accent, horizontal, 5% opacity transition)
- Charts use solid fills only

---

## IV. Typography

| Category | Font | Weight | Size (px) | Color |
|----------|------|--------|-----------|-------|
| **Cover Title** | Source Han Sans SC (Bold) / Inter (Bold) | 700 | 52 | Primary `#1B2A4A` |
| **Cover Subtitle** | Source Han Sans SC (Medium) / Inter (Medium) | 500 | 26 | Secondary text `#6B7280` |
| **Section Title** | Source Han Sans SC (Bold) / Inter (Bold) | 700 | 36 | Primary `#1B2A4A` |
| **Page Title** | Source Han Sans SC (Medium) / Inter (Medium) | 500 | 28 | Primary `#1B2A4A` |
| **Subheading** | Source Han Sans SC (Medium) / Inter (Regular) | 500 | 20 | Body `#1E2024` |
| **Body** | Source Han Sans SC (Regular) / Inter (Regular) | 400 | 16 | Body `#1E2024` |
| **Caption** | Source Han Sans SC (Regular) / Inter (Regular) | 400 | 12 | Secondary text `#6B7280` |
| **Data Number** | Inter (Bold) | 700 | 40 | Accent `#2D7DD2` |
| **Code/Keyword** | JetBrains Mono (Regular) | 400 | 14 | Accent `#2D7DD2` |

**Formula Policy**: Use mathematical notation only when unavoidable (time complexity O(n log n)). Otherwise describe in plain text.

---

## V. Layout Patterns

| Pattern | Usage | Description |
|---------|-------|-------------|
| **L1 - Full-bleed hero** | Cover, section dividers | Title centered or anchored to left zone; large negative space on right |
| **L2 - Left-text right-visual** | Feature pages, architecture | 45% text left column + 55% diagram/icon right column |
| **L3 - Card grid (2×2)** | Feature detail, innovation points | Four evenly spaced cards with icon + title + 1-line description |
| **L4 - Three-column** | Comparative analysis, statistics | Equal thirds with numbers/headers |
| **L5 - Data hero** | Key metrics, test results | One oversized number + label, minimal surrounding text |
| **L6 - Timeline/flow** | Architecture, pipeline, learning loop | Horizontal flow with connecting arrow line; nodes as rounded rectangles |
| **L7 - Diagonal split** | Chapter dividers, transition pages | Background diagonal cut by primary color block (~35% Area) |

---

## VI. Icon Style

- **Style**: Line icons with solid fill on hover state
- **Stroke**: 2px consistent stroke width
- **Corner**: `rx="2"` rounded caps
- **Color**: Primary `#1B2A4A` by default, Accent `#2D7DD2` for active/emphasized
- **No gradients, no glow, no neon effects on icons**
- Source: built-in SVG icon library (search by keyword)

---

## VII. Visualization Reference List

| Type | Usage |
|------|-------|
| **Bar chart** | Test pass rates, comparison data |
| **Horizontal bars** | Skill mastery distribution |
| **DAG graph** | Learning path topology, Agent orchestration flow |
| **Mind map** | Knowledge structure display |
| **Pipeline flow** | Multi-agent generation pipeline phases |
| **Number card** | Key metrics (188 tests, 22 agents, etc.) |
| **Table** | Feature comparison, architecture layers |
| **Timeline** | Development phases |
| **Radial/circular** | Learning loop illustration |

---

## VIII. Image Resource List

| Page | Role | Description | Style |
|------|------|-------------|-------|
| 01_cover | hero_page | Abstract geometric AI-brain + data flow visualization; deep navy background, one electric blue accent line. NOT a literal brain — interconnected nodes suggesting algorithm + intelligence. | vector-illustration, cool-corporate palette |
| 03_pain_points | local | Split visual: left side shows a confused student facing a wall of code; right side shows clarity/guidance. Muted colors, professional. | vector-illustration, cool-corporate palette |
| 05_solution_overview | hero_page | A pilot standing at a ship's helm, looking at a futuristic-but-clean dashboard showing data structures as abstract geometric islands. Metaphor of "navigation." | vector-illustration, cool-corporate + restrained tech-neon accent |
| 07_architecture | local | Clean three-layer stacked architecture diagram — frontend/api/agent-engine. No 3D, flat isometric blocks with connecting lines. | vector-illustration, cool-corporate palette |
| 11_core_features | local | Collage of 5 feature icons in a pentagon layout, connected by thin lines showing data flow between modules. | vector-illustration, cool-corporate palette |
| 16_safety | local | Shield/checkpoint illustration — layered defense rings, clean geometric, no combat metaphors. Three concentric layers with labeled checkpoints. | vector-illustration, cool-corporate palette |
| 18_innovation_1 | local | A branching tree where each branch splits into a labeled innovation — DAG orchestration / Trace / RAG verification. Metaphor of "growing from roots." | vector-illustration, cool-corporate palette |
| 20_value | local | Three figures (student / teacher / institution) connected by light beams to a central node. Collaborative ecosystem visual. | vector-illustration, cool-corporate palette |

---

## IX. Content Outline

### Part 1: Opening & Context

#### Slide 01 - Cover

- **Cover impact**: Hero number hook — "22 Agents" + "One Platform" as a bold dual statement. Full-bleed deep navy primary block occupying lower 40%, geometric AI node motif faintly in secondary bg. Title: "AlgoPilot 算法领航员" in white on navy block. Subtitle: "面向《数据结构与算法》的多智能体智能学习平台". Info bar bottom-right.
- **Layout**: L1 - Full-bleed hero with diagonal color block
- **Title**: AlgoPilot 算法领航员
- **Subtitle**: 面向《数据结构与算法》的多智能体智能学习平台
- **Info**: 软件杯 A3 赛题 · 2026

#### Slide 02 - Table of Contents

- **Layout**: L1 - Left-aligned list with right-side decorative number
- **Title**: 目录 Contents
- **Core message**: 六大篇章的结构预览
- **Content**:
  - 01 背景与痛点 / Background & Pain Points
  - 02 解决方案 / Solution Overview
  - 03 技术架构 / System Architecture
  - 04 核心功能 / Core Features
  - 05 创新亮点 / Innovation Highlights
  - 06 应用价值 / Application Value

---

### Part 2: Background & Pain Points

#### Slide 03 - 五大学习痛点

- **Layout**: L3 - Three column layout with left column being 2 stacked cards
- **Title**: 每个算法学习者都懂的五道坎
- **Core message**: 《数据结构与算法》五大典型痛点严重制约学习效果
- **Content**:
  - P1 概念抽象难懂 / 树图动态规划静态教材难以传达
  - P2 刷题盲目无方向 / 题海茫茫缺乏个性化路径
  - P3 错题不知为何错 / OJ只返回WA/TLE冰冷判定
  - P4 学习过程无记录 / 换设备一切归零
  - P5 教师难因材施教 / 大班授课无法掌握个体薄弱点
  - 数据角标: "公认最难啃的硬骨头" — 各大高校计算机专业调研

#### Slide 04 - 现有方案不足

- **Layout**: L4 - Three-column comparative
- **Title**: 为什么现有方案不够？
- **Core message**: 传统OJ/MOOC/通用AI助手各有明显短板
- **Visualization**: Table comparison
- **Content**:
  | 方案 | 不足 | 评价 |
  |------|------|------|
  | 传统 OJ（力扣/洛谷） | 只判对错，无诊断无路径 | ❌ |
  | MOOC 课程 | 单向输出，无个性化 | ❌ |
  | 通用 AI 助手 | 无课程约束，易幻觉 | ⚠️ |
  | 算法可视化网站 | 只能看预设，不能追踪自己代码 | ❌ |
  | **AlgoPilot（我们）** | **全流程智能闭环** | **✅** |

Rightmost column reserved for a highlighted "AlgoPilot wins" summary.

---

### Part 3: Solution Overview

#### Slide 05 - AlgoPilot 是什么

- **Cover impact**: Hero image of a navigator at the helm, with abstract data-structure islands ahead. Central assertion: "一个懂你、记你、陪你、纠你的全流程智能学习平台"
- **Layout**: L1 - Full-bleed hero
- **Title**: AlgoPilot 算法领航员
- **Core message**: 多智能体协同 + RAG 知识库 + 大语言模型 + 代码Trace可视化深度融合
- **Content**:
  - 一句话: AlgoPilot 面向《数据结构与算法》，提供对话式学生画像、个性化学习路径、多智能体资源生成、OJ判题与Trace可视化诊断、AI辅导与教师学情看板

#### Slide 06 - 核心学习闭环

- **Layout**: L6 - Timeline/flow - circular loop design
- **Title**: 从"不会"到"掌握"的智能闭环
- **Core message**: 六大环节形成完整学习闭环，持续迭代优化
- **Visualization**: Pipeline flow / Circular
- **Content**:
  对话式学生画像 → 个性化学习路径 → 多智能体资源生成 → OJ 与 Trace 诊断 → 掌握度评估 → 路径动态调整
  (Each step shown as a node in a circular flow, with arrow connections)

---

### Part 4: Technical Architecture

#### Slide 07 - 系统架构总览

- **Layout**: L2 - Left-text right-visual
- **Title**: 三层架构 + 多智能体编排
- **Core message**: 前后端分离 + 自研轻量DAG编排，零langgraph依赖
- **Visualization**: Three-layer stacked architecture
- **Content**:
  前端层: Vue 3 + TypeScript · 30+页面 · 70+组件
  API层: FastAPI · 16路由 · JWT鉴权
  编排与Agent层: 自研DAG · 22 Agent注册 · 6 Layer
  RAG/知识层: BM25检索 · 课程Markdown切分
  OJ/安全层: Python/C++双语言 · AST审计 · 三重防幻觉
  数据层: SQLAlchemy 2.0 · 7表外键关联

#### Slide 08 - 多智能体系统

- **Layout**: L3 - Three-column by Layer groups
- **Title**: 22个智能体 · 6层协作
- **Core message**: 6大Layer各司其职，端到端覆盖学习全流程
- **Visualization**: DAG graph
- **Content**:
  Layer 1 画像层: ProfilingAgent, PersonaInitAgent
  Layer 2 资源层: ConceptAgent, GraphAgent, QuizAgent, ScenarioAgent, TraceAgent, ReadingAgent
  Layer 3 路径层: LearningPathAgent
  Layer 4 辅导层: AiTutorAgent, CodeReviewAgent, HintAgent, MisconceptionAgent
  Layer 5 安全层: ContentVerifierAgent, SafetyAgent, ASTAnalyzerAgent
  Layer 6 评估层: MasteryEvalAgent, LearningEventAgent, TeacherDashboardAgent

#### Slide 09 - 资源生成四阶段并行拓扑

- **Layout**: L6 - Timeline/flow
- **Title**: 四阶段并行生成，效率翻倍
- **Core message**: 串行依赖 → 并行拓扑，大幅提升资源生成效率
- **Visualization**: Pipeline flow with parallel branches
- **Content**:
  Phase 1: document (ConceptAgent) → 串行入口
  Phase 2: mindmap ∥ exercises (GraphAgent ∥ QuizAgent) → 并行
  Phase 3: code_case (ScenarioAgent) → 串行依赖
  Phase 4: trace_animation ∥ reading (TraceAgent ∥ ReadingAgent) → 并行

---

### Part 5: Core Features

#### Slide 10 - 六维学生画像

- **Layout**: L2 - Left-text right-visual
- **Title**: 懂你：对话式六维画像
- **Core message**: 3-5轮对话精准构建六维学生画像，无需问卷
- **Visualization**: Radial - 6 dimensions around a center
- **Content**:
  编程基础 | 语言偏好 | 数据结构掌握度 | 学习目标 | 学习风格 | 薄弱知识点
  每次对话更新画像，路径随之动态调整

#### Slide 11 - 个性化学习路径

- **Layout**: L2 - Left-text right-visual
- **Title**: 记你：动态学习路径DAG
- **Core message**: DAG可视化呈现知识点依赖关系，受挫自动插入巩固节点
- **Visualization**: DAG graph
- **Content**:
  - 基于画像生成个性化路径
  - 知识点DAG可视化，可拖动交互
  - 受挫自动插入巩固节点
  - 掌握度达阈值自动推进

#### Slide 12 - 六种智能资源

- **Layout**: L3 - Card grid (2×3)
- **Title**: 陪你：六种覆盖全场景学习资源
- **Core message**: 6种资源类型覆盖"理解→结构化→练习→实践→调试→拓展"全链路
- **Content**:
  ① 讲解文档 / ConceptAgent / 个性化课程讲解
  ② 思维导图 / GraphAgent / Mermaid知识结构化
  ③ 分层练习题 / QuizAgent / Bloom认知分层
  ④ 代码案例 / ScenarioAgent / 交互式代码沙盒
  ⑤ Trace动画 / TraceAgent / 13种可视化类型
  ⑥ 拓展阅读 / ReadingAgent / 分层推荐

#### Slide 13 - 在线 OJ 系统

- **Layout**: L2 - Left-text right-visual
- **Title**: 纠你：在线OJ + 代码诊断
- **Core message**: Python/C++双语言判题，AST静态审计提前熔断危险代码
- **Visualization**: Screenshot-like mockup of OJ interface
- **Content**:
  - Python + C++ 双语言支持
  - AST静态审计: 死循环/数组越界检测
  - 子进程超时3秒硬上限
  - C++危险调用拦截 (system/fork/exec)
  - 13种Trace可视化组件

#### Slide 14 - Trace 可视化诊断

- **Layout**: L2 - Left-text right-visual
- **Title**: 代码Trace可视化——看见每一步
- **Core message**: Python sys.settrace + C++ GDB MI，统一为13类可视化类型
- **Visualization**: Trace visualization element layout
- **Content**:
  Python Trace: sys.settrace 单步追踪变量变化
  C++ Trace: GDB MI单步追踪 + STL容器状态提取
  13种可视化类型: 变量追踪/调用栈/内存状态/链表结构...
  确定性旁白: 经典题目无LLM依赖，确保可复现

#### Slide 15 - AI 辅导与教师看板

- **Layout**: L4 - Three-column (Tutor + Dashboard split)
- **Title**: 学情全景：AI辅导 + 教师看板
- **Core message**: 学生端AI流式答疑，教师端全面学情监控
- **Content**:
  学生侧:
  - AI助教流式答疑 (RAG上下文感知)
  - OJ智能诊断 + Trace分析
  - 个性化错题本与薄弱点标注
  教师侧:
  - 掌握度热力图 (班级整体分布)
  - 学生花名册 (逐人薄弱点)
  - OJ学情统计 (全班完成情况)
  - 学习事件追踪 (行为记录分析)

---

### Part 6: Safety & Innovation

#### Slide 16 - 三重防幻觉机制

- **Layout**: L2 - Left-text right-visual (three concentric rings)
- **Title**: 如何让AI不说胡话？三重防幻觉防线
- **Core message**: RAG约束 + 校验闭环 + 安全审查，系统级降低大模型幻觉风险
- **Visualization**: Three concentric defense rings
- **Content**:
  第一层 RAG知识约束: Okapi BM25检索课程知识库切片，约束LLM生成范围
  第二层 校验闭环: ContentVerifierAgent 对照知识库校验，失败回流重试
  第三层 内容安全: SafetyAgent 检测敏感词/幻觉题号/Prompt注入

#### Slide 17 - 全方位安全机制

- **Layout**: L3 - Card grid (2×2)
- **Title**: 从代码到内容，层层设防
- **Core message**: 6道安全防线覆盖代码执行、内容生成、输出全链路
- **Content**:
  - CA1 AST静态审计: ASTAnalyzer识别死循环/数组越界，执行前熔断
  - CA2 C++安全拦截: check_cpp_security 正则拦截 system/fork/exec
  - CA3 子进程超时: Python 3秒/C++ Trace 3秒硬上限
  - CA4 输出截断: 防无限输出保护
  - CA5 内容安全: 敏感词/幻觉检测
  - CA6 Prompt防护: Prompt注入检测

---

### Part 7: Innovation Highlights

#### Slide 18 - 创新一：自研轻量 DAG 编排

- **Layout**: L2 - Left-text right-visual
- **Title**: 零依赖的自研DAG编排引擎
- **Core message**: 借鉴状态图与DAG编排思想，零langgraph依赖，自主实现
- **Visualization**: Timeline/flow
- **Content**:
  - 不依赖langgraph等第三方Agent框架
  - 自研轻量编排器，部署简单
  - 状态图 + DAG编排思想融合
  - 支持串行/并行/条件分支拓扑
  - 188测试通过验证编排正确性

#### Slide 19 - 创新二：多语言 Trace 统一协议

- **Layout**: L2 - Left-text right-visual
- **Title**: Python/C++ Trace协议统一归一化
- **Core message**: 不同语言、不同追踪技术，统一为13类可视化类型
- **Visualization**: Framework / Matrix
- **Content**:
  Python: sys.settrace HOOK → 统一事件流
  C++: GDB MI 单步 → gdb_stl_extract提取 → 统一事件流
  统一输出: 13类可视化类型（变量/栈/堆/图/链表...）
  前段渲染: D3.js 13个可视化组件

#### Slide 20 - 创新三至五

- **Layout**: L3 - Card grid (3 cards vertical)
- **Title**: 更多技术创新
- **Core message**: 四阶段并行 + 三重防幻觉 + 确定性旁白
- **Content**:
  创新三: 四阶段并行资源生成
  document → (mindmap ∥ exercises) → code_case → (trace ∥ reading)
  相比串行生成效率提升2-3倍
  创新四: RAG + 校验闭环 + Safety 三重防线
  BM25约束 → 对照校验回流重试 → 安全审查
  系统级降低幻觉风险
  创新五: 确定性旁白
  经典题目无LLM依赖
  确保可复现、可验证

---

### Part 8: Value & Verification

#### Slide 21 - 多维度应用价值

- **Layout**: L2 - Left-text right-visual
- **Title**: 三种角色，一套平台
- **Core message**: 对学生、教师、教育三个维度的价值
- **Content**:
  对学生: 个性化路径 + 多维度资源 + Trace可视化 + AI辅导
  对教师: 全面学情看板 + 精准识别薄弱学生 + 教学效果评估
  对教育: AI+教育深度融合实践 + 降低大模型幻觉风险 + 可复制范式

#### Slide 22 - 数据说话

- **Layout**: L5 - Data hero
- **Title**: 用数据证明完成度
- **Core message**: 严格的测试验证确保了系统的可靠性和完成度
- **Visualization**: Number cards
- **Content**:
  [big number] 188 [label] Backend pytest passed
  [big number] 22 [label] 多智能体注册 / 20已实现
  [big number] 13 [label] Trace可视化类型
  [big number] 70+ [label] Vue组件 / 30+页面
  [big number] 6 [label] Layer / 6种资源类型

#### Slide 23 - 项目资源

- **Layout**: L4 - Three-column
- **Title**: 完整的比赛文档体系
- **Core message**: 规范的工程交付，六份完整比赛文档
- **Content**:
  01 项目说明书
  02 系统开发说明书
  03 测试说明书
  04 部署说明书
  05 用户操作手册
  06 开源与AI Coding说明

---

### Part 9: Closing

#### Slide 24 - Closing

- **Closing impact**: "从不会到掌握，AlgoPilot 陪每个学习者走过每一步。" 简洁有力的结语。左半部分深海军蓝背景上白色团队信息，右半部分留白放Logo。
- **Layout**: L1 - Diagonal split (60/40 navy/white)
- **Content**:
  Thank You
  AlgoPilot — 算法领航员
  软件杯 A3 赛题
  2026

---

## X. Speaker Notes Requirements

One speaker note file per page, saved to `notes/`:

- **Filename**: match SVG name (e.g., `01_cover.md`)
- **Content**: script key points, timing cues, transition phrases
- Each note should include:
  - 开场/过渡用语 (1-2句)
  - 核心信息点 (3-5 bullet points)
  - 建议时长 (秒)
  - 下一页过渡提示
