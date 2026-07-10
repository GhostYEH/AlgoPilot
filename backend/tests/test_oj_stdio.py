"""OJ 判题：stdio 模式 Python / C++。"""

from __future__ import annotations

import shutil

import pytest

from services.oj.stdio_io import ensure_stdio_fields, stdout_equal
from services.oj.stdio_runner import run_cases_stdio

PYTHON_A_PLUS_B = """
a, b = map(int, input().split())
print(a + b)
"""

CPP_A_PLUS_B = """
#include <iostream>
using namespace std;
int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
"""

CASES = [{"stdin": "2 3\n", "stdout": "5\n"}]


def test_python_stdio_ac() -> None:
    summary = run_cases_stdio(PYTHON_A_PLUS_B, cases=CASES, language="python")
    assert summary.passed == 1
    assert summary.cases[0].verdict == "AC"
    assert summary.cases[0].runtime_ms is not None


def test_python_stdio_all_cases_ac() -> None:
    cases = [
        {"stdin": "2 3\n", "stdout": "5\n"},
        {"stdin": "-10 4\n", "stdout": "-6\n"},
        {"stdin": "0 0\n", "stdout": "0\n"},
    ]
    summary = run_cases_stdio(PYTHON_A_PLUS_B, cases=cases, language="python")
    assert summary.verdict == "AC"
    assert summary.passed == summary.total == 3


def test_python_stdio_wrong_answer_stops_at_first_failure() -> None:
    summary = run_cases_stdio("print(0)", cases=CASES, language="python")
    assert summary.verdict == "WA"
    assert summary.passed == 0
    assert summary.cases[0].actual_preview == "0"


def test_python_stdio_runtime_error() -> None:
    summary = run_cases_stdio("raise RuntimeError('boom')", cases=CASES, language="python")
    assert summary.verdict == "RE"
    assert "RuntimeError: boom" in summary.cases[0].message


def test_python_stdio_respects_subsecond_time_limit() -> None:
    code = "import time\ntime.sleep(0.25)\nprint(5)\n"
    summary = run_cases_stdio(code, cases=CASES, language="python", time_limit_ms=50)
    assert summary.verdict == "TLE"


def test_stdio_rejects_empty_case_list() -> None:
    summary = run_cases_stdio(PYTHON_A_PLUS_B, cases=[], language="python")
    assert summary.verdict == "CE"
    assert summary.total == 0
    assert summary.compile_error == "No test cases configured"


def test_stdio_rejects_non_positive_time_limit() -> None:
    summary = run_cases_stdio(PYTHON_A_PLUS_B, cases=CASES, language="python", time_limit_ms=0)
    assert summary.verdict == "CE"
    assert "positive" in (summary.compile_error or "")


def test_stdio_rejects_unknown_language() -> None:
    summary = run_cases_stdio(PYTHON_A_PLUS_B, cases=CASES, language="javascript")
    assert summary.verdict == "CE"
    assert "Unsupported language" in (summary.compile_error or "")


def test_stdout_equal_normalizes_line_endings_and_outer_whitespace() -> None:
    assert stdout_equal("  5\r\n", "5\n")
    assert not stdout_equal("5  6\n", "5 6\n")


def test_stdout_equal_order_insensitive_numeric_tokens() -> None:
    assert stdout_equal("3 1 2\n", "1 2 3\n", order_insensitive=True)
    assert not stdout_equal("3 1 2\n", "1 2 4\n", order_insensitive=True)


def test_legacy_args_case_is_converted_to_stdio() -> None:
    case = ensure_stdio_fields({"args": [[3, 1, 2]], "expected": [1, 2, 3]})
    code = """
n = int(input())
values = list(map(int, input().split()))
print(*sorted(values[:n]))
"""
    summary = run_cases_stdio(code, cases=[case], language="python")
    assert summary.verdict == "AC"


def test_python_stdio_static_audit_rejects_obvious_infinite_loop() -> None:
    summary = run_cases_stdio("while True:\n    pass\n", cases=CASES, language="python")
    assert summary.verdict == "CE"
    assert summary.compile_error


@pytest.mark.skipif(not shutil.which("g++"), reason="g++ not installed")
def test_cpp_stdio_ac() -> None:
    summary = run_cases_stdio(CPP_A_PLUS_B, cases=CASES, language="cpp")
    assert summary.passed == 1
    assert summary.cases[0].verdict == "AC"


@pytest.mark.skipif(not shutil.which("g++"), reason="g++ not installed")
def test_cpp_stdio_compile_error() -> None:
    summary = run_cases_stdio("int main( {", cases=CASES, language="cpp")
    assert summary.verdict == "CE"
    assert summary.compile_error
