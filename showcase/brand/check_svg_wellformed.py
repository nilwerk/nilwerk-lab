#!/usr/bin/env python3
"""Check that every SVG under showcase/brand (and showcase/content) is well-formed XML (equivalent of `xmllint --noout`).
Usage: python3 -I check_svg_wellformed.py   -> prints failures, exit 1 if any.
Templates keep {{PLACEHOLDERS}} in text and attributes only, which is still well-formed XML.
"""
import pathlib
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
n = 0
for base in (ROOT / "brand", ROOT / "content"):
    for p in sorted(base.rglob("*.svg")):
        n += 1
        try:
            ET.parse(p)
        except ET.ParseError as e:
            bad += 1
            print(f"NOT WELL-FORMED {p.relative_to(ROOT)}: {e}")
print(f"{n} SVG files checked, {bad} not well-formed")
sys.exit(1 if bad else 0)
