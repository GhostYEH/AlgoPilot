"""Inspect trace step line numbers for branch-heavy code."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from services.oj.cpp_trace_runner import run_trace_cpp_stdio
from services.oj.trace_runner import run_trace_stdio

CPP = r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    if (!(cin >> s)) return 0;
    stack<char> st;
    bool is_valid = true;
    for (char c : s) {
        if (c == '(') st.push(')');
        else if (c == ')') {
            if (st.empty()) { is_valid = false; break; }
            st.pop();
        }
    }
    if (!st.empty()) is_valid = false;
    cout << (is_valid ? "true" : "false") << "\n";
    return 0;
}
""".strip()

PY = """
import sys
def main():
    s = sys.stdin.readline().strip()
    st = []
    is_valid = True
    for c in s:
        if c == '(':
            st.append(')')
        elif c == ')':
            if not st:
                is_valid = False
                break
            st.pop()
    if st:
        is_valid = False
    print('true' if is_valid else 'false')
if __name__ == '__main__':
    main()
""".strip()


def dump(code: str, lang: str) -> None:
    case = {"stdin": "()[]{}\n", "stdout": "true\n"}
    if lang == "cpp":
        r = run_trace_cpp_stdio(code, case=case, time_limit_ms=15000)
    else:
        r = run_trace_stdio(code, case=case, time_limit_ms=15000)
    lines = code.splitlines()
    print(f"\n=== {lang} verdict={r.verdict} steps={len(r.steps)} ===")
    for i, s in enumerate(r.steps):
        ln = s.line
        snippet = lines[ln - 1].strip() if 1 <= ln <= len(lines) else "?"
        print(f"  [{i:2d}] line={ln:2d} changed={s.changed!s:20s} | {snippet}")


if __name__ == "__main__":
    dump(CPP, "cpp")
    dump(PY, "python")
