"""临时检查特定题目的所有完整测试用例。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
BUNDLE_PATH = BACKEND / "data" / "oj" / "tests_bundle.json"

SLUGS = [
    "linked-list-cycle",
    "linked-list-cycle-ii",
    "intersection-of-two-linked-lists",
    "design-linked-list",
    "implement-stack-using-queues",
    "implement-queue-using-stacks",
]


def main() -> int:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    for slug in SLUGS:
        cfg = bundle.get(slug)
        print(f"\n=== [{slug}] ===")
        if cfg is None:
            print("  [缺失]")
            continue
        for label in ("samples", "hidden"):
            cases = cfg.get(label) or []
            for i, c in enumerate(cases):
                args = c.get("args")
                exp = c.get("expected")
                stdin = (c.get("stdin") or "").replace("\n", "\\n")
                stdout = (c.get("stdout") or "").replace("\n", "\\n")
                print(f"  {label}[{i}] args={json.dumps(args, ensure_ascii=False)}")
                print(f"         expected={json.dumps(exp, ensure_ascii=False)}")
                print(f"         stdin={stdin}")
                print(f"         stdout={stdout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
