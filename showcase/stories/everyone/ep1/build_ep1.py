"""Everyone track, episode 1: 'Who's looking after Basil?'
Renders a 9-slide carousel (1080x1350) and the same scenes as 9:16 frames (1080x1920) for a Reel."""
import asyncio, pathlib, subprocess
from playwright.async_api import async_playwright

ROOT = pathlib.Path('/home/claude/story')
F = ROOT / 'fonts/node_modules/@fontsource'
IMG = (ROOT / 'everyone/img').as_uri()
PAGE_IMG = (ROOT / 'page/img').as_uri()
AV = (ROOT / 'page/avatars').as_uri()
BASIL = (ROOT / 'everyone/basil.svg').as_uri()
OUT = ROOT / 'everyone/out'
OUT.mkdir(parents=True, exist_ok=True)

def face(fam, path, w):
    return f"@font-face{{font-family:'{fam}';src:url('{(F/path).as_uri()}') format('woff2');font-weight:{w}}}"

CSS = "\n".join([
    face('Brico', 'bricolage-grotesque/files/bricolage-grotesque-latin-700-normal.woff2', 700),
    face('Brico', 'bricolage-grotesque/files/bricolage-grotesque-latin-800-normal.woff2', 800),
    face('Inst', 'instrument-sans/files/instrument-sans-latin-400-normal.woff2', 400),
    face('Inst', 'instrument-sans/files/instrument-sans-latin-600-normal.woff2', 600),
    face('Mono', 'jetbrains-mono/files/jetbrains-mono-latin-600-normal.woff2', 600),
]) + """
*{box-sizing:border-box}body{margin:0}
.s{width:1080px;position:relative;overflow:hidden;display:flex;flex-direction:column;gap:34px;padding:96px 88px 130px;
   font-family:'Inst';font-size:40px;line-height:1.35;color:#1d2a22;background:#fbf3df}
.s.c{height:1350px}.s.r{height:1920px;padding:220px 88px 300px;font-size:46px}
.s.green{background:#2f6b45;color:#fff}.s.pink{background:#d83a4c;color:#fff}.s.sky{background:#dceef3}
h1{font-family:'Brico';font-weight:800;font-size:112px;line-height:1;letter-spacing:-.025em;margin:0}
.r h1{font-size:124px}
h2{font-family:'Brico';font-weight:800;font-size:84px;line-height:1.02;letter-spacing:-.02em;margin:0}
.r h2{font-size:96px}
p{margin:0}
.ep{font-family:'Mono';font-size:26px;letter-spacing:.08em;text-transform:uppercase;opacity:.8}
.mark{background:#ffd23f;color:#1d2a22;padding:0 .18em;border-radius:.18em;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.foot{position:absolute;left:88px;right:88px;bottom:48px;display:flex;justify-content:space-between;align-items:center;font-family:'Mono';font-size:24px;opacity:.75}
.r .foot{bottom:150px}
.foot span{display:flex;gap:12px;align-items:center}.foot img{width:48px;height:48px}
.pic{flex:1;min-height:0;display:flex;align-items:center;justify-content:center}
.pic img{max-width:100%;max-height:100%;object-fit:contain}
.card{background:#fff;border-radius:28px;overflow:hidden;box-shadow:0 18px 40px rgba(29,42,34,.15)}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}
.grid div{display:flex;flex-direction:column;align-items:center;gap:6px;font-family:'Brico';font-weight:700;font-size:28px}
.grid img{width:150px;height:150px}
.r .grid img{width:160px;height:160px}
.checks{display:flex;flex-direction:column;gap:18px}
.checks div{display:flex;gap:22px;align-items:center;background:rgba(255,255,255,.14);border-radius:22px;padding:16px 22px}
.checks img{width:96px;height:96px}
.big{font-family:'Brico';font-weight:800;font-size:150px;line-height:.95;letter-spacing:-.03em}
.ask{background:#fff;color:#1d2a22;border-radius:28px;padding:26px 30px;font-family:'Brico';font-weight:700;font-size:44px}
"""

def foot(kind, n, total):
    num = f'{n}/{total}' if kind == 'c' else 'nilwerk.de'
    return f'<div class="foot"><span><img src="{AV}/pr-social.svg">Poppy · @nilwerk</span><span>{num}</span></div>'

TEAM = [('lead-pm','Nora'),('architect','Theo'),('qa','Ines'),('devops','Kai'),('firmware','Mira'),
        ('fullstack','Leo'),('cloud-ai','Sana'),('pcb','Emil'),('mechanical','Yara'),('sales','Max')]

