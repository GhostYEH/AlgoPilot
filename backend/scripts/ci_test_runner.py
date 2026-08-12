"""CI 测试运行器：分离 fast/slow 测试，支持分阶段 CI。

用法：
    python scripts/ci_test_runner.py fast     # 仅运行快速测试（CI 默认）
    python scripts/ci_test_runner.py slow     # 仅运行 slow 测试（定时/手动）
    python scripts/ci_test_runner.py all      # 运行全部测试
    python scripts/ci_test_runner.py migrate  # 仅运行迁移测试

slow 测试标记：@pytest.mark.slow
    - 依赖真实 subprocess（Python trace runner、代码执行）
    - 依赖外部 LLM API（ai_diagnose 调用）
    - 可能耗时 5-30 秒/个
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PYTHON = sys.executable

_PHASES = {
    "fast": [
        "-m", "not slow",
        "--tb=short",
        "-q",
    ],
    "slow": [
        "-m", "slow",
        "--tb=short",
        "-v",
    ],
    "all": [
        "--tb=short",
        "-q",
    ],
    "migrate": [
        "tests/test_migration_applied_evidence.py",
        "--tb=short",
        "-v",
    ],
}


def run_phase(phase: str) -> int:
    if phase not in _PHASES:
        print(f"未知阶段: {phase}")
        print(f"可用阶段: {', '.join(_PHASES.keys())}")
        return 2

    args = [_PYTHON, "-m", "pytest"] + _PHASES[phase]
    print(f"\n{'='*60}")
    print(f"运行测试阶段: {phase}")
    print(f"命令: {' '.join(args)}")
    print(f"{'='*60}\n")

    result = subprocess.run(args, cwd=str(_BACKEND_DIR))
    return result.returncode


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python scripts/ci_test_runner.py <phase>")
        print(f"阶段: {', '.join(_PHASES.keys())}")
        return 2

    phase = sys.argv[1]
    return run_phase(phase)


if __name__ == "__main__":
    sys.exit(main())