from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from services.oj.compare import values_equal
from services.oj.runner import CaseResult, RunSummary, _preview_args, _preview_value
from utils.security import CPP_SECURITY_MESSAGE, CppSecurityViolation, check_cpp_security

CPP_HELPERS = textwrap.dedent(
    """
    struct ListNode {
        int val;
        ListNode* next;
        ListNode(int x) : val(x), next(nullptr) {}
    };
    struct TreeNode {
        int val;
        TreeNode *left, *right;
        TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    };
    ListNode* vecToList(const vector<int>& v) {
        if (v.empty()) return nullptr;
        ListNode* head = new ListNode(v[0]);
        ListNode* cur = head;
        for (size_t i = 1; i < v.size(); ++i) {
            cur->next = new ListNode(v[i]);
            cur = cur->next;
        }
        return head;
    }
    vector<int> listToVec(ListNode* head) {
        vector<int> out;
        while (head) { out.push_back(head->val); head = head->next; }
        return out;
    }
    pair<ListNode*, ListNode*> buildIntersect(
        const vector<int>& pa, const vector<int>& pb, const vector<int>& common) {
        ListNode* tail = common.empty() ? nullptr : vecToList(common);
        auto attach = [&](const vector<int>& pre, ListNode* tailNode) -> ListNode* {
            if (pre.empty()) return tailNode;
            ListNode* head = vecToList(pre);
            ListNode* cur = head;
            while (cur->next) cur = cur->next;
            cur->next = tailNode;
            return head;
        };
        return {attach(pa, tail), attach(pb, tail)};
    }
    """
)


def _to_cpp_literal(val: Any, *, as_list_node: bool = False) -> str:
    if val is None:
        return "nullptr" if as_list_node else "nullptr"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return str(val)
    if isinstance(val, str):
        esc = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{esc}"'
    if isinstance(val, list):
        if as_list_node:
            inner = ", ".join(str(x) for x in val)
            return f"vecToList({{{inner}}})"
        if not val:
            return "vector<int>{}"
        if all(isinstance(x, int) for x in val):
            inner = ", ".join(str(x) for x in val)
            return f"vector<int>{{{inner}}}"
        if all(isinstance(x, str) for x in val):
            inner = ", ".join(_to_cpp_literal(x) for x in val)
            return f"vector<string>{{{inner}}}"
        if all(isinstance(x, list) for x in val):
            rows = []
            for row in val:
                if all(isinstance(y, int) for y in row):
                    rows.append("{" + ", ".join(str(y) for y in row) + "}")
                else:
                    raise TypeError(f"unsupported nested list: {row}")
            return "vector<vector<int>>{" + ", ".join(rows) + "}"
        raise TypeError(f"unsupported list: {val}")
    raise TypeError(f"unsupported value: {type(val)}")


