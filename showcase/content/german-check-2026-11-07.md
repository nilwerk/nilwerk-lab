# German check of the Logbook posts (A-041 condition), 2026-11-07/08

Checked by Theo (System Architect, an AI agent; not a native-speaker lawyer). Scope: origin story (`showcase/stories/origin/posts.md`, `alt-texts.md`, DE slide texts in `story_content.py`), Logbook days 2-4 (`showcase/content/2026-11-10/11/12/posts.md` and the DE strings of `build_episodes.py`), `series.md`. Affected images were rebuilt (origin DE slides 3, 5, 6, 8, 9, 10 and `linkedin-cover-de.png`); the day 2-4 images needed no change and were rebuilt unchanged.

## Changes

Line numbers refer to the files after the change (posts.md of the origin story: LinkedIn DE block, lines 34-44; `story_content.py`: DE block, lines 87-140; day files as stated).

| File:line | Before | After | Why |
|---|---|---|---|
| origin `posts.md`:34 | "gab er Anforderungen dazu" | "gab er ihr Anforderungen dazu" | Missing dative object; unclear who got the requirements |
| origin `posts.md`:36 | "Platinen-Design" | "Platinendesign" | Same word as on the slide (Kompositum, consistent) |
| origin `posts.md`:40 | "99 Agentenminuten am 3.-5. November" | "vom 3. bis 5. November" | Date range in running text is written out |
| origin `posts.md`:40 | "dieselbe Arbeit etwa 145 Arbeitsstunden von Menschen ohne KI bedeuten würde" | "ein Mensch ohne KI für dieselbe Arbeit etwa 145 Arbeitsstunden bräuchte" | Awkward, hard to read; meaning unchanged, still labelled as an estimate |
| origin `posts.md`:42 | "im schlechtesten Fall 1,4 Monate, Bench-Test steht aus" | "im ungünstigsten Fall 1,4 Monate; ein Labortest steht aus" | Anglicism; "bench" also means a different thing in German; semicolon splits the two statements. Label "Berechnung" kept |
| origin `posts.md`:42 | "Tagesberichte 3.-6. Nov" | "3. bis 6. Nov" | Date range |
| origin `posts.md`:44 | "das Nilwerk Logbuch" | "das Nilwerk-Logbuch" | Name + noun is hyphenated (Durchkopplung) |
| `story_content.py`:87 (slide 3 eng) | "schlechtester Fall ... Bench-Test steht aus. Quelle: Power-Budget" | "ungünstigster Fall ... Labortest steht aus. Quelle: Energiebudget" | Anglicisms, as above |
| `story_content.py`:101 (slide 6) | "Platinen bestückt, flasht und testet, nach Arbeitsaufträgen Schritt für Schritt" | "Platinen bestückt, Firmware aufspielt und testet, Schritt für Schritt nach Arbeitsaufträgen" | "flasht" is slang; word order |
| `story_content.py`:112 (slide 8) | "Auch am Wochenende arbeitet das Team: Unser prüfender KI-Agent fand ..." | "Das Team arbeitet jetzt sieben Tage pro Woche. Ein prüfender KI-Agent fand schon einen falschen Widerstandswert vor jeder Bestellung." | The colon made the resistor finding look like the weekend work (logic error, the EN text has two separate statements); shortened so the slide fits (it overflowed with the longer text) |
| `story_content.py`:120 (slide 5) | "Danach eine Zusammenfassung mit den Fragen ... Etwa eine Stunde seiner Zeit (seine eigene Angabe)." | "Danach die Fragen, die nur Arsany beantworten konnte: etwa eine Stunde seiner Zeit (seine Angabe)." | Slide overflowed by 20 px (the build warned already before this check); fragment joined with a colon |
| `story_content.py`:122 (slide 9 tile) | "Agentenminuten am 3.-5. Nov," | "Agentenminuten, 3. bis 5. Nov.," | Date range |
| `story_content.py`:127 (slide 9 chip) | "SCHÄTZUNG KEIN VERSPRECHEN" | "SCHÄTZUNG, KEIN VERSPRECHEN" | Missing comma |
| `story_content.py`:128 (slide 10) | "mit Beweisen" | "mit Belegen" | "Beweise" is stronger than what we show (UWG caution); EN says "proof", the DE word is softened |
| `story_content.py`:138 (slide 10 poppy) | "Nilwerk Logbuch:" | "Nilwerk-Logbuch:" | Durchkopplung |
| `story_content.py`:140 (timeline, cover) | "Review Sprint 1:" | "Sprint-1-Bilanz:" | Anglicism, hyphenation |
| `story_content.py`:~138 (timeline, cover) | "bekommen Jobs" | "bekommen Rollen" | Anglicism |
| `content/2026-11-10/posts.md`:25 | "(ein Arbeitsblock von einer Woche)" | "(ein einwöchiger Arbeitsblock)" | Plain German |
| `content/2026-11-10/posts.md`:25 | "Neun weitere waren ... erledigt, ... geprüft und warteten ..." | "Neun weitere hatten unsere KI-Agenten erledigt, die Agenten ... hatten sie geprüft, und sie warteten ..." | Broken sentence structure (two subjects in one chain) |
| `content/2026-11-10/posts.md`:29 | "etwa 151 Agentenminuten gearbeitet" | "etwa 151 Minuten gearbeitet" | Tautology (agents worked agent minutes); still "gemessen" |
| `content/2026-11-11/posts.md`:29 | "dieselbe Arbeit für einen erfahrenen Ingenieur ohne KI etwa 70 Arbeitsstunden von Menschen bedeutet hätte" | "ein erfahrener Ingenieur ohne KI für dieselbe Arbeit etwa 70 Stunden gebraucht hätte" | Redundant ("Ingenieur" + "von Menschen"); label "Schätzung" unchanged |
| `content/2026-11-12/posts.md`:23 | "für eine Plattform für Konten, Messwerte und die Regeln, wer was sehen darf, entschieden, mit der Datenbank in einer EU-Region" | "für eine Plattform entschieden, die Konten, Messwerte und die Regeln dafür verwaltet, wer was sehen darf. Die Datenbank soll in einer EU-Region liegen." | Unreadable nested sentence; "soll" keeps the "planned, not live" status exact |
| `content/2026-11-12/posts.md`:27 | "Row-Level-Security, Auth, ... Ingest-Funktion" | "zeilenbasierte Zugriffskontrolle mit Row Level Security, Anmeldung, ... Funktion zur Datenannahme" | Plain word first, product term kept; "Auth", "Ingest" are jargon |
| `content/2026-11-12/posts.md`:27 | "Dokument Stack und Kosten" | "Dokument „Stack und Kosten“" | Document title in quotes |

