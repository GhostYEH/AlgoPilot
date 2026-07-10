"""检查删除重复后是否还有题目低于10个"""
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
bundle = json.loads((BACKEND / 'data/oj/tests_bundle.json').read_text(encoding='utf-8'))

under_10_after_dedup = []
for slug, cfg in bundle.items():
    samples = cfg.get('samples') or []
    hidden = cfg.get('hidden') or []
    sample_stds = set(c.get('stdin') for c in samples)
    # 模拟删除重复
    new_hidden = [c for c in hidden if c.get('stdin') not in sample_stds]
    total = len(samples) + len(new_hidden)
    if total < 10:
        under_10_after_dedup.append((slug, len(samples), len(hidden), len(new_hidden), total))

print(f"删除重复后会低于10个用例的题目: {len(under_10_after_dedup)}")
for slug, s, h, nh, t in sorted(under_10_after_dedup, key=lambda x: x[4]):
    print(f"  {slug}: samples={s}, hidden={h} -> {nh}, total={t}")
