"""Smoke test executed by the frozen AlgoPilot executable."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

app_dir = Path(sys.executable).resolve().parent
db_path = app_dir / "data" / "alp_learning.db"
assert db_path.is_file(), db_path
with sqlite3.connect(db_path) as conn:
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    assert integrity == "ok", integrity
    assert not conn.execute("PRAGMA foreign_key_check").fetchall()
    counts = {
        table: conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        for table in ("users", "student_profiles", "generated_resources", "learning_event_logs", "oj_submissions")
    }

from services.oj.cpp_runner import _find_gpp, run_cases_cpp
from services.oj.cpp_trace_runner import _find_gdb, run_trace_cpp_stdio

gpp = _find_gpp()
gdb = _find_gdb()
assert gpp and Path(gpp).is_file(), gpp
assert gdb and Path(gdb).is_file(), gdb
assert str(app_dir / "mingw") in gpp, gpp
assert str(app_dir / "mingw") in gdb, gdb
cpp_result = run_cases_cpp(
    "class Solution { public: int twice(int x) { return x * 2; } };",
    entry={"class": "Solution", "method": "twice"},
    cases=[{"args": [21], "expected": 42}],
)
assert cpp_result.verdict == "AC", cpp_result
trace_result = run_trace_cpp_stdio(
    """#include <iostream>
using namespace std;
int main() {
    int x = 0;
    cin >> x;
    int y = x * 2;
    cout << y << endl;
    return 0;
}
""",
    case={"stdin": "21\n", "stdout": "42\n"},
)
assert trace_result.verdict == "OK", trace_result
assert trace_result.steps, trace_result
print(json.dumps({"database_integrity": integrity, "database_counts": counts, "gpp": gpp, "gdb": gdb, "cpp_verdict": cpp_result.verdict, "trace_verdict": trace_result.verdict, "trace_steps": len(trace_result.steps)}, ensure_ascii=False))
