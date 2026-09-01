"""Reference selection and semantic first-divergence detection.

The trace recorder currently exposes line, variable snapshot, and changed
variable metadata. This module works with that real shape: it normalizes the
snapshots, aligns the semantic sequences, then reports a meaningful mismatch.
"""

from __future__ import annotations

import ast
import io
import keyword
import logging
import re
import tokenize
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from models.db_models import OjSubmission

_logger = logging.getLogger(__name__)
_MAX_TRACE_STEPS_TO_COMPARE = 200
_MAX_VAR_REPR_LEN = 200


@dataclass(frozen=True)
class AlignmentConfig:
    """Centralized limits for Semantic Trace Alignment v2."""

    gap_penalty: float = -0.55
    meaningful_similarity: float = 0.72
    strong_divergence_similarity: float = 0.40
    state_weight: float = 0.70
    changed_weight: float = 0.20
    event_type_weight: float = 0.10
    source_role_weight: float = 0.20
    control_context_weight: float = 0.15
    max_reference_candidates: int = 25
    max_reference_rows_to_scan: int = 100
    reference_cluster_similarity: float = 0.76


ALIGNMENT_CONFIG = AlignmentConfig()
_TEMP_NAME_RE = re.compile(
    r"^(?:_|tmp\d*|temp\d*|debug\w*|log\w*|unused\w*|dummy\w*)$", re.IGNORECASE
)
_POINTER_NAME_RE = re.compile(
    r"^(?:i|j|k|idx|index|l|r|lo|hi|left|right|mid|head|tail|prev|curr|next)$",
    re.IGNORECASE,
)
_CONTROL_EVENTS = {"branch", "loop", "return", "exception", "call"}
_STRICT_CONTROL_ROLES = {"branch", "loop", "return", "exception", "loop_control"}
_CONTAINER_TYPES = {
    "list", "dict", "matrix", "queue", "stack", "linked_list", "tree",
    "sequence", "associative",
}
_DATA_EVENT_TYPES = {"assignment", "state_change", "container_mutation"}
_MUTATING_METHODS = {
    "add", "append", "clear", "discard", "extend", "heappop", "heappush",
    "insert", "pop", "popleft", "push", "push_back", "remove", "reverse",
    "setdefault", "sort", "update",
}


@dataclass(frozen=True)
class SourceLineContext:
    """Static role and control-flow metadata for one executable source line."""

    role: str = ""
    control_path: tuple[str, ...] = ()
    branch_membership: tuple[tuple[int, bool], ...] = ()
    loop_membership: tuple[int, ...] = ()
    condition: str = ""


@dataclass
class FirstDivergenceResult:
    """Backward-compatible first-divergence result."""

    detected: bool = False
    step_index: int = 0
    line: int | None = None
    reference_line: int | None = None
    student_state: str = ""
    reference_state: str = ""
    divergent_variable: str = ""
    explanation: str = ""
    confidence: str = "low"
    reference_source: str = ""
    reason: str = ""
    alignment_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "step_index": self.step_index,
            "line": self.line,
            "reference_line": self.reference_line,
            "student_state": self.student_state,
            "reference_state": self.reference_state,
            "divergent_variable": self.divergent_variable,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "reference_source": self.reference_source,
            "reason": self.reason,
            "alignment_score": self.alignment_score,
        }


@dataclass(frozen=True)
class ReferenceCandidate:
    """One unique, fully verified AC candidate and its stable ranking metadata."""

    code: str
    submission_id: int
    total: int
    runtime_ms_avg: int
    recency_rank: int


@dataclass(frozen=True)
class ReferenceCluster:
    """A structural strategy cluster represented by its canonical medoid."""

    members: tuple[ReferenceCandidate, ...]
    canonical: ReferenceCandidate


@dataclass(frozen=True)
class ReferenceSelection:
    """Selected canonical reference plus bounded-pool diagnostics."""

    code: str
    cluster_size: int
    cluster_count: int
    candidate_count: int
    compatibility: float | None = None


def _python_structure(code: str) -> tuple[dict[str, int], list[str]]:
    features: dict[str, int] = {}
    tokens: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = None
    if tree is not None:
        function_names = {
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While, ast.If, ast.Call, ast.Return, ast.Subscript)):
                kind = type(node).__name__
                features[kind] = features.get(kind, 0) + 1
            if isinstance(node, ast.Call):
                called = ""
                if isinstance(node.func, ast.Name):
                    called = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    called = node.func.attr
                if called in function_names:
                    features["Recursion"] = features.get("Recursion", 0) + 1
                if called in {"sort", "sorted", "bisect", "heappush", "heappop", "deque"}:
                    key = f"api:{called}"
                    features[key] = features.get(key, 0) + 1
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type in {
                tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE,
                tokenize.NL, tokenize.ENDMARKER, tokenize.COMMENT,
            }:
                continue
            if token.type == tokenize.NAME and not keyword.iskeyword(token.string):
                tokens.append("ID")
            elif token.type in {tokenize.NUMBER, tokenize.STRING}:
                tokens.append("LITERAL")
            else:
                tokens.append(token.string)
    except (tokenize.TokenError, IndentationError):
        tokens = []
    return features, tokens


