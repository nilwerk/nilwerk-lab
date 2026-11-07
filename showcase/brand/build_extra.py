#!/usr/bin/env python3
"""Fill and render the extra templates: Instagram story, carousel slide, six 16:9 slides.
  python3 -I build_extra.py     (needs NW_FONT_DIR = .../node_modules/@fontsource and Node playwright, see build_post.py)
Outputs: previews/story-1080x1920-sample.png, previews/carousel-1080x1350-sample.png,
         slides/png/*.png (sample text, light and dark), slides/png-clean/*.png (art only, no text: use as slide backgrounds).
Sample text is placeholder content for demonstration, not a post to publish.
"""
import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_post as v01  # noqa: E402  (tokens + render helpers of v0.1, unchanged)

STAT = (HERE / "brand-status.css").read_text()


def tokens(theme):
    def block(css, start):
        i = css.index(start)
        return css[css.index("{", i) + 1: css.index("}", i)]

    def parse(t):
        return dict(re.findall(r"--nw-([a-z-]+):\s*(#[0-9a-fA-F]{6})", t))

    tk = {**parse(block(v01.CSS, ":root {")), **parse(block(STAT, ":root {"))}
    if theme == "dark":
        tk.update(parse(block(v01.CSS, ':root[data-theme="dark"]')))
        tk.update(parse(block(STAT, ':root[data-theme="dark"]')))
    return tk


MONO = {"KICKER": (0.6, 0.05, 0.9), "STATUS": (0.6, 0.05, 0.8)}


def fill(svg, f, theme):
    f = dict(f)
    # chip widths from the font size found next to each placeholder (mono: 0.6 em + letter spacing)
    for key in ("KICKER", "STATUS"):
        m = re.search(r'font-size="([\d.]+)" letter-spacing="([\d.]+)"[^>]*>\{\{%s\}\}' % key, svg)
        if m:
            fs, ls = float(m.group(1)), float(m.group(2))
            pad = fs * 2.0 if key == "KICKER" else fs * 1.9
            f[f"{key}_W"] = round(len(f.get(key, "")) * (0.6 * fs + ls) + pad) if f.get(key) else 0
    f.setdefault("ALT", " ".join(f.get(k, "") for k in ("H1", "H2", "H3")).strip() or "Nilwerk template")
    tk = tokens(theme)
    f.setdefault("TONE_A", "var(--nw-warn)")
    f.setdefault("TONE_B", "var(--nw-accent)")

    def sub(mo):
        k = mo.group(1)
        v = f.get(k, "")
        return str(v) if k.endswith("_W") or k.startswith("TONE_") else html.escape(str(v), quote=True)

    svg = re.sub(r"\{\{([A-Z0-9_]+)\}\}", sub, svg)
    return re.sub(r"var\(--nw-([a-z-]+)\)", lambda mo: tk[mo.group(1)], svg)


COMMON = dict(HANDLE="@nilwerk · nilwerk.de", FOOT_NOTE="AI agents, led and reviewed by humans")

STORY = dict(COMMON, KICKER="CAUGHT IN REVIEW · HARDWARE", H1="A review caught", H2="a charger resistor", H3="before any order.",
             INTRO1="A tiny part sets how fast the battery charges.", INTRO2="Our reviewing AI agent flagged the wrong value.",
             TILE_A_LABEL="BEFORE · R9 = 1.2 kOhm", TILE_A_VALUE="~0.9 A", TILE_A_SUB1="about 0.9C on a 1000 mAh cell,", TILE_A_SUB2="flagged in review",
             TILE_B_LABEL="AFTER · R9 = 2.4 kOhm", TILE_B_VALUE="458 mA", TILE_B_SUB1="0.46C, from R = 1100 / I", TILE_B_SUB2="worst case 527 mA (+15 % tolerance)",
             STATUS="CALCULATED · NOT YET BENCH-TESTED", SRC1="R9 sets charge current, R = 1100 / I (charger datasheet)", SRC2="Calculated, not yet measured on a real board")

CAROUSEL = dict(COMMON, KICKER="HOW WE CHECK", N="2", TOTAL="5", H1="Every part gets", H2="a second look.",
                P1="Our reviewing AI agent reads each", P2="design change against the requirements.", P3="Wrong value? It is flagged before", P4="anything is ordered.",
                E1="Review: architect agent, requirement IDs,", E2="line-level findings on the pull request.", E3="Then QA, then pipeline, then a human", E4="approves and merges.",
                STATUS="SAMPLE TEXT · NOT A CLAIM", SRC1="Sample slide for the template", SWIPE="Swipe →")

