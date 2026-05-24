# 软件杯 A3 赛道 — 系统说明（竞赛文档索引）

## 1. 需求与场景

面向大一计算机专业《数据结构与算法》课程，解决学习资源分散、路径固定、难以因材施教等问题。系统通过**对话式画像**、**多智能体资源生成**、**AI 学习路径规划**与**OJ/动画/游戏**一体化教学闭环，实现个性化学习辅助。

## 2. 多智能体架构

| Agent | 职责 |
|-------|------|
| PersonaAgent | 对话构建 7 维学习画像 |
| 课纲/导图/出题/拓展/实操/视频脚本 Agent | 六类个性化资源 |
| ContentVerifierAgent | 对照知识库校验生成内容 |
| LearningPathAgent | 动态模块学习顺序 |
| TutorAgent / OjAssistantAgent | 智能辅导 |
| EvaluationAgent | 学习效果多维度评估 |

编排入口：`services/orchestrator/core.py`（统一调度，API 禁止直连 LLM）。

## 3. 知识库与防幻觉

- 知识库：`knowledge_base/chunks.json`（按模块知识点切片）
- 检索：`services/knowledge/retriever.py`（关键词匹配 RAG）
- 安全：`services/safety/content_filter.py`（敏感词与长度）
- 校验：生成后由 Verifier Agent 对照知识库片段，并在 `meta.verified` / `knowledge_refs` 中记录

## 4. 核心 API（`/api/orchestrator`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/persona/chat` | 画像对话 SSE |
| POST | `/persona/patch-from-learning` | 随学随新 |
| POST | `/learning-path/replan` | AI 重排路径 |
| GET | `/resources/recommendations` | 精准资源推送 |
| POST | `/evaluation` | 学习效果评估 |
| POST | `/resources/generate-all` | 批量生成 SSE |

## 5. 测试要点

1. 注册登录 → 画像对话 → 同步画像 JSON  
2. 资源库一键生成 → 查看「知识库已校验」标签  
3. 学习路径页「AI 规划」→ 模块顺序变化  
4. 我的学习 → 效果评估 → 雷达维度与推送策略  
5. 完成小节后登录态下画像 `weak_points` 自动更新  

## 6. 开源与工具声明

见项目根目录及各 `README.md`；大模型 API 配置见 `.env.example`（赛题要求科大讯飞工具接入时替换 `services/llm` 实现即可，编排层无需改动）。
