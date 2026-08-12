"""评测结果导出为 JSON / CSV。"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from evaluation.metrics import EvaluationReport


def export_json(report: EvaluationReport, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def export_csv(report: EvaluationReport, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "name", "value", "unit", "sample_size", "available", "reason"])
        categories = {
            "bug_localization": report.bug_localization,
            "bug_classification": report.bug_classification,
            "counterexample": report.counterexample,
            "ai_reliability": report.ai_reliability,
            "teaching_effect": report.teaching_effect,
            "system_performance": report.system_performance,
        }
        for cat, metrics in categories.items():
            for m in metrics:
                writer.writerow(
                    [cat, m.name, m.value, m.unit, m.sample_size, m.is_available, m.reason]
                )
    return p


def print_summary(report: EvaluationReport) -> None:
    """终端友好输出。"""
    sections = {
        "Bug 定位": report.bug_localization,
        "Bug 类型识别": report.bug_classification,
        "反例生成": report.counterexample,
        "AI 可靠性": report.ai_reliability,
        "教学效果": report.teaching_effect,
        "系统性能": report.system_performance,
    }
    for title, metrics in sections.items():
        print(f"\n=== {title} ===")
        if not metrics:
            print("  (无指标)")
            continue
        for m in metrics:
            if m.is_available:
                print(f"  {m.name}: {m.value}{m.unit} (n={m.sample_size})")
            else:
                print(f"  {m.name}: N/A — {m.reason}")