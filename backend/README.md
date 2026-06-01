# AlgoPilot 后端 — 《数据结构与算法》课程个性化学习系统（FastAPI）

中国软件杯 **A3 赛道** 后端服务：为高校《数据结构与算法》课程提供 REST API，涵盖账号、学习进度、**多智能体编排**（画像、路径、资源生成、评估）、**课内在线评测（OJ）** 与 **Trace 智能辅导**。默认大模型为 **科大讯飞星火 Spark**（已接入 `services/llm`）。

## 环境要求

- Python **3.10–3.12**（推荐 [python.org](https://www.python.org/downloads/) **Windows 版 CPython**）
- **数据库**：默认 **SQLite**（`data/alp_learning.db`）。高并发场景可在 `.env` 中设置 `DATABASE_URL` 指向 MySQL（需自行安装 `pymysql` 并调整依赖）。
- MSYS2 / MinGW Python 可能缺少预编译轮子；请改用官方 CPython 并重建虚拟环境。

复制 `backend/.env.example` 为 `.env`，至少设置 `JWT_SECRET`。首次启动自动建表（`users`、`learning_progress` 等）。

## 安装依赖

```bash
cd backend
python -m venv .venv
```

**Windows（PowerShell）**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动服务

在 `backend` 目录执行：

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 9000
```

> Windows：端口 **7907–8006** 可能被系统保留，请使用 **9000**（与前端 `VITE_API_BASE_URL` 一致）。

- Swagger：<http://127.0.0.1:9000/docs>
- 健康检查：<http://127.0.0.1:9000/api/health>

### 演示数据预热（可选）

比赛演示前可一键写入 `a3_demo` 账号的画像、记忆、路径、掌握度与模板资源（**无需 LLM Key**）：

```bash
python backend/scripts/seed_a3_demo_data.py
```

默认账号：`a3_demo` / `Demo1234!`（仅更新该用户，幂等可重复执行）。

### 课内 OJ API（课程编程实践）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/oj/problems` | 课程题单列表 |
| `GET` | `/api/oj/problems/{slug}` | 题目详情 |
| `POST` | `/api/oj/problems/{slug}/run` | 运行样例（Python 3） |
| `POST` | `/api/oj/problems/{slug}/submit` | 提交判题（需 Bearer） |

详见 `docs/OJ.md`。更新题单后执行：`python scripts/build_oj_data.py`。

### 账号与学习进度

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/register` | 注册，返回 JWT |
| `POST` | `/api/auth/login` | 登录 |
| `GET` | `/api/me/learning-progress` | 读取进度（Bearer） |
| `PUT` | `/api/me/learning-progress` | 保存进度（Bearer） |

### 多智能体编排 API（`/api/orchestrator`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/persona/profile` | 学习画像（**六维** JSON + 分数） |
| `GET` | `/persona/history` | 画像对话历史 |
| `POST` | `/persona/chat` | **SSE 流式**画像对话（无 LLM Key 时模板降级） |
| `POST` | `/persona/sync-from-stored` | 从对话抽取画像 |
| `POST` | `/persona/patch-from-learning` | **随学随新**更新画像 |
| `POST` | `/resources/generate` | 单类资源生成 |
| `POST` | `/resources/generate-all` | **SSE** 批量生成（无 LLM Key 时模板降级，含 **8 类**资源） |
| `GET` | `/resources` | 资源列表 |
| `GET` | `/learning-path/plan` | 个性化路径 |
| `POST` | `/learning-path/replan` | 重排路径 |
| `GET` | `/resources/recommendations` | 按画像/路径推送资源 |
| `POST` | `/evaluation` | 学习效果评估 |
| `POST` | `/evaluation/oj-struggle` | OJ 受挫 → 路径巩固建议（OJ 页 **已实现自动触发**，连续 WA/RE/TLE/CE ≥3） |

`/api/ai/tutor/chat`、`/api/ai/oj/assistant` 经 **Orchestrator** 调度，禁止业务层直连 LLM。

### 知识库与内容安全

- **课程级知识库（A3 文档集）**：`knowledge/courses/data_structures_algorithms/`（`course_manifest.yaml` + 14 章 + 实验 + 项目 Markdown）
- 模块切片（兼容）：`knowledge_base/chunks.json`
- 课纲摘要：`knowledge_base/syllabus.json`
- RAG：`services/knowledge/retriever.py`（合并 legacy 切片与课程 Markdown 切片，BM25）
- 课程加载：`services/knowledge/course_loader.py`
- 过滤：`services/safety/content_filter.py`
- 校验：`services/agents/verifier.py`

竞赛文档：`docs/competition/README.md` · 根目录 `README.md`（赛题适配与演示闭环）。

### Learning SkillCard（算法学习技能卡）

- 技能卡 YAML：`services/skills/cards/`（13 张，含 DP/图 BFS/树遍历/二分等完整策略）
- 路由：`services/skills/skill_router.py`（按章节、模块、OJ 错误、Trace 摘要匹配）
- API：`GET /api/skills`、`GET /api/skills/{id}`、`POST /api/skills/route`
- 资源生成：`workflow.py` 将 `resource_strategy` / `hint_policy` / `common_mistakes` 注入 Agent 上下文；`meta.skill_card` 供前端展示

## 项目结构

| 路径 | 说明 |
|------|------|
| `main.py` | 应用入口 |
| `api/` | 路由（`orchestrator`、`oj`、`auth` 等） |
| `core/` | 配置与数据库 |
| `models/` | ORM |
| `schemas/` | Pydantic |
| `services/agents/` | 各 Agent |
| `services/orchestrator/` | 工作流编排 |
| `services/oj/` | 判题、Trace、AI 诊断 |
| `knowledge/courses/` | 课程级知识库（`data_structures_algorithms/` 等） |
| `knowledge_base/` | 检索切片产物（`chunks.json`、`syllabus.json`） |
| `data/` | SQLite（勿提交） |

## 后续扩展（可选）

- **LangGraph** 可视化编排（规划中，当前为自研 Orchestrator）
- **Docker** 判题进程隔离（可选部署，见 `docs/OJ.md`）
