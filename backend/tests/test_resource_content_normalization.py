import pytest

from services.agents.resource_roles import (
    PersonaHints,
    ConceptAgent,
    ReadingAgent,
    ResourceRoleAgent,
    ScenarioAgent,
    TraceAgent,
    _assess_trace_quality,
    _fallback_trace_payload,
    _parse_json_object,
    _record_trace,
    _trace_payload_matches_topic,
)


def test_parse_json_object_unwraps_double_encoded_json():
    raw = '"{\\"domain_narrative\\":{\\"headline\\":\\"任务\\"},\\"structure_logic\\":{\\"code_framework\\":\\"# TODO\\"}}"'

    payload = _parse_json_object(raw)

    assert payload["domain_narrative"]["headline"] == "任务"
    assert payload["structure_logic"]["code_framework"] == "# TODO"


def test_parse_json_object_recovers_json_prefix_with_escaped_newlines():
    raw = 'json\\n{\\n  \\"domain_narrative\\": {\\"headline\\": \\"任务\\"},\\n  \\"structure_logic\\": {\\"code_framework\\": \\"# TODO\\"}\\n}'

    payload = _parse_json_object(raw)

    assert payload["domain_narrative"]["headline"] == "任务"


def test_scenario_never_turns_broken_json_into_editor_code():
    raw = 'json\\n{\\n  \\"domain_narrative\\": {\\"headline\\": \\"任务\\"}'

    content = ScenarioAgent().normalize_output(
        raw,
        hints=PersonaHints(),
        topic="链表反转",
    )
    payload = _parse_json_object(content)

    framework = payload["structure_logic"]["code_framework"]
    assert "# TODO" in framework
    compile(framework, "<test-scenario>", "exec")
    assert "domain_narrative" not in framework
    assert "反转" in payload["domain_narrative"]["story"]
    assert "链表" not in payload["domain_narrative"]["story"]


def test_trace_quality_rejects_single_scalar_shell():
    quality = _assess_trace_quality([
        {"line": 1, "changed": ["n"], "vars": {"n": {"type": "int", "value": 3}}},
    ])

    assert quality["trace_quality_passed"] is False
    assert "有效步骤不足（1/4）" in quality["trace_quality_reasons"]


def test_trace_quality_accepts_teachable_state_changes():
    steps = [
        {"line": 1, "changed": ["nums"], "vars": {"nums": {"type": "list", "value": [1, 2]}}},
        {"line": 2, "changed": ["total"], "vars": {"nums": {"type": "list", "value": [1, 2]}, "total": {"type": "int", "value": 0}}},
        {"line": 3, "changed": ["total"], "vars": {"nums": {"type": "list", "value": [1, 2]}, "total": {"type": "int", "value": 1}}},
        {"line": 3, "changed": ["total"], "vars": {"nums": {"type": "list", "value": [1, 2]}, "total": {"type": "int", "value": 3}}},
    ]

    assert _assess_trace_quality(steps)["trace_quality_passed"] is True


def test_trace_agent_uses_topic_safe_fallback_instead_of_unrelated_sum_demo():
    content = TraceAgent().normalize_output(
        "not-json",
        hints=PersonaHints(),
        topic="链表反转",
    )
    payload = _parse_json_object(content)

    assert "next_index" in payload["code"]
    assert payload["stdout"] == "4 3 2 1\n"
    assert payload["generated_fallback"] == "topic_safe_trace"


def test_trace_topic_alignment_rejects_unrelated_algorithm():
    assert _trace_payload_matches_topic(
        {
            "title": "数组求和",
            "narration_hint": "观察累加器变化",
            "code": "print(sum(map(int, input().split())))",
        },
        topic="链表反转",
    ) is False


@pytest.mark.asyncio
async def test_trace_record_requires_actual_output_to_match_expected():
    code = (
        "nums = list(map(int, input().split()))\n"
        "total = 0\n"
        "for value in nums:\n"
        "    total += value\n"
        "print(total)\n"
    )
    result = await _record_trace(
        code,
        "1 2 3\n",
        expected_stdout="999\n",
        topic="数组求和",
    )

    assert result["verdict"] == "OK"
    assert result["trace_quality_passed"] is False
    assert any("实际输出与期望输出不一致" in reason for reason in result["trace_quality_reasons"])


