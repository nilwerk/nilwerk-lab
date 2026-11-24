# Draft pack 24 Nov 2026: "The reviewers caught what the builders missed"

**Status: DRAFT. Not published, not scheduled, not for posting.** Open before posting: owner approval, technical check, native German check, recount of every number on the day of posting. As of 24 Nov 2026, evening Berlin time.

Image status: no image exists yet. The slides below are text cards to be built from the approved brand templates (code-generated, not AI imagery). If any AI-made image is added later, it must be labelled "AI-generated". No real photo of the bench exists in this pack.

Public text carries no file names, task numbers or first names. Sources are named in the claim tables as "where from".

---

## LinkedIn, English (layer 1: the story)

The reviewers caught what the builders missed.

Our AI agents build a plant-monitor app and its cloud and firmware parts. On 24 November two builders worked in a morning round and again in an afternoon round. Nothing they wrote went forward without a review chain: an architect review, a QA pass that re-runs the whole test suite and plants deliberate bugs ("mutants") that the tests must catch, and a pipeline check.

Three real catches from that day:

1. A leftover import broke the code-style check. The automated pipeline caught it and it was fixed in one round.
2. A reviewer said a decision was still open. That was wrong, and it was corrected against our written decision log.
3. An error message in the app said "the key was not created". But if a reply gets lost on the way, the key may well have been created. The wording and the reload behaviour were fixed.

None of these is dramatic. That is the point: small mistakes are cheap when someone else looks.

And the bench? Our real Raspberry Pi test bench ran today. The board was flashed, set up, advertised over Bluetooth and printed its wake line. The phone got the app. Then the app-flow step failed before the app even launched, because the test automation server on the Pi did not answer. So: partial success, one honest red step. A health check that names that cause in one line is built, and tested offline, but not yet run on the Pi.

Not done yet: the 30- and 90-day line chart. The data does not have a daily series yet, so its scope waits for the owner's decision. Nothing ran on a phone or against a live backend.

AI agents, led and reviewed by humans.

**For engineers** (as of 24 Nov 2026, Berlin)
- App, premium dashboard: bar graphs for the soil range and a first-week versus last-week comparison, with handling for missing readings. Full app suite: 443 tests passing on the merged state; 475 with the new "Connect your AI" screen, which is not merged yet. Not run on a phone or a live backend. (source: test runs, 24 Nov)
- Cloud, analytics endpoint: premium-only, the premium check runs before any reading is touched. Local tests 13 + 7 + 13 passing (endpoint, adapter, aggregates); not run against a live backend. Watering-event rule: a soil rise of 10 percentage points or more; readings more than 2 hours apart do not join. Boundary tests at exactly 10 points and exactly 2 hours; 6 of 6 deliberate-bug checks caught. (source: local test runs and QA pass, 24 Nov)
- Firmware boot-loop guard: pure C, host tests only. 433 checks, 46 of 46 deliberate bugs caught; it compiles for the ESP32-C3 in CI. Not wired into the firmware yet; never run on a board. (source: CI run and QA pass, 24 Nov)
- Bench pipeline: manual run on the current main, 24 Nov. Passed: flash, provisioning, Bluetooth advertising, serial wake line, app install. Failed: app-flow step, automation server on the Pi did not answer. (source: pipeline run, 24 Nov)
- Time: no measured total for the day is quoted here.

---

## LinkedIn, Deutsch (Ebene 1: die Geschichte)

Die Prüfer haben gefunden, was die Entwickler übersehen haben.

Unsere KI-Agenten bauen eine App zur Pflanzenüberwachung samt Cloud- und Firmware-Teilen. Am 24. November haben zwei Entwickler in einer Vormittags- und einer Nachmittagsrunde gearbeitet. Nichts davon ging ohne Prüfkette weiter: ein Architektur-Review, ein QA-Durchlauf, der die gesamte Testsuite neu startet und absichtlich Fehler einbaut („Mutanten“), die die Tests bemerken müssen, und eine Pipeline-Prüfung.

Drei echte Funde dieses Tages:

1. Ein übrig gebliebener Import hat die Stilprüfung des Codes gebrochen. Die automatische Pipeline hat es gefunden, in einer Runde war es behoben.
2. Ein Prüfer meinte, eine Entscheidung sei noch offen. Das war falsch und wurde anhand unseres schriftlichen Entscheidungsprotokolls korrigiert.
3. Eine Fehlermeldung in der App sagte: „Der Schlüssel wurde nicht erstellt.“ Geht aber eine Antwort unterwegs verloren, kann der Schlüssel sehr wohl erstellt worden sein. Wortlaut und Neuladen wurden korrigiert.

Nichts davon ist dramatisch. Genau darum geht es: Kleine Fehler sind billig, wenn jemand anderes hinschaut.

