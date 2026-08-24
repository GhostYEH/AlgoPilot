"""Bug 分类系统（error_patterns）单元测试。

AlgoPilot 核心创新之一：基于程序执行证据的 Bug 类型识别。
覆盖 classify_error_type 对 9 种 ErrorType 的规则分类准确性。
"""

from __future__ import annotations

from services.oj.error_patterns import (
    ERROR_TYPE_LABELS,
    ErrorType,
    classify_error_type,
)


class TestErrorTypeLabels:
    def test_all_error_types_have_labels(self):
        from typing import get_args

        all_types = get_args(ErrorType)
        for t in all_types:
            assert t in ERROR_TYPE_LABELS, f"ErrorType {t} 缺少中文标签"

    def test_labels_are_nonempty_chinese(self):
        for key, label in ERROR_TYPE_LABELS.items():
            assert label, f"{key} 标签为空"
            assert len(label) >= 2, f"{key} 标签过短：{label}"


class TestClassifyErrorType:
    def test_tle_verdict_classified_as_complexity(self):
        result = classify_error_type(verdict="TLE")
        assert result == "time_complexity_issue"

    def test_tle_with_pointer_stall_classified_as_loop_condition(self):
        result = classify_error_type(verdict="TLE", analysis="pointer 停滞未推进")
        assert result == "loop_condition_error"

    def test_infinite_loop_keyword(self):
        result = classify_error_type(analysis="死循环导致超时")
        assert result == "time_complexity_issue"

    def test_recursion_base_case(self):
        result = classify_error_type(analysis="递归基线条件错误", trace_summary="栈溢出")
        assert result == "recursion_base_case_error"

    def test_recursion_stack_overflow(self):
        result = classify_error_type(trace_summary="stack overflow")
        assert result == "recursion_base_case_error"

    def test_pointer_update_linked_list(self):
        result = classify_error_type(
            slug="reverse-linked-list",
            analysis="next 指针未正确移动，链表反转失败",
        )
        assert result == "pointer_update_error"

    def test_initialization_dp(self):
        result = classify_error_type(
            slug="climbing-stairs",
            analysis="dp[0] 初始化错误",
        )
        assert result == "initialization_error"

    def test_boundary_condition_empty_input(self):
        result = classify_error_type(analysis="空数组边界条件未处理")
        assert result == "boundary_condition_error"

    def test_boundary_index_overflow(self):
        result = classify_error_type(analysis="数组越界 overflow")
        assert result == "boundary_condition_error"

    def test_state_transition_dp(self):
        result = classify_error_type(
            slug="coin-change",
            analysis="状态转移方程错误",
        )
        assert result == "state_transition_error"

    def test_loop_condition_stall(self):
        result = classify_error_type(analysis="while 循环未收缩窗口")
        assert result == "loop_condition_error"

    def test_data_structure_misuse(self):
        result = classify_error_type(analysis="栈误用为队列")
        assert result == "data_structure_misuse"

    def test_dp_slug_fallback(self):
        result = classify_error_type(slug="unique-paths", title="不同路径")
        assert result == "state_transition_error"

    def test_linked_list_slug_fallback(self):
        result = classify_error_type(slug="reverse-linked-list", title="反转链表")
        assert result == "pointer_update_error"

    def test_unknown_fallback(self):
        result = classify_error_type()
        assert result == "unknown"

    def test_edge_category_boundary(self):
        result = classify_error_type(edge_category="空输入")
        assert result == "boundary_condition_error"

    def test_code_with_off_by_one(self):
        code = "for i in range(n+1):"
        result = classify_error_type(code=code, analysis="边界")
        assert result == "boundary_condition_error"
