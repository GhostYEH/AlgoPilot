# 软件杯 A3 赛道 — 系统说明（竞赛文档索引）

## 1. 需求与场景

**AlgoPilot**：面向高校 **《数据结构与算法》** 课程的个性化多模态学习资源生成与多智能体协同学习系统。

解决学习资源分散、路径固定、难以因材施教等问题。通过 **对话式六维画像**、**多智能体资源生成**、**个性化学习路径**、**课内 OJ + Trace 智能辅导** 与 **学习效果评估** 形成教学闭环。OJ 与 Trace 服务于课程编程实践与辅导，不作为独立刷题平台。

## 2. 多智能体架构

| Agent | 职责 |
|-------|------|
| ProfilingAgent | 对话构建 **六维**学习画像；`patch-from-learning` 随学随新 |
| Concept / Graph / Quiz / Scenario / Trace / Ppt / VideoScript / Reading | **八类**个性化资源（满足「≥5 类」） |
| ContentVerifierAgent | 对照知识库校验生成内容 |
| LearningPathAgent | 动态模块学习顺序与先修 DAG |
| TutorAgent / OjAssistantAgent / OjDiagnosisAgent | 智能辅导（讲义、OJ 提示、Trace 诊断） |
| EvaluationAgent | 学习效果多维度评估 |

编排入口：`services/orchestrator/core.py`（统一调度，API 禁止直连 LLM）。

## 3. 知识库与防幻觉

- 课纲：`knowledge_base/syllabus.json`
- 切片：`knowledge_base/chunks.json`
- 检索：`services/knowledge/retriever.py`（BM25 + 同义词）
- 安全：`services/safety/content_filter.py`
- 校验：`meta.verified` / `meta.knowledge_refs` / `meta.safety_panel`

## 4. 核心 API（`/api/orchestrator`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/persona/chat` | 画像对话 SSE |
| POST | `/persona/patch-from-learning` | 随学随新 |
| POST | `/learning-path/replan` | 重排路径 |
| GET | `/resources/recommendations` | 资源推送 |
| POST | `/evaluation` | 学习效果评估 |
| POST | `/evaluation/oj-struggle` | OJ 受挫路径建议（OJ 页 **已实现自动触发**） |
| POST | `/resources/generate-all` | 批量生成 SSE |

## 5. 测试要点

1. 注册登录 → 画像对话 → 同步六维画像  
2. 资源库 / 工作台生成 → 查看安全校验面板与知识库溯源  
3. 学习路径「AI 规划」→ 模块顺序变化  
4. 我的学习 → 效果评估 → 推送策略与路径重排  
5. 完成小节后登录态下 `patch-from-learning` 更新画像  

## 6. 科大讯飞生态集成

- 大模型：`services/llm/client.py` — 星火 Spark（`SPARK_API_PASSWORD` 等）
- 语音：`services/tts/iflytek_tts.py` — `/api/ai/tts/synthesize`
- 前端：主导航「讯飞星火 Spark · iFlytek TTS」
- **iFlyCode**：开发辅助声明见根目录 `README.md`

## 7. 防幻觉与安全可视化

- `SafetyValidationPanel.vue`：知识库溯源、复杂度校验、敏感词、承办 Agent
- 课内 OJ：限时、限内存、危险系统调用拦截、子进程执行；**Docker 强隔离为可选部署**

## 8. 开源与工具声明

见根目录 `README.md` 技术栈章节；环境变量见 `backend/.env.example`。

完整演示闭环见根目录 [比赛演示闭环](../../../README.md#-比赛演示闭环)。
