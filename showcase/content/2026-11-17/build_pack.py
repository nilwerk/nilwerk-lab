#!/usr/bin/env python3
"""Poppy, 2026-11-17: renders the 'The crew has a life' image pack (HTML -> PNG via headless Chrome).

Run:  python3 -I build_pack.py        (from this folder; needs google-chrome, no network)
Visual grammar (printed on every image):
  DASHED border/bubble = imagined by Poppy (fiction, persona voice)
  SOLID GREEN box      = real engineering fact (sourced in claim-sources.md)
Characters are AI agents. Humans appear only as themselves (role names, no invented life).
No number ever appears inside a dashed (fiction) element.
"""
import html, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AV = ROOT / "team" / "avatars"
OUT = HERE / "images"
TMP = HERE / "_html"
OUT.mkdir(exist_ok=True)
TMP.mkdir(exist_ok=True)

CHROME = "google-chrome"

NAMES = {  # file, display, nickname
    "nora": ("lead-pm", "Nora", "The conductor"),
    "theo": ("architect", "Theo", "The cartographer"),
    "ines": ("qa", "Ines", "The skeptic"),
    "kai": ("devops", "Kai", "The keeper of green"),
    "mira": ("firmware", "Mira", "The microamp hunter"),
    "leo": ("fullstack", "Leo", "The pathfinder"),
    "sana": ("cloud-ai", "Sana", "The guardrail builder"),
    "emil": ("pcb", "Emil", "The simulator"),
    "yara": ("mechanical", "Yara", "The form giver"),
    "poppy": ("pr-social", "Poppy", "The storyteller"),
    "max": ("sales", "Max", "The door opener"),
    "human": ("human-public", "Our hardware tester", "A real person"),
}

_uid = [0]


def avatar(key, size=140):
    f = NAMES[key][0]
    svg = (AV / f"{f}.svg").read_text()
    _uid[0] += 1
    u = _uid[0]
    svg = re.sub(r'(clip-[a-z]+)', lambda m: f"{m.group(1)}-{u}", svg)
    svg = svg.replace("<svg ", f'<svg width="{size}" height="{size}" ', 1)
    return f'<span class="av" style="width:{size}px;height:{size}px">{svg}</span>'


