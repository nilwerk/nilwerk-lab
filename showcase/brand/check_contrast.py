#!/usr/bin/env python3
"""WCAG 2.x contrast check for the Nilwerk brand palette (PROPOSAL v0.1).

Usage: python3 check_contrast.py            -> prints the table, exit 1 if a required pair fails AA
Tokens are read from brand.css (the two token blocks), so the table cannot drift from the CSS.
AA thresholds: 4.5 for normal text, 3.0 for large text (>= 24 px, or >= 18.66 px bold) and UI components.
"""
import pathlib
import re
import sys

CSS = pathlib.Path(__file__).with_name("brand.css").read_text()


def block(selector_start):
    i = CSS.index(selector_start)
    return CSS[CSS.index("{", i) + 1 : CSS.index("}", i)]


def tokens(text):
    return dict(re.findall(r"--nw-([a-z-]+):\s*(#[0-9a-fA-F]{6})", text))


LIGHT = tokens(block(":root {"))
DARK = {**LIGHT, **tokens(block(':root[data-theme="dark"]'))}


def lum(hexv):
    c = [int(hexv[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# (foreground, background, minimum, what)
PAIRS = [
    ("ink", "bg", 4.5, "body text on page"),
    ("ink", "surface", 4.5, "body text on card"),
    ("muted", "bg", 4.5, "secondary text on page"),
    ("muted", "surface", 4.5, "secondary text on card"),
    ("accent", "bg", 4.5, "accent text / links on page"),
    ("accent", "surface", 4.5, "accent text on card"),
    ("accent-ink", "accent", 4.5, "text on accent button"),
    ("accent", "accent-soft", 4.5, "accent text on soft chip"),
    ("ink", "accent-soft", 4.5, "body text on soft chip"),
    ("warn", "bg", 4.5, "warning text on page"),
    ("warn", "surface", 4.5, "warning text on card"),
    ("signal", "bg", 3.0, "decorative wave only (not text)"),
    ("line", "bg", 1.0, "hairline, decorative (no requirement)"),
]

failed = False
for name, tk in (("LIGHT", LIGHT), ("DARK", DARK)):
    print(f"\n{name}")
    for fg, bg, need, what in PAIRS:
        r = ratio(tk[fg], tk[bg])
        ok = r >= need
        decorative = fg in ("signal", "line")
        if not ok and not decorative:
            failed = True
        verdict = "n/a (decorative)" if decorative else ("AA ok" if ok else "FAIL")
        print(f"  {fg:<10} {tk[fg]} on {bg:<11} {tk[bg]}  {r:5.2f}:1  need {need}  {verdict}  ({what})")
sys.exit(1 if failed else 0)
