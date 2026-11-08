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
        "en": dict(KICKER="LOGBOOK · DAY 2 · NUMBER OF THE DAY", H1="Sprint 1, 6 Nov:", H2="three tasks done,", H3="nine in review.",
                   INTRO1="Week one of the plant sensor is over.", INTRO2="Nothing is done until a human has merged it.",
                   TILE_A_LABEL="DONE · PLAN, 6 NOV", TILE_A_VALUE="3 / 20", TILE_A_SUB1="of the 20 tasks committed", TILE_A_SUB2="for sprint 1 were", TILE_A_SUB3="fully done on 6 Nov",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="IN REVIEW · PLAN, 6 NOV", TILE_B_VALUE="9", TILE_B_SUB1="finished by the agents,", TILE_B_SUB2="checked by architect and QA,", TILE_B_SUB3="waiting for a human",
                   TONE_B_TOKEN="warn", STATUS="COUNTED FROM THE PLAN · AS OF 6 NOV",
                   SRC1="Plan, report of Fri 6 Nov: 20 committed, Done 3, In review 9", SRC2="Not counted: tasks Arsany did himself (1.1-1.4)"),
        "de": dict(KICKER="LOGBUCH · TAG 2 · ZAHL DES TAGES", H1="Sprint 1, 6. Nov:", H2="drei fertig,", H3="neun in Prüfung.",
                   INTRO1="Woche eins des Pflanzensensors ist vorbei.", INTRO2="Fertig ist nichts, bevor ein Mensch es gemergt hat.",
                   TILE_A_LABEL="FERTIG · PLAN, 6. NOV", TILE_A_VALUE="3 / 20", TILE_A_SUB1="der 20 zugesagten Aufgaben", TILE_A_SUB2="aus Sprint 1 waren am", TILE_A_SUB3="6. Nov ganz fertig",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="IN PRÜFUNG · PLAN, 6. NOV", TILE_B_VALUE="9", TILE_B_SUB1="von den Agenten fertig,", TILE_B_SUB2="von Architekt und QA geprüft,", TILE_B_SUB3="warten auf einen Menschen",
                   TONE_B_TOKEN="warn", STATUS="AUS DEM PLAN GEZÄHLT · STAND 6. NOV",
                   SRC1="Plan, Bericht vom Fr 6. Nov: 20 zugesagt, Done 3, In Review 9", SRC2="Nicht gezählt: Arsanys eigene Aufgaben (1.1-1.4)")}),
    "2026-11-11": ("day3-saturday-behind-the-scenes", "light", {
        "en": dict(KICKER="LOGBOOK · DAY 3 · BEHIND THE SCENES", H1="A Saturday at", H2="Nilwerk: ten", H3="changes merged.",
                   INTRO1="The team now works seven days a week.", INTRO2="A human still merges every change.",
                   TILE_A_LABEL="WORKING DAYS PER WEEK", TILE_A_VALUE="7", TILE_A_SUB1="since the owner's", TILE_A_SUB2="decision of", TILE_A_SUB3="6 November",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="MERGED · SAT 7 NOV", TILE_B_VALUE="10", TILE_B_SUB1="pull requests merged,", TILE_B_SUB2="as of 20:46,", TILE_B_SUB3="counted in the repo",
                   TONE_B_TOKEN="accent", STATUS="COUNTED FROM THE REPO · AS OF SAT 20:46",
                   SRC1="Team charter, section 7; 10 merges on 7 Nov, as of 20:46", SRC2="Recount on the day of posting; effort figures: see the post"),
        "de": dict(KICKER="LOGBUCH · TAG 3 · HINTER DEN KULISSEN", H1="Ein Samstag bei", H2="Nilwerk: zehn", H3="Merges.",
                   INTRO1="Das Team arbeitet jetzt an sieben Tagen pro Woche.", INTRO2="Ein Mensch mergt weiterhin jede Änderung.",
                   TILE_A_LABEL="ARBEITSTAGE PRO WOCHE", TILE_A_VALUE="7", TILE_A_SUB1="seit der Entscheidung", TILE_A_SUB2="des Gründers", TILE_A_SUB3="vom 6. November",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="GEMERGT · SA 7. NOV", TILE_B_VALUE="10", TILE_B_SUB1="Pull Requests gemergt,", TILE_B_SUB2="Stand 20:46,", TILE_B_SUB3="im Repo gezählt",
                   TONE_B_TOKEN="accent", STATUS="AUS DEM REPO GEZÄHLT · STAND SA 20:46",
                   SRC1="Team-Charta, Abschnitt 7; 10 Merges am 7. Nov, Stand 20:46", SRC2="Am Tag des Postens neu zählen; Aufwandszahlen: siehe Post")}),
    "2026-11-12": ("day4-decision-data-in-the-eu", "dark", {
        "en": dict(KICKER="LOGBOOK · DAY 4 · A DECISION", H1="Our database is", H2="planned for an", H3="EU region.",
                   INTRO1="A decision from week one. Not live yet,", INTRO2="tested on a local database only.",
                   TILE_A_LABEL="DATABASE REGION · DECIDED", TILE_A_VALUE="EU", TILE_A_SUB1="export and deletion", TILE_A_SUB2="are requirements,", TILE_A_SUB3="not yet built",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="ALTERNATIVES REJECTED", TILE_B_VALUE="3", TILE_B_SUB1="including Firebase", TILE_B_SUB2="and a self-run", TILE_B_SUB3="server",
                   TONE_B_TOKEN="accent", STATUS="DECISION · NOT LIVE · LOCAL TEST ONLY",
                   SRC1="Decision record ADR-003, 3 Nov 2026: Supabase, EU region", SRC2="Helper services may process pseudonymous data outside the EU"),
        "de": dict(KICKER="LOGBUCH · TAG 4 · EINE ENTSCHEIDUNG", H1="Unsere Datenbank", H2="soll in einer", H3="EU-Region liegen.",
                   INTRO1="Eine Entscheidung aus Woche eins. Noch nicht", INTRO2="live, nur lokal getestet.",
                   TILE_A_LABEL="REGION · ENTSCHIEDEN", TILE_A_VALUE="EU", TILE_A_SUB1="Export und Löschung", TILE_A_SUB2="sind Anforderungen,", TILE_A_SUB3="noch nicht gebaut",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="ALTERNATIVEN ABGELEHNT", TILE_B_VALUE="3", TILE_B_SUB1="darunter Firebase", TILE_B_SUB2="und ein selbst", TILE_B_SUB3="betriebener Server",
                   TONE_B_TOKEN="accent", STATUS="ENTSCHEIDUNG · NICHT LIVE · NUR LOKAL GETESTET",
                   SRC1="Entscheidung ADR-003, 3. Nov 2026: Supabase, EU-Region", SRC2="Hilfsdienste können pseudonyme Daten außerhalb der EU verarbeiten")}),
    "2026-11-13": ("day5-caught-mistakes", "light", {
        "en": dict(KICKER="LOGBOOK · DAY 5 · WE CAUGHT A MISTAKE", H1="Review caught", H2="three mistakes.", H3="We missed a target.",
                   INTRO1="Five builds on 8 Nov, each checked by a second agent.", INTRO2="None is merged: a human decides that.",
                   TILE_A_LABEL="CAUGHT BY REVIEW", TILE_A_VALUE="3", TILE_A_SUB1="wrong pin map, wrong caption", TILE_A_SUB2="number, a baseline that", TILE_A_SUB3="proved nothing",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="EDGE-AI RECALL · TARGET 95 %", TILE_B_VALUE="27-40 %", TILE_B_SUB1="of wetting events found,", TILE_B_SUB2="target not met;", TILE_B_SUB3="circuit ERC never run",
                   TONE_B_TOKEN="warn", STATUS="COUNTED FROM REVIEWS · AS OF 8 NOV · NOT MERGED",
                   SRC1="Review comments on PRs 41, 44, 46; model report, PR 46", SRC2="Agent time per build: 6 to 15 minutes (measured)"),
        "de": dict(KICKER="LOGBUCH · TAG 5 · FEHLER GEFUNDEN", H1="Prüfung fand", H2="drei Fehler.", H3="Ein Ziel verfehlt.",
                   INTRO1="Fünf Bausteine am 8. Nov, je zweifach geprüft.", INTRO2="Keiner ist gemergt: Das entscheidet ein Mensch.",
                   TILE_A_LABEL="IN DER PRÜFUNG GEFUNDEN", TILE_A_VALUE="3", TILE_A_SUB1="falsche Pinbelegung, falsche", TILE_A_SUB2="Zahl in der Bildunterschrift,", TILE_A_SUB3="ein wertloser Vergleich",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="EDGE-KI RECALL · ZIEL 95 %", TILE_B_VALUE="27-40 %", TILE_B_SUB1="der Ereignisse erkannt,", TILE_B_SUB2="Ziel nicht erreicht;", TILE_B_SUB3="Schaltplan-ERC nie gelaufen",
                   TONE_B_TOKEN="warn", STATUS="AUS PRÜFBERICHTEN GEZÄHLT · STAND 8. NOV · NICHT GEMERGT",
                   SRC1="Prüfkommentare PR 41, 44, 46; Modellbericht, PR 46", SRC2="Agentenzeit je Baustein: 6 bis 15 Minuten (gemessen)")}),
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
                if lang == "de":  # the template label is English; set the German label
                    svg.write_text(svg.read_text().replace("FOR ENGINEERS", "FÜR INGENIEURE"))
                jobs.append((svg, out / f"{slug}-{lang}-{suf}.png"))
    bp.render_png(jobs)
