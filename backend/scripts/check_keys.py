"""检查并修复 HIDDEN_SUPPLEMENT 中的键名问题"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from oj_test_data_hidden import HIDDEN_SUPPLEMENT
import json

# 读取 catalog 获知正确的 slug (它是列表)
bundle = json.loads((Path(__file__).parent.parent / 'data/oj/catalog.json').read_text(encoding='utf-8'))
valid_slugs = set(item['slug'] for item in bundle)

print(f"Valid slugs count: {len(valid_slugs)}")
print()

issues = []
for key in sorted(HIDDEN_SUPPLEMENT.keys()):
    if key not in valid_slugs:
        # 尝试找到匹配的slug（忽略大小写和连字符）
        key_lower = key.lower().replace('-', '').replace('_', '')
        match = None
        for valid in valid_slugs:
            valid_lower = valid.lower().replace('-', '').replace('_', '')
            if key_lower == valid_lower:
                match = valid
                break
        if match:
            issues.append((key, match))
            print(f"  {key} -> 应该改为 {match}")
        else:
            print(f"  {key} -> 未找到匹配！")
    else:
        print(f"  {key} -> 正确")

print()
print(f"问题数量: {len(issues)}")
