#!/usr/bin/env python3
"""Write the v0.2 logo options (logo/*.svg) and the comparison sheet (logo/logo-options-sheet.svg + .png).
The v0.1 logo (../logo/nilwerk-mark.svg) is shown for reference and is not modified.
Logo SVGs in logo/ have the wordmark outlined (paths), so no font is needed. Run with NW_FONT_DIR set.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build_post as v01  # noqa: E402

LOGO = HERE / "logo"
LOGO.mkdir(exist_ok=True)
FD = "font-family=\"'Space Grotesk', Inter, sans-serif\" font-weight=\"700\""
FM = "font-family=\"'JetBrains Mono', monospace\""
OLD = (HERE.parent / "logo" / "nilwerk-mark.svg").read_text()


# ---- outlined wordmark: text converted to paths with fontTools (no font needed to open the SVGs) ----
import os as _os
from fontTools.ttLib import TTFont  # run this script with a Python that has fontTools (e.g. python3.13)
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

_FONT = TTFont(_os.path.join(_os.environ["NW_FONT_DIR"], "space-grotesk", "files", "space-grotesk-latin-700-normal.woff"))
_GS, _CMAP, _UPM = _FONT.getGlyphSet(), _FONT.getBestCmap(), _FONT["head"].unitsPerEm


def word(text, x, y, size, ls, fill):
    """Return (<path .../>, end_x) for `text` set in Space Grotesk 700 at baseline y (no kerning table applied)."""
    sc = size / _UPM
    pen = SVGPathPen(_GS)
    cx = x
    for ch in text:
        g = _CMAP[ord(ch)]
        _GS[g].draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y)))
        cx += _GS[g].width * sc + ls
    return f'<path d="{pen.getCommands()}" fill="{fill}"/>', cx

INK, PAPER, ACC, ACC_D, PLATE = "#15181d", "#f6f4ef", "#0f7a5c", "#3fc79a", "#15181d"


def mark(x, y, s, stroke, pad, sw=2.4):
    """Option A mark: one trace-N path, one pad ring (grid 28 x 28)."""
    return (f'<g transform="translate({x} {y}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M6 25V8.5L19 25V12" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<circle cx="19" cy="9.2" r="2.7" stroke="{pad}" stroke-width="2"/></g>')


def lockup_a(ink, pad, werk=None):
    return mark(0, 0, 1.7, ink, pad) + word("nilwerk", 62, 39, 44, -2.4, ink)[0]


def lockup_b(ink, pad):
    """Wordmark only: dotless i with the pad ring as its dot."""
    return (word("n\u0131lwerk", 0, 39, 44, -2.4, ink)[0] +
            f'<circle cx="30.5" cy="8.4" r="4.1" fill="none" stroke="{pad}" stroke-width="2.6"/>')


def lockup_c(ink, pad):
    """Wordmark with a single trace running under it: one 45-degree step, ending in a pad."""
    return (word("nilwerk", 0, 36, 44, -2.4, ink)[0] +
            f'<path d="M0 50H70l6 -6h40" fill="none" stroke="{pad}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="122" cy="44" r="3.4" fill="none" stroke="{pad}" stroke-width="2.2"/>')


def svg(w, h, body, bg=None, label="nilwerk"):
    r = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">{r}{body}</svg>\n'


files = {
    "alt-a-lockup.svg": svg(220, 52, lockup_a(INK, ACC)),
    "alt-a-lockup-mono.svg": svg(220, 52, lockup_a(INK, INK)),
    "alt-a-lockup-reverse.svg": svg(220, 52, lockup_a(PAPER, ACC_D)),
    "alt-a-mark.svg": svg(56, 56, mark(0, 0, 2, INK, ACC)),
    "alt-a-mark-mono.svg": svg(56, 56, mark(0, 0, 2, INK, INK)),
    # avatar: plate is only for platforms that crop to a circle; mark centred with 24 % padding
    "alt-a-avatar.svg": svg(400, 400, mark(100, 100, 7.14, ACC_D, "#ecebe7", 2.4), bg=PLATE, label="nilwerk avatar"),
    # favicon: heavier stroke so it holds at 16 px
    "alt-a-favicon.svg": svg(32, 32, mark(3, 3, 0.93, ACC_D, "#ecebe7", 3.4), bg=PLATE, label="nilwerk favicon"),
    "alt-b-wordmark.svg": svg(190, 52, lockup_b(INK, ACC)),
    "alt-c-wordmark-trace.svg": svg(190, 56, lockup_c(INK, ACC)),
}
for n, s in files.items():
    (LOGO / n).write_text(s)

# ---- comparison sheet (2400 x 1500) ----
W, H = 2400, 1340
b = [f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
b.append(f'<text x="80" y="90" {FM} font-size="26" letter-spacing="2" fill="#5b616b">NILWERK LOGO OPTIONS · V0.2 ALTERNATIVE · FOR COMPARISON</text>')
b.append(f'<line x1="80" y1="120" x2="{W - 80}" y2="120" stroke="#c9c2b3" stroke-width="1.5"/>')
cols = [("v0.1 (current, kept)", 80), ("A · trace-N, one pad (recommended)", 560), ("B · wordmark, pad as i-dot", 1130), ("C · wordmark + trace line", 1660)]
for t, x in cols:
    b.append(f'<text x="{x}" y="176" {FM} font-size="22" font-weight="600" letter-spacing="1" fill="{ACC}">{t}</text>')
# row 1: light
b.append(f'<g transform="translate(80 230) scale(3)">{OLD.replace(chr(10), "").split("</svg>")[0].split(">", 1)[1]}</g>'.replace('viewBox', 'viewBox'))
b.append(f'<g transform="translate(560 232) scale(2.0)">{lockup_a(INK, ACC)}</g>')
b.append(f'<g transform="translate(1130 224) scale(2.3)">{lockup_b(INK, ACC)}</g>')
b.append(f'<g transform="translate(1660 220) scale(2.3)">{lockup_c(INK, ACC)}</g>')
# old wordmark text under old mark (v0.1 wordmark: nil + green werk)
b.append(f'<text x="200" y="330" {FD} font-size="50" letter-spacing="-1.5" fill="{INK}">nil<tspan fill="{ACC}">werk</tspan></text>')
# row 2: dark panels
for x, w in ((552, 520), (1106, 500), (1636, 560)):
    b.append(f'<rect x="{x}" y="450" width="{w}" height="190" fill="#101317"/>')
b.append(f'<g transform="translate(560 502) scale(2.0)">{lockup_a(PAPER, ACC_D)}</g>')
b.append(f'<g transform="translate(1130 494) scale(2.3)">{lockup_b("#ecebe7", ACC_D)}</g>')
b.append(f'<g transform="translate(1660 490) scale(2.3)">{lockup_c("#ecebe7", ACC_D)}</g>')
b.append(f'<rect x="56" y="450" width="470" height="190" fill="#101317"/>')
b.append(f'<g transform="translate(80 490) scale(3)">{OLD.replace(chr(10), "").split("</svg>")[0].split(">", 1)[1]}</g>')
b.append(f'<text x="200" y="590" {FD} font-size="50" letter-spacing="-1.5" fill="#ecebe7">nil<tspan fill="{ACC_D}">werk</tspan></text>')
# row 3: option A variants
b.append(f'<line x1="80" y1="690" x2="{W - 80}" y2="690" stroke="#c9c2b3" stroke-width="1.5"/>')
b.append(f'<text x="80" y="740" {FM} font-size="22" font-weight="600" letter-spacing="1" fill="{ACC}">OPTION A, VARIANTS</text>')
vx = 80
variants = [("lockup", lockup_a(INK, ACC), None, 2.2, 880), ("mono (one colour)", lockup_a(INK, INK), None, 2.2, 600),
            ("reverse on ink", lockup_a(PAPER, ACC_D), "#101317", 2.2, 600)]
x = 80
for label, body, bg, sc, wd in variants:
    if bg:
        b.append(f'<rect x="{x - 20}" y="790" width="{wd - 40}" height="150" fill="{bg}"/>')
    b.append(f'<g transform="translate({x} 810) scale({sc})">{body}</g>')
    b.append(f'<text x="{x}" y="970" {FM} font-size="18" fill="#5b616b">{label}</text>')
    x += 640 if label == "lockup" else 580
# avatar + favicon
b.append(f'<defs><clipPath id="c"><circle cx="2120" cy="860" r="90"/></clipPath></defs>')
b.append(f'<g clip-path="url(#c)"><rect x="2030" y="770" width="180" height="180" fill="{PLATE}"/>{mark(2030 + 45, 770 + 45, 3.2, ACC_D, "#ecebe7")}</g>')
b.append(f'<text x="2030" y="970" {FM} font-size="18" fill="#5b616b">avatar (circle crop)</text>')
# row 4: small sizes
b.append(f'<line x1="80" y1="1010" x2="{W - 80}" y2="1010" stroke="#c9c2b3" stroke-width="1.5"/>')
b.append(f'<text x="80" y="1060" {FM} font-size="22" font-weight="600" letter-spacing="1" fill="{ACC}">SMALL SIZES · FAVICON 64 / 32 / 16 PX · MARK 48 / 32 / 24 PX</text>')
fx = 80
for px in (64, 32, 16):
    sc = px / 32
    b.append(f'<g transform="translate({fx} 1100) scale({sc})"><rect width="32" height="32" fill="{PLATE}"/>{mark(3, 3, 0.93, ACC_D, "#ecebe7", 3.4)}</g>')
    fx += px + 40
fx = 400
for px in (48, 32, 24):
    sc = px / 28
    b.append(f'<g transform="translate({fx} 1100) scale({sc})">{mark(0, 0, 1, INK, ACC)}</g>')
    fx += px + 40
b.append(f'<text x="80" y="1230" {FM} font-size="18" fill="#5b616b">v0.1 for reference: dark plate, green N with two pads, light-blue wave, lowercase wordmark with green "werk".</text>')
b.append(f'<text x="80" y="1262" {FM} font-size="18" fill="#5b616b">v0.2 simplifications: no plate (except avatar/favicon), no wave, one stroke weight, one pad, accent used once, tighter wordmark tracking.</text>')
sheet = svg(W, H, "".join(b))
(LOGO / "logo-options-sheet.svg").write_text(sheet)
v01.render_png([(LOGO / "logo-options-sheet.svg", LOGO / "logo-options-sheet.png")], scale=1)
print("logos written")
