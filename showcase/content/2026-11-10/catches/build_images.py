#!/usr/bin/env python3
"""Render the 5-slide carousel (EN + DE, 1080x1350). Code-generated from real data, no AI imagery; slide 1 embeds the real plan render.
Run: NW_FONT_DIR=<node_modules>/@fontsource NODE_PATH=<dir with playwright-core> python3 -I build_images.py
(Reuses the helpers of ../../diary/build_diary.py; Chrome via playwright-core, path in NW_CHROME, default /usr/bin/google-chrome.)"""
import base64, json, os, pathlib, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "diary"))
sys.path.insert(0, str(HERE))
import build_diary as bd  # noqa: E402
from catches_data import SLIDES  # noqa: E402
bd.W, bd.H = 1080, 1350
T, lines_block, chip, logo, footer, eng_block, wrap = bd.T, bd.lines_block, bd.chip, bd.logo, bd.footer, bd.eng_block, bd.wrap
OUT = HERE / "images"
PIC = OUT / "source-enclosure-v3-plan.png"


def head(b, lines, y=338):
    n = max(len(s) for s in lines)
    size = 76 if n <= 14 else 70 if n <= 16 else 64 if n <= 19 else 56
    bd.check(n <= 22, "headline too long")
    for i, s in enumerate(lines):
        b.append(T(72, y + i * round(size * 1.08), s, size, "sg", 700, "var(--nw-accent)" if i == len(lines) - 1 else "var(--nw-ink)", ls=-2.2))
    return y + len(lines) * round(size * 1.08)


def para(b, text, y, size=30, maxw=936, maxlines=8):
    ls = wrap(text, size, maxw, "inter")
    bd.check(len(ls) <= maxlines, f"paragraph too long ({len(ls)}): {text[:40]}")
    lh = round(size * 1.38)
    b.append(lines_block(72, y, ls, size, lh, "inter", 400, "var(--nw-ink)"))
    return y + len(ls) * lh


def tiles(b, items, top, h=190):
    n = len(items)
    w = (936 - 16 * (n - 1)) // n
    for i, (num, lab) in enumerate(items):
        x = 72 + i * (w + 16)
        b.append(f'<rect x="{x}" y="{top}" width="{w}" height="{h}" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
        b.append(f'<rect x="{x}" y="{top}" width="{w}" height="10" rx="5" fill="var(--nw-accent)"/>')
        b.append(T(x + w // 2, top + 92, num, 76 if n == 2 else 62, "sg", 700, "var(--nw-ink)", anchor="middle", ls=-2))
        ll = wrap(lab, 22 if n == 2 else 20, w - 40, "inter")
        bd.check(len(ll) <= 3, f"tile label long {lab}")
        b.append("".join(T(x + w // 2, top + 132 + j * 26, t, 22 if n == 2 else 20, "inter", 400, "var(--nw-muted)", anchor="middle") for j, t in enumerate(ll)))


def render(s, lang, idx):
    g = lambda k: s[k][lang]
    b = [logo()]
    kc, _ = chip(72, 176, g("kicker"), "var(--nw-accent)", 22, 52, "var(--nw-accent-soft)", ls=1.0)
    b.append(kc)
    yh = head(b, g("head"))
    k = s["kind"]
    if k == "cover":
        y = para(b, g("body"), yh + 40, 28, maxlines=4)
        top = y + 24
        pw = 430
        ph = round(pw * 862 / 1091)
        b.append(f'<rect x="72" y="{top}" width="{pw + 8}" height="{ph + 8}" rx="14" fill="#ffffff" stroke="var(--nw-line)" stroke-width="2"/>')
        data = base64.b64encode(PIC.read_bytes()).decode()
        b.append(f'<image x="76" y="{top + 4}" width="{pw}" height="{ph}" href="data:image/png;base64,{data}"/>')
        cap = wrap(g("pic"), 22, 460, "inter")
        bd.check(len(cap) <= 10, "pic caption long")
        b.append(lines_block(604 + 8, top + 40, cap, 22, 30, "inter", 400, "var(--nw-muted)"))
        sy = top + ph + 8 + 22
    elif k in ("tiles", "tiles3"):
        y = para(b, g("body"), yh + 46, 28, maxlines=8)
        tiles(b, [(n[lang], l[lang]) for n, l in s["tiles"]], y + 26, 206)
        sy = y + 26 + 206 + 22
    elif k == "rows":
        top = yh + 24
        for i, (tag, txt) in enumerate(s["rows"]):
            yy = top + i * 118
            b.append(f'<rect x="72" y="{yy}" width="936" height="106" rx="16" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
            b.append(f'<rect x="72" y="{yy}" width="10" height="106" rx="5" fill="var(--nw-accent)"/>')
            b.append(T(104, yy + 32, tag, 18, "mono", 600, "var(--nw-accent)", ls=1.2))
            ls_ = wrap(txt[lang], 24, 860, "inter")
            bd.check(len(ls_) <= 3, f"row too long {txt['en'][:30]}")
            b.append(lines_block(104, yy + 58, ls_, 24, 29, "inter", 400, "var(--nw-ink)"))
        sy = top + 5 * 118 + 2
    bd.check(sy <= 1132, f"status chip too low {sy} slide {idx}")
    sc, _ = chip(72, min(sy, 1124), g("status"), "var(--nw-warn)", 20, 44)
    b.append(sc)
    b.append(eng_block(lang, g("eng"), 1182, 3))
    b.append(footer(lang))
    return bd.wrapper("\n".join(b), g("alt"), f"c{idx}", "light")


def main():
    jobs, tmp = [], pathlib.Path(tempfile.mkdtemp(prefix="nwcatch_"))
    fcss = bd.bp.font_css()
    for i, s in enumerate(SLIDES, 1):
        for lang in ("en", "de"):
            svg = render(s, lang, i)
            name = f"catches-s{i}-{lang}-portrait-1080x1350"
            (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
            page = tmp / f"{name}.html"
            page.write_text(f"<!doctype html><meta charset=utf-8><style>{fcss}html,body{{margin:0;background:#fff}}svg{{display:block}}</style>{svg}")
            jobs.append(dict(html=str(page), png=str(OUT / f"{name}.png"), w=1080, h=1350))
    (tmp / "jobs.json").write_text(json.dumps(dict(scale=1, jobs=jobs)))
    js = tmp / "r.js"
    js.write_text("""const {chromium}=require('playwright-core');const fs=require('fs');
(async()=>{const {scale,jobs}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const br=await chromium.launch({executablePath:process.env.NW_CHROME||'/usr/bin/google-chrome'});
for(const j of jobs){const c=await br.newContext({viewport:{width:j.w,height:j.h},deviceScaleFactor:scale});const p=await c.newPage();
await p.goto('file://'+j.html);await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:j.png});await c.close();}
await br.close();})();""")
    subprocess.run(["node", str(js), str(tmp / "jobs.json")], check=True)
    print("problems:", bd.PROBLEMS)


main()
