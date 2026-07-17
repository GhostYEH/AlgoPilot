# AlgoPilot 第三方开源依赖与 AI Coding 使用说明

> 文档版本：v1.2 · 适用赛题：A3 · 更新日期：2026-07-16
> 对应代码版本：`a493bb03df876313eb57f6d5425abed8de745901`（提交前需随最终代码重新确认）
> 文档状态：提交候选版
> 本文档依据官方要求，如实标注 AlgoPilot 项目中使用的开源项目、开源协议、第三方库、AI 大模型与 AI Coding 工具的使用情况，以及团队自主设计与开发的部分。

---

## 一、开源项目使用清单

### 1.1 前端开源项目

| 项目名称 | 版本 | 开源协议 | 用途 | 项目地址 |
|---------|------|---------|------|---------|
| **Vue 3** | ^3.5.34 | MIT | 前端核心框架（Composition API） | https://github.com/vuejs/core |
| **Vue Router** | ^4.6.4 | MIT | SPA 路由与守卫 | https://github.com/vuejs/router |
| **Pinia** | ^3.0.4 | MIT | 状态管理（auth、learningPath、persona） | https://github.com/vuejs/pinia |
| **Element Plus** | ^2.14.0 | MIT | UI 组件库 | https://github.com/element-plus/element-plus |
| **@element-plus/icons-vue** | ^2.3.2 | MIT | Element Plus 图标库 | https://github.com/element-plus/element-plus-icons |
| **CodeMirror 6** | ^6.0.2 | MIT | OJ 代码编辑器 | https://github.com/codemirror/dev |
| **vue-codemirror** | ^6.1.1 | MIT | CodeMirror Vue 封装 | https://github.com/surmon-china/vue-codemirror |
| **@codemirror/lang-python** | ^6.2.1 | MIT | Python 语法高亮 | https://github.com/codemirror/lang-python |
| **@codemirror/lang-cpp** | ^6.0.3 | MIT | C++ 语法高亮 | https://github.com/codemirror/lang-cpp |
| **@codemirror/theme-one-dark** | ^6.1.3 | MIT | 暗色主题 | https://github.com/codemirror/theme-one-dark |
| **Mermaid** | ^11.15.0 | MIT | 思维导图与流程图渲染 | https://github.com/mermaid-js/mermaid |
| **D3.js** | ^7.9.0 | ISC | 自定义数据可视化 | https://github.com/d3/d3 |
| **@vue-flow/core** | ^1.48.2 | MIT | 学习路径 DAG 可视化 | https://github.com/bcakmakoglu/vue-flow |
| **@vue-flow/background** | ^1.3.2 | MIT | Vue Flow 背景组件 | 同上 |
| **@vue-flow/controls** | ^1.1.3 | MIT | Vue Flow 控制组件 | 同上 |
| **axios** | ^1.16.1 | MIT | HTTP 请求库 | https://github.com/axios/axios |
| **fuse.js** | ^7.3.0 | Apache-2.0 | 模糊搜索（题库搜索） | https://github.com/krisk/fuse |
| **Vite** | ^8.0.12 | MIT | 前端构建工具 | https://github.com/vitejs/vite |
| **@vitejs/plugin-vue** | ^6.0.6 | MIT | Vite Vue 插件 | https://github.com/vitejs/vite-plugin-vue |
| **TypeScript** | ~6.0.2 | Apache-2.0 | 类型系统 | https://github.com/microsoft/TypeScript |
| **vue-tsc** | ^3.2.8 | MIT | Vue 类型检查 | https://github.com/vuejs/language-tools |
| **unplugin-auto-import** | ^21.0.0 | MIT | API 自动导入 | https://github.com/unplugin/unplugin-auto-import |
| **unplugin-vue-components** | ^32.0.0 | MIT | 组件自动导入 | https://github.com/unplugin/unplugin-vue-components |
| **@vue/tsconfig** | ^0.9.1 | MIT | Vue TS 配置预设 | https://github.com/vuejs/tsconfig |
| **GSAP** | ^3.15.0 | GSAP Standard License (no charge) | 动画引擎（算法游戏过渡动画） | https://github.com/greensock/GSAP |
| **three.js** | ^0.185.1 | MIT | 3D 可视化 | https://github.com/mrdoob/three.js |
| **world-atlas** | ^2.0.2 | ISC | 世界地图 TopoJSON 数据 | https://github.com/topojson/world-atlas |