def _generic_structure(code: str) -> tuple[dict[str, int], list[str]]:
    lowered = code.lower()
    patterns = {
        "For": r"\bfor\b", "While": r"\bwhile\b", "If": r"\bif\b",
        "Return": r"\breturn\b", "Recursion": r"\b(?:dfs|bfs)\s*\(",
        "api:sort": r"\bsort(?:ed)?\s*\(",
        "api:heap": r"\b(?:priority_queue|heap)\b",
        "api:hash": r"\b(?:unordered_map|unordered_set|dict|set)\b",
    }
    features = {
        name: count for name, pattern in patterns.items()
        if (count := len(re.findall(pattern, lowered)))
    }
    raw = re.findall(
        r"[A-Za-z_]\w*|\d+(?:\.\d+)?|==|!=|<=|>=|[-+*/%<>{}()[\],.;:]", code
    )
    keywords = {"for", "while", "if", "else", "return", "break", "continue", "class", "def"}
    tokens = [
        item.lower() if item.lower() in keywords or not re.match(r"[A-Za-z_]", item) else "ID"
        for item in raw
    ]
    return features, tokens


def _code_structure(code: str, language: str) -> tuple[dict[str, int], list[str]]:
    if (language or "").lower() in {"python", "py", "python3"}:
        return _python_structure(code)
    return _generic_structure(code)


def _feature_similarity(left: dict[str, int], right: dict[str, int]) -> float:
    keys = set(left) | set(right)
    if not keys:
        return 1.0
    distance = sum(abs(left.get(key, 0) - right.get(key, 0)) for key in keys)
    scale = sum(max(left.get(key, 0), right.get(key, 0)) for key in keys)
    return max(0.0, 1.0 - distance / max(1, scale))


def _structure_compatibility(
    left: tuple[dict[str, int], list[str]],
    right: tuple[dict[str, int], list[str]],
) -> float:
    feature_score = _feature_similarity(left[0], right[0])
    token_score = SequenceMatcher(None, left[1], right[1], autojunk=False).ratio()
    return 0.65 * feature_score + 0.35 * token_score


def _reference_compatibility(student_code: str, reference_code: str, language: str) -> float:
    student_features, student_tokens = _code_structure(student_code, language)
    reference_features, reference_tokens = _code_structure(reference_code, language)
    return _structure_compatibility(
        (student_features, student_tokens),
        (reference_features, reference_tokens),
    )


def _normalized_code_identity(code: str, language: str) -> tuple[tuple[int, str], ...]:
    """Ignore formatting/comments while preserving identifiers and literal values."""
    if (language or "").lower() in {"python", "py", "python3"}:
        try:
            return tuple(
                (token.type, token.string)
                for token in tokenize.generate_tokens(io.StringIO(code).readline)
                if token.type not in {
                    tokenize.ENCODING,
                    tokenize.INDENT,
                    tokenize.DEDENT,
                    tokenize.NEWLINE,
                    tokenize.NL,
                    tokenize.ENDMARKER,
                    tokenize.COMMENT,
                }
            )
        except (tokenize.TokenError, IndentationError):
            pass
    compact = re.sub(r"\s+", "", code)
    return ((tokenize.ERRORTOKEN, compact),)


def _verified_reference_candidates(
    db: Session,
    slug: str,
    language: str = "python",
) -> list[ReferenceCandidate]:
    """Load at most 25 unique verified ACs from a bounded recent-row window."""
    rows = (
        db.query(OjSubmission)
        .filter(
            OjSubmission.problem_slug == slug,
            OjSubmission.verdict == "AC",
            OjSubmission.language == language,
            OjSubmission.total > 0,
            OjSubmission.passed == OjSubmission.total,
        )
        .order_by(OjSubmission.created_at.desc(), OjSubmission.id.desc())
        .limit(ALIGNMENT_CONFIG.max_reference_rows_to_scan)
        .all()
    )
    candidates: list[ReferenceCandidate] = []
    seen_codes: set[tuple[tuple[int, str], ...]] = set()
    for recency_rank, row in enumerate(rows):
        code = (row.code or "").strip()
        identity = _normalized_code_identity(code, language) if code else ()
        if not identity or identity in seen_codes:
            continue
        seen_codes.add(identity)
        candidates.append(ReferenceCandidate(
            code=row.code,
            submission_id=int(row.id),
            total=int(row.total or 0),
            runtime_ms_avg=int(row.runtime_ms_avg or 0),
            recency_rank=recency_rank,
        ))
        if len(candidates) >= ALIGNMENT_CONFIG.max_reference_candidates:
            break
    return candidates


