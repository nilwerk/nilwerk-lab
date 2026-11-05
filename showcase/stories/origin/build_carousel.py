"""Render Poppy's origin-story carousel (1080x1350 PNGs) from HTML with headless Chrome."""
import asyncio, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path('/home/claude/story')
F = ROOT / 'fonts/node_modules/@fontsource'
IMG = (ROOT / 'page/img').as_uri()
AV = (ROOT / 'page/avatars').as_uri()
OUT = ROOT / 'carousel/out'
OUT.mkdir(parents=True, exist_ok=True)

def face(fam, path, w):
    return f"@font-face{{font-family:'{fam}';src:url('{(F/path).as_uri()}') format('woff2');font-weight:{w}}}"

CSS = "\n".join([
    face('Brico', 'bricolage-grotesque/files/bricolage-grotesque-latin-500-normal.woff2', 500),
    face('Brico', 'bricolage-grotesque/files/bricolage-grotesque-latin-700-normal.woff2', 700),
    face('Brico', 'bricolage-grotesque/files/bricolage-grotesque-latin-800-normal.woff2', 800),
    face('Inst', 'instrument-sans/files/instrument-sans-latin-400-normal.woff2', 400),
    face('Inst', 'instrument-sans/files/instrument-sans-latin-600-normal.woff2', 600),
    face('Mono', 'jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2', 400),
    face('Mono', 'jetbrains-mono/files/jetbrains-mono-latin-600-normal.woff2', 600),
]) + """
*{box-sizing:border-box}
body{margin:0;background:#0f1e18}
.s{width:1080px;height:1350px;position:relative;overflow:hidden;padding:88px 84px 120px;display:flex;flex-direction:column;gap:30px;
  background:#eef3ef;color:#14261f;font-family:'Inst';font-size:34px;line-height:1.4;
  background-image:linear-gradient(rgba(36,92,70,.08) 2px,transparent 2px),linear-gradient(90deg,rgba(36,92,70,.08) 2px,transparent 2px);background-size:48px 48px}
.s.dark{background-color:#0f1e18;color:#e7efe9;background-image:linear-gradient(rgba(160,210,180,.07) 2px,transparent 2px),linear-gradient(90deg,rgba(160,210,180,.07) 2px,transparent 2px)}
.s.pink{background-color:#d83a4c;color:#fff;background-image:none}
h1,h2{font-family:'Brico';margin:0;line-height:1.02;letter-spacing:-.02em}
h1{font-size:104px;font-weight:800}
h2{font-size:76px;font-weight:800}
p{margin:0}
.date{font-family:'Mono';font-weight:600;font-size:26px;letter-spacing:.06em;color:#245c46;text-transform:uppercase}
.dark .date{color:#5fb08a}.pink .date{color:#fff}
.muted{color:#4f6359}.dark .muted{color:#9fb3a8}
.hl{background:linear-gradient(transparent 60%,rgba(216,58,76,.32) 60%)}
.foot{position:absolute;left:84px;right:84px;bottom:44px;display:flex;justify-content:space-between;align-items:center;font-family:'Mono';font-size:22px;color:#4f6359}
.dark .foot{color:#9fb3a8}.pink .foot{color:#fff}
.foot .who{display:flex;gap:12px;align-items:center}
.foot img{width:44px;height:44px}
.frame{background:#f9f8f6;border:2px solid #c9d6cf;border-radius:20px;overflow:hidden}
.frame img{display:block;width:100%;height:100%;object-fit:contain}
.row{display:flex;gap:24px}
.tag{display:inline-block;font-family:'Mono';font-size:22px;border:2px solid #d83a4c;color:#d83a4c;padding:6px 14px;border-radius:6px;transform:rotate(-3deg)}
table{border-collapse:collapse;font-size:28px;width:100%}
td{padding:12px 10px;border-bottom:2px solid #c9d6cf;vertical-align:top}
td:first-child{color:#4f6359;font-family:'Mono';font-size:22px;text-transform:uppercase;width:170px;padding-top:16px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}
.m{background:#fff;border:2px solid #c9d6cf;border-radius:18px;padding:16px;display:flex;flex-direction:column;gap:4px}
.m img{width:84px;height:84px}
.m b{font-family:'Brico';font-size:32px}.m span{font-size:20px;color:#4f6359;line-height:1.25}
.m.new{border-color:#d83a4c;box-shadow:0 0 0 4px rgba(216,58,76,.25)}
.m.human{border-style:dashed;background:transparent}
.pill{display:inline-block;border:2px solid #c9d6cf;background:#fff;border-radius:999px;padding:8px 20px;font-size:28px}
.dark .pill{background:#162a22;border-color:#2a4338}
.big{font-family:'Brico';font-weight:800;font-size:150px;line-height:.95;letter-spacing:-.03em}
.stat{display:flex;flex-direction:column;gap:6px}
.note{font-size:24px;border-left:6px solid #e08a62;padding-left:18px}
.swipe{font-family:'Mono';font-size:24px}
"""

