# AlgoPilot

> 基于程序执行证据链与多智能体协同的智能算法学习与诊断系统。

## Why AlgoPilot

普通大模型根据代码文本"猜"学生哪里错了。AlgoPilot 通过**真实程序执行结果、失败测试用例、变量变化和执行轨迹**，基于程序执行证据诊断学生**为什么**出错，并将错误转化为可解释的学习干预。

## 核心痛点

- 传统 OJ 只告诉你 Wrong Answer，不告诉你错在哪、为什么错
- 普通 AI 辅导只看代码文本，缺乏执行证据，容易幻觉
- 学生不知道自己哪个知识点薄弱，只知道自己"这道题没做对"
- 提示系统要么直接给答案，要么毫无帮助，缺乏分层引导

## 核心创新

### 1. Execution Evidence Engine（程序执行证据引擎）

将静态分析、OJ 判题、失败测试用例、Python/C++ Trace、AI 诊断统一抽象为 `ExecutionEvidence` 结构化数据模型。AI 诊断结论必须携带可追溯的执行证据，而非纯自然语言。

- 统一 schema：`backend/schemas/execution_evidence.py`
- 组装器：`backend/services/evidence/execution_evidence_builder.py`

### 2. First Divergence Detection（首次状态偏离检测）

比较学生程序执行过程与合理参考状态，定位**第一次出现异常的位置**、对应代码行、关键变量、学生状态与参考状态的差异。

### 3. Counterexample Generator（反例生成器）

当代码出现 Wrong Answer 时，系统主动寻找最能暴露 Bug 的测试输入。覆盖空输入、单元素、极值、重复、有序、逆序等边界类别，并通过真实执行验证反例有效性。

- 模块：`backend/services/oj/counterexample.py`

### 4. Bug Taxonomy（错误分类系统）

9 种 ErrorType �! 规则分类，每次诊断产生错误类型、疑似位置、证据、置信度、对应知识点。

- 模块：`backend/services/oj/error_patterns.py`

### 5. Bug → Knowledge Point 映射

代码错误 → 错误类别 → 算法知识点 → 学生知识薄弱点。连续出现相同 Bug 类型时，系统判断对应知识点掌握不足。

### 6. 分层提示系统

禁止 AI 一开始直接给答案。Hint Level 1 → 2 → 3 → 完整原理解释，记录 `hintLevelUsed` 并影响掌握度。

### 7. Student Knowledge State（学生知识状态模型）

六维加权 + BKT-lite 掌握概率，综合题目难度、历史表现、最近表现、是否第一次 AC、修改次数、Bug 类型、是否重复出现相同 Bug。

### 8. 多智能体协同

21 个注册节点，6 个 layer（profiling / resource / path / tutor / safety / eval），自主实现轻量级 DAG 工作流（零 langgraph 依赖）。

## AI 为什么不是普通 ChatGPT

| 普通 ChatGPT | AlgoPilot |
|-------------|-----------|
| 只看代码文本 | 真实执行代码 + Trace + 失败用例 |
| 自然语言诊断 | 结构化 ExecutionEvidence |
| 随机置信度 | 基于证据的 confidence_source |
| 直接给答案 | 分层提示 L1→L2→L3 |
| 无知识点关联 | Bug → Knowledge Point 映射 |
| 无学习状态 | Student Knowledge State 持久化 |
| 无降级能力 | LLM 不可用时规则诊断兜底 |

## 核心学习闭环

```
学习算法 → 提交代码 → 静态分析 → OJ 真实判题 → 发现错误
  → 寻找暴露 Bug 的测试用例 → 真实执行 Trace → 分析变量和控制流变化
  → 定位首次异常状态 → 识别 Bug 类型 → 映射到算法知识点
  → AI 分层教学 → 学生修改 → 再次提交 → Accepted
  → 更新知识掌握状态 → 动态调整后续学习路径
```

## Architecture

