"""多 Agent 协作共享上下文（批量生成时跨 Agent 传递摘要）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.knowledge.retriever import KnowledgeChunk


@dataclass
class PipelineContext:
    doc_summary: str = ""
    mindmap_outline: str = ""
    quiz_focus: str = ""
    collaboration_log: list[dict] = field(default_factory=list)

    def log(self, agent: str, action: str, detail: str = "") -> None:
        self.collaboration_log.append(
            {"agent": agent, "action": action, "detail": detail[:500]}
        )

    def agent_hints_block(self) -> str:
        parts: list[str] = []
        if self.doc_summary:
            parts.append(f"【DocAgent 讲解摘要】\n{self.doc_summary[:800]}")
        if self.mindmap_outline:
            parts.append(f"【MindMapAgent 结构提纲】\n{self.mindmap_outline[:600]}")
        if self.quiz_focus:
            parts.append(f"【QuizAgent 考查侧重】\n{self.quiz_focus[:400]}")
        return "\n\n".join(parts)

    def update_from_resource(self, resource_type: str, content: str) -> None:
        if resource_type == "document":
            self.doc_summary = _extract_summary(content)
            self.log("DocAgent", "output_summary", self.doc_summary[:120])
        elif resource_type == "mindmap":
            self.mindmap_outline = _extract_mindmap_labels(content)
            self.log("MindMapAgent", "output_outline", self.mindmap_outline[:120])
        elif resource_type == "exercises":
            self.quiz_focus = _extract_quiz_focus(content)
            self.log("QuizAgent", "output_focus", self.quiz_focus[:120])


def _extract_summary(md: str) -> str:
    lines = [ln.strip() for ln in md.splitlines() if ln.strip() and not ln.startswith("#")]
    text = " ".join(lines[:12])
    return text[:800] if text else md[:500]


def _extract_mindmap_labels(raw: str) -> str:
    import json

    try:
        data = json.loads(raw)
        labels = [str(n.get("label", "")) for n in data.get("nodes", []) if n.get("label")]
        root = str(data.get("root", ""))
        if root:
            labels.insert(0, root)
        return " → ".join(labels[:15])
    except Exception:
        return raw[:400]


def _extract_quiz_focus(raw: str) -> str:
    import json

    try:
        data = json.loads(raw)
        focuses = [
            str(q.get("focus", ""))
            for q in data.get("questions", [])
            if q.get("focus")
        ]
        return "；".join(focuses[:5])
    except Exception:
        return raw[:300]
