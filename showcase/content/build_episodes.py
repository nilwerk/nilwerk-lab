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
        "en": dict(KICKER="LOGBOOK · DAY 2 · NUMBER OF THE DAY", H1="Sprint 1, 6 Nov:", H2="7 of 20 done,", H3="9 in review.",
                   INTRO1="Week one of the plant sensor is over.", INTRO2="Nothing is done until a human has merged it.",
                   TILE_A_LABEL="DONE · PLAN, 6 NOV", TILE_A_VALUE="7 / 20", TILE_A_SUB1="3 by the agents,", TILE_A_SUB2="4 by Arsany;", TILE_A_SUB3="done on 6 Nov",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="IN REVIEW · PLAN, 6 NOV", TILE_B_VALUE="9", TILE_B_SUB1="in review in the Plan:", TILE_B_SUB2="7 committed + 2 pulled-in,", TILE_B_SUB3="waiting for a human",
                   TONE_B_TOKEN="warn", STATUS="COUNTED FROM THE PLAN · AS OF 6 NOV",
                   SRC1="Report of Fri 6 Nov: 20 = 3 + 4 done, 7 in review, 1 in progress, 5 not started", SRC2="Plan shows 9 in review: 2 pulled-in tasks included"),
        "de": dict(KICKER="LOGBUCH · TAG 2 · ZAHL DES TAGES", H1="Sprint 1, 6. Nov:", H2="7 von 20 fertig,", H3="9 in Prüfung.",
                   INTRO1="Woche eins des Pflanzensensors ist vorbei.", INTRO2="Fertig ist nichts, bevor ein Mensch es gemergt hat.",
                   TILE_A_LABEL="FERTIG · PLAN, 6. NOV", TILE_A_VALUE="7 / 20", TILE_A_SUB1="3 von den Agenten,", TILE_A_SUB2="4 von Arsany;", TILE_A_SUB3="fertig am 6. Nov",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="IN PRÜFUNG · PLAN, 6. NOV", TILE_B_VALUE="9", TILE_B_SUB1="in Prüfung im Plan:", TILE_B_SUB2="7 zugesagt + 2 vorgezogen,", TILE_B_SUB3="warten auf einen Menschen",
                   TONE_B_TOKEN="warn", STATUS="AUS DEM PLAN GEZÄHLT · STAND 6. NOV",
                   SRC1="Bericht Fr 6. Nov: 20 = 3 + 4 fertig, 7 in Prüfung, 1 in Arbeit, 5 offen", SRC2="Plan zeigt 9 in Prüfung: 2 vorgezogene Aufgaben enthalten")}),
    "2026-11-11": ("day3-saturday-behind-the-scenes", "light", {
        "en": dict(KICKER="LOGBOOK · DAY 3 · BEHIND THE SCENES", H1="A Saturday at", H2="Nilwerk: ten", H3="changes merged.",
                   INTRO1="The team now works seven days a week.", INTRO2="Our founder decides on every merge.",
                   TILE_A_LABEL="WORKING DAYS PER WEEK", TILE_A_VALUE="7", TILE_A_SUB1="since the owner's", TILE_A_SUB2="decision of", TILE_A_SUB3="6 November",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="MERGED · SAT 7 NOV", TILE_B_VALUE="10", TILE_B_SUB1="pull requests merged,", TILE_B_SUB2="as of 20:46,", TILE_B_SUB3="counted in the repo",
                   TONE_B_TOKEN="accent", STATUS="COUNTED FROM THE REPO · AS OF SAT 20:46",
                   SRC1="Team charter, section 7; 10 merges on 7 Nov, as of 20:46", SRC2="Recount on the day of posting; effort figures: see the post"),
        "de": dict(KICKER="LOGBUCH · TAG 3 · HINTER DEN KULISSEN", H1="Ein Samstag bei", H2="Nilwerk: zehn", H3="Merges.",
                   INTRO1="Das Team arbeitet jetzt an sieben Tagen pro Woche.", INTRO2="Unser Gründer entscheidet über jeden Merge.",
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
                   SRC1="Review comments on PRs 41, 44, 46; model report, PR 46", SRC2="Agent time per build: 6 to 16 minutes (measured)"),
        "de": dict(KICKER="LOGBUCH · TAG 5 · FEHLER GEFUNDEN", H1="Prüfung fand", H2="drei Fehler.", H3="Ein Ziel verfehlt.",
                   INTRO1="Fünf Bausteine am 8. Nov, je zweifach geprüft.", INTRO2="Noch keiner übernommen: Das entscheidet ein Mensch.",
                   TILE_A_LABEL="IN DER PRÜFUNG GEFUNDEN", TILE_A_VALUE="3", TILE_A_SUB1="falsche Pinbelegung, falsche", TILE_A_SUB2="Zahl in der Bildunterschrift,", TILE_A_SUB3="ein wertloser Vergleich",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="EDGE-KI RECALL · ZIEL 95 %", TILE_B_VALUE="27-40 %", TILE_B_SUB1="der Nässeereignisse erkannt,", TILE_B_SUB2="Ziel nicht erreicht;", TILE_B_SUB3="Schaltplan-ERC nie gelaufen",
                   TONE_B_TOKEN="warn", STATUS="AUS PRÜFUNGEN GEZÄHLT · STAND 8. NOV · NICHT ÜBERNOMMEN",
                   SRC1="Prüfkommentare PR 41, 44, 46; Modellbericht, PR 46", SRC2="Agentenzeit je Baustein: 6 bis 16 Minuten (gemessen)")}),
    "2026-11-14": ("day6-sprint2-template", "light", {
        "en": dict(KICKER="LOGBOOK · DAY 6 · SPRINT 2 IN NUMBERS", H1="Sprint 2, as of", H2="[day, time]:", H3="the numbers.",
                   INTRO1="SAMPLE LAYOUT: fill the values on the day", INTRO2="from the Plan and the Agent Log.",
                   TILE_A_LABEL="DONE · AS OF [TIME]", TILE_A_VALUE="n / n", TILE_A_SUB1="tasks done of the", TILE_A_SUB2="tasks committed", TILE_A_SUB3="(source: Plan)",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="AGENT MIN · MEASURED", TILE_B_VALUE="n min", TILE_B_SUB1="without the lead's time,", TILE_B_SUB2="from the Agent Log;", TILE_B_SUB3="hours = estimate",
                   TONE_B_TOKEN="warn", STATUS="SAMPLE LAYOUT · FILL ON THE DAY",
                   SRC1="Plan status, merge count, Agent Log: add source and time", SRC2="Recount on the day of posting"),
        "de": dict(KICKER="LOGBUCH · TAG 6 · SPRINT 2 IN ZAHLEN", H1="Sprint 2, Stand", H2="[Tag, Uhrzeit]:", H3="die Zahlen.",
                   INTRO1="MUSTERLAYOUT: Werte am Tag selbst eintragen", INTRO2="aus Plan und Agent Log.",
                   TILE_A_LABEL="FERTIG · STAND [UHRZEIT]", TILE_A_VALUE="n / n", TILE_A_SUB1="Aufgaben fertig von den", TILE_A_SUB2="zugesagten Aufgaben", TILE_A_SUB3="(Quelle: Plan)",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="AGENTEN-MIN · GEMESSEN", TILE_B_VALUE="n min", TILE_B_SUB1="ohne Zeit der Leitung,", TILE_B_SUB2="aus dem Agent Log;", TILE_B_SUB3="Stunden = Schätzung",
                   TONE_B_TOKEN="warn", STATUS="MUSTERLAYOUT · AM TAG AUSFÜLLEN",
                   SRC1="Plan-Status, Merges, Agent Log: Quelle und Zeit eintragen", SRC2="Am Tag des Postens neu zählen")}),
    "2026-11-15": ("day7-how-a-change-moves", "light", {
        "en": dict(KICKER="LOGBOOK · DAY 7 · BEHIND THE SCENES", H1="Who checks the", H2="work of AI", H3="agents?",
                   INTRO1="The path of a code change: builder, architect,", INTRO2="QA, pipeline, then our founder decides.",
                   TILE_A_LABEL="MERGED · SAT 7 NOV", TILE_A_VALUE="13", TILE_A_SUB1="pull requests merged,", TILE_A_SUB2="whole day, counted", TILE_A_SUB3="on 8 Nov, 15:07",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="STEPS OF A CODE CHANGE", TILE_B_VALUE="4", TILE_B_SUB1="architect, QA, pipeline,", TILE_B_SUB2="then a human", TILE_B_SUB3="decides to merge",
                   TONE_B_TOKEN="accent", STATUS="COUNTED · AS OF 8 NOV 15:07",
                   SRC1="TEAM.md section 3; git log of 7 Nov, counted 8 Nov 15:07", SRC2="Recount on the day of posting"),
        "de": dict(KICKER="LOGBUCH · TAG 7 · HINTER DEN KULISSEN", H1="Wer prüft die", H2="Arbeit von", H3="KI-Agenten?",
                   INTRO1="Der Weg einer Codeänderung: Entwickler, Architekt,", INTRO2="QA, Pipeline, dann entscheidet der Gründer.",
                   TILE_A_LABEL="GEMERGT · SA 7. NOV", TILE_A_VALUE="13", TILE_A_SUB1="Pull Requests gemergt,", TILE_A_SUB2="ganzer Tag, gezählt", TILE_A_SUB3="am 8. Nov, 15:07",
                   TONE_A_TOKEN="accent", TILE_B_LABEL="SCHRITTE EINER CODEÄNDERUNG", TILE_B_VALUE="4", TILE_B_SUB1="Architekt, QA, Pipeline,", TILE_B_SUB2="dann entscheidet ein", TILE_B_SUB3="Mensch über den Merge",
                   TONE_B_TOKEN="accent", STATUS="GEZÄHLT · STAND 8. NOV 15:07",
                   SRC1="Team-Charta Abschnitt 3; git log vom 7. Nov, gezählt 8. Nov 15:07", SRC2="Am Tag des Postens neu zählen")}),
}
SIZES = {"portrait-1080x1350": "post-portrait-1080x1350", "linkedin-1200x627": "post-linkedin-1200x627"}

if __name__ == "__main__":
    jobs = []
    for date, (slug, theme, langs) in EPISODES.items():
        if len(sys.argv) > 1 and date not in sys.argv[1:]:
            continue  # optional: render only the given dates (arguments)
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