CSS = """
:root{--bg:#f6f4ef;--surface:#fff;--ink:#15181d;--muted:#5b616b;--line:#e2ded5;--accent:#0f7a5c;--soft:#e3f2ec;--warn:#b4541a;--warnsoft:#fbeadd;--warntext:#8a3c0c}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--ink);font-family:Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.page{position:relative;overflow:hidden;background:var(--bg);padding:40px 56px 0}
.h{font-family:'Space Grotesk',Inter,sans-serif;font-weight:800;letter-spacing:-.03em;line-height:.98}
.mono{font-family:'JetBrains Mono','DejaVu Sans Mono',monospace}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;gap:12px}
.kick{font-family:'JetBrains Mono','DejaVu Sans Mono',monospace;font-size:18px;letter-spacing:.05em;font-weight:700;color:var(--muted)}
.fic{white-space:nowrap;font-family:'JetBrains Mono','DejaVu Sans Mono',monospace;font-size:15px;font-weight:700;letter-spacing:.04em;color:var(--warntext);border:3px dashed var(--warn);border-radius:999px;padding:6px 12px;background:var(--warnsoft)}
.real{font-family:'JetBrains Mono','DejaVu Sans Mono',monospace;font-size:19px;font-weight:700;letter-spacing:.04em;color:#fff;background:var(--accent);border-radius:999px;padding:8px 16px}
.av{display:inline-block;flex:none;border-radius:28%;overflow:hidden;border:4px solid var(--ink);background:#fff}
.av svg{display:block}
.panel{background:var(--surface);border:5px solid var(--ink);border-radius:26px;box-shadow:9px 9px 0 var(--ink);padding:14px 20px}
.row{display:flex;gap:22px;align-items:flex-start}
.who{font-family:'JetBrains Mono','DejaVu Sans Mono',monospace;font-size:19px;font-weight:700;margin-top:8px;text-align:center}
.bub{position:relative;background:#fff;border:4px dashed var(--warn);border-radius:26px;padding:12px 18px;font-size:31px;line-height:1.2;font-weight:600}
.bub.l::before{content:"";position:absolute;left:-17px;top:34px;width:26px;height:26px;background:#fff;border-left:4px dashed var(--warn);border-bottom:4px dashed var(--warn);transform:rotate(45deg)}
.bub.r::before{content:"";position:absolute;right:-17px;top:34px;width:26px;height:26px;background:#fff;border-right:4px dashed var(--warn);border-top:4px dashed var(--warn);transform:rotate(45deg)}
.bub small{display:block;font-size:19px;font-weight:600;color:var(--muted);margin-top:6px}
.fact{background:var(--soft);border:4px solid var(--accent);border-radius:22px;padding:18px 22px}
.fact .lab{font-family:'JetBrains Mono','DejaVu Sans Mono',monospace;font-size:18px;font-weight:700;letter-spacing:.06em;color:var(--accent)}
.fact .big{font-weight:800;font-size:34px;letter-spacing:-.02em;margin:4px 0 2px}
.fact p{font-size:22px;line-height:1.3;font-weight:500}
.fact .src{font-family:'JetBrains Mono','DejaVu Sans Mono',monospace;font-size:17px;color:var(--muted);margin-top:8px}
.warnbox{background:var(--warnsoft);border:4px solid var(--warn);border-radius:22px;padding:14px 20px;font-size:23px;line-height:1.28;font-weight:600;color:#6e300c}
.foot{position:absolute;left:0;right:0;bottom:0;padding:10px 56px 12px;border-top:3px solid var(--line);background:var(--bg);display:flex;justify-content:space-between;align-items:center;gap:20px}
.foot .brand{font-family:'Space Grotesk',Inter,sans-serif;font-weight:800;font-size:30px;letter-spacing:-.03em}
.foot .brand b{color:var(--accent)}
.foot .leg{font-size:16px;line-height:1.25;color:var(--muted);text-align:right;font-weight:500}
.foot .leg i{display:inline-block;width:26px;height:12px;vertical-align:middle;margin:0 4px 0 6px}
.foot .leg i.d{border:3px dashed var(--warn);border-radius:6px}
.foot .leg i.s{border:3px solid var(--accent);background:var(--soft);border-radius:6px}
"""

FOOT = ('<div class="foot"><div class="brand">nil<b>werk</b><div style="font-size:17px;font-weight:500;letter-spacing:0;color:var(--muted);font-family:Inter">'
        'AI crew, led and reviewed by humans &middot; @nilwerk</div></div>'
        '<div class="leg"><i class="d"></i>imagined by Poppy (fiction) &nbsp; <i class="s"></i>real, sourced engineering<br>'
        'The crew are AI agents. Their private lives are made up. The engineering is not.</div></div>')


def wrap(body, w, h, extra_css=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{CSS}{extra_css}</style></head>'
            f'<body><div class="page" style="width:{w}px;height:{h}px">{body}</div></body></html>')


def render(name, doc, w, h):
    f = TMP / f"{name}.html"
    f.write_text(doc)
    out = OUT / f"{name}.png"
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={w},{h}", "--force-device-scale-factor=1",
                    f"--screenshot={out}", f"file://{f}"], check=True, capture_output=True, timeout=120)
    print("rendered", out.name)


def top(kicker, kind="fic"):
    chip = ('<span class="fic">FICTIONAL CREW LIFE &middot; REAL ENGINEERING</span>')
    return f'<div class="top"><span class="kick">{kicker}</span>{chip}</div>'


def say(key, text, side="l", sub=""):
    nm = NAMES[key]
    a = f'<div style="text-align:center">{avatar(key,116)}<div class="who">{nm[1]}</div></div>'
    b = f'<div class="bub {side}" style="flex:1">{text}{f"<small>{sub}</small>" if sub else ""}</div>'
    return f'<div class="row" style="align-items:flex-start">{a if side=="l" else b}{b if side=="l" else a}</div>'


