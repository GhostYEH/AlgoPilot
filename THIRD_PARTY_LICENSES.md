AlgoPilot 第三方依赖与开源许可证声明
=====================================

本项目基于以下开源组件构建，各组件受其自身许可证约束。
以下列出主要直接依赖及其用途与许可证类型。

前端依赖
--------

| 组件 | 版本 | 用途 | 许可证 |
|------|------|------|--------|
| [Vue 3](https://vuejs.org/) | ^3.5 | UI 框架 | MIT |
| [Vite](https://vitejs.dev/) | ^8.0 | 构建工具 | MIT |
| [TypeScript](https://www.typescriptlang.org/) | ~6.0 | 类型系统 | Apache-2.0 |
| [Element Plus](https://element-plus.org/) | ^2.14 | UI 组件库 | MIT |
| [Pinia](https://pinia.vuejs.org/) | ^3.0 | 全局状态管理 | MIT |
| [Vue Router](https://router.vuejs.org/) | ^4.6 | 前端路由 | MIT |
| [CodeMirror 6](https://codemirror.net/) | ^6.0 | 课内 OJ 代码编辑器 | MIT |
| [Mermaid](https://mermaid.js.org/) | ^11.15 | 思维导图 / 流程图渲染 | MIT |
| [@vue-flow/core](https://vueflow.dev/) | ^1.48 | 概念知识图谱 DAG 可视化 | MIT |
| [Axios](https://axios-http.com/) | ^1.16 | HTTP 客户端 | MIT |
| [D3.js](https://d3js.org/) | ^7.9 | 数据可视化 | ISC |
| [Fuse.js](https://www.fusejs.org/) | ^7.3 | 模糊搜索 | Apache-2.0 |
| [vue-codemirror](https://github.com/codemirror/vue-codemirror) | ^6.1 | CodeMirror Vue 封装 | MIT |

后端依赖
--------

| 组件 | 版本 | 用途 | 许可证 |
|------|------|------|--------|
| [FastAPI](https://fastapi.tiangolo.com/) | >=0.115 | Web API 框架 | MIT |
| [Uvicorn](https://www.uvicorn.org/) | >=0.32 | ASGI 服务器 | BSD-3-Clause |
| [Pydantic v2](https://docs.pydantic.dev/) | >=2.0 | 数据校验与 Schema 定义 | MIT |
| [SQLAlchemy 2](https://www.sqlalchemy.org/) | >=2.0 | ORM（默认 SQLite） | MIT |
| [httpx](https://www.python-httpx.org/) | >=0.27 | 异步 HTTP 客户端（调用大模型） | BSD-3-Clause |
| [python-jose](https://github.com/mpdavis/python-jose/) | >=3.3 | JWT 令牌 | MIT |
| [bcrypt](https://github.com/pyca/bcrypt/) | >=4.0 | 密码哈希 | Apache-2.0 |
| [PyYAML](https://pyyaml.org/) | >=6.0 | YAML 解析 | MIT |
| [cryptography](https://cryptography.io/) | >=41.0 | 加密原语 | Apache-2.0 或 BSD-3-Clause |
| [email-validator](https://github.com/JoshData/python-email-validator) | >=2.0 | 邮箱格式校验 | Unlicense |

开发与测试依赖
--------------

| 组件 | 版本 | 用途 | 许可证 |
|------|------|------|--------|
| [pytest](https://docs.pytest.org/) | >=8.0 | 单元测试框架 | MIT |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | >=5.0 | 测试覆盖率 | MIT |
| [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | >=0.24 | 异步测试支持 | MIT |
| [ruff](https://docs.astral.sh/ruff/) | >=0.8 | Python Linter & Formatter | MIT |
| [vue-tsc](https://github.com/vuejs/language-tools) | ^3.2 | Vue TypeScript 类型检查 | MIT |

AI 工具声明
-----------

本项目在开发过程中使用了以下 AI 辅助工具：

| 工具 | 提供方 | 用途 | 声明 |
|------|--------|------|------|
| 讯飞星火 Spark | 科大讯飞 | 默认核心大模型，用于画像构建、资源生成、智能辅导、评估等 | 运行时依赖，非代码生成工具 |
| 科大讯飞在线语音合成（TTS） | 科大讯飞 | 教案朗读、短视频脚本试听 | 运行时依赖，非代码生成工具 |
| 讯飞星火智能编程助手（iFlyCode） | 科大讯飞 | 辅助样板代码编写、单测草拟、Bug 排查建议、Agent Prompt 与文档润色 | 所有产出经人工审阅与测试后纳入版本管理 |

---

以上清单基于 `frontend/package.json` 与 `backend/requirements.txt` / `requirements-dev.txt`
中的直接依赖整理，许可证类型以各项目官方仓库声明为准。如有遗漏或更新，请以实际依赖为准。
