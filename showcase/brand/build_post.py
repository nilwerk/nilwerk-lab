#!/usr/bin/env python3
"""Fill a Nilwerk post template (SVG with {{PLACEHOLDERS}}), resolve brand.css tokens, render PNG.

Library: build(template_name, fields, theme, out_svg) -> path
CLI:     python3 build_post.py --previews OUTDIR     (renders the 3 templates with placeholder text)

Rendering uses headless Chromium through Node playwright (NODE_PATH must contain playwright) and the
Google Fonts files from the npm package @fontsource/* (set NW_FONT_DIR to ".../node_modules/@fontsource").
Fonts are only embedded in the throw-away HTML used for rendering; the SVG keeps font names, so it opens
in Figma/Canva/Inkscape when Space Grotesk, Inter and JetBrains Mono are installed.
Everything here is code-generated: no AI image is involved, so no AI label is needed on these images.
"""
import base64
import html
import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CSS = (HERE / "brand.css").read_text()

# per-template chip metrics: (font size, letter spacing, horizontal padding) for kicker and status chips
METRICS = {
    "post-portrait-1080x1350": dict(k=(24, 1.2, 48), s=(22, 1.0, 40)),
    "post-linkedin-1200x627": dict(k=(17, 0.9, 36), s=(15, 0.8, 32)),
    "post-square-1080x1080": dict(k=(22, 1.1, 44), s=(21, 1.0, 40)),
}
# rough max characters per headline line (Space Grotesk bold), used for a warning only; always look at the render
HEADLINE_MAX = {"post-portrait-1080x1350": 19, "post-linkedin-1200x627": 21, "post-square-1080x1080": 22}

FONTS = [  # family, weight, fontsource package, file
    ("Space Grotesk", 500, "space-grotesk", "space-grotesk-latin-500-normal.woff2"),
    ("Space Grotesk", 700, "space-grotesk", "space-grotesk-latin-700-normal.woff2"),
    ("Inter", 400, "inter", "inter-latin-400-normal.woff2"),
    ("Inter", 600, "inter", "inter-latin-600-normal.woff2"),
    ("JetBrains Mono", 400, "jetbrains-mono", "jetbrains-mono-latin-400-normal.woff2"),
    ("JetBrains Mono", 600, "jetbrains-mono", "jetbrains-mono-latin-600-normal.woff2"),
]


def tokens(theme):
    def block(start):
        i = CSS.index(start)
        return CSS[CSS.index("{", i) + 1 : CSS.index("}", i)]

    def parse(t):
        return dict(re.findall(r"--nw-([a-z-]+):\s*(#[0-9a-fA-F]{6})", t))

    tk = parse(block(":root {"))
    if theme == "dark":
        tk.update(parse(block(':root[data-theme="dark"]')))
    return tk


def mono_w(text, fs, ls, pad):
    return round(len(text) * (0.6 * fs + ls) + pad)


def build(template, fields, theme="light", out_svg=None):
    f = dict(fields)
    f.setdefault("ALT", " ".join(str(f.get(k, "")) for k in ("H1", "H2", "H3")).strip())
    for k in ("INTRO1", "INTRO2", "TILE_A_SUB3", "TILE_B_SUB3", "SRC2"):
        f.setdefault(k, "")
    tk = tokens(theme)
    m = METRICS[template]
    f["KICKER_W"] = mono_w(f["KICKER"], *m["k"])
    f["STATUS_W"] = mono_w(f["STATUS"], *m["s"])
    f["TONE_A"] = f"var(--nw-{f.get('TONE_A_TOKEN', 'warn')})"
    f["TONE_B"] = f"var(--nw-{f.get('TONE_B_TOKEN', 'accent')})"
    for line in ("H1", "H2", "H3"):
        if len(f[line]) > HEADLINE_MAX[template]:
            print(f"WARNING {template}: {line} has {len(f[line])} chars (> {HEADLINE_MAX[template]}), check the render", file=sys.stderr)
    svg = (HERE / "templates" / f"{template}.svg").read_text()

    def sub(mo):
        key = mo.group(1)
        if key not in f:
            raise KeyError(f"missing placeholder {key}")
        v = str(f[key])
        return v if key.endswith("_W") or key.startswith("TONE_") else html.escape(v, quote=True)

    svg = re.sub(r"\{\{([A-Z0-9_]+)\}\}", sub, svg)
    svg = re.sub(r"var\(--nw-([a-z-]+)\)", lambda mo: tokens_lookup(tk, mo.group(1)), svg)
    if out_svg:
        pathlib.Path(out_svg).write_text(svg)
    return svg


def tokens_lookup(tk, name):
    return tk[name]


def font_css():
    base = pathlib.Path(os.environ.get("NW_FONT_DIR", ""))
    out = []
    for fam, w, pkg, fn in FONTS:
        p = base / pkg / "files" / fn
        data = base64.b64encode(p.read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "\n".join(out)


def render_png(svgs_and_pngs, scale=2):
    """svgs_and_pngs: list of (svg_path, png_path). One Chromium launch for all."""
    fcss = font_css()
    jobs = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="nwrender_"))
    for i, (svg_path, png_path) in enumerate(svgs_and_pngs):
        svg = pathlib.Path(svg_path).read_text()
        w, h = re.search(r'width="(\d+)" height="(\d+)"', svg).groups()
        page = tmp / f"p{i}.html"
        page.write_text(f"<!doctype html><meta charset=utf-8><style>{fcss}html,body{{margin:0;background:#fff}}svg{{display:block}}</style>{svg}")
        jobs.append(dict(html=str(page), png=str(png_path), w=int(w), h=int(h)))
    import json

    jf = tmp / "jobs.json"
    jf.write_text(json.dumps(dict(scale=scale, jobs=jobs)))
    env = dict(os.environ)
    env.setdefault("NODE_PATH", "/opt/node-tools/node_modules")
    subprocess.run(["node", str(HERE / "render.js"), str(jf)], check=True, env=env)


PLACEHOLDER_FIELDS = dict(
    KICKER="KICKER · SPRINT N",
    H1="Headline line one",
    H2="Headline line two",
    H3="Accent line three",
    INTRO1="PLAIN LAYER: one benefit-first sentence,",
    INTRO2="no jargon, anyone can follow.",
    TILE_A_LABEL="BEFORE · LABEL",
    TILE_A_VALUE="0 000",
    TILE_A_SUB1="What this number is,",
    TILE_A_SUB2="in one plain line.",
    TILE_B_LABEL="AFTER · LABEL",
    TILE_B_VALUE="0 000",
    TILE_B_SUB1="What this number is,",
    TILE_B_SUB2="in one plain line.",
    STATUS="STATUS · MEASURED OR ESTIMATED",
    SRC1="ENGINEER LAYER: formula / test / source",
    SRC2="What is still unmeasured or stubbed",
    HANDLE="@nilwerk · nilwerk.de",
    FOOT_NOTE="AI agents, led and reviewed by humans",
)

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--previews":
        out = pathlib.Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        jobs = []
        for tpl in METRICS:
            for theme in ("light", "dark"):
                s = out / f"{tpl}-{theme}.svg"
                build(tpl, PLACEHOLDER_FIELDS, theme, s)
                jobs.append((s, out / f"{tpl}-{theme}.png"))
        render_png(jobs)
    else:
        print(__doc__)