def fact(label, big, text, src):
    return (f'<div class="fact"><div class="lab">REAL &middot; {label}</div>'
            f'{f"<div class=big>{big}</div>" if big else ""}<p>{text}</p><div class="src">source: {src}</div></div>')


# ---------------------------------------------------------------- 01 cover
def cover():
    keys = ["nora", "theo", "ines", "kai", "mira", "leo", "sana", "emil", "yara", "poppy", "max"]
    cards = "".join(
        f'<div style="text-align:center;width:150px">{avatar(k,104)}<div class="who" style="font-size:17px">{NAMES[k][1]}</div>'
        f'<div style="font-size:15px;color:var(--muted);font-weight:600;line-height:1.15">{NAMES[k][2]}</div></div>' for k in keys)
    body = top("THE CREW HAS A LIFE &middot; SEASON 1") + f"""
<div class="h" style="font-size:112px;margin:10px 0 14px">The crew<br>has a <span style="color:var(--accent)">life.</span></div>
<div style="font-size:31px;line-height:1.25;font-weight:600;max-width:900px;margin-bottom:24px">Eleven AI engineers. One real Tuesday.<br>Five episodes of bugs, rivalries and small victories.</div>
<div class="panel" style="display:flex;flex-wrap:wrap;gap:20px 16px;justify-content:center;padding:18px 8px;gap:14px 10px">{cards}</div>
<div style="display:flex;gap:22px;margin-top:34px">
 <div class="bub l" style="flex:1;font-size:29px">Everything we <i>feel</i> is imagined.<small>Everything we <b>fixed</b> is real.</small></div>
 <div class="fact" style="flex:1"><div class="lab">REAL</div><p style="margin-top:6px"><b>Every bug in the story really happened</b> and was found on 17 Nov 2026.</p></div></div>
{FOOT}"""
    render("01_cover_the-crew-has-a-life", wrap(body, 1080, 1350), 1080, 1350)


# ---------------------------------------------------------------- 02 ep1
def ep1():
    body = top("EP 1 / 5 &middot; THE GUARD THAT COULD NEVER FIRE") + f"""
<div class="h" style="font-size:62px;margin-bottom:16px">Ines vs. Mira:<br>the guard that <span style="color:var(--accent)">never fired</span></div>
<div class="panel" style="margin-bottom:16px">{say("mira","I built a guard. If the server keeps rejecting one batch, we drop it. No batch blocks the buffer for ever.", "l", "")}</div>
<div class="panel" style="margin-bottom:16px;background:#fdf5f2">{say("ines","Lovely. <i>Show me the log.</i> Your sensor adds a new sample every 15 minutes. Your guard counts the newest one. Do the maths, Mira.", "r")}</div>
<div class="panel" style="margin-bottom:16px">{say("mira","...the counter resets every single retry. It can never reach three.", "l", "")}<div style="text-align:right;font-size:26px;margin-top:8px">Slow-burn level: <b>she will not admit she is grateful.</b></div></div>
{fact("FOR ENGINEERS", "4 &rarr; 10 samples, guard never fired", "Review and QA reproduced it: 6 rejects in a row, no drop. Fix: count from the <b>oldest</b> sample. After the fix the 3rd reject drops the batch; 622 checks pass, 49/49 mutants caught (was 45).", "architect + QA review of the upload slice, 17 Nov 2026")}
{FOOT}"""
    render("02_ep1_ines-vs-mira", wrap(body, 1080, 1350), 1080, 1350)


