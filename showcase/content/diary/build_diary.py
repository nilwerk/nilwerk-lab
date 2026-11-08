#!/usr/bin/env python3
"""Render the Agent Diary cards and the extra visuals (EN + DE) with the v0.1 brand tokens. Code-generated, no AI imagery.
Run: NW_FONT_DIR=<node_modules>/@fontsource python3 -I build_diary.py [--only name-substring]
Outputs (svg + png) into ./images. Texts: diary_data.py (facts as of 8 Nov 2026), claims: claim-check.md.
After rendering it runs check_bbox.js (no text may run past the right margin). LOOK at every PNG anyway.
"""
import base64
import html
import json
import pathlib
import re
import subprocess
import sys
import os

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # showcase/
sys.path.insert(0, str(ROOT / "brand"))
sys.path.insert(0, str(HERE))
import build_post as bp  # noqa: E402
from diary_data import DAYS  # noqa: E402

AV = ROOT.parent / "team" / "avatars"
SHOTS = ROOT / "items" / "2026-11-08_4.A2"
OUT = HERE / "images"
W, H = 1080, 1350
FOOT = {"en": "AI agents, led and reviewed by humans", "de": "KI-Agenten, geleitet und geprüft von Menschen"}
ASOF = "16:10"  # set at build time after the recount
FW = {"inter": 0.54, "sg": 0.57, "mono": 0.6}  # average advance per em (safety margin included)


def check(cond, msg):
    if not cond:
        print("LAYOUT WARNING:", msg, file=sys.stderr)
        PROBLEMS.append(msg)


PROBLEMS = []


def esc(s):
    return html.escape(str(s), quote=True)


def wrap(text, size, maxw, fam="inter", ls=0.0):
    per = FW[fam] * size + ls
    lim = max(8, int(maxw / per))
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if len(t) <= lim:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def T(x, y, s, size, fam="inter", weight=400, fill="var(--nw-ink)", anchor=None, ls=None, style=None):
    f = {"inter": "Inter, sans-serif", "sg": "'Space Grotesk', Inter, sans-serif", "mono": "'JetBrains Mono', monospace"}[fam]
    a = f' text-anchor="{anchor}"' if anchor else ""
    l = f' letter-spacing="{ls}"' if ls is not None else ""
    st = f' font-style="{style}"' if style else ""
    return f'<text x="{x}" y="{y}" font-family="{f}" font-weight="{weight}" font-size="{size}"{l}{a}{st} fill="{fill}">{esc(s)}</text>'


def lines_block(x, y, lines, size, lh, fam="inter", weight=400, fill="var(--nw-ink)", ls=None):
    return "\n".join(T(x, y + i * lh, ln, size, fam, weight, fill, ls=ls) for i, ln in enumerate(lines))


def chip(x, y, text, color, size=22, h=48, fill="none", dash=False, ls=1.0):
    w = round(len(text) * (0.6 * size + ls) + 40)
    d = ' stroke-dasharray="10 7"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h // 2 if fill != "none" else 8}" fill="{fill}" stroke="{color}" stroke-width="2"{d}/>'
            + T(x + 20, y + h // 2 + size // 3, text, size, "mono", 600, color, ls=ls)), w


def logo(x=72, y=64):
    return f'''<g transform="translate({x} {y}) scale(2.25)">
<rect x="1" y="1" width="30" height="30" rx="9" fill="#15181d" stroke="#ffffff" stroke-opacity=".12"/>
<path d="M10 22V9.5l12 12.5V9.5" fill="none" stroke="#3fc79a" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="10" cy="22" r="2.6" fill="#15181d" stroke="#3fc79a" stroke-width="1.8"/><circle cx="22" cy="9.5" r="2.6" fill="#15181d" stroke="#3fc79a" stroke-width="1.8"/>
<path d="M6.5 26.6c2.4-1.5 4.8-1.5 7.2 0s4.8 1.5 7.2 0 4.8-1.5 6.9-.1" fill="none" stroke="#8fd9ff" stroke-opacity=".7" stroke-width="1.4" stroke-linecap="round"/></g>
''' + \
        f'<text x="{x + 84}" y="{y + 55}" font-family="\'Space Grotesk\', Inter, sans-serif" font-weight="700" font-size="44" letter-spacing="-1.3" fill="var(--nw-ink)">nil<tspan fill="var(--nw-accent)">werk</tspan></text>'


def avatar(name, x, y, size, uid):
    s = (AV / f"{name}.svg").read_text()
    inner = s[s.index(">") + 1 : s.rindex("</svg>")]
    inner = inner.replace('clip-pr"', f'clip-{uid}"')  # keep clip ids unique per use
    ids = set(re.findall(r'id="([^"]+)"', inner))
    for i in ids:
        inner = inner.replace(f'id="{i}"', f'id="{i}-{uid}"').replace(f"url(#{i})", f"url(#{i}-{uid})")
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 120 120">{inner}</svg>'


def grid():
    return ('<defs><pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="var(--nw-line)" stroke-width="1.5" opacity=".55"/></pattern></defs>'
            f'<rect width="{W}" height="{H}" fill="var(--nw-bg)"/><rect width="{W}" height="{H}" fill="url(#grid)"/>')


def footer(lang, y=1316):
    return ('<line x1="72" y1="1278" x2="1008" y2="1278" stroke="var(--nw-line)" stroke-width="2"/>'
            + T(72, y, "@nilwerk · nilwerk.de", 21, "mono", 400, "var(--nw-muted)")
            + T(1008, y, FOOT[lang], 21, "mono", 400, "var(--nw-muted)", anchor="end"))


def eng_block(lang, text, y=1160, lines_max=4):
    ls = wrap(text, 20, 936, "mono")
    check(len(ls) <= lines_max, f"engineer layer too long ({len(ls)} lines): {text[:50]}")
    label = "FOR ENGINEERS" if lang == "en" else "FÜR INGENIEURE"
    return T(72, y, label, 20, "mono", 600, "var(--nw-accent)", ls=1.5) + "\n" + lines_block(72, y + 28, ls, 20, 24, "mono", 400, "var(--nw-muted)")


def wrapper(body, alt, uid, theme):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(alt)}">'
           f'{grid()}{body}</svg>')
    tk = bp.tokens(theme)
    svg = re.sub(r"var\(--nw-([a-z-]+)\)", lambda m: tk[m.group(1)], svg)
    return svg