### 1.2 后端开源项目

| 项目名称 | 版本 | 开源协议 | 用途 | 项目地址 |
|---------|------|---------|------|---------|
| **FastAPI** | ≥0.115.0 | MIT | Web 框架（异步 API、自动文档） | https://github.com/tiangolo/fastapi |
| **Uvicorn** | ≥0.32.0 | BSD-3-Clause | ASGI 服务器 | https://github.com/encode/uvicorn |
| **python-multipart** | ≥0.0.9 | Apache-2.0 | 表单与文件上传解析 | https://github.com/Kludex/python-multipart |
| **Pydantic** | ≥2.0.0 | MIT | 数据校验与 Schema 定义 | https://github.com/pydantic/pydantic |
| **pydantic-settings** | ≥2.0.0 | MIT | 环境变量配置管理 | https://github.com/pydantic/pydantic-settings |
| **SQLAlchemy** | ≥2.0.0 | MIT | ORM（数据库映射） | https://github.com/sqlalchemy/sqlalchemy |
| **cryptography** | ≥41.0.0 | Apache-2.0/BSD | 加密库（JWT 底层依赖） | https://github.com/pyca/cryptography |
| **python-jose** | ≥3.3.0 | MIT | JWT 签发与验证 | https://github.com/mpdavis/python-jose |
| **bcrypt** | ≥4.0.0 | Apache-2.0 | 密码哈希 | https://github.com/pyca/bcrypt |
| **email-validator** | ≥2.0.0 | UNLICENSE | 邮箱格式校验 | https://github.com/JoshData/python-email-validator |
| **httpx** | ≥0.27.0 | BSD-3-Clause | HTTP 客户端（调用星火 API） | https://github.com/encode/httpx |
| **websocket-client** | ≥1.6.0 | BSD-3-Clause | 讯飞 TTS WebSocket 客户端 | https://github.com/websocket-client/websocket-client |
| **PyYAML** | ≥6.0.0 | MIT | YAML 解析（课程 manifest、技能卡） | https://github.com/yaml/pyyaml |

### 1.3 开发与测试工具

| 项目名称 | 版本 | 开源协议 | 用途 |
|---------|------|---------|------|
| **pytest** | ≥8.0.0 | MIT | 测试框架 |
| **pytest-asyncio** | ≥0.24.0 | Apache-2.0 | 异步测试支持 |
| **pytest-cov** | ≥5.0.0 | MIT | 测试覆盖率 |
| **ruff** | ≥0.8.0 | MIT | Python lint |
| **PyInstaller** | — | GPL-2.0 | 打包为 exe |
| **GitHub Actions** | — | 专有 | CI/CD |

### 1.4 系统级工具（运行时依赖）

| 工具 | 协议 | 用途 | 必需性 |
|------|------|------|--------|
| **Python** | PSF License | 后端运行时 | 必需 |
| **Node.js** | MIT | 前端构建 | 必需（开发模式） |
| **g++ (GCC/MinGW)** | GPL-3.0 | C++ OJ 编译 | 可选 |
| **gdb** | GPL-3.0 | C++ Trace 追踪 | 可选 |
| **MSYS2** | GPL-3.0 | Windows 下 g++/gdb 提供 | 可选 |

---

## 二、开源协议说明

### 2.1 AlgoPilot 自身授权方式

AlgoPilot 项目源代码托管于 GitHub 仓库（https://github.com/GhostYEH/AlgoPilot.git）。项目自身的软件著作权及授权方式以仓库根目录 `LICENSE` 文件为准，**当前 LICENSE 为专有协议（All Rights Reserved）**，未授予复制、修改、分发的权利。本文中"开源"一词仅指 AlgoPilot 所使用的第三方开源组件，不代表项目自身已以标准开源协议发布。

### 2.2 依赖协议说明

