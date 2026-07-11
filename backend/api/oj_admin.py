"""教师 OJ 题目管理 API：查看/修改测试用例、新增题目、挂载到章节。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.deps import require_teacher
from models.db_models import User
from services.knowledge.course_loader import add_problem_to_chapter, list_chapters
from services.oj.problem_store import (
    ProblemExistsError,
    ProblemNotFoundError,
    create_problem,
    get_problem_cases,
    update_problem_cases,
)

router = APIRouter(prefix="/oj/admin", tags=["oj-admin"])


# ──────────────────────────── 测试用例 ────────────────────────────

class TestCaseItem(BaseModel):
    args: list[Any] | None = None
    expected: Any = None
    stdin: str | None = None
    stdout: str | None = None
    note: str | None = None


class ProblemCasesResponse(BaseModel):
    slug: str
    title: str
    judge_mode: str
    entry: dict[str, Any] = Field(default_factory=dict)
    samples: list[dict[str, Any]] = Field(default_factory=list)
    hidden: list[dict[str, Any]] = Field(default_factory=list)


class UpdateCasesRequest(BaseModel):
    samples: list[dict[str, Any]] = Field(default_factory=list)
    hidden: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/problems/{slug}/cases", response_model=ProblemCasesResponse)
def api_get_cases(slug: str, _: User = Depends(require_teacher)) -> ProblemCasesResponse:
    try:
        data = get_problem_cases(slug)
    except ProblemNotFoundError:
        raise HTTPException(status_code=404, detail=f"题目不存在: {slug}")
    return ProblemCasesResponse(**data)


@router.put("/problems/{slug}/cases", response_model=ProblemCasesResponse)
def api_update_cases(
    slug: str,
    body: UpdateCasesRequest,
    _: User = Depends(require_teacher),
) -> ProblemCasesResponse:
    try:
        data = update_problem_cases(slug, samples=body.samples, hidden=body.hidden)
    except ProblemNotFoundError:
        raise HTTPException(status_code=404, detail=f"题目不存在: {slug}")
    return ProblemCasesResponse(**data)


# ──────────────────────────── 新增题目 ────────────────────────────

class CreateProblemRequest(BaseModel):
    slug: str
    title: str
    module_key: str = ""
    difficulty: str = "medium"
    lc_id: int = 0
    description: str = ""
    judge_mode: str = "stdio"
    entry: dict[str, Any] | None = None
    starter_code: dict[str, str] | None = None
    samples: list[dict[str, Any]] = Field(default_factory=list)
    hidden: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    common_errors: list[str] = Field(default_factory=list)


@router.post("/problems")
def api_create_problem(
    body: CreateProblemRequest,
    _: User = Depends(require_teacher),
) -> dict[str, Any]:
    try:
        return create_problem(
            slug=body.slug,
            title=body.title,
            module_key=body.module_key,
            difficulty=body.difficulty,
            lc_id=body.lc_id,
            description=body.description,
            judge_mode=body.judge_mode,
            entry=body.entry,
            starter_code=body.starter_code,
            samples=body.samples,
            hidden=body.hidden,
            tags=body.tags,
            common_errors=body.common_errors,
        )
    except ProblemExistsError:
        raise HTTPException(status_code=409, detail=f"题目 slug 已存在: {body.slug}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────── 章节列表与挂载 ────────────────────────────

@router.get("/chapters")
def api_list_chapters(_: User = Depends(require_teacher)) -> list[dict[str, Any]]:
    return list_chapters()


class AttachToChapterRequest(BaseModel):
    slug: str
    chapter_id: str


@router.post("/chapters/attach")
def api_attach_to_chapter(
    body: AttachToChapterRequest,
    _: User = Depends(require_teacher),
) -> dict[str, Any]:
    try:
        problems = add_problem_to_chapter(body.slug, body.chapter_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "chapter_id": body.chapter_id,
        "slug": body.slug,
        "recommended_problems": problems,
    }