def _cluster_reference_candidates(
    candidates: list[ReferenceCandidate],
    language: str,
) -> list[ReferenceCluster]:
    """Build deterministic complete-link clusters and choose a medoid per strategy."""
    if not candidates:
        return []
    pair_scores: dict[tuple[int, int], float] = {}
    structures = [_code_structure(candidate.code, language) for candidate in candidates]

    def similarity(left_index: int, right_index: int) -> float:
        if left_index == right_index:
            return 1.0
        key = tuple(sorted((left_index, right_index)))
        if key not in pair_scores:
            pair_scores[key] = _structure_compatibility(
                structures[key[0]],
                structures[key[1]],
            )
        return pair_scores[key]

    member_indices: list[list[int]] = [[index] for index in range(len(candidates))]
    while True:
        best_merge: tuple[float, float, int, int] | None = None
        for left_cluster in range(len(member_indices)):
            for right_cluster in range(left_cluster + 1, len(member_indices)):
                cross_scores = [
                    similarity(left, right)
                    for left in member_indices[left_cluster]
                    for right in member_indices[right_cluster]
                ]
                minimum = min(cross_scores)
                if minimum < ALIGNMENT_CONFIG.reference_cluster_similarity:
                    continue
                candidate_merge = (
                    minimum,
                    sum(cross_scores) / len(cross_scores),
                    -left_cluster,
                    -right_cluster,
                )
                if best_merge is None or candidate_merge > best_merge:
                    best_merge = candidate_merge
        if best_merge is None:
            break
        left_cluster, right_cluster = -best_merge[2], -best_merge[3]
        member_indices[left_cluster].extend(member_indices[right_cluster])
        del member_indices[right_cluster]

    clusters: list[ReferenceCluster] = []
    for indices in member_indices:
        canonical_index = max(
            indices,
            key=lambda index: (
                sum(similarity(index, other) for other in indices) / len(indices),
                candidates[index].total,
                -(candidates[index].runtime_ms_avg or 10**9),
                -candidates[index].recency_rank,
                -candidates[index].submission_id,
            ),
        )
        members = tuple(candidates[index] for index in indices)
        clusters.append(ReferenceCluster(
            members=members,
            canonical=candidates[canonical_index],
        ))
    return sorted(clusters, key=lambda cluster: cluster.canonical.recency_rank)


def select_reference_solution(
    db: Session,
    slug: str,
    language: str = "python",
    *,
    student_code: str | None = None,
) -> ReferenceSelection | None:
    """Select a canonical verified solution from the closest strategy cluster."""
    candidates = _verified_reference_candidates(db, slug, language)
    if not candidates:
        return None
    clusters = _cluster_reference_candidates(candidates, language)
    if not student_code:
        selected_cluster = max(
            clusters,
            key=lambda cluster: (
                len(cluster.members),
                cluster.canonical.total,
                -cluster.canonical.recency_rank,
            ),
        )
        return ReferenceSelection(
            code=selected_cluster.canonical.code,
            cluster_size=len(selected_cluster.members),
            cluster_count=len(clusters),
            candidate_count=len(candidates),
        )

    student_structure = _code_structure(student_code, language)
    candidate_scores = {
        candidate.submission_id: _structure_compatibility(
            student_structure,
            _code_structure(candidate.code, language),
        )
        for candidate in candidates
    }

    def cluster_score(cluster: ReferenceCluster) -> tuple[float, float, int, int]:
        member_scores = [
            candidate_scores[member.submission_id]
            for member in cluster.members
        ]
        canonical_score = candidate_scores[cluster.canonical.submission_id]
        compatibility = 0.70 * max(member_scores) + 0.30 * canonical_score
        return (
            compatibility,
            canonical_score,
            len(cluster.members),
            -cluster.canonical.recency_rank,
        )

    selected_cluster = max(clusters, key=cluster_score)
    selected_score = cluster_score(selected_cluster)[0]
    return ReferenceSelection(
        code=selected_cluster.canonical.code,
        cluster_size=len(selected_cluster.members),
        cluster_count=len(clusters),
        candidate_count=len(candidates),
        compatibility=round(selected_score, 3),
    )


def find_reference_solution(
    db: Session,
    slug: str,
    language: str = "python",
    *,
    student_code: str | None = None,
) -> str | None:
    """Return selected code; without student context preserve newest-AC behavior."""
    if not student_code:
        candidates = _verified_reference_candidates(db, slug, language)
        return candidates[0].code if candidates else None
    selection = select_reference_solution(
        db,
        slug,
        language=language,
        student_code=student_code,
    )
    return selection.code if selection is not None else None


def _extract_var_value(var_snapshot: Any) -> Any:
    if isinstance(var_snapshot, dict):
        return var_snapshot.get("value", var_snapshot)
    return var_snapshot