项目使用多项第三方开源组件，各组件分别遵循其原始开源许可证。主要涉及的协议类型包括：

- **MIT**：最宽松，允许商用、修改、分发，仅需保留版权声明
- **Apache-2.0**：宽松，含专利授权条款
- **BSD-3-Clause**：宽松，需保留版权声明
- **ISC**：MIT 的简化版
- **GPL-3.0**：g++/gdb/MSYS2 为系统工具，由后端通过 subprocess 动态调用，不与项目代码静态链接，不触发 GPL 传染
- **GPL-2.0**：PyInstaller 为打包工具，仅在构建阶段使用，不进入运行时分发产物
- **PSF License**：Python 运行时授权

团队已对主要第三方依赖及其许可证进行登记，项目使用、提交和分发应持续遵循相应许可证条款。

---

## 三、第三方库使用说明

### 3.1 核心第三方库使用方式

| 第三方库 | 使用方式 | 是否修改源码 |
|---------|---------|-------------|
| Vue 3 | 按官方 Composition API 使用，未修改源码 | 否 |
| Element Plus | 按官方文档使用组件，未修改源码 | 否 |
| CodeMirror 6 | 按官方 API 集成，未修改源码 | 否 |
| Mermaid | 按官方 API 渲染，未修改源码 | 否 |
| D3.js | 按官方 API 绑定数据，未修改源码 | 否 |
| FastAPI | 按官方文档定义路由与依赖注入，未修改源码 | 否 |
| SQLAlchemy | 按官方 ORM API 定义模型，未修改源码 | 否 |
| Pydantic | 按官方 API 定义 Schema，未修改源码 | 否 |
| httpx | 按官方 API 调用星火接口，未修改源码 | 否 |

### 3.2 未使用的常见库（刻意避免）

| 未使用库 | 原因 |
|---------|------|
| LangChain | 过重，本项目自研轻量 DAG 编排即可满足需求 |
| LangGraph | 同上，系统借鉴状态图与 DAG 编排思想，自主实现轻量级多智能体工作流 |
| numpy / pandas | 本项目无数据分析需求，避免重依赖 |
| matplotlib | 前端使用 D3/Mermaid 可视化，后端无需绘图 |

---

## 四、AI 大模型使用说明

### 4.1 使用的 AI 大模型

| 模型 | 提供方 | 用途 | 调用方式 |
|------|--------|------|---------|
| **讯飞星火 Spark** | 科大讯飞 | 画像对话、资源生成、AI 助教、AI 深度诊断 | OpenAI 兼容接口（`https://spark-api-open.xf-yun.com/v1/chat/completions`） |

### 4.2 模型配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| SPARK_API_PASSWORD | （必填） | 星火 API Password |
| SPARK_MODEL | lite | 模型版本（可选 generalv3、4.0Ultra 等） |
| SPARK_CHAT_URL | https://spark-api-open.xf-yun.com/v1/chat/completions | API 地址 |
| SPARK_MAX_TOKENS_LIMIT | 4096 | 单次请求最大 token |
| SPARK_TIMEOUT | 90 秒 | 非流式超时 |
| SPARK_STREAM_TIMEOUT | 180 秒 | 流式超时 |

### 4.3 调用约束

- **所有 LLM 调用收口于 `services/llm/client.py`**，API 层禁止直连大模型
- 所有 Agent 通过 `from services.llm import chat_completion, chat_completion_stream` 统一调用
- 提供流式（`chat_completion_stream`，AsyncIterator）与非流式（`chat_completion`）两种调用方式

### 4.4 模型使用场景

| 场景 | 调用方式 | 说明 |
|------|---------|------|
| 画像对话 | 流式 SSE | ProfilingAgent 多轮对话，实时返回 |
| 资源生成 | 非流式 | 6 种资源 Agent 生成完整内容（5 类核心 + 1 类扩展阅读） |
| AI 助教答疑 | 流式 SSE | TutorAgent 实时答疑 |
| AI 深度诊断 | 非流式 | OjDiagnosisAgent 生成诊断报告 |
| 学情评估 | 非流式 | EvaluationAgent 多维度评估 |

