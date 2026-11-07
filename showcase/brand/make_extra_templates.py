#!/usr/bin/env python3
"""Generate the extra v0.1-style templates (SVG with {{PLACEHOLDERS}}, colours as var(--nw-*) tokens):
  templates/story-1080x1920.svg, templates/carousel-1080x1350.svg      (Instagram story, LinkedIn/Instagram carousel slide)
  slides/templates/slide-*.svg                                         (16:9, 1920x1080)
Same look as the v0.1 post templates: warm paper + grid, line-art logo plate, kicker chip, tiles, status chip, FOR ENGINEERS block.
Run: python3 -I make_extra_templates.py   then   build_extra.py renders samples and previews.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
FD = "font-family=\"'Space Grotesk', Inter, sans-serif\""
FM = "font-family=\"'JetBrains Mono', monospace\""
FB = "font-family=\"Inter, sans-serif\""

LOGO = ('<g transform="translate({x} {y}) scale({s})">'
        '<rect x="1" y="1" width="30" height="30" rx="9" fill="#15181d" stroke="#ffffff" stroke-opacity=".12"/>'
        '<path d="M10 22V9.5l12 12.5V9.5" fill="none" stroke="#3fc79a" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>'
        '<circle cx="10" cy="22" r="2.6" fill="#15181d" stroke="#3fc79a" stroke-width="1.8"/>'
        '<circle cx="22" cy="9.5" r="2.6" fill="#15181d" stroke="#3fc79a" stroke-width="1.8"/>'
        '<path d="M6.5 26.6c2.4-1.5 4.8-1.5 7.2 0s4.8 1.5 7.2 0 4.8-1.5 6.9-.1" fill="none" stroke="#8fd9ff" stroke-opacity=".7" stroke-width="1.4" stroke-linecap="round"/></g>')


def head(W, H, grid=True, desc=""):
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{{{{ALT}}}}">\n'
    s += f'  <!-- Nilwerk v0.1 template: {desc}. Placeholders {{{{...}}}}; colours var(--nw-*) from brand.css / brand-status.css. -->\n'
    s += '  <defs><pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="var(--nw-line)" stroke-width="1.5" opacity=".55"/></pattern></defs>\n'
    s += f'  <rect width="{W}" height="{H}" fill="var(--nw-bg)"/>\n'
    if grid:
        s += f'  <rect width="{W}" height="{H}" fill="url(#grid)"/>\n'
    return s


def logo(x, y, scale, wm, wx, wy):
    return (LOGO.format(x=x, y=y, s=scale) + f'\n  <text x="{wx}" y="{wy}" {FD} font-weight="700" font-size="{wm}" letter-spacing="{-wm * 0.03:.1f}" fill="var(--nw-ink)">nil<tspan fill="var(--nw-accent)">werk</tspan></text>\n')


def kicker(x, y, h, fs, ph="KICKER", key="KICKER"):
    return (f'  <rect x="{x}" y="{y}" width="{{{{{key}_W}}}}" height="{h}" rx="{h / 2}" fill="var(--nw-accent-soft)" stroke="var(--nw-accent)" stroke-width="2"/>\n'
            f'  <text x="{x + h * 0.45:.0f}" y="{y + h * 0.66:.0f}" {FM} font-weight="600" font-size="{fs}" letter-spacing="{fs * 0.05:.1f}" fill="var(--nw-accent)">{{{{{key}}}}}</text>\n')


def chip(x, y, h, fs):
    return (f'  <rect x="{x}" y="{y}" width="{{{{STATUS_W}}}}" height="{h}" rx="8" fill="none" stroke="var(--nw-warn)" stroke-width="2"/>\n'
            f'  <text x="{x + h * 0.4:.0f}" y="{y + h * 0.68:.0f}" {FM} font-weight="600" font-size="{fs}" letter-spacing="{fs * 0.05:.1f}" fill="var(--nw-warn)">{{{{STATUS}}}}</text>\n')


def tile(x, y, w, h, tone, label, value, subs, lfs, vfs, sfs, pad=28):
    s = (f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>\n'
         f'  <rect x="{x}" y="{y}" width="{w}" height="10" rx="5" fill="{tone}"/>\n'
         f'  <text x="{x + pad}" y="{y + 60}" {FM} font-weight="600" font-size="{lfs}" letter-spacing="1" fill="{tone}">{{{{{label}}}}}</text>\n'
         f'  <text x="{x + pad}" y="{y + 60 + vfs * 1.0:.0f}" {FD} font-weight="700" font-size="{vfs}" letter-spacing="{-vfs * 0.03:.1f}" fill="var(--nw-ink)">{{{{{value}}}}}</text>\n')
    for i, k in enumerate(subs):
        s += f'  <text x="{x + pad}" y="{y + 60 + vfs * 1.0 + vfs * 0.18 + sfs * 1.9 * (i + 1):.0f}" {FB} font-size="{sfs}" fill="var(--nw-muted)">{{{{{k}}}}}</text>\n'
    return s


def eng(x, y, fs, gap, lines):
    s = f'  <text x="{x}" y="{y}" {FM} font-weight="600" font-size="{fs}" letter-spacing="1.5" fill="var(--nw-accent)">FOR ENGINEERS</text>\n  <g {FM} font-size="{fs}" fill="var(--nw-muted)">\n'
    for i, k in enumerate(lines):
        s += f'    <text x="{x}" y="{y + gap * (i + 1)}">{{{{{k}}}}}</text>\n'
    return s + '  </g>\n'


def story():
    W, H, M = 1080, 1920, 72
    s = head(W, H, desc="Instagram story 1080x1920, safe area y 250-1580")
    s += logo(M, 262, 2.0, 40, M + 76, 312)
    s += f'  <text x="{W - M}" y="310" text-anchor="end" {FM} font-size="22" fill="var(--nw-muted)">{{{{HANDLE}}}}</text>\n'
    s += kicker(M, 360, 50, 22)
    s += f'  <g {FD} font-weight="700" font-size="92" letter-spacing="-2.4">\n    <text x="{M}" y="530" fill="var(--nw-ink)">{{{{H1}}}}</text>\n    <text x="{M}" y="626" fill="var(--nw-ink)">{{{{H2}}}}</text>\n    <text x="{M}" y="722" fill="var(--nw-accent)">{{{{H3}}}}</text>\n  </g>\n'
    s += f'  <g {FB} font-size="34" fill="var(--nw-muted)"><text x="{M}" y="792">{{{{INTRO1}}}}</text><text x="{M}" y="836">{{{{INTRO2}}}}</text></g>\n'
    s += tile(M, 880, 936, 250, "{{TONE_A}}", "TILE_A_LABEL", "TILE_A_VALUE", ["TILE_A_SUB1", "TILE_A_SUB2"], 22, 70, 24)
    s += tile(M, 1146, 936, 250, "{{TONE_B}}", "TILE_B_LABEL", "TILE_B_VALUE", ["TILE_B_SUB1", "TILE_B_SUB2"], 22, 70, 24)
    s += chip(M, 1416, 48, 21)
    s += eng(M, 1500, 20, 28, ["SRC1", "SRC2"])
    s += '</svg>\n'
    return s


def carousel():
    W, H, M = 1080, 1350, 72
    s = head(W, H, desc="carousel slide 1080x1350 (LinkedIn document / Instagram carousel)")
    s += logo(M, 56, 1.75, 36, M + 66, 98)
    s += f'  <text x="{W - M}" y="96" text-anchor="end" {FM} font-weight="600" font-size="26" fill="var(--nw-muted)">{{{{N}}}} / {{{{TOTAL}}}}</text>\n'
    s += kicker(M, 160, 48, 21)
    s += f'  <g {FD} font-weight="700" font-size="84" letter-spacing="-2.2">\n    <text x="{M}" y="330" fill="var(--nw-ink)">{{{{H1}}}}</text>\n    <text x="{M}" y="424" fill="var(--nw-accent)">{{{{H2}}}}</text>\n  </g>\n'
    s += f'  <g {FB} font-size="38" fill="var(--nw-ink)">\n'
    for i in range(4):
        s += f'    <text x="{M}" y="{520 + 58 * i}">{{{{P{i + 1}}}}}</text>\n'
    s += '  </g>\n'
    s += f'  <rect x="{M}" y="800" width="936" height="330" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>\n'
    s += f'  <rect x="{M}" y="800" width="10" height="330" rx="5" fill="var(--nw-accent)"/>\n'
    s += eng(M + 40, 856, 23, 40, ["E1", "E2", "E3", "E4"])
    s += chip(M, 1160, 48, 21)
    s += f'  <g {FM} font-size="21" fill="var(--nw-muted)"><text x="{M}" y="1260">{{{{SRC1}}}}</text><text x="{W - M}" y="1260" text-anchor="end">{{{{SWIPE}}}}</text></g>\n'
    s += f'  <line x1="{M}" y1="1282" x2="{W - M}" y2="1282" stroke="var(--nw-line)" stroke-width="2"/>\n'
    s += f'  <g {FM} font-size="21" fill="var(--nw-muted)"><text x="{M}" y="1318">{{{{HANDLE}}}}</text><text x="{W - M}" y="1318" text-anchor="end">{{{{FOOT_NOTE}}}}</text></g>\n'
    s += '</svg>\n'
    return s


def slide_frame(desc, page=True):
    W, H, M = 1920, 1080, 120
    s = head(W, H, desc="slide 16:9 1920x1080: " + desc)
    s += logo(M, 56, 1.9, 40, M + 70, 100)
    s += f'  <line x1="{M}" y1="1004" x2="{W - M}" y2="1004" stroke="var(--nw-line)" stroke-width="2"/>\n'
    s += f'  <g {FM} font-size="22" fill="var(--nw-muted)"><text x="{M}" y="1044">{{{{FOOT_L}}}}</text><text x="{W - M}" y="1044" text-anchor="end">{{{{FOOT_R}}}}</text></g>\n'
    return s, W, H, M


def slides():
    out = {}
    s, W, H, M = slide_frame("title")
    s += kicker(M, 220, 56, 26)
    s += f'  <g {FD} font-weight="700" font-size="150" letter-spacing="-4">\n    <text x="{M}" y="470" fill="var(--nw-ink)">{{{{H1}}}}</text>\n    <text x="{M}" y="620" fill="var(--nw-ink)">{{{{H2}}}}</text>\n    <text x="{M}" y="770" fill="var(--nw-accent)">{{{{H3}}}}</text>\n  </g>\n'
    s += f'  <g {FB} font-size="42" fill="var(--nw-muted)"><text x="{M}" y="860">{{{{SUB1}}}}</text><text x="{M}" y="914">{{{{SUB2}}}}</text></g>\n'
    out["slide-1-title"] = s + '</svg>\n'

    s, W, H, M = slide_frame("section")
    s += f'  <text x="{M - 10}" y="640" {FM} font-weight="600" font-size="380" letter-spacing="-12" fill="var(--nw-accent)">{{{{NUM}}}}</text>\n'
    s += f'  <g {FD} font-weight="700" font-size="104" letter-spacing="-2.6" fill="var(--nw-ink)"><text x="740" y="330">{{{{H1}}}}</text><text x="740" y="450">{{{{H2}}}}</text></g>\n'
    s += f'  <g {FB} font-size="40" fill="var(--nw-muted)"><text x="740" y="570">{{{{PLAIN1}}}}</text><text x="740" y="624">{{{{PLAIN2}}}}</text></g>\n'
    s += f'  <line x1="740" y1="700" x2="{W - M}" y2="700" stroke="var(--nw-line)" stroke-width="2"/>\n'
    s += eng(740, 760, 26, 42, ["SRC1", "SRC2"])
    out["slide-2-section"] = s + '</svg>\n'

    s, W, H, M = slide_frame("key number")
    s += tile(M, 190, 860, 560, "{{TONE_B}}", "TILE_LABEL", "TILE_VALUE", ["TILE_SUB1", "TILE_SUB2", "TILE_SUB3"], 26, 220, 36, pad=40)
    s += f'  <g {FD} font-weight="700" font-size="76" letter-spacing="-2"><text x="1060" y="290" fill="var(--nw-ink)">{{{{H1}}}}</text><text x="1060" y="380" fill="var(--nw-ink)">{{{{H2}}}}</text><text x="1060" y="470" fill="var(--nw-accent)">{{{{H3}}}}</text></g>\n'
    s += f'  <g {FB} font-size="38" fill="var(--nw-muted)"><text x="1060" y="570">{{{{INTRO1}}}}</text><text x="1060" y="620">{{{{INTRO2}}}}</text></g>\n'
    s += chip(M, 800, 58, 26)
    s += eng(M, 900, 24, 38, ["SRC1", "SRC2"])
    out["slide-3-key-number"] = s + '</svg>\n'

    s, W, H, M = slide_frame("two columns: plain words / for engineers")
    s += f'  <text x="{M}" y="260" {FD} font-weight="700" font-size="84" letter-spacing="-2.2" fill="var(--nw-ink)">{{{{H1}}}}</text>\n'
    s += f'  <text x="{M}" y="360" {FM} font-weight="600" font-size="26" letter-spacing="1.5" fill="var(--nw-ink)">IN PLAIN WORDS</text>\n  <line x1="{M}" y1="380" x2="{M + 120}" y2="380" stroke="var(--nw-ink)" stroke-width="3"/>\n'
    s += f'  <g {FB} font-size="40" fill="var(--nw-ink)">\n'
    for i in range(4):
        s += f'    <text x="{M}" y="{450 + 78 * i}">{{{{L{i + 1}}}}}</text>\n'
    s += '  </g>\n'
    s += f'  <rect x="1000" y="320" width="800" height="560" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>\n  <rect x="1000" y="320" width="10" height="560" rx="5" fill="var(--nw-accent)"/>\n'
    s += eng(1048, 380, 26, 62, ["R1", "R2", "R3", "R4", "R5"])
    s += chip(M, 910, 58, 26)
    out["slide-4-two-column"] = s + '</svg>\n'

    s, W, H, M = slide_frame("architecture diagram frame")
    s += f'  <text x="{M}" y="230" {FD} font-weight="700" font-size="72" letter-spacing="-2" fill="var(--nw-ink)">{{{{H1}}}}</text>\n'
    s += f'  <rect x="{M}" y="270" width="1680" height="540" rx="18" fill="var(--nw-surface)" stroke="var(--nw-ink)" stroke-width="2" stroke-dasharray="10 8"/>\n'
    s += f'  <text x="960" y="550" text-anchor="middle" {FM} font-size="28" fill="var(--nw-muted)">{{{{FRAME_HINT}}}}</text>\n'
    s += f'  <g {FB} font-size="34" fill="var(--nw-ink)"><text x="{M}" y="880">{{{{PLAIN1}}}}</text><text x="{M}" y="926">{{{{PLAIN2}}}}</text></g>\n'
    s += f'  <text x="1100" y="868" {FM} font-weight="600" font-size="22" letter-spacing="1.5" fill="var(--nw-accent)">FOR ENGINEERS</text>\n'
    s += f'  <g {FM} font-size="22" fill="var(--nw-muted)"><text x="1100" y="906">{{{{SRC1}}}}</text><text x="1100" y="940">{{{{SRC2}}}}</text></g>\n'
    s += chip(M, 944, 44, 20)
    out["slide-5-architecture"] = s + '</svg>\n'

    s, W, H, M = slide_frame("closing / contact")
    s += f'  <g {FD} font-weight="700" font-size="170" letter-spacing="-5"><text x="{M}" y="470" fill="var(--nw-ink)">{{{{H1}}}}</text><text x="{M}" y="640" fill="var(--nw-accent)">{{{{H2}}}}</text></g>\n'
    s += f'  <g {FB} font-size="42" fill="var(--nw-muted)"><text x="{M}" y="740">{{{{SUB1}}}}</text><text x="{M}" y="794">{{{{SUB2}}}}</text></g>\n'
    s += f'  <g {FM} font-size="34" fill="var(--nw-ink)">\n'
    for i, (lab, key) in enumerate((("WEB", "C1"), ("INSTAGRAM", "C2"), ("LINKEDIN", "C3"), ("EMAIL", "C4"))):
        y = 300 + 80 * i
        s += f'    <text x="1180" y="{y}" fill="var(--nw-accent)" font-weight="600" font-size="24" letter-spacing="1.5">{lab}</text><text x="1420" y="{y}">{{{{{key}}}}}</text>\n'
    s += '  </g>\n'
    s += f'  <line x1="1180" y1="640" x2="{W - M}" y2="640" stroke="var(--nw-line)" stroke-width="2"/>\n  <text x="1180" y="690" {FM} font-size="24" fill="var(--nw-muted)">{{{{FOOT_NOTE}}}}</text>\n'
    out["slide-6-closing"] = s + '</svg>\n'
    return out


if __name__ == "__main__":
    (HERE / "templates").mkdir(exist_ok=True)
    (HERE / "slides" / "templates").mkdir(parents=True, exist_ok=True)
    (HERE / "templates" / "story-1080x1920.svg").write_text(story())
    (HERE / "templates" / "carousel-1080x1350.svg").write_text(carousel())
    for k, v in slides().items():
        (HERE / "slides" / "templates" / f"{k}.svg").write_text(v)
    print("templates written")
