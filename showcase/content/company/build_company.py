#!/usr/bin/env python3
"""Render the three company carousels (4 slides x EN/DE, 1080x1350) in the Agent Diary look (avatar speech bubbles).
Run from this folder: NW_FONT_DIR=<node_modules>/@fontsource NODE_PATH=/opt/node-tools/node_modules python3 -I build_company.py
Code-generated, no AI imagery. Uses the helpers of ../diary/build_diary.py. Texts: company_data.py."""
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "diary"))
sys.path.insert(0, str(HERE))
import build_diary as bd  # noqa: E402
from company_data import POSTS  # noqa: E402

_wrap0 = bd.wrap


def wrap(text, *a, **k):
    """Keep a non-breaking space (e.g. in "27 %") inside one word; str.split() would split it."""
    return [l.replace("\ue000", "\u00a0") for l in _wrap0(text.replace("\u00a0", "\ue000"), *a, **k)]


bd.wrap = wrap  # eng_block and others wrap through the module global
T, lines_block, chip, logo, footer, eng_block, wrapper = bd.T, bd.lines_block, bd.chip, bd.logo, bd.footer, bd.eng_block, bd.wrapper


def avatar(name, x, y, size, uid):
    """Like bd.avatar but renames every id uniquely (bd.avatar breaks the clip path of pr-social.svg)."""
    import re
    s = (bd.AV / f"{name}.svg").read_text()
    inner = s[s.index(">") + 1 : s.rindex("</svg>")]
    for i in set(re.findall(r'id="([^"]+)"', inner)):
        inner = inner.replace(f'id="{i}"', f'id="{i}-{uid}"').replace(f"url(#{i})", f"url(#{i}-{uid})")
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 120 120">{inner}</svg>'
OUT = HERE / "images"


def head(b, lines, lang, y=320, size=None):
    n = max(len(s) for s in lines)
    size = size or (84 if n <= 16 else 74 if n <= 19 else 64 if n <= 22 else 56)
    for i, s in enumerate(lines):
        b.append(T(72, y + i * round(size * 1.08), s, size, "sg", 700, "var(--nw-accent)" if i == len(lines) - 1 else "var(--nw-ink)", ls=-2.2))
    return y + len(lines) * round(size * 1.08)


def speech(b, av, name, text, y, lang, uid, size=32):
    b.append(f'<rect x="68" y="{y}" width="176" height="176" rx="28" fill="var(--nw-surface)" stroke="var(--nw-accent)" stroke-width="4"/>')
    b.append(avatar(av, 72, y + 4, 168, uid))
    b.append(bd.T(156, y + 208, name, 24, "sg", 700, "var(--nw-ink)", anchor="middle"))
    q = wrap("“" + text + "”" if lang == "en" else "„" + text + "“", size, 690, "sg")
    bd.check(len(q) <= 6, f"bubble too long {name} {text[:30]}")
    bh = len(q) * round(size * 1.3) + 66
    bx = 272
    b.append(f'<rect x="{bx}" y="{y}" width="736" height="{bh}" rx="28" fill="var(--nw-surface)" stroke="var(--nw-accent)" stroke-width="3"/>')
    b.append(f'<path d="M{bx} {y + 60}L{bx - 30} {y + 84}L{bx} {y + 104}Z" fill="var(--nw-surface)" stroke="var(--nw-accent)" stroke-width="3" stroke-linejoin="round"/>')
    b.append(f'<line x1="{bx}" y1="{y + 66}" x2="{bx}" y2="{y + 100}" stroke="var(--nw-surface)" stroke-width="6"/>')
    b.append(lines_block(bx + 28, y + 54, q, size, round(size * 1.3), "sg", 500, "var(--nw-ink)"))
    pv = "PERSONA VOICE · WRITTEN FROM THE EVIDENCE" if lang == "en" else "PERSONA-STIMME · AUS DEN BELEGEN GESCHRIEBEN"
    b.append(T(1008 - 22, y + bh - 14, pv, 14, "mono", 400, "var(--nw-muted)", anchor="end", ls=0.5))
    return y + max(bh, 230)


