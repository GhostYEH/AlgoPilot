from __future__ import annotations

import shutil

import pytest

from services.oj.cpp_trace_runner import gdb_available, run_trace_cpp_stdio


pytestmark = pytest.mark.skipif(
    not shutil.which("g++") or not gdb_available(),
    reason="g++/gdb not installed",
)


CPP_STL_TRACE = r"""
#include <array>
#include <deque>
#include <forward_list>
#include <iostream>
#include <list>
#include <map>
#include <queue>
#include <set>
#include <stack>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using namespace std;
int main() {
    array<int, 3> arr{1, 2, 3};
    vector<int> vec{4, 5};
    deque<int> deq{6, 7};
    list<int> lst{8, 9};
    forward_list<int> flst{10, 11};
    stack<int> stk; stk.push(12); stk.push(13);
    queue<int> que; que.push(14); que.push(15);
    priority_queue<int> pq; pq.push(3); pq.push(7); pq.push(5);
    map<string, int> mp{{"a", 1}, {"b", 2}};
    multimap<string, int> mmp{{"a", 1}, {"a", 2}};
    set<int> st{1, 2};
    multiset<int> mst{1, 1, 2};
    unordered_map<string, int> ump{{"x", 9}, {"y", 8}};
    unordered_multimap<string, int> ummp{{"x", 9}, {"x", 8}};
    unordered_set<int> ust{4, 5};
    unordered_multiset<int> umst{4, 4, 5};
    vec.push_back(6);
    mp["c"] = 3;
    cout << vec.size() + mp.size() << "\n";
    return 0;
}
"""


def test_cpp_trace_serializes_standard_stl_container_families() -> None:
    summary = run_trace_cpp_stdio(
        CPP_STL_TRACE,
        case={"stdin": "", "stdout": "6\n"},
        time_limit_ms=30000,
    )

    assert summary.verdict == "OK", summary.message
    latest: dict[str, dict] = {}
    for step in summary.steps:
        latest.update(step.vars)

    expected_hints = {
        "arr": "array",
        "vec": "vector",
        "deq": "deque",
        "lst": "list",
        "flst": "forward_list",
        "stk": "stack",
        "que": "queue",
        "pq": "priority_queue",
        "mp": "map",
        "mmp": "multimap",
        "st": "set",
        "mst": "multiset",
        "ump": "unordered_map",
        "ummp": "unordered_multimap",
        "ust": "unordered_set",
        "umst": "unordered_multiset",
    }
    for name, hint in expected_hints.items():
        assert latest[name]["view_hint"] == hint
        assert latest[name]["value"], name

    assert latest["vec"]["value"] == [4, 5, 6]
    assert latest["stk"]["value"] == [12, 13]
    assert latest["que"]["value"] == [14, 15]
    assert latest["mp"]["value"][-1] == {"key": "c", "value": 3}
    assert [entry["key"] for entry in latest["mmp"]["value"]] == ["a", "a"]