```
frontend/          Vue 3 + Vite + Pinia + vue-router
  src/views/       24 个页面（学习/OJ/Trace/诊断/教师看板）
  src/components/  70+ 组件（含 Trace 可视化 13 个子组件）
  src/stores/      Pinia 状态管理
  src/api/         15 个 API 模块

backend/           FastAPI + SQLite + JWT + RBAC
  api/             17 个路由模块
  services/        核心业务逻辑
    agents/        22 个多智能体节点
    orchestrator/  DAG 编排核心
    oj/            OJ 判题 + Trace + AI 诊断 + 反例生成
    evidence/      信任证据链 + Execution Evidence Engine
    mastery/       六维加权掌握度
    llm/           LLM 调用 + 输出验证
    safety/        内容安全审查
  models/          12 张 SQLAlchemy 表
  schemas/         22 个 Pydantic schema 模块
  knowledge_base/  BM25 检索索引

evaluation/        系统评测框架（12 项指标）
```

## Tech Stack

- **后端**：Python 3.13 + FastAPI + SQLAlchemy 2.0 + Alembic + SQLite + JWT
- **前端**：Vue 3.5 + Vite 8 + Pinia 3 + TypeScript 6 + vue-router 4
- **可视化**：D3.js + Three.js + Mermaid + Vue Flow + GSAP
- **代码编辑**：CodeMirror 6（Python/C++ 语法高亮）
- **AI**：科大讯飞星火大模型（OpenAI 兼容接口）+ 自主实现多智能体编排
- **OJ**：Python subprocess + C++ g++ + GDB MI（STL 容器提取）
- **检索**：BM25 RAG（无向量依赖）+ 同义词扩展

## Quick Start

### 配置

复制 `backend/.env.example` 为 `backend/.env`，至少设置：

```dotenv
JWT_SECRET=请替换为长随机字符串
SPARK_API_PASSWORD=你的星火_APIPassword
```

### 启动后端

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 9000
```

### 启动前端

```powershell
cd frontend
npm install
npm run dev
```

访问 http://127.0.0.1:5173（开发）或 http://127.0.0.1:9000（打包）。

### Windows 一键启动

```powershell
.\启动.bat
```

## Tests

### 后端测试

```powershell
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

### 前端测试

```powershell
cd frontend
npm run typecheck
npm run build
npm run test:oj-struggle
npm run test:path-replan-diff
npm run test:graph-module
npm run test:structured-json
```

### 测试状态

| 项目 | 状态 |
|------|------|
| Backend pytest (deterministic) | 137 passed, 18 slow deselected |
| Frontend typecheck | 通过 |
| Frontend build | 通过 |
| Frontend test:oj-struggle | 9 项通过 |
| Frontend test:structured-json | 13 项通过 |
| Frontend test:path-replan-diff | 10 项通过 |
| Frontend test:graph-module | 11 项通过 |
| Frontend test:exec-evidence | 9 项通过 |

> 上述测试结果基于 2026-08-12 本地真实执行（Windows 11 / Python 3.13.7 / Node.js 25.8.1）。

### Slow 测试分层

18 个 slow 测试分为两类：

| 类别 | 数量 | 原因 | 运行策略 |
|------|------|------|---------|
| A. 外部 LLM / 真实 subprocess | 11 | `ai_diagnose` 调用真实 Trace runner + Counterexample subprocess + LLM API | 发布前人工运行 |
| B. 真实 Python subprocess | 7 | `run_cases` 真实执行学生代码 | 发布前人工运行 |

### CI 测试运行

```powershell
# 在 backend 目录下执行
python scripts/ci_test_runner.py fast      # 仅快速测试（137 passed, 18 deselected）
python scripts/ci_test_runner.py slow      # 仅 slow 测试（需 LLM + subprocess）
python scripts/ci_test_runner.py migrate   # 仅迁移测试（6 passed）
python scripts/ci_test_runner.py all       # 全部测试
```

GitHub Actions 配置：
- `.github/workflows/backend-tests.yml`：push/PR 时运行 fast + migration 测试
- `.github/workflows/slow-tests-scheduled.yml`：每日 04:00 UTC 运行 slow 测试

### Counterexample 开销优化

