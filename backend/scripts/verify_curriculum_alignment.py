"""校验课程 slug、public bundle、HTTP 题目详情一致性。"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from scripts.audit_oj_full import CATALOG_PATH, FRONTEND_BUNDLE, scan_curriculum_slugs  # noqa: E402

BASE = "http://127.0.0.1:9000"


def main() -> int:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    pub = json.loads(FRONTEND_BUNDLE.read_text(encoding="utf-8"))
    curriculum = scan_curriculum_slugs()

    cat_slugs = {p["slug"] for p in catalog}
    cur_slugs = set(curriculum.keys())
    pub_slugs = set(pub.keys())

    missing_in_cat = sorted(cur_slugs - cat_slugs)
    missing_in_pub = sorted(cat_slugs - pub_slugs)
    not_ready_pub = [s for s, v in pub.items() if not v.get("ready")]
    no_samples = [s for s, v in pub.items() if not (v.get("samples") or [])]

    http_fail: list[str] = []
    for slug in sorted(cat_slugs):
        try:
            with urllib.request.urlopen(
                f"{BASE}/api/oj/problems/{slug}",
                timeout=8,
            ) as resp:
                detail = json.loads(resp.read())
            if not detail.get("ready"):
                http_fail.append(f"{slug}: ready=false")
            if detail.get("judge_mode") != "stdio":
                http_fail.append(f"{slug}: judge_mode={detail.get('judge_mode')}")
            if not detail.get("samples"):
                http_fail.append(f"{slug}: no samples")
            sc = detail.get("starter_code") or {}
            if "def main" not in sc.get("python", ""):
                http_fail.append(f"{slug}: python starter missing main")
            if "int main" not in sc.get("cpp", ""):
                http_fail.append(f"{slug}: cpp starter missing main")
        except Exception as e:
            http_fail.append(f"{slug}: {e}")

    print("=== 课程 / 题库 / HTTP 对齐 ===")
    print(f"catalog:                  {len(cat_slugs)}")
    print(f"curriculum practice links: {len(cur_slugs)}")
    print(f"public bundle:            {len(pub_slugs)}")
    print(f"curriculum not in catalog:     {len(missing_in_cat)}")
    print(f"catalog not in public bundle:  {len(missing_in_pub)}")
    print(f"public ready=false:       {len(not_ready_pub)}")
    print(f"public no samples:        {len(no_samples)}")
    print(f"HTTP GET issues:          {len(http_fail)}")

    issues = missing_in_cat + missing_in_pub + not_ready_pub + no_samples + http_fail
    if missing_in_cat:
        print("curriculum missing in catalog:", missing_in_cat[:10])
    if missing_in_pub:
        print("catalog missing in public:", missing_in_pub[:10])
    if http_fail:
        for x in http_fail[:20]:
            print(" -", x)
    elif not issues:
        print("All GET /api/oj/problems/{slug} OK")

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
