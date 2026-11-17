#!/usr/bin/env python3
"""Poppy, 2026-11-17: first rough cut of the 25 s vertical video 'The guard that could never fire'.

Offline only: frames are HTML rendered by headless Chrome (reuses build_pack.py), the sound is
synthesised with numpy (original little chiptune bed + effects, no samples, no licences), the cut is
made with ffmpeg. No text-to-speech engine exists in this environment, so there is NO voice-over:
the voice-over lines are burned in as captions and the recording is a to-do (see video-script.md).
Run: python3 -I build_video.py   (from this folder)
"""
import subprocess, wave
from pathlib import Path
import numpy as np
import build_pack as bp
from build_pack import wrap, render, avatar, FOOT, CSS

HERE = Path(__file__).resolve().parent
VID = HERE / "video"
FR = VID / "frames"
FR.mkdir(parents=True, exist_ok=True)
bp.OUT = FR  # render frames into video/frames

W, H = 1080, 1920
PAD = "padding-top:150px"


def chips(real=False):
    return ('<div class="top" style="margin-top:150px"><span class="kick">THE CREW HAS A LIFE &middot; EP 1</span>'
            '<span class="fic">FICTIONAL CREW LIFE &middot; REAL ENGINEERING</span></div><div style="height:170px"></div>')


def bubble(key, text, side="l", size=52):
    return (f'<div style="display:flex;gap:26px;align-items:flex-start;{"flex-direction:row-reverse;" if side=="r" else ""}">'
            f'<div style="text-align:center">{avatar(key,230)}<div class="who" style="font-size:26px">{bp.NAMES[key][1]}</div></div>'
            f'<div class="bub {side}" style="flex:1;font-size:{size}px;padding:26px 30px;border-radius:34px">{text}</div></div>')


def realbox(label, big, text, bigsize=84):
    return (f'<div class="fact" style="padding:30px 34px"><div class="lab" style="font-size:24px">REAL &middot; {label}</div>'
            f'<div style="font-weight:800;font-size:{bigsize}px;letter-spacing:-.03em;margin:10px 0 6px;line-height:1">{big}</div>'
            f'<p style="font-size:34px;line-height:1.25">{text}</p></div>')


def capt(t):
    return f'<div style="position:absolute;left:56px;right:56px;bottom:300px;font-size:40px;font-weight:700;line-height:1.25;text-align:center;background:#15181d;color:#fff;border-radius:22px;padding:20px 26px">{t}</div>'


frames = []  # (name, seconds)


def frame(name, body, secs):
    render(name, wrap(body, W, H), W, H)
    frames.append((name, secs))


