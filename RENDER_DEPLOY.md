# Render 免费部署指南

## 📋 前置准备

1. **GitHub 账号** - 用于托管代码
2. **Render 账号** - 免费注册即可

---

## 🚀 部署步骤

### 第一步：将代码推送到 GitHub

1. 在 GitHub 上创建一个新仓库（公开或私有都可以）
2. 在本地项目目录执行：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

### 第二步：部署后端

1. 访问 [Render.com](https://render.com) 并注册/登录
2. 点击右上角的 **"New +"** → 选择 **"Blueprint"**
3. 连接你的 GitHub 账户，授权 Render 访问你的仓库
4. 选择你的仓库，Render 会自动检测 `render.yaml` 文件
5. 确认服务名称为 `algopilot-backend`，点击 **"Apply"**
6. 等待部署完成（约 5-10 分钟）
7. 部署完成后，你会获得一个后端 URL，例如：`https://algopilot-backend.onrender.com`

**验证后端是否正常工作**：
访问 `https://你的后端地址/api/health`，应该能看到 JSON 响应。

### 第三步：部署前端

1. 在 Render 点击 **"New +"** → 选择 **"Web Service"**
2. 再次选择你的 GitHub 仓库
3. 填写配置：
   - **Name**: `algopilot-frontend`
   - **Region**: 选择离你近的区域
   - **Branch**: `main`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./frontend/Dockerfile.render`
   - **Docker Context**: `./frontend`
   - **Plan**: `Free`

4. 点击 **"Advanced"**，添加环境变量：
   - 键：`VITE_API_BASE_URL`
   - 值：`https://你的后端地址`（例如：`https://algopilot-backend.onrender.com`）

5. 点击 **"Create Web Service"**
6. 等待部署完成（约 5-10 分钟）

### 第四步：访问你的应用

部署完成后，Render 会给你一个前端地址，例如：`https://algopilot-frontend.onrender.com`

访问这个地址，你就可以使用你的算法智能学习平台了！

---

## 💡 注意事项

### 免费计划限制

- 每个免费服务每月有 **750 小时**的运行时间（足够 24/7 运行）
- 如果 15 分钟没有请求，服务会自动休眠（首次访问会有 30-60 秒的冷启动时间）
- 免费计划有 512MB RAM 和 0.1 CPU 的限制

### 数据持久化

- 后端数据已通过磁盘挂载持久化存储
- 不要担心重启服务后数据丢失

### 环境变量

如果需要启用 LLM 功能（AI 辅导），可以在后端服务中添加环境变量：
- `SPARK_API_PASSWORD`: 你的星火 API 密钥

---

## 🔧 故障排查

### 后端部署失败
- 检查 Render 的日志（服务详情页的 **Logs** 标签）
- 确保 `requirements.txt` 中的依赖正确

### 前端无法连接后端
- 检查 `VITE_API_BASE_URL` 环境变量是否正确设置
- 确保后端服务正在运行
- 访问后端的 `/api/health` 确认后端正常

### 服务休眠问题
- 可以使用 [UptimeRobot](https://uptimerobot.com) 等免费服务定期 ping 你的应用，防止休眠

---

## 📚 更多资源

- [Render 官方文档](https://render.com/docs)
- [Render 免费计划说明](https://render.com/docs/free)