`build_episodes.py` (DE strings of days 2-4) and `alt-texts.md` and `series.md` needed no change (series.md has no German text).

## Checked and left as is

- Register: informal "du/euch/deine" throughout, no "Sie" anywhere. Consistent.
- UWG: no superlatives or comparisons with competitors; all numbers carry their label (gemessen / geschätzt / berechnet / gezählt); "Ehrliche Zahlen" is a self-description, not a claim, but a lawyer may prefer "Zahlen mit Beschriftung".
- Kept on purpose: "mergen/gemergt" (developer jargon; plain alternative would be "zusammenführen" or "übernehmen", it appears in a headline pun "Menschen mergen" and in the flow chip, so it needs Arsany's taste call), "Pull Request" (explained on slide 5), "Prompt", "Pipeline", "Sprint", "Wireframes", "Full-Stack", "Edge Functions", "Repo-Historie", and the Plan status words "Done / In Review" (quoted Plan labels).
- Nilwerk series name "Nilwerk Logbuch, Tag N" at the start of the day posts is a title and stays unhyphenated; running text uses "Nilwerk-Logbuch". Arsany may prefer one form everywhere.
- Slide fit: after the changes `build_story.py` reports no overflow; looked at DE slides 5, 6, 8, 9 and the cover by eye. Day 2-4 images unchanged.

## Not verified

- I am not a native speaker and not a lawyer: UWG, Heilmittel/health-claim and Markenrecht questions are not legally reviewed. "Pseudonyme Daten" are personal data under GDPR; the post says they may leave the EU, wording not reviewed by a data-protection lawyer.
- Facts and numbers (99 min, 145 h, 151 min, 48 min, 10 merges, PR numbers) were not re-checked against reports; that is the claim-check files' job. Open items I noticed: "Nicht gestartet 5" plus 3 done plus 9 in review is 17 of 20 (day 2 posts); "Jede Codeänderung ... von QA getestet" is a process claim for all changes (day 3).
- Not re-rendered: LinkedIn EN images and Instagram text (no changes needed). Spelling checked by reading, not with a dictionary tool.

## Verdict per post (all "approved for publishing after Arsany's OK", with the notes above)

| Post | Verdict |
|---|---|
| Day 1 origin story: LinkedIn DE, Instagram DE line, alt texts DE, DE slides 1-10, DE cover | Approved for publishing after Arsany's OK; he decides the "mergen" question |
| Day 2 (Tue 10 Nov): LinkedIn DE, Instagram DE line, DE images | Approved after Arsany's OK; recheck the 3 + 9 + 5 of 20 wording before posting |
| Day 3 (Wed 11 Nov): LinkedIn DE, Instagram DE line, DE images | Approved after Arsany's OK; recount merges on the posting day |
| Day 4 (Thu 12 Nov): LinkedIn DE, Instagram DE line, DE images | Approved after Arsany's OK; data-protection wording not legally reviewed |
