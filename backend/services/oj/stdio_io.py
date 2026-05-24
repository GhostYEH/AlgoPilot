"""洛谷风格：stdin/stdout 测例格式化与比对。"""

from __future__ import annotations

import json
from typing import Any


def _is_int_or_none_list(val: list[Any]) -> bool:
    return all(x is None or isinstance(x, int) for x in val)


def _format_input_arg(val: Any) -> list[str]:
    """将单个参数转为若干行输入。"""
    if isinstance(val, dict) and {"a", "b", "common"} <= set(val.keys()):
        lines: list[str] = []
        for key in ("a", "b", "common"):
            arr = list(val.get(key) or [])
            lines.append(str(len(arr)))
            if arr:
                lines.append(" ".join(str(x) for x in arr))
        return lines

    if isinstance(val, list):
        if not val:
            return ["0"]
        if _is_int_or_none_list(val):
            tokens = ["null" if x is None else str(x) for x in val]
            return [str(len(val)), " ".join(tokens)]
        if all(isinstance(x, str) for x in val):
            return list(val)
        if all(isinstance(x, list) for x in val) and all(
            all(isinstance(y, int) for y in row) for row in val
        ):
            lines = [str(len(val))]
            for row in val:
                lines.append(" ".join(str(y) for y in row))
            return lines
        return [json.dumps(val, ensure_ascii=False)]

    if isinstance(val, bool):
        return [str(val).lower()]
    if isinstance(val, (int, float)):
        return [str(int(val) if isinstance(val, float) and val == int(val) else val)]
    if isinstance(val, str):
        return [val]
    if val is None:
        return ["0"]
    return [json.dumps(val, ensure_ascii=False)]


def _format_expected_output(expected: Any) -> str:
    if expected is None:
        return "null\n"
    if isinstance(expected, bool):
        return ("true\n" if expected else "false\n")
    if isinstance(expected, int):
        return f"{expected}\n"
    if isinstance(expected, str):
        return expected if expected.endswith("\n") else expected + "\n"
    if isinstance(expected, list):
        if not expected:
            return "\n"
        if all(isinstance(x, int) for x in expected):
            return " ".join(str(x) for x in expected) + "\n"
        if all(isinstance(x, str) for x in expected):
            return json.dumps(expected, ensure_ascii=False) + "\n"
        if all(isinstance(x, list) for x in expected):
            if all(
                all(isinstance(y, int) for y in row) for row in expected if isinstance(row, list)
            ):
                return "\n".join(" ".join(str(y) for y in row) for row in expected) + "\n"
            return json.dumps(expected, ensure_ascii=False) + "\n"
        return json.dumps(expected, ensure_ascii=False) + "\n"
    return str(expected) + "\n"


def leetcode_case_to_stdio(args: list[Any], expected: Any) -> tuple[str, str]:
    """将力扣风格 args/expected 转为洛谷文本测例。"""
    lines_in: list[str] = []
    for arg in args:
        lines_in.extend(_format_input_arg(arg))

    stdin = "\n".join(lines_in)
    if stdin and not stdin.endswith("\n"):
        stdin += "\n"

    stdout = _format_expected_output(expected)
    return stdin, stdout


def ensure_stdio_fields(case: dict[str, Any]) -> dict[str, Any]:
    if case.get("stdin") is not None and case.get("stdout") is not None:
        return case
    args = case.get("args", [])
    expected = case.get("expected")
    stdin, stdout = leetcode_case_to_stdio(args, expected)
    out = {**case, "stdin": stdin, "stdout": stdout}
    return out


def case_input_text(case: dict[str, Any]) -> str:
    if case.get("stdin") is not None:
        return str(case["stdin"]).rstrip("\n")
    if case.get("args") is not None:
        stdin, _ = leetcode_case_to_stdio(case["args"], case.get("expected"))
        return stdin.rstrip("\n")
    return ""


def case_output_text(case: dict[str, Any]) -> str:
    if case.get("stdout") is not None:
        return str(case["stdout"]).rstrip("\n")
    if case.get("expected") is not None:
        _, stdout = leetcode_case_to_stdio(case.get("args", []), case["expected"])
        return stdout.rstrip("\n")
    return ""


def _tokenize(s: str) -> list[str]:
    return s.split()


def stdout_equal(actual: str, expected: str, *, order_insensitive: bool = False) -> bool:
    a = actual.replace("\r\n", "\n").strip()
    e = expected.replace("\r\n", "\n").strip()
    if a == e:
        return True
    if a.splitlines() == e.splitlines():
        return True
    if order_insensitive:
        at = _tokenize(a)
        et = _tokenize(e)
        if at and et and all(t.lstrip("-").isdigit() for t in at + et):
            return sorted(at) == sorted(et)
        al = sorted(a.splitlines())
        el = sorted(e.splitlines())
        if al == el:
            return True
    return False
