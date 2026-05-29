# 在线 OJ 使用说明

## 功能

- 与学习路径题单同步（约 120 道，按 slug 去重）
- 前端：CodeMirror 编辑器 + 运行样例 / 提交判题
- 后端：Python 3 沙箱判题（子进程 + 超时）
- 当前 **仅支持 Python 3**，力扣风格 `class Solution` + 方法名

## 启动

1. 后端（端口 9000）：

```bash
cd backend
python scripts/build_oj_data.py   # 更新 catalog 与测例
uvicorn main:app --reload --host 127.0.0.1 --port 9000
```

2. 前端：

```bash
cd frontend
npm run dev
```

3. 浏览器打开：**在线 OJ** 菜单，或学习页 **站内 OJ 练习**。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/oj/problems` | 题库列表 |
| GET | `/api/oj/problems/{slug}` | 题目详情（不含隐藏测例） |
| POST | `/api/oj/problems/{slug}/run` | 运行公开样例 |
| POST | `/api/oj/problems/{slug}/submit` | 提交全部测例（需登录） |

## 扩充测例

编辑 `scripts/oj_test_data.py` 中的 `TEST_DEFINITIONS`，然后执行：

```bash
python scripts/build_oj_data.py
```

## 生产环境注意

当前判题在宿主机 Python 子进程中执行，适合课程演示与内网部署。公网生产建议：

- 限时：每次运行设置题目级超时，Trace 录制额外设置 8s 上限。
- 限内存：生产环境通过 Docker/cgroup 按题目配置内存上限。
- 禁止危险调用：提交前拦截 `system` / `fork` / `exec` / 危险头文件等高风险代码。
- 隔离执行：判题逻辑与主 API 进程分离，推荐 Docker / isolate 容器隔离并关闭网络。
- 队列化：判题队列与主 API 分离，避免恶意或异常提交拖垮服务。

可选后续接入 [Judge0](https://github.com/judge0/judge0) 以支持 C++/Java 等多语言。