FOOT = dict(FOOT_L="PLACEHOLDER DECK TEXT · sample values, not a claim", FOOT_R="nilwerk.de")
SLIDES = {
    "slide-1-title": dict(FOOT, KICKER="DEMO · SAMPLE", H1="A plant sensor,", H2="built by AI agents,", H3="checked by humans.",
                          SUB1="Prototype status, plain words first,", SUB2="numbers and sources for engineers."),
    "slide-2-section": dict(FOOT, NUM="02", H1="The backend,", H2="in short.", PLAIN1="Where the sensor data is stored,", PLAIN2="and who is allowed to see it.",
                            SRC1="Supabase (PostgreSQL), row-level security", SRC2="Local test run; not yet on a live project"),
    "slide-3-key-number": dict(FOOT, TILE_LABEL="TABLES WITH RLS", TILE_VALUE="14 / 14", TILE_SUB1="all tables of our own", TILE_SUB2="database schema,", TILE_SUB3="checked by the test run",
                               H1="One user cannot", H2="read another", H3="user's plants.", INTRO1="Tested by letting user A try everything", INTRO2="it should not be able to do.",
                               STATUS="TESTED ON LOCAL POSTGRES 16 · NOT YET LIVE", SRC1="Local PostgreSQL 16 run: RLS + retention tests", SRC2="Auth, scheduler, storage stubbed locally; not on live Supabase"),
    "slide-4-two-column": dict(FOOT, H1="How the data is protected", L1="Each user only sees their own plants.", L2="We test this by trying to break it.",
                               L3="Not yet checked on the live system.", L4="A person approves every change.",
                               R1="RLS enabled on 14 / 14 tables", R2="B's rows: 0 of A's attempts succeed",
                               R3="Retention: raw 3 months, hourly 12 months", R4="Stubbed locally: auth, scheduler, storage", R5="Next: run on a real Supabase project",
                               STATUS="TESTED LOCALLY · NOT YET LIVE"),
    "slide-5-architecture": dict(FOOT, H1="System overview", FRAME_HINT="Insert diagram here (export from Mermaid / draw.io as PNG or SVG)",
                                 PLAIN1="Sensor, phone app and cloud, in one picture.", PLAIN2="Arrows show where the data travels.",
                                 SRC1="Source: docs/architecture (link in speaker notes)", SRC2="Diagram status: draft", STATUS="DRAFT DIAGRAM"),
    "slide-6-closing": dict(FOOT, H1="Thank you.", H2="Next step?", SUB1="Tell us about your idea,", SUB2="we answer with a plan and proof.",
                            C1="nilwerk.de", C2="@nilwerk", C3="@nilwerk", C4="name@example.com", FOOT_NOTE="AI agents, led and reviewed by humans"),
}


def main():
    jobs = []
    (HERE / "previews").mkdir(exist_ok=True)
    for name, tpl, data, theme in (("story-1080x1920", "templates/story-1080x1920.svg", STORY, "dark"),
                                   ("carousel-1080x1350", "templates/carousel-1080x1350.svg", CAROUSEL, "light")):
        svg = fill((HERE / tpl).read_text(), data, theme)
        out = HERE / "previews" / f"{name}-sample.svg"
        out.write_text(svg)
        jobs.append((out, HERE / "previews" / f"{name}-sample.png"))
    (HERE / "slides" / "png").mkdir(parents=True, exist_ok=True)
    (HERE / "slides" / "png-clean").mkdir(parents=True, exist_ok=True)
    tmp = HERE / "slides" / ".tmp"
    tmp.mkdir(exist_ok=True)
    for name, data in SLIDES.items():
        tpl = (HERE / "slides" / "templates" / f"{name}.svg").read_text()
        for theme in (("light", "dark") if name in ("slide-1-title", "slide-6-closing") else ("light",)):
            for kind, d in (("sample", data), ("clean", {})):
                if kind == "clean":
                    d = {"ALT": "Nilwerk slide background (no text)"}
                svg = fill(tpl, d, theme)
                f = tmp / f"{name}-{theme}-{kind}.svg"
                f.write_text(svg)
                folder = "png" if kind == "sample" else "png-clean"
                jobs.append((f, HERE / "slides" / folder / f"{name}-{theme}-{kind}.png"))
    v01.render_png(jobs, scale=1)
    for f in tmp.glob("*.svg"):
        f.unlink()
    tmp.rmdir()
    for f in (HERE / "previews").glob("*-sample.svg"):
        f.unlink()


if __name__ == "__main__":
    main()
