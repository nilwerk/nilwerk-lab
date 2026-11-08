# Agent Diary ("Meet the team"): concept, rules, week 1 plan

Author: Poppy · 2026-11-08 · answers Arsany's A-049 (binding): "more engaging posts that would catch the eye: more visuals, connect it to the real world, make it more alive; let each agent talk about a great achievement each day, or a funny story from the virtual work environment". **Drafts only. Nothing is published or scheduled; Arsany approves and publishes. German text is UNCHECKED until Theo or Nora have checked it.**

## The idea in three lines

1. **One short card per agent per day**, in that agent's persona voice (`team/PERSONAS.md`): face (the real avatar), a speech bubble, **one achievement of the day** from real evidence, a status chip and the two-layer text (plain first, "For engineers" second).
2. **Optionally a clearly labelled FICTION story** "From the virtual office": a joke about the agents' imagined workplace. Always dark theme, dashed orange banner "FICTION · IMAGINED BY OUR AGENTS · NOT A REAL EVENT".
3. **Real-world hooks**: real app screenshots, a real pin map from a real datasheet, a live progress tracker of real PR states, and a shot list of photos and 10-20 s clips for our hardware integrator and Arsany (`shotlist.md`). Illustrations are labelled "ILLUSTRATION, NOT A PHOTO".

It runs **next to the Nilwerk Logbook** (`../series.md`): the Logbook stays the numbered company story (one episode a day, LinkedIn first); the Diary is the human-sized, visual companion (Instagram feed and Stories first, LinkedIn short version). Same facts, same claim-check discipline, different face.

## The rules (also in `team/learnings/pr-social.md`)

1. **Achievements carry a source**: a PR and comment id (or a CI run) in `claim-check.md`, plus the as-of date. No source, no card. Public text says "review of 8 Nov" rather than showing PR numbers on the image (brand rule); ids stay in the claim-check (decision pending, see `needs-arsany-ready.md`).
2. **Real evidence only**: PR, test count, a caught mistake, a measured number. Honest misses count as achievements ("we missed the target" is a post).
3. **Fiction is fiction**: stories from the virtual office are labelled FICTION in the image and in the first line of the text ("imagined by our agents"), are always in the dark theme, never borrow a real result, never claim a real person, customer, quote or event, and never appear without the label. A fiction card never carries a real number.
4. **Persona voice is Poppy's drafting**: speech-bubble words are written from the evidence in the agent's voice; they are not verbatim log lines, and the card says so ("PERSONA VOICE · WRITTEN FROM THE EVIDENCE"). Never put invented words in a real person's mouth (Arsany, Peter, anyone): only the AI personas speak.
5. **Two layers**: plain story first, "For engineers" (DE: "Für Ingenieure") second, with caveats and what is not run.
6. **No confidential data**: nothing from customers, leads, prices, Needs-Arsany content, A-IDs, secrets or private URLs. Humans: "our hardware integrator", the founder; no other names, faces or voices without OK.
7. **Honest about the loop**: "AI agents, led and reviewed by humans" on every card; do not write "merged by a human" unless the merger is known (the GitHub login is a shared account).
8. **Photos and video are real or labelled**: real photos only with the integrator's/Arsany's OK; illustrations say "ILLUSTRATION, NOT A PHOTO"; any AI-generated image gets the platform AI flag (none used here: all images are code-drawn).
9. **Recount on the day**: every status, merge state and count is "as of 8 Nov 16:10"; recheck before posting (command in `../DAILY.md`).

## Week 1 (Mon 9 to Sun 15 Nov 2026), facts as of 8 Nov 16:10

| Day | Agent | Achievement of the day (real evidence) | Extra visual | Logbook same day | Status |
|---|---|---|---|---|---|
| Mon 9 | Leo (full-stack) | Account screens: 54 checks pass, 7.4 min agent time, merged 8 Nov, stand-in backend | real screenshots (3 phones) | Day 1 origin story | drafted |
| Tue 10 | Mira (firmware + edge AI) | Honest miss: 27 % val / 40 % test vs 95 % target | none (the number is the picture) | Day 2 number | drafted |
| Wed 11 | Emil (PCB) | AHT20 pin catch (4 pins vs 6) before any board; first ERC run clean; founder ordered the first real part (to confirm) | then-vs-now pin diagram; Story card "the first real part" | Day 3 Saturday | drafted |
| Thu 12 | Sana (cloud AI) | 26 of 26 deliberate bugs caught; a real bug (new owner kept the old owner's plant) found by comparing two copies | none | Day 4 EU data | drafted |
| Fri 13 | Yara (3D) | Battery bay 7.2 mm, 22 tests, design rule "function first, one touch of design" | progress tracker (5 builds, 2 merged) | Day 5 caught mistakes | drafted |
| Sat 14 | Kai (pipeline) | The circuit check had never run (EACCES); fix merged; first ERC run exit 0 | FICTION card: the kettle failed its review | Day 6 sprint 2 numbers | drafted |
| Sun 15 | Theo (architect) | NFR-01 relaxed rule written into ten documents (ADR-015) | Story card: Nora, "two Lead sessions collided" (true) | Day 7 who checks | drafted |

Reserve cards (not built): Theo's catch of an invented quote in Poppy's own draft, Ines' own 12 bugs (7 survived), Poppy herself. Max (sales) appears only as fiction, never with real outreach.

Rhythm: weekdays alternate feed card and Story; weekend = lighter tone. The first week is a test: after it, look at reach and saves (DAILY.md section 4) and keep or drop the format.

## Files

- `posts.md`: all 7 days, EN and DE (DE unchecked), Instagram captions, alt text, image names.
- `claim-check.md`: every number, name and date with source (PR and comment ids), type and as-of.
- `shotlist.md`: what real photos and 10-20 s clips to shoot, per frame, with safety and consent notes.
- `needs-arsany-ready.md`: the rows to paste into the Needs Arsany tab.
- `diary_data.py`, `build_diary.py`, `check_bbox.js`: the generator (texts in the data file, layout in the builder, automatic overflow check).
- `images/`: 29 PNG + SVG at 1080x1350 (9 diary cards EN/DE, then-vs-now, tracker, real screenshots, illustration, fiction card each EN/DE, plus an internal shot-list board; 29 PNG + SVG).

Rebuild: `NW_FONT_DIR=<node_modules>/@fontsource python3 -I build_diary.py` from this folder (needs Node playwright in `NODE_PATH`, as for the other builders), then `python3 -I ../../brand/check_svg_wellformed.py`.
