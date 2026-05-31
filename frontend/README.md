# AlgoPilot 前端 — 《数据结构与算法》课程个性化学习系统

中国软件杯 **A3 赛道** 前端：Vue 3 + TypeScript + Vite + Element Plus，支撑 **六维学习画像**、**多智能体资源工作台**、**课程学习路径 DAG**、**多模态资源库**、**课内 OJ 与 Trace 智能辅导**、**学习效果评估** 等答辩演示页面。

## 环境要求

- Node.js 18+（推荐 LTS）

## 安装与启动

```bash
cd frontend
npm install
npm run dev
```

默认：<http://localhost:5173>

## 环境变量

复制 `.env.example` 为 `.env.development`：

| 变量名 | 说明 |
|--------|------|
| `VITE_API_BASE_URL` | 后端根地址，如 `http://127.0.0.1:9000` |

`vite.config.ts` 可配置 `/api` 开发代理，或依赖后端 CORS。

## 构建

```bash
npm run build
npm run preview
```

## 目录说明

| 目录 | 说明 |
|------|------|
| `src/views` | 首页、学习路径、资源库、我的学习、多智能体工作台、课内 OJ 等 |
| `src/layouts` | 主布局（含讯飞 Spark / TTS 标识） |
| `src/router` | 路由 |
| `src/components/persona` | 画像对话与雷达图 |
| `src/components/agents` | Agent 终端、资源仪表盘 |
| `src/components/oj/trace` | Trace 可视化 |
| `src/modules` | 各课程章节讲义与进度 |

## 与后端联调

启动后端后访问 `GET {VITE_API_BASE_URL}/api/health`。完整赛题演示路径见根目录 [README.md](../README.md#-比赛演示闭环)。

## 说明

- Web 标题仍可能显示历史名称「算法智能学习平台」，与 AlgoPilot 课程系统为同一产品。
- 科大讯飞星火与 TTS 能力由后端 API 提供；`SPARK_API_PASSWORD` 可选，未配置时画像与资源生成走模板降级。
