"""AST 静态审计（原 scripts 冒烟逻辑）。"""

from __future__ import annotations

from services.agents.ast_analyzer import ASTAnalyzerAgent


def test_python_stale_pointer_detected() -> None:
    code = """
class Solution:
    def f(self, nums):
        left, right = 0, len(nums) - 1
        while left < right:
            if nums[left] < nums[right]:
                pass
            else:
                right -= 1
"""
    r = ASTAnalyzerAgent.audit(code, language="python")
    assert not r.passed


def test_cpp_safe_no_loop_fast_pass() -> None:
    r = ASTAnalyzerAgent.audit("int main(){ return 0; }", language="cpp")
    assert r.passed and r.source == "fast_pass"