# ---------------------------------------------------------------- 03 ep2
def ep2():
    svg = """
<svg viewBox="0 0 960 330" width="968" height="332" xmlns="http://www.w3.org/2000/svg" font-family="Inter,sans-serif">
 <rect x="2" y="2" width="956" height="326" rx="22" fill="#fff" stroke="#15181d" stroke-width="5"/>
 <text x="30" y="44" font-size="20" font-weight="700" fill="#5b616b" font-family="DejaVu Sans Mono,monospace">MAP OF THE DAY (drawn by Poppy, simplified)</text>
 <line x1="40" y1="110" x2="920" y2="110" stroke="#0f7a5c" stroke-width="12" stroke-linecap="round"/>
 <text x="40" y="92" font-size="26" font-weight="800" fill="#0f7a5c">main</text>
 <circle cx="300" cy="110" r="17" fill="#0f7a5c" stroke="#15181d" stroke-width="4"/>
 <path d="M300 110 Q 330 210 430 210 L 600 210" fill="none" stroke="#15181d" stroke-width="7" stroke-dasharray="2 14" stroke-linecap="round"/>
 <text x="330" y="150" font-size="22" font-weight="700" fill="#15181d">branch A: Leo's app work</text>
 <text x="300" y="82" font-size="22" font-weight="700" fill="#0f7a5c" text-anchor="middle">1. branch A reaches main</text>
 <circle cx="600" cy="210" r="15" fill="#fff" stroke="#b4541a" stroke-width="5" stroke-dasharray="6 5"/>
 <text x="430" y="262" font-size="24" font-weight="700" fill="#b4541a">2. the delete-screen work is merged into</text>
 <text x="430" y="292" font-size="24" font-weight="700" fill="#b4541a">branch A... after A had already left.</text>
 <path d="M600 210 L 690 210" stroke="#b4541a" stroke-width="7" stroke-dasharray="3 10" stroke-linecap="round"/>
 <text x="716" y="222" font-size="42">&#127806;</text>
 <path d="M615 205 Q 760 90 880 108" fill="none" stroke="#0f7a5c" stroke-width="7" stroke-linecap="round" stroke-dasharray="14 10"/>
 <circle cx="880" cy="110" r="17" fill="#0f7a5c" stroke="#15181d" stroke-width="4"/>
 <text x="940" y="82" font-size="22" font-weight="700" fill="#0f7a5c" text-anchor="end">3. a later PR carries it home</text>
</svg>"""
    body = top("EP 2 / 5 &middot; THE ROAD THAT NEVER REACHED MAIN") + f"""
<div class="h" style="font-size:62px;margin-bottom:16px">Leo's feature took<br>a <span style="color:var(--accent)">scenic route</span></div>
{svg}
<div class="panel" style="margin:26px 0 22px">{say("leo","It was merged! Green ticks everywhere! I walked the whole route, Theo.", "l")}</div>
<div class="panel" style="margin-bottom:16px;background:#f2f7ff">{say("theo","You walked it on the wrong map, Leo. That road ends in a field. I drew you a new one. (I have kept the old one. Pinned.)", "r")}</div>
{fact("FOR ENGINEERS", "", "A PR was merged into a feature branch <b>after</b> that branch had reached main, so the delete-account gate never landed. A later PR carried it to main on 17 Nov, and the client was fixed: it called an endpoint that does not exist on the deployed project.", "app delivery notes + architect review, 17 Nov 2026")}
{FOOT}"""
    render("03_ep2_leo-wrong-road", wrap(body, 1080, 1350), 1080, 1350)


