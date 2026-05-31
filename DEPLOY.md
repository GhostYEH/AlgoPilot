# Docker 部署指南 — AlgoPilot（《数据结构与算法》课程系统）

## 📋 前置要求

- Docker Desktop（推荐）或 Docker Engine + Docker Compose
- 至少 4GB 可用内存
- 至少 5GB 可用磁盘空间

## 🚀 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/GhostYEH/AlgoPilot.git
cd AlgoPilot
```

### 2. 配置环境变量（可选但推荐）

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env`（至少修改 `JWT_SECRET`）：

```env
JWT_SECRET=your-very-secret-jwt-key-change-this-in-production
JWT_EXPIRE_MINUTES=10080
DATABASE_URL=sqlite:///./data/alp_learning.db
SPARK_API_PASSWORD=your-spark-api-password
SPARK_MODEL=lite
```

### 3. 启动服务

```bash
docker compose up --build
```

首次构建约 5–10 分钟。

### 4. 访问应用

| 服务 | 地址 |
|------|------|
| **前端** | http://localhost:8080 |
| **后端 API** | http://localhost:9000 |
| **健康检查** | http://localhost:9000/api/health |

健康检查返回示例如下（可用于演示前预检）：

```json
{
  "status": "ok",
  "llm_configured": true,
  "tts_configured": false,
  "trace_python": true,
  "trace_cpp": true,
  "demo_hints": []
}
```

## 🏆 A3 比赛演示推荐启动方式

### 方式一：Docker（答辩现场推荐）

```bash
cp .env.example .env
# 编辑 .env：至少改 JWT_SECRET；演示资源生成需 SPARK_API_PASSWORD
docker compose up --build
```

1. 打开 http://localhost:8080 → 导航 **「比赛演示」** → `/a3-demo`
2. 注册/登录演示账号
3. 按页面 **「开始 7 分钟演示」** Stepper 逐步跳转

### 方式二：本地双进程（开发调试）

```bash
# 终端 1 — 后端
cd backend
py -3 -m uvicorn main:app --reload --port 9000

# 终端 2 — 前端
cd frontend
npm run dev
```

访问 http://localhost:5173（Vite 开发服），API 默认代理到 9000。

### 演示能力矩阵

| 能力 | 无 LLM Key | 有 LLM Key | 无 TTS | 无 C++ 环境 |
|------|------------|------------|--------|-------------|
| 首页 / A3 演示页 | ✅ mock fallback | ✅ 真实数据 | ✅ | ✅ |
| Python OJ + Trace | ✅ | ✅ | — | ✅ |
| C++ Trace | — | — | — | ❌ 请改 Python |
| OJ AI 诊断 | ✅ 规则 fallback | ✅ LLM 增强 | — | ✅ |
| 画像对话 / 资源 generate-all | ✅ 模板降级 | ✅ LLM 增强 | ✅ 脚本可展示 | ✅ |
| 掌握度 / Memory / Events | ✅ | ✅ | — | ✅ |
| 视频脚本分镜 | ✅ 文本 | ✅ | ✅ | ✅ |
| TTS 试听 | — | — | ❌ 友好提示 | — |

完整检查项见 **[DEMO_CHECKLIST.md](./DEMO_CHECKLIST.md)**。

### 演示前快速验证

```bash
# 后端 70 项测试
py -3 -m pytest backend/tests -q

# 前端类型检查
cd frontend && npm run typecheck
```


```
AlgoPilot/
├── docker-compose.yml
├── .env.example
├── backend/
├── frontend/
└── README.md          # 赛题适配、课程场景、演示闭环
```

## 🔧 常用命令

```bash
docker compose up -d --build    # 后台启动
docker compose logs -f backend  # 查看日志
docker compose down             # 停止
docker compose down -v          # 停止并删除数据卷
```

## 🎯 功能说明

### 基础功能（无需 API Key）

- 用户注册与登录
- 《数据结构与算法》学习路径与章节讲义浏览
- 课内 OJ 样题运行（Python）、Trace 可视化（Python）
- 资源库浏览、主题切换

### 高级功能（配置 `SPARK_API_PASSWORD` 为 LLM 增强）

- 六维学习画像对话（无 Key 时 `TemplatePersonaFallbackAgent` 模板降级）
- 多智能体个性化资源生成（无 Key 时 `TemplateFallbackAgent` 模板降级）
- 智能辅导 LLM 增强（模块助教、OJ 思路提示、Trace + AI 诊断；规则兜底始终可用）
- 学习效果评估与路径重排

### 无 Key 仍可演示（比赛 fallback）

- `/a3-demo` 演示仪表盘：字段级 mock + `/api/health` 提示
- Python OJ / Trace + AI 诊断规则兜底
- 学习路径启发式规划、MasteryAgent / StudentMemory API
- 视频脚本 JSON 分镜（TTS 未配置时仅文本展示）

### 演示闭环 API

| API | 说明 |
|-----|------|
| `GET /api/health` | LLM / TTS / Trace 子系统就绪 |
| `GET /api/oj/capabilities` | OJ 判题与 Trace 能力 |
| `GET /api/mastery/report` | 掌握度报告 |
| `GET /api/memory/summary` | 学习记忆摘要 |
| `GET /api/events/recent` | Agent 协作事件链 |
| `POST /api/skills/route` | SkillCard 路由 |

## 📊 数据持久化

- `backend_data` 卷：SQLite 数据库

重置数据：`docker compose down -v`

## 🔒 安全说明

1. 生产环境请使用强随机 `JWT_SECRET`
2. 勿将 `.env` 提交到 Git
3. 生产环境可选用 PostgreSQL/MySQL 替代 SQLite（需自行配置 `DATABASE_URL`）
4. 建议 Nginx 反向代理 + HTTPS
5. **Docker 判题进程隔离**：当前为子进程 + 静态规则；容器级强隔离为**可选部署增强**（见 `backend/docs/OJ.md`）

## 🛠️ 故障排查

- **端口占用**：修改 `docker-compose.yml` 端口映射
- **构建失败**：`docker system prune -a` 后 `docker compose build --no-cache`
- **后端不健康**：`docker compose logs backend`
- **C++ Trace**：镜像内已含 `g++` / `gdb`；Windows 本地无 MinGW 时请用 **Python** 演示 Trace
- **LLM 未配置**：画像与 generate-all 走模板降级；检查 `SPARK_API_PASSWORD` 可启用完整 LLM 生成
- **TTS 503**：不影响视频脚本展示，仅试听不可用
- **演示页空白**：访问 `/a3-demo` 应自动补全 mock；查看 `/api/health` 的 `demo_hints`

## 📚 更多文档

- [演示前检查清单](./DEMO_CHECKLIST.md)

- [项目 README](./README.md) — A3 赛题定位、演示闭环、快速开始
- [后端 README](./backend/README.md) — API 与知识库
- [多智能体架构](./backend/docs/MULTI_AGENT_ARCHITECTURE.md)
- [竞赛文档索引](./backend/docs/competition/README.md)
- [Trace 协议](./backend/docs/trace_viz_schema.md)

## 📄 许可证

详见 [README](./README.md)。
