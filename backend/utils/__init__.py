"""工具函数目录（后续扩展：LangChain 工具、星火客户端封装等）"""

import sys


def python_exec_args(script_path: str, *extra_args: str) -> list[str]:
    """返回用于 subprocess.run 的 Python 执行命令列表。

    开发模式下直接使用 sys.executable（python.exe）；
    PyInstaller 打包后使用 ``AlgoPilot.exe --exec-script <path>``，
    由 main.py 中的 --exec-script 分支解释执行。
    """
    if getattr(sys, "frozen", False):
        return [sys.executable, "--exec-script", script_path, *extra_args]
    return [sys.executable, script_path, *extra_args]
