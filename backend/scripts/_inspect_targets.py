import json
b = json.load(open('data/oj/tests_bundle.json', encoding='utf-8'))
for slug in ['n-queens', 'sudoku-solver', 'permutations', 'subsets', 'palindrome-partitioning', 'happy-number', 'permutations-ii', 'combinations', 'number-of-islands', 'course-schedule', 'rotting-oranges']:
    cfg = b[slug]
    print('===', slug, '===')
    print('order_insensitive:', cfg.get('order_insensitive'))
    for label in ['samples', 'hidden']:
        cases = cfg.get(label) or []
        for i, c in enumerate(cases):
            args = c.get('args')
            exp = c.get('expected')
            print(' ', label, '[', i, ']: args=', json.dumps(args, ensure_ascii=False)[:100], ' expected=', json.dumps(exp, ensure_ascii=False)[:150])
    print()
