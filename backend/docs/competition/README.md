# 软件杯 A3 赛道 — 系统说明（竞赛文档索引）

## 1. 需求与场景

面向大一计算机专业《数据结构与算法》课程，解决学习资源分散、路径固定、难以因材施教等问题。系统通过**对话式画像**、**多智能体资源生成**、**AI 学习路径规划**与**OJ/动画/游戏**一体化教学闭环，实现个性化学习辅助。

## 2. 多智能体架构

| Agent | 职责 |
|-------|------|
| PersonaAgent | 对话构建 7 维学习画像 |
| Concept/Graph/Quiz/Scenario/Trace/Ppt/VideoScript/Reading Agent | 八类个性化资源，满足“至少 5 种个性化资源”要求 |
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

## 6. 科大讯飞生态集成

- 核心大模型：`backend/services/llm/client.py` 默认调用科大讯飞星火 Spark OpenAI 兼容接口，配置项为 `SPARK_API_PASSWORD`、`SPARK_MODEL`、`SPARK_CHAT_URL`。
- 多模态语音：`backend/services/tts/iflytek_tts.py` 封装科大讯飞在线语音合成 WebAPI，前端教案朗读与短视频脚本试听均走 `/api/ai/tts/synthesize`。
- 前端显式标识：主导航展示“讯飞星火 Spark · iFlytek TTS”，Agent DAG 展示 Spark、TTS 节点。
- AI Coding 工具声明：团队使用“讯飞星火智能编程助手（iFlyCode）”辅助 AlgoPilot 开发，包括 Agent Prompt 草稿、FastAPI/TypeScript 样板生成、单测样例补全、Bug 排查建议和文档润色。所有生成代码均由团队人工审阅、运行测试并纳入 Git 版本管理。

## 7. 防幻觉与安全可视化

- 每份资源 `meta.safety_panel` 记录知识库溯源、复杂度事实校验、敏感词过滤和承办 Agent。
- 前端 `SafetyValidationPanel.vue` 以绿色盾牌面板展示“知识库溯源 / 复杂度校验 / 敏感词过滤 / ContentVerifierAgent + SafetyAgent”。
- OJ Playground 与资源校验面板展示沙盒限制：限时、限内存、危险系统调用拦截、子进程执行，生产部署建议 Docker 隔离。

## 8. 开源与工具声明

见项目根目录及各 `README.md`；大模型与语音 API 配置见 `.env.example`，当前后端已默认接入科大讯飞星火 Spark 与科大讯飞在线语音合成。
