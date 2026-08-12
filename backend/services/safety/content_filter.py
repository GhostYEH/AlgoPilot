"""生成内容安全过滤与 SafetyAgent 显式把关。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# 敏感词规则：覆盖政治、色情、赌博、毒品、暴恐、邪教、歧视、自残、个人隐私等基础类别。
# 命中即阻断（返回 blocked=True），避免不合规内容下发到学生侧。
_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"翻墙",
        r"色情|淫秽|黄色电影|av女优|成人视频",
        r"赌博|博彩|时时彩|六合彩|赌场|赌资",
        r"毒品|冰毒|大麻|海洛因|可卡因|摇头丸|吸毒",
        r"暴恐|恐怖袭击|炸弹制作|自制炸药|纵火",
        r"政治敏感|颠覆国家|分裂国家|港独|台独|疆独|藏独",
        r"邪教|法轮|全能神|门徒会",
        r"自残|自杀方法|轻生方式|上吊|割腕|跳楼指南",
        r"辱骂|侮辱|歧视|仇恨言论|种族歧视",
        r"私服|外挂|刷钻|代练作弊",
        # 个人隐私：手机号、身份证、银行卡（基础正则，避免误伤教学内容）
        r"1[3-9]\d{9}",
        r"\d{17}[\dXx]",
        r"\b\d{16,19}\b",
    )
]

# 虚构学术事实检测：力扣题号 > 3500 / arXiv 编号 / DOI / ISBN
_FAKE_LC_PATTERN = re.compile(r"(?:力扣|leetcode)\s*#?\s*(\d{4,})", re.IGNORECASE)
_FAKE_ARXIV_PATTERN = re.compile(r"arxiv[:\s]?\d{4}\.\d{4,5}", re.IGNORECASE)
_FAKE_DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
_FAKE_ISBN_PATTERN = re.compile(r"ISBN[:\s]?\d{9}[\dXx]", re.IGNORECASE)

# Prompt 注入检测：覆盖中英文常见注入话术与 ChatML 等格式注入。
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        # 英文注入
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?prior",
        r"override\s+(system|instructions)",
        r"system\s*:\s*you\s+are",
        r"new\s+role\s*:",
        r"now\s+you\s+are\s+a",
        r"#\s*new\s+instructions?\s*:",
        # 中文注入
        r"忽略(以上|先前|上面|上文|前面|前文).{0,12}(指令|规则|设定|提示|prompt)",
        r"忘掉(之前|上文|前面|前面所有)",
        r"现在(你|请你)(是|扮演|充当)\s*",
        r"新角色[:：]\s*",
        r"新指令[:：]\s*",
        r"重新设定(你|角色)",
        # ChatML / 特殊 token 注入
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[/INST\]",
        r"<s>\[INST\]",
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
            m = pat.search(cleaned)
            if m:
                sensitive.append(f"命中敏感词过滤规则：{m.group(0)[:20]}")
                return SafetyResult(
                    text="",
                    blocked=True,
                    reasons=["命中敏感词过滤规则"],
                    sensitive_risks=sensitive,
                )

        for pat in _INJECTION_PATTERNS:
            m = pat.search(cleaned)
            if m:
                injection.append(f"疑似 Prompt 注入：{m.group(0)[:30]}")
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
        for m in _FAKE_ARXIV_PATTERN.finditer(text):
            warnings.append(f"疑似虚构 arXiv 编号：{m.group(0)}")
        for m in _FAKE_DOI_PATTERN.finditer(text):
            warnings.append(f"疑似虚构 DOI：{m.group(0)}")
        for m in _FAKE_ISBN_PATTERN.finditer(text):
            warnings.append(f"疑似虚构 ISBN：{m.group(0)}")
        return warnings

    def check_stream_chunk(self, chunk: str) -> bool:
        """对流式 chunk 做轻量级增量检测，命中即返回 True 表示应阻断。

        用于在 SSE 流式输出过程中对每个 token 段做实时安全扫描，
        避免等完整生成后再过滤时敏感内容已部分下发到前端。
        """
        if not chunk:
            return False
        for pat in _SENSITIVE_PATTERNS:
            if pat.search(chunk):
                return True
        for pat in _INJECTION_PATTERNS:
            if pat.search(chunk):
                return True
        return False


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
