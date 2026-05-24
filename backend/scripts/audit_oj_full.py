"""
全站 OJ 深度审计：题库、课程 slug、前后端一致性、提交测例。

用法（后端根目录）:
  python scripts/audit_oj_full.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from verify_oj_stdio import (  # noqa: E402
    FRONTEND_BUNDLE,
    _load_bundle,
    check_config,
    check_frontend_bundle,
    check_runner_echo,
)
from services.oj.problem_store import get_cases, get_public_problem  # noqa: E402
from services.oj.stdio_runner import run_cases_stdio  # noqa: E402

CATALOG_PATH = BACKEND_ROOT / "data" / "oj" / "catalog.json"
FRONTEND_MODULES = (
    BACKEND_ROOT.parent / "frontend" / "src" / "modules"
)
DIST_BUNDLE = (
    BACKEND_ROOT.parent
    / "frontend"
    / "dist"
    / "oj"
    / "bundle.json"
)

PRACTICE_RE = re.compile(
    r"\{\s*id:\s*(-?\d+),\s*title:\s*'([^']+)',\s*slug:\s*'([^']+)'\s*\}",
    re.MULTILINE,
)


def scan_curriculum_slugs() -> dict[str, dict]:
    by_slug: dict[str, dict] = {}
    for path in sorted(FRONTEND_MODULES.glob("*/*Curriculum.ts")):
        text = path.read_text(encoding="utf-8")
        module = path.parent.name
        for m in PRACTICE_RE.finditer(text):
            slug = m.group(3)
            by_slug[slug] = {
                "slug": slug,
                "lc_id": int(m.group(1)),
                "title": m.group(2),
                "module": module,
            }
    return by_slug


def check_catalog(bundle: dict) -> list[str]:
    errors: list[str] = []
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog_slugs = {p["slug"] for p in catalog}
    bundle_slugs = set(bundle.keys())
    if not bundle_slugs <= catalog_slugs:
        errors.append(f"bundle slugs not in catalog: {sorted(bundle_slugs - catalog_slugs)}")
    for slug in bundle:
        if slug not in catalog_slugs:
            errors.append(f"catalog missing bundle slug: {slug}")
    return errors


def check_curriculum_practice(curriculum: dict[str, dict], bundle: dict) -> list[str]:
    """课程中带 OJ 链接的题：应有测例或明确 offline fallback。"""
    warnings: list[str] = []
    missing_tests: list[str] = []
    for slug, meta in sorted(curriculum.items()):
        if slug in bundle:
            continue
        missing_tests.append(f"{slug} ({meta['module']}, lc {meta['lc_id']})")
    if missing_tests:
        warnings.append(
            f"curriculum OJ slugs without tests_bundle ({len(missing_tests)}): "
            + "; ".join(missing_tests[:15])
            + (" ..." if len(missing_tests) > 15 else "")
        )
    return warnings


def check_public_bundle_parity(bundle: dict) -> list[str]:
    errors: list[str] = []
    pub = json.loads(FRONTEND_BUNDLE.read_text(encoding="utf-8"))
    for slug, cfg in bundle.items():
        if slug not in pub:
            errors.append(f"public bundle missing: {slug}")
            continue
        p = pub[slug]
        if p.get("judge_mode") != cfg.get("judge_mode"):
            errors.append(f"{slug}: judge_mode mismatch pub/backend")
        if len(p.get("samples") or []) != len(cfg.get("samples") or []):
            errors.append(f"{slug}: sample count mismatch")
        for i, (bs, ps) in enumerate(zip(cfg.get("samples") or [], p.get("samples") or [])):
            if bs.get("stdin") != ps.get("stdin") or bs.get("stdout") != ps.get("stdout"):
                errors.append(f"{slug}: sample[{i}] stdin/stdout mismatch pub/backend")
                break
        api = get_public_problem(slug)
        if api["hidden_count"] != len(cfg.get("hidden") or []):
            errors.append(f"{slug}: hidden_count mismatch api={api['hidden_count']}")
    extra = set(pub.keys()) - set(bundle.keys())
    if extra:
        errors.append(f"public bundle has extra slugs not in backend: {sorted(extra)[:10]}")
    return errors


def check_dist_bundle() -> list[str]:
    errors: list[str] = []
    if not DIST_BUNDLE.is_file():
        return [f"dist bundle absent (ok for dev-only): {DIST_BUNDLE}"]
    pub = json.loads(FRONTEND_BUNDLE.read_text(encoding="utf-8"))
    dist = json.loads(DIST_BUNDLE.read_text(encoding="utf-8"))
    lc = [s for s, v in dist.items() if v.get("judge_mode") == "leetcode"]
    if lc:
        errors.append(f"dist bundle leetcode mode ({len(lc)}): {lc[:8]}")
    for slug in pub:
        if slug not in dist:
            errors.append(f"dist missing slug: {slug}")
        elif dist[slug].get("judge_mode") != pub[slug].get("judge_mode"):
            errors.append(f"dist judge_mode != public: {slug}")
    return errors


def check_submit_cases(bundle: dict) -> list[str]:
    """提交测例（含 hidden）格式可判题。"""
    errors: list[str] = []
    for slug in sorted(bundle):
        cases = get_cases(slug, mode="submit")
        for ci, case in enumerate(cases):
            exp = case.get("stdout", "")
            code = (
                "import sys\n"
                f"exp = {exp!r}\n"
                "sys.stdout.write(exp if exp.endswith('\\n') else exp + '\\n')\n"
            )
            insens = bundle[slug].get("order_insensitive", False) or case.get(
                "order_insensitive", False
            )
            r = run_cases_stdio(
                code,
                cases=[case],
                language="python",
                order_insensitive=insens,
            )
            if r.verdict != "AC":
                msg = r.cases[0].message if r.cases else r.verdict
                errors.append(f"{slug} submit case {ci}: {msg[:100]}")
                break
    return errors


def check_empty_stdout(bundle: dict) -> list[str]:
    """stdout 为空字符串的测例应可比对。"""
    errors: list[str] = []
    for slug, cfg in bundle.items():
        for label in ("samples", "hidden"):
            for i, c in enumerate(cfg.get(label) or []):
                if c.get("stdout") == "" and c.get("expected") not in (None, ""):
                    errors.append(f"{slug} {label}[{i}]: empty stdout but expected set")
    return errors


def main() -> int:
    bundle = _load_bundle()
    curriculum = scan_curriculum_slugs()

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_config(bundle))
    errors.extend(check_runner_echo(bundle))
    errors.extend(check_frontend_bundle())
    errors.extend(check_catalog(bundle))
    errors.extend(check_public_bundle_parity(bundle))
    errors.extend(check_dist_bundle())
    errors.extend(check_submit_cases(bundle))
    errors.extend(check_empty_stdout(bundle))
    warnings.extend(check_curriculum_practice(curriculum, bundle))

    catalog_n = len(json.loads(CATALOG_PATH.read_text(encoding="utf-8")))
    pub_n = len(json.loads(FRONTEND_BUNDLE.read_text(encoding="utf-8")))

    print("=== OJ 全站审计 ===")
    print(f"catalog 题目数:     {catalog_n}")
    print(f"tests_bundle 有测例: {len(bundle)}")
    print(f"public bundle:      {pub_n}")
    print(f"课程 practice 链接: {len(curriculum)}")
    print(f"课程中有测例:       {len([s for s in curriculum if s in bundle])}")
    print(f"课程中无测例:       {len([s for s in curriculum if s not in bundle])}")

    if warnings:
        print(f"\n提示 ({len(warnings)}):")
        for w in warnings:
            print(" *", w)

    if errors:
        print(f"\n失败 ({len(errors)}):")
        for e in errors:
            print(" -", e)
        return 1

    print("\n全部检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
