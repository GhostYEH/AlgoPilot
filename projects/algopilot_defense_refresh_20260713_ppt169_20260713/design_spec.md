# AlgoPilot 软件杯答辩 — Design Specification

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | AlgoPilot（算法领航员）软件杯 A3 答辩稿 |
| Canvas Format | PPT 16:9，1280×720 |
| Page Count | 20 |
| Target Audience | 中国软件杯 A3 赛题评委：高校计算机教师、企业技术专家、教育数字化评审 |
| Use Case | 现场答辩与产品演示 |
| Delivery Purpose | `presentation`：一页一个结论，依靠口述串联 |
| Communication Mode | `narrative`：痛点张力 → 闭环转折 → 产品与工程证据 → 创新与验证 → 价值落点 |
| Visual Style | `blueprint` 为主，局部等距系统模型与数据产品舞台 |
| Content Strategy | 在现有 PPT、项目说明书、开发说明书和测试说明书的事实范围内重构、补强和去重；不引入外部事实 |
| Visual Mix | 技术蓝图约 70%，等距系统模型约 20%，数据产品舞台约 10% |
| Spec Review | 开启；正式生成前由用户复审 |

### Core Message

AlgoPilot 不是一个简单的 AI 聊天机器人或 OJ 判题器，而是一套能记住学习状态、解释代码错误并据此重规划学习路径的全流程智能学习系统。

### Content Guardrails

- “22 个 Agent”必须表述为“22 个注册条目，其中 20 个已实现，2 个为规划中扩展节点”。
- “6 种资源”必须表述为“5 类 A3 核心展示资源 + 1 类扩展阅读”。
- 测试证据以 2026-07-12 的真实执行结果为准：188/188 通过、1 个不影响功能的弃用警告、54.05 秒。
- OJ/Trace 当前是课程学习场景的轻量执行环境，不宣称为生产级公网沙箱。
- 不使用无来源的行业调查数字、用户增长数字、效率百分比或效果提升比例。

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280×720 |
| viewBox | `0 0 1280 720` |
| Safe Margin | 左右 56，上 46，下 42 |
| Header Zone | 46–116；章节码、标题、单句结论 |
| Main Content Zone | 126–650 |
| Footer Zone | 664–700；页码、证据来源或状态注记 |

画布模拟工程图纸：全局暗底、低对比细网格、少量坐标刻度和图纸标题栏。网格只承担空间秩序，不穿过正文文字。页面内容必须优先于装饰线。

## III. Visual Theme

### Theme Style

- `blueprint` 占主体：深色工程纸、细线框、模块连线、数据流箭头、尺寸线、坐标标签和关键路径高亮。
- `3d-isometric` 仅用于 Slide 07–09 的局部核心图形；模块保持低透视、低装饰、文字全部留在原生 SVG 层。
- `digital-dashboard` 仅用于 Slide 01、04、20 的舞台气氛；不扩散到普通内容页。
- 页面不采用泛滥卡片。只有并列事实确实需要容器时才使用边框分区；多数页面以连线、分区线、标注与留白组织信息。
- 结构容器、等距模块和状态分区的边框统一使用低对比蓝灰 `#24455B`；青色只用于截图焦点框，红色只保留真实错误状态。黄、绿状态优先通过路径、节点填充和文字表达，不再使用多色容器描边。
- 禁止紫色渐变、玻璃面板、无意义粒子、悬浮光球、过度圆角、密集霓虹描边和模板化 AI 装饰。

### Color Scheme

| Role | HEX | Usage |
| --- | --- | --- |
| Background | `#071521` | 深海工程图纸底色 |
| Secondary Background | `#10283B` | 局部系统区、图例带、代码区 |
| Primary | `#4CC9F0` | 结构线、模块边框、数据流 |
| Accent | `#FFB703` | 唯一关键路径、当前状态、转折点 |
| Secondary Accent | `#52B788` | 通过、完成、验证状态 |
| Body Text | `#F3F7FA` | 标题与正文 |
| Secondary Text | `#A9C2D3` | 注释、说明、次级标签 |
| Tertiary Text | `#6E8CA0` | 页码、坐标、辅助刻度 |
| Border / Grid | `#24455B` / `#163246` | 分区线与背景网格 |
| Warning | `#FF6B6B` | WA/TLE、限制、风险提示 |

每页颜色不超过背景、正文、结构线、单一强调色和状态色五个角色。黄色强调只用于真正的关键路径，不作为大面积填充。

