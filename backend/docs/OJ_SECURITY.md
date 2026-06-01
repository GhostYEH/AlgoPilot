# AlgoPilot OJ / Trace 执行安全边界

> 本文档说明 AlgoPilot 课内在线评测（OJ）与 Trace Engine 的**当前安全实现**、**已知限制**以及**生产级部署增强建议**。
> 不涉及判题逻辑变更，仅补安全边界说明。
>
> **定位声明**：当前 OJ / Trace 为课程演示与比赛答辩场景下的轻量执行环境，**不是生产级公网在线判题沙箱**，不承诺 seccomp / gVisor 级别的进程隔离。

---

## 1. 当前已实现的安全措施

### 1.1 Python 子进程执行与超时

| 机制 | 实现位置 | 说明 |
|------|----------|------|
| 子进程隔离 | `services/oj/runner.py` L266 | 用户代码在 `subprocess.run([sys.executable, ...])` 中执行，与主进程隔离 |
| 执行超时 | `runner.py` L270, `trace_runner.py` L298, `stdio_runner.py` L71 | `timeout=max(1, time_limit_ms / 1000)`，默认 3 秒，超时返回 TLE |
| 临时文件清理 | `runner.py` L287, `trace_runner.py` L315–316 | `path.unlink(missing_ok=True)` 清理用户脚本与 `trace_serialize.py` |
| 静态审计门闸 | `services/oj/static_audit.py` → `ASTAnalyzerAgent` | 执行前先通过 AST 静态审计，违规直接返回 CE |

### 1.2 C++ 静态危险调用拦截

| 机制 | 实现位置 | 说明 |
|------|----------|------|
| 危险头文件拦截 | `utils/security.py` L12–16 | 正则匹配 `#include <cstdlib>`, `<windows.h>`, `<unistd.h>`, `<fstream>` |
| 危险函数调用拦截 | `utils/security.py` L18–26 | 正则匹配 `system(`, `popen(`, `fork(`, `exec*(`, `syscall(`, `__asm__`, `asm(` |
| 编译前强制检查 | `services/oj/cpp_runner.py` L416–424 | `check_cpp_security()` 在编译前执行，命中则直接返回 CE |
| Trace 编译前检查 | `services/oj/cpp_trace_runner.py` L787–794, L900–907 | GDB Trace 入口同样调用 `check_cpp_security()` |
| 错误信息 | `utils/security.py` L9 | 统一返回 `"安全系统拦截：代码包含违规的系统调用或头文件"` |

> **注意**：`check_cpp_security()` 是**编译前正则扫描**，属于静态防线，不等同于运行时沙箱隔离。恶意代码可能通过字符串拼接、宏展开、模板元编程等方式绕过正则匹配。

### 1.3 输出长度限制

| 机制 | 实现位置 | 说明 |
|------|----------|------|
| 错误信息截断 | `runner.py` L296, `cpp_runner.py` L467 | `err[:800]` 限制错误输出预览长度 |
| 标准输出截断 | `runner.py` L316, `stdio_runner.py` L101 | `stdout[:400]` 限制实际输出预览 |
| Trace 结果截断 | `trace_runner.py` L349, L460 | `result_preview` 截断至 300 字符 |
| 输入/预期预览截断 | `runner.py` L126–134 | `_preview_args` / `_preview_value` 截断至 500 字符 |
| Trace 步数上限 | `trace_runner.py` L21, `cpp_trace_runner.py` L20 | `MAX_TRACE_STEPS = 200`，`MAX_CPP_TRACE_STEPS = 200` |

> **注意**：当前截断作用于**结果预览**，用户进程的 stdout 本身未在 `subprocess.run` 层做硬限制。恶意代码仍可产生大量输出占用内存，需依赖生产级沙箱解决。

### 1.4 Trace 录制额外时间上限

| 机制 | 实现位置 | 说明 |
|------|----------|------|
| GDB 子进程硬上限 | `cpp_trace_runner.py` L22 | `CPP_TRACE_SUBPROCESS_CAP_S = 3.0` 秒，防止 GDB 死循环拖垮 worker |
| 动态超时计算 | `cpp_trace_runner.py` L25–28 | `_trace_subprocess_timeout()` 取 `min(3.0, requested)`，不超过硬上限 |
| Python Trace 超时 | `trace_runner.py` L298, L409 | 与判题共用 `time_limit_ms` 超时参数 |
| Trace 步数上限 | `trace_runner.py` L21, `cpp_trace_runner.py` L20 | `MAX_TRACE_STEPS = 200`，超出后停止采集但仍正常返回 |

---

## 2. 当前限制

### 2.1 不是生产级在线判题沙箱

当前实现为**课程场景下的轻量执行环境**，存在以下安全边界：

