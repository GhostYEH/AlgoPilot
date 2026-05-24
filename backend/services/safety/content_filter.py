"""生成内容安全过滤与基础合规检查。"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 敏感词示例（可扩展；生产可对接第三方审核 API）
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

# 学术防幻觉：禁止无依据的 LeetCode 题号模式（可改为白名单校验）
_FAKE_LC_PATTERN = re.compile(r"(?:力扣|leetcode)\s*#?\s*(\d{4,})", re.IGNORECASE)


@dataclass
class SafetyResult:
    text: str
    blocked: bool
    reasons: list[str]


class ContentSafetyFilter:
    max_chars: int = 48_000

    def check(self, text: str) -> SafetyResult:
        reasons: list[str] = []
        if not text or not text.strip():
            return SafetyResult(text="", blocked=True, reasons=["内容为空"])

        cleaned = text.strip()
        if len(cleaned) > self.max_chars:
            cleaned = cleaned[: self.max_chars] + "\n\n（内容过长已截断）"
            reasons.append("内容过长已截断")

        for pat in _SENSITIVE_PATTERNS:
            if pat.search(cleaned):
                reasons.append("命中敏感词过滤规则")
                return SafetyResult(text="", blocked=True, reasons=reasons)

        return SafetyResult(text=cleaned, blocked=False, reasons=reasons)

    def warn_hallucination_risk(self, text: str) -> list[str]:
        warnings: list[str] = []
        for m in _FAKE_LC_PATTERN.finditer(text):
            num = m.group(1)
            if int(num) > 3500:
                warnings.append(f"疑似虚构题号引用：{m.group(0)}")
        return warnings


content_filter = ContentSafetyFilter()
