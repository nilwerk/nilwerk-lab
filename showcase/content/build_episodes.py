#!/usr/bin/env python3
"""Render the images of the Nilwerk Logbook episodes (days 2-4) from the approved v0.1 post templates, EN and DE.
Run: NW_FONT_DIR=<node_modules>/@fontsource python3 -I build_episodes.py     (code-generated images, no AI flag needed)
Texts and claim sources: content/<date>/posts.md and claim-check.md. Values here must match those files.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "brand"))
import build_post as bp  # noqa: E402

COMMON = {"en": dict(HANDLE="@nilwerk · nilwerk.de", FOOT_NOTE="AI agents, led and reviewed by humans"),
          "de": dict(HANDLE="@nilwerk · nilwerk.de", FOOT_NOTE="KI-Agenten, geleitet und geprüft von Menschen")}

EPISODES = {
    "2026-11-10": ("day2-sprint1-number", "light", {
        "en": dict(KICKER="LOGBOOK · DAY 2 · NUMBER OF THE DAY", H1="Sprint 1: three", H2="tasks done, nine", H3="waiting for review.",
                   INTRO1="Week one of the plant sensor is over.", INTRO2="Nothing is done until a human has merged it.",
                   TILE_A_LABEL="DONE · PLAN, 6 NOV", TILE_A_VALUE="3 / 20", TILE_A_SUB1="of the 20 tasks committed", TILE_A_SUB2="for sprint 1", TILE_A_SUB3="are fully done",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="IN REVIEW · PLAN, 6 NOV", TILE_B_VALUE="9", TILE_B_SUB1="finished by the agents,", TILE_B_SUB2="checked by architect and QA,", TILE_B_SUB3="waiting for a human",
                   TONE_B_TOKEN="warn", STATUS="COUNTED FROM THE PLAN · AS OF 6 NOV",
                   SRC1="Sprint 1: 20 committed, Done 3, In review 9", SRC2="Agent time in the sprint: about 151 min (measured)"),
        "de": dict(KICKER="LOGBUCH · TAG 2 · ZAHL DES TAGES", H1="Sprint 1: drei", H2="Aufgaben fertig,", H3="neun in Prüfung.",
                   INTRO1="Woche eins des Pflanzensensors ist vorbei.", INTRO2="Fertig ist nichts, bevor ein Mensch es gemergt hat.",
                   TILE_A_LABEL="FERTIG · PLAN, 6. NOV", TILE_A_VALUE="3 / 20", TILE_A_SUB1="der 20 zugesagten Aufgaben", TILE_A_SUB2="aus Sprint 1", TILE_A_SUB3="sind ganz fertig",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="IN PRÜFUNG · PLAN, 6. NOV", TILE_B_VALUE="9", TILE_B_SUB1="von den Agenten fertig,", TILE_B_SUB2="von Architekt und QA geprüft,", TILE_B_SUB3="warten auf einen Menschen",
                   TONE_B_TOKEN="warn", STATUS="AUS DEM PLAN GEZÄHLT · STAND 6. NOV",
                   SRC1="Sprint 1: 20 zugesagt, Done 3, In Review 9", SRC2="Agentenzeit im Sprint: etwa 151 min (gemessen)")}),
    "2026-11-11": ("day3-saturday-behind-the-scenes", "light", {
        "en": dict(KICKER="LOGBOOK · DAY 3 · BEHIND THE SCENES", H1="A Saturday at", H2="Nilwerk: seven", H3="changes merged.",
                   INTRO1="The team now works seven days a week.", INTRO2="A human still merges every change.",
                   TILE_A_LABEL="WORKING DAYS PER WEEK", TILE_A_VALUE="7", TILE_A_SUB1="since the owner's", TILE_A_SUB2="decision of", TILE_A_SUB3="6 November",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="MERGED · SAT 7 NOV", TILE_B_VALUE="7", TILE_B_SUB1="pull requests merged", TILE_B_SUB2="by a human,", TILE_B_SUB3="counted in the repo",
                   TONE_B_TOKEN="accent", STATUS="COUNTED FROM THE REPO HISTORY",
                   SRC1="Team charter, section 7; merge commits of 7 Nov 2026", SRC2="Effort figures: see the post (measured vs estimated)"),
        "de": dict(KICKER="LOGBUCH · TAG 3 · HINTER DEN KULISSEN", H1="Ein Samstag bei", H2="Nilwerk: sieben", H3="Merges.",
                   INTRO1="Das Team arbeitet jetzt an sieben Tagen pro Woche.", INTRO2="Ein Mensch mergt weiterhin jede Änderung.",
                   TILE_A_LABEL="ARBEITSTAGE PRO WOCHE", TILE_A_VALUE="7", TILE_A_SUB1="seit der Entscheidung", TILE_A_SUB2="des Inhabers", TILE_A_SUB3="vom 6. November",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="GEMERGT · SA 7. NOV", TILE_B_VALUE="7", TILE_B_SUB1="Pull Requests von", TILE_B_SUB2="einem Menschen gemergt,", TILE_B_SUB3="im Repo gezählt",
                   TONE_B_TOKEN="accent", STATUS="AUS DER REPO-HISTORIE GEZÄHLT",
                   SRC1="Team-Charta, Abschnitt 7; Merge-Commits vom 7. Nov 2026", SRC2="Aufwandszahlen: siehe Post (gemessen vs geschätzt)")}),
    "2026-11-12": ("day4-decision-data-in-the-eu", "dark", {
        "en": dict(KICKER="LOGBOOK · DAY 4 · A DECISION", H1="Where does your", H2="plant's data live?", H3="In the EU.",
                   INTRO1="A decision from week one: one backend,", INTRO2="hosted in the EU. Not live yet.",
                   TILE_A_LABEL="DATA HOSTED IN", TILE_A_VALUE="EU", TILE_A_SUB1="one region, with", TILE_A_SUB2="export and deletion", TILE_A_SUB3="as a requirement",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="ALTERNATIVES REJECTED", TILE_B_VALUE="3", TILE_B_SUB1="including Firebase", TILE_B_SUB2="and running our", TILE_B_SUB3="own server",
                   TONE_B_TOKEN="accent", STATUS="DECISION · NOT YET LIVE",
                   SRC1="Decision record dated 3 Nov 2026: Supabase, EU region", SRC2="Tested on a local database only; not on a live project"),
        "de": dict(KICKER="LOGBUCH · TAG 4 · EINE ENTSCHEIDUNG", H1="Wo liegen die", H2="Daten deiner", H3="Pflanze? In der EU.",
                   INTRO1="Eine Entscheidung aus Woche eins: ein Backend,", INTRO2="gehostet in der EU. Noch nicht live.",
                   TILE_A_LABEL="DATEN GEHOSTET IN", TILE_A_VALUE="EU", TILE_A_SUB1="eine Region, mit Export", TILE_A_SUB2="und Löschung als", TILE_A_SUB3="Anforderung",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="ALTERNATIVEN ABGELEHNT", TILE_B_VALUE="3", TILE_B_SUB1="darunter Firebase", TILE_B_SUB2="und ein eigener", TILE_B_SUB3="Server",
                   TONE_B_TOKEN="accent", STATUS="ENTSCHEIDUNG · NOCH NICHT LIVE",
                   SRC1="Entscheidungsdokument vom 3. Nov 2026: Supabase, EU-Region", SRC2="Nur auf lokaler Datenbank getestet; nicht auf Live-Projekt")}),
}
SIZES = {"portrait-1080x1350": "post-portrait-1080x1350", "linkedin-1200x627": "post-linkedin-1200x627"}

if __name__ == "__main__":
    jobs = []
    for date, (slug, theme, langs) in EPISODES.items():
        out = HERE / date / "images"
        out.mkdir(parents=True, exist_ok=True)
        for lang, fields in langs.items():
            for suf, tpl in SIZES.items():
                svg = out / f"{slug}-{lang}-{suf}.svg"
                bp.build(tpl, dict(fields, **COMMON[lang]), theme, svg)
                jobs.append((svg, out / f"{slug}-{lang}-{suf}.png"))
    bp.render_png(jobs)
