#!/usr/bin/env python3
"""Re-render the 2026-11-07 posts with the v0.2 "designer" templates (alternative to ../images).
The TEXTS are read from ../build_images.py (single source, so the claim-check stays valid); only layout changes.
Run: NW_FONT_DIR=<node_modules/@fontsource> python3 -I build_alt_images.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ALT = HERE.parents[2] / "brand" / "alt-designer-v0.2"
sys.path.insert(0, str(ALT))
import build_alt as A  # noqa: E402

# read the post texts from the v0.1 script without running its rendering part
src = (HERE.parent / "build_images.py").read_text().split("jobs = []")[0]
src = src.replace("import build_post as bp  # noqa: E402", "").replace("sys.path.insert(0, str(HERE.parent.parent / \"brand\"))", "")
ns = {"pathlib": pathlib, "sys": sys, "__file__": str(HERE.parent / "build_images.py")}
exec(compile(src, "build_images.py", "exec"), ns)
POSTS = ns["POSTS"]


def to_alt(f):
    g = {k: f[k] for k in ("KICKER", "H1", "H2", "H3", "INTRO1", "INTRO2", "STATUS", "SRC1", "SRC2", "HANDLE", "FOOT_NOTE")}
    # tile A (secondary, left in v0.1) -> AUX; tile B (the proof) -> HERO
    for k in ("LABEL", "VALUE", "SUB1", "SUB2", "SUB3"):
        g[f"AUX_{k}"] = f[f"TILE_A_{k}"]
        g[f"HERO_{k}"] = f[f"TILE_B_{k}"]
    import html
    num, _, unit = f["TILE_B_VALUE"].partition(" ")
    g["HERO_VALUE"] = html.escape(num) + (f'<tspan font-size="0.36em" letter-spacing="0" dx="0.25em">{html.escape(unit)}</tspan>' if unit else "")
    return g


TRACES = {
    "post1-r9-review-catch": lambda W, M, y, sw, fs: A.trace_resistor(W, M, y, sw, fs, "R9 · 1.2 kOhm to 2.4 kOhm"),
    "post2-rls-proof": lambda W, M, y, sw, fs: A.trace_lanes(W, M, y - fs * 1.2, y + fs * 1.6, sw, fs),
}

jobs = []
for name, (theme, fields) in POSTS.items():
    for suffix, (tpl, W, M, y, sw, fs) in A.SIZES.items():
        f = to_alt(fields)
        f["TRACE"] = TRACES[name](W, M, y, sw, fs)
        svg = HERE / f"{name}-{suffix}.svg"
        A.build(tpl, f, theme, svg)
        jobs.append((svg, HERE / f"{name}-{suffix}.png"))
A.v01.render_png(jobs)
