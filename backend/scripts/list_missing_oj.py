#!/usr/bin/env python3
import json
import re
from pathlib import Path

import sys

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))
catalog = json.loads((BACKEND / "data/oj/catalog.json").read_text(encoding="utf-8"))
bundle = set(json.loads((BACKEND / "data/oj/tests_bundle.json").read_text(encoding="utf-8")).keys())
from oj_test_data import TEST_DEFINITIONS  # noqa: E402

missing = [p for p in catalog if p["slug"] not in bundle and p["slug"] not in TEST_DEFINITIONS]
for p in missing:
    print(p["slug"], p.get("lc_id"), p.get("title"))