### 4.5 防幻觉措施

| 措施 | 说明 |
|------|------|
| RAG 知识约束 | BM25 检索课程知识库，约束生成范围 |
| 校验闭环 | ContentVerifierAgent 对照知识库校验，失败回流重试 |
| 安全审查 | SafetyAgent 检测敏感词、幻觉题号、Prompt 注入 |
| 占位符检测 | 未配置真实密钥时 AI 功能不可用，避免误用 |

---

## 五、AI Coding 工具使用说明

### 5.1 使用的 AI Coding 工具

| 工具 | 提供方 | 使用范围 | 使用方式 |
|------|--------|---------|---------|
| **讯飞 iFlyCode** | 科大讯飞 | 辅助代码编写、重构、调试、文档生成 | 交互式对话生成代码片段、代码审查、问题排查 |

> 说明：仅列出实际使用过的工具。团队成员在项目开发过程中使用讯飞 iFlyCode 辅助完成代码解释、问题定位、测试用例建议、局部代码生成、文档整理与重构建议。所有 AI 生成或修改内容均由团队成员进行人工审核、运行测试和版本控制。项目需求设计、系统架构、功能取舍、数据设计、联调测试和最终交付由团队负责。

### 5.2 AI Coding 工具使用范围

#### 5.2.1 用于以下辅助工作

| 工作类型 | 说明 | 人工审查程度 |
|---------|------|-------------|
| **样板代码生成** | FastAPI 路由骨架、Pydantic Schema 定义、Vue 组件模板 | 逐行审查并修改 |
| **代码补全** | 工具函数实现、类型注解、异常处理 | 逐行审查 |
| **重构建议** | 提取公共逻辑、优化循环、简化条件 | 评估后采纳部分建议 |
| **文档生成** | 函数 docstring、注释、README 片段 | 审校准确性后修改 |
| **Bug 排查** | 分析错误堆栈、定位问题根因 | 验证后修复 |
| **测试用例生成** | pytest 测试函数骨架 | 审查后补充断言与边界用例 |

#### 5.2.2 未用于以下工作（团队自主完成）

| 工作类型 | 说明 |
|---------|------|
| **架构设计** | 多智能体 DAG 编排、四阶段并行拓扑、PipelineContext 协作机制由团队自主设计 |
| **核心算法实现** | BM25 检索算法、BKT-lite 掌握度计算、AST 静态分析、GDB MI STL 提取由团队自主实现 |
| **Trace 协议设计** | 13 类可视化类型归一化协议由团队自主设计 |
| **知识库内容** | 14 章课程 Markdown、技能卡 YAML、OJ 题库由团队自主编写 |
| **Prompt 工程** | 各 Agent 的系统 Prompt 由团队自主设计与调优 |
| **安全机制设计** | AST 熔断、C++ 危险调用拦截、SafetyAgent 审查策略由团队自主设计 |
| **产品决策** | 功能优先级、用户流程、交互设计由团队自主决策 |

### 5.3 AI 生成代码的审查与测试

#### 5.3.1 审查流程

```
AI 生成代码
  ↓
人工逐行审查 ← 对照项目架构规范与编码标准
  ↓
修改与适配 ← 调整命名、补充类型注解、处理边界情况
  ↓
集成到项目 ← 确保与现有代码风格一致
  ↓
单元测试 ← 编写 pytest 测试用例验证
  ↓
集成测试 ← 端到端验证功能正确性
  ↓
CI 验证 ← GitHub Actions 自动运行 ruff + pytest + build
```

#### 5.3.2 审查标准

| 审查维度 | 标准 |
|---------|------|
| 功能正确性 | 代码是否实现预期功能 |
| 类型安全 | TypeScript/Pydantic 类型注解完整 |
| 错误处理 | 异常场景是否妥善处理 |
| 安全性 | 是否引入安全漏洞（如 SQL 注入、XSS） |
| 性能 | 是否有明显的性能问题 |
| 代码风格 | 是否符合 ruff/eslint 规范 |
| 架构一致性 | 是否遵循项目分层架构（API → Orchestrator → Agent → LLM） |
| 数据归属 | 是否遵循"从 JWT 取 user_id"原则 |