def build_frames():
    frame("f1", chips() + f"""<div class="h" style="font-size:120px;margin:50px 0 60px">One real bug.<br><span style="color:var(--accent)">Two stubborn</span><br>engineers.</div>
{bubble("ines","<b>Show me the log.</b>","l",64)}
<div style="height:40px"></div>{capt("Tuesday 17 November 2026. The crew are AI agents; their drama is made up.")}""", 3.5)
    frame("f2", chips() + f"""<div style="height:40px"></div>{bubble("mira","My guard drops a batch the server keeps rejecting. So one bad batch can never block us.","l",46)}
<div style="height:50px"></div>{realbox("HOW THE DEVICE WORKS","Every 15 min","the sensor stores a new sample. A retry waits at least as long.",92)}
{capt("Mira's guard counted the newest sample. Spot the problem?")}""", 4.5)
    # counter frames
    cells = lambda n: "".join(f'<span style="display:inline-block;width:96px;height:96px;border-radius:18px;border:5px solid var(--ink);background:{"var(--accent)" if i<4 else "var(--warnsoft)"};margin:6px"></span>' for i in range(n))
    frame("f3a", chips() + f"""<div style="height:40px"></div>{bubble("ines","Six rejects in a row. Watch the buffer.","r",52)}
<div style="height:40px"></div><div class="panel" style="padding:30px"><div class="mono" style="font-size:26px;font-weight:700;color:var(--accent)">REAL &middot; QA'S REPRODUCTION</div>
<div style="font-size:150px;font-weight:800;letter-spacing:-.04em;line-height:1">4 <span style="font-size:60px;color:var(--muted)">samples waiting</span></div><div>{cells(4)}</div>
<div class="mono" style="font-size:30px;font-weight:700;margin-top:16px;color:var(--warn)">guard fired: NO</div></div>{capt("Every retry, a new sample arrives.")}""", 1.0)
    for n in range(5, 11):
        frame(f"f3_{n}", chips() + f"""<div style="height:40px"></div>{bubble("ines","Six rejects in a row. Watch the buffer.","r",52)}
<div style="height:40px"></div><div class="panel" style="padding:30px"><div class="mono" style="font-size:26px;font-weight:700;color:var(--accent)">REAL &middot; QA'S REPRODUCTION</div>
<div style="font-size:150px;font-weight:800;letter-spacing:-.04em;line-height:1;color:{"var(--warn)" if n>=9 else "var(--ink)"}">{n} <span style="font-size:60px;color:var(--muted)">samples waiting</span></div><div>{cells(n)}</div>
<div class="mono" style="font-size:30px;font-weight:700;margin-top:16px;color:var(--warn)">guard fired: NO</div></div>{capt("The counter resets. The guard never fires." if n==10 else "Every retry, a new sample arrives.")}""", 0.5 if n < 10 else 1.2)
    frame("f4", chips() + f"""<div style="height:40px"></div>{bubble("mira","...Count from the <b>oldest</b> sample, not the newest. Fine. You were right.","l",50)}
<div style="height:50px"></div>{realbox("AFTER THE FIX","3rd reject = batch dropped","QA re-ran the same case: the guard now fires and the buffer is cleared.",70)}
{capt("Fixed the same morning. Re-checked by QA.")}""", 4.0)
    frame("f5", chips() + f"""<div style="height:30px"></div><div class="mono" style="font-size:28px;font-weight:700;background:var(--accent);color:#fff;display:inline-block;border-radius:999px;padding:8px 20px">MEASURED, 17 NOV 2026 &middot; HOST TESTS ON A PC</div>
<div style="height:30px"></div>
<div class="fact" style="margin-bottom:26px;padding:30px"><div style="font-size:120px;font-weight:800;letter-spacing:-.04em;line-height:1">622</div><p style="font-size:38px">checks pass in the upload tests</p></div>
<div class="fact" style="margin-bottom:26px;padding:30px"><div style="font-size:120px;font-weight:800;letter-spacing:-.04em;line-height:1">49 / 49</div><p style="font-size:38px">deliberate bugs caught (it was 45; none covered this one)</p></div>
<div class="warnbox" style="font-size:32px;padding:22px 26px">Not run on a real device yet. No Wi-Fi code exists yet.</div>
{capt("Real engineering underneath the fun.")}""", 4.0)
    frame("f6", f"""<div style="margin-top:360px;text-align:center"><div style="display:inline-block;width:220px;height:220px">{(HERE.parents[1]/"brand"/"logo"/"nilwerk-mark.svg").read_text().replace('width="128" height="128"','width="220" height="220"')}</div>
<div class="h" style="font-size:150px;margin:20px 0">nil<span style="color:var(--accent)">werk</span></div>
<div style="font-size:54px;font-weight:700;line-height:1.2;margin:30px 60px">Fictional crew life.<br><span style="color:var(--accent)">Real engineering.</span></div>
<div style="font-size:36px;font-weight:600;color:var(--muted);margin:30px 90px;line-height:1.3">AI crew, led and reviewed by humans.<br>The characters' private lives are made up.</div>
<div class="mono" style="font-size:36px;font-weight:700;margin-top:40px">@nilwerk &middot; nilwerk.de</div></div>""", 4.5)


# ------------------------------------------------------------------ audio
SR = 44100


def t_(d):
    return np.linspace(0, d, int(SR * d), endpoint=False)


def env(n, a=0.005, r=0.08):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def tone(f, d, kind="tri", vol=0.3, a=0.005, r=0.08):
    t = t_(d)
    if kind == "sq":
        w = np.sign(np.sin(2 * np.pi * f * t)) * 0.6
    elif kind == "saw":
        w = 2 * ((f * t) % 1) - 1
    elif kind == "tri":
        w = 2 * np.abs(2 * ((f * t) % 1) - 1) - 1
    else:
        w = np.sin(2 * np.pi * f * t)
    return w * env(len(t), a, r) * vol


