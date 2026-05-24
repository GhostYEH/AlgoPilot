"""Inspect trace with user-style includes (iostream/string/stack)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from services.oj.cpp_trace_runner import run_trace_cpp_stdio

CODE = r"""
#include <iostream>
#include <string>
#include <stack>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    if (!(cin >> s)) return 0;
    stack<char> st;
    bool is_valid = true;
    for (char c : s) {
        if (c == '(') st.push(c);
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


def main() -> int:
    r = run_trace_cpp_stdio(
        CODE,
        case={"stdin": "()\n", "stdout": "true\n"},
        time_limit_ms=15000,
    )
    print("verdict:", r.verdict, "steps:", len(r.steps))
    for i, s in enumerate(r.steps):
        st = s.vars.get("st", {})
        c = s.vars.get("c", {})
        print(
            f"  [{i}] line={s.line} changed={s.changed} "
            f"st={st!r} c={c!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
