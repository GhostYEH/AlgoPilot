import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent

bundle = json.loads((BACKEND_ROOT / 'data/oj/tests_bundle.json').read_text(encoding='utf-8'))

# Check all problematic entries mentioned in the error
problems = [
    ('valid-parentheses', 8),
    ('reverse-vowels-of-a-string', 9),
    ('longest-happy-prefix', 1),
    ('shortest-palindrome', 2),
    ('replace-space-lcof', 2),
]

for slug, idx in problems:
    if slug in bundle:
        cfg = bundle[slug]
        hidden = cfg.get('hidden', [])
        if idx < len(hidden):
            case = hidden[idx]
            print(f"{slug} hidden[{idx}]:")
            print(f"  raw case: {case}")
            print(f"  stdin={repr(case.get('stdin'))}, stdout={repr(case.get('stdout'))}")
            print(f"  args={repr(case.get('args'))}, expected={repr(case.get('expected'))}")
            print()
        else:
            print(f"{slug}: hidden has only {len(hidden)} entries, no index {idx}")
    else:
        print(f"{slug}: not found in bundle")
