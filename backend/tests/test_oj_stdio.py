"""OJ 判题：stdio 模式 Python / C++。"""

from __future__ import annotations

import shutil

import pytest

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


@pytest.mark.skipif(not shutil.which("g++"), reason="g++ not installed")
def test_cpp_stdio_ac() -> None:
    summary = run_cases_stdio(CPP_A_PLUS_B, cases=CASES, language="cpp")
    assert summary.passed == 1
    assert summary.cases[0].verdict == "AC"
