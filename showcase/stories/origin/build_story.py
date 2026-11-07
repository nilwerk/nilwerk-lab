#!/usr/bin/env python3
"""Render the Nilwerk origin story carousel in the approved v0.1 brand: 10 slides 1080x1350 (EN + DE) and a LinkedIn timeline cover 1200x627.
Texts: story_content.py. Output: slides/en/slide-NN.png, slides/de/slide-NN.png, linkedin-cover-en.png, linkedin-cover-de.png.
Run with a Python that has fontTools (e.g. python3.13) and NW_FONT_DIR=<node_modules>/@fontsource:
    NW_FONT_DIR=... python3.13 -I build_story.py
Text is wrapped with real font metrics (no kerning, 3 % safety margin); after rendering a Chromium pass checks that no text leaves the canvas margins.
"""
import html
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BRAND = HERE.parents[1] / "brand"
sys.path.insert(0, str(BRAND))
sys.path.insert(0, str(HERE))
import build_extra as bx  # noqa: E402  (tokens + fill helpers of the approved brand)
import build_post as v01  # noqa: E402
import make_extra_templates as mt  # noqa: E402  (logo, fonts strings)
from fontTools.ttLib import TTFont  # noqa: E402
from story_content import ROLES, SLIDES, TEAM, TIMELINE  # noqa: E402

FD, FM, FB = mt.FD, mt.FM, mt.FB
FD_DIR = pathlib.Path(os.environ["NW_FONT_DIR"])


def load(pkg, fn):
    f = TTFont(FD_DIR / pkg / "files" / fn)
    return f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm


METRIC = {"d": load("space-grotesk", "space-grotesk-latin-700-normal.woff"), "b": load("inter", "inter-latin-400-normal.woff"),
          "bs": load("inter", "inter-latin-600-normal.woff")}


def width(text, kind, size, ls=0.0):
    gs, cmap, upm = METRIC[kind]
    w = 0.0
    for ch in text:
        g = cmap.get(ord(" " if ch == "\u00a0" else ch)) or cmap.get(ord("?"))
        w += gs[g].width * size / upm + ls
    return w * 1.03


