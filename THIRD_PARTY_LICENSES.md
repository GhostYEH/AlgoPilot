# Third-Party Licenses

AlgoPilot 项目自身的软件著作权及授权方式以根目录 [LICENSE](./LICENSE) 为准（专有协议，All Rights Reserved）。

本项目使用了多项第三方开源组件，各组件分别遵循其原始开源许可证。本文件仅列出主要依赖的索引信息，不构成法律意见。

完整依赖清单、版本、用途及许可证说明请参见：

- [docs/submission/06_开源与AI_Coding说明.md](./docs/submission/06_开源与AI_Coding说明.md)

## 主要前端依赖

| 组件 | 许可证 | 用途 |
|------|--------|------|
| Vue 3 | MIT | 前端核心框架 |
| Vue Router | MIT | SPA 路由 |
| Pinia | MIT | 状态管理 |
| Element Plus | MIT | UI 组件库 |
| @element-plus/icons-vue | MIT | 图标 |
| CodeMirror 6 | MIT | 代码编辑器 |
| vue-codemirror | MIT | CodeMirror Vue 封装 |
| @codemirror/lang-python | MIT | Python 语法高亮 |
| @codemirror/lang-cpp | MIT | C++ 语法高亮 |
| @codemirror/theme-one-dark | MIT | 暗色主题 |
| Mermaid | MIT | 思维导图与流程图渲染 |
| D3.js | ISC | 自定义数据可视化 |
| @vue-flow/core | MIT | 学习路径 DAG 可视化 |
| @vue-flow/background | MIT | Vue Flow 背景组件 |
| @vue-flow/controls | MIT | Vue Flow 控制组件 |
| axios | MIT | HTTP 请求库 |
| fuse.js | Apache-2.0 | 模糊搜索 |
| Vite | MIT | 构建工具 |
| vue-tsc | MIT | Vue 类型检查 |
| TypeScript | Apache-2.0 | 类型系统 |
| unplugin-auto-import | MIT | API 自动导入 |
| unplugin-vue-components | MIT | 组件自动导入 |
| GSAP | GSAP Standard License (no charge) | 动画引擎（算法游戏过渡动画） |
| three.js | MIT | 3D 可视化 |
| world-atlas | ISC | 世界地图 TopoJSON 数据 |

## 主要后端依赖

| 组件 | 许可证 | 用途 |
|------|--------|------|
| FastAPI | MIT | Web 框架 |
| uvicorn[standard] | BSD-3-Clause | ASGI 服务器 |
| Pydantic | MIT | 数据校验 |
| pydantic-settings | MIT | 配置管理 |
| SQLAlchemy | MIT | ORM |
| python-jose[cryptography] | MIT | JWT 签发与验证 |
| bcrypt | Apache-2.0 | 密码哈希 |
| cryptography | Apache-2.0 OR BSD-3-Clause | 加密库 |
| httpx | BSD-3-Clause | HTTP 客户端 |
| websocket-client | BSD-3-Clause | WebSocket 客户端 |
| PyYAML | MIT | YAML 解析 |
| email-validator | UNLICENSE | 邮箱校验 |
| python-multipart | Apache-2.0 | 表单解析 |

## 开发与测试工具

| 工具 | 许可证 | 用途 |
|------|--------|------|
| pytest | MIT | 后端测试框架 |
| pytest-asyncio | Apache-2.0 | 异步测试支持 |
| pytest-cov | MIT | 覆盖率统计 |
| ruff | MIT | Python lint |

## 系统级运行工具

| 工具 | 许可证 | 用途 |
|------|--------|------|
| Python | PSF License | 后端运行时 |
| Node.js | MIT | 前端构建 |
| g++ (MinGW ucrt64) | GPL-3.0 | C++ OJ 编译 |
| gdb (MinGW ucrt64) | GPL-3.0 | C++ Trace |

## 第三方服务

| 服务 | 用途 |
|------|------|
| 科大讯飞星火大模型 | LLM 能力来源 |
| 讯飞 TTS | 语音朗读 |

> 上述服务的调用受其官方服务条款约束，使用前请确认账号配额与接口权限。

## 合规声明

团队已对主要第三方依赖及其许可证进行登记，项目使用、提交和分发应持续遵循相应许可证条款。本文件不构成法律意见，也不代表对所有依赖许可证完备性的绝对保证。
