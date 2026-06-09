# AlgoPilot 多智能体编排与可观测性

## 设计目标

AlgoPilot 将画像、路径规划、知识检索、资源生成、内容校验、安全审查和学习评估组织为可观测工作流。

> 系统采用可观测多智能体编排机制，每个资源生成过程均可追踪、可校验、可回滚。

前端 `AgentWorkbenchView` 通过 SSE 订阅编排事件，将每个 Agent 的运行状态、输入输出摘要、耗时、校验结果、失败原因和重试次数展示为可点击流程节点。SSE 不可用或尚未开始生成时，节点统一以 `waiting` 状态降级展示，不影响资源库的既有读取和生成能力。

## Agent 分工

| Agent | 职责 |
| --- | --- |
| ProfilingAgent | 加载六维动态学习画像，提供知识基础、认知风格、编码能力、学习目标、易错偏好和抗挫折能力 |
| LearningPathAgent | 读取当前学习路径与模块上下文，约束资源生成的顺序和侧重点 |
| KnowledgeRetriever | 使用 BM25 检索课程知识库，输出可追溯知识片段 |
| ConceptAgent | 生成概念讲解资源 |
| GraphAgent | 生成知识思维导图 |
| QuizAgent | 生成个性化练习题 |
| ScenarioAgent | 生成场景化代码沙箱 |
| TraceAgent | 调用 trace runner 生成执行轨迹 |
| PptAgent | PPT 资源扩展节点；当前 `generate-all` 未启用时明确标记为 `skipped` |
| VideoScriptAgent | 视频脚本扩展节点；当前 `generate-all` 未启用时明确标记为 `skipped` |
| ReadingAgent | 生成基础、进阶、挑战三层阅读资源 |
| ContentVerifierAgent | 对照知识片段检查事实、引用和复杂度结论；失败时将修订建议回流给生成 Agent |
| SafetyAgent | 检查敏感内容、提示注入和幻觉风险，决定发布、草稿或阻断 |
| EvaluationAgent | 汇总批次完成情况、复用数量和失败数量，形成流程级质量结果 |

## 数据流

1. `ProfilingAgent` 和 `LearningPathAgent` 提供用户与课程上下文。
2. `KnowledgeRetriever` 根据主题、模块和生成侧重点检索 Top-K 课程片段。
3. 资源 Agent 按阶段执行。`ConceptAgent` 的摘要可传给 `GraphAgent` 和 `QuizAgent`，后续 Agent 通过 `PipelineContext` 读取已完成资源的协作摘要。
4. `ContentVerifierAgent` 使用正文和知识片段进行规则校验与模型校验。
5. `SafetyAgent` 对校验后的内容执行安全审查。
6. Orchestrator 只将通过的内容标记为 `published`；未通过内容保留为 `draft`，安全失败内容标记为 `blocked`。
7. `EvaluationAgent` 汇总本次批次结果，SSE 发送最终评估状态。

## 校验回流

`ContentVerifierAgent` 最多允许两次回流重试：

1. 校验通过：发送 `success`，附带证据数量和引用结果。
2. 校验未通过且仍可重试：发送 `retry`，`failure_reason` 和 `message` 中包含修订建议。
3. 生成 Agent 接收 `revised_hint` 后重新生成，事件中的 `retry_count` 递增。
4. 超过重试上限：发送 `failed`，资源以草稿形式保留，避免错误内容静默发布。
5. Trace 资源由执行轨迹判定负责，文本校验节点发送带原因的 `skipped`。

该机制形成“生成 -> 校验 -> 修订 -> 再校验”的可观察闭环，也为后续人工回滚和复核保留完整依据。

## 安全审查

`SafetyAgent` 在内容校验之后执行，结构化结果写入：

- `meta.verification`
- `meta.safety_panel`
- `meta.agent_logs`
- `meta.evidence`

安全结果包含敏感风险、提示注入风险、幻觉告警和最终决策。`SafetyValidationPanel` 从同一份结构化元数据展示验证状态、证据数量、风险项和沙箱限制，保证工作台流程状态与资源详情页一致。

## SSE 可观测性

工作流事件使用 `type=workflow`，核心字段如下：

```json
{
  "type": "workflow",
  "agent_id": "ContentVerifierAgent",
  "agent_name": "ContentVerifierAgent",
  "stage": "content_verify",
  "status": "retry",
  "message": "复杂度结论缺少知识库依据",
  "timestamp": "2026-06-08T10:00:00+00:00",
  "duration_ms": 842,
  "validation_result": {
    "status": "failed",
    "evidence_count": 5
  },
  "retry_count": 1,
  "input_summary": "动态规划入门 | 5 evidence chunks",
  "output_summary": "",
  "failure_reason": "复杂度结论缺少知识库依据"
}
```

状态值统一为：

- `waiting`
- `running`
- `success`
- `retry`
- `failed`
- `skipped`

兼容层仍可将历史 `done/warn/error` 映射为 `success/retry/failed`。批量生成还会发送 `progress`、`collaboration`、`resource`、`heartbeat` 和 `done` 事件；前端使用 workflow 事件更新流程图，使用 resource 事件确认资源最终落态。

## 触发与观察

1. 登录 AlgoPilot。
2. 打开“多智能体协同工作台”。
3. 输入课程主题与生成侧重点。
4. 点击“启动个性化资源生成”。
5. 在“智能体协作流程图”中观察节点从 `waiting` 进入 `running`，再进入 `success/retry/failed/skipped`。
6. 点击任一节点查看输入摘要、输出摘要、耗时、校验结果、失败原因和重试次数。
7. 在下方 Agent Terminal 查看相同事件的时间序列，在资源卡片的 `SafetyValidationPanel` 查看最终证据和安全结果。
