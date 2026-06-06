# A3 比赛演示数据种子 · 使用指南

## 快速开始

```bash
# 1. 确保后端虚拟环境已激活
cd backend
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 2. 设置环境变量（生产环境默认关闭）
export ALGO_DEMO_SEED_ENABLED=1

# 3. 执行种子脚本
python -m scripts.seed_demo
# 或直接运行
python scripts/seed_a3_demo_data.py

# 本地临时演示可跳过环境变量检查
python scripts/seed_a3_demo_data.py --force
```

## 演示数据闭环

执行一条命令后，将生成以下完整演示数据：

| 数据项 | 说明 |
|--------|------|
| 演示用户 | `a3_demo` / `Demo1234!` |
| 六维画像 | 知识基础偏弱、视觉化偏好、代码实操中等偏弱、OJ 通过率目标、边界条件易错、抗挫折中等 |
| 学习路径 | array → linked-list → stack-queue → binary-tree → graph → dp，含 DP 受挫后插入 array 巩固节点 |
| 8 类资源 | document / mindmap / exercises / code_case / trace_animation / ppt / video_script / reading |
| OJ 提交记录 | WA（链表反转）+ TLE（图 BFS）+ AC（括号匹配 + 爬楼梯） |
| 评估快照 | EvaluationAgent 学习效果评估记录 |
| 路径重排 | 评估触发的路径重排标记 |

## 前端验证

1. 使用 `a3_demo` / `Demo1234!` 登录
2. **学习路径页**：能看到六维画像、DAG 星图、推荐路径
3. **我的学习页**：能看到进度仪表盘、活跃度热力图、模块进度
4. **资源库页**：能看到 8 类已生成资源卡片
5. **多智能体工作台**：能看到 Agent 状态卡片、SSE 实时进度
6. **OJ 练习**：能看到提交历史记录

## 环境变量保护

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ALGO_DEMO_SEED_ENABLED` | 空（关闭） | 必须设为 `1`/`true`/`yes`/`on` 才允许执行 |
| `--force` 参数 | — | 绕过环境变量检查，仅用于本地临时演示 |

**生产环境默认关闭**，不会影响正常用户数据。

## 幂等性

- 脚本可重复执行，不会产生重复数据
- 同名 `a3_demo` 用户存在时更新而非重复创建
- `clear_demo_seed_artifacts()` 仅删除带 demo 标记的数据

## SSE 实时进度体验

资源批量生成时，前端能看到：

1. **"Orchestrator 已接收任务"** — 立即显示
2. **RAG 检索开始/完成** — 实时推送
3. **每个 Agent 状态卡片** — pending → running → verifying → done
4. **校验重试** — 显示第几次重试
5. **安全审查** — 实时状态
6. **Heartbeat** — 每 2.5 秒发送，避免长时间无响应
7. **Fallback 降级** — 显示 warning 但不崩溃
8. **单个资源失败** — 显示失败卡片，其余继续

## 无 LLM Key 演示

即使没有配置 `SPARK_API_PASSWORD`，系统会：

- 自动降级为课程知识库模板生成
- 前端显示"模板降级"提示
- 资源仍可正常生成和展示
- SSE 进度仍然实时可见
