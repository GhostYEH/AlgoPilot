# A3 比赛演示前检查清单

> 建议在正式答辩 / 录屏前 **15 分钟** 按序完成。全部打勾即可开始 7 分钟演示。

## 1. 环境启动

- [ ] 已执行 `docker compose up --build`（或本地 `backend` + `frontend` 双进程）
- [ ] 浏览器打开 http://localhost:8080 首页无白屏
- [ ] http://localhost:9000/api/health 返回 `status: ok`
- [ ] 健康检查中 `trace_python: true`（Python Trace 可用）
- [ ] 若 `trace_cpp: false`：**OJ 演示请选 Python 语言**，不要演示 C++ Trace

## 2. API Key 与可选服务

- [ ] **LLM（推荐）**：`.env` 中 `SPARK_API_PASSWORD` 已配置且非占位符
  - 未配置时：画像对话与 generate-all 走**模板降级**（非 503）；OJ Trace 诊断、学习路径启发式、掌握度评估仍可用
- [ ] **TTS（可选）**：未配置不影响演示；视频脚本分镜与 `tts_preview_text` 仍可展示
- [ ] **JWT**：生产/容器环境已修改默认 `JWT_SECRET`

## 3. 演示账号

- [ ] 已注册并登录演示账号（资源生成、掌握度、Memory 需登录）
- [ ] 或运行 `python backend/scripts/seed_a3_demo_data.py` 预热 `a3_demo` 演示数据（密码 `Demo1234!`）
- [ ] 或确认 `/a3-demo` 在未登录下可展示 mock 闭环（含「含演示数据」标签）

## 4. 七步演示路径（推荐顺序）

| 步骤 | 页面 | 检查点 |
|------|------|--------|
| 1 | 首页 `/` | 导航可见「比赛演示」 |
| 2 | `/a3-demo` | 无白屏；有 loading；后端不可用时有 warning + mock |
| 3 | 学习路径 · 画像 | 破冰对话或已有画像摘要 |
| 4 | 多智能体工作台 | 点击「启动个性化资源生成」；控制台有 Agent 日志 |
| 5 | OJ `/practice/reverse-linked-list` | **Python** 提交错误代码 → Trace → AI 诊断 → 智能辅导面板 |
| 6 | 我的学习 · 评估 | MasteryAgent 卡片有分数或「重试」按钮 |
| 7 | 资源库 | 资源带校验标签；Safety 面板可展开 |

## 5. 后端自检（可选，1 分钟）

```bash
curl http://localhost:9000/api/a3/health
py -3 -m pytest backend/tests -q
```

期望：health 返回 `status: ok`；pytest 以当前 CI / pytest 输出为准（不写死通过数）。

## 6. 前端构建自检（可选）

```bash
cd frontend && npm run typecheck
```

## 7. 常见故障快速处理

| 现象 | 处理 |
|------|------|
| 资源生成无 LLM Key | 工作台仍可走 generate-all 模板降级；配置 `SPARK_API_PASSWORD` 可启用完整多智能体生成 |
| TTS 试听失败 | 忽略，展示脚本分镜即可 |
| C++ Trace 400 | 切换语言为 Python |
| 演示页空白区块 | 刷新；或访问 `/a3-demo` 查看「含演示数据」fallback |
| OJ 列表为空 | 确认 `frontend/public/oj/bundle.json` 存在；后端离线会自动 fallback |

## 8. 答辩话术要点（30 秒）

1. **不是普通聊天**：OJ 辅导基于 Trace 执行轨迹 + SkillCard 分层提示  
2. **闭环**：错误 → 诊断 → 资源推荐 → Memory → Mastery → 路径调整  
3. **防幻觉**：ContentVerifier + SafetyAgent 结构化 evidence；trace_animation 跳过文本校验但 Safety 仍审查  
