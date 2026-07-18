"""临时检查 linked-list/stack-queue/monotonic-stack 题目的当前测试用例状态。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

BUNDLE_PATH = BACKEND / "data" / "oj" / "tests_bundle.json"

TARGET_SLUGS = [
    "remove-nth-node-from-end-of-list",
    "swap-nodes-in-pairs",
    "reverse-nodes-in-k-group",
    "reverse-linked-list-ii",
    "linked-list-cycle",
    "linked-list-cycle-ii",
    "intersection-of-two-linked-lists",
    "remove-linked-list-elements",
    "reverse-linked-list",
    "palindrome-linked-list",
    "delete-node-in-a-linked-list",
    "design-linked-list",
    "middle-of-the-linked-list",
    "valid-parentheses",
    "evaluate-reverse-polish-notation",
    "implement-stack-using-queues",
    "implement-queue-using-stacks",
    "sliding-window-maximum",
    "top-k-frequent-elements",
    "remove-all-adjacent-duplicates-in-string",
    "trapping-rain-water",
    "largest-rectangle-in-histogram",
    "next-greater-element-i",
    "next-greater-element-ii",
    "daily-temperatures",
]


def main() -> int:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    for slug in TARGET_SLUGS:
        cfg = bundle.get(slug)
        print(f"\n=== [{slug}] ===")
        if cfg is None:
            print("  [缺失]")
            continue
        samples = cfg.get("samples") or []
        hidden = cfg.get("hidden") or []
        print(f"  samples={len(samples)} hidden={len(hidden)}")
        print(f"  order_insensitive={cfg.get('order_insensitive')}")
        # 显示第一个 sample 和前 2 个 hidden 的结构
        for label, cases in (("samples", samples), ("hidden", hidden)):
            for i, c in enumerate(cases):
                if label == "samples" and i > 0:
                    continue
                if label == "hidden" and i > 1:
                    break
                args = c.get("args")
                exp = c.get("expected")
                stdin = (c.get("stdin") or "").replace("\n", "\\n")
                stdout = (c.get("stdout") or "").replace("\n", "\\n")
                print(f"  {label}[{i}] args={json.dumps(args, ensure_ascii=False)}")
                print(f"         expected={json.dumps(exp, ensure_ascii=False)}")
                print(f"         stdin={stdin[:120]}")
                print(f"         stdout={stdout[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