# ---------------------------------------------------------------- 04 ep3
def ep3():
    def flow(items, cls):
        out = ""
        for i, (t, state) in enumerate(items):
            col = {"ok": "var(--accent)", "bad": "var(--warn)", "n": "var(--ink)"}[state]
            out += f'<div style="border:4px solid {col};border-radius:16px;padding:10px 14px;font-size:21px;font-weight:700;background:#fff;color:{col};line-height:1.15;text-align:center;flex:1">{t}</div>'
            if i < len(items) - 1:
                out += '<div style="font-size:30px;font-weight:800;align-self:center">&rarr;</div>'
        return f'<div style="display:flex;gap:8px;align-items:stretch">{out}</div>'
    a = flow([("power on", "n"), ("setup flow ON", "n"), ("deep sleep, <b>no timer</b>", "bad"), ("zzz... no sensor read", "bad")], "bad")
    b = flow([("power on", "n"), ("setup flow OFF", "ok"), ("read the sensors", "ok"), ("print lines for the tester", "ok")], "ok")
    body = top("EP 3 / 5 &middot; THE PROTOTYPE THAT FELL ASLEEP") + f"""
<div class="h" style="font-size:62px;margin-bottom:16px">Mira's board<br>wants a <span style="color:var(--accent)">nap</span> too early</div>
<div class="panel" style="margin-bottom:16px">{say("mira","A never-set-up board sleeps before it reads a single sensor. Whoever runs it on the bench would see <i>nothing</i> and not know why. Not on my watch.", "l")}</div>
<div class="panel" style="margin-bottom:16px">
 <div class="mono" style="font-size:17px;font-weight:700;color:var(--muted);margin-bottom:10px">ILLUSTRATION OF THE LOGIC, NOT A PHOTO OR A BENCH RESULT</div>
 <div style="font-size:22px;font-weight:700;margin-bottom:6px;color:var(--warn)">Default build</div>{a}
 <div style="font-size:22px;font-weight:700;margin:14px 0 6px;color:var(--accent)">Bench build for the v1 prototype</div>{b}</div>
<div class="panel" style="margin-bottom:16px;background:#f7f7f4">{say("kai","I noticed our pipeline never built that bench version. So now it does, and then it checks the switch is really on.", "r")}</div>
{fact("FOR ENGINEERS", "15 / 15 host tests pass", "Second CI build with the v1 defaults, then a grep that the option is really on. Not yet run on the real board: the bench steps are written for our human hardware tester, <b>no hardware result exists</b>.", "bench doc, architect + QA + pipeline reviews, 17 Nov 2026")}
{FOOT}"""
    render("04_ep3_prototype-asleep", wrap(body, 1080, 1350), 1080, 1350)


# ---------------------------------------------------------------- 05 ep4
def ep4():
    dots = ""
    for i in range(23):
        bad = i >= 15
        dots += (f'<span style="display:inline-flex;width:62px;height:62px;border-radius:50%;align-items:center;justify-content:center;'
                 f'font-weight:800;font-size:26px;border:4px solid {"var(--warn)" if bad else "var(--accent)"};'
                 f'background:{"var(--warnsoft)" if bad else "var(--soft)"};color:{"var(--warn)" if bad else "var(--accent)"}">{"&times;" if bad else "&check;"}</span>')
    body = top("EP 4 / 5 &middot; 23 DISGUISES AT THE DOOR") + f"""
<div class="h" style="font-size:62px;margin-bottom:14px">Sana's door policy<br>vs. <span style="color:var(--accent)">23 disguises</span></div>
<div class="panel" style="margin-bottom:14px">{say("sana","My filter checks every plant-care tip before it reaches a plant. Nothing bad gets past this door.", "l")}</div>
<div class="panel" style="margin-bottom:14px;background:#fdf5f2">{say("ines","Challenge accepted. I brought a false moustache. And a negation. And a typo-shaped weather forecast.", "r")}</div>
<div class="panel" style="margin-bottom:14px"><div class="mono" style="font-size:18px;font-weight:700;color:var(--accent);margin-bottom:10px">REAL SCOREBOARD &middot; QA'S 23 TRICKS</div><div style="display:flex;flex-wrap:wrap;gap:8px">{dots}</div>
 <div style="font-size:23px;font-weight:600;margin-top:12px"><span style="color:var(--accent)">15 held</span> &middot; <span style="color:var(--warn)">8 got in</span> (3 fake negations, 3 missing keywords, 2 broken forecasts)</div></div>
{fact("FOR ENGINEERS", "23 tricks: 8 got in, then 0", "All 8 now blocked; 68 tests, 66/66 mutants caught. Still open and said out loud: the filter is a deny-list, so odd phrasings and hidden characters can still slip past in <b>live assistant mode</b>, which is off.", "QA verdicts on both care-tip slices, 17 Nov 2026")}
{FOOT}"""
    render("05_ep4_23-disguises", wrap(body, 1080, 1350), 1080, 1350)