### AI Image Strategy

- Core rendering: `blueprint`
- Palette behavior: `tech-neon`，但严格使用已锁定的青蓝、黄色、绿色；不引入紫色。
- AI 图片只承担氛围、空间和抽象系统世界；所有中文、指标、架构节点、流程标签和真实界面均由 SVG 或项目截图承载。
- AI 图不得生成虚构产品界面、虚构图表、虚构用户案例或可被误读为真实数据的内容。
- AI 主视觉严格限于 Slide 01、04、20，且图像本体不得包含任何文字、数字、命名模块、架构标签或不可验证技术结构。

## IV. Typography

| Role | CJK | Latin | Size | Weight |
| --- | --- | --- | --- | --- |
| Cover Headline | Noto Sans SC | Segoe UI | 88 | 700 |
| Section / Hero | Noto Sans SC | Segoe UI | 64–72 | 700 |
| Page Title | Noto Sans SC | Segoe UI | 54 | 700 |
| Subtitle | Noto Sans SC | Segoe UI | 42 | 600 |
| Body | Noto Sans SC | Segoe UI | 32 | 400–500 |
| Annotation | Noto Sans SC | Segoe UI | 24 | 400 |
| Footnote / Page No. | Noto Sans SC | Segoe UI | 18 | 400 |
| Technical Label / Code | Noto Sans SC | Consolas | 22–26 | 400–600 |

- 正文基线为 32，符合现场演示模式；密集页通过减少文字、分层讲述和口述补充解决，不缩小正文逃避版面问题。
- 中文为主，英文只出现在技术名、协议、Agent 名称和代码路径中。
- 组件 ID、Phase、Layer、API、状态码使用等宽字体，形成真实工程图标注感。
- Formula policy: `text-only`。复杂度如 `O(n)`、`top_k=4` 保持可编辑文本。

## V. Layout Principles

### Page Structure

- 标题区由章节码、结论式标题和一条短引导线组成，禁止“标题 + 大段副标题”的重复层级。
- 主体优先使用全页系统图、单条主流程、真实截图加标注或关键证据大数字。
- 图纸标题栏只在页脚右下角出现，包含页码与章节缩写；不重复项目 Logo。
- 背景网格线宽 1，结构线 2，关键路径 3–4；通过线宽和明度建立层级，不靠阴影。

### Layout Families

| Family | Usage |
| --- | --- |
| Full-canvas blueprint | 架构、流程、Agent、数据流与安全机制 |
| Evidence screenshot + engineering annotation | 首页、学习路径、OJ、教师看板 |
| Isometric exploded system | 总体架构、Agent 分层、四阶段拓扑 |
| Single-path narrative | OJ 受挫闭环、Trace 诊断、RAG 校验链 |
| Data hero | 测试验证、完成度与项目规模 |
| Data-product stage | 封面、产品实证、结尾 |

### Spacing

| Element | Value |
| --- | --- |
| Safe margin | 56 |
| Major block gap | 32–40 |
| Diagram node gap | 24–36 |
| Label-to-line gap | 10–14 |
| Container padding | 22–28 |
| Corner radius | 0–6；默认 2 |

### Page Rhythm

- `anchor`：01、03、04、11、12、17、20
- `dense`：02、07、08、09、13、14、15、18
- `breathing`：05、06、10、16、19

节奏要求：连续两个 dense 页面后必须用 anchor 或 breathing 页面释放视觉压力。卡片网格不得成为跨页默认结构。

## VI. Icon Usage Specification

- Primary library: `tabler-outline`
- 图标只作为 32–44 的识别辅助，不承担复杂概念；投影页上保持 2.4–3 的有效描边。
- 不使用 Emoji。品牌 Logo 仅在确有技术栈识别需要时使用 `simple-icons`，本稿默认不放品牌墙。

| Purpose | Icon Path | Pages |
| --- | --- | --- |
| 学生画像 | `tabler-outline/user-scan` | 03, 10 |
| 学习路径 | `tabler-outline/route-2` | 03, 10 |
| 多智能体 | `tabler-outline/robot` | 03, 08 |
| 数据库 / 记忆 | `tabler-outline/database` | 07, 14 |
| 代码与 OJ | `tabler-outline/code` | 05, 12 |
| Trace / 诊断 | `tabler-outline/scan-traces` | 05, 11 |
| 安全 | `tabler-outline/shield-check` | 13, 14 |
| 测试验证 | `tabler-outline/test-pipe-2` | 17 |
| 教师与教学 | `tabler-outline/school` | 06, 19 |
| 数据流 / 网络 | `tabler-outline/network` | 07–09 |

