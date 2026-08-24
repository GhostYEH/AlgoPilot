"""Execution Evidence Engine 统一数据模型与组装器测试。

AlgoPilot 核心创新：将 OJ 判题 + Trace + 静态分析 + AI 诊断
统一抽象为 ExecutionEvidence，确保诊断结论可追溯、可展示、可验证。
"""

from __future__ import annotations

from services.evidence.execution_evidence_builder import build_execution_evidence


class TestExecutionEvidenceAssembly:
    def test_minimal_evidence(self):
        ev = build_execution_evidence(problem_slug="two-sum")
        assert ev.problem_slug == "two-sum"
        assert ev.language == "python"
        assert ev.compile_result.verdict == "CE"
        assert ev.static_analysis.passed is True
        assert ev.failed_test_cases == []
        assert ev.has_execution_evidence is False

    def test_judge_wa_produces_failed_cases(self):
        ev = build_execution_evidence(
            problem_slug="binary-search",
            judge_result={
                "verdict": "WA",
                "passed": 2,
                "total": 3,
                "cases": [
                    {"index": 0, "verdict": "AC", "input_preview": "[1,2]", "expected_preview": "1"},
                    {
                        "index": 1,
                        "verdict": "WA",
                        "input_preview": "[1,3,5,7] target=7",
                        "expected_preview": "3",
                        "actual_preview": "-1",
                    },
                ],
            },
        )
        assert ev.compile_result.verdict == "WA"
        assert ev.passed_cases == 2
        assert ev.total_cases == 3
        assert len(ev.failed_test_cases) == 1
        fc = ev.failed_test_cases[0]
        assert fc.input_preview == "[1,3,5,7] target=7"
        assert fc.expected_output == "3"
        assert fc.actual_output == "-1"
        assert ev.has_execution_evidence is True

    def test_static_audit_rejection(self):
        ev = build_execution_evidence(
            static_audit={
                "passed": False,
                "reason": "检测到 while True 死循环",
                "findings": [{"type": "infinite_loop"}],
            },
        )
        assert ev.static_analysis.passed is False
        assert ev.static_analysis.reason == "检测到 while True 死循环"
        assert ev.has_execution_evidence is True

    def test_trace_evidence_attached(self):
        ev = build_execution_evidence(
            trace_result={
                "verdict": "OK",
                "user_line_count": 10,
                "steps": [
                    {"line": 1, "vars": {"i": 0}},
                    {"line": 2, "vars": {"i": 1}},
                ],
                "narrations": [{"step_index": 0, "text": "初始化"}],
            },
        )
        assert ev.execution_trace.available is True
        assert ev.execution_trace.total_steps == 2
        assert ev.execution_trace.user_line_count == 10
        assert ev.has_execution_evidence is True

    def test_ai_diagnosis_with_first_divergence(self):
        ev = build_execution_evidence(
            problem_slug="binary-search",
            source_code="while left < right:",
            judge_result={"verdict": "WA", "passed": 0, "total": 1, "cases": []},
            ai_diagnosis={
                "bug_step_index": 4,
                "bug_line": 17,
                "root_cause": "闭区间循环条件导致提前退出",
                "actual_state": "left=3, right=3",
                "expected_state": "left=3, right=3 仍含候选元素",
                "invariant": "闭区间 [left, right]",
                "confidence": "high",
                "source": "ai_with_evidence",
                "hints": [
                    {"level": 1, "title": "循环终止", "content": "检查循环什么时候停止。"},
                    {"level": 2, "title": "边界观察", "content": "left == right 时是否应继续？"},
                ],
            },
        )
        diag = ev.bug_diagnosis
        assert diag.first_divergence.detected is True
        assert diag.first_divergence.step_index == 4
        assert diag.first_divergence.line == 17
        assert diag.first_divergence.student_state == "left=3, right=3"
        assert diag.confidence == "high"
        assert diag.confidence_source == "ai_with_evidence"
        assert 17 in diag.suspicious_lines
        assert len(ev.layered_hints) == 2
        assert ev.layered_hints[0].level == 1
        assert ev.is_diagnosed is True

    def test_bug_type_classified_from_evidence(self):
        ev = build_execution_evidence(
            problem_slug="reverse-linked-list",
            source_code="curr = curr.next",
            judge_result={"verdict": "WA", "passed": 0, "total": 1, "cases": []},
            ai_diagnosis={"root_cause": "next 指针未移动，反转失败"},
        )
        assert ev.bug_diagnosis.bug_type == "pointer_update_error"
        assert ev.bug_diagnosis.bug_type_label == "指针更新错误"

    def test_diagnosis_evidence_text_built(self):
        ev = build_execution_evidence(
            problem_slug="binary-search",
            judge_result={"verdict": "WA", "passed": 0, "total": 1, "cases": []},
            ai_diagnosis={
                "bug_step_index": 3,
                "bug_line": 17,
                "root_cause": "循环提前终止",
            },
        )
        text = ev.bug_diagnosis.diagnosis_evidence
        assert "错误类型" in text
        assert "Line 17" in text
        assert "首次状态偏离" in text
        assert "循环提前终止" in text

    def test_edge_cases_appended(self):
        ev = build_execution_evidence(
            judge_result={"verdict": "WA", "passed": 0, "total": 1, "cases": []},
            edge_cases=[
                {
                    "input_preview": "空数组",
                    "expected_preview": "0",
                    "reason": "未处理空输入边界",
                    "source": "llm",
                }
            ],
        )
        assert len(ev.failed_test_cases) == 1
        assert ev.failed_test_cases[0].why_exposes_bug == "未处理空输入边界"
        assert ev.failed_test_cases[0].source == "llm"

    def test_ai_unavailable_sets_fallback(self):
        ev = build_execution_evidence(
            ai_available=False,
            fallback_reason="LLM 不可用，使用规则诊断兜底",
        )
        assert ev.ai_available is False
        assert ev.fallback_reason
        assert ev.bug_diagnosis.source == "fallback"

    def test_knowledge_mappings_attached(self):
        ev = build_execution_evidence(
            knowledge_mappings=[
                {"module_key": "array", "concept_id": "binary-search", "knowledge_point": "闭区间不变量", "mastery": 56},
            ],
        )
        assert len(ev.related_knowledge_points) == 1
        assert ev.related_knowledge_points[0].knowledge_point == "闭区间不变量"
        assert ev.related_knowledge_points[0].mastery == 56.0
