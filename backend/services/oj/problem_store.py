from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

OJ_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "oj"
CATALOG_PATH = OJ_ROOT / "catalog.json"
TESTS_PATH = OJ_ROOT / "tests_bundle.json"


class ProblemNotFoundError(KeyError):
    pass


class ProblemExistsError(ValueError):
    pass


@lru_cache(maxsize=1)
def _load_catalog() -> list[dict[str, Any]]:
    if not CATALOG_PATH.is_file():
        return []
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_tests_bundle() -> dict[str, Any]:
    if not TESTS_PATH.is_file():
        return {}
    return json.loads(TESTS_PATH.read_text(encoding="utf-8"))


def _reload_caches() -> None:
    """写入文件后清除 lru_cache，使后续读取拿到最新数据。"""
    _load_catalog.cache_clear()
    _load_tests_bundle.cache_clear()


def _save_catalog(catalog: list[dict[str, Any]]) -> None:
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _save_tests_bundle(bundle: dict[str, Any]) -> None:
    TESTS_PATH.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_problems(*, q: str | None = None) -> list[dict[str, Any]]:
    items = _load_catalog()
    if q:
        key = q.strip().lower()
        items = [
            p
            for p in items
            if key in p.get("slug", "").lower() or key in p.get("title", "")
        ]
    return items


def get_problem(slug: str) -> dict[str, Any]:
    catalog = {p["slug"]: p for p in _load_catalog()}
    if slug not in catalog:
        raise ProblemNotFoundError(slug)
    meta = catalog[slug]
    bundle = _load_tests_bundle().get(slug, {})
    return {**meta, **bundle, "slug": slug}


def get_public_problem(slug: str) -> dict[str, Any]:
    """返回题目详情（不含隐藏测例内容）。"""
    full = get_problem(slug)
    hidden = full.get("hidden") or []
    entry = full.get("entry") or {}
    judge_mode = full.get("judge_mode")
    if not judge_mode:
        if entry.get("mode") == "stdio":
            judge_mode = "stdio"
        elif entry.get("class") == "Solution" and entry.get("method"):
            judge_mode = "leetcode"
        else:
            judge_mode = "stdio"
    has_cases = bool(full.get("samples") or hidden)
    if judge_mode == "stdio":
        ready = has_cases
    else:
        ready = bool(full.get("entry") and has_cases)

    return {
        "slug": full["slug"],
        "title": full.get("title") or slug,
        "lc_id": full.get("lc_id", 0),
        "difficulty": full.get("difficulty", "medium"),
        "description": full.get("description") or _default_description(full),
        "judge_mode": judge_mode,
        "entry": full.get("entry"),
        "starter_code": _merge_starter_code(full),
        "samples": full.get("samples") or [],
        "hidden_count": len(hidden),
        "ready": ready,
        "time_limit_ms": full.get("time_limit_ms", 3000),
        "order_insensitive": full.get("order_insensitive", False),
        "tags": full.get("tags") or [],
        "common_errors": full.get("common_errors") or [],
        **_course_context_fields(full, slug),
    }


def _course_context_fields(full: dict[str, Any], slug: str) -> dict[str, str]:
    """合并 catalog 字段与 concept_graph / SkillRouter 推断的课程上下文。"""
    from services.oj.problem_context import resolve_problem_context

    title = str(full.get("title") or slug)
    ctx = resolve_problem_context(slug, title=title, meta=full)
    return {
        "course_id": ctx["course_id"],
        "chapter_id": ctx.get("chapter_id") or "",
        "module_key": ctx.get("module_key") or "",
        "skill_id": ctx.get("skill_id") or "",
    }


def get_cases(slug: str, *, mode: str) -> list[dict[str, Any]]:
    full = get_problem(slug)
    if full.get("judge_mode") == "stdio":
        samples = full.get("samples") or []
        hidden = full.get("hidden") or []
        if mode == "run":
            return samples
        if mode == "submit":
            return samples + hidden
        raise ValueError(mode)
    if not full.get("entry"):
        return []
    samples = full.get("samples") or []
    hidden = full.get("hidden") or []
    if mode == "run":
        return samples
    if mode == "submit":
        return samples + hidden
    raise ValueError(mode)


