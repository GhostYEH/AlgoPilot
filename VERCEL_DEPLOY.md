# Vercel + Railway 部署指南

## 🎯 部署方案

由于项目包含前端和后端，我们采用混合部署方案：
- **前端** → Vercel（快速、免费、无需绑卡）
- **后端** → Railway（免费、无需绑卡）

---

## 📋 前置准备

1. **GitHub 账号** - 代码已在 `https://github.com/GhostYEH/AlgoPilot_bushu.git`
2. **Vercel 账号** - 免费注册
3. **Railway 账号** - 免费注册（无需绑卡）

---

## 🚀 部署步骤

### 第一步：先部署后端（Railway）

按照 [RAILWAY_DEPLOY.md](file:///k:\A3\RAILWAY_DEPLOY.md) 中的步骤部署后端：

1. 访问 [railway.app](https://railway.app) 用 GitHub 登录
2. 创建项目，部署后端（详见 RAILWAY_DEPLOY.md）
3. 获得后端地址，例如：`https://algopilot-backend.up.railway.app`
4. 验证后端：访问 `https://你的后端地址/api/health`

**重要**：先完成后端部署，拿到后端地址后再部署前端！

### 第二步：部署前端（Vercel）

1. 访问 [vercel.com](https://vercel.com) 用 GitHub 账号登录
2. 点击 **"Add New"** → **"Project"**
3. 选择 `AlgoPilot_bushu` 仓库，点击 **"Import"**
4. 配置项目设置：
   - **Project Name**: `algopilot-frontend`
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. 点击 **"Environment Variables"**，添加环境变量：
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: `https://你的后端地址`（例如：`https://algopilot-backend.up.railway.app`）
6. 点击 **"Deploy"** 开始部署
7. 等待部署完成（约 2-5 分钟）
8. 部署完成后，你会获得一个 Vercel 地址，例如：`https://algopilot-frontend.vercel.app`

### 第三步：访问应用

点击 Vercel 提供的地址，就可以使用你的算法智能学习平台了！

---

## 💡 方案优势

### Vercel（前端）
- ✅ 完全免费
- ✅ 全球 CDN 加速，访问速度快
- ✅ 自动 HTTPS
- ✅ 自动部署（push 代码自动更新）
- ✅ 无需绑卡

### Railway（后端）
- ✅ 免费额度充足（每月 5 美元）
- ✅ 无需绑卡
- ✅ 支持 Docker
- ✅ 数据持久化

---

## 📚 更多资源

- [Vercel 官方文档](https://vercel.com/docs)
- [Railway 官方文档](https://docs.railway.app)
- [RAILWAY_DEPLOY.md](file:///k:\A3\RAILWAY_DEPLOY.md) - 后端部署详细指南
