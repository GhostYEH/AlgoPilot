# AlgoPilot

AlgoPilot 是面向《数据结构与算法》课程的智能学习平台，提供账号级学习记录、动态学习画像、个性化路径、多智能体资源生成、在线 OJ、Trace 诊断和教师教学看板。

## 核心能力

- 学习进度、游戏记录、OJ 行为、Trace 诊断和学习事件按用户账号持久化。
- ProfilingAgent、LearningPathAgent、资源角色 Agent、ContentVerifierAgent、SafetyAgent、MasteryAgent 协同工作。
- AI 助教与资源生成会读取当前账号的画像、近期学习证据、薄弱模式和掌握度。
- 教师看板仅允许教师账号访问，并只聚合数据库中的真实学生记录。
- Python 与 C++ 在线判题；Python Trace 默认可用，C++ Trace 需要本机安装 `g++` 和 `gdb`。

## 快速启动

Windows 可直接运行：

```powershell
.\start.bat
```

手动启动后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 9000
```

手动启动前端：

```powershell
cd frontend
npm install
npm run dev
```

## 配置

复制 `backend/.env.example` 为 `backend/.env`，至少设置：

```dotenv
JWT_SECRET=请替换为长随机字符串
SPARK_API_PASSWORD=你的星火_APIPassword
```

默认数据库位于 `backend/data/alp_learning.db`。生产环境应使用强随机 `JWT_SECRET`、受控 CORS 来源、定期备份和反向代理 HTTPS。

## 数据归属

所有学生侧接口从 JWT 获取用户身份，服务端不接受客户端指定 `user_id`。学习进度、画像、资源、路径、学习记忆和事件日志均以数据库外键关联账号。退出登录时前端会清理本地学习缓存，避免同一设备切换账号时混入其他账号数据。

## 验证

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest

cd ..\frontend
npm run typecheck
npm run build
```

更多技术说明见 `backend/docs/`。
