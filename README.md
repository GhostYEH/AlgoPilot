# 算法智能学习平台

软件杯 A3 赛道 — 多智能体个性化学习系统。

## 目录结构

| 目录 | 说明 |
|------|------|
| [`backend/`](backend/) | FastAPI 后端、多智能体编排、OJ 判题 |
| [`frontend/`](frontend/) | Vue 3 + Vite 前端 |

## 快速启动

**后端**（默认端口 9000）：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1   # 若无虚拟环境：python -m venv .venv
pip install -r requirements.txt
copy .env.example .env           # 配置 JWT_SECRET、SILICONFLOW_API_KEY 等
uvicorn main:app --reload --host 127.0.0.1 --port 9000
```

**前端**（默认 <http://localhost:5173>）：

```powershell
cd frontend
npm install
npm run dev
```

也可在仓库根目录执行 `start.bat`（会打开 backend / frontend 两个窗口）。

## 迁移说明

若仍存在旧目录 `algorithm-learning-platform-backend`、`algorithm-learning-platform-frontend`：

1. 关闭占用它们的终端、IDE 与 dev 服务；
2. 确认 `backend/`、`frontend/` 可正常使用后，手动删除上述两个旧文件夹。

（当前 `backend\.venv`、`frontend\node_modules` 可能通过联接指向旧目录，删除旧目录前请先在新目录执行 `pip install` / `npm install`。）
