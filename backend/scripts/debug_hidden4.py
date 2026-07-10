import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT / 'scripts'))

from oj_test_data_hidden import HIDDEN_SUPPLEMENT
from services.oj.stdio_io import ensure_stdio_fields

# Check longest-happy-prefix entry [1]
# According to the error: longest-happy-prefix: hidden[1] missing stdin/stdout
# But longest-happy-prefix entry [1] is: {'args': ['a'], 'expected': ''}

print("Testing longest-happy-prefix entries:")
entries = HIDDEN_SUPPLEMENT['longest-happy-prefix']
for i, e in enumerate(entries):
    result = ensure_stdio_fields(e)
    stdin = result.get('stdin')
    stdout = result.get('stdout')
    has_issue = stdin is None or stdout is None
    print(f"  [{i}]: args={e['args']}, expected={repr(e['expected'])}")
    print(f"       stdin={repr(stdin)}, stdout={repr(stdout)}")
    if has_issue:
        print(f"       *** ISSUE: stdin or stdout is None!")
    print()