def _brace_block_end(code: str, open_brace: int) -> int:
    depth = 0
    i = open_brace
    while i < len(code):
        ch = code[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(code)


def _remove_cpp_named_blocks(code: str, names: set[str]) -> str:
    """移除用户代码中与评测辅助代码重复的 struct/class 定义。"""
    if not names:
        return code
    pattern = re.compile(
        r"\b(?:struct|class)\s+(" + "|".join(re.escape(n) for n in names) + r")\b"
    )
    out: list[str] = []
    i = 0
    while i < len(code):
        m = pattern.search(code, i)
        if not m:
            out.append(code[i:])
            break
        out.append(code[i : m.start()])
        brace = code.find("{", m.end())
        if brace < 0:
            out.append(code[m.start() :])
            break
        end = _brace_block_end(code, brace)
        if end < len(code) and code[end] == ";":
            end += 1
        i = end
    return "".join(out)


def _remove_cpp_main(code: str) -> str:
    """LeetCode 风格判题由评测器提供 main，需去掉用户自带的 main。"""
    pattern = re.compile(r"\bint\s+main\s*\([^)]*\)\s*\{")
    out: list[str] = []
    i = 0
    while i < len(code):
        m = pattern.search(code, i)
        if not m:
            out.append(code[i:])
            break
        out.append(code[i : m.start()])
        brace = code.find("{", m.end() - 1)
        end = _brace_block_end(code, brace)
        i = end
    return "".join(out)


def _sanitize_user_cpp(code: str, *, inject_helpers: bool) -> str:
    cleaned = code.strip()
    if inject_helpers:
        cleaned = _remove_cpp_named_blocks(cleaned, {"ListNode", "TreeNode"})
    cleaned = _remove_cpp_main(cleaned)
    return cleaned.strip()


def _serialize_result(expr: str, expected: Any, *, var_already_declared: bool = False) -> str:
    """生成将返回值打印为 JSON 的 C++ 代码片段（避免 f-string 与 C++ 下标语法冲突）。"""
    if expected is None:
        return 'cout << "{\\"ok\\":true,\\"result\\":null,\\"ms\\":0}";'
    if isinstance(expected, bool):
        return (
            'cout << "{\\"ok\\":true,\\"result\\":" << ('
            + expr
            + ' ? "true" : "false") << ",\\"ms\\":0}";'
        )
    if isinstance(expected, int):
        return 'cout << "{\\"ok\\":true,\\"result\\":" << ' + expr + ' << ",\\"ms\\":0}";'
    if isinstance(expected, str):
        return (
            'cout << "{\\"ok\\":true,\\"result\\":\\""; '
            "for (char c : "
            + expr
            + ") { if (c=='\\\\') cout<<'\\\\\\\\'; else if (c=='\"') cout<<'\\\\\"'; else cout<<c; } "
            'cout << "\\",\\"ms\\":0}";'
        )
    if isinstance(expected, list):
        if not expected:
            return 'cout << "{\\"ok\\":true,\\"result\\":[],\\"ms\\":0}";'
        if all(isinstance(x, int) for x in expected):
            if var_already_declared:
                return (
                    'cout << "{\\"ok\\":true,\\"result\\":[";\n'
                    f"  for (size_t i=0; i<{expr}.size(); ++i) "
                    f"{{ if(i) cout<<','; cout<<{expr}[i]; }}\n"
                    '  cout << "],\\"ms\\":0}";'
                )
            return (
                "{\n"
                "  auto __v = "
                + expr
                + ";\n"
                '  cout << "{\\"ok\\":true,\\"result\\":[";\n'
                "  for (size_t i=0; i<__v.size(); ++i) { if(i) cout<<','; cout<<__v[i]; }\n"
                '  cout << "],\\"ms\\":0}";\n'
                "}"
            )
        if all(isinstance(x, list) for x in expected):
            if var_already_declared:
                return (
                    'cout << "{\\"ok\\":true,\\"result\\":[";\n'
                    f"  for (size_t i=0; i<{expr}.size(); ++i) {{\n"
                    "    if(i) cout<<',';\n"
                    '    cout<<"[";\n'
                    f"    for (size_t j=0; j<{expr}[i].size(); ++j) "
                    f"{{ if(j) cout<<','; cout<<{expr}[i][j]; }}\n"
                    '    cout<<"]";\n'
                    "  }\n"
                    '  cout << "],\\"ms\\":0}";'
                )
            return (
                "{\n"
                "  auto __v = "
                + expr
                + ";\n"
                '  cout << "{\\"ok\\":true,\\"result\\":[";\n'
                "  for (size_t i=0; i<__v.size(); ++i) {\n"
                "    if(i) cout<<',';\n"
                '    cout<<"[";\n'
                "    for (size_t j=0; j<__v[i].size(); ++j) { if(j) cout<<','; cout<<__v[i][j]; }\n"
                '    cout<<"]";\n'
                "  }\n"
                '  cout << "],\\"ms\\":0}";\n'
                "}"
            )
    return 'cout << "{\\"ok\\":true,\\"result\\":null,\\"ms\\":0}";'


def _build_cpp_source(
    user_code: str,
    *,
    class_name: str,
    method_name: str,
    args: list[Any],
    entry: dict[str, Any],
    expected: Any,
    in_place_arg: int | None,
) -> str:
    list_idx = set(entry.get("list_arg_indices") or [])
    needs_list = entry.get("needs_list_node") or bool(list_idx)

    helpers = CPP_HELPERS if needs_list else ""
    if (
        len(args) == 1
        and isinstance(args[0], dict)
        and "a" in args[0]
        and "b" in args[0]
    ):
        helpers = CPP_HELPERS
        spec = args[0]
        pa = _to_cpp_literal(spec.get("a") or [])
        pb = _to_cpp_literal(spec.get("b") or [])
        pc = _to_cpp_literal(spec.get("common") or [])
        call = (
            f"auto __heads = buildIntersect({pa}, {pb}, {pc}); "
            f"{class_name} __sol; auto __result = __sol.{method_name}(__heads.first, __heads.second);"
        )
    else:
        arg_exprs = []
        for i, a in enumerate(args):
            arg_exprs.append(_to_cpp_literal(a, as_list_node=(i in list_idx)))
        call = f"{class_name} __sol; auto __result = __sol.{method_name}({', '.join(arg_exprs)});"

    if in_place_arg is not None:
        out_expr = _to_cpp_literal(args[in_place_arg])
        if isinstance(args[in_place_arg], list):
            out_expr = "{" + ", ".join(str(x) for x in args[in_place_arg]) + "}"
        print_stmt = (
            'cout << "{\\"ok\\":true,\\"in_place\\":[";\n'
            f"  auto __v = {out_expr};\n"
            "  for (size_t i=0; i<__v.size(); ++i) { if(i) cout<<','; cout<<__v[i]; }\n"
            '  cout << "],\\"ms\\":0}";'
        )
    elif needs_list and expected is not None and isinstance(expected, list):
        print_stmt = (
            "{ ListNode* __r = __result; auto __v = listToVec(__r);\n"
            + _serialize_result("__v", expected, var_already_declared=True)
            + "\n}"
        )
    else:
        print_stmt = _serialize_result("__result", expected)

    user_part = _sanitize_user_cpp(user_code, inject_helpers=bool(helpers))

    return textwrap.dedent(
        f"""
        #include <bits/stdc++.h>
        using namespace std;
        {helpers}
        {user_part}

        int main() {{
            ios::sync_with_stdio(false);
            cin.tie(nullptr);
            {call}
            {print_stmt}
            cout << endl;
            return 0;
        }}
        """
    )


def _toolchain_roots() -> list[Path]:
    """常见 MinGW/MSYS2 安装位置（含 IDE 启动时 PATH 为空的情况）。"""
    import os
    import string

    roots: list[Path] = []
    seen: set[str] = set()

    def add(base: str | Path | None) -> None:
        if not base:
            return
        p = Path(base)
        key = str(p)
        if key in seen:
            return
        seen.add(key)
        roots.append(p)

    for env_key in ("MINGW_PREFIX", "MSYSTEM_PREFIX", "MSYS2_UCRT64"):
        add(os.environ.get(env_key))
    for fixed in (
        r"C:\msys64\ucrt64",
        r"C:\msys64\mingw64",
        r"H:\Dev\msys2\ucrt64",
        Path.home() / "msys64" / "ucrt64",
        Path.home() / "scoop" / "apps" / "msys2" / "current" / "ucrt64",
    ):
        add(fixed)
    for drive in string.ascii_uppercase:
        root = Path(f"{drive}:\\")
        if not root.exists():
            continue
        for tail in (r"msys64\ucrt64", r"Dev\msys2\ucrt64", r"msys2\ucrt64"):
            add(root / tail)
    return roots


def ensure_toolchain_on_path() -> None:
    """将已发现的 toolchain bin 目录注入进程 PATH，便于 gdb/g++ 被子进程找到。"""
    import os

    prepend: list[str] = []
    path_parts = os.environ.get("PATH", "").split(os.pathsep)
    for root in _toolchain_roots():
        bin_dir = root / "bin"
        if not bin_dir.is_dir():
            continue
        s = str(bin_dir)
        if s not in path_parts and s not in prepend:
            prepend.append(s)
    if prepend:
        os.environ["PATH"] = os.pathsep.join(prepend + path_parts)


def _find_gpp() -> str | None:
    import os

    ensure_toolchain_on_path()
    for name in ("g++", "g++.exe", "clang++", "clang++.exe"):
        p = shutil.which(name)
        if p:
            return p
    for env_key in ("GPP", "CXX", "MINGW_GPP"):
        p = os.environ.get(env_key)
        if p and Path(p).is_file():
            return p
    for base in _toolchain_roots():
        cand = base / "bin" / "g++.exe"
        if cand.is_file():
            return str(cand)
    return None


ensure_toolchain_on_path()


def run_cases_cpp(
    user_code: str,
    *,
    entry: dict[str, Any],
    cases: list[dict[str, Any]],
    time_limit_ms: int = 3000,
    order_insensitive: bool = False,
) -> RunSummary:
    from services.oj.static_audit import audit_user_code, run_summary_rejected

    audit = audit_user_code(user_code, language="cpp")
    if not audit.passed:
        return run_summary_rejected(audit, total=max(1, len(cases)))

    gpp = _find_gpp()
    if not gpp:
        return RunSummary(
            verdict="CE",
            passed=0,
            total=len(cases),
            cases=[],
            compile_error="未找到 g++ / clang++，请安装 MinGW 或 LLVM 并加入 PATH",
        )

    class_name = entry.get("class") or "Solution"
    method_name = entry["method"]
    results: list[CaseResult] = []
    passed = 0
    timeout_s = max(1, time_limit_ms / 1000)

    try:
        check_cpp_security(user_code)
    except CppSecurityViolation as e:
        return RunSummary(
            verdict="CE",
            passed=0,
            total=len(cases),
            cases=[],
            compile_error=str(e),
        )

    for idx, case in enumerate(cases):
        args = case.get("args", [])
        expected = case["expected"]
        in_place = case.get("in_place_arg")
        try:
            src = _build_cpp_source(
                user_code,
                class_name=class_name,
                method_name=method_name,
                args=args,
                entry=entry,
                expected=expected,
                in_place_arg=in_place,
            )
        except TypeError as e:
            return RunSummary(
                verdict="RE",
                passed=passed,
                total=len(cases),
                cases=results,
                compile_error=str(e),
            )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cpp_file = tmp_path / "main.cpp"
            exe_file = tmp_path / "main.exe" if Path(gpp).name.lower().startswith("g++") else tmp_path / "main"
            cpp_file.write_text(src, encoding="utf-8")

            compile = subprocess.run(
                [gpp, "-std=c++17", "-O2", str(cpp_file), "-o", str(exe_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if compile.returncode != 0:
                err = (compile.stderr or compile.stdout or "编译失败").strip()
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="CE",
                        message=err[:800],
                        input_preview=_preview_args(args),
                        expected_preview=_preview_value(expected),
                        actual_preview=None,
                    )
                )
                return RunSummary(
                    verdict="CE",
                    passed=passed,
                    total=len(cases),
                    cases=results,
                    compile_error=err[:800],
                )

            try:
                run = subprocess.run(
                    [str(exe_file)],
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    cwd=str(tmp_path),
                )
            except subprocess.TimeoutExpired:
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="TLE",
                        message=f"超出时间限制 {time_limit_ms}ms",
                        input_preview=_preview_args(args),
                        expected_preview=_preview_value(expected),
                        actual_preview=None,
                    )
                )
                return RunSummary(verdict="TLE", passed=passed, total=len(cases), cases=results)

            if run.returncode != 0:
                err = (run.stderr or run.stdout or "运行错误").strip()
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="RE",
                        message=err[:800],
                        input_preview=_preview_args(args),
                        expected_preview=_preview_value(expected),
                        actual_preview=None,
                    )
                )
                return RunSummary(verdict="RE", passed=passed, total=len(cases), cases=results)

            stdout = run.stdout.strip()
            try:
                payload = json.loads(stdout.splitlines()[-1])
                actual = payload.get("result")
                if in_place is not None and "in_place" in payload:
                    actual = payload.get("in_place")
            except (json.JSONDecodeError, IndexError):
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="RE",
                        message=f"无法解析输出: {stdout[:400]}",
                        input_preview=_preview_args(args),
                        expected_preview=_preview_value(expected),
                        actual_preview=stdout[:400] or None,
                    )
                )
                return RunSummary(verdict="RE", passed=passed, total=len(cases), cases=results)

            if values_equal(actual, expected, order_insensitive=order_insensitive):
                passed += 1
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="AC",
                        message="通过",
                        input_preview=_preview_args(args),
                        expected_preview=_preview_value(expected),
                        actual_preview=_preview_value(actual),
                    )
                )
            else:
                results.append(
                    CaseResult(
                        index=idx,
                        verdict="WA",
                        message="答案错误",
                        input_preview=_preview_args(args),
                        expected_preview=_preview_value(expected),
                        actual_preview=_preview_value(actual),
                    )
                )
                return RunSummary(verdict="WA", passed=passed, total=len(cases), cases=results)

    return RunSummary(verdict="AC", passed=passed, total=len(cases), cases=results)
