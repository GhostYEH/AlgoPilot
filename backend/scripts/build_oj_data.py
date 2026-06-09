"""
从前端 *Curriculum.ts 提取题目 slug，合并测例，生成 data/oj/catalog.json 与 tests_bundle.json。

用法（在后端根目录）:
  python scripts/build_oj_data.py
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
FRONTEND_MODULES = BACKEND_ROOT.parent / "frontend" / "src" / "modules"
OJ_DIR = BACKEND_ROOT / "data" / "oj"
CATALOG_PATH = OJ_DIR / "catalog.json"
TESTS_PATH = OJ_DIR / "tests_bundle.json"
FRONTEND_BUNDLE = (
    BACKEND_ROOT.parent
    / "frontend"
    / "public"
    / "oj"
    / "bundle.json"
)

# 测例定义（slug -> 完整判题配置）
from oj_test_data import TEST_DEFINITIONS  # noqa: E402
from oj_test_data_extra import EXTRA_TEST_DEFINITIONS  # noqa: E402
from oj_test_data_hidden import HIDDEN_SUPPLEMENT  # noqa: E402
from oj_test_data_samples import SAMPLE_OVERRIDES  # noqa: E402
from services.oj.stdio_io import ensure_stdio_fields  # noqa: E402

ALL_TEST_DEFINITIONS = {**TEST_DEFINITIONS, **EXTRA_TEST_DEFINITIONS}


def _normalize_cases(cases: list[dict[str, Any]], *, stdio: bool) -> list[dict[str, Any]]:
    if not stdio:
        return list(cases)
    return [ensure_stdio_fields(c) for c in cases]


def _apply_sample_overrides(definitions: dict[str, dict]) -> dict[str, dict]:
    """用 SAMPLE_OVERRIDES 替换公开样例（略复杂于原版）。"""
    out: dict[str, dict] = {}
    for slug, cfg in definitions.items():
        override = SAMPLE_OVERRIDES.get(slug)
        if not override:
            out[slug] = cfg
            continue
        stdio = cfg.get("judge_mode") == "stdio" or (cfg.get("entry") or {}).get("mode") == "stdio"
        out[slug] = {**cfg, "samples": _normalize_cases(override, stdio=stdio)}
    return out


def _apply_hidden_supplement(definitions: dict[str, dict]) -> dict[str, dict]:
    """将 HIDDEN_SUPPLEMENT 合并进各题 hidden 测例（洛谷 stdio 格式）。"""
    out: dict[str, dict] = {}
    for slug, cfg in definitions.items():
        extra = HIDDEN_SUPPLEMENT.get(slug)
        if not extra:
            out[slug] = cfg
            continue
        hidden = list(cfg.get("hidden") or [])
        for case in extra:
            hidden.append(ensure_stdio_fields(case))
        out[slug] = {**cfg, "hidden": hidden}
    return out

PRACTICE_RE = re.compile(
    r"\{\s*id:\s*(-?\d+),\s*title:\s*'([^']+)',\s*slug:\s*'([^']+)'\s*\}",
    re.MULTILINE,
)

MODULE_DIR_KEYS = {
    "array": "array",
    "linkedList": "linked-list",
    "hashTable": "hash-table",
    "string": "string",
    "twoPointers": "two-pointers",
    "stackQueue": "stack-queue",
    "sorting": "sorting",
    "binaryTree": "binary-tree",
    "backtracking": "backtracking",
    "greedy": "greedy",
    "dp": "dp",
    "monotonicStack": "monotonic-stack",
    "graph": "graph",
}


def scan_curricula() -> dict[str, dict]:
    by_slug: dict[str, dict] = {}
    for path in sorted(FRONTEND_MODULES.glob("*/*Curriculum.ts")):
        text = path.read_text(encoding="utf-8")
        module_key = MODULE_DIR_KEYS.get(path.parent.name, "")
        for m in PRACTICE_RE.finditer(text):
            lc_id = int(m.group(1))
            title = m.group(2)
            slug = m.group(3)
            if slug not in by_slug or (by_slug[slug].get("lc_id", 0) == 0 and lc_id > 0):
                by_slug[slug] = {
                    "slug": slug,
                    "title": title,
                    "lc_id": max(lc_id, 0),
                    "module_key": module_key,
                }
    return by_slug


def main() -> None:
    OJ_DIR.mkdir(parents=True, exist_ok=True)
    catalog_map = scan_curricula()
    catalog = sorted(catalog_map.values(), key=lambda x: (x.get("lc_id") or 99999, x["slug"]))

    merged_definitions = _apply_hidden_supplement(
        _apply_sample_overrides(ALL_TEST_DEFINITIONS)
    )
    bundle: dict = {}
    for slug, meta in catalog_map.items():
        if slug in merged_definitions:
            bundle[slug] = {
                **merged_definitions[slug],
                "title": meta["title"],
                "lc_id": meta["lc_id"],
                "module_key": meta.get("module_key", ""),
            }

    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    TESTS_PATH.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    # 前端离线题库（不含 hidden 测例）
    public_bundle: dict[str, dict] = {}
    for slug, cfg in bundle.items():
        meta = catalog_map.get(slug, {})
        samples = cfg.get("samples") or []
        hidden = cfg.get("hidden") or []
        if cfg.get("judge_mode") == "stdio":
            public_samples = [
                {"stdin": c.get("stdin", ""), "stdout": c.get("stdout", "")}
                for c in samples
            ]
        else:
            public_samples = [
                {"args": c.get("args", []), "expected": c.get("expected")}
                for c in samples
            ]
        public_bundle[slug] = {
            "slug": slug,
            "title": cfg.get("title") or meta.get("title") or slug,
            "lc_id": cfg.get("lc_id", meta.get("lc_id", 0)),
            "difficulty": cfg.get("difficulty", "medium"),
            "description": cfg.get("description")
            or f"## {meta.get('title', slug)}\n\n请按洛谷格式使用标准输入/输出完成本题。",
            "judge_mode": cfg.get("judge_mode", "stdio"),
            "entry": cfg.get("entry"),
            "starter_code": cfg.get("starter_code", {}),
            "samples": public_samples,
            "hidden_count": len(hidden),
            "ready": bool(
                (samples or hidden)
                and (
                    cfg.get("judge_mode") == "stdio"
                    or cfg.get("entry")
                )
            ),
            "time_limit_ms": cfg.get("time_limit_ms", 3000),
            "order_insensitive": cfg.get("order_insensitive", False),
            "module_key": cfg.get("module_key", meta.get("module_key", "")),
            "tags": cfg.get("tags", []),
            "common_errors": cfg.get("common_errors", []),
        }
    FRONTEND_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_BUNDLE.write_text(
        json.dumps(public_bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    dist_bundle = (
        BACKEND_ROOT.parent
        / "frontend"
        / "dist"
        / "oj"
        / "bundle.json"
    )
    if dist_bundle.parent.is_dir():
        shutil.copy2(FRONTEND_BUNDLE, dist_bundle)
        print(f"synced dist bundle -> {dist_bundle}")

    print(f"catalog: {len(catalog)} problems")
    hidden_slugs = len(HIDDEN_SUPPLEMENT)
    sample_slugs = len(SAMPLE_OVERRIDES)
    print(
        f"tests_bundle: {len(bundle)} with test cases "
        f"(base {len(TEST_DEFINITIONS)} + extra {len(EXTRA_TEST_DEFINITIONS)}, "
        f"sample upgrade {sample_slugs}, hidden supplement {hidden_slugs})"
    )
    missing = [p["slug"] for p in catalog if p["slug"] not in bundle]
    if missing:
        print(f"WARNING: {len(missing)} catalog slugs still without tests: {missing[:8]}...")
    print(f"frontend bundle: {len(public_bundle)} -> {FRONTEND_BUNDLE}")

    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    from verify_oj_stdio import main as verify_main  # noqa: E402
    from audit_oj_full import main as audit_main  # noqa: E402

    if verify_main() != 0:
        raise SystemExit("verify_oj_stdio failed after build")
    if audit_main() != 0:
        raise SystemExit("audit_oj_full failed after build")


if __name__ == "__main__":
    main()
