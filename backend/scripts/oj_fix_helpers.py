"""Helper utilities for OJ test case fix scripts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parent.parent
BUNDLE_PATH = BACKEND / "data" / "oj" / "tests_bundle.json"


def load_bundle() -> dict[str, Any]:
    return json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))


def save_bundle(bundle: dict[str, Any]) -> None:
    BUNDLE_PATH.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def update_slug(slug: str, *, samples: list | None = None, hidden: list | None = None) -> None:
    """Update a single slug's samples and/or hidden in tests_bundle.json."""
    bundle = load_bundle()
    if slug not in bundle:
        raise KeyError(f"slug not found: {slug}")
    if samples is not None:
        bundle[slug]["samples"] = samples
    if hidden is not None:
        bundle[slug]["hidden"] = hidden
    save_bundle(bundle)


def merge_fixes(fixes: dict[str, dict]) -> None:
    """Merge a dict of {slug: {"samples": [...], "hidden": [...]}} into the bundle."""
    bundle = load_bundle()
    for slug, fix in fixes.items():
        if slug not in bundle:
            print(f"  WARN: slug not in bundle: {slug}")
            continue
        if "samples" in fix:
            bundle[slug]["samples"] = fix["samples"]
        if "hidden" in fix:
            bundle[slug]["hidden"] = fix["hidden"]
        if "description" in fix:
            bundle[slug]["description"] = fix["description"]
        if "order_insensitive" in fix:
            bundle[slug]["order_insensitive"] = fix["order_insensitive"]
    save_bundle(bundle)


if __name__ == "__main__":
    print(f"Bundle path: {BUNDLE_PATH}")
    b = load_bundle()
    print(f"Total slugs: {len(b)}")
