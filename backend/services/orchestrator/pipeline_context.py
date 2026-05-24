"""多 Agent 协作共享上下文（批量生成时跨 Agent 传递摘要）。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class PipelineContext:
    doc_summary: str = ""
    graph_outline: str = ""
    quiz_focus: str = ""
    scenario_hook: str = ""
    trace_hint: str = ""
    collaboration_log: list[dict] = field(default_factory=list)
    agent_logs: list[dict] = field(default_factory=list)

    def log(
        self,
        agent: str,
        action: str,
        detail: str = "",
        *,
        role: str = "",
        resource_type: str = "",
        status: str = "done",
    ) -> None:
        entry = {
            "agent": agent,
            "role": role,
            "action": action,
            "detail": detail[:500],
            "resource_type": resource_type,
            "status": status,
        }
        self.collaboration_log.append(entry)
        self.agent_logs.append(entry)

    def agent_hints_block(self) -> str:
        parts: list[str] = []
        if self.doc_summary:
            parts.append(f"【ConceptAgent 讲解摘要】\n{self.doc_summary[:800]}")
        if self.graph_outline:
            parts.append(f"【GraphAgent 知识拓扑】\n{self.graph_outline[:600]}")
        if self.quiz_focus:
            parts.append(f"【QuizAgent 考查侧重】\n{self.quiz_focus[:400]}")
        if self.scenario_hook:
            parts.append(f"【ScenarioAgent 剧本钩子】\n{self.scenario_hook[:400]}")
        if self.trace_hint:
            parts.append(f"【TraceAgent 动画提示】\n{self.trace_hint[:300]}")
        return "\n\n".join(parts)

    def update_from_resource(self, resource_type: str, content: str) -> None:
        if resource_type == "document":
            self.doc_summary = _extract_summary(content)
            self.log(
                "ConceptAgent",
                "output_summary",
                self.doc_summary[:120],
                role="概念导师",
                resource_type=resource_type,
            )
        elif resource_type == "mindmap":
            self.graph_outline = _extract_graph_outline(content)
            self.log(
                "GraphAgent",
                "output_outline",
                self.graph_outline[:120],
                role="拓扑专家",
                resource_type=resource_type,
            )
        elif resource_type == "exercises":
            self.quiz_focus = _extract_quiz_focus(content)
            self.log(
                "QuizAgent",
                "output_focus",
                self.quiz_focus[:120],
                role="考题官",
                resource_type=resource_type,
            )
        elif resource_type == "code_case":
            self.scenario_hook = _extract_scenario_hook(content)
            self.log(
                "ScenarioAgent",
                "output_hook",
                self.scenario_hook[:120],
                role="互动编剧",
                resource_type=resource_type,
            )
        elif resource_type in ("trace_animation", "video_script"):
            self.trace_hint = _extract_trace_hint(content)
            self.log(
                "TraceAgent",
                "output_trace",
                self.trace_hint[:120],
                role="动画总导演",
                resource_type=resource_type,
            )


def _extract_summary(md: str) -> str:
    lines = [ln.strip() for ln in md.splitlines() if ln.strip() and not ln.startswith("#")]
    text = " ".join(lines[:12])
    return text[:800] if text else md[:500]


def _extract_graph_outline(raw: str) -> str:
    labels = re.findall(r'\[["\']?([^"\']+)["\']?\]', raw)
    if labels:
        return " → ".join(labels[:15])
    return raw[:400]


def _extract_quiz_focus(raw: str) -> str:
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


def _extract_scenario_hook(raw: str) -> str:
    for ln in raw.splitlines():
        if ln.strip().startswith("##") and "背景" in ln:
            idx = raw.splitlines().index(ln)
            body = "\n".join(raw.splitlines()[idx + 1 : idx + 4]).strip()
            return body[:300]
    return raw[:200]


def _extract_trace_hint(raw: str) -> str:
    try:
        data = json.loads(raw)
        hint = str(data.get("narration_hint") or "")
        steps = data.get("steps") or []
        verdict = str(data.get("verdict") or "")
        return f"{hint}（{verdict}，{len(steps)} 步）"[:300]
    except Exception:
        return raw[:200]
