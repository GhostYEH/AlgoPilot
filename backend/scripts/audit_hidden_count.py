"""Audit hidden test case counts per problem in tests_bundle.json.

Reports problems that have fewer than 5 hidden test cases.
"""
import json
from pathlib import Path

BUNDLE_PATH = Path(__file__).resolve().parent.parent / 'data' / 'oj' / 'tests_bundle.json'
MIN_HIDDEN = 5


def main() -> None:
    bundle = json.loads(BUNDLE_PATH.read_text(encoding='utf-8'))
    insufficient = []
    print(f"{'Slug':<60} {'Samples':<10} {'Hidden':<10} {'Status':<10}")
    print('-' * 90)
    for slug in sorted(bundle.keys()):
        cfg = bundle[slug]
        samples = len(cfg.get('samples') or [])
        hidden = len(cfg.get('hidden') or [])
        status = 'OK' if hidden >= MIN_HIDDEN else f'NEED {MIN_HIDDEN - hidden}'
        print(f"{slug:<60} {samples:<10} {hidden:<10} {status:<10}")
        if hidden < MIN_HIDDEN:
            insufficient.append((slug, samples, hidden))
    print()
    print(f"Total problems: {len(bundle)}")
    print(f"Problems with fewer than {MIN_HIDDEN} hidden cases: {len(insufficient)}")
    if insufficient:
        print("\nInsufficient problems:")
        for slug, samples, hidden in insufficient:
            print(f"  {slug}: samples={samples}, hidden={hidden}")


if __name__ == '__main__':
    main()
