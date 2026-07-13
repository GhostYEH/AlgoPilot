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

系统支持 **6 种资源类型**：5 类 A3 核心展示资源 + 1 类扩展资源。

| 类型 | Agent | 说明 |
|------|-------|------|
| 个性化课程讲解文档 | ConceptAgent | A3 核心资源 |
| 知识点思维导图 | GraphAgent | A3 核心资源 |
| 分层练习题 | QuizAgent | A3 核心资源 |
| 代码实操案例 | ScenarioAgent | A3 核心资源 |
| Trace 执行动画 | TraceAgent | A3 核心资源 |
| 分层拓展阅读 | ReadingAgent | 扩展资源 |

批量生成按四阶段并行拓扑执行：

```
Phase 1：document
Phase 2：mindmap ∥ exercises
Phase 3：code_case
Phase 4：trace_animation ∥ reading
```

## 多智能体节点

系统注册 22 个多智能体协作节点，其中 20 个已实现，PptAgent、VideoScriptAgent 为规划中扩展节点（仅注册，未实现）。分属 6 个 layer：profiling / resource / path / tutor / safety / eval。编排框架借鉴状态图与 DAG 编排思想，自主实现轻量级多智能体工作流（零 langgraph 依赖）。

## 系统截图

真实系统截图将在最终比赛版本冻结后补充，截图清单见：

- [docs/submission/05_用户操作手册.md](docs/submission/05_用户操作手册.md)

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
```

### 测试状态

| 项目 | 状态 |
|------|------|
| Backend pytest | 188 passed |
| Frontend typecheck | passed |
| Frontend build | passed |

> 上述测试结果基于本次本地真实执行。GitHub Actions CI 状态以实际工作流运行结果为准。

## 比赛文档

- [01 项目说明书](docs/submission/01_项目说明书.md)
- [02 系统开发说明书](docs/submission/02_系统开发说明书.md)
- [03 测试说明书](docs/submission/03_测试说明书.md)
- [04 部署说明书](docs/submission/04_部署说明书.md)
- [05 用户操作手册](docs/submission/05_用户操作手册.md)
- [06 第三方开源依赖与 AI Coding 使用说明](docs/submission/06_开源与AI_Coding说明.md)
- [00 提交前检查清单](docs/submission/00_提交前检查清单.md)

更多技术说明见 `backend/docs/`。

## 授权说明

项目自身授权方式以根目录 [LICENSE](LICENSE) 为准（专有协议，All Rights Reserved）。第三方开源依赖分别遵循各自许可证，详见 [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) 与 [docs/submission/06_开源与AI_Coding说明.md](docs/submission/06_开源与AI_Coding说明.md)。

> 项目源代码托管于 GitHub 仓库，不代表项目自身采用标准开源协议。在未获得版权持有人书面许可前，不得复制、修改、分发、再许可或使用本软件及其源代码。
