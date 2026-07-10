import json
from pathlib import Path
from collections import defaultdict

bundle = json.loads(Path('data/oj/tests_bundle.json').read_text(encoding='utf-8'))

module_counts = defaultdict(lambda: {'count': 0, 'total_cases': 0})
for slug, cfg in bundle.items():
    module = cfg.get('module_key', 'unknown')
    samples = len(cfg.get('samples') or [])
    hidden = len(cfg.get('hidden') or [])
    module_counts[module]['count'] += 1
    module_counts[module]['total_cases'] += samples + hidden

print(f"{'Module':<20} {'Problems':<10} {'Total Cases':<15} {'Avg per Problem':<20}")
print('-' * 70)
for module, data in sorted(module_counts.items()):
    avg = data['total_cases'] / data['count'] if data['count'] > 0 else 0
    print(f"{module:<20} {data['count']:<10} {data['total_cases']:<15} {avg:.1f}")

# List problems needing more test cases (less than 10)
print("\nProblems needing more test cases:")
for slug, cfg in sorted(bundle.items()):
    samples = len(cfg.get('samples') or [])
    hidden = len(cfg.get('hidden') or [])
    total = samples + hidden
    if total < 10:
        print(f"  {slug}: {total} cases (need {10 - total} more)")