## VII. Visualization Reference List

本稿不锁定通用图表模板。所有核心图均为与 AlgoPilot 数据结构一一对应的原生 SVG 信息图，避免用通用卡片或套版图表削弱工程真实性。

| Page | Visualization | Data / Structure Contract |
| --- | --- | --- |
| 03 | 六节点学习闭环 | 画像 → 路径 → 资源 → OJ/Trace → 掌握度 → 重规划 |
| 05 | OJ 受挫闭环 | 连续失败 → 事件 → 巩固节点 → 修正 AC → 掌握度更新 |
| 07 | 总体架构 | 前端 / API / 编排与 Agent / RAG-OJ-数据层 |
| 08 | 六层 Agent 系统 | 22 注册条目、20 已实现、2 规划节点、6 layer |
| 09 | 四阶段资源拓扑 | document → mindmap∥exercises → code_case → trace∥reading |
| 11 | Trace 统一协议 | Python sys.settrace 与 C++ GDB MI → 统一事件流 → 13 类可视化 |
| 13 | 双通道防线 | 内容生成三重防幻觉 + OJ 执行安全 |
| 14 | 数据归属图 | JWT 身份 → 7 表 user_id 外键 → 学生/教师权限边界 |
| 17 | 验证仪表 | 188/188、0 failed、typecheck/build 通过、54.05s |

