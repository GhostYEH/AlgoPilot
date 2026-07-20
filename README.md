# AlgoPilot

> AlgoPilot（算法领航员）是一个基于科大讯飞星火大模型、多智能体协同、个性化学习路径和代码 Trace 诊断的《数据结构与算法》智能学习平台。

## 项目一句话介绍

AlgoPilot 面向《数据结构与算法》课程，提供对话式学生画像、个性化学习路径、多智能体资源生成、OJ 判题与 Trace 可视化诊断、AI 辅导与教师学情看板。系统通过 BM25 RAG 检索、内容校验、安全审查和有限重试等机制，降低大模型生成幻觉和不合规内容的风险。

## 核心学习闭环

```
对话式学生画像
  → 个性化学习路径
  → 多智能体资源生成
  → OJ 与 Trace 诊断
  → 掌握度评估
  → 路径动态调整
```

## 资源类型

系统支持 **5 种资源类型**：4 类 A3 核心展示资源 + 1 类扩展资源。

| 类型 | Agent | 说明 |
|------|-------|------|
| 个性化课程讲解文档 | ConceptAgent | A3 核心资源 |
| 知识点思维导图 | GraphAgent | A3 核心资源 |
| 代码实操案例 | ScenarioAgent | A3 核心资源 |
| Trace 执行动画 | TraceAgent | A3 核心资源 |
| 分层拓展阅读 | ReadingAgent | 扩展资源 |

批量生成按四阶段并行拓扑执行：

```
Phase 1：document
Phase 2：mindmap
Phase 3：code_case
Phase 4：trace_animation ∥ reading
```

## 多智能体节点

系统注册 21 个多智能体协作节点，其中 19 个已实现，PptAgent、VideoScriptAgent 为规划中扩展节点（仅注册，未实现）。分属 6 个 layer：profiling / resource / path / tutor / safety / eval。编排框架借鉴状态图与 DAG 编排思想，自主实现轻量级多智能体工作流（零 langgraph 依赖）。

## 系统截图

真实系统截图将在最终比赛版本冻结后补充，截图清单见：

- [文档和ppt/05_AlgoPilot用户操作手册.docx](文档和ppt/05_AlgoPilot用户操作手册.docx)

## 快速启动

### Windows 一键启动

```powershell
.\start.bat
```

### 手动启动后端

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 9000
```

### 手动启动前端

```powershell
cd frontend
npm install
npm run dev
```

访问 http://127.0.0.1:5173（开发）或 http://127.0.0.1:9000（打包）。

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
npm run test:oj-struggle
npm run test:path-replan-diff
npm run test:graph-module
npm run test:structured-json
```

### 测试状态

| 项目 | 状态 |
|------|------|
| Backend pytest | 241 passed（2026-07-19 本地执行，154.18s） |
| Frontend typecheck | passed |
| Frontend build | passed（3.10s） |
| Frontend test:oj-struggle | passed |
| Frontend test:path-replan-diff | passed |
| Frontend test:graph-module | passed |
| Frontend test:structured-json | passed |

> 上述测试结果基于 2026-07-19 本地真实执行（Windows 11 / Python 3.13.7 / Node.js 25.8.1 / npm 11.11.0）。项目 CI 使用 Python 3.11 + Node.js 22，并覆盖后端 ruff/pytest、前端 typecheck/build 与 4 个脚本；远端运行状态以 GitHub Actions 为准。

## 比赛文档

- [01 项目说明书](文档和ppt/01_AlgoPilot项目说明书.docx)
- [02 系统开发说明书](文档和ppt/02_AlgoPilot系统开发说明书.docx)
- [03 测试说明书](文档和ppt/03_AlgoPilot测试说明书.docx)
- [05 用户操作手册](文档和ppt/05_AlgoPilot用户操作手册.docx)
- [AlgoPilot 软件杯答辩 PPT（v1.3）](文档和ppt/AlgoPilot_软件杯答辩_评委视角优化版_v1.3.pptx)

更多技术说明见 `backend/docs/`。

## 授权说明

项目自身授权方式以根目录 [LICENSE](LICENSE) 为准（专有协议，All Rights Reserved）。第三方开源依赖分别遵循各自许可证，详见 [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)。

> 项目源代码托管于 GitHub 仓库，不代表项目自身采用标准开源协议。在未获得版权持有人书面许可前，不得复制、修改、分发、再许可或使用本软件及其源代码。