Und der Prüfstand? Unser echter Raspberry-Pi-Prüfstand lief heute. Die Platine wurde geflasht, eingerichtet, hat sich per Bluetooth gemeldet und ihre Startzeile ausgegeben. Das Telefon bekam die App. Dann ist der Schritt „App-Ablauf“ gescheitert, noch bevor die App startete, weil der Test-Automatisierungsserver auf dem Pi nicht geantwortet hat. Also: Teilerfolg, ein ehrlich roter Schritt. Eine Gesundheitsprüfung, die diese Ursache in einer klaren Zeile nennt, ist gebaut und offline getestet, aber noch nicht auf dem Pi gelaufen.

Noch nicht gebaut: das Liniendiagramm für 30 und 90 Tage. Die Daten haben noch keine Tagesreihe, deshalb wartet der Umfang auf die Entscheidung des Inhabers. Nichts lief auf einem Telefon oder gegen ein echtes Backend.

KI-Agenten, geleitet und geprüft von Menschen.

**Für Ingenieure** (Stand 24.11.2026, Berlin)
- App, Premium-Dashboard: Balkendiagramme für den Bodenfeuchte-Bereich und den Vergleich erste gegen letzte Woche, mit Behandlung fehlender Messwerte. Gesamte App-Testsuite: 443 Tests bestanden auf dem gemergten Stand; 475 mit dem neuen Bildschirm „Connect your AI“, noch nicht gemergt. Nicht auf einem Telefon oder echtem Backend gelaufen. (Quelle: Testläufe, 24.11.)
- Cloud, Analyse-Endpunkt: nur Premium, die Premium-Prüfung läuft, bevor ein Messwert gelesen wird. Lokale Tests 13 + 7 + 13 bestanden (Endpunkt, Adapter, Aggregate); nicht gegen ein echtes Backend gelaufen. Regel für Gießereignisse: Anstieg der Bodenfeuchte um mindestens 10 Prozentpunkte; Messwerte mit mehr als 2 Stunden Abstand werden nicht verbunden. Grenztests bei genau 10 Punkten und genau 2 Stunden; 6 von 6 absichtlichen Fehlern gefunden. (Quelle: lokale Testläufe und QA-Durchlauf, 24.11.)
- Firmware-Schutz gegen Boot-Schleifen: reines C, nur Host-Tests. 433 Prüfungen, 46 von 46 absichtlichen Fehlern gefunden; kompiliert in CI für den ESP32-C3. Noch nicht in die Firmware eingebunden; nie auf einer Platine gelaufen. (Quelle: CI-Lauf und QA-Durchlauf, 24.11.)
- Prüfstand-Pipeline: manueller Lauf auf dem aktuellen Stand, 24.11. Bestanden: Flashen, Einrichtung, Bluetooth-Werbung, serielle Startzeile, App-Installation. Gescheitert: Schritt App-Ablauf, der Automatisierungsserver auf dem Pi antwortete nicht. (Quelle: Pipeline-Lauf, 24.11.)
- Zeit: Für den Tag wird keine gemessene Gesamtzahl genannt.

---

## Instagram carousel (outline, 5 slides, 4:5; text cards from brand templates, not AI imagery; no image built yet)

Caption (EN): The reviewers caught what the builders missed. Three real catches from one day of our AI agent team, and one honest red step on the bench. AI agents, led and reviewed by humans. Details in the "For engineers" slide. @nilwerk nilwerk.de

Caption (DE): Die Prüfer haben gefunden, was die Entwickler übersehen haben. Drei echte Funde eines Tages unseres KI-Agenten-Teams und ein ehrlich roter Schritt am Prüfstand. KI-Agenten, geleitet und geprüft von Menschen. Details auf der Folie „Für Ingenieure“. @nilwerk nilwerk.de

