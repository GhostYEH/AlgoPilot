"""批量检查题库 Python 可视化调试是否可用（不崩溃）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from api.oj import _pick_trace_case  # noqa: E402
from services.oj.problem_store import _merge_starter_code, get_cases, get_problem  # noqa: E402
from services.oj.trace_runner import run_trace_stdio  # noqa: E402


def main() -> int:
    bundle_path = BACKEND_ROOT / "data" / "oj" / "tests_bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    ok, skip, fail = 0, 0, 0
    fails: list[str] = []

    for slug in sorted(bundle.keys()):
        try:
            prob = get_problem(slug)
            if prob.get("judge_mode") != "stdio":
                skip += 1
                continue
            cases = get_cases(slug, mode="run")
            if not cases:
                skip += 1
                continue
            starter = _merge_starter_code(prob).get("python", "").strip()
            if not starter:
                skip += 1
                continue
            r = run_trace_stdio(starter, case=_pick_trace_case(cases), time_limit_ms=6000)
            if r.verdict in ("OK", "RE", "TLE", "CE"):
                ok += 1
            else:
                fail += 1
                fails.append(f"{slug}: unexpected {r.verdict}")
        except Exception as e:
            fail += 1
            fails.append(f"{slug}: EXC {e}")

    print(f"trace_api_ok={ok} skip={skip} fail={fail} (RE on template-only is expected)")
    for line in fails[:20]:
        print(" ", line)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