`verify_and_find_best(early_stop=True)`：找到第一个触发 Bug 的候选后立即停止，平均 subprocess 调用从 8 次降至 1-2 次。候选去重（`_deduplicate`）跳过 args 完全相同的候选。

### 集成审计证据表

下表证明每个核心能力均**真正进入正式用户业务流程**（被生产 endpoint 调用），而非独立工具类。

| 能力 | 生产代码入口 | 核心函数 | 数据库 | 前端组件 | 自动测试 | 状态 |
|------|-------------|---------|--------|---------|---------|------|
| ExecutionEvidence | `api/oj.py: api_ai_diagnose` | `build_execution_evidence` | — | `OjAiDiagnosisPanel.vue` | test_execution_evidence (10), test_evidence_builder (11) | **Integrated** |
| Counterexample (WA) | `api/oj.py: api_ai_diagnose` | `try_counterexample` | — | `OjAiDiagnosisPanel.vue` | test_counterexample_integration (13) | **Integrated** |
| First Divergence | `api/oj.py: api_ai_diagnose` | `run_first_divergence_analysis` | — | `OjAiDiagnosisPanel.vue` | test_first_divergence (26) | **Integrated** |
| Bug 分类 (9 种) | `api/oj.py: api_ai_diagnose` | `classify_error_type` | `bug_records` | `OjAiDiagnosisPanel.vue` | test_error_patterns (19) | **Integrated** |
| Bug → Knowledge | `api/oj.py: api_ai_diagnose` | `update_knowledge_state` | `student_knowledge_states` | — | test_db_integration (17) | **Integrated** |
| ExecutionTrace 持久化 | `api/oj.py: api_ai_diagnose` | `persist_execution_trace` | `execution_traces` | — | test_db_integration (3), test_trace_size (6) | **Integrated** |
| BugRecord 持久化 | `api/oj.py: api_ai_diagnose` | `persist_bug_record` | `bug_records` | — | test_db_integration (3) | **Integrated** |
| HintRecord 持久化 | `api/oj.py: api_ai_diagnose` | `persist_hint_record` | `hint_records` | — | test_db_integration (2) | **Integrated** |
| StudentKnowledgeState | `api/oj.py: api_submit + api_ai_diagnose` | `update_knowledge_state` | `student_knowledge_states` | — | test_db_integration (9), test_e2e_mastery (2) | **Integrated** |
| AC Mastery Update | `api/oj.py: api_submit` | `update_knowledge_state` | `student_knowledge_states` | — | test_e2e_mastery (2) | **Integrated** |
| 重复 Diagnosis 幂等 | `api/oj.py: api_ai_diagnose` | `applied_evidence` 检查 | `student_knowledge_states` | — | test_e2e_mastery (slow) | **Integrated** |
| Alembic 迁移 (applied_evidence) | `migrations/versions/20260812_0004` | `upgrade` / `downgrade` | `student_knowledge_states` | — | test_migration_applied_evidence (6) | **Integrated** |
| Counterexample early_stop 优化 | `services/oj/counterexample.py` | `verify_and_find_best(early_stop=True)` | — | — | test_counterexample (5) | **Integrated** |
| Frontend Evidence Rendering | — | — | — | `OjAiDiagnosisPanel.vue` | test:exec-evidence (9) | **Integrated** |
| E2E 完整流程 | `POST /submit` + `ai/diagnose` | 全链路 | 4 张新表 | — | test_e2e_oj_flow (3 fast + 8 slow) | **Integrated** |

> **First Divergence 算法覆盖度说明**：Integrated in AI diagnosis pipeline. Experimental algorithmic coverage: currently strongest for Python algorithms with comparable reference traces (AC submissions as reference). When no AC submission exists, returns null + reason (不伪造).

> **E2E 验证流程**：注册 → 提交 AC 参考解 → 提交错误代码 (WA) → AI 诊断 → 验证 `execution_evidence` / `counterexample` / `first_divergence` / `bug_record_id` / `trace_record_id` 非空 → 验证 4 张新表有真实 INSERT → 提交修复代码 (AC) → 验证 knowledge state 变化。

