"""深度检查 OJ 测试用例质量"""
import json
import sys
from pathlib import Path
from collections import Counter

BACKEND = Path(__file__).resolve().parent.parent
bundle = json.loads((BACKEND / 'data/oj/tests_bundle.json').read_text(encoding='utf-8'))
catalog = json.loads((BACKEND / 'data/oj/catalog.json').read_text(encoding='utf-8'))

issues = []

# 1. 检查每题测试用例数量 >= 10
print("=== 1. 测试用例数量检查 ===")
under_10 = []
for slug, cfg in bundle.items():
    samples = cfg.get('samples') or []
    hidden = cfg.get('hidden') or []
    total = len(samples) + len(hidden)
    if total < 10:
        under_10.append((slug, total, len(samples), len(hidden)))
if under_10:
    for slug, total, s, h in sorted(under_10, key=lambda x: x[1]):
        print(f"  不足10个: {slug}: total={total} (samples={s}, hidden={h})")
    issues.append(f"{len(under_10)} 道题不足10个用例")
else:
    print(f"  全部 {len(bundle)} 道题 >= 10 个用例")

# 2. 检查 stdin/stdout 是否为 None
print("\n=== 2. stdin/stdout 完整性检查 ===")
none_stdio = []
for slug, cfg in bundle.items():
    for label, cases in [("samples", cfg.get('samples') or []), ("hidden", cfg.get('hidden') or [])]:
        for i, c in enumerate(cases):
            if c.get('stdin') is None or c.get('stdout') is None:
                none_stdio.append(f"{slug}: {label}[{i}] stdin={c.get('stdin')} stdout={c.get('stdout')}")
if none_stdio:
    for n in none_stdio:
        print(f"  {n}")
    issues.append(f"{len(none_stdio)} 个用例 stdin/stdout 为 None")
else:
    print("  全部用例 stdin/stdout 完整")

# 3. 检查 catalog 中的题目是否都在 bundle 中
print("\n=== 3. catalog 与 bundle 一致性检查 ===")
catalog_slugs = set(item['slug'] for item in catalog)
bundle_slugs = set(bundle.keys())
missing_in_bundle = catalog_slugs - bundle_slugs
extra_in_bundle = bundle_slugs - catalog_slugs
if missing_in_bundle:
    print(f"  catalog 中有但 bundle 中没有: {missing_in_bundle}")
    issues.append(f"{len(missing_in_bundle)} 题在 bundle 中缺失")
if extra_in_bundle:
    print(f"  bundle 中有但 catalog 中没有: {extra_in_bundle}")
    issues.append(f"{len(extra_in_bundle)} 题在 catalog 中缺失")
if not missing_in_bundle and not extra_in_bundle:
    print(f"  catalog({len(catalog_slugs)}) 与 bundle({len(bundle_slugs)}) 完全一致")

# 4. 检查重复测试用例
print("\n=== 4. 重复测试用例检查 ===")
dup_count = 0
for slug, cfg in bundle.items():
    all_cases = (cfg.get('samples') or []) + (cfg.get('hidden') or [])
    stdin_list = [c.get('stdin') for c in all_cases]
    seen = set()
    for s in stdin_list:
        if s in seen:
            print(f"  {slug}: 重复 stdin = {repr(s[:50] if s else s)}...")
            dup_count += 1
            break
        seen.add(s)
if dup_count == 0:
    print("  无重复测试用例")

# 5. 检查空 stdin/stdout（空字符串是合法的，但需要确认）
print("\n=== 5. 空 stdin/stdout 检查 ===")
empty_count = 0
for slug, cfg in bundle.items():
    for label, cases in [("samples", cfg.get('samples') or []), ("hidden", cfg.get('hidden') or [])]:
        for i, c in enumerate(cases):
            if c.get('stdin') == '' or c.get('stdout') == '':
                empty_count += 1
                if empty_count <= 5:
                    print(f"  {slug}: {label}[{i}] stdin={repr(c.get('stdin'))} stdout={repr(c.get('stdout'))}")
if empty_count > 5:
    print(f"  ... 共 {empty_count} 个空 stdin/stdout 用例")
elif empty_count == 0:
    print("  无空 stdin/stdout 用例")

# 6. 检查 samples 和 hidden 比例
print("\n=== 6. samples/hidden 比例统计 ===")
total_problems = len(bundle)
total_samples = sum(len(cfg.get('samples') or []) for cfg in bundle.values())
total_hidden = sum(len(cfg.get('hidden') or []) for cfg in bundle.values())
print(f"  总题目数: {total_problems}")
print(f"  总 samples: {total_samples} (avg {total_samples/total_problems:.1f})")
print(f"  总 hidden: {total_hidden} (avg {total_hidden/total_problems:.1f})")
print(f"  总用例数: {total_samples + total_hidden} (avg {(total_samples+total_hidden)/total_problems:.1f})")

# 7. 检查 HIDDEN_SUPPLEMENT 中的键名是否与 catalog 匹配
print("\n=== 7. HIDDEN_SUPPLEMENT 键名检查 ===")
sys.path.insert(0, str(BACKEND / 'scripts'))
from oj_test_data_hidden import HIDDEN_SUPPLEMENT
bad_keys = []
for key in HIDDEN_SUPPLEMENT:
    if key not in catalog_slugs:
        bad_keys.append(key)
if bad_keys:
    print(f"  以下键名不在 catalog 中: {bad_keys}")
    issues.append(f"HIDDEN_SUPPLEMENT 有 {len(bad_keys)} 个无效键名")
else:
    print(f"  HIDDEN_SUPPLEMENT({len(HIDDEN_SUPPLEMENT)}) 全部键名有效")

# 8. 检查 frontend bundle 是否与 backend bundle 一致
print("\n=== 8. 前后端 bundle 一致性检查 ===")
fe_bundle = json.loads((BACKEND.parent / 'frontend/public/oj/bundle.json').read_text(encoding='utf-8'))
be_bundle = bundle
if set(fe_bundle.keys()) == set(be_bundle.keys()):
    print(f"  前后端 bundle 题目数一致: {len(fe_bundle)}")
else:
    diff = set(fe_bundle.keys()) ^ set(be_bundle.keys())
    print(f"  前后端 bundle 不一致: {diff}")
    issues.append("前后端 bundle 不一致")

# 总结
print("\n" + "=" * 50)
if issues:
    print(f"发现 {len(issues)} 个问题:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
else:
    print("全部检查通过，无问题！")