def wrap(text, kind, size, maxw, ls=0.0):
    text = re.sub(r"(\d\.) (Nov)", "\\1\u00a0\\2", text)
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if width(t, kind, size, ls) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def mono_wrap(text, size, maxw, ls=0.0):
    per = max(1, int(maxw // (0.6 * size + ls)))
    return wrap_chars(text, per)


def wrap_chars(text, per):
    out, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if len(t) <= per or not cur:
            cur = t
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    return out


def esc(s):
    return html.escape(s, quote=True)


W, H, M = 1080, 1350, 72
CW = W - 2 * M
AV = (ROOT / "team" / "avatars").as_uri()
ASSET = (HERE / "assets").as_uri()
WF = (ROOT / "projects" / "plant-monitor" / "app" / "wireframes" / "03-plants.png").as_uri()
IMGS = {"v1-exploded": (420, 410), "pcb-v1": (430, 700), "v2-assembled": (390, 470), "v2-exploded": (440, 420), "v2-back-shell": (250, 360)}


def image_el(name, x, y, w, h):
    """Place an asset inside the box (x, y, w, h), contain, never enlarged beyond 1.25x."""
    if name == "wireframe":
        cw, ch, cx, cy, src = 545, 485, 0, 100, WF
        full = (1268, 1235)
        s = min(w / cw, h / ch, 1.25)
        dw, dh = cw * s, ch * s
        ox, oy = x + (w - dw) / 2, y + (h - dh) / 2
        return (f'<svg x="{ox:.1f}" y="{oy:.1f}" width="{dw:.1f}" height="{dh:.1f}" viewBox="{cx} {cy} {cw} {ch}">'
                f'<image href="{src}" width="{full[0]}" height="{full[1]}"/></svg>')
    iw, ih = IMGS[name]
    s = min(w / iw, h / ih, 1.25)
    dw, dh = iw * s, ih * s
    return f'<image href="{ASSET}/{name}.png" x="{x + (w - dw) / 2:.1f}" y="{y + (h - dh) / 2:.1f}" width="{dw:.1f}" height="{dh:.1f}"/>'


def pill(x, y, text, size=26):
    w = width(text, "bs", size) + 40
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="52" rx="26" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>'
            f'<text x="{x + 20}" y="{y + 35}" {FB} font-weight="600" font-size="{size}" fill="var(--nw-ink)">{esc(text)}</text>', w)


def slide_svg(spec, n, total, lang):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(spec["alt"])}">',
         '<defs><pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="var(--nw-line)" stroke-width="1.5" opacity=".55"/></pattern></defs>',
         f'<rect width="{W}" height="{H}" fill="var(--nw-bg)"/><rect width="{W}" height="{H}" fill="url(#grid)"/>']
    s.append(mt.logo(M, 56, 1.75, 36, M + 66, 98))
    s.append(f'<text x="{W - M}" y="96" text-anchor="end" {FM} font-weight="600" font-size="26" fill="var(--nw-muted)">{n} / {total}</text>')
    kw = len(spec["kicker"]) * (0.6 * 21 + 1.05) + 44
    s.append(f'<rect x="{M}" y="150" width="{kw:.0f}" height="48" rx="24" fill="var(--nw-accent-soft)" stroke="var(--nw-accent)" stroke-width="2"/>'
             f'<text x="{M + 22}" y="182" {FM} font-weight="600" font-size="21" letter-spacing="1.05" fill="var(--nw-accent)">{esc(spec["kicker"])}</text>')
    hs = 96 if spec.get("big") else 76
    while max(width(t, "d", hs, -hs * 0.025) for t in spec["headline"]) > CW and hs > 56:
        hs -= 2
    y = 300 if not spec.get("big") else 310
    lh = hs * 1.1
    hl = spec["headline"]
    for i, line in enumerate(hl):
        fill = "var(--nw-accent)" if (spec.get("big") and i == len(hl) - 1) else "var(--nw-ink)"
        if width(line, "d", hs, -hs * 0.025) > CW:
            print(f"WARN headline too wide slide {n} {lang}: {line}", file=sys.stderr)
        s.append(f'<text x="{M}" y="{y + i * lh:.0f}" {FD} font-weight="700" font-size="{hs}" letter-spacing="{-hs * 0.025:.1f}" fill="{fill}">{esc(line)}</text>')
    y += (len(hl) - 1) * lh + (84 if spec.get("big") else 58)
    bottom = 1282  # footer rule
    # pinned bottom parts: chip + eng
    eng = spec.get("eng")
    eng_lines = []
    if eng:
        for e in eng:
            eng_lines += mono_wrap(e, 20, CW - 64)
    eng_h = (34 + 30 * len(eng_lines) + 26) if eng else 0
    chip = spec.get("chip")
    chip_h = 70 if chip else 0
    eng_top = bottom - 22 - eng_h
    chip_top = eng_top - chip_h
    limit = chip_top - 10 if chip else eng_top - 14
    for kind, val in spec["blocks"]:
        if kind == "text":
            paras = val if isinstance(val, list) else [val]
            for p in paras:
                for ln in wrap(p, "b", 34, CW):
                    s.append(f'<text x="{M}" y="{y:.0f}" {FB} font-size="34" fill="var(--nw-ink)">{esc(ln)}</text>')
                    y += 48
                y += 14
        elif kind == "media":
            h = limit - y
            if h < 150:
                print(f"WARN media area only {h:.0f}px on slide {n} {lang}", file=sys.stderr)
            s.append(f'<rect x="{M}" y="{y:.0f}" width="{CW}" height="{h:.0f}" rx="18" fill="#faf9f7" stroke="var(--nw-line)" stroke-width="2"/>')
            k = len(val)
            gap = 20
            bw = (CW - 40 - gap * (k - 1)) / k
            for i, name in enumerate(val):
                s.append(image_el(name, M + 20 + i * (bw + gap), y + 16, bw, h - 32))
            y += h
        elif kind == "grid":
            cols, cell = 5, CW / 5
            for i, (av, nm) in enumerate(TEAM):
                cx, cy = M + (i % cols) * cell, y + (i // cols) * 232
                role = ROLES[lang][i]
                rs = 19
                while width(role, "b", rs) > cell - 28 and rs > 14:
                    rs -= 1
                s.append(f'<rect x="{cx + 6:.0f}" y="{cy:.0f}" width="{cell - 12:.0f}" height="216" rx="16" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>'
                         f'<image href="{AV}/{av}.svg" x="{cx + cell / 2 - 52:.0f}" y="{cy + 14:.0f}" width="104" height="104"/>'
                         f'<text x="{cx + cell / 2:.0f}" y="{cy + 154:.0f}" text-anchor="middle" {FD} font-weight="700" font-size="30" fill="var(--nw-ink)">{esc(nm)}</text>'
                         f'<text x="{cx + cell / 2:.0f}" y="{cy + 188:.0f}" text-anchor="middle" {FB} font-size="{rs}" fill="var(--nw-muted)">{esc(role)}</text>')
            y += 2 * 232 + 6
        elif kind == "humans":
            for i, t in enumerate(val):
                cx = M + i * (CW / 2)
                s.append(f'<rect x="{cx:.0f}" y="{y:.0f}" width="{CW / 2 - 12:.0f}" height="96" rx="16" fill="none" stroke="var(--nw-ink)" stroke-width="2" stroke-dasharray="8 6"/>'
                         f'<image href="{AV}/human-public.svg" x="{cx + 14:.0f}" y="{y + 12:.0f}" width="72" height="72"/>')
                for j, ln in enumerate(wrap(t, "b", 22, CW / 2 - 130)):
                    s.append(f'<text x="{cx + 100:.0f}" y="{y + 40 + j * 28:.0f}" {FB} font-size="22" fill="var(--nw-ink)">{esc(ln)}</text>')
            y += 110
        elif kind == "flow":
            x, rows_y = M, y
            for i, t in enumerate(val):
                el, w = pill(x, rows_y, t)
                if x + w > W - M:
                    x, rows_y = M, rows_y + 70
                    el, w = pill(x, rows_y, t)
                    if s[-1].startswith('<text') and "→" in s[-1]:
                        s.pop()  # no dangling arrow at the end of the previous row
                s.append(el)
                x += w
                if i < len(val) - 1:
                    s.append(f'<text x="{x + 8:.0f}" y="{rows_y + 36}" {FM} font-size="24" fill="var(--nw-muted)">→</text>')
                    x += 34
            y = rows_y + 52 + 44
        elif kind == "tiles":
            for i, key in enumerate(("a", "b")):
                lab, val_, subs, tone = val[key]
                tc = "var(--nw-ink)" if tone == "ink" else "var(--nw-warn)"
                bar = "var(--nw-accent)" if tone == "ink" else "var(--nw-warn)"
                tx = M + i * (CW / 2 + 12)
                tw = CW / 2 - 12
                th = 330
                s.append(f'<rect x="{tx:.0f}" y="{y:.0f}" width="{tw:.0f}" height="{th}" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>'
                         f'<rect x="{tx:.0f}" y="{y:.0f}" width="{tw:.0f}" height="10" rx="5" fill="{bar}"/>'
                         f'<text x="{tx + 28:.0f}" y="{y + 62:.0f}" {FM} font-weight="600" font-size="22" letter-spacing="1" fill="{tc if tone != "ink" else "var(--nw-accent)"}">{esc(lab)}</text>'
                         f'<text x="{tx + 28:.0f}" y="{y + 160:.0f}" {FD} font-weight="700" font-size="92" letter-spacing="-2.8" fill="var(--nw-ink)">{esc(val_)}</text>')
                for j, ln in enumerate(subs):
                    s.append(f'<text x="{tx + 28:.0f}" y="{y + 214 + j * 34:.0f}" {FB} font-size="26" fill="var(--nw-muted)">{esc(ln)}</text>')
            y += 330 + 16
        elif kind == "poppy":
            y += 20
            s.append(f'<image href="{AV}/pr-social.svg" x="{M}" y="{y:.0f}" width="220" height="220"/>')
            for j, ln in enumerate(val):
                s.append(f'<text x="{M + 256}" y="{y + 96 + j * 52:.0f}" {FB} font-weight="600" font-size="34" fill="var(--nw-ink)">{esc(ln)}</text>')
            y += 240
    if y > limit + 2:
        print(f"WARN content overflows by {y - limit:.0f}px on slide {n} {lang}", file=sys.stderr)
    if chip:
        cw_ = len(chip) * (0.6 * 21 + 1.05) + 40
        s.append(f'<rect x="{M}" y="{chip_top + 6}" width="{cw_:.0f}" height="48" rx="8" fill="none" stroke="var(--nw-warn)" stroke-width="2"/>'
                 f'<text x="{M + 20}" y="{chip_top + 38}" {FM} font-weight="600" font-size="21" letter-spacing="1.05" fill="var(--nw-warn)">{esc(chip)}</text>')
    if eng:
        s.append(f'<rect x="{M}" y="{eng_top}" width="{CW}" height="{eng_h}" rx="14" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>'
                 f'<rect x="{M}" y="{eng_top}" width="8" height="{eng_h}" rx="4" fill="var(--nw-accent)"/>'
                 f'<text x="{M + 32}" y="{eng_top + 34}" {FM} font-weight="600" font-size="20" letter-spacing="1.5" fill="var(--nw-accent)">FOR ENGINEERS</text>'.replace("FOR ENGINEERS", "FÜR INGENIEURE" if lang == "de" else "FOR ENGINEERS"))
        for j, ln in enumerate(eng_lines):
            s.append(f'<text x="{M + 32}" y="{eng_top + 34 + 30 * (j + 1)}" {FM} font-size="20" fill="var(--nw-muted)">{esc(ln)}</text>')
    s.append(f'<line x1="{M}" y1="1282" x2="{W - M}" y2="1282" stroke="var(--nw-line)" stroke-width="2"/>')
    foot = "AI agents, led and reviewed by humans" if lang == "en" else "KI-Agenten, geleitet und geprüft von Menschen"
    s.append(f'<g {FM} font-size="21" fill="var(--nw-muted)"><text x="{M}" y="1318">@nilwerk · nilwerk.de</text><text x="{W - M}" y="1318" text-anchor="end">{esc(foot)}</text></g>')
    s.append("</svg>")
    return "".join(s)


def cover_svg(lang):
    W2, H2, M2 = 1200, 627, 56
    items = TIMELINE[lang]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}" role="img" aria-label="Timeline of the first week of Nilwerk, 1 to 7 November 2026">',
         '<defs><pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="var(--nw-line)" stroke-width="1.5" opacity=".55"/></pattern></defs>',
         f'<rect width="{W2}" height="{H2}" fill="var(--nw-bg)"/><rect width="{W2}" height="{H2}" fill="url(#grid)"/>']
    s.append(mt.logo(M2, 36, 1.5, 30, M2 + 60, 74))
    kick = "LOGBOOK · THE STORY SO FAR" if lang == "en" else "LOGBUCH · DIE GESCHICHTE BISHER"
    s.append(f'<text x="{W2 - M2}" y="70" text-anchor="end" {FM} font-weight="600" font-size="16" letter-spacing="1.4" fill="var(--nw-accent)">{kick}</text>')
    hl = ["One prompt. One plant sensor.", "A whole team."] if lang == "en" else ["Ein Prompt. Ein Pflanzensensor.", "Ein ganzes Team."]
    s.append(f'<g {FD} font-weight="700" font-size="64" letter-spacing="-1.8"><text x="{M2}" y="190" fill="var(--nw-ink)">{esc(hl[0])}</text><text x="{M2}" y="262" fill="var(--nw-accent)">{esc(hl[1])}</text></g>')
    sub = ("The first week of an AI-agent team, led and reviewed by humans." if lang == "en" else "Die erste Woche eines KI-Agenten-Teams, geleitet und geprüft von Menschen.")
    s.append(f'<text x="{M2}" y="306" {FB} font-size="24" fill="var(--nw-muted)">{esc(sub)}</text>')
    n = len(items)
    x0, x1, ty = M2 + 12, W2 - M2 - 118, 380
    step = (x1 - x0) / (n - 1)
    s.append(f'<path d="M{M2 - 20},{ty} H{W2 + 10}" stroke="var(--nw-accent)" stroke-width="4" fill="none"/>')
    for i, (d, l1, l2) in enumerate(items):
        cx = x0 + i * step
        s.append(f'<circle cx="{cx:.0f}" cy="{ty}" r="10" fill="var(--nw-bg)" stroke="var(--nw-accent)" stroke-width="4"/>')
        anchor = "start"
        tx = cx - 10
        s.append(f'<text x="{tx:.0f}" y="{ty + 40}" text-anchor="{anchor}" {FM} font-weight="600" font-size="14" letter-spacing="1" fill="var(--nw-accent)">{esc(d)}</text>'
                 f'<text x="{tx:.0f}" y="{ty + 66}" text-anchor="{anchor}" {FB} font-size="15" fill="var(--nw-ink)">{esc(l1)}</text>'
                 f'<text x="{tx:.0f}" y="{ty + 88}" text-anchor="{anchor}" {FB} font-size="15" fill="var(--nw-ink)">{esc(l2)}</text>')
    chip = "FACTS FROM THE DAILY REPORTS AND THE REPO" if lang == "en" else "FAKTEN AUS DEN TAGESBERICHTEN UND DEM REPO"
    cw_ = len(chip) * (0.6 * 14 + 0.7) + 36
    s.append(f'<rect x="{M2}" y="506" width="{cw_:.0f}" height="36" rx="8" fill="none" stroke="var(--nw-warn)" stroke-width="2"/>'
             f'<text x="{M2 + 16}" y="530" {FM} font-weight="600" font-size="14" letter-spacing="0.7" fill="var(--nw-warn)">{chip}</text>')
    foot = "AI agents, led and reviewed by humans" if lang == "en" else "KI-Agenten, geleitet und geprüft von Menschen"
    s.append(f'<line x1="{M2}" y1="582" x2="{W2 - M2}" y2="582" stroke="var(--nw-line)" stroke-width="1.5"/>'
             f'<g {FM} font-size="15" fill="var(--nw-muted)"><text x="{M2}" y="610">@nilwerk · nilwerk.de</text><text x="{W2 - M2}" y="610" text-anchor="end">{esc(foot)}</text></g></svg>')
    return "".join(s)


