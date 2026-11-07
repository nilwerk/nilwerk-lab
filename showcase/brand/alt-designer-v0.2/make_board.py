#!/usr/bin/env python3
"""Build comparison-board.png: v0.1 (current) next to v0.2 (designer alternative) for post 1 and post 2
at portrait and LinkedIn size, plus the logo options sheet. Reads existing PNGs only (nothing is modified).
Run after build_alt_images.py and make_logos.py, with NW_FONT_DIR set."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build_post as v01  # noqa: E402

C = HERE.parents[1] / "content" / "2026-11-07"
FD = "font-family=\"'Space Grotesk', Inter, sans-serif\""
FM = "font-family=\"'JetBrains Mono', monospace\""
W, H = 2400, 2560
b = [f'<rect width="{W}" height="{H}" fill="#f6f4ef"/>',
     f'<text x="100" y="78" {FD} font-weight="700" font-size="44" fill="#15181d">Nilwerk look: v0.1 (current) vs v0.2 (designer alternative)</text>',
     f'<text x="100" y="116" {FM} font-size="20" fill="#5b616b">Same texts, same caveats, same claim-check. Only layout, logo and use of colour differ. Arsany decides which one to adopt.</text>']


def img(path, x, y, w, h):
    return f'<image href="{pathlib.Path(path).as_uri()}" x="{x}" y="{y}" width="{w}" height="{h}"/><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#c9c2b3" stroke-width="1.5"/>'


cols = [100, 660, 1220, 1780]
heads = ["POST 1 · v0.1", "POST 1 · v0.2", "POST 2 · v0.1", "POST 2 · v0.2"]
p = [C / "images" / "post1-r9-review-catch-portrait-1080x1350.png", C / "alt" / "post1-r9-review-catch-portrait-1080x1350.png",
     C / "images" / "post2-rls-proof-portrait-1080x1350.png", C / "alt" / "post2-rls-proof-portrait-1080x1350.png"]
l = [C / "images" / "post1-r9-review-catch-linkedin-1200x627.png", C / "alt" / "post1-r9-review-catch-linkedin-1200x627.png",
     C / "images" / "post2-rls-proof-linkedin-1200x627.png", C / "alt" / "post2-rls-proof-linkedin-1200x627.png"]
for x, hd, pp, ll in zip(cols, heads, p, l):
    col = "#0f7a5c" if "v0.2" in hd else "#5b616b"
    b.append(f'<text x="{x}" y="176" {FM} font-weight="600" font-size="20" letter-spacing="1.4" fill="{col}">{hd} · INSTAGRAM 1080x1350</text>')
    b.append(img(pp, x, 196, 520, 650))
    b.append(f'<text x="{x}" y="900" {FM} font-weight="600" font-size="20" letter-spacing="1.4" fill="{col}">{hd} · LINKEDIN 1200x627</text>')
    b.append(img(ll, x, 920, 520, 272))
b.append(f'<line x1="100" y1="1250" x2="{W - 100}" y2="1250" stroke="#c9c2b3" stroke-width="1.5"/>')
b.append(img(HERE / "logo" / "logo-options-sheet.png", 100, 1290, 2200, 1229))
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + "".join(b) + "</svg>"
tmp = pathlib.Path(tempfile.mkdtemp()) / "board.svg"
tmp.write_text(svg)
v01.render_png([(tmp, HERE / "comparison-board.png")], scale=1)
