# 数字口径与版本快照表

## Version Freeze

| Field | Value |
| --- | --- |
| Git commit | `dc3e1503fdffaa7c778f83192048c58785cc5870` |
| Statistics date | 2026-07-13 |
| Code tree status | `backend/`、`frontend/`、`.github/` 相对该 commit 无差异 |
| Presentation worktree | dirty；新增故事板、截图交付资产和 ppt-master 项目文件，不改变上述代码统计范围 |
| OS | Microsoft Windows 11 家庭版 中文版，10.0.26200，Build 26200 |
| Python | 3.13.7 |
| Node.js | v25.8.1 |

## Dynamic Numbers

| Metric | Frozen value | Reproducible source / method | Usage decision |
| --- | ---: | --- | --- |
| 注册多智能体节点 | 22 | 在 `backend/` 目录运行 `from services.agents.registry import AGENT_REGISTRY; len(AGENT_REGISTRY)` | Slide 08 可用 |
| Agent layer | 6 | `len({x['layer'] for x in AGENT_REGISTRY})` | Slide 08、18 可用 |
| 已实现节点 | 20 | `sources/02_系统开发说明书.md` 4.2/4.3.1；注册表本身无 status 字段 | Slide 08 使用，但须同时说明状态来源不是代码内字段 |
| 规划节点 | 2 | `PptAgent`、`VideoScriptAgent`；来源同上 | Slide 08 可用，必须标“规划中” |
| 资源类型 | 6 | `len(RESOURCE_TYPE_TO_AGENT)`；`backend/services/agents/registry.py:106-113` | Slide 09、15 可用 |
| A3 核心展示资源 | 5 | `sources/01_项目说明书.md` 4.1 与 A3 对应关系；reading 为扩展 | Slide 09、15 可用 |
| 当前测试实跑 | 190 passed / 0 failed / 1 warning | 2026-07-13 执行 `cd backend; .\.venv\Scripts\python.exe -m pytest --tb=no -q` | 不替换 Slide 17 的归档 188 主画面；用于风险披露 |
| 后端测试文件 | 32 | `Get-ChildItem backend/tests -File -Filter 'test_*.py'` | Slide 17、18 可用 |
| Vue 组件文件 | 73 | `Get-ChildItem frontend/src/components -Recurse -File -Filter '*.vue'` | 作为 Slide 18 小型证据标签 |
| 视图文件 | 23 | `Get-ChildItem frontend/src/views -Recurse -File -Filter '*.vue'` | Slide 18 产品界面资产主数字 |
| 前端命名路由 | 24 | `frontend/src/router/*.ts` 中行首 `name:` 统计 | Slide 18 小型证据标签 |
| OJ 题目 | 126 | `backend/data/oj/catalog.json` JSON 数组长度 | Slide 18 课程与题库资产主数字 |
| 算法游戏组件 | 13 | `frontend/src/modules/games/components/*Game.vue` | Slide 18 小型证据标签 |
| Trace Vue 组件 | 13 | `frontend/src/components/oj/trace/*.vue` | Slide 11、18 可用；口径为组件文件数 |
| FastAPI 路由装饰器 | 67 | `backend/api/*.py` + `backend/main.py` 中 `@router/@app` HTTP 方法装饰器统计 | Slide 18 API 资产主数字；口径不是运行时路由实例数 |
| ORM 表 | 8 | `len(Base.metadata.tables)`；表名见 `backend/models/db_models.py` | Slide 14、18 可用 |
| 正式课程章节 | 14 | `chapters/01-*.md` 至 `14-*.md`；排除 `_chapter_template_sections.md` | Slide 18 小型证据标签 |
| 实验 / 项目 | 6 / 2 | `labs/*.md`、`projects/*.md` 文件数 | Slide 18 小型证据标签 |

## Archived Test Snapshot Used on Slide 17

| Field | Value |
| --- | --- |
| Result | 188 passed，0 failed，1 warning |
| Test files | 32 |
| Execution date | 2026-07-12 |
| OS | Windows 11 |
| Python | 3.13.7 |
| Node.js | v25.8.1 |
| Git commit | 待补充；测试说明书未记录 |
| Backend command | `cd backend; .\.venv\Scripts\python.exe -m pytest --tb=no -q` |
| Frontend commands | `npm run typecheck`；`npm run build` |
| Runtime | 54.05 秒；只进入页脚或 Speaker Notes |
| Frontend build runtime | 2.43 秒；只进入页脚或 Speaker Notes |
| Source | `sources/03_测试说明书.md` 2.2–2.3 |

## Current Implementation Configuration

| Configuration | Current value | Code location | Required wording |
| --- | ---: | --- | --- |
| OJ 受挫阈值 | 3 次连续失败 | `backend/schemas/evaluation.py:48` 默认值；`backend/services/agents/evaluation.py:163` 判断 | “当前默认配置：连续失败 ≥3” |
| BM25 返回数量 | `top_k=4` | `backend/services/knowledge/retriever.py:189-196` | “当前默认配置：top_k=4” |
| 内容校验重试 | 最多 2 次 | `backend/services/orchestrator/workflow.py:30` `MAX_VERIFY_RETRIES=2` | “当前实现配置：最多重试 2 次” |
| Python Trace 步数 | 200 | `backend/services/oj/trace_runner.py:21` `MAX_TRACE_STEPS=200` | “当前实现上限：200 步” |
| OJ 题目默认时限 | 3000ms | `backend/schemas/oj.py:35`；`backend/services/oj/runner.py:229` | “当前题目默认时限：3 秒” |
| C++ Trace 子进程上限 | 30 秒 | `backend/services/oj/cpp_trace_runner.py:26` `CPP_TRACE_SUBPROCESS_CAP_S=30.0` | 与 OJ 3 秒分开描述；不得写成 C++ Trace 3 秒 |