@pytest.mark.asyncio
async def test_trace_agent_replaces_runnable_but_untraceable_llm_code(monkeypatch):
    async def fake_generate(self, **kwargs):
        return (
            "Trace · dp · 状态转移",
            '''{
              "code": "def climb_stairs(n):\\n    return n\\n",
              "stdin": "5\\n",
              "stdout": "5\\n",
              "title": "动态规划状态转移",
              "narration_hint": "观察状态变化"
            }''',
            {"format": "trace_json"},
        )

    monkeypatch.setattr(ResourceRoleAgent, "generate", fake_generate)

    _, content, meta = await TraceAgent().generate(
        topic="动态规划的状态转移方程",
        profile_block="",
        module_key="dp",
        chunks=[],
    )
    payload = _parse_json_object(content)

    assert payload["generated_fallback"] == "topic_safe_trace"
    assert payload["steps"]
    assert payload["verdict"] == "OK"
    assert meta["trace_quality_passed"] is True
    assert meta["trace_recovered"] is True
    assert meta["trace_source"] == "topic_safe_fallback"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topic",
    [
        "数组入门",
        "链表入门",
        "哈希表入门",
        "字符串入门",
        "双指针法入门",
        "栈与队列入门",
        "排序算法入门",
        "二叉树入门",
        "回溯算法入门",
        "贪心算法入门",
        "动态规划入门",
        "单调栈入门",
        "图论入门",
    ],
)
async def test_every_teacher_module_has_an_executable_trace_fallback(topic):
    payload = _fallback_trace_payload(topic=topic)

    assert payload["generated_fallback"] == "topic_safe_trace"
    assert _trace_payload_matches_topic(payload, topic=topic) is True

    result = await _record_trace(
        payload["code"],
        payload["stdin"],
        expected_stdout=payload["stdout"],
        topic=topic,
    )

    assert result["verdict"] == "OK", (topic, result["message"])
    assert result["trace_quality_passed"] is True, (
        topic,
        result["trace_quality_reasons"],
    )
    assert result["steps"]


def test_reading_agent_replaces_prompt_placeholders_with_actionable_tasks():
    raw = '''{
      "reading_goal": "掌握链表反转并能解释指针更新顺序",
      "levels": [
        {"level":"基础","items":[{"title":"教材/文献/工程材料名称","why":"为什么读","task":"阅读"}]},
        {"level":"进阶","items":[{"title":"实现分析","why":"理解不同写法的差异","task":"比较实现并记录结论"}]},
        {"level":"挑战","items":[{"title":"证明练习","why":"训练严谨论证和边界分析","task":"写出循环不变量证明"}]}
      ]
    }'''

    content = ReadingAgent().normalize_output(
        raw,
        hints=PersonaHints(),
        topic="链表反转",
        chunks=[],
    )
    payload = _parse_json_object(content)
    first = payload["levels"][0]["items"][0]

    assert "工程材料名称" not in first["title"]
    assert len(first["why"]) >= 12
    assert any(action in first["task"] for action in ("手算", "比较", "整理"))


def test_concept_agent_recovers_domain_nature_schema_drift():
    raw = '''{
      "domain_nature": "业务域",
      "structure_logic": {
        "learning_objectives": ["掌握排序算法"],
        "abstract_model": "形式化问题抽象",
        "data_structures": ["数组"],
        "algorithm_outline": [
          {"headline":"货箱排序任务","story":"调度员需要把顺序混乱的货箱按编号重新排列，任何遗漏都会造成装载冲突。"}
        ],
        "time_complexity":"O(n^2)",
        "space_complexity":"O(1)",
        "correctness_proof":"相邻逆序对逐步减少直至为零。",
        "pitfalls":["边界"]
      }
    }'''

    content = ConceptAgent().normalize_output(
        raw,
        hints=PersonaHints(),
        topic="排序算法",
    )
    payload = _parse_json_object(content)

    assert "货箱" in payload["domain_narrative"]["headline"]
    assert "排序" not in payload["domain_narrative"]["headline"]
    assert len(payload["structure_logic"]["algorithm_outline"]) >= 60
    assert len(payload["structure_logic"]["pitfalls"]) >= 2


def test_sorting_scenario_replaces_copied_schema_with_valid_practice_code():
    raw = '''{
      "domain_narrative":{"headline":"排序任务","story":"调度员必须重新排列货箱，避免装载顺序发生冲突。","mission":"恢复正确顺序。"},
      "structure_logic":{
        "problem_formalization":"给定序列并返回排序结果",
        "data_structures":["数组"],
        "code_framework":"Python3 代码框架，15～35 行，关键逻辑处使用 # TODO",
        "step_hints":["确定边界","相邻比较","提前结束"],
        "time_complexity":"O(n^2)",
        "space_complexity":"O(1)",
        "correctness_proof":"每轮确定一个元素。"
      }
    }'''

    content = ScenarioAgent().normalize_output(
        raw,
        hints=PersonaHints(),
        topic="排序算法",
    )
    payload = _parse_json_object(content)
    framework = payload["structure_logic"]["code_framework"]

    compile(framework, "<sorting-scenario>", "exec")
    assert "bubble_sort" in framework
    assert "# TODO" in framework
    assert "输入：" in payload["structure_logic"]["problem_formalization"]


def test_reading_agent_expands_short_goal():
    raw = '''{"reading_goal":"掌握排序算法","levels":[
      {"level":"基础","items":[]},{"level":"进阶","items":[]},{"level":"挑战","items":[]}
    ]}'''

    content = ReadingAgent().normalize_output(
        raw,
        hints=PersonaHints(),
        topic="排序算法",
        chunks=[],
    )

    assert len(_parse_json_object(content)["reading_goal"]) >= 14