数值图只呈现来源文件中的明确数据；不做推断性趋势图或虚构对比柱状图。

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cover_blueprint_hero.png` | 1280×720 target | 16:9 | 封面系统世界与关键路径 | Background | #1 Full-bleed background with floating title + #29 Two-stop scrim — opaque on text side, transparent on focal side + #41 Background image + measurement lines and module tags (engineering overlay) | ai | Pending | 多个算法模块与学习节点组成一张可运行的工程蓝图，数据流沿一条高亮路径汇聚到学习者，右侧保留视觉焦点、左侧保留标题静区 | none | hero_page |
| `product_stage_atmosphere.png` | 1280×720 target | 16:9 | 真实首页截图的舞台背景 | Background | #1 Full-bleed background with floating title + #17 Picture-in-picture inset + #41 Background image + measurement lines and module tags (engineering overlay) | ai | Pending | 深色系统控制台空间与少量发光数据轨迹，中部形成稳定暗区承托真实产品截图，不出现任何虚构界面或文字 | none | hero_page |
| `closing_path_hero.png` | 1280×720 target | 16:9 | 结尾记忆点 | Background | #1 Full-bleed background with floating title + #27 Linear gradient mask for text legibility + #39 Background image + flow nodes drawn over the scene | ai | Pending | 一条学习路径从错误节点出发，经诊断与巩固后收束到已掌握状态，构图右侧汇聚、左侧保留结语空间 | none | hero_page |
| `homepage.png` | 1680×945 | 1.778 | 核心产品实证 | Screenshot | #17 Picture-in-picture inset + #46 Background image + bordered lens rectangle highlighting a sub-region + #70 Image with thin colored matte frame | user | Existing | AlgoPilot 首页真实截图；锁定标准化版本 |  |  |
| `learning-path.png` | 1680×945 | 1.778 | 动态学习路径实证 | Screenshot | #19 Image floating in whitespace with thin frame and caption + #46 Background image + bordered lens rectangle highlighting a sub-region | user | Existing | 学习路径 DAG 页面真实截图；锁定标准化版本 |  |  |
| `oj-trace-workbench.png` | 1680×945 | 1.778 | OJ 工作台与 Trace 入口实证 | Screenshot | #45 Background image + numbered hotspots with sidebar legend + #70 Image with thin colored matte frame | user | Existing | OJ 与 Trace 工作台真实截图；锁定标准化版本 |  |  |
| `teacher-dashboard.png` | 1680×945 | 1.778 | 教师看板实证 | Screenshot | #45 Background image + numbered hotspots with sidebar legend + #66 Image fading into the solid background | user | Existing | 教师端真实截图；锁定标准化版本 |  |  |

### Image Allocation

- AI 主视觉：Slide 01、04、20；其中 Slide 04 必须叠加真实首页截图，AI 图只做舞台背景。
- 真实截图：Slide 04、06、10、12、19；每张截图都用原生 SVG 热点、尺寸线或状态标注解释，不放进圆角卡片画廊。
- Slide 07–09 的等距模型全部由原生 SVG 构建，不依赖 AI 图片，保证节点文字和连线可编辑。
- 四类截图统一为 16:9 交付视窗，采用同一套直角焦点框、编号热点、单线引导和等宽标签；不混用其他版本或其他浏览器比例的截图。

## IX. Content Outline

### Part 1 — The Learning Problem

#### Slide 01 — 封面：让每一次错误，都成为下一步路径的依据

- **Cover impact**: 以“一条从错误节点通向掌握状态的发光路径”为视觉钩子；真实工程蓝图世界承载标题，不使用泛化 AI 大脑。
- **Layout**: 全幅 `cover_blueprint_hero.png`，左侧标题静区，右侧系统节点与关键路径；底部只保留“软件杯 A3 · 2026”。
- **Title**: AlgoPilot 算法领航员
- **Subtitle**: 面向《数据结构与算法》的多智能体智能学习平台
- **Core message**: 系统不止回答问题，而是记住状态、解释错误并重规划下一步。

#### Slide 02 — 五个痛点，本质是一条断裂的学习链

- **Layout**: 一条从“理解”到“教学反馈”的断裂数据流，五个断点沿路径展开；不做五张等宽卡片。
- **Core message**: 概念、练习、诊断、记忆和教学反馈彼此割裂，才是算法学习效率低的根因。
- **Content**: 概念抽象难懂；刷题无方向；OJ 只给 WA/TLE；学习记录散落；教师难以掌握个体薄弱点。
- **Evidence note**: 痛点来自课程学习观察、公开教学场景分析、团队学习经历和现有平台功能对比，不标注虚构调研比例。

### Part 2 — The Turn: A Closed Learning System

#### Slide 03 — 转折：六个不重复阶段组成会自我调整的闭环

- **Layout**: 全页六节点闭环，中心只放一句“学习状态持续更新”；黄色高亮当前路径，绿色标记完成反馈。
- **Core message**: AlgoPilot 将学习过程统一为六个语义清晰阶段，并让调整结果重新写回画像与路径。
- **Content**: 动态画像 → 路径规划 → 资源生成 → 训练执行 → 诊断评估 → 动态调整；动态调整回写画像与路径。

#### Slide 04 — 产品实证：这套闭环已经落到真实系统界面

- **Layout**: `product_stage_atmosphere.png` 作暗色舞台，真实 `homepage.png` 居中放大；四条工程标注分别指向画像、路径、资源与 OJ 入口。
- **Core message**: AlgoPilot 已将核心学习链路整合为可操作的平台，而非停留在概念方案。
- **Content**: 学生端入口、学习路径、资源工作台、在线 OJ、教师入口；不生成任何虚构 UI。

#### Slide 05 — 一次 WA，触发的不只是一次提示

- **Layout**: 单条横向事件链，节点从红色 WA 转为黄色诊断，再转为绿色 AC；中间用 EventBus 与 Mastery 状态作为工程转折点。
- **Core message**: 连续失败会触发事件、记忆、掌握度与路径调整，错误成为下一次教学决策的输入。
- **Content**: 连续失败 ≥3 → EvaluatorAgent → EventBus → LearningPathAgent 插入巩固节点 → 修正 AC → MasteryAgent 更新 → ProfilingAgent patch 画像。
- **Caveat**: 不把阈值机制表述为普适教学结论，只说明当前系统实现。

#### Slide 06 — 同一条证据链，服务学生也服务教师

- **Layout**: 左侧学生学习事件流，右侧教师看板真实截图；两者通过数据库证据链连接。
- **Core message**: 学生获得个性化反馈，教师看到的则是同一批真实学习记录的聚合结果。
- **Content**: 学生侧：答疑、诊断、错因与薄弱点；教师侧：活跃度、OJ 通过情况、掌握度热力图、学生花名册。

### Part 3 — Engineering the System

#### Slide 07 — 总体架构：所有 AI 调用都经过统一编排与治理

- **Layout**: 局部等距爆炸图：前端层、HTTP/SSE、FastAPI、编排与 Agent、RAG/OJ/数据层；右侧用两条治理原则收束。
- **Core message**: 前后端分离只是表层，核心是请求必须经过 Orchestrator、知识检索、校验和安全链路。
- **Content**: Vue 3 + TypeScript；FastAPI；自研 DAG Orchestrator；BM25；Python/C++ OJ；SQLAlchemy 2.0；讯飞星火 OpenAI 兼容接口。
- **Proof labels**: 30 余页面、70 个组件、16 个路由模块、63 条 API 路由、7 张数据表。

#### Slide 08 — 多智能体不是数量堆砌，而是六层职责分工

- **Layout**: 六层等距剖面，每层列出职责与代表节点；20 个已实现节点用实线，2 个规划节点用虚线并明确标记“规划中”。
- **Core message**: 22 个注册条目按 profiling/resource/path/tutor/safety/eval 六层协作，其中 20 个已有功能或调度实现。
- **Content**: 画像层、资源层、路径层、辅导层、安全层、评估层；PptAgent 与 VideoScriptAgent 不作为已完成功能宣传。

#### Slide 09 — 四阶段拓扑：并行发生在有数据依赖依据的位置

- **Layout**: 低透视等距流水线，Phase 2 与 Phase 4 分叉；每条依赖边标注 `doc_summary`、`quiz_focus`、`scenario_hook`。
- **Core message**: 资源生成不是盲目并发，而是按跨 Agent 摘要依赖组织的四阶段 DAG。
- **Content**: document → mindmap ∥ exercises → code_case → trace_animation ∥ reading；并行任务使用独立 Session，写入不同 PipelineContext 字段。

#### Slide 10 — 个性化不是一句 Prompt，而是可持续更新的状态

- **Layout**: `learning-path.png` 横向主视觉；上方标注画像输入，下方标注学习事件、掌握度和受挫节点如何回写路径。
- **Core message**: 个性化由持久化画像、学习记忆、掌握度与路径 DAG 共同驱动，而不是一次性提示词。
- **Content**: 六维画像；学习路径计划；错误记忆；受挫插入巩固节点；掌握度阈值推进。

### Part 4 — The Diagnostic Core

#### Slide 11 — Trace：让学生看见自己的代码如何出错

- **Layout**: 左右两条输入轨道汇入统一事件总线：Python `sys.settrace` 与 C++ `GDB MI`；下游展开 13 类可视化与确定性旁白。
- **Core message**: AlgoPilot 追踪学生自己的 Python/C++ 代码，并将不同追踪技术归一为统一可视化协议。
- **Content**: Python 行级变量快照；C++ 单步追踪与 STL 状态提取；最多 200 步；链表、树、矩阵、栈、队列等 13 类组件；经典题目确定性旁白。

#### Slide 12 — OJ 工作台：判题、Trace 与深度诊断在同一现场

- **Layout**: `oj-trace-workbench.png` 全宽截图，四个编号热点标注语言切换、提交状态、Trace 入口和 AI 深度诊断；右下角放安全边界短注。
- **Core message**: 从提交代码到查看轨迹、分析错因，学生不必离开同一工作台。
- **Content**: Python/C++；力扣风格与洛谷风格；AST 审计；3 秒超时；边界测例与复杂度报告。

#### Slide 13 — AI 可信来自两条独立防线：内容与执行

- **Layout**: 上半为 RAG → 生成 → ContentVerifier 回流 → Safety；下半为 AST 门闸 → Python/C++ 执行 → 超时/截断；两条线最终汇入“可追溯输出”。
- **Core message**: 内容可靠性和代码执行安全必须分开治理，AlgoPilot 为两条链路分别设置门闸。
- **Content**: BM25 top_k=4；校验失败最多重试 2 次；敏感词/幻觉题号/Prompt 注入；危险调用拦截；Trace 200 步上限；输出截断。
- **Caveat**: 当前 OJ/Trace 是课程学习场景轻量环境，生产部署仍需容器隔离、资源限制和判题队列。

#### Slide 14 — 账号级数据归属，让“记住学生”不等于“混淆学生”

- **Layout**: JWT 身份为根节点，连接 7 张以 `user_id` 关联的数据表；学生权限边界与教师只读聚合边界用不同线型标识。
- **Core message**: 学习记忆和个性化只有建立在清晰的数据归属与角色隔离上才可信。
- **Content**: 前端路由守卫 + 后端 role 校验；服务端不接受客户端指定 `user_id`；学生只能操作自身数据；教师查看班级聚合学情。

### Part 5 — Why It Matters

#### Slide 15 — 对照 A3：核心要求都有代码、页面和状态证据

- **Layout**: 左侧 A3 能力链，右侧对应实现路径；用 6 条代表性证据覆盖画像、5 类核心资源、路径、智能辅导、效果评估、多智能体/RAG/LLM。
- **Core message**: 项目不只覆盖赛题关键词，还为每项能力提供代码位置、API 或页面证据。
- **Content**: ProfilingAgent；LearningPathAgent；资源 generate-all；Tutor/OJ Diagnosis；Mastery/TeacherDashboard；BM25 与 Spark client。
- **Status**: 5 类核心资源已完成，拓展阅读为扩展资源；智能辅导与学习效果评估为已完成加分功能。

#### Slide 16 — 真正的创新，是把“生成”接回学习过程

- **Layout**: 中心为学习状态，四条创新路径向外展开：DAG 编排、Trace 统一、三重防幻觉、OJ 受挫闭环；每条只保留一条机制与一条差异。
- **Core message**: AlgoPilot 的工程创新不在单点模型调用，而在生成、诊断、记忆和重规划被接成可验证闭环。
- **Content**: 零 langgraph 依赖的轻量编排；Python/C++ Trace 归一；RAG+校验+Safety；失败事件驱动巩固节点；经典题目确定性旁白。

#### Slide 17 — 验证结果：188 个后端用例全部通过

- **Layout**: `188 passed` 为唯一主数字；主画面仅保留 0 failed、32 个后端测试文件、前端 typecheck 通过、前端 production build 通过。
- **Core message**: 2026-07-12 归档测试快照显示，核心后端测试与前端构建检查均通过。
- **Content**: 运行耗时只进入页脚或讲稿；归档快照 commit 待补充。当前 2026-07-13 重跑为 190 passed，与归档快照差异进入风险列表。

#### Slide 18 — 四条资产轨道，构成可核验的工程完成度

- **Layout**: 四条横向资产轨道，每轨一个主数字，其余为小型证据标签；禁止并列 KPI 卡片。
- **Core message**: 产品界面、课程题库、OJ/Trace 实践、API/数据/工程四类资产共同证明完成度。
- **Content**: 23 个视图文件；126 道 OJ 题；13 个 Trace Vue 组件；67 个 FastAPI 路由装饰器。辅助标签：73 个组件文件、24 个命名路由、14 章+6 实验+2 项目、13 个游戏组件、8 张 ORM 表、32 个测试文件、6 个 Agent layer。全部绑定 commit `dc3e1503fdffaa7c778f83192048c58785cc5870` 与 2026-07-13 统计口径。

#### Slide 19 — 价值与边界：能运行、能演示，不等于已经生产化

- **Layout**: 全可编辑 SVG 五分支图：学生价值、教师价值、课程建设价值、部署与推广路径、当前生产化边界；不重复使用教师截图。
- **Core message**: 当前可运行与可直接演示能力必须和后续生产化升级项明确分开。
- **Content**: 当前可运行能力；可直接演示能力；后续生产化升级项。
- **Boundary**: 容器级代码沙箱、HTTPS、监控告警、备份、高并发与判题队列均为后续升级项，不描述为已完成。

### Part 6 — Closing

#### Slide 20 — 结尾：让错误留下证据，让系统知道下一步

- **Closing impact**: `closing_path_hero.png` 中一条路径从红色错误节点穿过诊断与巩固，最终抵达绿色掌握状态；结语占据左侧，右侧只留收束后的系统路径。
- **Layout**: 全幅数据产品舞台，但所有节点名称与结语使用原生 SVG；不放通用 “Thank You” 大字。
- **Core message**: AlgoPilot 希望把每一次错误，从一次挫败，变成下一步学习路径的依据。
- **Content**: AlgoPilot 算法领航员 · 软件杯 A3 赛题 · 2026。

## X. Speaker Notes Requirements

每页生成一段适合现场答辩的中文讲稿，并汇总到 `notes/total.md`：

- 单页建议 25–45 秒；封面和结尾各 20–30 秒，架构与 Agent 页可到 50 秒。
- 每页讲稿必须先说结论，再解释图中的一条主路径；不逐字朗读页面。
- 使用自然过渡制造叙事推进，例如“但真正的区别不在功能数量”“接下来把这个闭环拆开看”。
- 口径与 Content Guardrails 一致；对规划节点、轻量执行环境和生产化边界主动说明。
- 演示页（04、10、12、19）在讲稿中给出可切换真实系统 Demo 的提示。
