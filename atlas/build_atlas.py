#!/usr/bin/env python3
"""Build the self-contained atlas page (atlas/index.html) from its template and its data.

    python atlas/build_atlas.py

The page has no server, no database and no external data: the aggregates are embedded in the HTML.
Only two web fonts and the map links of the cells are loaded from the network.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
template = (HERE / "src" / "template.html").read_text(encoding="utf-8")
data = (HERE / "src" / "data.json").read_text(encoding="utf-8")
assert template.count("/*DATA*/") == 1, "the template must contain exactly one /*DATA*/ marker"
out = HERE / "index.html"
out.write_text(template.replace("/*DATA*/", data), encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")
