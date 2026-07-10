import json
from pathlib import Path

bundle = json.loads(Path('data/oj/tests_bundle.json').read_text(encoding='utf-8'))

# Check ransom-note specifically
slug = 'Ransom-Note'
if slug in bundle:
    cfg = bundle[slug]
    samples = cfg.get('samples') or []
    hidden = cfg.get('hidden') or []
    print(f"{slug}:")
    print(f"  samples: {len(samples)}")
    print(f"  hidden: {len(hidden)}")
    print(f"  total: {len(samples) + len(hidden)}")
else:
    print(f"{slug} not found in bundle")

# Also check for variations
for key in bundle.keys():
    if 'ransom' in key.lower():
        cfg = bundle[key]
        samples = cfg.get('samples') or []
        hidden = cfg.get('hidden') or []
        print(f"\nFound: {key}: samples={len(samples)}, hidden={len(hidden)}, total={len(samples) + len(hidden)}")
