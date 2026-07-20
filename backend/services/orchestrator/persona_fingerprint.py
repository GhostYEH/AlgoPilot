"""画像指纹：persona / 主题变更时仅重生受影响的资源类型。"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from schemas.resources import ResourceType

if TYPE_CHECKING:
    from models.db_models import GeneratedResource, StudentProfile

# 各资源类型敏感的画像维度（六维 + summary）
RESOURCE_PERSONA_KEYS: dict[ResourceType, tuple[str, ...]] = {
    "document": (
        "knowledge_base",
        "cognitive_style",
        "coding_ability",
        "learning_goals",
        "error_preference",
        "grit",
    ),
    "mindmap": ("knowledge_base", "learning_goals", "cognitive_style"),
    "exercises": ("error_preference", "coding_ability", "knowledge_base"),
    "code_case": ("cognitive_style", "grit", "error_preference", "coding_ability"),
    "trace_animation": ("coding_ability", "cognitive_style", "error_preference"),
    "reading": ("knowledge_base", "learning_goals"),
    "ppt": (
        "knowledge_base",
        "cognitive_style",
        "learning_goals",
        "error_preference",
    ),
}

FPS_STORAGE_KEY = "_resource_generation_fps"


def _dimension_scores(row: StudentProfile | None) -> dict[str, int]:
    if row is None or not row.dimensions:
        return {}
    raw = (row.dimensions or {}).get("_dimension_scores") or {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for k, v in raw.items():
        if isinstance(v, (int, float)):
            out[str(k)] = max(1, min(10, int(v)))
    return out


def fingerprint_for_resource(
    row: StudentProfile | None,
    *,
    resource_type: ResourceType,
    topic: str,
    module_key: str,
    focus_hint: str,
) -> str:
    """稳定短指纹：画像相关维度 + 生成上下文。"""
    keys = RESOURCE_PERSONA_KEYS.get(resource_type, RESOURCE_PERSONA_KEYS["document"])
    scores = _dimension_scores(row)
    dim_slice = {k: scores.get(k, 5) for k in keys}
    summary = (row.summary or "")[:240] if row else ""
    payload = {
        "type": resource_type,
        "dims": dim_slice,
        "summary": summary,
        "topic": topic.strip(),
        "module_key": module_key.strip(),
        "focus_hint": focus_hint.strip()[:200],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def cache_key(resource_type: ResourceType, topic: str, module_key: str) -> str:
    return f"{resource_type}@{topic.strip()}|{module_key.strip()}"


def load_stored_fingerprints(row: StudentProfile | None) -> dict[str, str]:
    if row is None:
        return {}
    stored = (row.dimensions or {}).get(FPS_STORAGE_KEY) or {}
    return dict(stored) if isinstance(stored, dict) else {}


def save_fingerprint(
    row: StudentProfile,
    *,
    resource_type: ResourceType,
    topic: str,
    module_key: str,
    fingerprint: str,
) -> None:
    dims = dict(row.dimensions or {})
    fps = dict(dims.get(FPS_STORAGE_KEY) or {})
    fps[cache_key(resource_type, topic, module_key)] = fingerprint
    dims[FPS_STORAGE_KEY] = fps
    row.dimensions = dims


def find_latest_resource(
    rows: list[GeneratedResource],
    *,
    resource_type: ResourceType,
    topic: str,
    module_key: str,
) -> GeneratedResource | None:
    topic_n = topic.strip()
    module_n = module_key.strip()
    for row in rows:
        if row.resource_type != resource_type:
            continue
        meta = row.meta or {}
        if str(meta.get("topic", "")).strip() != topic_n:
            continue
        if str(meta.get("module_key", "")).strip() != module_n:
            continue
        return row
    return None


def should_skip_generation(
    row: StudentProfile | None,
    existing: GeneratedResource | None,
    *,
    resource_type: ResourceType,
    topic: str,
    module_key: str,
    focus_hint: str,
) -> tuple[bool, str]:
    """若已有同主题资源且指纹未变，则跳过 LLM 生成。"""
    if existing is None:
        return False, ""
    new_fp = fingerprint_for_resource(
        row,
        resource_type=resource_type,
        topic=topic,
        module_key=module_key,
        focus_hint=focus_hint,
    )
    stored = load_stored_fingerprints(row)
    old_fp = stored.get(cache_key(resource_type, topic, module_key))
    if old_fp and old_fp == new_fp:
        return True, "画像与主题未变，复用已有资源"
    return False, ""