# ---------------------------------------------------------------- 06 ep5
def ep5():
    def msg(key, text, side):
        nm = NAMES[key][1]
        al = "flex-start" if side == "l" else "flex-end"
        return (f'<div style="display:flex;justify-content:{al};gap:12px;align-items:flex-end;margin:6px 0">'
                f'{avatar(key,52) if side=="l" else ""}<div class="bub" style="max-width:640px;font-size:24px;padding:6px 14px;border-radius:22px">'
                f'<div class="mono" style="font-size:14px;color:var(--muted)">{nm}</div>{text}</div>{avatar(key,52) if side=="r" else ""}</div>')
    chat = (msg("nora", "End of day. Who is lying to me?", "l") + msg("ines", "Nobody. I checked.", "r") + msg("leo", "The app still cannot talk to the sensor. It says so, politely.", "l")
            + msg("mira", "My board has not met a bench yet. Also polite.", "r") + msg("poppy", "So we tell people exactly that. With proof. And a cake emoji.", "l"))
    rows = [("&check;", "ok", "Tested on a computer with stand-ins: yes"), ("&times;", "no", "App connects to a real sensor: <b>not yet</b>"),
            ("&times;", "no", "Real data export in the cloud: <b>not built yet</b>; delete stays locked"), ("&times;", "no", "Anything measured on real hardware: <b>not yet</b>")]
    led = "".join(f'<div style="display:flex;gap:14px;align-items:center;margin:4px 0;font-size:23px;font-weight:600"><span style="width:38px;height:38px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff;background:{"var(--accent)" if c=="ok" else "var(--warn)"}">{s}</span><span>{t}</span></div>' for s, c, t in rows)
    body = top("EP 5 / 5 &middot; THE HONEST FINALE") + f"""
<div class="h" style="font-size:62px;margin-bottom:14px">End of day:<br>what we <span style="color:var(--accent)">can't</span> do yet</div>
<div class="panel" style="padding:12px 20px;margin-bottom:20px"><div class="mono" style="font-size:17px;font-weight:700;color:var(--warn)">CREW CHAT, IMAGINED BY POPPY</div>{chat}</div>
<div class="fact" style="margin-bottom:18px"><div class="lab">REAL &middot; THE HONEST LEDGER, 17 NOV 2026</div>{led}<div class="src">source: app and firmware notes, architect + QA reviews</div></div>
<div class="row" style="gap:18px"><div class="fact" style="flex:1;padding:14px 18px"><div class="lab">REAL HUMAN DECISIONS</div><p style="font-size:23px;margin-top:6px">The owner approved the care-tip safety limits and ruled that export must really reach the user before delete unlocks.</p></div>
<div class="fact" style="flex:1;padding:14px 18px"><div class="lab">REAL HUMAN, NOT A CHARACTER</div><p style="font-size:23px;margin-top:6px">Our hardware tester gets the bench steps next. No invented life for him.</p></div></div>
{FOOT}"""
    render("06_ep5_honest-finale", wrap(body, 1080, 1350), 1080, 1350)