def _vars_at_step(step: dict[str, Any]) -> dict[str, Any]:
    raw_vars = step.get("vars", {})
    if not isinstance(raw_vars, dict):
        return {}
    return {name: _extract_var_value(snapshot) for name, snapshot in raw_vars.items()}


def _values_equal(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if (
        isinstance(a, (int, float)) and isinstance(b, (int, float))
        and not isinstance(a, bool) and not isinstance(b, bool)
    ):
        return abs(a - b) < 1e-9
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_values_equal(a[key], b[key]) for key in a)
    return a == b


def _format_state(vars_map: dict[str, Any], focus_keys: list[str] | None = None) -> str:
    keys = focus_keys or list(vars_map)
    parts: list[str] = []
    for key in keys:
        if key not in vars_map:
            continue
        value_repr = repr(vars_map[key])
        if len(value_repr) > _MAX_VAR_REPR_LEN:
            value_repr = value_repr[:_MAX_VAR_REPR_LEN] + "..."
        parts.append(f"{key}={value_repr}")
    return ", ".join(parts)


def _find_common_keys(student_vars: dict[str, Any], reference_vars: dict[str, Any]) -> list[str]:
    common = set(student_vars) & set(reference_vars)
    return sorted(key for key in common if not key.startswith("_"))


def _snapshot_type(step: dict[str, Any], name: str, value: Any) -> str:
    snapshot = (step.get("vars") or {}).get(name)
    if isinstance(snapshot, dict) and snapshot.get("type"):
        return str(snapshot["type"])
    return type(value).__name__


def _python_statement_role(node: ast.stmt) -> str:
    if isinstance(node, ast.If):
        return "branch"
    if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
        return "loop"
    if isinstance(node, ast.Return):
        return "return"
    if isinstance(node, ast.Raise):
        return "exception"
    if isinstance(node, (ast.Break, ast.Continue)):
        return "loop_control"
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return "assignment"
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        func = node.value.func
        if isinstance(func, ast.Attribute) and func.attr in _MUTATING_METHODS:
            return "container_mutation"
        return "call"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "function_entry"
    return "state_change"


def _build_python_line_context(code: str) -> dict[int, SourceLineContext]:
    try:
        tree = ast.parse(code.strip())
    except SyntaxError:
        return {}

    contexts: dict[int, SourceLineContext] = {}

    def visit_statements(
        statements: list[ast.stmt],
        control_path: tuple[str, ...],
        branch_membership: tuple[tuple[int, bool], ...],
        loop_membership: tuple[int, ...],
    ) -> None:
        for node in statements:
            line = getattr(node, "lineno", None)
            if line is not None:
                contexts[line] = SourceLineContext(
                    role=_python_statement_role(node),
                    control_path=control_path,
                    branch_membership=branch_membership,
                    loop_membership=loop_membership,
                    condition=(
                        ast.unparse(node.test)
                        if isinstance(node, (ast.If, ast.While))
                        else ""
                    ),
                )

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit_statements(
                    node.body,
                    control_path + ("function",),
                    branch_membership,
                    loop_membership,
                )
                continue
            if isinstance(node, ast.If):
                header = int(node.lineno)
                visit_statements(
                    node.body,
                    control_path + ("branch:body",),
                    branch_membership + ((header, True),),
                    loop_membership,
                )
                visit_statements(
                    node.orelse,
                    control_path + ("branch:else",),
                    branch_membership + ((header, False),),
                    loop_membership,
                )
                continue
            if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                header = int(node.lineno)
                visit_statements(
                    node.body,
                    control_path + ("loop:body",),
                    branch_membership,
                    loop_membership + (header,),
                )
                visit_statements(
                    node.orelse,
                    control_path + ("loop:else",),
                    branch_membership,
                    loop_membership,
                )
                continue
            if isinstance(node, (ast.Try, ast.TryStar)):
                visit_statements(
                    node.body, control_path + ("try:body",), branch_membership, loop_membership
                )
                for handler in node.handlers:
                    visit_statements(
                        handler.body,
                        control_path + ("try:handler",),
                        branch_membership,
                        loop_membership,
                    )
                visit_statements(
                    node.orelse, control_path + ("try:else",), branch_membership, loop_membership
                )
                visit_statements(
                    node.finalbody,
                    control_path + ("try:finally",),
                    branch_membership,
                    loop_membership,
                )
                continue
            if isinstance(node, (ast.With, ast.AsyncWith)):
                visit_statements(
                    node.body, control_path + ("with",), branch_membership, loop_membership
                )
                continue
            if isinstance(node, ast.ClassDef):
                visit_statements(
                    node.body, control_path + ("class",), branch_membership, loop_membership
                )

    visit_statements(tree.body, (), (), ())
    return contexts


