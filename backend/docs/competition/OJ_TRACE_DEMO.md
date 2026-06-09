# OJ + Trace 智能诊断答辩场景

## 目标

以「反转链表」的真实 WA 为入口，稳定展示：

`OJ 判错 -> Trace 关键帧 -> OjDiagnosisAgent 规则诊断 -> 巩固资源 -> EvaluationAgent -> 路径调整建议`

该链路服务于 A3 赛道的智能辅导和个性化学习闭环，不将 AlgoPilot 定位为通用刷题平台。

## 无 API Key 降级

`services/oj/rule_diagnosis.py` 使用 Python AST 识别以下顺序错误：

```python
curr.next = prev
nxt = curr.next
```

规则仅在 `reverse-linked-list` 且代码结构明确命中时生效。诊断结合真实 Trace 帧返回：

- 错误类型：`pointer_update_error`
- 出错步骤：`nxt = curr.next` 对应 Trace step
- 变量证据：`curr` 指向节点、`nxt=null`
- WA 原因：原后继被覆盖，循环提前结束，输出只剩首节点
- 修改建议：先保存后继，再反转指针，最后推进三指针
- 巩固知识点和学习干预建议

规则优先于 LLM 调用，因此即使未配置 `SPARK_API_PASSWORD`，答辩流程也可重复运行。

## 两级学习干预

1. 首次失败：结构化 Trace 报告立即生成学习干预，推荐「指针更新动画」「边界条件练习」「错题复盘卡」。
2. 连续 3 次失败：前端触发 `/api/orchestrator/evaluation/oj-struggle`，由 EvaluationAgent 评估受挫状态，并建议 PlannerAgent 插入巩固模块或重排路径。

## 验证

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_oj_reverse_linked_list_demo.py -q
```

完整点击顺序、错误代码和答辩旁白见根目录 `DEMO_CHECKLIST.md`。
