# A3 比赛演示数据种子 · 使用指南

## OJ + Trace 核心答辩场景

### 场景选择

- 演示题目：**反转链表**（`reverse-linked-list`）
- 选择原因：`prev / curr / nxt` 三指针关系可视化明确，错误发生在首轮循环，评委能快速看懂“保存后继过晚导致断链”的因果关系。
- 演示定位：OJ 不是独立刷题平台，而是采集编程实践证据并驱动画像更新、资源推荐和学习路径调整的入口。
- 无 Key 保证：该典型错误由 AST + Trace 规则诊断，不调用 LLM；未配置 `SPARK_API_PASSWORD` 也能稳定演示。

### 典型错误代码

```python
import sys


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def main():
    data = list(map(int, sys.stdin.read().split()))
    n = data[0]
    values = data[1:1 + n]

    dummy = ListNode()
    tail = dummy
    for value in values:
        tail.next = ListNode(value)
        tail = tail.next

    prev = None
    curr = dummy.next
    while curr:
        curr.next = prev
        nxt = curr.next  # 错误：原后继已经被覆盖
        prev = curr
        curr = nxt

    answer = []
    curr = prev
    while curr:
        answer.append(curr.val)
        curr = curr.next
    print(*answer)


if __name__ == '__main__':
    main()
```

正确顺序应为：

```python
nxt = curr.next
curr.next = prev
prev = curr
curr = nxt
```

### 演示点击顺序

1. 使用 `a3_demo` / `Demo1234!` 登录，进入「OJ 练习」，打开「反转链表」。
2. 点击代码区右上角「评委演示模式」。系统自动切换到 Python 并装载上述错误代码，同时清空上一轮演示状态。
3. 点击「提交」。等待显示 `WA · 答案错误`、`0 / 1 通过`，失败点应显示期望 `5 4 3 2 1`、实际 `1`。
4. 观察自动生成的「AI Trace 诊断报告」：错因应为「指针更新顺序错误」，并显示错误步骤、`curr` 与 `nxt=null`、WA 原因及修复顺序。
5. 点击「一键进行可视化诊断」。分屏会自动跳转到 `nxt = curr.next` 对应帧；在「三指针观察窗」中重点展示 `prev / curr / nxt`。
6. 返回报告区，展示推荐知识点和三类资源：「指针更新动画」「边界条件练习」「错题复盘卡」。
7. 为展示持续受挫联动，可再提交两次。第 3 次失败后触发 `EvaluationAgent` 的 `oj-struggle` 评估，并给出插入链表巩固模块、由 `PlannerAgent` 重排路径的建议。

### 预期显示结果

| 环节 | 预期结果 |
|------|----------|
| OJ 判题 | WA，样例期望 `5 4 3 2 1`，实际 `1` |
| Trace 定位 | 定位到 `nxt = curr.next`，此时 `curr` 仍指向节点而 `nxt=null` |
| 规则诊断 | 错误类型「指针更新顺序错误」；解释原后继被覆盖、循环提前结束 |
| 修复建议 | 先保存 `nxt`，再修改 `curr.next`，最后推进 `prev/curr` |
| 学习干预 | 首次失败即推荐知识点与巩固资源；连续 3 次失败触发受挫评估 |
| 路径联动 | 建议在当前 DAG 路径插入「链表指针更新巩固」节点 |

### 答辩讲解旁白

> 这里展示的不是传统 OJ 的简单判对判错。学生提交后，系统把失败用例与逐行 Trace 对齐，定位到 `nxt = curr.next` 这一帧。此时 `curr` 仍指向当前节点，但 `nxt` 已经变成空，说明原后继在保存前被覆盖，链表从首轮反转开始断开。OjDiagnosisAgent 在无大模型 Key 的情况下也能通过规则稳定给出错因、变量证据和修改顺序，并推荐指针动画、边界练习和错题复盘卡。若学生连续受挫，EvaluationAgent 会把这次编程证据回写学习画像，再由 PlannerAgent 建议向 DAG 路径插入巩固模块，形成“判题、诊断、资源、画像、路径”的学习闭环。

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
7. **教师教学看板**：顶栏点击「教师教学看板」，确认以下内容完整展示：
   - 班级学生数、画像数、平均掌握度、资源生成数量、OJ 提交次数
   - 高频薄弱知识点与高频错误类型
   - 自动生成的 3 条教师补讲建议
   - 对应模块、推荐资源类型和推荐 OJ 题目的课后巩固包

## 教师端答辩演示

1. 使用任一已登录账号进入 `/teacher-dashboard`
2. 先说明数据来源于用户、学习进度、画像/Evaluation、OJ 学习记忆和资源记录的实时聚合
3. 指出高频薄弱点和错误类型，展示系统如何从学生自学证据发现班级共性问题
4. 展示 3 条补讲建议，说明教师可据此调整下一次课堂内容
5. 点击巩固包中的 OJ 题目，演示从教学分析直接进入课后练习

接口：`GET /api/teacher/dashboard-summary`

当真实班级记录不足时，页面显示“比赛演示数据”标记并使用 demo fallback。当前入口仅要求登录，后续正式部署可接入教师角色与班级范围权限。

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
