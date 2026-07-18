"""Write a deterministic inventory for validating a portable release."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1]).resolve()
db = root / "data" / "alp_learning.db"
with sqlite3.connect(db) as conn:
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise SystemExit(f"database integrity failed: {integrity}")
    foreign_key_violations = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    counts = {name: conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in tables}
manifest = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "platform": "Windows x64",
    "database": {
        "path": "data/alp_learning.db",
        "bytes": db.stat().st_size,
        "sha256": hashlib.sha256(db.read_bytes()).hexdigest(),
        "integrity": integrity,
        "foreign_key_violations": foreign_key_violations,
        "table_counts": counts,
    },
    "runtime": {
        "app_exe": (root / "AlgoPilot.exe").is_file(),
        "gpp": (root / "mingw" / "ucrt64" / "bin" / "g++.exe").is_file(),
        "gdb": (root / "mingw" / "ucrt64" / "bin" / "gdb.exe").is_file(),
        "frontend": (root / "_internal" / "frontend" / "index.html").is_file(),
    },
}
(root / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False))