#### 5.3.3 测试覆盖

所有 AI 辅助生成的代码均纳入测试体系：
- 后端：191 个 pytest 测试函数（实际收集并通过 190 个，2026-07-16 本地执行结果），详见 [03_测试说明书.md](03_测试说明书.md)
- 前端：TypeScript 类型检查 + 构建验证 + 3 个工具函数单元测试脚本（`test:oj-struggle`、`test:path-replan-diff`、`test:graph-module`）
- CI：GitHub Actions 自动化检查（后端 ruff + pytest，前端 typecheck + build + 3 个测试脚本）

---

## 六、团队自主设计与开发部分

### 6.1 自主设计的核心架构

| 模块 | 自主设计内容 | 代码位置 |
|------|-------------|---------|
| **多智能体 DAG 编排** | 自研轻量 Orchestrator + Workflow DAG（借鉴状态图与 DAG 编排思想，零 langgraph 依赖，自主实现） | `services/orchestrator/` |
| **四阶段并行拓扑** | document → (mindmap ∥ exercises) → code_case → (trace_animation ∥ reading) | `schemas/resources.py` PARALLEL_PHASES |
| **PipelineContext 协作** | 跨 Agent 摘要传递（doc_summary/quiz_focus/scenario_hook/trace_hint） | `services/orchestrator/pipeline_context.py` |
| **Agent 注册表** | 22 个注册条目，其中 20 个有真实实现，分属 6 个 layer（profiling/resource/path/tutor/safety/eval）；PptAgent、VideoScriptAgent 为规划中扩展节点，仅注册未实现 | `services/agents/registry.py` |
| **六维画像模型** | 知识基础/认知风格/代码实操/学习目标/易错偏好/抗挫心理 | `services/agents/persona.py` |
| **OJ 受挫闭环** | EvaluatorAgent 检测连续 3 次失败 → EventBus → LearningPathAgent 插巩固节点 | `services/events/`、`api/orchestrator.py` |
| **Trace 可视化协议** | 13 类类型归一化（list/matrix/linked_list/tree/sequence/associative 等） | `backend/docs/trace_viz_schema.md`、`frontend/src/utils/traceProtocol.ts` |

### 6.2 自主实现的核心算法

| 算法 | 说明 | 代码位置 |
|------|------|---------|
| **Okapi BM25 检索** | 轻量 BM25 实现（k1=1.5, b=0.75）+ 同义词扩展，无向量依赖 | `services/knowledge/retriever.py` |
| **BKT-lite 掌握度** | 贝叶斯知识追踪简化版，计算章节/技能掌握度 | `services/mastery/scoring.py` |
| **AST 静态分析** | Python AST 死循环检测、越界熔断 | `services/agents/ast_analyzer.py` |
| **Python Trace 引擎** | sys.settrace 逐行追踪 + 变量快照 + 类型归一化 | `services/oj/trace_runner.py` |
| **C++ GDB MI 追踪** | GDB Machine Interface + STL Pretty-Printers 提取 | `services/oj/cpp_trace_runner.py`、`gdb_stl_extract.py` |
| **C++ 安全正则** | 危险头文件与函数调用拦截 | `utils/security.py` |
| **技能卡路由** | 基于画像与 OJ 表现的技能卡推荐路由 | `services/skills/skill_router.py` |

### 6.3 自主编写的内容

| 内容 | 说明 | 位置 |
|------|------|------|
| **课程知识库** | 14 章《数据结构与算法》课程 Markdown | `knowledge/courses/data_structures_algorithms/chapters/` |
| **实验指导** | 6 个实验文档 | `knowledge/courses/.../labs/` |
| **项目案例** | 2 个综合项目 | `knowledge/courses/.../projects/` |
| **OJ 题库** | 126 道题目（含题面、测例、隐藏测例） | `backend/data/oj/`、`scripts/oj_test_data*.py` |
| **技能卡** | 13 张技能卡 YAML（backtracking/binary-search/dp-state-design 等） | `services/skills/cards/` |
| **知识切片** | 按模块分块的概念/例题/常见错误/代码模板 | `knowledge_base/chunks.json` |
| **学生画像模板** | 4 个典型学生画像 JSON | `knowledge_base/student_profiles/` |
| **Agent Prompt** | 20 个已实现 Agent 的系统 Prompt（PptAgent、VideoScriptAgent 为规划中扩展节点，未实现） | `services/agents/*.py`、`services/oj/ai_diagnosis.py` |
| **前端组件** | 74 个通用 Vue 组件（学习、OJ、Trace、画像、资源等，统计自 `frontend/src/components/`） | `frontend/src/components/` |
| **算法游戏** | 13 个游戏化学习组件 | `frontend/src/modules/games/` |

