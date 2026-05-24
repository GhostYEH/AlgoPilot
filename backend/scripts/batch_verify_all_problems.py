"""批量验证全部 OJ 题目：ready、逐用例 echo 判题、HTTP API、trace 启动。"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from services.oj.problem_store import (  # noqa: E402
    _merge_starter_code,
    get_cases,
    get_problem,
    get_public_problem,
)
from services.oj.stdio_runner import run_cases_stdio  # noqa: E402

BASE = "http://127.0.0.1:9000"
TESTS_PATH = BACKEND_ROOT / "data" / "oj" / "tests_bundle.json"


def post_run(slug: str, code: str, lang: str = "python") -> dict:
    req = urllib.request.Request(
        f"{BASE}/api/oj/problems/{slug}/run",
        data=json.dumps({"code": code, "language": lang}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def py_echo_code(stdout: str) -> str:
    return (
        "import sys\n"
        f"exp = {stdout!r}\n"
        "sys.stdout.write(exp if exp.endswith('\\n') else exp + '\\n')\n"
    )


def cpp_echo_code(stdout: str) -> str:
    body = stdout.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    if not body.endswith("\\n"):
        body += "\\n"
    return (
        "#include <bits/stdc++.h>\n"
        "using namespace std;\n"
        "int main() {\n"
        f'    cout << "{body}";\n'
        "    return 0;\n"
        "}\n"
    )


def main() -> int:
    bundle = json.loads(TESTS_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    api_fail: list[str] = []
    not_ready: list[str] = []
    py_echo_ok = 0
    py_echo_total = 0
    cpp_echo_ok = 0
    cpp_echo_total = 0
    submit_ok = 0
    submit_total = 0
    http_ok = 0

    for slug in sorted(bundle.keys()):
        try:
            pub = get_public_problem(slug)
            if not pub["ready"]:
                not_ready.append(slug)
                continue

            starter = _merge_starter_code(get_problem(slug)).get("python", "")
            try:
                res = post_run(slug, starter, "python")
                if res.get("verdict") in ("WA", "RE", "AC", "TLE", "CE"):
                    http_ok += 1
                else:
                    api_fail.append(f"{slug}: bad verdict {res.get('verdict')}")
            except urllib.error.URLError as e:
                print(f"后端未启动: {e}")
                return 1
            except Exception as e:
                api_fail.append(f"{slug}: starter HTTP {e}")

            insens = bundle[slug].get("order_insensitive", False)
            for mode in ("run", "submit"):
                cases = get_cases(slug, mode=mode)
                for ci, case in enumerate(cases):
                    exp = case.get("stdout", "")
                    py_code = py_echo_code(exp)
                    cpp_code = cpp_echo_code(exp)
                    case_insens = insens or case.get("order_insensitive", False)

                    py_echo_total += 1
                    rpy = run_cases_stdio(
                        py_code,
                        cases=[case],
                        language="python",
                        order_insensitive=case_insens,
                    )
                    if rpy.verdict != "AC":
                        msg = rpy.cases[0].message if rpy.cases else rpy.verdict
                        errors.append(f"{slug} {mode}[{ci}] py echo: {rpy.verdict} {msg[:60]}")
                    else:
                        py_echo_ok += 1

                    cpp_echo_total += 1
                    rcpp = run_cases_stdio(
                        cpp_code,
                        cases=[case],
                        language="cpp",
                        order_insensitive=case_insens,
                    )
                    if rcpp.verdict != "AC":
                        msg = rcpp.cases[0].message if rcpp.cases else rcpp.verdict
                        ce = rcpp.compile_error or ""
                        errors.append(
                            f"{slug} {mode}[{ci}] cpp echo: {rcpp.verdict} {msg[:40]} {ce[:40]}"
                        )
                    else:
                        cpp_echo_ok += 1

                    if mode == "submit":
                        submit_total += 1
                        if rpy.verdict == "AC":
                            submit_ok += 1

        except Exception as e:
            errors.append(f"{slug}: {e}")

    total = len(bundle)
    ready_n = total - len(not_ready)
    print("=== 全题库批量验证 ===")
    print(f"tests_bundle 题目:   {total}")
    print(f"ready:               {ready_n}")
    print(f"not_ready:             {len(not_ready)}")
    print(f"HTTP starter 可判题:   {http_ok}/{ready_n}")
    print(f"Python echo 用例:    {py_echo_ok}/{py_echo_total}")
    print(f"C++ echo 用例:       {cpp_echo_ok}/{cpp_echo_total}")
    print(f"submit 用例(py):     {submit_ok}/{submit_total}")
    print(f"api_fail:              {len(api_fail)}")
    print(f"errors:                {len(errors)}")

    if not_ready:
        print("\nnot_ready:")
        for s in not_ready:
            print(" -", s)
    if api_fail:
        print("\napi_fail:")
        for x in api_fail[:20]:
            print(" -", x)
    if errors:
        print("\nerrors (first 30):")
        for x in errors[:30]:
            print(" -", x)

    return 1 if (errors or api_fail or not_ready) else 0


if __name__ == "__main__":
    raise SystemExit(main())
