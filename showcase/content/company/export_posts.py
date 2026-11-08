#!/usr/bin/env python3
"""Write posts.md from company_data.py (single source of the texts). Run: python3 -I export_posts.py"""
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from company_data import POSTS

DE1 = {"p1-why": "Auf Deutsch: Warum es Nilwerk gibt, in vier Folien.",
       "p2-who": "Auf Deutsch: Lernt unser Team kennen, elf KI-Agenten und zwei Menschen.",
       "p3-how": "Auf Deutsch: Ein Tag bei Nilwerk, vom Plan um 07:30 bis zum Ja des Gründers."}
SLOT = {"p1-why": "Mon 9 Nov 2026, 10:00 Berlin", "p2-who": "Tue 10 Nov 2026, 10:00 Berlin", "p3-how": "Wed 11 Nov 2026, 10:00 Berlin"}
out = ["# Company posts, days 1-3 (Mon 9 to Wed 11 Nov 2026)", "",
       "Author: Poppy. Drafts only: nothing is scheduled or published. Facts as of Sun 8 Nov 2026, 18:54 Berlin; every claim has a row in `claim-check.md`. "
       "Speech bubbles are persona voice, written from the evidence, never a quote of a human. **German text is UNCHECKED until Theo or Nora have checked it.** "
       "One post per day: Instagram (1080x1350 carousel, 4 slides); Arsany takes the same PNGs and the same text for LinkedIn.", "",
       "Rebuild images: `NW_FONT_DIR=<node_modules>/@fontsource NODE_PATH=<playwright dir> python3 -I build_company.py`. Rebuild this file: `python3 -I export_posts.py`.", ""]
for k, p in POSTS.items():
    out += [f"## Day {p['day']}: {p['title']['en']} / {p['title']['de']}", "",
            f"- Slot: **{SLOT[k]}** (Metricool best-time data peaks at 10:00 on weekdays; see `calendar.md`).",
            f"- Images EN: " + ", ".join(f"`images/{k}-s{i}-en.png`" for i in range(1, 5)),
            f"- Images DE (unchecked): " + ", ".join(f"`images/{k}-s{i}-de.png`" for i in range(1, 5)),
            "- Instagram: carousel of the 4 EN images in order; AI flag not needed (all images are code-drawn, avatars are the team's own drawings).", "",
            "### Instagram caption (EN + one German line)", "", "```", p["caption"]["en"] + "\n\n" + DE1[k], "```", "",
            "### LinkedIn text EN (same text; Arsany adds it with the same PNGs)", "", "```", p["caption"]["en"].rsplit("\n#", 1)[0].strip().rsplit("\n\nnilwerk.de", 1)[0] + "\n\nnilwerk.de · @nilwerk", "```", "",
            "### LinkedIn text DE (UNCHECKED)", "", "```", p["caption"]["de"], "```", "",
            "### Alt text per slide (EN / DE)", ""]
    for i, a in enumerate(p["alt"], 1):
        out += [f"{i}. EN: {a['en']}", f"   DE: {a['de']}"]
    out.append("")
pathlib.Path(__file__).with_name("posts.md").write_text("\n".join(out), encoding="utf-8")
print("posts.md written")
