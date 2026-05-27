"""ASTAnalyzerAgent 冒烟测试：python -m scripts.test_ast_analyzer（在 backend 目录）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.agents.ast_analyzer import ASTAnalyzerAgent  # noqa: E402


def main() -> None:
    bad_py = """
class Solution:
    def f(self, nums):
        left, right = 0, len(nums) - 1
        while left < right:
            if nums[left] < nums[right]:
                pass
            else:
                right -= 1
"""
    r = ASTAnalyzerAgent.audit(bad_py, language="python")
    assert not r.passed, r.reason
    print("python stale pointer:", r.reason[:100])

    bad_cpp = "int main(){ int left=0,right=10; while(left<right){} return 0; }"
    r2 = ASTAnalyzerAgent.audit(bad_cpp, language="cpp")
    assert not r2.passed, r2.reason
    print("cpp stale pointer:", r2.reason[:100])

    safe_cpp = "int main(){ return 0; }"
    r_safe = ASTAnalyzerAgent.audit(safe_cpp, language="cpp")
    assert r_safe.passed and r_safe.source == "fast_pass"
    print("cpp no-loop fast pass:", r_safe.source)

    good = "for i in range(10):\n    print(i)\n"
    r3 = ASTAnalyzerAgent.audit(good, language="python")
    assert r3.passed
    print("ok: benign loop passed")


if __name__ == "__main__":
    main()
