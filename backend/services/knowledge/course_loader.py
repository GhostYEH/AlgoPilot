"""《数据结构与算法》课程级知识库加载与切片索引。"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict

import yaml

from services.knowledge.retriever import KnowledgeChunk

_COURSES_ROOT = Path(__file__).resolve().parents[2] / "knowledge" / "courses"
_DEFAULT_COURSE_ID = "data_structures_algorithms"
_COURSE_DIR = _COURSES_ROOT / _DEFAULT_COURSE_ID
_MANIFEST_PATH = _COURSE_DIR / "course_manifest.yaml"

_SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_REQUIRED_SECTIONS = frozenset(
    {
        "学习目标",
        "核心概念",
        "关键算法或数据结构",
        "常见误区",
        "课堂案例",
        "实操练习",
        "可生成资源建议",
        "和 OJ/Trace 的结合点",
    }
)


class CourseChapterMeta(TypedDict, total=False):
    id: str
    title: str
    difficulty: str
    prerequisites: list[str]
    module_keys: list[str]
    learning_outcomes: list[str]
    resource_types: list[str]
    recommended_problems: list[str]
    oj_trace_hooks: list[str]


class CourseManifest(TypedDict, total=False):
    course_id: str
    course_name: str
    course_code: str
    credit_hours: int
    target_majors: list[str]
    target_audience: str
    default_resource_types: list[str]
    module_key_aliases: dict[str, str]
    chapters: list[CourseChapterMeta]
    labs: list[dict[str, str]]
    projects: list[dict[str, str]]


def course_root(course_id: str = _DEFAULT_COURSE_ID) -> Path:
    return _COURSES_ROOT / course_id


def manifest_path(course_id: str = _DEFAULT_COURSE_ID) -> Path:
    return course_root(course_id) / "course_manifest.yaml"


@lru_cache(maxsize=4)
def load_manifest(course_id: str = _DEFAULT_COURSE_ID) -> CourseManifest:
    path = manifest_path(course_id)
    if not path.is_file():
        raise FileNotFoundError(f"课程清单不存在: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("course_manifest.yaml 根节点必须为映射")
    if raw.get("course_id") != course_id:
        raise ValueError(f"course_id 不一致: 期望 {course_id}, 实际 {raw.get('course_id')}")
    return raw  # type: ignore[return-value]


def list_registered_courses() -> list[str]:
    if not _COURSES_ROOT.is_dir():
        return []
    out: list[str] = []
    for p in _COURSES_ROOT.iterdir():
        if p.is_dir() and (p / "course_manifest.yaml").is_file():
            out.append(p.name)
    return sorted(out)


def chapter_by_id(manifest: CourseManifest, chapter_id: str) -> CourseChapterMeta | None:
    for ch in manifest.get("chapters") or []:
        if ch.get("id") == chapter_id:
            return ch
    return None


def chapter_id_for_module(manifest: CourseManifest, module_key: str) -> str | None:
    if not module_key:
        return None
    aliases = manifest.get("module_key_aliases") or {}
    if module_key in aliases:
        return str(aliases[module_key])
    for ch in manifest.get("chapters") or []:
        keys = ch.get("module_keys") or []
        if module_key in keys:
            return str(ch["id"])
    return None


def validate_prerequisite_graph(manifest: CourseManifest) -> list[str]:
    """校验先修图：引用存在、无环。返回错误列表，空表示通过。"""
    errors: list[str] = []
    chapters = manifest.get("chapters") or []
    ids = {str(ch["id"]) for ch in chapters if ch.get("id")}

    for ch in chapters:
        cid = str(ch.get("id", ""))
        for pre in ch.get("prerequisites") or []:
            pre_id = str(pre)
            if pre_id not in ids:
                errors.append(f"章节 {cid} 的先修 {pre_id} 不存在")

    # Kahn 拓扑判环
    indeg: dict[str, int] = {cid: 0 for cid in ids}
    adj: dict[str, list[str]] = {cid: [] for cid in ids}
    for ch in chapters:
        cid = str(ch.get("id", ""))
        for pre in ch.get("prerequisites") or []:
            pre_id = str(pre)
            if pre_id in ids:
                adj[pre_id].append(cid)
                indeg[cid] = indeg.get(cid, 0) + 1

    queue = [n for n, d in indeg.items() if d == 0]
    visited = 0
    while queue:
        n = queue.pop()
        visited += 1
        for nxt in adj.get(n, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    if visited != len(ids):
        errors.append("章节先修关系存在环")

    return errors


def module_dependency_edges_from_course(
    manifest: CourseManifest,
) -> dict[str, list[str]]:
    """由课程章节先修推导 platform module_key 之间的先修边。"""
    ch_map = {str(ch["id"]): ch for ch in manifest.get("chapters") or [] if ch.get("id")}
    edges: dict[str, set[str]] = {}

    def module_keys_for(chapter_id: str) -> list[str]:
        ch = ch_map.get(chapter_id)
        if not ch:
            return []
        return [str(k) for k in ch.get("module_keys") or [] if k]

    for ch in manifest.get("chapters") or []:
        cid = str(ch.get("id", ""))
        targets = module_keys_for(cid)
        for pre_id in ch.get("prerequisites") or []:
            for pre_mk in module_keys_for(str(pre_id)):
                for tgt in targets:
                    if pre_mk != tgt:
                        edges.setdefault(tgt, set()).add(pre_mk)

    return {k: sorted(v) for k, v in edges.items()}


def _chapter_id_from_chapter_filename(stem: str) -> str:
    # 01-introduction-complexity -> ch01-introduction-complexity
    if stem.startswith("ch"):
        return stem
    m = re.match(r"^(\d+)-(.+)$", stem)
    if m:
        return f"ch{m.group(1)}-{m.group(2)}"
    return stem


def _parse_markdown_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    title_m = _H1_RE.search(text)
    doc_title = title_m.group(1).strip() if title_m else "未命名"
    parts = _SECTION_HEADING_RE.split(text)
    # split: [preamble, h2, body, h2, body, ...]
    sections: list[tuple[str, str]] = []
    if len(parts) < 3:
        body = text.strip()
        if body:
            sections.append(("全文", body))
        return doc_title, sections

    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if heading and body:
            sections.append((heading, body))
    return doc_title, sections


def _slug(s: str) -> str:
    s = re.sub(r"\s+", "-", s.strip().lower())
    return re.sub(r"[^a-z0-9\u4e00-\u9fff\-]", "", s)[:48] or "section"


def _build_chunk(
    *,
    course_id: str,
    doc_kind: str,
    doc_id: str,
    chapter_id: str,
    doc_title: str,
    section: str,
    body: str,
    module_keys: list[str],
    keywords_extra: list[str],
    source_path: str,
) -> KnowledgeChunk:
    chunk_id = f"course:{course_id}:{doc_id}:{_slug(section)}"
    kw = list(
        dict.fromkeys(
            keywords_extra
            + [doc_title, section, chapter_id, course_id, doc_kind]
            + module_keys
        )
    )
    primary_module = module_keys[0] if module_keys else ""
    return KnowledgeChunk(
        id=chunk_id,
        chunk_id=chunk_id,
        module_key=primary_module,
        module_id=primary_module,
        title=f"{doc_title} · {section}",
        chapter_title=doc_title,
        section_title=section,
        keywords=kw,
        content=body,
        excerpt=re.sub(r"\s+", " ", body).strip()[:240],
        chunk_type=_slug(section),
        course_id=course_id,
        chapter_id=chapter_id,
        doc_kind=doc_kind,
        doc_id=doc_id,
        section=section,
        source_path=source_path,
        module_keys=module_keys,
    )


@lru_cache(maxsize=2)
def index_course_chunks(course_id: str = _DEFAULT_COURSE_ID) -> list[KnowledgeChunk]:
    manifest = load_manifest(course_id)
    root = course_root(course_id)
    chunks: list[KnowledgeChunk] = []

    ch_by_file: dict[str, str] = {}
    for ch in manifest.get("chapters") or []:
        cid = str(ch.get("id", ""))
        # ch01-introduction-complexity -> 01-introduction-complexity.md
        suffix = cid[2:] if cid.startswith("ch") else cid
        ch_by_file[suffix] = cid

    def resolve_chapter_id(file_stem: str, default: str = "") -> str:
        if file_stem in ch_by_file:
            return ch_by_file[file_stem]
        return _chapter_id_from_chapter_filename(file_stem) or default

    def module_keys_for_chapter(chapter_id: str) -> list[str]:
        meta = chapter_by_id(manifest, chapter_id)
        if not meta:
            return []
        return [str(k) for k in meta.get("module_keys") or [] if k]

    # syllabus
    syllabus_path = root / "syllabus.md"
    if syllabus_path.is_file():
        text = syllabus_path.read_text(encoding="utf-8")
        doc_title, sections = _parse_markdown_sections(text)
        for section, body in sections:
            chunks.append(
                _build_chunk(
                    course_id=course_id,
                    doc_kind="syllabus",
                    doc_id="syllabus",
                    chapter_id="",
                    doc_title=doc_title,
                    section=section,
                    body=body,
                    module_keys=[],
                    keywords_extra=[manifest.get("course_name", ""), "课程大纲"],
                    source_path=str(syllabus_path.relative_to(root.parent.parent)),
                )
            )

    chapters_dir = root / "chapters"
    if chapters_dir.is_dir():
        for md in sorted(chapters_dir.glob("*.md")):
            if md.name.startswith("_"):
                continue
            stem = md.stem
            chapter_id = resolve_chapter_id(stem)
            text = md.read_text(encoding="utf-8")
            doc_title, sections = _parse_markdown_sections(text)
            mks = module_keys_for_chapter(chapter_id)
            meta = chapter_by_id(manifest, chapter_id)
            kw_extra = [str(meta.get("title", ""))] if meta else []
            for section, body in sections:
                chunks.append(
                    _build_chunk(
                        course_id=course_id,
                        doc_kind="chapter",
                        doc_id=chapter_id,
                        chapter_id=chapter_id,
                        doc_title=doc_title,
                        section=section,
                        body=body,
                        module_keys=mks,
                        keywords_extra=kw_extra,
                        source_path=str(md.relative_to(root.parent.parent)),
                    )
                )

    for lab in manifest.get("labs") or []:
        lab_id = str(lab.get("id", ""))
        lab_path = root / "labs" / f"{lab_id}.md"
        if not lab_path.is_file():
            continue
        chapter_id = str(lab.get("chapter_id", ""))
        text = lab_path.read_text(encoding="utf-8")
        doc_title, sections = _parse_markdown_sections(text)
        mks = module_keys_for_chapter(chapter_id)
        for section, body in sections:
            chunks.append(
                _build_chunk(
                    course_id=course_id,
                    doc_kind="lab",
                    doc_id=lab_id,
                    chapter_id=chapter_id,
                    doc_title=doc_title,
                    section=section,
                    body=body,
                    module_keys=mks,
                    keywords_extra=["实验", lab_id],
                    source_path=str(lab_path.relative_to(root.parent.parent)),
                )
            )

    for proj in manifest.get("projects") or []:
        proj_id = str(proj.get("id", ""))
        proj_path = root / "projects" / f"{proj_id}.md"
        if not proj_path.is_file():
            continue
        chapter_id = str(proj.get("chapter_id", ""))
        text = proj_path.read_text(encoding="utf-8")
        doc_title, sections = _parse_markdown_sections(text)
        mks = module_keys_for_chapter(chapter_id)
        for section, body in sections:
            chunks.append(
                _build_chunk(
                    course_id=course_id,
                    doc_kind="project",
                    doc_id=proj_id,
                    chapter_id=chapter_id,
                    doc_title=doc_title,
                    section=section,
                    body=body,
                    module_keys=mks,
                    keywords_extra=["项目", proj_id],
                    source_path=str(proj_path.relative_to(root.parent.parent)),
                )
            )

    return chunks


def list_chapters(course_id: str = _DEFAULT_COURSE_ID) -> list[dict[str, Any]]:
    """返回章节列表（id、title、module_keys、recommended_problems），供教师选题挂载用。"""
    manifest = load_manifest(course_id)
    out: list[dict[str, Any]] = []
    for ch in manifest.get("chapters") or []:
        out.append(
            {
                "id": ch.get("id", ""),
                "title": ch.get("title", ""),
                "difficulty": ch.get("difficulty", ""),
                "module_keys": list(ch.get("module_keys") or []),
                "recommended_problems": list(ch.get("recommended_problems") or []),
            }
        )
    return out


def add_problem_to_chapter(
    slug: str, chapter_id: str, course_id: str = _DEFAULT_COURSE_ID
) -> list[str]:
    """把题目 slug 追加到指定章节的 recommended_problems（去重，写回 yaml）。"""
    manifest = load_manifest(course_id)
    chapters = manifest.get("chapters") or []
    target = None
    for ch in chapters:
        if ch.get("id") == chapter_id:
            target = ch
            break
    if target is None:
        raise ValueError(f"章节不存在: {chapter_id}")

    problems: list[str] = list(target.get("recommended_problems") or [])
    if slug not in problems:
        problems.append(slug)
        target["recommended_problems"] = problems

        # 写回 yaml 文件
        path = manifest_path(course_id)
        path.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")
        clear_course_caches()
    return problems


def clear_course_caches() -> None:
    load_manifest.cache_clear()
    index_course_chunks.cache_clear()


def get_course_summary(course_id: str = _DEFAULT_COURSE_ID) -> dict[str, Any]:
    manifest = load_manifest(course_id)
    return {
        "course_id": manifest.get("course_id"),
        "course_name": manifest.get("course_name"),
        "chapter_count": len(manifest.get("chapters") or []),
        "lab_count": len(manifest.get("labs") or []),
        "project_count": len(manifest.get("projects") or []),
        "chunk_count": len(index_course_chunks(course_id)),
        "prerequisite_errors": validate_prerequisite_graph(manifest),
    }
