import json
b = json.load(open('data/oj/tests_bundle.json', encoding='utf-8'))
for slug in ['number-of-islands', 'course-schedule', 'rotting-oranges']:
    cfg = b[slug]
    print('===', slug, '===')
    print('order_insensitive:', cfg.get('order_insensitive'))
    print('judge_mode:', cfg.get('judge_mode'))
    print('entry:', cfg.get('entry'))
    sc = cfg.get('starter_code') or {}
    print('python starter:')
    print(sc.get('python', '')[:800])
    print()
    for label in ['samples', 'hidden']:
        cases = cfg.get(label) or []
        for i, c in enumerate(cases):
            print(' ', label, '[', i, ']:')
            print('    args=', json.dumps(c.get('args'), ensure_ascii=False)[:200])
            print('    expected=', json.dumps(c.get('expected'), ensure_ascii=False)[:200])
            print('    stdin=', repr(c.get('stdin'))[:200])
            print('    stdout=', repr(c.get('stdout'))[:200])
    print()
