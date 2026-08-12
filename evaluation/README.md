# AlgoPilot 系统评测（evaluation/）

本目录包含 AlgoPilot 系统自身的评测框架，用于量化核心创新点的效果。

## 评测指标

| 类别 | 指标 | 说明 |
|------|------|------|
| Bug 定位 | Top-1 Accuracy | 系统预测的 Bug 行号命中真实行号的比例 |
| Bug 定位 | Top-3 Accuracy | 前 3 个预测行号命中真实行号的比例 |
| Bug 类型识别 | Classification Accuracy | 系统分类的 Bug 类型与人工标注一致的比例 |
| 反例生成 | Bug Trigger Rate | 生成的测试用例能触发 Bug 的比例 |
| AI 可靠性 | Hallucination Rate | 被标记为幻觉的诊断比例（越低越好） |
| AI 可靠性 | Evidence Coverage | 携带结构化执行证据的诊断比例（越高越好） |
| 教学效果 | Fix Success Rate | 诊断后最终 AC 的会话比例 |
| 教学效果 | Avg Hint Level Used | 平均使用的提示层级（越低越好） |
| 教学效果 | Repeated Bug Rate | 同一用户再次出现相同 Bug 类型的比例（越低越好） |
| 系统性能 | P50 / P95 / P99 Latency | 请求延迟分位数（ms） |

## 运行

```powershell
# 终端输出
python -m evaluation.run_eval

# 导出 JSON + CSV
python -m evaluation.run_eval --json results.json --csv results.csv
```

## 数据来源

所有指标从后端数据库（`oj_submissions`、`learning_event_logs`、`student_learning_memories`）提取真实数据计算。

## 诚实原则

- **不伪造任何实验数据**。
- 当缺乏人工标注或实验数据时，指标显示 `N/A` 并标注原因。
- 随着系统使用积累真实数据，指标会自动变为可用。
- Bug 定位 / Bug 类型识别准确率需要人工标注的 ground truth，目前标注集为空，显示为待收集。