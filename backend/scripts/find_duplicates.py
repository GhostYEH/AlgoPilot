"""修复重复测试用例：删除与 samples 重复的 hidden 用例"""
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
bundle = json.loads((BACKEND / 'data/oj/tests_bundle.json').read_text(encoding='utf-8'))

# 找出重复
dup_report = []
for slug, cfg in bundle.items():
    samples = cfg.get('samples') or []
    hidden = cfg.get('hidden') or []
    sample_stds = set(c.get('stdin') for c in samples)
    dup_indices = []
    for i, c in enumerate(hidden):
        if c.get('stdin') in sample_stds:
            dup_indices.append(i)
    if dup_indices:
        dup_report.append((slug, len(samples), len(hidden), dup_indices))

print(f"有 {len(dup_report)} 道题存在 samples-hidden 重复")
for slug, s, h, indices in dup_report:
    print(f"  {slug}: samples={s}, hidden={h}, 重复hidden索引={indices}")
