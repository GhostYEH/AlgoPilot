"""OJ 判题 + 可视化调试端到端自检（Python / C++）。"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

BASE = "http://127.0.0.1:9000"

TWO_SUM_PY = """
import sys

def main():
    lines = sys.stdin.read().strip().splitlines()
    n = int(lines[0])
    nums = list(map(int, lines[1].split()))
    target = int(lines[2])
    seen = {}
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            print(seen[need], i)
            return
        seen[x] = i

if __name__ == '__main__':
    main()
""".strip()

TWO_SUM_CPP = r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, target;
    cin >> n;
    vector<int> nums(n);
    for (int i = 0; i < n; ++i) cin >> nums[i];
    cin >> target;
    unordered_map<int, int> seen;
    for (int i = 0; i < n; ++i) {
        int need = target - nums[i];
        if (seen.count(need)) {
            cout << seen[need] << " " << i << "\n";
            return 0;
        }
        seen[nums[i]] = i;
    }
    return 0;
}
""".strip()

MIN_SUB_PY = """
import sys

def main():
    lines = sys.stdin.read().strip().splitlines()
    target = int(lines[0])
    n = int(lines[1])
    nums = list(map(int, lines[2].split()))
    left = 0
    total = 0
    best = 10**9
    for right, x in enumerate(nums):
        total += x
        while total >= target:
            best = min(best, right - left + 1)
            total -= nums[left]
            left += 1
    print(0 if best == 10**9 else best)

if __name__ == '__main__':
    main()
""".strip()

MIN_SUB_CPP = r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int target, n;
    cin >> target >> n;
    vector<int> nums(n);
    for (int i = 0; i < n; ++i) cin >> nums[i];
    int left = 0, total = 0, best = 1e9;
    for (int right = 0; right < n; ++right) {
        total += nums[right];
        while (total >= target) {
            best = min(best, right - left + 1);
            total -= nums[left++];
        }
    }
    cout << (best == (int)1e9 ? 0 : best) << "\n";
    return 0;
}
""".strip()


def post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as resp:
        return json.loads(resp.read())


def check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "OK" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    fails = 0

    try:
        caps = get("/api/oj/capabilities")
    except urllib.error.URLError as e:
        print(f"后端未启动: {e}")
        return 1

    fails += not check("capabilities", caps.get("trace_cpp") is True, str(caps))

    cases = [
        ("two-sum", "python", TWO_SUM_PY, "run"),
        ("two-sum", "cpp", TWO_SUM_CPP, "run"),
        ("minimum-size-subarray-sum", "python", MIN_SUB_PY, "run"),
        ("minimum-size-subarray-sum", "cpp", MIN_SUB_CPP, "run"),
    ]

    for slug, lang, code, mode in cases:
        path = f"/api/oj/problems/{slug}/{mode}"
        try:
            res = post(path, {"code": code, "language": lang})
            ok = res.get("verdict") == "AC"
            fails += not check(f"{mode} {slug} {lang}", ok, f"verdict={res.get('verdict')}")
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            fails += not check(f"{mode} {slug} {lang}", False, f"HTTP {e.code} {body[:120]}")

    # submit 需登录，用服务层测 hidden 用例
    try:
        from services.oj.stdio_runner import run_cases_stdio as _run
        from services.oj.problem_store import get_cases as _get_cases

        for slug, lang, code in [("two-sum", "python", TWO_SUM_PY), ("two-sum", "cpp", TWO_SUM_CPP)]:
            s = _run(code, cases=_get_cases(slug, mode="submit"), language=lang, order_insensitive=True)
            ok = s.verdict == "AC"
            fails += not check(f"submit(service) {slug} {lang}", ok, f"verdict={s.verdict} {s.passed}/{s.total}")
    except Exception as e:
        fails += not check("submit(service)", False, str(e))

    trace_cases = [
        ("two-sum", "python", TWO_SUM_PY),
        ("two-sum", "cpp", TWO_SUM_CPP),
        ("minimum-size-subarray-sum", "python", MIN_SUB_PY),
        ("minimum-size-subarray-sum", "cpp", MIN_SUB_CPP),
    ]

    for slug, lang, code in trace_cases:
        try:
            res = post(f"/api/oj/problems/{slug}/trace", {"code": code, "language": lang})
            steps = len(res.get("steps") or [])
            ok = res.get("verdict") == "OK" and steps >= 8
            fails += not check(f"trace {slug} {lang}", ok, f"verdict={res.get('verdict')} steps={steps}")
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            fails += not check(f"trace {slug} {lang}", False, f"HTTP {e.code} {body[:120]}")

    print(f"\n合计失败: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