def put(buf, sig, at):
    i = int(at * SR)
    buf[i:i + len(sig)] += sig[:max(0, len(buf) - i)]


def build_audio(total, cues):
    buf = np.zeros(int(total * SR))
    # music bed: C - G - Am - F arpeggio, 8th notes at 104 bpm, triangle + quiet square bass; plays low under everything
    beat = 60 / 104
    chords = [(130.81, [261.63, 329.63, 392.0]), (98.0, [196.0, 246.94, 293.66]), (110.0, [220.0, 261.63, 329.63]), (87.31, [174.61, 220.0, 261.63])]
    t0, bar = 0.0, 0
    while t0 < total - 0.2:
        root, notes = chords[bar % 4]
        put(buf, tone(root, beat * 2, "sq", 0.05, 0.01, 0.2), t0)
        for k in range(8):
            put(buf, tone(notes[k % 3] * (2 if k % 4 == 3 else 1), beat / 2 * 0.9, "tri", 0.07, 0.004, 0.05), t0 + k * beat / 2)
        t0 += beat * 4
        bar += 1
    # effects at cue times
    for kind, at in cues:
        if kind == "sting":  # two-note question sting
            put(buf, tone(392, 0.18, "sq", 0.22), at); put(buf, tone(523.25, 0.45, "sq", 0.22, r=0.3), at + 0.18)
        elif kind == "tick":
            put(buf, tone(1800, 0.03, "sq", 0.25, 0.001, 0.02), at)
        elif kind.startswith("blip"):
            n = int(kind[4:]); put(buf, tone(300 + 60 * n, 0.12, "sq", 0.22, 0.002, 0.06), at)
        elif kind == "buzz":
            put(buf, tone(95, 0.55, "saw", 0.3, 0.01, 0.2), at); put(buf, tone(101, 0.55, "saw", 0.2, 0.01, 0.2), at)
        elif kind == "ding":
            put(buf, tone(1046.5, 0.5, "sin", 0.3, 0.002, 0.4), at); put(buf, tone(1568, 0.6, "sin", 0.2, 0.002, 0.5), at + 0.1)
        elif kind == "tada":
            for j, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
                put(buf, tone(f, 0.25 if j < 3 else 0.7, "sq", 0.18, 0.003, 0.2), at + j * 0.11)
        elif kind == "whoosh":
            n = int(0.35 * SR); noise = np.random.RandomState(3).uniform(-1, 1, n) * np.linspace(0, 1, n) ** 2 * np.linspace(1, 0, n) ** 0.5 * 0.18
            put(buf, noise, at)
        elif kind == "chime":
            for j, f in enumerate([783.99, 987.77, 1318.5]):
                put(buf, tone(f, 1.2, "sin", 0.2, 0.003, 0.9), at + j * 0.12)
    # fade out last second, normalise to -3 dBFS peak
    fo = int(SR * 1.0); buf[-fo:] *= np.linspace(1, 0, fo)
    buf = buf / max(1e-9, np.abs(buf).max()) * 0.707
    return (buf * 32767).astype(np.int16)


def main():
    build_frames()
    total = sum(d for _, d in frames)
    # cue times
    starts, acc = {}, 0.0
    for n, d in frames:
        starts[n] = acc
        acc += d
    cues = [("sting", 0.05), ("whoosh", starts["f2"]), ("tick", starts["f2"] + 2.2), ("tick", starts["f2"] + 2.7), ("tick", starts["f2"] + 3.2), ("tick", starts["f2"] + 3.7),
            ("whoosh", starts["f3a"])]
    for n in range(5, 11):
        cues.append((f"blip{n}", starts[f"f3_{n}"]))
    cues += [("buzz", starts["f3_10"] + 0.1), ("whoosh", starts["f4"]), ("ding", starts["f4"] + 2.4), ("tada", starts["f5"]), ("chime", starts["f6"])]
    wav = VID / "soundtrack.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(build_audio(total, cues).tobytes())
    lst = VID / "frames.txt"
    lst.write_text("".join(f"file 'frames/{n}.png'\nduration {d}\n" for n, d in frames) + f"file 'frames/{frames[-1][0]}.png'\n")
    out = VID / "rough-cut_the-guard-that-could-never-fire.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(wav),
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    print("video", out, f"{total:.1f}s")


if __name__ == "__main__":
    main()