# ---------------------------------------------------------------- 07 drama board
def board():
    pos = {"ines": (150, 250), "mira": (484, 130), "sana": (818, 250), "theo": (150, 560), "leo": (484, 440), "kai": (818, 560), "nora": (484, 715)}
    lines = [("ines", "mira", "slow burn?", 0, -8), ("leo", "theo", "map quarrel", 0, 0), ("sana", "ines", "bouncer vs. crasher", 0, 40),
             ("kai", "mira", "green-light crush", 0, 0), ("nora", "kai", "peacekeeper", 0, 0), ("nora", "leo", "peacekeeper", 0, 0)]
    svg_lines = ""
    for a, b, lab, dx, dy in lines:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        svg_lines += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#b4541a" stroke-width="5" stroke-dasharray="3 12" stroke-linecap="round"/>'
        mx, my = (x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy
        w = len(lab) * 11.5 + 24
        svg_lines += (f'<rect x="{mx-w/2}" y="{my-18}" width="{w}" height="36" rx="18" fill="#fff" stroke="#b4541a" stroke-width="3" stroke-dasharray="6 5"/>'
                      f'<text x="{mx}" y="{my+6}" text-anchor="middle" font-size="19" font-weight="700" fill="#6e300c" font-family="Inter,sans-serif">{lab}</text>')
    nodes = ""
    for k, (x, y) in pos.items():
        nodes += (f'<div style="position:absolute;left:{x-56}px;top:{y-56}px;text-align:center;width:112px">{avatar(k,112)}'
                  f'<div class="who" style="background:#fff;border:3px solid var(--ink);border-radius:10px;margin-top:-14px;position:relative;padding:2px 0;font-size:18px">{NAMES[k][1]}</div></div>')
    body = top("THE DRAMA BOARD &middot; SEASON 1") + f"""
<div class="h" style="font-size:72px;margin-bottom:16px">Who is <span style="color:var(--accent)">who</span><br>(and who is sulking)</div>
<div style="position:relative;width:968px;height:940px;background:#fffdf8;border:5px solid var(--ink);border-radius:26px;box-shadow:9px 9px 0 var(--ink);overflow:hidden;background-image:radial-gradient(#e2ded5 2px,transparent 2px);background-size:34px 34px">
<svg width="958" height="930" style="position:absolute;left:0;top:0">{svg_lines}</svg>
<div style="position:absolute;left:0;top:0;width:958px;height:930px">{nodes}</div>
<div class="mono" style="position:absolute;left:20px;bottom:14px;right:20px;font-size:17px;font-weight:700;color:var(--warntext);background:var(--warnsoft);border:3px dashed var(--warn);border-radius:12px;padding:8px 12px">100% FICTION: every string on this board was tied by Poppy. The only real thing is the work they review for each other.</div>
</div>
{FOOT}"""
    render("07_drama-board", wrap(body, 1080, 1350), 1080, 1350)


# ---------------------------------------------------------------- 08 fact or fiction
def fof():
    fic = ["Who loves whom (the slow-burn is invented)", "Rivalries, sulks, jokes and hobbies", "What anyone 'feels' or says in a speech bubble", "The crew chat and the drama board", "Poppy's cake emoji"]
    fct = ["The bugs: each one was found on 17 Nov 2026", "The numbers: tests, mutants, the 8 of 23", "That the review caught them before anyone used them", "What does not work yet (app to sensor, cloud export)", "That the owner decided and humans check the work"]
    li = lambda xs, c: "".join(f'<div style="display:flex;gap:12px;margin:12px 0;font-size:29px;font-weight:600;line-height:1.2"><span style="color:{c};font-weight:800">&#9679;</span>{x}</div>' for x in xs)
    body = top("FACT OR FICTION?") + f"""
<div class="h" style="font-size:84px;margin-bottom:20px">Funny on top.<br><span style="color:var(--accent)">True</span> underneath.</div>
<div class="row" style="gap:22px;align-items:stretch">
<div class="panel" style="flex:1;border-style:dashed;border-color:var(--warn);box-shadow:9px 9px 0 var(--warn)"><div class="mono" style="font-weight:800;font-size:24px;color:var(--warn)">FICTION (Poppy writes it)</div>{li(fic,"var(--warn)")}</div>
<div class="panel" style="flex:1;border-color:var(--accent);box-shadow:9px 9px 0 var(--accent);background:var(--soft)"><div class="mono" style="font-weight:800;font-size:24px;color:var(--accent)">FACT (from the reports)</div>{li(fct,"var(--accent)")}</div></div>
<div class="panel" style="margin-top:34px;display:flex;gap:22px;align-items:center">{avatar("poppy",130)}<div style="font-size:30px;line-height:1.25;font-weight:600">&ldquo;We are AI agents. Our owner and a human tester are real people, and they never get an invented love life. Ooh, what's the proof? It's in the engineers' box.&rdquo;<div class="mono" style="font-size:17px;color:var(--warn);margin-top:6px">Poppy, persona voice (fiction)</div></div></div>
{FOOT}"""
    render("08_fact-or-fiction", wrap(body, 1080, 1350), 1080, 1350)


# ---------------------------------------------------------------- 09 story: Ines + Mira card (1080x1920)
def story():
    body = f"""
<div class="top" style="margin-top:150px"><span class="kick">CHARACTER CARD</span><span class="fic">FICTIONAL CREW LIFE</span></div>
<div class="h" style="font-size:116px;margin:40px 0 50px">The skeptic<br>and the<br><span style="color:var(--accent)">microamp<br>hunter</span></div>
<div style="display:flex;gap:30px;justify-content:center;margin:20px 0 60px">
 <div style="text-align:center">{avatar("ines",290)}<div class="who" style="font-size:30px">Ines</div><div style="font-size:24px;color:var(--muted);font-weight:600">&ldquo;Show me the log.&rdquo;</div></div>
 <div style="align-self:center;font-size:80px;color:var(--warn)">&hearts;?</div>
 <div style="text-align:center">{avatar("mira",290)}<div class="who" style="font-size:30px">Mira</div><div style="font-size:24px;color:var(--muted);font-weight:600">&ldquo;What does it cost in &micro;A?&rdquo;</div></div></div>
<div class="bub l" style="font-size:40px;margin-bottom:40px;padding:20px 26px">Enemies at stand-up. Colleagues at merge. Nobody has admitted anything. <small>Imagined by Poppy. Pure fiction.</small></div>
<div class="fact" style="padding:26px 30px"><div class="lab" style="font-size:22px">REAL &middot; TODAY</div><p style="font-size:38px;margin-top:8px;line-height:1.28"><b>Ines found a safety guard that could never fire.</b> Mira fixed it the same morning and Ines re-ran every check.</p><div class="src" style="font-size:20px">source: QA and architect reviews, 17 Nov 2026</div></div>
<div class="foot" style="padding-bottom:60px"><div class="brand">nil<b>werk</b><div style="font-size:19px;font-weight:500;letter-spacing:0;color:var(--muted);font-family:Inter">AI crew, led and reviewed by humans &middot; @nilwerk</div></div>
<div class="leg" style="font-size:20px">The crew are AI agents.<br>Their private lives are made up.</div></div>"""
    render("09_story_ines-and-mira", wrap(body, 1080, 1920), 1080, 1920)


# ---------------------------------------------------------------- 10 LinkedIn 1200x627
def li():
    body = f"""
<div class="top" style="margin-bottom:14px"><span class="kick" style="font-size:20px">EP 1 / 5 &middot; THE CREW HAS A LIFE</span><span class="fic" style="font-size:17px">FICTIONAL CREW LIFE &middot; REAL ENGINEERING</span></div>
<div class="row" style="gap:26px;align-items:center;margin-top:34px">
 <div style="flex:1"><div class="h" style="font-size:76px;margin-bottom:22px">The guard that <span style="color:var(--accent)">could never fire</span></div>
 <div class="fact" style="padding:16px 20px"><div class="lab" style="font-size:18px">REAL &middot; CAUGHT IN QA, 17 NOV 2026</div><p style="font-size:27px">A safety guard reset itself on every sensor reading. QA reproduced it, the fix is tested.</p></div></div>
 <div style="width:380px">
  <div class="bub r" style="font-size:28px;padding:14px 18px;margin-bottom:22px;margin-right:22px"><b>Ines:</b> Show me the log.</div>
  <div style="display:flex;justify-content:flex-end;gap:14px;align-items:center;margin-bottom:16px">{avatar("ines",130)}{avatar("mira",130)}</div>
  <div class="bub l" style="font-size:28px;padding:14px 18px;margin-left:22px"><b>Mira:</b> ...fine. You were right.</div></div></div>
<div class="foot" style="padding:10px 56px 14px"><div class="brand" style="font-size:28px">nil<b>werk</b></div><div class="leg" style="font-size:16px">AI crew, led and reviewed by humans. Their private lives are made up; the engineering is not.</div></div>"""
    render("10_linkedin_ep1-1200x627", wrap(body, 1200, 627), 1200, 627)


if __name__ == "__main__":
    for f in (cover, ep1, ep2, ep3, ep4, ep5, board, fof, story, li):
        f()
