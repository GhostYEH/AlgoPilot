"""
校验全站 OJ 洛谷 stdio 配置与测例格式。

用法（后端根目录）:
  python scripts/verify_oj_stdio.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from services.oj.problem_store import get_cases, get_public_problem  # noqa: E402
from services.oj.stdio_io import ensure_stdio_fields  # noqa: E402
from services.oj.stdio_runner import run_cases_stdio  # noqa: E402

TESTS_PATH = BACKEND_ROOT / "data" / "oj" / "tests_bundle.json"
FRONTEND_BUNDLE = (
    BACKEND_ROOT.parent
    / "frontend"
    / "public"
    / "oj"
    / "bundle.json"
)


def _load_bundle() -> dict:
    return json.loads(TESTS_PATH.read_text(encoding="utf-8"))


def check_config(bundle: dict) -> list[str]:
    errors: list[str] = []
    for slug, cfg in bundle.items():
        if cfg.get("judge_mode") != "stdio":
            errors.append(f"{slug}: judge_mode={cfg.get('judge_mode')}")
        if (cfg.get("entry") or {}).get("mode") != "stdio":
            errors.append(f"{slug}: entry.mode not stdio")
        sc = cfg.get("starter_code") or {}
        if "int main" not in sc.get("cpp", ""):
            errors.append(f"{slug}: cpp starter missing main")
        if "def main" not in sc.get("python", ""):
            errors.append(f"{slug}: python starter missing main")
        for label, cases in [("samples", cfg.get("samples") or []), ("hidden", cfg.get("hidden") or [])]:
            for i, c in enumerate(cases):
                fixed = ensure_stdio_fields(c)
                if fixed.get("stdin") is None or fixed.get("stdout") is None:
                    errors.append(f"{slug}: {label}[{i}] missing stdin/stdout")
        try:
            p = get_public_problem(slug)
            if not p["ready"] or p["judge_mode"] != "stdio":
                errors.append(f"{slug}: public problem not ready/stdio")
        except Exception as e:
            errors.append(f"{slug}: get_public_problem failed: {e}")
    return errors


def check_runner_echo(bundle: dict) -> list[str]:
    """用「直接输出期望 stdout」验证 runner 与测例格式。"""
    errors: list[str] = []
    for slug in sorted(bundle):
        cases = get_cases(slug, mode="run")
        for ci, case in enumerate(cases):
            exp = case.get("stdout", "")
            code = (
                "import sys\n"
                f"exp = {exp!r}\n"
                "sys.stdout.write(exp if exp.endswith('\\n') else exp + '\\n')\n"
            )
            r = run_cases_stdio(code, cases=[case], language="python")
            if r.verdict != "AC":
                msg = r.cases[0].message if r.cases else r.verdict
                errors.append(f"{slug} case {ci}: {msg[:120]}")
                break
    return errors


def check_frontend_bundle() -> list[str]:
    errors: list[str] = []
    if not FRONTEND_BUNDLE.is_file():
        errors.append(f"missing frontend bundle: {FRONTEND_BUNDLE}")
        return errors
    pub = json.loads(FRONTEND_BUNDLE.read_text(encoding="utf-8"))
    backend = _load_bundle()
    lc = [s for s, v in pub.items() if v.get("judge_mode") == "leetcode"]
    if lc:
        errors.append(f"frontend bundle still has leetcode: {lc[:5]}")
    for slug in backend:
        if slug not in pub:
            errors.append(f"frontend bundle missing slug: {slug}")
        elif pub[slug].get("judge_mode") != "stdio":
            errors.append(f"frontend {slug} not stdio")
    return errors


def main() -> int:
    bundle = _load_bundle()
    all_errors: list[str] = []
    all_errors.extend(check_config(bundle))
    all_errors.extend(check_runner_echo(bundle))
    all_errors.extend(check_frontend_bundle())

    print(f"Problems in tests_bundle: {len(bundle)}")
    if all_errors:
        print(f"FAILED ({len(all_errors)} issues):")
        for e in all_errors:
            print(" -", e)
        return 1
    print("OK: all stdio checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
