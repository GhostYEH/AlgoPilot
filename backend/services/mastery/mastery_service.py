"""掌握度计算、缓存与查询服务。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.db_models import StudentProfile
from schemas.learning_path import ModuleProgressInput
from services.knowledge.course_loader import chapter_id_for_module, load_manifest
from services.mastery.mastery_agent import mastery_agent
from services.mastery.models import (
    MasteryCourseOverview,
    MasteryEvidenceItem,
    MasteryReport,
    MasterySignals,
    mastery_level_from_score,
)
from services.mastery.scoring import (
    build_evidence_from_components,
    compute_bkt_lite,
    compute_component_scores,
    compute_mastery_score,
    resolve_weak_strong_skills,
)
from services.memory.memory_service import MemoryService


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _skill_name_map() -> dict[str, str]:
    try:
        from services.skills.registry import SkillRegistry

        reg = SkillRegistry()
        return {c.id: c.name for c in reg.list_all()}
    except Exception:
        return {}


def _chapter_meta(course_id: str, chapter_id: str) -> tuple[str, list[str]]:
    if not chapter_id:
        return "课程总览", []
    try:
        manifest = load_manifest(course_id)
        for ch in manifest.get("chapters") or []:
            if str(ch.get("id")) == chapter_id:
                return str(ch.get("title") or chapter_id), list(ch.get("module_keys") or [])
    except Exception:
        pass
    return chapter_id, []


def _self_report_from_profile(db: Session, user_id: int) -> float | None:
    row = db.get(StudentProfile, user_id)
    if not row or not row.dimensions:
        return None
    raw = row.dimensions.get("_dimension_scores") or {}
    if not isinstance(raw, dict) or not raw:
        return None
    vals = [float(v) for v in raw.values() if isinstance(v, (int, float))]
    if not vals:
        return None
    return sum(vals) / len(vals) * 10.0


def extract_signals(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
    module_keys: list[str] | None = None,
    modules: list[ModuleProgressInput] | None = None,
) -> MasterySignals:
    memories = MemoryService(db).list_recent(
        user_id,
        course_id=course_id,
        chapter_id=chapter_id if chapter_id else "",
        limit=80,
    )
    if chapter_id and not memories:
        memories = MemoryService(db).list_recent(user_id, course_id=course_id, limit=80)
        memories = [m for m in memories if not m.chapter_id or m.chapter_id == chapter_id]

    mk_set = set(module_keys or [])
    if mk_set:
        filtered = []
        for m in memories:
            if m.chapter_id == chapter_id:
                filtered.append(m)
                continue
            if m.skill_id:
                filtered.append(m)
                continue
            ev = m.evidence_json or {}
            if ev.get("module_key") in mk_set:
                filtered.append(m)
        if filtered:
            memories = filtered

    signals = MasterySignals(memory_event_count=len(memories))
    recent_patterns: list[str] = []
    older_patterns: list[str] = []
    split = max(1, len(memories) // 2)

    for i, mem in enumerate(memories):
        et = mem.event_type or ""
        pattern = (mem.observed_error_pattern or mem.failed_strategy or "").strip()
        if et == "oj_submit_fail":
            signals.oj_failures += 1
        elif et in ("oj_diagnosis", "trace_diagnosis"):
            signals.oj_diagnoses += 1
            if mem.successful_hint:
                signals.trace_with_hints += 1
        elif et == "resource_complete":
            signals.resource_completions += 1
        elif et == "section_done":
            signals.section_completions += 1
        elif et == "quiz_complete":
            signals.quiz_total += 1
            ev = mem.evidence_json or {}
            if ev.get("correct") is True or mem.mastery_delta > 0:
                signals.quiz_correct += 1
        elif et == "evaluation_struggle":
            signals.struggle_events += 1
        elif et == "gamified_practice_complete":
            signals.gamified_practice_count += 1
            signals.resource_completions += 1

        if mem.mastery_delta > 0:
            signals.positive_deltas += 1
        elif mem.mastery_delta < 0:
            signals.negative_deltas += 1

        if pattern:
            if i < split:
                recent_patterns.append(pattern)
            else:
                older_patterns.append(pattern)

        sid = mem.skill_id or ""
        if sid:
            if mem.mastery_delta >= 0 and et in ("resource_complete", "quiz_complete", "section_done", "gamified_practice_complete"):
                signals.skill_success_counts[sid] = signals.skill_success_counts.get(sid, 0) + 1
            elif mem.mastery_delta < 0 or et in ("oj_submit_fail", "evaluation_struggle"):
                signals.skill_fail_counts[sid] = signals.skill_fail_counts.get(sid, 0) + 1

    signals.recent_fail_patterns = recent_patterns
    signals.older_fail_patterns = older_patterns
    signals.self_report_score = _self_report_from_profile(db, user_id)

    if modules and mk_set:
        for m in modules:
            if m.key in mk_set:
                signals.module_percents[m.key] = m.percent
    elif modules and not chapter_id:
        for m in modules:
            if m.percent > 0 or m.total_count > 0:
                signals.module_percents[m.key] = m.percent

    return signals


def build_report(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
    modules: list[ModuleProgressInput] | None = None,
    persist: bool = True,
) -> MasteryReport:
    title, module_keys = _chapter_meta(course_id, chapter_id)
    signals = extract_signals(
        db,
        user_id,
        course_id=course_id,
        chapter_id=chapter_id,
        module_keys=module_keys or None,
        modules=modules,
    )

    if signals.memory_event_count == 0 and not signals.module_percents:
        report = MasteryReport.default_for_user(
            user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            chapter_title=title,
        )
        if persist:
            _save_report_cache(db, user_id, report)
        return report

    components = compute_component_scores(signals)
    score = compute_mastery_score(components)
    level = mastery_level_from_score(score)
    probability, trend, confidence, prob_explanation = compute_bkt_lite(score, signals)
    names = _skill_name_map()
    weak, strong = resolve_weak_strong_skills(signals, skill_name_map=names)

    memory_evidence = []
    for mem in MemoryService(db).list_recent(
        user_id, course_id=course_id, chapter_id=chapter_id, limit=5
    ):
        summary = mem.trace_summary or mem.observed_error_pattern or mem.event_type
        memory_evidence.append(
            MasteryEvidenceItem(
                source=f"memory:{mem.event_type}",
                detail=summary[:200],
                at=mem.created_at.isoformat() if mem.created_at else None,
            )
        )

    evidence = build_evidence_from_components(components, extra=memory_evidence)

    report = MasteryReport(
        user_id=user_id,
        course_id=course_id,
        chapter_id=chapter_id,
        chapter_title=title,
        mastery_score=score,
        mastery_level=level,
        weak_skills=weak,
        strong_skills=strong,
        evidence=evidence,
        component_scores=components,
        mastery_probability=probability,
        mastery_trend=trend,
        confidence_level=confidence,
        probability_explanation=prob_explanation,
        updated_at=_now_iso(),
    )
    report = mastery_agent.enrich_report(report, chapter_module_keys=module_keys)
    if persist:
        _save_report_cache(db, user_id, report)
    return report


def build_course_overview(
    db: Session,
    user_id: int,
    *,
    course_id: str = "data_structures_algorithms",
    chapter_id: str = "",
    modules: list[ModuleProgressInput] | None = None,
) -> MasteryCourseOverview:
    if chapter_id:
        report = build_report(
            db, user_id, course_id=course_id, chapter_id=chapter_id, modules=modules
        )
        return MasteryCourseOverview(
            course_id=course_id,
            overall_score=report.mastery_score,
            overall_level=report.mastery_level,
            chapters=[report],
            report=report,
            updated_at=report.updated_at,
        )

    chapters: list[MasteryReport] = []
    try:
        manifest = load_manifest(course_id)
        ch_list = manifest.get("chapters") or []
    except Exception:
        ch_list = []

    for ch in ch_list:
        cid = str(ch.get("id", ""))
        if not cid:
            continue
        chapters.append(
            build_report(
                db,
                user_id,
                course_id=course_id,
                chapter_id=cid,
                modules=modules,
                persist=False,
            )
        )

    if not chapters:
        report = build_report(db, user_id, course_id=course_id, modules=modules)
        return MasteryCourseOverview(
            course_id=course_id,
            overall_score=report.mastery_score,
            overall_level=report.mastery_level,
            chapters=[report],
            report=report,
            updated_at=report.updated_at,
        )

    overall = round(sum(c.mastery_score for c in chapters) / len(chapters))
    course_report = build_report(db, user_id, course_id=course_id, modules=modules, persist=True)
    return MasteryCourseOverview(
        course_id=course_id,
        overall_score=overall,
        overall_level=mastery_level_from_score(overall),
        chapters=chapters,
        report=course_report,
        updated_at=_now_iso(),
    )


def get_cached_mastery_by_chapter(db: Session, user_id: int) -> dict[str, int]:
    row = db.get(StudentProfile, user_id)
    if not row or not row.dimensions:
        return {}
    cache = row.dimensions.get("_mastery_cache") or {}
    if not isinstance(cache, dict):
        return {}
    out: dict[str, int] = {}
    for key, val in cache.items():
        if isinstance(val, dict) and "mastery_score" in val:
            out[str(key)] = int(val["mastery_score"])
    return out


def mastery_for_module(db: Session, user_id: int, module_key: str) -> int | None:
    try:
        manifest = load_manifest()
        cid = chapter_id_for_module(manifest, module_key)
    except Exception:
        cid = None
    if not cid:
        return None
    cached = get_cached_mastery_by_chapter(db, user_id)
    return cached.get(cid)


def _save_report_cache(db: Session, user_id: int, report: MasteryReport) -> None:
    row = db.get(StudentProfile, user_id)
    if row is None:
        row = StudentProfile(user_id=user_id, dimensions={}, summary="")
        db.add(row)
    payload = dict(row.dimensions or {})
    cache = dict(payload.get("_mastery_cache") or {})
    key = report.chapter_id or "_course"
    cache[key] = report.model_dump()
    payload["_mastery_cache"] = cache
    payload["_mastery_updated_at"] = report.updated_at
    row.dimensions = payload
    db.commit()


class MasteryService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_report(
        self,
        user_id: int,
        *,
        course_id: str = "data_structures_algorithms",
        chapter_id: str = "",
        modules: list[ModuleProgressInput] | None = None,
    ) -> MasteryCourseOverview:
        return build_course_overview(
            self._db,
            user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            modules=modules,
        )

    def recalculate(
        self,
        user_id: int,
        *,
        course_id: str = "data_structures_algorithms",
        chapter_id: str = "",
        modules: list[ModuleProgressInput] | None = None,
    ) -> MasteryCourseOverview:
        return build_course_overview(
            self._db,
            user_id,
            course_id=course_id,
            chapter_id=chapter_id,
            modules=modules,
        )
