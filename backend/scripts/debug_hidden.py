import json
from pathlib import Path

bundle = json.loads(Path('data/oj/tests_bundle.json').read_text(encoding='utf-8'))

# Check valid-parentheses hidden cases
if 'valid-parentheses' in bundle:
    cfg = bundle['valid-parentheses']
    print('valid-parentheses hidden cases:')
    for i, c in enumerate(cfg.get('hidden', [])):
        stdin_val = c.get('stdin')
        stdout_val = c.get('stdout')
        print(f'  hidden[{i}]: stdin={repr(stdin_val[:30]) if stdin_val else None}... stdout={repr(stdout_val[:20]) if stdout_val else None}')
        print(f'    has args: {c.get("args") is not None}, has expected: {c.get("expected") is not None}')
        print(f'    raw keys: {list(c.keys())}')

print()

# Check reverse-vowels-of-a-string
if 'reverse-vowels-of-a-string' in bundle:
    cfg = bundle['reverse-vowels-of-a-string']
    print('reverse-vowels-of-a-string hidden cases:')
    for i, c in enumerate(cfg.get('hidden', [])):
        stdin_val = c.get('stdin')
        stdout_val = c.get('stdout')
        print(f'  hidden[{i}]: stdin={repr(stdin_val[:30]) if stdin_val else None}... stdout={repr(stdout_val[:20]) if stdout_val else None}')
        print(f'    raw keys: {list(c.keys())}')
