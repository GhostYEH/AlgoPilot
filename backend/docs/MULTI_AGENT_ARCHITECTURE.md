# 多智能体架构说明（软件杯 A3）

## 1. 编排框架

采用 **Orchestrator + Workflow DAG**（与 LangGraph 同构：状态节点、有向边、顺序执行），所有 LLM 调用经 `services/llm/client.py`，API 层禁止直连大模型。

| 层级 | 模块 |
|------|------|
| 入口 | `api/orchestrator.py` |
| 编排 | `services/orchestrator/core.py` |
| 流水线 | `services/orchestrator/workflow.py` |
| 角色 | `services/agents/*` + `registry.py` |

## 2. 角色智能体（≥6）

| Agent ID | 职责 |
|----------|------|
| ProfilingAgent | 对话式画像、JSON 七维抽取、随学随新 |
| DocAgent | 讲解文档 Markdown |
| MindMapAgent | 思维导图 JSON |
| QuizAgent | 题单 JSON（选择/填空/编程） |
| ReadingAgent | 拓展阅读 |
| CodeAgent | 代码实操案例 |
| VideoAgent | 视频分镜脚本 |
| LearningPathAgent | 路径重排 |
| TutorAgent | 流式答疑（结合画像 + Mermaid） |
| ContentVerifierAgent | 知识库交叉校验 |
| EvaluationAgent | 学习效果评估 |
| KnowledgeRetriever | 课程知识库检索 |

## 3. 资源生成 Pipeline（非简单并行）

```
KnowledgeRetriever → DocAgent/MindMapAgent/... → ContentVerifierAgent → ContentSafety → 落库
```

SSE 事件：`workflow`（阶段进度）+ `progress` + `resource` + `done`。

## 4. 防幻觉与安全

- RAG：`knowledge_base/chunks.json`
- 校验：ContentVerifierAgent 对照片段
- 规则：外链/可疑题号拦截
- 过滤：`services/safety/content_filter.py`

## 5. 流式输出

- 画像对话：`POST /api/orchestrator/persona/chat`
- 助教：`POST /api/orchestrator/tutor/chat/stream`
- 批量资源：`POST /api/orchestrator/resources/generate-all`

## 6. 与 LangChain/LangGraph 关系

当前为 **自研轻量 DAG**（零额外依赖、易部署）。节点语义与 LangGraph `StateGraph` 一致，可在文档/PPT 中表述为「LangGraph 同构实现」；后续可替换为 `langgraph` 包而保留 Agent 接口不变。
