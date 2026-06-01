# Railway 免费部署指南（无需绑卡！）

## 🌟 为什么选择 Railway？

- ✅ **完全不需要绑定银行卡**
- ✅ 每月 **5 美元**免费额度
- ✅ 支持 Docker 部署
- ✅ 自动 HTTPS
- ✅ 简单易用

---

## 📋 前置准备

1. **GitHub 账号** - 代码已推送到 `https://github.com/GhostYEH/AlgoPilot_bushu.git`
2. **Railway 账号** - 免费注册即可

---

## 🚀 部署步骤

### 第一步：注册 Railway 账号

1. 访问 [railway.app](https://railway.app)
2. 点击 **"Login"**，使用 GitHub 账号登录（无需绑卡！）

### 第二步：部署后端

1. 登录后，点击 **"New Project"**
2. 选择 **"Deploy from GitHub repo"**
3. 连接你的 GitHub 账户，选择 `AlgoPilot_bushu` 仓库
4. 点击 **"Deploy Now"**
5. 现在需要配置部署设置：
   - 点击 **"Variables"** 标签，添加以下环境变量：
     - `JWT_SECRET`: 点击 **"Add"** → 输入一个随机字符串（或者用在线生成器生成）
     - `JWT_EXPIRE_MINUTES`: `10080`
     - `DATABASE_URL`: `sqlite:////app/data/alp_learning.db`
     - `SPARK_MODEL`: `lite`
     - `SPARK_API_PASSWORD`: （可选，留空即可）
   - 点击 **"Settings"** 标签：
     - **Name**: `algopilot-backend`
     - **Root Directory**: `backend`
     - **Dockerfile Path**: `Dockerfile`
     - **Port**: `9000`
6. 点击 **"Deploy"** 开始部署
7. 等待部署完成（约 5-10 分钟）
8. 部署完成后，点击 **"Settings"** → **"Generators"** → **"Public Networking"**，点击 **"Generate Domain"** 获得后端地址，例如：`https://algopilot-backend.up.railway.app`

**验证后端是否正常工作**：
访问 `https://你的后端地址/api/health`，应该能看到 JSON 响应。

### 第三步：部署前端

1. 在 Railway 项目页面，点击 **"New"** → **"Service"**
2. 再次选择 `AlgoPilot_bushu` 仓库
3. 配置部署设置：
   - 点击 **"Variables"** 标签，添加环境变量：
     - `VITE_API_BASE_URL`: `https://你的后端地址`（例如：`https://algopilot-backend.up.railway.app`）
   - 点击 **"Settings"** 标签：
     - **Name**: `algopilot-frontend`
     - **Root Directory**: `frontend`
     - **Dockerfile Path**: `Dockerfile.render`
     - **Port**: `80`
4. 点击 **"Deploy"** 开始部署
5. 等待部署完成（约 5-10 分钟）
6. 部署完成后，点击 **"Settings"** → **"Generators"** → **"Public Networking"**，点击 **"Generate Domain"** 获得前端地址

### 第四步：访问你的应用

点击前端地址，就可以使用你的算法智能学习平台了！

---

## 💡 Railway 免费计划说明

- **免费额度**：每月 5 美元
- **使用量**：两个服务（后端+前端）每月约 2-3 美元，完全在免费额度内
- **休眠**：如果 15 分钟没有请求，服务会休眠（首次访问会有 10-30 秒的冷启动）

---

## 🔧 故障排查

### 后端部署失败
- 检查 Railway 的日志（服务详情页的 **Logs** 标签）
- 确保环境变量配置正确

### 前端无法连接后端
- 检查 `VITE_API_BASE_URL` 环境变量是否正确设置
- 确保后端服务正在运行

---

## 📚 更多资源

- [Railway 官方文档](https://docs.railway.app)
- [Railway 定价说明](https://railway.app/pricing)