def _generic_line_role(text: str) -> str:
    stripped = text.strip().lower()
    if re.match(r"^(?:if|elif|else\s+if)\b", stripped):
        return "branch"
    if re.match(r"^(?:for|while)\b", stripped):
        return "loop"
    if re.match(r"^return\b", stripped):
        return "return"
    if re.match(r"^(?:raise|throw)\b", stripped):
        return "exception"
    if re.match(r"^(?:break|continue)\b", stripped):
        return "loop_control"
    if any(f".{method}(" in stripped for method in _MUTATING_METHODS):
        return "container_mutation"
    if re.search(r"(?<![=!<>])=(?!=)|\+=|-=|\*=|/=", stripped):
        return "assignment"
    if "(" in stripped and ")" in stripped:
        return "call"
    return "state_change"


def _build_source_line_context(code: str | None, language: str) -> dict[int, SourceLineContext]:
    if not code or not code.strip():
        return {}
    if (language or "").lower() in {"python", "py", "python3"}:
        return _build_python_line_context(code)
    return {
        line_number: SourceLineContext(role=_generic_line_role(text))
        for line_number, text in enumerate(code.strip().splitlines(), start=1)
        if text.strip()
    }


@dataclass(frozen=True)
class SemanticEvent:
    raw_index: int
    line: int | None
    event_type: str
    vars: dict[str, Any]
    var_types: dict[str, str]
    changed: tuple[str, ...]
    important: bool
    branch_outcome: Any = None
    source_role: str = ""
    control_path: tuple[str, ...] = ()
    raw: dict[str, Any] | None = None


def _explicit_event_type(step: dict[str, Any]) -> str:
    raw_type = str(step.get("event_type") or step.get("event") or step.get("kind") or "").lower()
    aliases = {
        "line": "state_change", "assignment": "assignment", "assign": "assignment",
        "branch": "branch", "condition": "branch", "loop": "loop", "call": "call",
        "return": "return", "exception": "exception", "raise": "exception",
        "container_mutation": "container_mutation",
    }
    return aliases.get(raw_type, raw_type)


def _branch_outcome(step: dict[str, Any]) -> Any:
    for key in ("branch_outcome", "condition", "taken", "outcome"):
        if key in step:
            return step[key]
    return None


