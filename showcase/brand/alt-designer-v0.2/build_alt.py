#!/usr/bin/env python3
"""Fill a v0.2 "designer" template, resolve brand-alt.css tokens, render PNG.
Reuses only the render helpers of v0.1 (build_post.py: font_css, render_png); v0.1 files are not modified.
Library: build(template, fields, theme, out_svg)   CLI: python3 build_alt.py --previews previews
Needs NW_FONT_DIR (npm @fontsource) and Node playwright, see ../build_post.py.
"""
import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build_post as v01  # noqa: E402  (render helpers only)

CSS = (HERE / "brand-alt.css").read_text()
RAW = {"TRACE", "HERO_VALUE"}  # raw SVG allowed: TRACE, and HERO_VALUE (number + optional smaller unit via <tspan>)


def tokens(theme):
    def block(start):
        i = CSS.index(start)
        return CSS[CSS.index("{", i) + 1: CSS.index("}", i)]

    def parse(t):
        return dict(re.findall(r"--nw-([a-z-]+):\s*(#[0-9a-fA-F]{6})", t))

    tk = parse(block(":root {"))
    if theme == "dark":
        tk.update(parse(block(':root[data-theme="dark"]')))
    return tk


def build(template, fields, theme="light", out_svg=None):
    f = dict(fields)
    f.setdefault("ALT", " ".join(str(f.get(k, "")) for k in ("H1", "H2", "H3")).strip())
    for k in ("INTRO1", "INTRO2", "TRACE"):
        f.setdefault(k, "")
    for pre in ("AUX", "HERO"):  # one-line sub for portrait/square, three lines for LinkedIn
        subs = [f.get(f"{pre}_SUB{i}", "") for i in (1, 2, 3)]
        f.setdefault(f"{pre}_SUB", " · ".join(x for x in subs if x))
        for i, x in enumerate(subs, 1):
            f.setdefault(f"{pre}_SUB{i}", x)
    svg = (HERE / "templates" / f"{template}.svg").read_text()

    def sub(mo):
        k = mo.group(1)
        if k not in f:
            raise KeyError(f"missing placeholder {k}")
        return str(f[k]) if k in RAW else html.escape(str(f[k]), quote=True)

    svg = re.sub(r"\{\{([A-Z0-9_]+)\}\}", sub, svg)
    tk = tokens(theme)
    svg = re.sub(r"var\(--nw-([a-z-]+)\)", lambda mo: tk[mo.group(1)], svg)
    if out_svg:
        pathlib.Path(out_svg).write_text(svg)
    return svg


def trace_resistor(W, M, y, sw, fs, label):
    """Post 1 device: a trace from a pad at the left margin, one resistor zigzag (R9), running off the right edge."""
    x0, zx = M, int(W * 0.36)
    zig = f"M{x0 + 12},{y} H{zx}"
    zw = int(W * 0.09)
    pts = [(zx, y)]
    for i, d in enumerate((-1, 1, -1, 1, -1, 1)):
        pts.append((zx + zw * (i + 0.5) / 6, y + d * fs * 0.9))
    pts.append((zx + zw, y))
    zig += " L" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts[1:])
    zig += f" H{W + 10}"
    return (f'<circle cx="{x0 + 6}" cy="{y}" r="6" fill="none" stroke="var(--nw-accent)" stroke-width="{sw}"/>'
            f'<path d="{zig}" fill="none" stroke="var(--nw-accent)" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<text x="{zx}" y="{y + fs * 2.6:.0f}" font-family="\'JetBrains Mono\', monospace" font-size="{fs}" fill="var(--nw-muted)">{label}</text>')


def trace_lanes(W, M, ya, yb, sw, fs, label_a="A", label_b="B", wall="RLS"):
    """Post 2 device: lane A bends toward lane B and stops at the wall; lane B runs on, off the edge."""
    bx = int(W * 0.60)
    xa = bx - 40
    ax = (f'<text x="{M}" y="{ya + fs * 0.35:.1f}" font-family="\'JetBrains Mono\', monospace" font-weight="600" font-size="{fs}" fill="var(--nw-accent)">{label_a}</text>'
          f'<text x="{M}" y="{yb + fs * 0.35:.1f}" font-family="\'JetBrains Mono\', monospace" font-weight="600" font-size="{fs}" fill="var(--nw-ink)">{label_b}</text>')
    pa = f"M{M + fs * 2},{ya} H{int(W * 0.30)} L{int(W * 0.30) + (yb - ya) * 0.55:.0f},{ya + (yb - ya) * 0.55:.0f} H{xa}"
    ye = ya + (yb - ya) * 0.55
    cross = (f'<path d="M{xa + 8},{ye - 7:.0f} l14,14 M{xa + 22},{ye - 7:.0f} l-14,14" stroke="var(--nw-warn)" stroke-width="{sw}" stroke-linecap="round"/>')
    pb = f"M{M + fs * 2},{yb} H{W + 10}"
    wall_el = (f'<line x1="{bx}" y1="{ya - fs * 1.2:.0f}" x2="{bx}" y2="{yb + fs * 1.2:.0f}" stroke="var(--nw-ink)" stroke-width="1.5" stroke-dasharray="5 5"/>'
               f'<text x="{bx + 10}" y="{ya - fs * 0.5:.0f}" font-family="\'JetBrains Mono\', monospace" font-size="{fs * 0.85:.0f}" letter-spacing="1.2" fill="var(--nw-muted)">{wall}</text>')
    return (ax + f'<path d="{pa}" fill="none" stroke="var(--nw-accent)" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>'
            + cross + f'<path d="{pb}" fill="none" stroke="var(--nw-ink)" stroke-width="{sw}"/>' + wall_el)


SIZES = {"portrait-1080x1350": ("post-portrait-1080x1350", 1080, 72, 46, 3, 16),
         "linkedin-1200x627": ("post-linkedin-1200x627", 1200, 56, 22, 2.5, 12),
         "square-1080x1080": ("post-square-1080x1080", 1080, 72, 36, 3, 14)}

PLACEHOLDER = dict(
    KICKER="KICKER · SPRINT N", H1="One big statement", H2="in three short", H3="lines at most.",
    INTRO1="PLAIN LAYER: one benefit-first sentence,", INTRO2="no jargon, anyone can follow.",
    AUX_LABEL="BEFORE · LABEL", AUX_VALUE="0 000", AUX_SUB1="Secondary number,", AUX_SUB2="one plain line.",
    HERO_LABEL="AFTER · LABEL", HERO_VALUE="000", HERO_SUB1="The number that matters,", HERO_SUB2="set large in mono,", HERO_SUB3="with its meaning.",
    STATUS="STATUS · MEASURED OR ESTIMATED", SRC1="ENGINEER LAYER: formula / test / source", SRC2="What is still unmeasured or stubbed",
    HANDLE="@nilwerk · nilwerk.de", FOOT_NOTE="AI agents, led and reviewed by humans")

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--previews":
        out = pathlib.Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        jobs = []
        for suffix, (tpl, W, M, y, sw, fs) in SIZES.items():
            for theme in ("light", "dark"):
                f = dict(PLACEHOLDER, TRACE=trace_resistor(W, M, y, sw, fs, "R9 · placeholder trace"))
                svg = out / f"alt-{tpl}-{theme}.svg"
                build(tpl, f, theme, svg)
                jobs.append((svg, out / f"alt-{tpl}-{theme}.png"))
        v01.render_png(jobs)
    else:
        print(__doc__)
