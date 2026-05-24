"""Inspect valid-parens trace steps for st/s snapshots."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from services.oj.cpp_trace_runner import run_trace_cpp_stdio

CODE = r"""
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
        sv = s.vars.get("s", {})
        st_val = st.get("value")
        s_val = sv.get("value")
        print(
            f"  [{i}] line={s.line} changed={s.changed} "
            f"st=({st.get('type')},{st.get('view_hint')},{st_val!r}) "
            f"s=({sv.get('type')},{s_val!r})"
        )
    has_push = any(
        isinstance(s.vars.get("st", {}).get("value"), list)
        and len(s.vars["st"]["value"]) > 0
        for s in r.steps
    )
    print("has_nonempty_stack:", has_push)
    return 0 if r.verdict == "OK" and has_push else 1


if __name__ == "__main__":
    raise SystemExit(main())
