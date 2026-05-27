"""ASTAnalyzerAgent：静动结合之静态语法诊断（死循环 / 越界 / 野指针风险）。"""

from __future__ import annotations

import ast
import asyncio
import concurrent.futures
import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from core.config import settings
from services.llm import chat_completion

RiskLevel = Literal["high", "medium", "low"]

_POINTER_LIKE = frozenset(
    {
        "left",
        "right",
        "l",
        "r",
        "i",
        "j",
        "lo",
        "hi",
        "low",
        "high",
        "slow",
        "fast",
        "curr",
        "current",
        "head",
        "tail",
        "p",
        "q",
        "start",
        "end",
        "mid",
        "k",
        "ptr",
        "index",
        "pos",
    }
)

_CPP_LOOP_RE = re.compile(r"\b(?:while|for)\s*\(", re.I)
_CPP_WHILE_BLOCK = re.compile(
    r"while\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
    re.MULTILINE | re.DOTALL,
)
_CPP_WHILE_TRUE = re.compile(r"while\s*\(\s*(?:true|1)\s*\)", re.I)
_CPP_BREAK = re.compile(r"\bbreak\s*;")
_CPP_UNINIT_PTR = re.compile(
    r"(?:int|long|char|double|float|bool|auto)\s*\*\s*(\w+)\s*;",
    re.MULTILINE,
)

_CPP_LLM_SYSTEM = """你是一个 C++ 静态分析器。只检查用户代码中的 while/for 循环与数组访问。
关注：死循环（指针/计数器未更新）、明显数组越界、未初始化指针解引用。
不要解释过程。严格只输出一个 JSON 对象：
{"safe": true}
或
{"safe": false, "reason": "while循环中left和right指针未更新"}
reason 使用简短中文。"""


@dataclass
class AstFinding:
    level: RiskLevel
    code: str
    message: str
    line: int | None = None


@dataclass
class AstAuditResult:
    passed: bool
    status: Literal["approved", "rejected"]
    agent: str = "ASTAnalyzerAgent"
    reason: str = ""
    findings: list[AstFinding] = field(default_factory=list)
    language: str = "python"
    source: str = "rule"  # rule | llm | fast_pass

    def to_rejection_payload(self) -> dict[str, Any]:
        return {
            "status": "rejected",
            "agent": self.agent,
            "reason": self.reason,
            "findings": [
                {"level": f.level, "code": f.code, "message": f.message, "line": f.line}
                for f in self.findings
            ],
        }

    def agent_log(self, *, passed: bool) -> dict[str, str]:
        if passed:
            return {
                "agent": "ASTAnalyzerAgent",
                "action": "静态抽象语法树扫描",
                "detail": "未发现死循环特征，移交动态沙箱",
                "status": "done",
            }
        return {
            "agent": "ASTAnalyzerAgent",
            "action": "静态熔断",
            "detail": self.reason,
            "status": "error",
        }


def _strip_cpp_strings_comments(code: str) -> str:
    out: list[str] = []
    i = 0
    n = len(code)
    while i < n:
        if code.startswith("//", i):
            i = code.find("\n", i)
            if i < 0:
                break
            continue
        if code.startswith("/*", i):
            end = code.find("*/", i + 2)
            i = end + 2 if end >= 0 else n
            continue
        if code[i] in "\"'":
            q = code[i]
            i += 1
            while i < n and code[i] != q:
                if code[i] == "\\":
                    i += 2
                else:
                    i += 1
            i += 1
            continue
        out.append(code[i])
        i += 1
    return "".join(out)


def _cpp_has_loops(code: str) -> bool:
    return bool(_CPP_LOOP_RE.search(_strip_cpp_strings_comments(code)))