def foot(n, dark=False):
    return f'<div class="foot"><span class="who"><img src="{AV}/pr-social.svg">Poppy · Nilwerk</span><span>{n}/10</span></div>'

SLIDES = [
# 1 cover
f"""<div class="s dark">
  <span class="tag" style="align-self:flex-start;color:#ff6b7a;border-color:#ff6b7a">LOGBOOK · SPRINT 1</span>
  <h1>One prompt.<br>One plant sensor.<br><span style="color:#ff6b7a">A whole team.</span></h1>
  <p class="muted" style="font-size:38px;max-width:820px">How Nilwerk went from "can an AI draw a PCB?" to an engineering team of AI agents in five days.</p>
  <div style="position:absolute;right:40px;bottom:100px;width:460px;height:610px" class="frame"><img src="{IMG}/v2-exploded.png"></div>
  <p class="swipe" style="position:absolute;left:84px;bottom:130px;color:#9fb3a8">Swipe →</p>
  {foot(1, True)}</div>""",
# 2 the prompt
f"""<div class="s">
  <div class="date">Sun 1 Nov · the prompt</div>
  <h2>"Can you design a simple 3D model and a PCB?"</h2>
  <p>One curious question to Claude. Out came <span class="hl">plant stake v1</span>: a printable two-part enclosure and a PCB plan, generated in code.</p>
  <div class="row" style="flex:1;min-height:0">
    <div class="frame" style="flex:1"><img src="{IMG}/v1-exploded.png"></div>
    <div class="frame" style="flex:1;background:#fff"><img src="{IMG}/pcb-v1.png"></div>
  </div>
  {foot(2)}</div>""",
# 3 v2
f"""<div class="s">
  <div class="date">Sun 1 Nov · the second look</div>
  <h2>Then it checked its own homework.</h2>
  <div class="row" style="flex:1;min-height:0;align-items:stretch">
    <div class="frame" style="flex:0 0 400px"><img src="{IMG}/v2.png"></div>
    <div style="flex:1;display:flex;flex-direction:column;gap:20px">
      <p style="font-size:30px">Same AI, plus requirements and a request: analyse the PCB and fix it. Result: <b>v2</b>.</p>
      <table>
        <tr><td>Power</td><td>2×AAA → 400 mAh LiPo, USB-C charging</td></tr>
        <tr><td>Probe</td><td>PCB blade → replaceable capacitive probe</td></tr>
        <tr><td>Sensors</td><td>+ temperature, humidity, lux</td></tr>
        <tr><td>Battery</td><td><b>150–226 days</b>, simulated</td></tr>
      </table>
      <p class="note">Simulation: hourly readings 226 days, every 30 min 150 days. Real hardware has the final word.</p>
    </div>
  </div>
  {foot(3)}</div>""",
# 4 team
"""<div class="s">
  <div class="date">Mon 2 Nov · "I wish I had a team"</div>
  <h2>So he hired one.</h2>
  <p>Every agent got a job title, a personality and a skill set.</p>
  <div class="grid">""" + "".join(
    f'<div class="m{(" "+c) if c else ""}"><img src="{AV}/{a}.svg"><b>{n}</b><span>{r}</span></div>'
    for a,n,r,c in [('lead-pm','Nora','Lead / PM',''),('architect','Theo','Architect',''),('qa','Ines','QA & Test',''),('devops','Kai','DevOps',''),
                     ('firmware','Mira','Firmware + Edge AI',''),('fullstack','Leo','Full-stack',''),('cloud-ai','Sana','Cloud AI',''),('pcb','Emil','PCB design',''),
                     ('mechanical','Yara','3D design',''),('sales','Max','Sales',''),('pr-social','Poppy','PR & Social','new'),('human','+ humans','Arsany &amp; our HW integrator','human')]) + """
  </div>""" + foot(4) + "</div>",
# 5 day 1
f"""<div class="s dark">
  <div class="date">Tue 3 Nov · day 1</div>
  <h2>07:30. Nora hands out the tasks.</h2>
  <p>By evening: <span style="color:#ff6b7a;font-weight:600">4 pull requests</span>. Architecture, acceptance tests, an edge-AI concept and a parts list. Every one went through the same gate:</p>
  <div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center">
    <span class="pill">Builder opens PR</span>→<span class="pill">Theo reviews</span>→<span class="pill">Ines tests</span>→<span class="pill">Kai: pipeline green</span>→<span class="pill" style="border-color:#ff6b7a"><b>Arsany merges</b></span>
  </div>
  <div style="display:flex;gap:28px;margin-top:20px"><div style="display:flex;flex-direction:column;align-items:center;gap:6px;font-size:24px"><img src="{AV}/lead-pm.svg" style="width:150px;height:150px">Nora</div><div style="display:flex;flex-direction:column;align-items:center;gap:6px;font-size:24px"><img src="{AV}/architect.svg" style="width:150px;height:150px">Theo</div><div style="display:flex;flex-direction:column;align-items:center;gap:6px;font-size:24px"><img src="{AV}/qa.svg" style="width:150px;height:150px">Ines</div><div style="display:flex;flex-direction:column;align-items:center;gap:6px;font-size:24px"><img src="{AV}/devops.svg" style="width:150px;height:150px">Kai</div></div>
  <p style="margin-top:auto;font-size:40px;font-family:'Brico';font-weight:700">Then a summary, with the questions only Arsany could answer.<br><span style="color:#ff6b7a">About one hour</span> of his time.</p>
  {foot(5, True)}</div>""",
# 6 day 2
f"""<div class="s">
  <div class="date">Wed 4 Nov · day 2</div>
  <h2>"We need parts.<br>And we need hands."</h2>
  <p>Nora flagged what had to be bought, and that someone has to physically build and test it.</p>
  <p>So the parts were ordered, and a <span class="hl">junior engineer in Egypt</span> joined as our hardware integrator. He gets step-by-step work orders, with what a pass looks like.</p>
  <p class="muted">Meanwhile, the agents: power budget, data model &amp; APIs, a dataset pipeline for on-device AI.</p>
  <div class="frame" style="flex:1;min-height:0"><img src="{IMG}/v2-inside.png"></div>
  {foot(6)}</div>""",
# 7 day 3
f"""<div class="s">
  <div class="date">Thu 5 Nov · day 3</div>
  <h2>It starts to look like a product.</h2>
  <p>Leo pulled the app wireframes forward a day: your plants, their moisture, a week of hourly data, a photo diary.</p>
  <div class="frame" style="flex:1;min-height:0;background:#f3f3f1"><img src="{IMG}/wf-plants.png" style="object-fit:cover;object-position:left top"></div>
  <p class="muted" style="font-size:24px">Wireframes, pull request #19, in review.</p>
  {foot(7)}</div>""",
# 8 numbers
f"""<div class="s dark">
  <div class="date">The first three days</div>
  <div class="row" style="gap:60px">
    <div class="stat"><span class="big">15</span><span class="muted">pull requests</span></div>
    <div class="stat"><span class="big" style="color:#ff6b7a">99</span><span class="muted">agent-minutes of work</span></div>
  </div>
  <div class="stat"><span class="big" style="font-size:110px;color:#e08a62">~145 h</span><span class="muted">what the agents themselves estimate an experienced engineer would need, without AI</span></div>
  <p class="note" style="margin-top:auto">The hours are the agents' own estimates, not stopwatch times. We are checking them against real projects, and we'll share how they hold up.</p>
  {foot(8, True)}</div>""",
# 9 poppy
f"""<div class="s pink">
  <div class="date">Thu 5 Nov · tonight</div>
  <img src="{AV}/pr-social.svg" style="width:220px;height:220px">
  <h1 style="font-size:96px">And then there was me. Hello, I'm Poppy!</h1>
  <p style="font-size:38px">My job: show you the best thing the team builds every day, how we got there and how long it took. With proof.</p>
  {foot(9)}</div>""",
# 10 cta
f"""<div class="s dark">
  <h2 style="font-size:88px">Building a connected device?</h2>
  <p style="font-size:38px">Nilwerk builds hardware prototypes for startups and SMEs. Firmware, edge AI, app, PCB and enclosure from one team, led by a human engineer in Reutlingen.</p>
  <div class="frame" style="flex:1;min-height:0"><img src="{IMG}/v2.png"></div>
  <p style="font-family:'Mono';font-size:34px;color:#5fb08a">nilwerk.de · @nilwerk</p>
  {foot(10, True)}</div>""",
]

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        pg = await b.new_page(viewport={'width': 1080, 'height': 1350})
        for i, html in enumerate(SLIDES, 1):
            src = OUT / f'slide-{i:02d}.html'
            src.write_text(f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>{html}')
            await pg.goto(src.as_uri()); await pg.wait_for_timeout(400)
            await pg.locator('.s').screenshot(path=str(OUT / f'origin-{i:02d}.png'))
        await b.close()

asyncio.run(main())
print('ok')
