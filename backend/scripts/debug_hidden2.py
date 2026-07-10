import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(BACKEND_ROOT))

from services.oj.stdio_io import ensure_stdio_fields

# Test the specific problematic cases
test_cases = [
    # valid-parentheses
    {"args": ["(]"], "expected": False},
    {"args": ["(((())))"], "expected": True},
    {"args": ["()[]{}"], "expected": True},
    {"args": ["([{}])"], "expected": True},
    {"args": ["(("], "expected": False},
    {"args": ["){"], "expected": False},
    {"args": ["{[]}"], "expected": True},
    {"args": [""], "expected": True},  # This is hidden[8] - empty string
]

print("Testing ensure_stdio_fields with empty string:")
for i, tc in enumerate(test_cases):
    result = ensure_stdio_fields(tc)
    print(f"  case[{i}]: args={tc['args']}, expected={tc['expected']}")
    print(f"    result stdin={repr(result.get('stdin'))}, stdout={repr(result.get('stdout'))}")
    print()

# Test with actual empty string
print("\nDirect test of empty string:")
tc = {"args": [""], "expected": True}
result = ensure_stdio_fields(tc)
print(f"  args={tc['args']}, expected={tc['expected']}")
print(f"  stdin={repr(result.get('stdin'))}, stdout={repr(result.get('stdout'))}")