def resolve(svg, theme="light"):
    import re
    tk = bx.tokens(theme)
    return re.sub(r"var\(--nw-([a-z-]+)\)", lambda mo: tk[mo.group(1)], svg)


def write_alt_texts():
    out = ["# Alt texts of the origin story slides (EN and DE)\n"]
    for lang in ("en", "de"):
        out.append(f"\n## {lang.upper()}\n")
        for i, sp in enumerate(SLIDES[lang], 1):
            out.append(f"{i}. {sp['alt']}\n")
    (HERE / "alt-texts.md").write_text("".join(out))


def main():
    write_alt_texts()
    jobs = []
    tmp = HERE / ".tmp"
    tmp.mkdir(exist_ok=True)
    for lang in ("en", "de"):
        out = HERE / "slides" / lang
        out.mkdir(parents=True, exist_ok=True)
        total = len(SLIDES[lang])
        for i, spec in enumerate(SLIDES[lang], 1):
            f = tmp / f"{lang}-{i:02d}.svg"
            f.write_text(resolve(slide_svg(spec, i, total, lang)))
            jobs.append((f, out / f"slide-{i:02d}.png"))
        f = tmp / f"cover-{lang}.svg"
        f.write_text(resolve(cover_svg(lang)))
        jobs.append((f, HERE / f"linkedin-cover-{lang}.png"))
    v01.render_png(jobs, scale=1)
    for f in tmp.glob("*.svg"):
        f.unlink()
    tmp.rmdir()


if __name__ == "__main__":
    main()