def _safe_eval_condition(expression: str, variables: dict[str, Any]) -> bool | None:
    """Evaluate a small side-effect-free Python condition over trace values."""
    if not expression:
        return None
    try:
        root = ast.parse(expression, mode="eval").body
    except SyntaxError:
        return None

    comparison_ops = {
        ast.Eq: lambda left, right: left == right,
        ast.NotEq: lambda left, right: left != right,
        ast.Lt: lambda left, right: left < right,
        ast.LtE: lambda left, right: left <= right,
        ast.Gt: lambda left, right: left > right,
        ast.GtE: lambda left, right: left >= right,
        ast.In: lambda left, right: left in right,
        ast.NotIn: lambda left, right: left not in right,
        ast.Is: lambda left, right: left is right,
        ast.IsNot: lambda left, right: left is not right,
    }
    binary_ops = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
        ast.FloorDiv: lambda left, right: left // right,
        ast.Mod: lambda left, right: left % right,
    }

    def evaluate(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise ValueError("unknown name")
            return variables[node.id]
        if isinstance(node, ast.List):
            return [evaluate(item) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(evaluate(item) for item in node.elts)
        if isinstance(node, ast.Set):
            return {evaluate(item) for item in node.elts}
        if isinstance(node, ast.Dict):
            return {
                evaluate(key): evaluate(value)
                for key, value in zip(node.keys, node.values)
                if key is not None
            }
        if isinstance(node, ast.Subscript):
            return evaluate(node.value)[evaluate(node.slice)]
        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)
            if isinstance(node.op, ast.Not):
                return not value
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            raise ValueError("unsupported unary operator")
        if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
            return binary_ops[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.BoolOp):
            values = [bool(evaluate(item)) for item in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise ValueError("unsupported boolean operator")
        if isinstance(node, ast.Compare):
            left = evaluate(node.left)
            for operator, comparator in zip(node.ops, node.comparators):
                operation = comparison_ops.get(type(operator))
                if operation is None:
                    raise ValueError("unsupported comparison")
                right = evaluate(comparator)
                if not operation(left, right):
                    return False
                left = right
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "len"
            and len(node.args) == 1
            and not node.keywords
        ):
            return len(evaluate(node.args[0]))
        raise ValueError("unsupported condition")

    try:
        return bool(evaluate(root))
    except (ArithmeticError, KeyError, TypeError, ValueError):
        return None


def _inferred_control_outcome(
    event_type: str,
    line: int | None,
    next_context: SourceLineContext | None,
) -> bool | None:
    if line is None or next_context is None:
        return None
    if event_type == "branch":
        membership = dict(next_context.branch_membership)
        return membership.get(line)
    if event_type == "loop":
        return True if line in next_context.loop_membership else None
    return None


def _normalize_trace(
    steps: list[dict[str, Any]],
    *,
    code: str | None = None,
    language: str = "python",
) -> list[SemanticEvent]:
    line_contexts = _build_source_line_context(code, language)
    events: list[SemanticEvent] = []
    bounded_steps = steps[:_MAX_TRACE_STEPS_TO_COMPARE]
    for raw_index, step in enumerate(bounded_steps):
        vars_map = _vars_at_step(step)
        var_types = {name: _snapshot_type(step, name, value) for name, value in vars_map.items()}
        changed = tuple(name for name in (step.get("changed") or ()) if name in vars_map)
        line = step.get("line")
        source_context = line_contexts.get(line, SourceLineContext())
        event_type = _explicit_event_type(step)
        if not event_type:
            if source_context.role:
                event_type = source_context.role
            elif any(var_types.get(name) in _CONTAINER_TYPES for name in changed):
                event_type = "container_mutation"
            elif changed:
                event_type = "assignment"
            else:
                event_type = "state_change"
        branch = _branch_outcome(step) if event_type in {"branch", "loop"} else None
        if branch is None and event_type in {"branch", "loop"}:
            branch = _safe_eval_condition(source_context.condition, vars_map)
        if branch is None and event_type in {"branch", "loop"} and raw_index + 1 < len(bounded_steps):
            next_line = bounded_steps[raw_index + 1].get("line")
            branch = _inferred_control_outcome(event_type, line, line_contexts.get(next_line))
        only_temporary = bool(changed) and all(_TEMP_NAME_RE.match(name) for name in changed)
        important = (
            event_type in _CONTROL_EVENTS
            or event_type == "container_mutation"
            or any(_POINTER_NAME_RE.match(name) for name in changed)
            or (bool(changed) and not only_temporary)
        )
        event = SemanticEvent(
            raw_index=raw_index,
            line=line,
            event_type=event_type,
            vars=vars_map,
            var_types=var_types,
            changed=changed,
            important=important,
            branch_outcome=branch,
            source_role=source_context.role,
            control_path=source_context.control_path,
            raw=step,
        )
        if events and not important and _state_similarity(events[-1], event) >= 1.0:
            continue
        events.append(event)
    return events


def _pair_variables(left: SemanticEvent, right: SemanticEvent) -> list[tuple[str | None, str | None]]:
    left_names = [name for name in left.vars if not _TEMP_NAME_RE.match(name)]
    right_names = [name for name in right.vars if not _TEMP_NAME_RE.match(name)]
    pairs: list[tuple[str | None, str | None]] = []
    remaining_left, remaining_right = list(left_names), list(right_names)
    for name in list(remaining_left):
        if name in remaining_right:
            pairs.append((name, name))
            remaining_left.remove(name)
            remaining_right.remove(name)
    for left_name in list(remaining_left):
        match = next((
            right_name for right_name in remaining_right
            if left.var_types.get(left_name) == right.var_types.get(right_name)
            and _values_equal(left.vars[left_name], right.vars[right_name])
        ), None)
        if match is not None:
            pairs.append((left_name, match))
            remaining_left.remove(left_name)
            remaining_right.remove(match)
    for left_name in list(remaining_left):
        match = next((
            right_name for right_name in remaining_right
            if left.var_types.get(left_name) == right.var_types.get(right_name)
        ), None)
        if match is not None:
            pairs.append((left_name, match))
            remaining_left.remove(left_name)
            remaining_right.remove(match)
    pairs.extend((name, None) for name in remaining_left)
    pairs.extend((None, name) for name in remaining_right)
    return pairs


def _state_similarity(left: SemanticEvent, right: SemanticEvent) -> float:
    pairs = _pair_variables(left, right)
    if not pairs:
        return 1.0
    matched = sum(
        1.0 for left_name, right_name in pairs
        if left_name is not None and right_name is not None
        and _values_equal(left.vars[left_name], right.vars[right_name])
    )
    return matched / len(pairs)


def _changed_similarity(left: SemanticEvent, right: SemanticEvent) -> float:
    left_values = [
        left.vars[name] for name in left.changed
        if name in left.vars and not _TEMP_NAME_RE.match(name)
    ]
    right_values = [
        right.vars[name] for name in right.changed
        if name in right.vars and not _TEMP_NAME_RE.match(name)
    ]
    if not left_values and not right_values:
        return 1.0
    used: set[int] = set()
    matches = 0
    for value in left_values:
        for index, other in enumerate(right_values):
            if index not in used and _values_equal(value, other):
                used.add(index)
                matches += 1
                break
    return matches / max(len(left_values), len(right_values), 1)


def _event_type_similarity(left_type: str, right_type: str) -> float:
    if left_type == right_type:
        return 1.0
    if {left_type, right_type} <= _DATA_EVENT_TYPES:
        return 0.65
    if {left_type, right_type} <= {"branch", "loop"}:
        return 0.45
    return 0.0


def _semantic_similarity(left: SemanticEvent, right: SemanticEvent) -> float:
    if (
        left.event_type == right.event_type
        and left.event_type in {"branch", "loop"}
        and left.branch_outcome is not None and right.branch_outcome is not None
        and not _values_equal(left.branch_outcome, right.branch_outcome)
    ):
        return 0.0
    return (
        ALIGNMENT_CONFIG.state_weight * _state_similarity(left, right)
        + ALIGNMENT_CONFIG.changed_weight * _changed_similarity(left, right)
        + ALIGNMENT_CONFIG.event_type_weight
        * _event_type_similarity(left.event_type, right.event_type)
    )


def _control_context_similarity(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    if left == right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def _event_similarity(left: SemanticEvent, right: SemanticEvent) -> float:
    """Score an alignment candidate using state plus optional source context."""
    if (
        left.source_role
        and right.source_role
        and left.source_role != right.source_role
        and (left.source_role in _STRICT_CONTROL_ROLES or right.source_role in _STRICT_CONTROL_ROLES)
    ):
        return 0.10
    semantic_score = _semantic_similarity(left, right)
    numerator = semantic_score
    denominator = 1.0
    if left.source_role and right.source_role:
        numerator += (
            ALIGNMENT_CONFIG.source_role_weight
            * _event_type_similarity(left.source_role, right.source_role)
        )
        denominator += ALIGNMENT_CONFIG.source_role_weight
    if left.control_path and right.control_path:
        numerator += (
            ALIGNMENT_CONFIG.control_context_weight
            * _control_context_similarity(left.control_path, right.control_path)
        )
        denominator += ALIGNMENT_CONFIG.control_context_weight
    return numerator / denominator


def _align_events(
    student: list[SemanticEvent], reference: list[SemanticEvent]
) -> list[tuple[SemanticEvent | None, SemanticEvent | None, float]]:
    rows, cols = len(student), len(reference)
    scores = [[0.0] * (cols + 1) for _ in range(rows + 1)]
    moves = [[""] * (cols + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        scores[i][0], moves[i][0] = i * ALIGNMENT_CONFIG.gap_penalty, "up"
    for j in range(1, cols + 1):
        scores[0][j], moves[0][j] = j * ALIGNMENT_CONFIG.gap_penalty, "left"
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            similarity = _event_similarity(student[i - 1], reference[j - 1])
            diagonal = scores[i - 1][j - 1] + 2.0 * similarity - 1.0
            up = scores[i - 1][j] + ALIGNMENT_CONFIG.gap_penalty
            left = scores[i][j - 1] + ALIGNMENT_CONFIG.gap_penalty
            best = max(diagonal, up, left)
            scores[i][j] = best
            moves[i][j] = "diag" if best == diagonal else ("up" if best == up else "left")
    alignment: list[tuple[SemanticEvent | None, SemanticEvent | None, float]] = []
    i, j = rows, cols
    while i or j:
        move = moves[i][j]
        if move == "diag":
            student_event, reference_event = student[i - 1], reference[j - 1]
            alignment.append((student_event, reference_event, _event_similarity(student_event, reference_event)))
            i -= 1
            j -= 1
        elif move == "up":
            alignment.append((student[i - 1], None, 0.0))
            i -= 1
        else:
            alignment.append((None, reference[j - 1], 0.0))
            j -= 1
    alignment.reverse()
    return alignment


def _first_variable_difference(
    student: SemanticEvent, reference: SemanticEvent
) -> tuple[str, Any, Any, list[str], list[str]]:
    for student_name, reference_name in _pair_variables(student, reference):
        if student_name is None or reference_name is None:
            name = student_name or reference_name or ""
            return (
                name,
                student.vars.get(student_name) if student_name else None,
                reference.vars.get(reference_name) if reference_name else None,
                [student_name] if student_name else [],
                [reference_name] if reference_name else [],
            )
        student_value, reference_value = student.vars[student_name], reference.vars[reference_name]
        if not _values_equal(student_value, reference_value):
            label = student_name if student_name == reference_name else f"{student_name}/{reference_name}"
            return label, student_value, reference_value, [student_name], [reference_name]
    return "", None, None, [], []


def _divergence_result(
    student: SemanticEvent,
    reference: SemanticEvent,
    similarity: float,
    reference_source: str,
    *,
    reason: str | None = None,
    confidence_similarity: float | None = None,
) -> FirstDivergenceResult:
    variable, student_value, reference_value, student_focus, reference_focus = (
        _first_variable_difference(student, reference)
    )
    if reason is None:
        reason = "对齐后的语义事件首次偏离"
        if variable:
            reason += f"：{variable} 的学生值 {student_value!r} 与参考值 {reference_value!r} 不同"
    confidence_basis = similarity if confidence_similarity is None else confidence_similarity
    return FirstDivergenceResult(
        detected=True,
        step_index=student.raw_index,
        line=student.line,
        reference_line=reference.line,
        student_state=_format_state(student.vars, student_focus or None),
        reference_state=_format_state(reference.vars, reference_focus or None),
        divergent_variable=variable,
        explanation=reason,
        confidence=(
            "high"
            if confidence_basis <= ALIGNMENT_CONFIG.strong_divergence_similarity
            else "medium"
        ),
        reference_source=reference_source,
        alignment_score=round(similarity, 3),
    )


def detect_first_divergence(
    *,
    student_steps: list[dict[str, Any]],
    reference_steps: list[dict[str, Any]],
    reference_source: str = "ac_submission",
    student_code: str | None = None,
    reference_code: str | None = None,
    language: str = "python",
) -> FirstDivergenceResult:
    """Return the first meaningful mismatch after context-aware sequence alignment."""
    if not student_steps or not reference_steps:
        return FirstDivergenceResult(reason="student 或 reference trace 为空")
    student_events = _normalize_trace(student_steps, code=student_code, language=language)
    reference_events = _normalize_trace(reference_steps, code=reference_code, language=language)
    if not student_events or not reference_events:
        return FirstDivergenceResult(reason="归一化后的 student 或 reference trace 为空")
    for student_event, reference_event, similarity in _align_events(student_events, reference_events):
        if student_event is None or reference_event is None:
            unmatched = student_event or reference_event
            if unmatched and unmatched.event_type in {"return", "exception"}:
                counterpart = reference_events[-1] if student_event is not None else student_events[-1]
                if student_event is None:
                    return _divergence_result(
                        counterpart, unmatched, 0.0, reference_source,
                        reason=f"参考 trace 出现未对齐的 {unmatched.event_type} 事件",
                    )
                return _divergence_result(
                    unmatched, counterpart, 0.0, reference_source,
                    reason=f"学生 trace 出现未对齐的 {unmatched.event_type} 事件",
                )
            continue
        if (
            student_event.event_type == reference_event.event_type
            and student_event.event_type in {"branch", "loop"}
            and student_event.branch_outcome is not None
            and reference_event.branch_outcome is not None
            and not _values_equal(student_event.branch_outcome, reference_event.branch_outcome)
        ):
            control_label = "分支结果" if student_event.event_type == "branch" else "循环结果"
            return _divergence_result(
                student_event, reference_event, 0.0, reference_source,
                reason=(
                    f"{control_label}首次偏离：学生 {student_event.branch_outcome!r}，"
                    f"参考 {reference_event.branch_outcome!r}"
                ),
            )
        semantic_similarity = _semantic_similarity(student_event, reference_event)
        if semantic_similarity < ALIGNMENT_CONFIG.meaningful_similarity:
            return _divergence_result(
                student_event,
                reference_event,
                similarity,
                reference_source,
                confidence_similarity=semantic_similarity,
            )
    final_similarity = _state_similarity(student_events[-1], reference_events[-1])
    if final_similarity < ALIGNMENT_CONFIG.meaningful_similarity:
        return _divergence_result(
            student_events[-1], reference_events[-1], final_similarity, reference_source,
            reason="trace 结束时关键状态仍不一致",
        )
    return FirstDivergenceResult(
        reason="student 与 reference trace 经语义序列对齐后关键状态一致，无有意义偏离",
        reference_source=reference_source,
        alignment_score=1.0,
    )


def run_first_divergence_analysis(
    db: Session,
    *,
    slug: str,
    student_code: str,
    student_steps: list[dict[str, Any]],
    language: str = "python",
    run_reference_trace_fn: Any = None,
) -> FirstDivergenceResult:
    """Select a compatible verified reference, run it, and align both traces."""
    reference_selection = select_reference_solution(
        db, slug, language=language, student_code=student_code
    )
    if reference_selection is None:
        return FirstDivergenceResult(
            reason="insufficient_reference_trace: 该题目尚无完整验证的 AC 提交可作为参考解"
        )
    reference_code = reference_selection.code
    if reference_code.strip() == student_code.strip():
        return FirstDivergenceResult(reason="student 代码与参考解相同，无需比较")
    if run_reference_trace_fn is None:
        return FirstDivergenceResult(reason="未提供 reference trace 运行函数")
    try:
        reference_steps = run_reference_trace_fn(reference_code, slug, language)
    except Exception as exc:
        _logger.warning("参考解 trace 运行失败 slug=%s: %s", slug, exc)
        return FirstDivergenceResult(reason=f"参考解 trace 运行失败: {exc}")
    if not reference_steps:
        return FirstDivergenceResult(reason="参考解 trace 为空")
    return detect_first_divergence(
        student_steps=student_steps,
        reference_steps=reference_steps,
        reference_source=(
            f"canonical_ac_submission_cluster:{slug}:"
            f"cluster_size={reference_selection.cluster_size}:"
            f"clusters={reference_selection.cluster_count}"
        ),
        student_code=student_code,
        reference_code=reference_code,
        language=language,
    )
