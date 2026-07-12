# 截图存放目录

本目录用于存放用户操作手册（[../05_用户操作手册.md](../05_用户操作手册.md)）中 S01-S18 截图任务对应的真实运行截图。

## 命名规则

| 编号 | 文件名 | 内容 |
|------|--------|------|
| S01 | `S01-login.png` | 登录与注册页面 |
| S02 | `S02-persona-chat.png` | 画像多轮对话 |
| S03 | `S03-persona-result.png` | 六维画像结果 |
| S04 | `S04-persona-evidence.png` | 画像证据链 |
| S05 | `S05-learning-path.png` | 个性化学习路径 |
| S06 | `S06-agent-progress.png` | 多智能体生成进度 |
| S07 | `S07-resource-document.png` | 个性化讲解文档 |
| S08 | `S08-resource-mindmap.png` | 思维导图 |
| S09 | `S09-resource-quiz.png` | 分层练习 |
| S10 | `S10-code-case.png` | 代码实操案例 |
| S11 | `S11-oj-problem.png` | OJ 题目与编辑器 |
| S12 | `S12-oj-failed.png` | OJ 错误判定 |
| S13 | `S13-trace-view.png` | Trace 执行轨迹 |
| S14 | `S14-ai-diagnosis.png` | AI 错误诊断 |
| S15 | `S15-mastery-update.png` | 掌握度变化 |
| S16 | `S16-path-replan.png` | 学习路径重规划 |
| S17 | `S17-teacher-dashboard.png` | 教师看板 |
| S18 | `S18-student-detail.png` | 学生详情 |

## 推荐分辨率

- 最低 1280×720
- 推荐 1920×1080
- 格式：PNG

## 隐私处理要求

截图前必须隐藏以下敏感信息：

- 用户名、邮箱、手机号
- 密码、Token、JWT
- `SPARK_API_PASSWORD`、`IFLYTEK_TTS_API_KEY` 等环境变量
- 真实学生姓名（教师看板截图请使用示例账号或打码）

## 截图完成后如何插入文档

每张截图在 `05_用户操作手册.md` 中都有对应 HTML 注释占位，例如：

```markdown
<!-- 截图完成后取消下一行注释：
![六维学生画像结果](images/S03-persona-result.png)
-->
```

截图完成后，将注释取消为：

```markdown
![六维学生画像结果](images/S03-persona-result.png)
```

## 正式提交前

正式提交比赛材料前：

1. 确认所有 S01-S18 截图已补齐
2. 删除 `05_用户操作手册.md` 末尾的"截图进度表"
3. 将各章节中的"待补截图"任务文字删除（保留已取消注释的图片引用）
4. 验证所有图片链接在 GitHub 上可正常打开