def _analyze_cpp_regex(code: str) -> list[AstFinding]:
    findings: list[AstFinding] = []
    stripped = _strip_cpp_strings_comments(code)

    if _CPP_WHILE_TRUE.search(stripped):
        for m in _CPP_WHILE_BLOCK.finditer(stripped):
            body = m.group(1)
            if not _CPP_BREAK.search(body):
                findings.append(
                    AstFinding(
                        level="high",
                        code="cpp_while_true",
                        message="C++ while(true/1) 循环体内未见 break，极易死循环",
                    )
                )
                break

    for m in _CPP_WHILE_BLOCK.finditer(stripped):
        header_start = stripped.rfind("while", 0, m.start())
        header = stripped[header_start : m.start() + 20] if header_start >= 0 else ""
        body = m.group(1)
        cond_match = re.search(r"while\s*\(([^)]*)\)", header + "while(")
        if not cond_match:
            continue
        cond = cond_match.group(1)
        cond_vars = set(re.findall(r"\b([a-zA-Z_]\w*)\b", cond))
        ptrs = [v for v in cond_vars if v in _POINTER_LIKE]
        if not ptrs:
            continue
        names_pat = "|".join(re.escape(p) for p in ptrs)
        upd = rf"\b(?:{names_pat})\s*(?:\+\+|--|\+=|-=|=)(?!=)"
        if not re.search(upd, body, re.I):
            joined = "、".join(ptrs)
            findings.append(
                AstFinding(
                    level="high",
                    code="cpp_stale_pointer",
                    message=(
                        f"while 条件含 {joined}，但循环体内未检测到"
                        f" {joined} 的更新（++/--/=），可能导致死循环"
                    ),
                )
            )

    declared_ptrs: dict[str, int] = {}
    for m in _CPP_UNINIT_PTR.finditer(stripped):
        declared_ptrs[m.group(1)] = stripped[: m.start()].count("\n") + 1

    for name, line_no in list(declared_ptrs.items()):
        decl_region = re.search(
            rf"(?:int|long|char|double|float|bool|auto)\s*\*\s*{re.escape(name)}\s*;",
            stripped,
        )
        if not decl_region:
            continue
        after = stripped[decl_region.end() : decl_region.end() + 400]
        if re.search(rf"\b{re.escape(name)}\s*=", after):
            declared_ptrs.pop(name, None)
            continue
        if re.search(rf"(?:\*{re.escape(name)}\b|{re.escape(name)}\s*->)", after):
            findings.append(
                AstFinding(
                    level="high",
                    code="cpp_uninit_ptr",
                    message=f"指针 {name} 声明后可能未初始化即使用，存在野指针风险",
                    line=line_no,
                )
            )

    return findings


