#!/usr/bin/env python3
"""Generate the three v0.2 "designer" SVG templates (templates/*.svg) from one layout table.
Placeholders: {{KICKER}} {{H1}} {{H2}} {{H3}} {{INTRO1}} {{INTRO2}} {{TRACE}} (raw SVG, drawn per post)
{{AUX_LABEL}} {{AUX_VALUE}} {{AUX_SUB}} {{HERO_LABEL}} {{HERO_VALUE}} {{HERO_SUB}} {{HERO_SUB1..3}} {{STATUS}}
{{SRC1}} {{SRC2}} {{HANDLE}} {{FOOT_NOTE}} {{ALT}}.  Colours are var(--nw-*) tokens from brand-alt.css.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

MARK = ('<g transform="translate({x} {y}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M6 25V8.5L19 25V12" stroke="var(--nw-ink)" stroke-width="2.4"/>'
        '<circle cx="19" cy="9.2" r="2.7" stroke="var(--nw-accent)" stroke-width="2"/></g>')

FONT_D = "font-family=\"'Space Grotesk', Inter, sans-serif\""
FONT_M = "font-family=\"'JetBrains Mono', monospace\""
FONT_B = "font-family=\"Inter, sans-serif\""


def header(W, M, y, ms, wm):
    return f'''  <!-- header: line mark + wordmark left, mono kicker right, hairline -->
  {MARK.format(x=M - 4, y=y - ms * 1.0, s=ms / 28)}
  <text x="{M + ms * 1.05:.0f}" y="{y + ms * 0.1:.0f}" {FONT_D} font-weight="700" font-size="{wm}" letter-spacing="{-wm * 0.05:.1f}" fill="var(--nw-ink)">nilwerk</text>
  <text x="{W - M}" y="{y + ms * 0.1:.0f}" text-anchor="end" {FONT_M} font-size="{wm * 0.52:.0f}" letter-spacing="1.4" fill="var(--nw-muted)">{{{{KICKER}}}}</text>
  <line x1="{M}" y1="{y + ms * 0.75:.0f}" x2="{W - M}" y2="{y + ms * 0.75:.0f}" stroke="var(--nw-rule)" stroke-width="1.5"/>
'''


def footer(W, M, rule_y, text_y, fs):
    return f'''  <line x1="{M}" y1="{rule_y}" x2="{W - M}" y2="{rule_y}" stroke="var(--nw-rule)" stroke-width="1.5"/>
  <g {FONT_M} font-size="{fs}" fill="var(--nw-muted)">
    <text x="{M}" y="{text_y}">{{{{HANDLE}}}}</text>
    <text x="{W - M}" y="{text_y}" text-anchor="end">{{{{FOOT_NOTE}}}}</text>
  </g>
'''


def status(M, y, fs):
    return (f'  <rect x="{M}" y="{y - fs * 0.8:.0f}" width="{fs * 0.75:.0f}" height="{fs * 0.75:.0f}" fill="var(--nw-warn)"/>\n'
            f'  <text x="{M + fs * 1.3:.0f}" y="{y}" {FONT_M} font-weight="600" font-size="{fs}" letter-spacing="0.8" fill="var(--nw-ink)">{{{{STATUS}}}}</text>\n')


def engineers(M, y, fs, gap, inline_x=None):
    if inline_x:
        return (f'  <text x="{M}" y="{y}" {FONT_M} font-weight="600" font-size="{fs}" letter-spacing="1.4" fill="var(--nw-accent)">FOR ENGINEERS</text>\n'
                f'  <g {FONT_M} font-size="{fs}" fill="var(--nw-muted)"><text x="{inline_x}" y="{y}">{{{{SRC1}}}}</text><text x="{inline_x}" y="{y + gap}">{{{{SRC2}}}}</text></g>\n')
    return (f'  <text x="{M}" y="{y}" {FONT_M} font-weight="600" font-size="{fs}" letter-spacing="1.4" fill="var(--nw-accent)">FOR ENGINEERS</text>\n'
            f'  <g {FONT_M} font-size="{fs}" fill="var(--nw-muted)"><text x="{M}" y="{y + gap}">{{{{SRC1}}}}</text><text x="{M}" y="{y + 2 * gap}">{{{{SRC2}}}}</text></g>\n')


def stack(W, H, M, hy, hs, lh, iy, isz, ilh, trace_y, aux, hero, st, eng, foot, ms, wm, hdr_y, hero_sub_lines=False, hero_x=None, hero_col=None):
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{{{{ALT}}}}">\n'
    s += f'  <!-- Nilwerk post template v0.2 (designer alternative, PROPOSAL). {W}x{H}. Strict grid, hairlines, no cards, no pills. -->\n'
    s += f'  <rect width="{W}" height="{H}" fill="var(--nw-bg)"/>\n'
    s += header(W, M, hdr_y, ms, wm)
    s += f'  <g {FONT_D} font-weight="500" font-size="{hs}" letter-spacing="{-hs * 0.03:.1f}" fill="var(--nw-ink)">\n'
    for i in range(3):
        s += f'    <text x="{M}" y="{hy + i * lh}">{{{{H{i + 1}}}}}</text>\n'
    s += '  </g>\n'
    s += f'  <g {FONT_B} font-size="{isz}" fill="var(--nw-muted)">\n    <text x="{M}" y="{iy}">{{{{INTRO1}}}}</text>\n    <text x="{M}" y="{iy + ilh}">{{{{INTRO2}}}}</text>\n  </g>\n'
    s += f'  <!-- trace: the one graphic device, drawn per post from the real content -->\n  <g transform="translate(0 {trace_y})">{{{{TRACE}}}}</g>\n'
    s += aux + hero + st + eng + foot + '</svg>\n'
    return s


def portrait():
    W, H, M = 1080, 1350, 72
    aux = (f'  <line x1="{M}" y1="716" x2="{W - M}" y2="716" stroke="var(--nw-rule)" stroke-width="1.5"/>\n'
           f'  <text x="{M}" y="754" {FONT_M} font-weight="600" font-size="18" letter-spacing="1.4" fill="var(--nw-warn)">{{{{AUX_LABEL}}}}</text>\n'
           f'  <text x="{M}" y="814" {FONT_M} font-weight="600" font-size="56" letter-spacing="-1" fill="var(--nw-ink)">{{{{AUX_VALUE}}}}</text>\n'
           f'  <text x="{M}" y="850" {FONT_B} font-size="22" fill="var(--nw-muted)">{{{{AUX_SUB}}}}</text>\n')
    hero = (f'  <line x1="{M}" y1="882" x2="{W - M}" y2="882" stroke="var(--nw-rule)" stroke-width="1.5"/>\n'
            f'  <text x="{M}" y="920" {FONT_M} font-weight="600" font-size="20" letter-spacing="1.4" fill="var(--nw-accent)">{{{{HERO_LABEL}}}}</text>\n'
            f'  <text x="{M - 8}" y="1096" {FONT_M} font-weight="600" font-size="220" letter-spacing="-8" fill="var(--nw-ink)">{{{{HERO_VALUE}}}}</text>\n'
            f'  <text x="{M}" y="1138" {FONT_B} font-size="24" fill="var(--nw-muted)">{{{{HERO_SUB}}}}</text>\n')
    return stack(W, H, M, 268, 80, 88, 520, 28, 40, 600, aux, hero, status(M, 1184, 20), engineers(M, 1226, 18, 24),
                 footer(W, M, 1288, 1322, 18), 40, 30, 96)


def square():
    W, H, M = 1080, 1080, 72
    aux = (f'  <line x1="{M}" y1="548" x2="{W - M}" y2="548" stroke="var(--nw-rule)" stroke-width="1.5"/>\n'
           f'  <text x="{M}" y="582" {FONT_M} font-weight="600" font-size="17" letter-spacing="1.4" fill="var(--nw-warn)">{{{{AUX_LABEL}}}}</text>\n'
           f'  <text x="{M}" y="634" {FONT_M} font-weight="600" font-size="48" letter-spacing="-1" fill="var(--nw-ink)">{{{{AUX_VALUE}}}}</text>\n'
           f'  <text x="{M}" y="664" {FONT_B} font-size="21" fill="var(--nw-muted)">{{{{AUX_SUB}}}}</text>\n')
    hero = (f'  <line x1="{M}" y1="690" x2="{W - M}" y2="690" stroke="var(--nw-rule)" stroke-width="1.5"/>\n'
            f'  <text x="{M}" y="724" {FONT_M} font-weight="600" font-size="18" letter-spacing="1.4" fill="var(--nw-accent)">{{{{HERO_LABEL}}}}</text>\n'
            f'  <text x="{M - 6}" y="858" {FONT_M} font-weight="600" font-size="170" letter-spacing="-6" fill="var(--nw-ink)">{{{{HERO_VALUE}}}}</text>\n'
            f'  <text x="{M}" y="894" {FONT_B} font-size="22" fill="var(--nw-muted)">{{{{HERO_SUB}}}}</text>\n')
    return stack(W, H, M, 232, 66, 72, 428, 26, 36, 470, aux, hero, status(M, 934, 18), engineers(M, 972, 16, 22),
                 footer(W, M, 1034, 1062, 17), 36, 28, 84)


def linkedin():
    W, H, M = 1200, 627, 56
    s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{{{{ALT}}}}">\n'
    s += f'  <!-- Nilwerk post template v0.2 (designer alternative, PROPOSAL). {W}x{H}. Hero number right, statement left, trace across. -->\n'
    s += f'  <rect width="{W}" height="{H}" fill="var(--nw-bg)"/>\n'
    s += header(W, M, 52, 30, 24)
    s += f'  <g {FONT_D} font-weight="500" font-size="48" letter-spacing="-1.4" fill="var(--nw-ink)">\n'
    for i in range(3):
        s += f'    <text x="{M}" y="{150 + i * 54}">{{{{H{i + 1}}}}}</text>\n'
    s += '  </g>\n'
    s += f'  <g {FONT_B} font-size="19" fill="var(--nw-muted)">\n    <text x="{M}" y="{150 + 2 * 54 + 44}">{{{{INTRO1}}}}</text>\n    <text x="{M}" y="{150 + 2 * 54 + 70}">{{{{INTRO2}}}}</text>\n  </g>\n'
    s += f'  <text x="680" y="124" {FONT_M} font-weight="600" font-size="14" letter-spacing="1.4" fill="var(--nw-accent)">{{{{HERO_LABEL}}}}</text>\n'
    s += f'  <text x="672" y="244" {FONT_M} font-weight="600" font-size="128" letter-spacing="-5" fill="var(--nw-ink)">{{{{HERO_VALUE}}}}</text>\n'
    s += f'  <g {FONT_B} font-size="17" fill="var(--nw-muted)">\n    <text x="680" y="278">{{{{HERO_SUB1}}}}</text>\n    <text x="680" y="300">{{{{HERO_SUB2}}}}</text>\n    <text x="680" y="322">{{{{HERO_SUB3}}}}</text>\n  </g>\n'
    s += f'  <g transform="translate(0 372)">{{{{TRACE}}}}</g>\n'
    s += f'  <line x1="{M}" y1="436" x2="{W - M}" y2="436" stroke="var(--nw-rule)" stroke-width="1.5"/>\n'
    s += (f'  <text x="{M}" y="466" {FONT_M} font-weight="600" font-size="13" letter-spacing="1.4" fill="var(--nw-warn)">{{{{AUX_LABEL}}}}</text>\n'
          f'  <text x="{M}" y="506" {FONT_M} font-weight="600" font-size="38" letter-spacing="-1" fill="var(--nw-ink)">{{{{AUX_VALUE}}}}</text>\n'
          f'  <text x="{M}" y="530" {FONT_B} font-size="15" fill="var(--nw-muted)">{{{{AUX_SUB}}}}</text>\n')
    s += status(680, 470, 14)
    s += engineers(M, 554, 13, 20, inline_x=190)
    s += footer(W, M, 592, 616, 13)
    s += '</svg>\n'
    return s


if __name__ == "__main__":
    out = HERE / "templates"
    out.mkdir(exist_ok=True)
    (out / "post-portrait-1080x1350.svg").write_text(portrait())
    (out / "post-square-1080x1080.svg").write_text(square())
    (out / "post-linkedin-1200x627.svg").write_text(linkedin())
    print("templates written")