> **AC 不依赖 AI 诊断**：`api_submit` 直接调用 `update_knowledge_state(evidence_type="SUBMISSION_RESULT")`，学生 WA → 自己修改 → AC（不调用 ai_diagnose）仍然记录 attempt/success/mastery。

> **重复 Diagnosis 幂等**：`update_knowledge_state` 通过 `applied_evidence` 列表记录 `(submission_id, evidence_type)`，同一证据不重复应用。不同证据类型（SUBMISSION_RESULT / DIAGNOSIS_BUG / HINT_USAGE）可分别应用。`applied_evidence` 列由 Alembic 迁移 `20260812_0004` 添加，生产环境需执行 `alembic upgrade head`。

### 评测框架

```powershell
python -m evaluation.run_eval --json results.json --csv results.csv
```

覆盖 12 项指标：Bug 定位 Top-1/Top-3 准确率、Bug 分类准确率、反例 Bug Trigger Rate、AI Hallucination Rate、Evidence Coverage、Fix Success Rate、Hint Usage、Repeated Bug Rate、P50/P95/P99 延迟。详见 [evaluation/README.md](evaluation/README.md)。

## Core Workflow

```
登录 → 学习中心 → 打开算法题 → 提交真实错误代码
  → OJ 运行 → Wrong Answer → 失败测试用例 → Trace
  → First Divergence / 异常位置 → AI 证据化诊断
  → 分层提示 → 学生修改 → 再次提交 → Accepted
  → 学生知识状态更新 → 学习路径发生变化
```

整条流程使用真实系统能力，无 Demo Mode / 比赛专用模式 / 固定假数据。

## Security

- JWT 校验：生产环境拒绝不安全的默认 secret
- 代码执行安全：AST 静态分析熔断（system/popen/fork/exec/asm 黑名单）+ subprocess 列表参数（无 shell=True）+ 资源限制
- 数据归属：所有学生接口从 JWT 取 user_id，不接受客户端指定
- 内容安全：敏感词过滤 + Prompt 注入检测 + 虚构学术事实检测
- LLM 输出验证：JSON Schema 校验 + 有限重试 + 降级兜底

## Project Structure

```
algo/
├── backend/                 FastAPI 后端
│   ├── api/                 17 个路由模块
│   ├── services/
│   │   ├──     agents/          22 个多智能体节点
│   │   ├── orchestrator/    DAG 编排
│   │   ├── oj/              OJ + Trace + 诊断 + 反例
│   │   ├── evidence/        证据链 + Execution Evidence
│   │   ├── mastery/         掌握度模型
│   │   └── llm/             LLM 调用与验证
│   ├── models/              12 张表（含 4 张 Execution Evidence 表）
│   ├── schemas/             20 个 schema
│   ├── migrations/          Alembic 迁移（4 个版本）
│   └── tests/               pytest 测试（137 passed, 18 slow）
�%── frontend/               Vue 3 前端
│   └── src/
│       ├── views/           24 个页面
│       ├── components/      70+ 组件
│       └── utils/           40+ 工具模块（含 5 个 .test.ts）
└── evaluation/              系统评测框架（12 项指标）
```

## 数据归属

所有学生侧接口从 JWT 获取用户身份，服务端不接受客户端指定 `user_id`。学习进度、画像、资源、路径、学习记忆和事件日志均以数据库外键关联账号。退出登录时前端会清理本地学习缓存，避免同一设备切换账号时混入其他账号数据。

## Roadmap


- [ ] Docker 沙箱化代码执行环境
- [ ] 更多算法语言的 Trace 支持（Java）
- [ ] Property-based Testing 集成
- [ ] 教师端批量布置算法作业
- [ ] 知识图谱可视化交互优化

## License

项目自身授权方式以根目录 [LICENSE](LICENSE) 为准（专有协议，All Rights Reserved）。第三方开源依赖分别遵循各自许可证。

> 项目源代码托管于 GitHub 仓库，不代表项目自身采用标准开源协议。在未获得版权持有人书面许可前，不得复制、修改、分发、再许可或使用本软件及其源代码。
