# 算法智能学习平台 — 前端（Vue3 + Vite + Element Plus + TypeScript）

面向软件杯的算法个性化学习平台前端，采用组合式 API（`<script setup>`），Element Plus **按需引入**（`unplugin-vue-components` + `unplugin-auto-import`）。

## 环境要求

- Node.js 18+（推荐 LTS）

## 安装与启动

```bash
cd frontend
npm install
npm run dev
```

默认开发服务器：<http://localhost:5173>

## 环境变量

复制 `.env.example` 为 `.env.development`（仓库已提供示例），配置后端地址：

| 变量名 | 说明 |
|--------|------|
| `VITE_API_BASE_URL` | 后端 API 根地址，如 `http://127.0.0.1:8000` |

`vite.config.ts` 中已配置 `/api` 开发代理（可选），也可依赖后端 CORS 直连。

## 构建

```bash
npm run build
npm run preview
```

## 目录说明

| 目录 | 说明 |
|------|------|
| `src/views` | 页面视图（首页、学习路径、资源库、我的学习等） |
| `src/layouts` | 布局（顶栏 + 内容区） |
| `src/router` | Vue Router 配置 |
| `src/components` | 公共组件（按需添加） |
| `src/utils` | 工具与常量（含 Axios 封装 `request.ts`） |
| `src/assets` | 静态资源与全局样式 |

## 与后端联调

启动后端后，首页「后端联调」标签应显示 `/api/health` 正常；接口路径：`GET {VITE_API_BASE_URL}/api/health`。

## 后续扩展点（代码内亦有中文注释）

- 多智能体对话与 LangChain 编排页面
- 科大讯飞星火大模型 API 对接
- 用户鉴权与请求头 Token 注入（见 `src/utils/request.ts`）