### 6.4 自主设计的 Prompt 工程

各 Agent 的系统 Prompt 均由团队自主设计与调优，包括但不限于：

| Agent | Prompt 设计要点 |
|-------|----------------|
| ProfilingAgent | 六维画像引导式对话，约束输出为 JSON |
| ConceptAgent | 注入画像 + RAG 上下文，约束 Domain/Structure JSON 格式 |
| QuizAgent | 基于画像生成 5 道个性化题（选择+填空），含难度梯度 |
| ContentVerifierAgent | 对照知识库校验，输出 pass/fail + 理由 |
| SafetyAgent | 检测敏感词、幻觉题号、Prompt 注入 |
| OjDiagnosisAgent | 4 个系统 Prompt（TRACE_BUG_DIAGNOSIS/EDGE_CASE/TRACE_DIAGNOSIS/COMPLEXITY） |
| TutorAgent | 流式答疑，注入画像 + 知识上下文 + 防幻觉提示 |

---

## 七、AI 辅助使用范围说明

> 说明：本节不使用无法验证的精确百分比（如"前端 50%""文档 60%""整体 30%–40%"等），改为按"主要使用场景—影响范围—人工审查方式—是否涉及核心逻辑—最终责任归属"的口径如实说明。如后续能提供 commit、生成记录或审查记录支持的精确比例，可在此基础上补充。

### 7.1 主要使用场景

AI Coding 工具（讯飞 iFlyCode）在项目中的主要使用场景：

| 使用场景 | 影响范围 | 是否涉及核心逻辑 |
|---------|---------|----------------|
| 样板代码生成 | FastAPI 路由骨架、Pydantic Schema 定义、Vue 组件模板 | 否（结构化样板，业务逻辑由团队填充） |
| 代码补全 | 工具函数实现、类型注解、异常处理片段 | 否（局部片段，需人工审查并适配） |
| 重构建议 | 提取公共逻辑、优化循环、简化条件 | 否（建议性质，评估后选择性采纳） |
| 文档初稿 | 函数 docstring、注释、README 片段、提交文档初稿 | 否（内容审校与修正由人工完成） |
| Bug 排查 | 分析错误堆栈、定位问题根因 | 否（验证后由人工修复） |
| 测试用例骨架 | pytest 测试函数骨架 | 否（断言与边界用例由人工补充） |

### 7.2 团队自主完成的工作

以下工作未使用 AI Coding 工具，由团队自主设计与实现：

- **架构设计**：多智能体 DAG 编排、四阶段并行拓扑、PipelineContext 协作机制
- **核心算法实现**：BM25 检索算法、BKT-lite 掌握度计算、AST 静态分析、GDB MI STL 提取
- **Trace 协议设计**：13 类可视化类型归一化协议
- **知识库内容**：14 章课程 Markdown、6 个实验、2 个综合项目
- **OJ 题库**：126 道题目（含题面、测例、隐藏测例）
- **技能卡 YAML**：13 张技能卡
- **Prompt 工程**：各 Agent 的系统 Prompt 设计与调优
- **安全机制设计**：AST 熔断、C++ 危险调用拦截、SafetyAgent 审查策略
- **产品决策**：功能优先级、用户流程、交互设计

### 7.3 人工审查方式

