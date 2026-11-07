#!/usr/bin/env python3
"""WCAG 2.x contrast check for the status tokens in brand-status.css against brand.css (v0.1 palette).
Usage: python3 -I check_status_contrast.py  -> exit 1 if a required text pair is below AA (4.5:1).
Each status colour is checked as text on bg, on surface and on its own soft background (badge), light and dark;
danger is also checked as a solid button (danger-ink on danger). Non-text parts (borders, icons) need 3:1.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
BASE = (HERE / "brand.css").read_text()
STAT = (HERE / "brand-status.css").read_text()


def block(css, start):
    i = css.index(start)
    return css[css.index("{", i) + 1 : css.index("}", i)]


def tok(t):
    return dict(re.findall(r"--nw-([a-z-]+):\s*(#[0-9a-fA-F]{6})", t))


LIGHT = {**tok(block(BASE, ":root {")), **tok(block(STAT, ":root {"))}
DARK = {**LIGHT, **tok(block(BASE, ':root[data-theme="dark"]')), **tok(block(STAT, ':root[data-theme="dark"]'))}


def lum(h):
    c = [int(h[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


STATUSES = ["ok", "dry", "wet", "low", "offline", "danger"]
failed = False
for name, tk in (("LIGHT", LIGHT), ("DARK", DARK)):
    print(name)
    pairs = []
    for s in STATUSES:
        pairs += [(s, "bg", 4.5), (s, "surface", 4.5), (s, f"{s}-soft", 4.5)]
    pairs += [("ink", "danger-soft", 4.5), ("ink", "ok-soft", 4.5), ("danger-ink", "danger", 4.5),
              ("accent-ink", "accent", 4.5), ("muted", "offline-soft", 4.5)]
    for fg, bg, need in pairs:
        r = ratio(tk[fg], tk[bg])
        ok = r >= need
        failed |= not ok
        print(f"  {fg:<11} {tk[fg]} on {bg:<12} {tk[bg]}  {r:5.2f}:1  need {need}  {'AA ok' if ok else 'FAIL'}")
sys.exit(1 if failed else 0)
