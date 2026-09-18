#!/usr/bin/env python3
"""Build only the independent Is This Really Legal dashboard."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data/dashboard.json").read_text())
serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
page = (ROOT / "src/dashboard.html").read_text()
for key, value in {
    "__CSS__": (ROOT / "src/dashboard.css").read_text(),
    "__JS__": (ROOT / "src/dashboard.js").read_text(),
    "__DATA__": serialized,
}.items():
    page = page.replace(key, value)
for name in ["index.html", "dashboard.html"]:
    (ROOT / name).write_text(page)
(ROOT / "artifact.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print(f"Built Is This Really Legal dashboard: {len(page):,} characters")