# ---------------------------------------------------------------- diary card
def diary_card(d, lang, theme="light"):
    uid = d["slug"].split("-")[0]
    kicker = d["kicker"][lang]
    b = [logo()]
    kc, kw = chip(72, 176, kicker, "var(--nw-accent)", 24, 52, "var(--nw-accent-soft)", ls=1.2)
    b.append(kc)
    # avatar + name
    b.append('<rect x="68" y="248" width="236" height="236" rx="32" fill="var(--nw-surface)" stroke="var(--nw-accent)" stroke-width="4"/>')
    b.append(avatar(d["avatar"], 72, 252, 228, uid))
    b.append(T(340, 326, d["name"], 88, "sg", 700, "var(--nw-ink)", ls=-2.5))
    rc, _ = chip(340, 352, d["role"][lang], "var(--nw-accent)", 19, 40, "none", ls=0.6)
    b.append(rc)
    ask = wrap(d["ask"][lang], 28, 660, "inter")
    b.append(lines_block(340, 432, ask, 28, 36, "inter", 400, "var(--nw-muted)"))
    # bubble
    q = wrap("\u201c" + d["quote"][lang] + "\u201d" if lang == "en" else "\u201e" + d["quote"][lang] + "\u201c", 34, 860, "sg")
    check(len(q) <= 4, f"quote too long ({len(q)} lines) {d['name']} {lang}")
    bh = len(q) * 44 + 74
    by = 520
    b.append(f'<rect x="72" y="{by}" width="936" height="{bh}" rx="30" fill="var(--nw-surface)" stroke="var(--nw-accent)" stroke-width="3"/>')
    b.append(f'<path d="M110 {by}L136 {by - 34}L180 {by}Z" fill="var(--nw-surface)" stroke="var(--nw-accent)" stroke-width="3" stroke-linejoin="round"/>')
    b.append(f'<line x1="114" y1="{by}" x2="176" y2="{by}" stroke="var(--nw-surface)" stroke-width="6"/>')
    b.append(lines_block(104, by + 56, q, 34, 44, "sg", 500, "var(--nw-ink)"))
    pv = "PERSONA VOICE · WRITTEN FROM THE EVIDENCE" if lang == "en" else "PERSONA-STIMME · AUS DEN BELEGEN GESCHRIEBEN"
    b.append(T(1008 - 24, by + bh - 14, pv, 15, "mono", 400, "var(--nw-muted)", anchor="end", ls=0.6))
    # achievement panel
    ay = by + bh + 22
    ah = 1066 - ay
    b.append(f'<rect x="72" y="{ay}" width="936" height="{ah}" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
    b.append(f'<rect x="72" y="{ay}" width="936" height="10" rx="5" fill="var(--nw-accent)"/>')
    lab = "ACHIEVEMENT OF THE DAY" if lang == "en" else "ERFOLG DES TAGES"
    b.append(T(100, ay + 50, lab, 22, "mono", 600, "var(--nw-accent)", ls=1))
    for fs in (34, 32, 30, 29, 28, 27):
        al = wrap(d["ach"][lang], fs, 880, "inter")
        lh = round(fs * 1.34)
        avail = (ah - 92 - 22) // lh + 1
        if len(al) <= avail:
            break
    check(len(al) <= avail, f"achievement too long ({len(al)} > {avail}) {d['name']} {lang}")
    b.append(lines_block(100, ay + 96, al, fs, lh, "inter", 400, "var(--nw-ink)"))
    # status + engineers
    sc, _ = chip(72, 1086, d["status"][lang], "var(--nw-warn)", 20, 44, "none")
    b.append(sc)
    b.append(eng_block(lang, d["eng"][lang], 1164, 4))
    b.append(footer(lang))
    alt = f"{d['name']}, AI agent, {d['role']['en'].split(' · ')[0].lower()}: {d['ach']['en']}"
    return wrapper("\n".join(b), alt, uid, theme)


# ---------------------------------------------------------------- then vs now: sensor pins
def pins_chip(cx, cy, left, right, color, rows, pitch=70, bw=130):
    """left/right: list of (num, label, flag) top to bottom. flag True = highlighted in `color`."""
    h = rows * pitch
    out = [f'<rect x="{cx - bw // 2}" y="{cy - h // 2}" width="{bw}" height="{h}" rx="14" fill="var(--nw-ink)"/>',
           f'<circle cx="{cx - bw // 2 + 22}" cy="{cy - h // 2 + 22}" r="7" fill="var(--nw-surface)"/>']
    for side, pins in (("l", left), ("r", right)):
        for i, (num, lab, flag) in enumerate(pins):
            py = cy - h // 2 + pitch // 2 + i * pitch
            if side == "l":
                x0, x1 = cx - bw // 2 - 30, cx - bw // 2
                out.append(f'<rect x="{x0}" y="{py - 8}" width="30" height="16" rx="3" fill="{color if flag else "var(--nw-muted)"}"/>')
                out.append(T(x0 - 10, py + 8, f"{num} {lab}", 22, "mono", 600, color if flag else "var(--nw-muted)", anchor="end"))
            else:
                x0 = cx + bw // 2
                out.append(f'<rect x="{x0}" y="{py - 8}" width="30" height="16" rx="3" fill="{color if flag else "var(--nw-muted)"}"/>')
                out.append(T(x0 + 40, py + 8, f"{lab} {num}", 22, "mono", 600, color if flag else "var(--nw-muted)"))
    return "\n".join(out)


def thenvsnow(lang, theme="light"):
    en = lang == "en"
    b = [logo()]
    kc, _ = chip(72, 176, "THEN VS NOW · PIN MAP" if en else "DAMALS VS JETZT · PINBELEGUNG", "var(--nw-accent)", 24, 52, "var(--nw-accent-soft)", ls=1.2)
    b.append(kc)
    hl = ["One sensor,", "two pin maps.", "The datasheet won."] if en else ["Ein Sensor,", "zwei Pinbelegungen.", "Das Datenblatt gewann."]
    b.append(T(72, 330, hl[0], 84, "sg", 700, "var(--nw-ink)", ls=-2.2))
    b.append(T(72, 420, hl[1], 84, "sg", 700, "var(--nw-ink)", ls=-2.2))
    b.append(T(72, 510, hl[2], 84, "sg", 700, "var(--nw-accent)", ls=-2.2))
    intro = ("Emil's first sketch of the humidity sensor had the wrong pins. A reviewing agent compared it with the datasheet."
             if en else "Emils erste Skizze des Feuchtesensors hatte falsche Pins. Ein prüfender Agent verglich sie mit dem Datenblatt.")
    b.append(lines_block(72, 570, wrap(intro, 30, 936, "inter"), 30, 40, "inter", 400, "var(--nw-muted)"))
    # tiles
    for x, col, lab, in ((72, "var(--nw-warn)", "THEN · FIRST DRAFT" if en else "DAMALS · ERSTER ENTWURF"), (552, "var(--nw-accent)", "NOW · PER DATASHEET" if en else "JETZT · LAUT DATENBLATT")):
        b.append(f'<rect x="{x}" y="670" width="456" height="400" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
        b.append(f'<rect x="{x}" y="670" width="456" height="10" rx="5" fill="{col}"/>')
        b.append(T(x + 28, 722, lab, 22, "mono", 600, col, ls=1))
    wc = "var(--nw-warn)"
    ac = "var(--nw-accent)"
    b.append(pins_chip(72 + 228, 860, [(1, "SDA", True), (2, "GND", True)], [(4, "SCL", True), (3, "VDD", True)], wc, 2))
    b.append(T(72 + 228, 1006, "4-pin sketch" if en else "4-Pin-Skizze", 22, "inter", 400, "var(--nw-muted)", anchor="middle"))
    b.append(T(72 + 228, 1040, "all four wrong" if en else "alle vier falsch", 22, "inter", 600, wc, anchor="middle"))
    b.append(pins_chip(552 + 228, 860, [(1, "NC", False), (2, "VDD", True), (3, "SCL", True)], [(6, "NC", False), (5, "GND", True), (4, "SDA", True)], ac, 3, 66))
    b.append(T(552 + 228, 1006, "6-pin DFN" if en else "6-Pin-DFN", 22, "inter", 400, "var(--nw-muted)", anchor="middle"))
    b.append(T(552 + 228, 1040, "as the maker says" if en else "wie der Hersteller es sagt", 22, "inter", 600, ac, anchor="middle"))
    sc, _ = chip(72, 1092, "REVIEW FINDING · FIXED · NO BOARD YET" if en else "PRÜFBEFUND · BEHOBEN · NOCH KEINE PLATINE", "var(--nw-warn)", 20, 44)
    b.append(sc)
    eng = ("Source: architect review of the schematic PR, 8 Nov. The check script now asserts the map; QA closed it from the artefact, not the datasheet. Footprint still to draw."
           if en else "Quelle: Architektenprüfung des Schaltplan-PR, 8. Nov. Das Prüfskript fordert die Belegung jetzt ein; QA hat den Fund anhand der Datei geschlossen, nicht anhand des Datenblatts. Footprint noch zu zeichnen.")
    b.append(eng_block(lang, eng, 1180, 3))
    b.append(footer(lang))
    return wrapper("\n".join(b), "Then versus now: the humidity sensor drawn with 4 wrong pins in the first draft, and with the 6-pin map from its datasheet in the fixed schematic.", "tvn", theme)


# ---------------------------------------------------------------- progress tracker
def tracker(lang, theme="light"):
    en = lang == "en"
    rows = [  # avatar, name, piece EN/DE, proof EN/DE, built, reviewed, tested, merged  (PR states of 8 Nov)
        ("pcb", "Emil", ("Circuit schematic", "Schaltplan"), ("netlist check + ERC exit 0 in CI", "Netzlistenprüfung + ERC Exit 0 in CI"), 1, 1, 1, 1),
        ("fullstack", "Leo", ("App account screens", "App-Konto-Screens"), ("54 tests pass", "54 Tests grün"), 1, 1, 1, 1),
        ("cloud-ai", "Sana", ("Cloud claim + ingest", "Cloud: Koppeln + Annahme"), ("13 tests, 26 of 26 mutants", "13 Tests, 26 von 26 Mutanten"), 1, 1, 1, 0),
        ("mechanical", "Yara", ("Battery bay (3D)", "Akku-Aussparung (3D)"), ("22 tests pass", "22 Tests grün"), 1, 1, 1, 0),
        ("firmware", "Mira", ("Edge-AI model", "Edge-KI-Modell"), ("134 tests; target missed", "134 Tests; Ziel verfehlt"), 1, 1, 1, 0),
    ]
    b = [logo()]
    kc, _ = chip(72, 176, "PROGRESS · SUN 8 NOV" if en else "FORTSCHRITT · SO 8. NOV", "var(--nw-accent)", 24, 52, "var(--nw-accent-soft)", ls=1.2)
    b.append(kc)
    hl = ["Five builds.", "Two merged.", "Review comes first."] if en else ["Fünf Arbeitspakete.", "Zwei übernommen.", "Erst die Prüfung."]
    sizes = (80, 80, 80) if en else (76, 76, 60)
    for i, (t, col) in enumerate(zip(hl, ("var(--nw-ink)", "var(--nw-ink)", "var(--nw-accent)"))):
        b.append(T(72, 310 + i * 82, t, sizes[i], "sg", 700, col, ls=-2.4))
    intro = ("These five were checked by a second agent and tested by a third. Merging is the founder's call."
             if en else "Diese fünf prüfte ein zweiter Agent, ein dritter testete. Die Übernahme entscheidet der Gründer.")
    b.append(lines_block(72, 540, wrap(intro, 30, 936, "inter"), 30, 40, "inter", 400, "var(--nw-muted)"))
    # grid
    top = 620
    cols = [(640, "BUILT" if en else "GEBAUT"), (738, "REVIEW" if en else "PRÜFUNG"), (836, "TEST"), (934, "MERGED" if en else "GEMERGT")]
    b.append(f'<rect x="72" y="{top}" width="936" height="{70 + 5 * 66}" rx="18" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
    for x, lab in cols:
        b.append(T(x, top + 40, lab, 17, "mono", 600, "var(--nw-muted)", anchor="middle", ls=0.4))
    for i, (av, name, piece, proof, *st) in enumerate(rows):
        y = top + 70 + i * 66
        b.append(f'<line x1="96" y1="{y}" x2="984" y2="{y}" stroke="var(--nw-line)" stroke-width="1.5"/>')
        b.append(avatar(av, 92, y + 8, 50, f"tr{i}"))
        b.append(T(156, y + 31, f"{name}: {piece[0 if en else 1]}", 23, "inter", 600, "var(--nw-ink)"))
        b.append(T(156, y + 52, proof[0 if en else 1], 17, "mono", 400, "var(--nw-muted)"))
        for (x, _), v in zip(cols, st):
            cy = y + 33
            if v:
                b.append(f'<circle cx="{x}" cy="{cy}" r="19" fill="var(--nw-accent)"/><path d="M{x - 9} {cy}l6 7l12 -14" fill="none" stroke="var(--nw-accent-ink)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
            else:
                b.append(f'<circle cx="{x}" cy="{cy}" r="17" fill="none" stroke="var(--nw-warn)" stroke-width="3" stroke-dasharray="6 5"/>')
    ny = top + 70 + 5 * 66 + 44
    note = ("Also merged on 8 Nov: Kai's pipeline fix, so the circuit check can run at all. Three builds wait for the founder." if en else
            "Ebenfalls übernommen: Kais Pipeline-Fix, damit die Schaltungsprüfung läuft. Drei warten auf den Gründer.")
    b.append(lines_block(72, ny, wrap(note, 26, 936, "inter"), 26, 34, "inter", 400, "var(--nw-ink)"))
    sc, _ = chip(72, 1124, f"COUNTED FROM PR STATE · AS OF 8 NOV {ASOF}" if en else f"AUS PR-STATUS GEZÄHLT · STAND 8. NOV {ASOF}", "var(--nw-warn)", 20, 44)
    b.append(sc)
    eng = ("Review = architect verdict (approved, mostly with conditions), test = QA verdict (pass, mostly with notes), per PR comments of 8 Nov. Test counts are agent-run, QA re-ran them. Recount on the day of posting."
           if en else "Prüfung = Architektenurteil (freigegeben, meist mit Auflagen), Test = QA-Urteil (bestanden, meist mit Hinweisen), laut PR-Kommentaren vom 8. Nov. Testzahlen vom Agenten, QA wiederholte sie. Am Tag des Postens neu zählen.")
    b.append(eng_block(lang, eng, 1196, 3))
    b.append(footer(lang))
    svg = wrapper("\n".join(b), "Progress tracker as of 8 November: five builds each reviewed and tested by AI agents; two of five merged.", "trk", theme)
    return svg


# ---------------------------------------------------------------- real screenshots of the app
def screens(lang, theme="light"):
    en = lang == "en"
    b = [logo()]
    kc, _ = chip(72, 176, "REAL SCREENSHOTS · LEO'S APP" if en else "ECHTE SCREENSHOTS · LEOS APP", "var(--nw-accent)", 24, 52, "var(--nw-accent-soft)", ls=1.2)
    b.append(kc)
    hl = ["The app already", "has a front door."] if en else ["Die App hat schon", "eine Haustür."]
    b.append(T(72, 330, hl[0], 84, "sg", 700, "var(--nw-ink)", ls=-2.2))
    b.append(T(72, 420, hl[1], 84, "sg", 700, "var(--nw-accent)", ls=-2.2))
    intro = ("Welcome, sign-up with plain error messages, profile. A web build, not yet on a phone." if en else
             "Willkommen, Registrierung mit klaren Fehlermeldungen, Profil. Eine Web-Version, noch nicht auf dem Handy.")
    b.append(lines_block(72, 480, wrap(intro, 30, 936, "inter"), 30, 40, "inter", 400, "var(--nw-muted)"))
    files = ["light-01-welcome.png", "light-02-signup-errors.png", "dark-04-profile.png"]
    labs = (["WELCOME", "SIGN-UP ERRORS", "PROFILE (DARK)"] if en else ["WILLKOMMEN", "FEHLERMELDUNGEN", "PROFIL (DUNKEL)"])
    pw, ph = 259, 560  # 780x1688 scaled
    x0 = 72 + (936 - 3 * pw - 2 * 36) // 2
    for i, f in enumerate(files):
        x = x0 + i * (pw + 36)
        b.append(f'<rect x="{x - 6}" y="{560 - 6}" width="{pw + 12}" height="{ph + 12}" rx="30" fill="var(--nw-ink)"/>')
        b.append(f'<clipPath id="cp{i}"><rect x="{x}" y="560" width="{pw}" height="{ph}" rx="24"/></clipPath>')
        b.append(f'<image x="{x}" y="560" width="{pw}" height="{ph}" preserveAspectRatio="xMidYMid slice" clip-path="url(#cp{i})" href="@@SHOT:{f}@@"/>')
        b.append(T(x + pw // 2, 560 + ph + 40, labs[i], 17, "mono", 600, "var(--nw-muted)", anchor="middle", ls=0.6))
    stat = "WEB BUILD · STAND-IN BACKEND · NOT A PHONE" if en else "WEB-VERSION · PLATZHALTER-SERVER · KEIN HANDY"
    c2, _ = chip(72, 1182, stat, "var(--nw-warn)", 19, 36)
    b.append(c2)
    eng = "Expo web export at 390 px against an in-memory mock; no real Supabase." if en else "Expo-Web-Export, 390 px, Mock-Server; App-Texte noch Englisch."
    b.append(T(72, 1250, eng, 20, "mono", 400, "var(--nw-muted)"))
    b.append(footer(lang))
    return wrapper("\n".join(b), "Three real screenshots of the Nilwerk plant app web build: welcome, sign-up with error messages, profile in dark theme. Stand-in backend, not on a phone.", "scr", theme)


# ---------------------------------------------------------------- plant in the real world (illustration)
def plant_scene(lang, theme="light"):
    en = lang == "en"
    b = [logo()]
    kc, _ = chip(72, 176, "WHERE THIS IS HEADING · ILLUSTRATION" if en else "WOHIN ES GEHT · ILLUSTRATION", "var(--nw-accent)", 24, 52, "var(--nw-accent-soft)", ls=1.2)
    b.append(kc)
    hl = ["A plant, a sensor,", "a phone."] if en else ["Eine Pflanze, ein", "Sensor, ein Handy."]
    b.append(T(72, 330, hl[0], 84, "sg", 700, "var(--nw-ink)", ls=-2.2))
    b.append(T(72, 420, hl[1], 84, "sg", 700, "var(--nw-accent)", ls=-2.2))
    intro = ("The idea in one picture. This is a drawing: no prototype is running yet." if en else "Die Idee in einem Bild. Das ist eine Zeichnung: Noch läuft kein Prototyp.")
    b.append(lines_block(72, 480, wrap(intro, 30, 936, "inter"), 30, 40, "inter", 400, "var(--nw-muted)"))
    # scene frame
    b.append('<rect x="72" y="560" width="936" height="520" rx="22" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
    b.append('<rect x="110" y="590" width="250" height="260" rx="10" fill="var(--nw-accent-soft)" stroke="var(--nw-ink)" stroke-width="5"/>'
             '<line x1="235" y1="590" x2="235" y2="850" stroke="var(--nw-ink)" stroke-width="5"/><line x1="110" y1="720" x2="360" y2="720" stroke="var(--nw-ink)" stroke-width="5"/>'
             '<circle cx="300" cy="650" r="26" fill="var(--nw-warn)" opacity=".35"/>')
    b.append('<rect x="72" y="960" width="936" height="24" fill="var(--nw-ink)"/><rect x="120" y="984" width="20" height="96" fill="var(--nw-ink)"/><rect x="940" y="984" width="20" height="96" fill="var(--nw-ink)"/>')
    # pot
    b.append('<path d="M470 800h200l-26 160h-148Z" fill="var(--nw-warn)"/><rect x="460" y="786" width="220" height="30" rx="8" fill="var(--nw-warn)"/>'
             '<rect x="460" y="786" width="220" height="30" rx="8" fill="none" stroke="var(--nw-ink)" stroke-width="3"/>')
    b.append('<path d="M570 790C570 700 566 650 560 610" fill="none" stroke="var(--nw-accent)" stroke-width="9" stroke-linecap="round"/>'
             '<path d="M566 700C510 690 484 650 486 616C540 616 570 650 566 700Z" fill="var(--nw-accent)"/>'
             '<path d="M572 664C630 660 662 624 660 590C602 592 570 624 572 664Z" fill="var(--nw-accent)"/>'
             '<path d="M562 626C530 610 524 580 534 556C566 568 574 596 562 626Z" fill="var(--nw-accent)" opacity=".8"/>')
    # sensor probe in the soil and the small device on the rim
    b.append('<rect x="606" y="800" width="14" height="74" rx="4" fill="var(--nw-ink)"/><rect x="598" y="760" width="30" height="46" rx="8" fill="var(--nw-ink)"/>'
             '<circle cx="613" cy="776" r="5" fill="#3fc79a"/>')
    b.append('<path d="M640 770c26 0 40 -22 76 -22" fill="none" stroke="var(--nw-ink)" stroke-width="3" stroke-linecap="round"/>'
             '<path d="M700 740c14 -10 30 -10 44 0M690 722c22 -16 46 -16 68 0" fill="none" stroke="var(--nw-accent)" stroke-width="5" stroke-linecap="round"/>')
    # phone
    b.append('<rect x="790" y="640" width="150" height="300" rx="24" fill="var(--nw-ink)"/><rect x="800" y="662" width="130" height="256" rx="12" fill="var(--nw-surface)"/>'
             '<path d="M850 800c0 -40 -4 -60 -10 -80c34 8 48 36 44 74Z" fill="var(--nw-accent)"/><rect x="814" y="836" width="102" height="12" rx="6" fill="var(--nw-line)"/><rect x="814" y="860" width="70" height="12" rx="6" fill="var(--nw-line)"/>')
    # Poppy bubble
    b.append('<rect x="100" y="992" width="80" height="80" rx="14" fill="var(--nw-surface)"/>')
    b.append(avatar("pr-social", 100, 992, 80, "pl"))
    msg = ("This is a drawing. The real photo comes once the first board is built." if en else "Das ist eine Zeichnung. Das echte Foto kommt, sobald die erste Platine gebaut ist.")
    ml = wrap(msg, 22, 560, "inter")
    b.append(f'<rect x="196" y="994" width="620" height="{len(ml) * 28 + 24}" rx="16" fill="var(--nw-bg)" stroke="var(--nw-accent)" stroke-width="3"/>')
    b.append(lines_block(214, 1026, ml, 22, 28, "inter", 600, "var(--nw-ink)"))
    chp, _ = chip(72, 1106, "ILLUSTRATION, NOT A PHOTO · NO PROTOTYPE RUNNING YET" if en else "ILLUSTRATION, KEIN FOTO · NOCH KEIN PROTOTYP IM BETRIEB", "var(--nw-warn)", 20, 44, dash=True)
    b.append(chp)
    eng = ("Intended chain: soil sensor, ESP32-class board, Wi-Fi, cloud, app. Battery life stays 'simulated' until a bench test exists. The drawing shows no real reading and no real device."
           if en else "Geplante Kette: Bodensensor, Board der ESP32-Klasse, WLAN, Cloud, App. Akkulaufzeit bleibt „simuliert“, bis ein Bench-Test existiert. Die Zeichnung zeigt keinen echten Messwert und kein echtes Gerät.")
    b.append(eng_block(lang, eng, 1196, 3))
    b.append(footer(lang))
    return wrapper("\n".join(b), "Illustration, not a photo: a potted plant with a soil sensor, a small radio wave and a phone showing a plant. No prototype is running yet.", "pls", theme)


# ---------------------------------------------------------------- from the virtual office (FICTION)
def office(lang, theme="dark"):
    en = lang == "en"
    b = [logo()]
    kc, _ = chip(72, 176, "FROM THE VIRTUAL OFFICE" if en else "AUS DEM VIRTUELLEN BÜRO", "var(--nw-accent)", 24, 52, "var(--nw-accent-soft)", ls=1.2)
    b.append(kc)
    b.append(f'<rect x="72" y="244" width="936" height="52" rx="8" fill="none" stroke="var(--nw-warn)" stroke-width="3" stroke-dasharray="12 8"/>')
    b.append(T(540, 279, "FICTION · IMAGINED BY OUR AGENTS · NOT A REAL EVENT" if en else "FIKTION · VON UNSEREN AGENTEN ERFUNDEN · KEIN ECHTES EREIGNIS", 22, "mono", 600, "var(--nw-warn)", anchor="middle", ls=1))
    hl = ["The kettle failed", "its review."] if en else ["Der Wasserkocher", "fiel durch die Prüfung."]
    b.append(T(72, 400, hl[0], 84, "sg", 700, "var(--nw-ink)", ls=-2.2))
    b.append(T(72, 490, hl[1], 84 if en else 66, "sg", 700, "var(--nw-accent)", ls=-2.2))
    # room
    b.append('<rect x="72" y="540" width="936" height="440" rx="22" fill="var(--nw-surface)" stroke="var(--nw-line)" stroke-width="2"/>')
    b.append('<rect x="72" y="900" width="936" height="80" fill="var(--nw-line)" opacity=".5"/>')
    b.append('<rect x="760" y="580" width="200" height="140" rx="8" fill="var(--nw-accent-soft)" stroke="var(--nw-ink)" stroke-width="4"/><line x1="860" y1="580" x2="860" y2="720" stroke="var(--nw-ink)" stroke-width="4"/>'
             '<rect x="110" y="610" width="150" height="100" rx="6" fill="var(--nw-bg)" stroke="var(--nw-muted)" stroke-width="3"/><path d="M126 690l30-30 24 20 28-40 36 50" fill="none" stroke="var(--nw-accent)" stroke-width="4" stroke-linejoin="round"/>')
    # Ines at left, kettle at right
    b.append(avatar("qa", 110, 735, 200, "of1"))
    b.append('<path d="M650 900c-6-70 20-120 90-120s96 50 90 120Z" fill="var(--nw-muted)"/><rect x="660" y="880" width="160" height="26" rx="8" fill="var(--nw-ink)"/>'
             '<path d="M830 830c34 -4 46 -40 22 -52" fill="none" stroke="var(--nw-muted)" stroke-width="12" stroke-linecap="round"/><path d="M652 830l-34 -20" stroke="var(--nw-muted)" stroke-width="12" stroke-linecap="round"/>'
             '<circle cx="716" cy="830" r="9" fill="var(--nw-bg)"/><circle cx="760" cy="830" r="9" fill="var(--nw-bg)"/><circle cx="718" cy="832" r="4" fill="var(--nw-ink)"/><circle cx="762" cy="832" r="4" fill="var(--nw-ink)"/>'
             '<path d="M722 858q18 12 36 0" fill="none" stroke="var(--nw-bg)" stroke-width="4" stroke-linecap="round"/><rect x="722" y="762" width="36" height="14" rx="6" fill="var(--nw-ink)"/>')
    b.append('<rect x="322" y="770" width="290" height="64" rx="16" fill="var(--nw-bg)" stroke="var(--nw-accent)" stroke-width="3"/><path d="M322 808l-14 12l30 -2Z" fill="var(--nw-bg)" stroke="var(--nw-accent)" stroke-width="3" stroke-linejoin="round"/>')
    b.append(T(342, 812, "Show me the log." if en else "Zeig mir das Log.", 28, "sg", 500, "var(--nw-ink)"))
    kt = "It boiled. Trust me." if en else "Es kochte. Vertrau mir."
    b.append('<rect x="470" y="640" width="340" height="64" rx="16" fill="var(--nw-bg)" stroke="var(--nw-warn)" stroke-width="3"/><path d="M720 704l8 40l22 -40Z" fill="var(--nw-bg)" stroke="var(--nw-warn)" stroke-width="3" stroke-linejoin="round"/>')
    b.append('<line x1="722" y1="704" x2="748" y2="704" stroke="var(--nw-bg)" stroke-width="6"/>')
    b.append(T(490, 682, kt, 28, "sg", 500, "var(--nw-ink)"))
    story = ("Ines asked the office kettle for a log. The kettle offered a feeling. Ines: \u201cThat is not a log.\u201d The kettle is now on a corrective plan. (Made up, for fun.)"
             if en else "Ines bat den Büro-Wasserkocher um ein Log. Der Wasserkocher bot ein Gefühl an. Ines: „Das ist kein Log.“ Der Wasserkocher steht jetzt unter Beobachtung. (Erfunden, zum Spaß.)")
    b.append(lines_block(72, 1030, wrap(story, 28, 936, "inter"), 28, 38, "inter", 400, "var(--nw-ink)"))
    eng = ("The only real part: our QA agent's rule is to paste real output for every check (see the team's persona sheet). No real event, result or quote here."
           if en else "Der einzige echte Teil: Die Regel unseres QA-Agenten lautet, bei jeder Prüfung die echte Ausgabe einzufügen (siehe Persona-Blatt). Hier kein echtes Ereignis, Ergebnis oder Zitat.")
    b.append(eng_block(lang, eng, 1196, 3))
    b.append(footer(lang))
    return wrapper("\n".join(b), "Fiction, imagined by our agents: Ines, the QA agent, asks the office kettle for a log. Not a real event.", "off", theme)


# ---------------------------------------------------------------- shot-list placeholder board (internal)
def shotboard(theme="light"):
    lang = "en"
    b = [logo()]
    kc, _ = chip(72, 176, "SHOT LIST · PLACEHOLDERS · INTERNAL", "var(--nw-warn)", 24, 52, "none", ls=1.2)
    b.append(kc)
    b.append(T(72, 330, "Six photos make", 84, "sg", 700, "var(--nw-ink)", ls=-2.2))
    b.append(T(72, 420, "this feed real.", 84, "sg", 700, "var(--nw-accent)", ls=-2.2))
    b.append(lines_block(72, 480, wrap("Placeholders only: each frame is replaced by a real photo or a 10-20 s clip. Details in shotlist.md.", 28, 936, "inter"), 28, 38, "inter", 400, "var(--nw-muted)"))
    frames = [("1", "BENCH", "Wide shot of the bench:", "board, laptop, tools"), ("2", "THE PLANT", "A real pot, sensor in soil,", "natural light"),
              ("3", "PCB CLOSE-UP", "Bare board or devkit,", "ruler for scale"), ("4", "3D PRINT", "Print running on the P1S,", "or the test bay"),
              ("5", "SCREEN + HAND", "The app on a real phone,", "a thumb tapping"), ("6", "THE WINDOW", "Plant on the sill, phone", "next to it, daylight")]
    fw, fh = 296, 270
    for i, (n, t, l1, l2) in enumerate(frames):
        x = 72 + (i % 3) * (fw + 24)
        y = 580 + (i // 3) * (fh + 30)
        b.append(f'<rect x="{x}" y="{y}" width="{fw}" height="{fh}" rx="16" fill="var(--nw-surface)" stroke="var(--nw-warn)" stroke-width="3" stroke-dasharray="12 8"/>')
        b.append(f'<circle cx="{x + 46}" cy="{y + 50}" r="26" fill="var(--nw-warn)"/>' + T(x + 46, y + 60, n, 28, "sg", 700, "var(--nw-accent-ink)", anchor="middle"))
        b.append(f'<path d="M{x + 120} {y + 120}h20l10 -14h40l10 14h20a8 8 0 0 1 8 8v56a8 8 0 0 1 -8 8h-100a8 8 0 0 1 -8 -8v-56a8 8 0 0 1 8 -8Z" fill="none" stroke="var(--nw-muted)" stroke-width="4" stroke-linejoin="round"/><circle cx="{x + 148}" cy="{y + 156}" r="18" fill="none" stroke="var(--nw-muted)" stroke-width="4"/>')
        b.append(T(x + 82, y + 58, t, 20, "mono", 600, "var(--nw-warn)", ls=0.6))
        b.append(T(x + 20, y + 232, l1, 19, "inter", 400, "var(--nw-ink)"))
        b.append(T(x + 20, y + 256, l2, 19, "inter", 400, "var(--nw-ink)"))
    chp, _ = chip(72, 1180, "PLACEHOLDER BOARD · NOT FOR POSTING", "var(--nw-warn)", 20, 44, dash=True)
    b.append(chp)
    b.append(footer(lang))
    return wrapper("\n".join(b), "Internal placeholder board with six dashed photo frames: bench, plant, PCB, 3D print, app on a phone, window. Not for posting.", "shot", theme)


JOBS = []


def emit(name, svg):
    OUT.mkdir(exist_ok=True)
    p = OUT / f"{name}.svg"
    p.write_text(svg, encoding="utf-8")
    JOBS.append((name, p))


def main():
    only = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--only" else None
    for date, d in DAYS.items():
        for lang in ("en", "de"):
            emit(f"{d['slug']}-{lang}", diary_card(d, lang))
    for lang in ("en", "de"):
        emit(f"extra-thenvsnow-sensor-pins-{lang}", thenvsnow(lang))
        emit(f"extra-tracker-5-builds-{lang}", tracker(lang))
        emit(f"extra-screens-leo-app-{lang}", screens(lang))
        emit(f"extra-plant-illustration-{lang}", plant_scene(lang))
        emit(f"extra-virtual-office-fiction-{lang}", office(lang))
    emit("internal-shot-list-placeholders-en", shotboard())
    jobs = []
    tmp = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "nwdiary"
    tmp.mkdir(exist_ok=True)
    for name, p in JOBS:
        if only and only not in name:
            continue
        s = p.read_text(encoding="utf-8")
        # keep the saved svg self-contained-free: real screenshots are referenced by relative path
        s_saved = re.sub(r"@@SHOT:([^@]+)@@", lambda m: "../../../items/2026-11-08_4.A2/" + m.group(1), s)
        p.write_text(s_saved, encoding="utf-8")
        s_render = re.sub(r"@@SHOT:([^@]+)@@", lambda m: "data:image/png;base64," + base64.b64encode((SHOTS / m.group(1)).read_bytes()).decode(), s)
        rp = tmp / f"{name}.svg"
        rp.write_text(s_render, encoding="utf-8")
        jobs.append((rp, OUT / f"{name}.png"))
    bp.render_png(jobs, scale=1)
    # automatic overflow check (text boxes against the margins), real fonts embedded
    fcss = bp.font_css()
    pages = []
    for rp, png in jobs:
        hp = rp.with_suffix(".html")
        hp.write_text(f"<!doctype html><meta charset=utf-8><style>{fcss}html,body{{margin:0}}svg{{display:block}}</style>" + rp.read_text(encoding="utf-8"), encoding="utf-8")
        pages.append(dict(html=str(hp), name=rp.stem))
    jf = tmp / "pages.json"
    jf.write_text(json.dumps(pages))
    env = dict(os.environ)
    env.setdefault("NODE_PATH", "/opt/node-tools/node_modules")
    r = subprocess.run(["node", str(HERE / "check_bbox.js"), str(jf)], env=env)
    print("layout warnings:", len(PROBLEMS), "| bbox check exit:", r.returncode)


if __name__ == "__main__":
    main()
