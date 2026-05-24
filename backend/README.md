# 算法智能学习平台 — 后端（FastAPI）

软件杯算法学习平台后端服务，提供 REST API（账号、学习进度、健康检查），后续可接入 LangChain 多智能体与科大讯飞星火大模型。

## 环境要求

- Python **3.10–3.12**（推荐从 [python.org](https://www.python.org/downloads/) 安装 **Windows 版 CPython**）
- **数据库**：默认 **SQLite**（单文件 `data/alp_learning.db`，无需安装 MySQL）。若需高并发或团队共用库，可在 `.env` 中设置 `DATABASE_URL` 指向 **MySQL**（需自行安装 `pymysql` 并调整依赖）。
- 若使用 MSYS2 / MinGW 自带的 Python，可能缺少 `pydantic-core` 等预编译轮子，导致 `pip install` 失败；请改用官方 CPython 并重新创建虚拟环境。

复制 `backend/.env.example` 为 `.env`，至少设置 `JWT_SECRET`（可选覆盖 `DATABASE_URL`）。应用首次启动时会根据 ORM 自动建表（`users`、`learning_progress`）。

## 安装依赖

建议使用虚拟环境：

```bash
cd backend
python -m venv .venv
```

**Windows（PowerShell，CPython 虚拟环境默认使用 `Scripts` 目录）**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**若仅有 `venv\bin\python.exe`（部分 MinGW 环境）**

```powershell
.\.venv\bin\python.exe -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动服务

在后端项目根目录执行（保证当前目录为 `backend`，以便默认 SQLite 路径一致）：

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 9000
```

> **Windows 提示**：部分环境（Hyper-V / WSL 等）会保留 TCP 端口 **7907–8006**，在此区间内使用 `--port 8000` 会报 `[winerror 10013]` 并立刻退出。请改用 **9000**（与前端 `.env.development` 中 `VITE_API_BASE_URL` 一致）。

启动后访问：

- Swagger 文档：<http://127.0.0.1:9000/docs>
- 健康检查：<http://127.0.0.1:9000/api/health>（应返回 `{"status":"ok"}`）

### 在线 OJ API（摘要）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/oj/problems` | 题库列表 |
| `GET` | `/api/oj/problems/{slug}` | 题目详情 |
| `POST` | `/api/oj/problems/{slug}/run` | 运行样例（Python 3） |
| `POST` | `/api/oj/problems/{slug}/submit` | 提交判题（需 Bearer） |

详见 `docs/OJ.md`。首次使用或更新课程题单后请执行：`python scripts/build_oj_data.py`。

### 账号与学习进度 API（摘要）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/register` | 注册（JSON：`username`、`password`，可选 `email`），返回 JWT |
| `POST` | `/api/auth/login` | 登录，返回 JWT |
| `GET` | `/api/me/learning-progress` | 需 `Authorization: Bearer <token>`，读取个人进度 JSON |
| `PUT` | `/api/me/learning-progress` | 需 Bearer，请求体 `{ "payload": { ... } }` 覆盖保存 |

### 把项目发给别人时

- 代码里**不包含**你的 `data/alp_learning.db`（已在 `.gitignore`）。对方克隆/解压后执行 `pip install` 与 `uvicorn`，会**自动生成新的空库**。
- 若需要连**同一套数据**，把 `data/alp_learning.db` 文件单独拷贝给对方对应目录即可（注意账号与隐私）。

## 项目结构

| 路径 | 说明 |
|------|------|
| `main.py` | 应用入口：中间件、路由挂载、启动时建表 |
| `api/` | 接口模块（`health`、`auth`、`learning` 等） |
| `core/` | 配置与数据库引擎、会话 |
| `models/` | ORM（`db_models.py`）等 |
| `schemas/` | Pydantic 请求/响应模型 |
| `utils/` | 安全（密码哈希、JWT）等 |
| `data/` | 默认 SQLite 文件目录（自动生成，勿提交仓库） |

### 多智能体编排 API（`/api/orchestrator`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/persona/profile` | 需 Bearer，读取学习画像（7 维 JSON） |
| `GET` | `/persona/history` | 需 Bearer，画像对话历史 |
| `POST` | `/persona/chat` | 需 Bearer，**SSE 流式**画像对话 |
| `POST` | `/persona/sync-from-stored` | 需 Bearer，从对话抽取画像入库 |
| `POST` | `/resources/generate` | 需 Bearer，单类资源生成 |
| `POST` | `/resources/generate-all` | 需 Bearer，**SSE** 批量生成六类资源 |
| `GET` | `/resources` | 需 Bearer，资源列表 |
| `GET` | `/learning-path/plan` | 需 Bearer，读取已保存的个性化路径 |
| `POST` | `/learning-path/replan` | 需 Bearer，根据画像+进度重排路径 |
| `POST` | `/persona/patch-from-learning` | 需 Bearer，随学随新更新画像 |
| `GET` | `/resources/recommendations` | 需 Bearer，按画像/路径推送资源 |
| `POST` | `/evaluation` | 需 Bearer，学习效果评估 |

原有 `/api/ai/tutor/chat`、`/api/ai/oj/assistant` 已改为经 **Orchestrator** 调度，禁止 API 直连 LLM。

### 知识库与内容安全

- 课程知识库：`knowledge_base/chunks.json`
- RAG：`services/knowledge/retriever.py`
- 内容过滤：`services/safety/content_filter.py`
- 生成校验：`services/agents/verifier.py`

竞赛文档索引：`docs/competition/README.md`。

## 后续扩展点

- 讯飞星火 API 替换 `services/llm` 实现（编排层接口不变）
- LangGraph 可视化编排（可选）
