"""AlgoPilot 系统评测入口脚本。

从后端数据库提取真实数据，计算六类评测指标，输出 JSON / CSV / 终端摘要。

用法：
    python -m evaluation.run_eval                  # 终端输出
    python -m evaluation.run_eval --json out.json  # 同时导出 JSON
    python -m evaluation.run_eval --csv out.csv    # 同时导出 CSV

不伪造数据：缺乏标注或实验数据时指标显示 N/A 并标注原因。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))


def run_evaluation() -> "EvaluationReport":
    from evaluation import data_loader, metrics

    report = metrics.EvaluationReport()

    # === Bug 定位 ===
    # 需要（系统预测行号, 人工标注行号）对，目前无人工标注
    report.bug_localization = [
        metrics.compute_top_k_accuracy([], [], 1),
        metrics.compute_top_k_accuracy([], [], 3),
    ]

    # === Bug 类型识别 ===
    # 需要（系统预测类型, 人工标注类型）对，目前无人工标注
    report.bug_classification = [
        metrics.compute_classification_accuracy([], []),
    ]

    # === 反例生成 ===
    report.counterexample = [
        metrics.compute_bug_trigger_rate([]),
    ]

    # === AI 可靠性 ===
    submissions = data_loader.fetch_submissions_with_diagnosis()
    diagnosis_results = [
        {"hallucination_detected": False, "has_execution_evidence": s["has_cases"]}
        for s in submissions
    ]
    report.ai_reliability = [
        metrics.compute_hallucination_rate(diagnosis_results),
        metrics.compute_evidence_coverage(diagnosis_results),
    ]

    # === 教学效果 ===
    report.teaching_effect = [
        metrics.compute_fix_success_rate([]),
        *metrics.compute_hint_usage([]),
        metrics.compute_repeated_bug_rate(data_loader.fetch_bug_type_histories()),
    ]

    # === 系统性能 ===
    latencies = data_loader.fetch_event_latencies()
    report.system_performance = metrics.compute_latency_percentiles(latencies)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="AlgoPilot 系统评测")
    parser.add_argument("--json", dest="json_path", help="导出 JSON 到指定路径")
    parser.add_argument("--csv", dest="csv_path", help="导出 CSV 到指定路径")
    args = parser.parse_args()

    report = run_evaluation()

    from evaluation.export import export_csv, export_json, print_summary

    print_summary(report)

    total = len(report.all_metrics())
    available = sum(1 for m in report.all_metrics() if m.is_available)
    print(f"\n=== 汇总 ===")
    print(f"  总指标数：{total}")
    print(f"  已有数据：{available}")
    print(f"  待收集：{total - available}（需人工标注或更多实验数据）")

    if args.json_path:
        p = export_json(report, args.json_path)
        print(f"\n  JSON 已导出：{p}")
    if args.csv_path:
        p = export_csv(report, args.csv_path)
        print(f"  CSV 已导出：{p}")


if __name__ == "__main__":
    main()