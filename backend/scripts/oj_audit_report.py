"""生成 OJ 审计摘要（stdout）。"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

FRONTEND = BACKEND_ROOT.parent / "frontend"
PUBLIC = FRONTEND / "public" / "oj" / "bundle.json"
DIST = FRONTEND / "dist" / "oj" / "bundle.json"
TESTS = BACKEND_ROOT / "data" / "oj" / "tests_bundle.json"
CATALOG = BACKEND_ROOT / "data" / "oj" / "catalog.json"

RE = re.compile(r"slug:\s*'([^']+)'", re.MULTILINE)


def main() -> None:
    pub = json.loads(PUBLIC.read_text(encoding="utf-8"))
    backend = json.loads(TESTS.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    dist = json.loads(DIST.read_text(encoding="utf-8")) if DIST.is_file() else {}

    cur: dict[str, list[str]] = defaultdict(list)
    for p in (FRONTEND / "src" / "modules").glob("*/*Curriculum.ts"):
        mod = p.parent.name
        for slug in RE.findall(p.read_text(encoding="utf-8")):
            if slug not in backend:
                cur[mod].append(slug)

    print("=== OJ 审计摘要 ===")
    print(f"catalog: {len(catalog)}")
    print(f"有测例 (tests_bundle): {len(backend)}")
    print(f"public bundle: {len(pub)} (stdio: {sum(1 for v in pub.values() if v.get('judge_mode') == 'stdio')})")
    if dist:
        print(f"dist bundle: {len(dist)} (leetcode: {sum(1 for v in dist.values() if v.get('judge_mode') == 'leetcode')})")
        print(f"public/dist keys 一致: {set(pub.keys()) == set(dist.keys())}")
    print(f"课程 practice slug: {sum(len(v) for v in cur.values()) + len(backend)}")
    print(f"课程中可提交 OJ: {len(backend)}")
    print(f"课程中仅离线预览: {sum(len(v) for v in cur.values())}")
    print("\n各模块「有课程链接但无测例」:")
    for mod in sorted(cur):
        print(f"  {mod}: {len(cur[mod])} 题")


def list_ready_by_module() -> None:
    backend = json.loads(TESTS.read_text(encoding="utf-8"))
    practice_re = re.compile(
        r"\{\s*id:\s*(-?\d+),\s*title:\s*'([^']+)',\s*slug:\s*'([^']+)'\s*\}",
        re.MULTILINE,
    )
    by_mod: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for p in (FRONTEND / "src" / "modules").glob("*/*Curriculum.ts"):
        mod = p.parent.name
        for m in practice_re.finditer(p.read_text(encoding="utf-8")):
            slug = m.group(3)
            if slug in backend:
                by_mod[mod].append((m.group(1), slug))
    print("\n=== 可提交 OJ 题目（按模块）===")
    for mod in sorted(by_mod):
        print(f"{mod} ({len(by_mod[mod])})")
        for lc, slug in sorted(by_mod[mod], key=lambda x: int(x[0])):
            print(f"  LC {lc:>4}  {slug}")


if __name__ == "__main__":
    main()
    list_ready_by_module()
