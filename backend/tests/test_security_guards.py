"""Security regressions for roles and OJ pre-execution gates."""

from __future__ import annotations

import pytest

from core.config import settings
from services.oj.static_audit import audit_user_code
from services.oj.stdio_runner import run_cases_stdio


def test_python_host_access_import_is_rejected() -> None:
    result = audit_user_code("import os\nprint('x')", language="python")
    assert not result.passed
    assert result.findings[0].code == "unsafe_import"


def test_python_algorithm_imports_remain_allowed() -> None:
    result = audit_user_code("import sys\nfrom collections import deque\nprint('x')", language="python")
    assert result.passed


def test_cpp_stdio_applies_cpp_security_policy_before_toolchain_execution() -> None:
    result = run_cases_stdio(
        "#include <cstdlib>\nint main() { return 0; }",
        cases=[{"stdin": "", "stdout": ""}],
        language="cpp",
    )
    assert result.verdict == "CE"
    assert "安全系统拦截" in (result.compile_error or "")


def test_production_refuses_builtin_host_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    from main import _check_oj_execution_mode

    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(SystemExit):
        _check_oj_execution_mode()