def scenes(k):
    team = ''.join(f'<div><img src="{AV}/{a}.svg">{n}</div>' for a, n in TEAM)
    return [
f"""<div class="s {k}"><div class="ep">Who's looking after Basil? · Ep. 1</div>
  <h1>Can a team of AI coworkers keep a basil plant alive?</h1>
  <div class="pic"><img src="{BASIL}" style="height:100%"></div></div>""",
f"""<div class="s {k} sky"><div class="ep">Meet Basil</div>
  <h2>Basil is our mascot. She has one problem.</h2>
  <p>She can't tell anyone when she's <span class="mark">thirsty</span>.</p>
  <div class="pic"><img src="{BASIL}" style="height:100%"></div></div>""",
f"""<div class="s {k}"><div class="ep">Sunday</div>
  <h2>Arsany asked an AI one question.</h2>
  <p>"Could you design a little gadget that feels if the soil is dry?" It drew one: <span class="mark">the case and the tiny brain</span>.</p>
  <div class="pic card"><img src="{IMG}/v1-exploded.png"></div></div>""",
f"""<div class="s {k}"><div class="ep">Still Sunday</div>
  <h2>Then he asked it to check its own work.</h2>
  <p>Version 2 has a battery you charge like a phone. Our computer test says one charge should last <span class="mark">about half a year</span>.</p>
  <div class="pic card"><img src="{IMG}/v2.png"></div></div>""",
f"""<div class="s {k} green"><div class="ep">Monday</div>
  <h2>"I wish I had a team." So he made one.</h2>
  <p>10 AI coworkers. Each one has a job and a personality.</p>
  <div class="grid">{team}</div>
  <p style="margin-top:auto">Plus two humans who check everything: Arsany, and an engineer who builds the real hardware.</p></div>""",
f"""<div class="s {k} green"><div class="ep">Day 1</div>
  <h2>07:30. Nora, the manager, plans the day.</h2>
  <p>Every piece of work is checked by three colleagues before it counts:</p>
  <div class="checks">
    <div><img src="{AV}/architect.svg"><span><b>Theo</b> checks the design</span></div>
    <div><img src="{AV}/qa.svg"><span><b>Ines</b> tests it</span></div>
    <div><img src="{AV}/devops.svg"><span><b>Kai</b> makes sure nothing breaks</span></div>
  </div>
  <p>Then the boss signs it off.</p></div>""",
f"""<div class="s {k} sky"><div class="ep">Day 2</div>
  <h2>"We need real parts. And real hands."</h2>
  <p>So the parts were ordered, and a human engineer joined the team to build it for real.</p>
  <div class="pic card"><img src="{IMG}/v2-exploded.png"></div></div>""",
f"""<div class="s {k}"><div class="ep">Day 3</div>
  <h2>Basil's app got its first sketch.</h2>
  <p>Her soil, her week, her photo diary. Next step: making it real.</p>
  <div class="pic card"><img src="{PAGE_IMG}/wf-plants.png" style="width:100%;height:100%;object-fit:cover;object-position:left top"></div></div>""",
f"""<div class="s {k} pink"><div class="ep">3 days in</div>
  <p>The team worked</p><div class="big">under 2 hours.</div>
  <p>They reckon a person would need <b>3–4 working weeks</b>. We'll find out if they're right.</p>
  <div class="ask">What would YOU want your plant to tell you? 👇</div>
  <p style="font-size:34px">Follow Basil. Next: her sensor gets a real body.</p></div>""",
    ]

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        for k, h in (('c', 1350), ('r', 1920)):
            pg = await b.new_page(viewport={'width': 1080, 'height': h})
            sc = scenes(k)
            for i, html in enumerate(sc, 1):
                html = html[:-6] + foot(k, i, len(sc)) + '</div>'
                src = OUT / f'{k}-{i:02d}.html'
                src.write_text(f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>{html}')
                await pg.goto(src.as_uri()); await pg.wait_for_timeout(300)
                name = f'basil-ep1-{i:02d}.png' if k == 'c' else f'reel-{i:02d}.png'
                await pg.locator('.s').screenshot(path=str(OUT / name))
        await b.close()

import sys
if '--video-only' not in sys.argv:
    asyncio.run(main())

# Reel: each scene 3.2 s (last 4.5 s) with a slow zoom, 0.5 s crossfades, silent (add music in the Instagram app).
dur = [3.2] * 8 + [4.5]
inputs, filt = [], []
for i, d in enumerate(dur, 1):
    inputs += ['-i', str(OUT / f'reel-{i:02d}.png')]
    frames = int(d * 30)
    filt.append(f"[{i-1}:v]scale=1188:2112,zoompan=z='min(1+0.0009*on,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,setsar=1,format=yuv420p[v{i}]")
chain, off, last = [], 0.0, 'v1'
for i in range(2, len(dur) + 1):
    off += dur[i-2] - 0.5
    out = f'x{i}'
    chain.append(f'[{last}][v{i}]xfade=transition=fade:duration=0.5:offset={off:.2f}[{out}]')
    last = out
cmd = ['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(filt + chain), '-map', f'[{last}]',
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT / 'basil-ep1-reel.mp4')]
subprocess.run(cmd, check=True)
print('ok')