def _default_description(meta: dict[str, Any]) -> str:
    title = meta.get("title") or meta.get("slug")
    lc_id = meta.get("lc_id", 0)
    entry = meta.get("entry") or {}
    judge_mode = meta.get("judge_mode")
    if not judge_mode:
        judge_mode = "stdio" if entry.get("mode") == "stdio" or not entry.get("method") else "leetcode"
    lines = [f"## {title}", ""]
    if lc_id:
        lines.append(f"力扣 {lc_id} · {title}")
        lines.append("")
    lines.append("请按**洛谷格式**编写完整程序，使用标准输入/输出（`cin`/`cout` 或 `input`/`print`）。")
    lines.append("")
    lines.append("按上方样例从标准输入读入、向标准输出写出答案；`null` 表示空树/空链表/无交点。")
    lines.append("")
    lines.append("若「运行样例」不可用，表示测例仍在完善中，可先参考学习页讲解与力扣原题。")
    return "\n".join(lines)


def _merge_starter_code(full: dict[str, Any]) -> dict[str, str]:
    """合并题库 starter_code；缺失的语言用 _default_starter 补全。"""
    raw = full.get("starter_code")
    if not isinstance(raw, dict):
        raw = {}
    default = _default_starter(full)
    merged = {**default, **{k: str(v) for k, v in raw.items() if v}}
    for key in ("python", "cpp"):
        if not (merged.get(key) or "").strip():
            merged[key] = default.get(key, "")
    return merged


def _default_starter(meta: dict[str, Any]) -> dict[str, str]:
    from scripts.oj_test_data import STDIO_STARTER_CPP, STDIO_STARTER_PY

    _ = meta
    return {"python": STDIO_STARTER_PY, "cpp": STDIO_STARTER_CPP}


# ──────────────────────────── 教师管理：测例读写 ────────────────────────────

def get_problem_cases(slug: str) -> dict[str, Any]:
    """返回题目完整测例（含 samples + hidden），供教师查看/编辑。"""
    full = get_problem(slug)
    return {
        "slug": slug,
        "title": full.get("title") or slug,
        "judge_mode": full.get("judge_mode") or "stdio",
        "entry": full.get("entry") or {},
        "samples": full.get("samples") or [],
        "hidden": full.get("hidden") or [],
    }


def update_problem_cases(
    slug: str,
    *,
    samples: list[dict[str, Any]],
    hidden: list[dict[str, Any]],
) -> dict[str, Any]:
    """更新题目测例（覆盖写入 tests_bundle.json 中该 slug 的 samples/hidden）。"""
    full = get_problem(slug)  # 不存在会抛 ProblemNotFoundError
    bundle = _load_tests_bundle()
    entry = bundle.get(slug) or {}
    entry = {**entry}
    entry["samples"] = samples
    entry["hidden"] = hidden
    bundle[slug] = entry
    _save_tests_bundle(bundle)
    _reload_caches()
    return get_problem_cases(slug)


# ──────────────────────────── 教师管理：题目创建 ────────────────────────────

def create_problem(
    *,
    slug: str,
    title: str,
    module_key: str = "",
    difficulty: str = "medium",
    lc_id: int = 0,
    description: str = "",
    judge_mode: str = "stdio",
    entry: dict[str, Any] | None = None,
    starter_code: dict[str, str] | None = None,
    samples: list[dict[str, Any]] | None = None,
    hidden: list[dict[str, Any]] | None = None,
    tags: list[str] | None = None,
    common_errors: list[str] | None = None,
) -> dict[str, Any]:
    """创建新题目，写入 catalog.json + tests_bundle.json。"""
    slug = slug.strip()
    if not slug:
        raise ValueError("slug 不能为空")

    catalog = _load_catalog()
    existing_slugs = {p["slug"] for p in catalog}
    if slug in existing_slugs:
        raise ProblemExistsError(slug)

    # 写 catalog.json
    catalog_entry: dict[str, Any] = {
        "slug": slug,
        "title": title.strip(),
    }
    if lc_id:
        catalog_entry["lc_id"] = lc_id
    if module_key:
        catalog_entry["module_key"] = module_key
    catalog.append(catalog_entry)
    _save_catalog(catalog)

    # 写 tests_bundle.json
    bundle = _load_tests_bundle()
    if entry is None:
        entry = {"mode": "stdio"} if judge_mode == "stdio" else {}
    tests_entry: dict[str, Any] = {
        "difficulty": difficulty,
        "description": description,
        "judge_mode": judge_mode,
        "entry": entry,
        "samples": samples or [],
        "hidden": hidden or [],
    }
    if starter_code:
        tests_entry["starter_code"] = starter_code
    if tags:
        tests_entry["tags"] = tags
    if common_errors:
        tests_entry["common_errors"] = common_errors
    bundle[slug] = tests_entry
    _save_tests_bundle(bundle)

    _reload_caches()
    return get_public_problem(slug)

