#!/usr/bin/env python3
"""Build the self-contained atlas page (docs/index.html) from its template and its data.

    python atlas/build_atlas.py

The page has no server, no database and no external data: the aggregates are embedded in the HTML.
Only two web fonts and the map links of the cells are loaded from the network.
The output goes to docs/ so that GitHub Pages can serve it ("Deploy from a branch", folder /docs).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
template = (ROOT / "atlas" / "src" / "template.html").read_text(encoding="utf-8")
data = (ROOT / "atlas" / "src" / "data.json").read_text(encoding="utf-8")
assert template.count("/*DATA*/") == 1, "the template must contain exactly one /*DATA*/ marker"

HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
out = ROOT / "docs" / "index.html"
out.write_text(HEAD + template.replace("/*DATA*/", data), encoding="utf-8")
(ROOT / "docs" / ".nojekyll").touch()
print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")
