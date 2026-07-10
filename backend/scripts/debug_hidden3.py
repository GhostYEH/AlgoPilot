import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT / 'scripts'))

# Read the HIDDEN_SUPPLEMENT directly
from oj_test_data_hidden import HIDDEN_SUPPLEMENT

# Check valid-parentheses
if 'valid-parentheses' in HIDDEN_SUPPLEMENT:
    entries = HIDDEN_SUPPLEMENT['valid-parentheses']
    print(f"valid-parentheses has {len(entries)} entries in HIDDEN_SUPPLEMENT")
    for i, e in enumerate(entries):
        print(f"  [{i}]: {e}")
        if i == 7:  # Check the 8th entry (index 7)
            print(f"    args type: {type(e.get('args'))}, value: {repr(e.get('args'))}")
            print(f"    args[0] type: {type(e.get('args')[0]) if e.get('args') else None}, value: {repr(e.get('args')[0]) if e.get('args') else None}")
else:
    print("valid-parentheses NOT in HIDDEN_SUPPLEMENT")

# Check reverse-vowels-of-a-string
print()
if 'reverse-vowels-of-a-string' in HIDDEN_SUPPLEMENT:
    entries = HIDDEN_SUPPLEMENT['reverse-vowels-of-a-string']
    print(f"reverse-vowels-of-a-string has {len(entries)} entries in HIDDEN_SUPPLEMENT")
    for i, e in enumerate(entries):
        print(f"  [{i}]: {e}")
        if i == 9:  # Check the 10th entry
            print(f"    This is the problematic entry with stdin=None")
else:
    print("reverse-vowels-of-a-string NOT in HIDDEN_SUPPLEMENT")

# Check longest-happy-prefix
print()
if 'longest-happy-prefix' in HIDDEN_SUPPLEMENT:
    entries = HIDDEN_SUPPLEMENT['longest-happy-prefix']
    print(f"longest-happy-prefix has {len(entries)} entries in HIDDEN_SUPPLEMENT")
    for i, e in enumerate(entries):
        print(f"  [{i}]: {e}")
else:
    print("longest-happy-prefix NOT in HIDDEN_SUPPLEMENT")