def para(b, text, y, lang, size=30, maxw=936, lh=None, fill="var(--nw-ink)", maxlines=9):
    lh = lh or round(size * 1.38)
    ls = wrap(text, size, maxw, "inter")
    bd.check(len(ls) <= maxlines, f"paragraph too long ({len(ls)}): {text[:40]}")
    b.append(lines_block(72, y, ls, size, lh, "inter", 400, fill))
    return y + len(ls) * lh


def finish(b, s, lang, status_y):
    sc, _ = chip(72, status_y, s["status"][lang], "var(--nw-warn)", 20, 44)
    b.append(sc)
    b.append(eng_block(lang, s["eng"][lang], 1180, 3))
    b.append(footer(lang))


def render_slide(s, lang, uid):
    b = [logo()]
    kc, _ = chip(72, 176, s["kicker"][lang], "var(--nw-accent)", 24, 52, "var(--nw-accent-soft)", ls=1.2)
    b.append(kc)
    k = s["kind"]
    yh = head(b, s["head"][lang], lang)
    if k == "cover":
        y = speech(b, s["av"], s["name"], s["bubble"][lang], yh + 70, lang, uid, 34)
        b.append(T(72, y + 90, s["sub"][lang], 30, "inter", 600, "var(--nw-accent)"))
        # little arrow hint
        b.append(f'<path d="M72 {y + 130}h120m-24 -20l24 20l-24 20" fill="none" stroke="var(--nw-accent)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
        finish(b, s, lang, 1110)
    elif k == "story":
        y = para(b, s["body"][lang], yh + 50, lang, 30)
        speech(b, s["av"], s["name"], s["bubble"][lang], min(y + 40, 840), lang, uid, 30)
        finish(b, s, lang, 1110)
    elif k == "six":
        y = para(b, s["body"][lang], yh + 50, lang, 28, maxlines=6)
        top = y + 30
        for i, (av, nm, lab) in enumerate(s["tiles"]):
            x = 72 + (i % 2) * 480
            yy = top + (i // 2) * 124
            b.append(f'<rect x="{x}" y="{yy}" width="456" height="108" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
            b.append(f'<rect x="{x}" y="{yy}" width="10" height="108" rx="5" fill="var(--nw-accent)"/>')
            b.append(avatar(av, x + 22, yy + 12, 84, f"{uid}t{i}"))
            b.append(T(x + 124, yy + 52, lab[lang], 32, "sg", 700, "var(--nw-ink)", ls=-0.5))
            b.append(T(x + 124, yy + 86, nm + " · AI agent" if lang == "en" else nm + " · KI-Agent", 20, "mono", 400, "var(--nw-muted)"))
        finish(b, s, lang, 1110)
    elif k == "roster":
        rows = s["rows"]
        top = yh + 40
        ph = (1090 - top) // len(rows)
        ph = min(ph, 150)
        for i, (av, nm, role, ask) in enumerate(rows):
            yy = top + i * ph
            b.append(f'<rect x="72" y="{yy}" width="936" height="{ph - 12}" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
            a = ph - 36
            b.append(avatar(av, 88, yy + 12, a, f"{uid}r{i}"))
            tx = 88 + a + 22
            ns = 36 if ph > 120 else 30
            b.append(T(tx, yy + (44 if ph > 120 else 34), nm, ns, "sg", 700, "var(--nw-ink)", ls=-1))
            b.append(T(tx + 28 + len(nm) * round(ns * 0.62), yy + (44 if ph > 120 else 34), role[lang].upper(), 17, "mono", 600, "var(--nw-accent)", ls=0.6))
            al = wrap(("Always asks: " if lang == "en" else "Fragt immer: ") + ask[lang], 22 if ph > 120 else 21, 936 - (tx - 72) - 30, "inter")
            b.append(lines_block(tx, yy + (76 if ph > 120 else 62), al[:2], 22 if ph > 120 else 21, 28, "inter", 400, "var(--nw-muted)"))
        finish(b, s, lang, 1110)
    elif k == "humans":
        top = yh + 40
        for i, (av, nm, txt) in enumerate(s["people"]):
            yy = top + i * 226
            b.append(f'<rect x="72" y="{yy}" width="936" height="206" rx="20" fill="var(--nw-surface)" stroke="var(--nw-accent)" stroke-width="3"/>')
            b.append(avatar(av, 92, yy + 20, 166, f"{uid}h{i}"))
            b.append(T(286, yy + 62, nm[lang], 36, "sg", 700, "var(--nw-ink)", ls=-1))
            b.append(T(286, yy + 90, "HUMAN" if lang == "en" else "MENSCH", 17, "mono", 600, "var(--nw-accent)", ls=1))
            b.append(lines_block(286, yy + 128, wrap(txt[lang], 25, 700, "inter")[:3], 25, 33, "inter", 400, "var(--nw-ink)"))
        y = top + 2 * 226 + 10
        para(b, s["note"][lang], y + 20, lang, 25, maxlines=3, fill="var(--nw-muted)")
        finish(b, s, lang, 1110)
    elif k == "flow":
        steps = s["steps"]
        top = yh + 30
        ph = 90
        for i, (av, t, d) in enumerate(steps):
            yy = top + i * (ph + 8)
            b.append(f'<rect x="72" y="{yy}" width="936" height="{ph}" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
            b.append(f'<circle cx="122" cy="{yy + 45}" r="22" fill="var(--nw-accent)"/>' + T(122, yy + 55, str(i + 1), 26, "sg", 700, "var(--nw-accent-ink)", anchor="middle"))
            b.append(avatar(av, 160, yy + 8, 74, f"{uid}f{i}"))
            b.append(T(262, yy + 42, t[lang], 32, "sg", 700, "var(--nw-ink)", ls=-0.8))
            b.append(T(262, yy + 72, d[lang], 22, "inter", 400, "var(--nw-muted)"))
            if i < len(steps) - 1:
                b.append(f'<path d="M122 {yy + 72}v{ph - 94 + 8}" stroke="var(--nw-accent)" stroke-width="3" stroke-linecap="round" opacity="0"/>')
        finish(b, s, lang, 1110)
    elif k == "stats":
        y = para(b, s["body"][lang], yh + 50, lang, 27, maxlines=8)
        top = y + 24
        for i, (num, lab) in enumerate(s["tiles"]):
            x = 72 + i * 316
            b.append(f'<rect x="{x}" y="{top}" width="304" height="210" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
            b.append(f'<rect x="{x}" y="{top}" width="304" height="10" rx="5" fill="var(--nw-accent)"/>')
            b.append(T(x + 152, top + 100, num, 76 if len(num) < 4 else 62, "sg", 700, "var(--nw-ink)", anchor="middle", ls=-2))
            ll = wrap(lab[lang], 22, 260, "inter")
            b.append("".join(T(x + 152, top + 150 + j * 28, t, 22, "inter", 400, "var(--nw-muted)", anchor="middle") for j, t in enumerate(ll[:2])))
        finish(b, s, lang, 1110)
    alt = s.get("alt_text", "")
    return wrapper("\n".join(b), alt, uid, "light")


def main():
    jobs, svgs = [], []
    tmp = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "nwcompany"
    tmp.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    for pid, p in POSTS.items():
        for i, s in enumerate(p["slides"]):
            for lang in ("en", "de"):
                s2 = dict(s, alt_text=p["alt"][i][lang])
                svg = render_slide(s2, lang, f"c{p['day']}{i}")
                name = f"{pid}-s{i + 1}-{lang}"
                (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
                svgs.append((name, OUT / f"{name}.svg"))
    for name, sp in svgs:
        jobs.append((sp, OUT / f"{name}.png"))
    bd.bp.render_png(jobs, scale=1)
    fcss = bd.bp.font_css()
    pages = []
    for name, sp in svgs:
        hp = tmp / f"{name}.html"
        hp.write_text(f"<!doctype html><meta charset=utf-8><style>{fcss}html,body{{margin:0}}svg{{display:block}}</style>" + sp.read_text(encoding="utf-8"), encoding="utf-8")
        pages.append(dict(html=str(hp), name=name))
    jf = tmp / "pages.json"
    jf.write_text(json.dumps(pages))
    env = dict(os.environ)
    env.setdefault("NODE_PATH", "/opt/node-tools/node_modules")
    r = subprocess.run(["node", str(HERE.parent / "diary" / "check_bbox.js"), str(jf)], env=env)
    print("layout warnings:", len(bd.PROBLEMS), "| bbox exit:", r.returncode)


if __name__ == "__main__":
    main()