- **无进程级资源限制**：`subprocess.run` 未设置 `rlimit`（CPU 时间、内存、文件描述符数），恶意代码可无限占用内存或 fork 炸弹
- **无文件系统隔离**：用户代码在临时目录执行，但进程本身可访问宿主文件系统
- **无网络隔离**：用户代码可通过 `socket` / `requests` 等访问外部网络
- **无用户权限隔离**：子进程继承主进程用户权限，可读写宿主文件
- **输出未硬限制**：`subprocess.run(capture_output=True)` 会将全部 stdout/stderr 缓存到内存，无流式截断
- **Python 安全依赖 AST 静态审计**：`ASTAnalyzerAgent` 可拦截 `import os` / `open()` 等危险调用，但属于编译前检查，非运行时隔离
- **C++ 静态拦截可被绕过**：`check_cpp_security()` 基于正则匹配，宏展开、模板元编程、字符串拼接等方式可绕过

### 2.2 C++ Trace 依赖本机 g++/gdb

- C++ 判题与 Trace 均依赖宿主机安装的 `g++` 和 `gdb`
- Windows 环境需安装 MinGW（`cpp_runner.py` 自动搜索常见路径）
- GDB MI 模式单步追踪性能受程序复杂度影响，已设 3 秒硬上限
- GDB 输出解析依赖正则匹配，非标准 GDB 版本可能解析失败

### 2.3 不承诺 seccomp / gVisor 级隔离

当前系统**不提供**以下生产级安全能力：

- seccomp 系统调用白名单
- gVisor 用户态内核
- namespace 隔离（PID / mount / network）
- cgroup 资源配额强制

这些能力需在部署层面（Docker / isolate / firejail）实现，不属于当前应用层代码的职责范围。

---

## 3. 生产部署增强建议

以下为将 AlgoPilot OJ / Trace 从课程演示环境升级为**生产级在线判题系统**的建议方案。

### 3.1 Docker 容器隔离

```dockerfile
# 示例：判题沙箱 Dockerfile
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 g++ gdb && \
    rm -rf /var/lib/apt/lists/*

# 创建非 root 判题用户
RUN useradd -m -s /bin/bash judge
USER judge
WORKDIR /home/judge
```

- 每次判题启动独立容器，执行完毕立即销毁
- 使用 `--rm` 自动清理，`--network none` 禁止网络

### 3.2 非 root 用户执行

```bash
docker run --rm --network none \
  --user judge \
  judge-sandbox python3 /home/judge/main.py
```

- 容器内以 `judge` 用户运行，禁止 root 权限
- 宿主机同样不应以 root 运行后端服务

### 3.3 禁止网络访问

```bash
docker run --rm --network none judge-sandbox ...
```

- `--network none` 彻底禁止容器内网络访问
- 防止用户代码发起外部请求、数据外泄

### 3.4 CPU / 内存 / 文件系统限制

```bash
docker run --rm --network none \
  --cpus=1 \
  --memory=256m \
  --memory-swap=256m \
  --pids-limit=64 \
  --read-only \
  --tmpfs /tmp:size=64m,noexec,nosuid \
  judge-sandbox ...
```

| 限制参数 | 说明 |
|----------|------|
| `--cpus=1` | 限制 CPU 核数 |
| `--memory=256m` | 限制内存使用 |
| `--memory-swap=256m` | 禁止 swap 扩展 |
| `--pids-limit=64` | 防止 fork 炸弹 |
| `--read-only` | 根文件系统只读 |
| `--tmpfs /tmp:size=64m,noexec,nosuid` | 临时目录大小限制 + noexec |

### 3.5 临时目录清理

- 当前实现已使用 `tempfile.TemporaryDirectory()` / `NamedTemporaryFile(delete=False)` + `unlink`
- 生产环境建议：
  - 容器销毁时自动清理（`--rm`）
  - 宿主机定期清理 `/tmp` 下残留文件
  - 可选 `tmpfs` 挂载，容器退出即释放

### 3.6 判题队列与 API 服务分离

- 当前判题与 API 服务运行在同一进程，恶意代码可能影响 API 响应
- 生产环境建议：
  - 使用 Celery / RQ 等任务队列，判题 worker 独立部署
  - 限制并发判题数，防止资源耗尽
  - 判题 worker 与 API 服务运行在不同主机或容器

### 3.7 额外建议

