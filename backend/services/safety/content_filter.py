"""生成内容安全过滤与 SafetyAgent 显式把关。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"翻墙",
        r"色情",
        r"赌博",
        r"毒品",
        r"暴恐",
        r"政治敏感",
    )
]

_FAKE_LC_PATTERN = re.compile(r"(?:力扣|leetcode)\s*#?\s*(\d{4,})", re.IGNORECASE)

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"忽略(以上|先前|上面).{0,8}指令",
        r"system\s*:\s*you\s+are",
    )
]


@dataclass
class SafetyResult:
    text: str
    blocked: bool
    reasons: list[str] = field(default_factory=list)
    hallucination_warnings: list[str] = field(default_factory=list)
    sensitive_risks: list[str] = field(default_factory=list)
    prompt_injection_risks: list[str] = field(default_factory=list)


@dataclass
class SafetyStructuredResult:
    status: str
    passed: bool
    text: str
    sensitive_risks: list[str] = field(default_factory=list)
    prompt_injection_risks: list[str] = field(default_factory=list)
    hallucination_warnings: list[str] = field(default_factory=list)
    logs: list[dict] = field(default_factory=list)


class ContentSafetyFilter:
    max_chars: int = 48_000

    def check(self, text: str) -> SafetyResult:
        reasons: list[str] = []
        sensitive: list[str] = []
        injection: list[str] = []
        if not text or not text.strip():
            return SafetyResult(text="", blocked=True, reasons=["内容为空"])

        cleaned = text.strip()
        if len(cleaned) > self.max_chars:
            cleaned = cleaned[: self.max_chars] + "\n\n（内容过长已截断）"
            reasons.append("内容过长已截断")

        for pat in _SENSITIVE_PATTERNS:
            if pat.search(cleaned):
                sensitive.append("命中敏感词过滤规则")
                return SafetyResult(
                    text="",
                    blocked=True,
                    reasons=["命中敏感词过滤规则"],
                    sensitive_risks=sensitive,
                )

        for pat in _INJECTION_PATTERNS:
            if pat.search(cleaned):
                injection.append("疑似 Prompt 注入")
                return SafetyResult(
                    text="",
                    blocked=True,
                    reasons=["疑似 Prompt 注入"],
                    prompt_injection_risks=injection,
                )

        hallucination_warnings = self.warn_hallucination_risk(cleaned)
        return SafetyResult(
            text=cleaned,
            blocked=False,
            reasons=reasons,
            hallucination_warnings=hallucination_warnings,
        )

    def warn_hallucination_risk(self, text: str) -> list[str]:
        warnings: list[str] = []
        for m in _FAKE_LC_PATTERN.finditer(text):
            num = m.group(1)
            if int(num) > 3500:
                warnings.append(f"疑似虚构题号引用：{m.group(0)}")
        return warnings


content_filter = ContentSafetyFilter()


class SafetyAgent:
    name = "SafetyAgent"
    role = "内容安全审查与防幻觉把关"

    def audit(self, text: str, *, resource_type: str = "") -> tuple[str, list[dict], bool]:
        structured = self.audit_structured(text, resource_type=resource_type)
        return structured.text, structured.logs, structured.passed

    def audit_structured(self, text: str, *, resource_type: str = "") -> SafetyStructuredResult:
        safety = content_filter.check(text)
        logs: list[dict] = []

        if safety.blocked:
            detail = "；".join(safety.reasons) or "内容未通过安全审查"
            logs.append(
                {
                    "agent": self.name,
                    "role": self.role,
                    "action": "内容安全审查未通过",
                    "detail": detail,
                    "status": "error",
                    "resource_type": resource_type,
                }
            )
            return SafetyStructuredResult(
                status="failed",
                passed=False,
                text="",
                sensitive_risks=list(safety.sensitive_risks),
                prompt_injection_risks=list(safety.prompt_injection_risks),
                hallucination_warnings=list(safety.hallucination_warnings),
                logs=logs,
            )

        if safety.hallucination_warnings:
            logs.append(
                {
                    "agent": self.name,
                    "role": self.role,
                    "action": "学术幻觉风险预警",
                    "detail": "；".join(safety.hallucination_warnings[:3]),
                    "status": "warn",
                    "resource_type": resource_type,
                }
            )
            detail = (
                f"内容安全审查通过，发现 {len(safety.hallucination_warnings)} 处疑似幻觉引用，"
                "已标注后准许下发资源"
            )
            return SafetyStructuredResult(
                status="warning",
                passed=True,
                text=safety.text,
                hallucination_warnings=list(safety.hallucination_warnings),
                logs=logs
                + [
                    {
                        "agent": self.name,
                        "role": self.role,
                        "action": "内容安全审查通过",
                        "detail": detail,
                        "status": "warn",
                        "resource_type": resource_type,
                    }
                ],
            )

        detail = "内容安全审查通过，未发现事实性幻觉，准许下发资源"
        logs.append(
            {
                "agent": self.name,
                "role": self.role,
                "action": "内容安全审查通过",
                "detail": detail,
                "status": "done",
                "resource_type": resource_type,
            }
        )
        return SafetyStructuredResult(
            status="passed",
            passed=True,
            text=safety.text,
            logs=logs,
        )


safety_agent = SafetyAgent()