- 所有 AI 生成或修改内容均由团队成员进行人工逐行审查
- 审查维度包括功能正确性、类型安全、错误处理、安全性、性能、代码风格、架构一致性与数据归属
- 所有 AI 辅助生成的代码均纳入测试体系：后端 190 个测试用例通过（2026-07-16）、前端 typecheck + build + 3 个测试脚本通过、GitHub Actions CI 自动化检查

### 7.4 最终责任归属

项目需求设计、系统架构、功能取舍、数据设计、Prompt 设计、知识库内容、安全机制、联调测试和最终交付由团队审核并负责。AI Coding 工具的使用不改变团队对项目最终质量与合规性的责任归属。

> AI 辅助比例的精确数值目前缺乏可核验的量化证据（如 commit 级生成记录、自动审查日志等），暂不给出百分比。如后续取得可核验证据，可在本节补充。

---

## 八、第三方开源依赖合规声明

### 8.1 开源协议保留

本项目保留所有使用的开源项目的版权声明与许可证文本。依赖的版权信息可通过以下方式查看：

```powershell
# 后端依赖
cd backend
pip show <包名>

# 前端依赖
cd frontend
npm ls <包名>
```

### 8.2 引用与致谢

AlgoPilot 项目基于以下优秀开源项目构建，在此表示感谢：

- **Vue 3** 及其生态（Vue Router、Pinia）—— 前端框架
- **Element Plus** —— UI 组件库
- **CodeMirror 6** —— 代码编辑器
- **Mermaid** —— 图表渲染
- **D3.js** —— 数据可视化
- **Vue Flow** —— DAG 可视化
- **FastAPI** —— 后端 Web 框架
- **SQLAlchemy** —— ORM
- **Pydantic** —— 数据校验
- **讯飞星火** —— 大语言模型
- **讯飞 TTS** —— 语音合成

### 8.3 声明

- 本项目未修改任何开源项目的源代码
- 本项目通过 API 调用讯飞星火大模型，未对模型本身进行微调或修改
- 项目使用的第三方开源组件分别遵循 MIT、Apache-2.0、BSD-3-Clause、ISC 等宽松协议，PyInstaller（GPL-2.0）与 g++/gdb/MSYS2（GPL-3.0）为构建阶段或运行时动态调用的系统工具，不进入项目分发产物
- g++/gdb/MSYS2 为系统工具，由后端通过 subprocess 动态调用，不与项目代码静态链接，不触发 GPL 传染
- 项目自身的软件著作权及授权方式以仓库根目录 `LICENSE` 文件为准

---

## 九、附录：依赖完整清单

### 9.1 后端依赖（requirements.txt）

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-multipart>=0.0.9
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
cryptography>=41.0.0
python-jose[cryptography]>=3.3.0
bcrypt>=4.0.0
email-validator>=2.0.0
httpx>=0.27.0
websocket-client>=1.6.0
PyYAML>=6.0.0
```

### 9.2 后端开发依赖（requirements-dev.txt）

```
pytest>=8.0.0
pytest-cov>=5.0.0
pytest-asyncio>=0.24.0
ruff>=0.8.0
```

### 9.3 前端依赖（package.json）

**dependencies**:
```
@codemirror/lang-cpp ^6.0.3
@codemirror/lang-python ^6.2.1
@codemirror/theme-one-dark ^6.1.3
@element-plus/icons-vue ^2.3.2
@vue-flow/background ^1.3.2
@vue-flow/controls ^1.1.3
@vue-flow/core ^1.48.2
axios ^1.16.1
codemirror ^6.0.2
d3 ^7.9.0
element-plus ^2.14.0
fuse.js ^7.3.0
gsap ^3.15.0
mermaid ^11.15.0
pinia ^3.0.4
three ^0.185.1
vue ^3.5.34
vue-codemirror ^6.1.1
vue-router ^4.6.4
world-atlas ^2.0.2
```

**devDependencies**:
```
@types/d3 ^7.4.3
@types/node ^24.12.3
@types/three ^0.185.1
@vitejs/plugin-vue ^6.0.6
@vue/tsconfig ^0.9.1
typescript ~6.0.2
unplugin-auto-import ^21.0.0
unplugin-vue-components ^32.0.0
vite ^8.0.12
vue-tsc ^3.2.8
```
