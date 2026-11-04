#!/usr/bin/env python3
"""Build only the independent Is This Really Legal dashboard."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data/dashboard.json").read_text())
serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
assets = ROOT / "assets"
assets.mkdir(exist_ok=True)
css = (ROOT / "src/dashboard.css").read_text()
js = "const D=" + serialized + ";\n" + (ROOT / "src/dashboard.js").read_text()
for name, content in {"dashboard.css": css, "dashboard.js": js}.items():
    (assets / name).write_text(content)

def asset_url(name, content):
    version = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"assets/{name}?v={version}"

page = (ROOT / "src/dashboard.html").read_text()
page = page.replace("__STYLESHEET__", asset_url("dashboard.css", css))
page = page.replace("__SCRIPT__", asset_url("dashboard.js", js))
assert not any(token in page for token in ("__STYLESHEET__", "__SCRIPT__", "__CSS__", "__JS__", "__DATA__"))
for name in ["index.html", "dashboard.html"]:
    (ROOT / name).write_text(page)
(ROOT / "artifact.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print(f"Built Is This Really Legal dashboard: {len(page):,} characters")