def _parse_llm_guard_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def _run_async(coro):
    """在 sync / async 上下文中安全运行协程，避免嵌套 asyncio.run 崩溃。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        return ex.submit(asyncio.run, coro).result(timeout=45)


async def _llm_cpp_static_guard(code: str) -> AstFinding | None:
    if not settings.llm_configured:
        return None
    snippet = code[:4500]
    try:
        raw = await chat_completion(
            [
                {"role": "system", "content": _CPP_LLM_SYSTEM},
                {"role": "user", "content": f"```cpp\n{snippet}\n```"},
            ],
            temperature=0.1,
            max_tokens=280,
        )
        data = _parse_llm_guard_json(raw)
        if data.get("safe") is True:
            return None
        reason = str(data.get("reason") or "模型检测到循环风险").strip()
        return AstFinding(level="high", code="llm_cpp_guard", message=reason)
    except Exception:
        return None


def _analyze_cpp(code: str) -> tuple[list[AstFinding], str]:
    """
    C++ 专用：禁止 Python ast。
    1) 无 while/for → 秒级放行
    2) 正则初筛
    3) 含循环时 Fast LLM Guard
    """
    if not _cpp_has_loops(code):
        return [], "fast_pass"

    findings = _analyze_cpp_regex(code)
    high = [f for f in findings if f.level == "high"]
    if high:
        return findings, "regex"

    llm_finding = _run_async(_llm_cpp_static_guard(code))
    if llm_finding:
        return [llm_finding], "llm"

    return findings, "llm" if settings.llm_configured else "regex"


# --- Python：仅 python 使用 ast 模块 ---


def _is_constant_true(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value in (True, 1)


def _names_in_expr(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    out: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            out.add(n.id)
    return out


def _assigned_in_stmts(stmts: list[ast.stmt]) -> set[str]:
    assigned: set[str] = set()

    def add_target(t: ast.AST) -> None:
        if isinstance(t, ast.Name):
            assigned.add(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for elt in t.elts:
                add_target(elt)

    def walk_stmt_list(body: list[ast.stmt]) -> None:
        for st in body:
            if isinstance(st, ast.Assign):
                for t in st.targets:
                    add_target(t)
            elif isinstance(st, ast.AugAssign):
                add_target(st.target)
            elif isinstance(st, ast.AnnAssign) and st.target:
                add_target(st.target)
            elif isinstance(st, ast.For):
                add_target(st.target)
                walk_stmt_list(st.body)
                walk_stmt_list(st.orelse)
            elif isinstance(st, (ast.While, ast.If, ast.With)):
                walk_stmt_list(getattr(st, "body", []))
                walk_stmt_list(getattr(st, "orelse", []))
            elif isinstance(st, ast.Try):
                walk_stmt_list(st.body)
                for h in st.handlers:
                    walk_stmt_list(h.body)
                walk_stmt_list(st.orelse)
                walk_stmt_list(st.finalbody)

    walk_stmt_list(stmts)
    return assigned


def _body_has_break_or_return(stmts: list[ast.stmt]) -> bool:
    for st in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(st, (ast.Break, ast.Return)):
            return True
    return False


class _PythonLoopRiskVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[AstFinding] = []

    def visit_While(self, node: ast.While) -> None:
        line = getattr(node, "lineno", None)
        if _is_constant_true(node.test) and not _body_has_break_or_return(node.body):
            self.findings.append(
                AstFinding(
                    level="high",
                    code="infinite_while_true",
                    message="while True/1 循环体内无 break/return，极易死循环",
                    line=line,
                )
            )
        cond_vars = _names_in_expr(node.test)
        updated = _assigned_in_stmts(node.body)
        stale = [v for v in cond_vars if v in _POINTER_LIKE and v not in updated]
        if stale and node.body:
            joined = "、".join(stale)
            self.findings.append(
                AstFinding(
                    level="high",
                    code="stale_loop_pointer",
                    message=(
                        f"while 循环条件依赖 {joined}，但循环体内未检测到对"
                        f" {joined} 的赋值/自增，可能导致死循环"
                    ),
                    line=line,
                )
            )
        self.generic_visit(node)


def _analyze_python(code: str) -> list[AstFinding]:
    findings: list[AstFinding] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [
            AstFinding(
                level="high",
                code="syntax_error",
                message=f"Python 语法错误：{e.msg}",
                line=e.lineno,
            )
        ]

    visitor = _PythonLoopRiskVisitor()
    visitor.visit(tree)
    findings.extend(visitor.findings)
    return findings


class ASTAnalyzerAgent:
    """静态语法诊断：Python 用 ast；C++ 用正则 + Fast LLM，绝不混用 Python ast 解析 C++。"""

    name = "ASTAnalyzerAgent"
    role = "静态语法诊断 · 死循环/越界/野指针"

    @classmethod
    def audit(cls, user_code: str, *, language: str = "python") -> AstAuditResult:
        lang = (language or "python").lower().replace("c++", "cpp")
        code = (user_code or "").strip()
        if not code:
            return AstAuditResult(
                passed=True,
                status="approved",
                agent=cls.name,
                reason="空代码，跳过静态分析",
                language=lang,
            )

        if lang in ("cpp", "cxx"):
            findings, src = _analyze_cpp(code)
        elif lang in ("python", "py"):
            findings = _analyze_python(code)
            src = "rule"
        else:
            return AstAuditResult(
                passed=True,
                status="approved",
                agent=cls.name,
                reason=f"语言 {lang} 暂无静态规则，跳过",
                language=lang,
            )

        high = [f for f in findings if f.level == "high"]
        if high:
            primary = high[0]
            reason = "静态分析拦截：" + primary.message + "，为保护沙箱已拦截本次运行。"
            return AstAuditResult(
                passed=False,
                status="rejected",
                agent=cls.name,
                reason=reason,
                findings=findings,
                language=lang,
                source=src,
            )

        msg = (
            "未发现 while/for 循环，已秒级放行"
            if src == "fast_pass"
            else "静态审查通过，未发现死循环特征"
        )
        return AstAuditResult(
            passed=True,
            status="approved",
            agent=cls.name,
            reason=msg,
            findings=findings,
            language=lang,
            source=src,
        )
