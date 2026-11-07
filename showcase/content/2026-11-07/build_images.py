#!/usr/bin/env python3
"""Render the 2026-11-07 post images from the brand templates (code-generated, no AI imagery).
Run: NW_FONT_DIR=<node_modules/@fontsource> python3 -I build_images.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "brand"))
import build_post as bp  # noqa: E402

COMMON = dict(HANDLE="@nilwerk · nilwerk.de", FOOT_NOTE="AI agents, led and reviewed by humans")

POSTS = {
    "post1-r9-review-catch": ("light", dict(
        KICKER="CAUGHT IN REVIEW · HARDWARE",
        H1="A review caught", H2="a charger resistor", H3="before any order.",
        INTRO1="R9 sets the charge current of a 1000 mAh cell.",
        INTRO2="Our reviewer flagged 1.2 kOhm as too high.",
        TILE_A_LABEL="BEFORE · R9 = 1.2 kOhm", TILE_A_VALUE="~0.9 A",
        TILE_A_SUB1="about 0.9C on a", TILE_A_SUB2="1000 mAh cell,", TILE_A_SUB3="flagged in review",
        TONE_A_TOKEN="warn",
        TILE_B_LABEL="AFTER · R9 = 2.4 kOhm", TILE_B_VALUE="458 mA",
        TILE_B_SUB1="0.46C, from R = 1100 / I", TILE_B_SUB2="worst case 527 mA", TILE_B_SUB3="(+15 % tolerance)",
        TONE_B_TOKEN="accent",
        STATUS="CALCULATED · NOT YET BENCH-TESTED",
        SRC1="Source: BOM draft rev. 2 and review, 6-7 Nov 2026", SRC2="Formula from the charger datasheet; bench test pending",
        **COMMON)),
    "post2-rls-proof": ("dark", dict(
        KICKER="TESTED · BACKEND SCAFFOLD",
        H1="User A cannot", H2="read user B's", H3="plant data.",
        INTRO1="Row-level security on every table,",
        INTRO2="proved by a test, not by a promise.",
        TILE_A_LABEL="TABLES WITH RLS", TILE_A_VALUE="14 / 14",
        TILE_A_SUB1="every table in the", TILE_A_SUB2="schema, checked by", TILE_A_SUB3="the test run",
        TONE_A_TOKEN="accent",
        TILE_B_LABEL="FOREIGN ROWS SEEN", TILE_B_VALUE="0",
        TILE_B_SUB1="A tries to read, change,", TILE_B_SUB2="delete or forge rows of B:", TILE_B_SUB3="all refused",
        TONE_B_TOKEN="accent",
        STATUS="TESTED ON LOCAL POSTGRES 16 · NOT YET LIVE",
        SRC1="Source: cloud test run, 7 Nov 2026 (RLS + retention)", SRC2="Not yet run on a real Supabase project",
        **COMMON)),
}
SIZES = {"portrait-1080x1350": "post-portrait-1080x1350", "linkedin-1200x627": "post-linkedin-1200x627", "square-1080x1080": "post-square-1080x1080"}

jobs = []
(HERE / "images").mkdir(exist_ok=True)
for name, (theme, fields) in POSTS.items():
    for suffix, tpl in SIZES.items():
        svg = HERE / "images" / f"{name}-{suffix}.svg"
        bp.build(tpl, fields, theme, svg)
        jobs.append((svg, HERE / "images" / f"{name}-{suffix}.png"))
bp.render_png(jobs)
