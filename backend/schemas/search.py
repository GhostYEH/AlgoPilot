"""语义检索 schema。"""

from pydantic import BaseModel, Field


class SemanticSearchResult(BaseModel):
    id: str
    kind: str
    title: str
    snippet: str = ""
    module_key: str = ""
    concept_ids: list[str] = Field(default_factory=list)
    node_ids: list[str] = Field(default_factory=list)
    score: float = 0.0
    slug: str = ""
    difficulty: str = ""


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult]
    highlight_node_ids: list[str] = Field(default_factory=list)
