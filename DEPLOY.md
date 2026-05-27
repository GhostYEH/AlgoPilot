# Docker 部署指南

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

复制环境变量模板：

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置（至少修改 `JWT_SECRET`）：

```env
# 必填：JWT 密钥，生产环境请使用强随机字符串
JWT_SECRET=your-very-secret-jwt-key-change-this-in-production

# 可选：会话过期时间（分钟），默认 7 天
JWT_EXPIRE_MINUTES=10080

# 可选：数据库连接，默认使用 SQLite
DATABASE_URL=sqlite:///./data/alp_learning.db

# 可选：讯飞星火 API，用于画像、资源生成、AI 诊断
SPARK_API_PASSWORD=your-spark-api-password
SPARK_MODEL=lite
```

### 3. 启动服务

```bash
docker compose up --build
```

首次启动会自动构建镜像，需要 5-10 分钟（取决于网络速度）。

### 4. 访问应用

| 服务 | 地址 |
|------|------|
| **前端** | http://localhost:8080 |
| **后端 API** | http://localhost:9000 |
| **健康检查** | http://localhost:9000/api/health |

## 📁 项目结构

```
AlgoPilot/
├── docker-compose.yml      # Docker Compose 配置
├── .env.example            # 环境变量模板
├── backend/
│   └── Dockerfile          # 后端镜像
├── frontend/
│   └── Dockerfile          # 前端镜像
└── README.md               # 项目说明
```

## 🔧 常用命令

### 启动服务

```bash
# 构建并启动
docker compose up --build

# 后台启动
docker compose up -d --build
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 停止服务

```bash
# 停止并保留数据
docker compose down

# 停止并删除所有数据（谨慎使用）
docker compose down -v
```

### 重启服务

```bash
docker compose restart
```

### 进入容器

```bash
# 进入后端容器
docker compose exec backend bash

# 进入前端容器
docker compose exec frontend sh
```

## 🎯 功能说明

### 基础功能（无需 API Key）

- ✅ 用户注册与登录
- ✅ 学习路径可视化
- ✅ OJ 样题浏览与运行（Python）
- ✅ 代码执行轨迹可视化（Python）
- ✅ 资源库浏览
- ✅ 主题切换

### 高级功能（需要配置 `SPARK_API_PASSWORD`）

- 🎯 破冰对话与六维画像生成
- 📚 个性化资源生成（讲解文档、思维导图、练习题、剧情沙盒、轨迹动画）
- 🔍 多智能体协作与终端展示
- 📊 AI 错题诊断
- 💬 智能助教对话
- 🔍 语义搜索

## 📊 数据持久化

用户数据通过 Docker Volume 持久化存储：

- `backend_data` 卷：存储 SQLite 数据库

即使删除容器，数据也会保留。如需完全重置数据：

```bash
docker compose down -v
```

## 🔒 安全说明

1. **生产环境**请务必修改 `JWT_SECRET` 为强随机字符串
2. 不要将 `.env` 文件提交到 Git（已在 `.gitignore` 中排除）
3. 生产环境建议使用 PostgreSQL/MySQL 替代 SQLite
4. 建议配置反向代理（Nginx）与 HTTPS

## 🛠️ 故障排查

### 端口被占用

如果 `8080` 或 `9000` 端口被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8081:80"    # 改为其他端口
  - "9001:9000"  # 改为其他端口
```

### 构建失败

清理 Docker 缓存并重新构建：

```bash
docker system prune -a
docker compose build --no-cache
```

### 后端健康检查失败

查看后端日志排查问题：

```bash
docker compose logs backend
```

### C++ 功能受限

Docker 容器中已安装 `g++` 和 `gdb`，C++ 功能应该可以正常使用。如遇问题，检查后端日志。

## 📚 更多文档

- [项目 README](./README.md) - 完整项目介绍
- [后端架构文档](./backend/docs/MULTI_AGENT_ARCHITECTURE.md) - 多智能体架构说明
- [Trace 可视化协议](./backend/docs/trace_viz_schema.md) - 轨迹可视化数据格式

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

详见 [README](./README.md)。
