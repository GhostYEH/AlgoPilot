import json
b = json.load(open('data/oj/tests_bundle.json', encoding='utf-8'))
for slug in ['sudoku-solver', 'n-queens']:
    cfg = b[slug]
    print('===', slug, '===')
    sc = cfg.get('starter_code') or {}
    print('python starter:')
    print(sc.get('python', '')[:600])
    print()
    cases = cfg.get('samples') or []
    for i, c in enumerate(cases):
        print('samples[', i, ']:')
        print('  args=', json.dumps(c.get('args'), ensure_ascii=False)[:200])
        print('  stdin=', repr(c.get('stdin'))[:300])
        print('  stdout=', repr(c.get('stdout'))[:300])
    print()