| 项目 | 建议 |
|------|------|
| seccomp 配置 | 使用 Docker 默认 seccomp profile 或自定义，限制 `clone` / `mount` 等系统调用 |
| isolate / firejail | Linux 下可使用 [isolate](https://github.com/ioi/isolate)（IOI 官方沙箱）或 firejail 替代 Docker |
| 输出流式截断 | 在 `subprocess.run` 前设置 `resource.setrlimit(RLIMIT_FSIZE, ...)` 限制输出文件大小 |
| 日志审计 | 记录所有用户提交代码与执行结果，用于安全审计 |
| 速率限制 | API 层限制提交频率，防止恶意刷题占满判题资源 |
| 镜像签名 | 生产环境使用签名镜像，防止供应链攻击 |

---

## 4. 安全措施速查表

| 安全维度 | 当前状态 | 生产建议 |
|----------|----------|----------|
| 进程隔离 | `subprocess.run` | Docker 容器 |
| 用户权限 | 继承主进程 | 非 root（`--user judge`） |
| 网络隔离 | 无 | `--network none` |
| CPU 限制 | `timeout` 参数 | `--cpus=1` + `rlimit` |
| 内存限制 | 无 | `--memory=256m` |
| 文件系统 | 临时目录 + `unlink` | `--read-only` + `--tmpfs` |
| 输出限制 | 预览截断（400–800 字符） | `rlimit RLIMIT_FSIZE` + 流式截断 |
| 进程数限制 | 无 | `--pids-limit=64` |
| C++ 静态拦截 | `check_cpp_security()` 正则 | 保留 + 容器级 seccomp |
| Python 静态审计 | `ASTAnalyzerAgent` | 保留 + 容器级隔离 |
| GDB 超时 | 3 秒硬上限 | 保留 + 容器级 CPU 限制 |

---

## 5. 演示建议

### 5.1 答辩优先使用 Python Trace

- Python Trace 基于 `sys.settrace`，**无外部依赖**，Windows / Linux / macOS 均可运行
- Python 静态审计（`ASTAnalyzerAgent`）覆盖 `while True` 死循环、`import os` 等危险调用
- Trace 步数上限 200 步，超时默认 3 秒，演示稳定性高
- **建议答辩时优先演示 Python 题目的 Trace 功能**

### 5.2 C++ Trace 作为扩展技术能力说明

- C++ Trace 依赖宿主机 `g++` + `gdb`，演示前需确认环境已安装
- GDB MI 单步追踪 + `gdb_stl_extract.py` STL 容器提取是技术亮点，可展示系统深度
- 若答辩环境 GDB 不可用，C++ 判题仍可正常工作（仅 Trace 受限）
- **建议将 C++ Trace 定位为"扩展技术能力"，而非核心演示路径**

### 5.3 安全问题应答策略

若评委追问安全问题，建议按以下思路回答：

1. **当前定位**：课程演示系统，面向受控内网环境，用户为课程学生
2. **已实现防线**：静态审计 + 超时控制 + 输出截断 + 临时文件清理
3. **已知边界**：坦诚说明无运行时沙箱隔离，不属于当前场景需求
4. **升级路径**：生产部署可接入 Docker / isolate / cgroup，方案成熟且明确

---

## 6. 常见问题：学生提交恶意代码怎么办？

### Q: 学生提交 `import os; os.system("rm -rf /")` 会怎样？

**Python**：`ASTAnalyzerAgent` 静态审计会拦截 `import os`，直接返回 CE，代码不会被执行。

**C++**：`check_cpp_security()` 会拦截 `#include <cstdlib>` 和 `system(` 调用，直接返回 CE。

### Q: 学生提交死循环 `while True: pass` 会怎样？

**Python**：`ASTAnalyzerAgent` 检测到 `while True` 且无 `break`/`return`，静态拦截返回 CE。即使绕过静态检查，`subprocess.run(timeout=3)` 也会在 3 秒后强制终止，返回 TLE。

**C++**：正则检测 `while(true/1)` 且无 `break`，静态拦截返回 CE。运行时同样受 `timeout` 保护。

### Q: 学生提交 fork 炸弹 `import os; [os.fork() for _ in range(100)]` 会怎样？

**Python**：`ASTAnalyzerAgent` 拦截 `import os`，代码不会执行。

**C++**：`check_cpp_security()` 拦截 `fork(` 调用，返回 CE。

### Q: 如果学生绕过静态检查怎么办？

当前静态检查基于 AST / 正则，存在被绕过的可能（如字符串拼接、`__import__`、宏展开等）。这是**当前已知限制**，在生产环境中需通过运行时沙箱（Docker + cgroup + seccomp）解决。当前课程演示场景下，静态检查已覆盖常见攻击模式，风险可控。

### Q: 学生代码能读取服务器文件吗？

当前无文件系统隔离，理论上用户代码可读取宿主文件。但：
- Python 静态审计拦截 `open()`、`import os` 等文件操作
- C++ 静态拦截拦截 `#include <fstream>` 等文件操作头文件
- 生产环境应使用 Docker `--read-only` + 非 root 用户彻底隔离

### Q: 学生代码能访问外网吗？

当前无网络隔离。生产环境应使用 `--network none` 彻底禁止容器内网络访问。

---

## 7. 相关文件索引

| 文件 | 职责 |
|------|------|
| `utils/security.py` | C++ 静态危险调用拦截 |
| `services/oj/runner.py` | Python 判题主流程（子进程 + 超时） |
| `services/oj/cpp_runner.py` | C++ 判题主流程（g++ 编译 + 子进程执行） |
| `services/oj/stdio_runner.py` | 洛谷风格 stdin/stdout 判题 |
| `services/oj/trace_runner.py` | Python Trace（`sys.settrace`） |
| `services/oj/cpp_trace_runner.py` | C++ Trace（GDB MI） |
| `services/oj/static_audit.py` | 静态审计门闸（AST 分析） |
| `services/agents/ast_analyzer.py` | AST 静态分析器（Python ast + C++ 正则 + LLM） |