| Slide | Text on card (EN / DE) | Alt text (EN / DE) |
|---|---|---|
| 1 | The reviewers caught what the builders missed. / Die Prüfer fanden, was die Entwickler übersahen. | EN: Title card on a light background with the line "The reviewers caught what the builders missed." DE: Titelkarte auf hellem Hintergrund mit dem Satz „Die Prüfer fanden, was die Entwickler übersahen.“ |
| 2 | Catch 1: a leftover import broke the code-style check. The pipeline caught it. Fixed in one round. / Fund 1: Ein übrig gebliebener Import brach die Stilprüfung. Die Pipeline fand es. In einer Runde behoben. | EN: Text card, catch one, a leftover import and the pipeline that caught it. DE: Textkarte, Fund eins, ein übrig gebliebener Import und die Pipeline, die ihn fand. |
| 3 | Catch 2 and 3: a reviewer wrongly said a decision was open; the decision log corrected it. An error said "key not created", but a lost reply could mean it was; wording and reload fixed. / Fund 2 und 3: Ein Prüfer hielt eine Entscheidung fälschlich für offen; das Entscheidungsprotokoll korrigierte es. Eine Meldung sagte „Schlüssel nicht erstellt“, obwohl er bei verlorener Antwort erstellt sein kann; Wortlaut und Neuladen korrigiert. | EN: Text card with two catches, a wrong claim corrected against the decision log and a misleading error message fixed. DE: Textkarte mit zwei Funden, eine falsche Behauptung gegen das Entscheidungsprotokoll korrigiert und eine irreführende Fehlermeldung verbessert. |
| 4 | Bench today: flashed, set up, Bluetooth, wake line, app installed. Then the app-flow step failed: the automation server on the Pi did not answer. One honest red step. / Prüfstand heute: geflasht, eingerichtet, Bluetooth, Startzeile, App installiert. Dann scheiterte der App-Ablauf: Der Automatisierungsserver auf dem Pi antwortete nicht. Ein ehrlich roter Schritt. | EN: Text card with a checklist: five green steps and one red step, labelled partial success. DE: Textkarte mit einer Liste: fünf grüne Schritte und ein roter Schritt, als Teilerfolg bezeichnet. |
| 5 | For engineers: 443 app tests passing (475 with an unmerged screen); endpoint tests 13 + 7 + 13; boot-loop guard 433 checks, 46 of 46 deliberate bugs caught. Host and local tests only; nothing on a phone or live backend. Source: CI and test runs, 24 Nov. AI agents, led and reviewed by humans. / Für Ingenieure: 443 App-Tests bestanden (475 mit einem nicht gemergten Bildschirm); Endpunkt-Tests 13 + 7 + 13; Boot-Schleifen-Schutz 433 Prüfungen, 46 von 46 absichtlichen Fehlern gefunden. Nur Host- und lokale Tests; nichts auf Telefon oder echtem Backend. Quelle: CI- und Testläufe, 24.11. KI-Agenten, geleitet und geprüft von Menschen. | EN: Number card with the test counts and the line "host and local tests only". DE: Zahlenkarte mit den Testzahlen und dem Hinweis „nur Host- und lokale Tests“. |

---

## Claim sources

Types: measured = a test or CI run result; observed = seen in a run or review; decision = a recorded owner decision. Nothing in this pack is simulated or estimated.

| Claim | Type | Where from |
|---|---|---|
| Two builders, a morning round and an afternoon round, each change reviewed by architect, QA (full suite re-run plus deliberate bugs) and pipeline check | observed | Review comments and pipeline runs, 24 Nov |
| Leftover import broke the lint step, caught by CI, fixed in one round | observed | CI run and fix round, 24 Nov |
| Reviewer's "decision still open" claim was wrong, corrected against the decision log | observed | Review thread and decision log, 24 Nov |
| Error message "key was not created" could be wrong after a lost reply; wording and reload fixed | observed | Review thread and fix round, 24 Nov |
| App: bar graphs (soil range, first week vs last week), missing readings handled | observed | App tests, 24 Nov |
| 30/90-day line chart not built; no daily series in the data contract; scope awaits owner decision | decision | Review thread, 24 Nov |
| 443 app tests on merged state; 475 with the unmerged "Connect your AI" screen | measured | App test run, 24 Nov |
| Not run on a phone or live backend (app and endpoint) | observed | Test notes, 24 Nov |
| Endpoint premium-only, premium check before any reading is touched | measured | Local tests and review, 24 Nov |
| Endpoint tests 13 + 7 + 13 passing | measured | Local test runs, 24 Nov |
| Watering rule: rise of 10 percentage points or more; readings over 2 hours apart do not join | decision | Owner decision, applied in the cloud code, 24 Nov |
| Boundary tests at exactly 10 points and exactly 2 hours; 6 of 6 deliberate bugs caught | measured | QA pass, 24 Nov |
| Boot-loop guard: 433 checks, 46 of 46 deliberate bugs caught (host tests, pure C) | measured | CI run and QA pass, 24 Nov |
| Boot-loop guard compiles for the ESP32-C3 in CI; not wired into firmware; never run on a board | measured / observed | CI run, 24 Nov |
| Bench: flash, provisioning, Bluetooth advertising, serial wake line, app install passed | measured | Bench pipeline run on main, 24 Nov |
| Bench: app-flow step failed because the automation server on the Pi did not answer | measured | Bench pipeline run on main, 24 Nov |
| Health check naming that cause built and tested offline, not run on the Pi | observed | Pipeline notes, 24 Nov |
| No time figure quoted | none | The day's measured total was not found in a daily report at drafting time |

## Open before posting
- Owner approval; technical check; native German check.
- Recount on the posting day, especially test counts (the 475 screen may be merged by then) and the bench step (it may be green by then).
- Build the slide images from the brand templates; run the brand and contrast checks. Instagram needs a media URL that the scheduling tool can read.
