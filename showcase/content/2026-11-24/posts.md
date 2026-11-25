# Draft pack 24 Nov 2026: "Three checks, one of them caught our own reviewer"

**Status: DRAFT. Not published, not scheduled, not for posting.** Open before posting: owner approval, technical check, native German check, and a **recount on the posting day** (several changes below are in review and may be merged, or change, by then; the bench step may be green by then). As of 24 Nov 2026, evening Berlin time.

Image status: no image exists yet. The cards below are text cards to be built from the approved brand templates (code-generated, not AI imagery). If an AI-made image is added later, it must be labelled "AI-generated". No real photo of the bench is in this pack.

Public text carries no file names, task numbers or first names. Sources are named in the claim tables ("where from"), which are for the reviewers, not for posting. Every number says whether it is on the main branch ("on main") or only in an open change ("in review").

---

## LinkedIn, English (layer 1: the story)

Three checks, one of them caught our own reviewer.

Our AI agents build a plant-monitor app with cloud and firmware parts. On 24 November several builder agents worked, and every change went through a review chain: an architect review, a QA pass that re-runs the whole test suite and plants deliberate bugs ("mutants") that the tests must catch, and a pipeline check.

Three real catches from that day, and who was wrong each time:

1. A machine check caught a builder's mistake. A leftover import broke the code-style check in the automated pipeline. It was fixed in one round.
2. A reviewer was wrong. The architect said a decision was still open. It was not, and the claim was corrected against the owner's recorded decision. We are telling you because the chain should check the reviewers too.
3. A reviewer caught a builder's miss. An error message in the app said "the key was not created". But if a reply gets lost on the way, the key may well have been created. The wording was fixed, and the screen now reloads the key list from the server after a lost reply. This screen was tested against a mocked backend only; the server function that creates and revokes keys does not exist yet.

None of these is dramatic. That is the point: small mistakes are cheap when someone else looks, and sometimes the someone is wrong too.

And the bench? Our real Raspberry Pi test bench ran today, on the current main branch. The board was flashed, set up, advertised over Bluetooth and printed its wake line. The phone got the app. Then the app-flow step failed before the app even launched, because the test automation server on the Pi did not answer. So: partial success, one step stayed red. A health check that names that cause in one clear line is built and tested offline. It is in review, not merged, and not yet run on the Pi.

Not done yet: the 30- and 90-day line chart. The data has no daily series yet, so the scope waits for the owner's decision. Nothing ran on a phone or against a live backend.

AI agents, led and reviewed by humans. A human approves this post before it goes out.

**For engineers** (as of 24 Nov 2026, Berlin; "on main" or "in review" for every number)
- App, premium dashboard (on main): bar graphs for the soil range and a first-week versus last-week comparison, with handling for missing readings. Full app suite: 443 tests passing on main (source: CI run, 24 Nov). Not run on a phone or a live backend.
- App, new "Connect your AI" screen (in review, not merged): 475 tests passing with it. Tested against a mocked backend only; the key create and revoke server function does not exist yet. (source: QA local run, 24 Nov)
- Cloud, analytics endpoint (on main): premium-only; the premium check runs before any reading is touched (local test with a fake database client). 13 endpoint tests passing. Not run against a live backend. (source: merged change and its QA pass, 24 Nov)
- Cloud, watering rule (in review, not merged): a soil rise of 10 percentage points or more, readings more than 2 hours apart do not join; on main the rule still counts only rises above 10. In the open change: adapter tests 7, aggregate tests 13, boundary tests at exactly 10 points and exactly 2 hours, 6 of 6 deliberate bugs caught (scratch mutants, not the CI mutation suite). (source: QA pass on the open change, 24 Nov)
- Firmware boot-loop guard (in review, not merged): pure C, host tests only. 433 checks, 46 of 46 deliberate bugs caught; compiles for the ESP32-C3 in CI. Not wired into the firmware; never run on a board. (source: QA pass and CI run on the open change, 24 Nov)
- Bench pipeline (on main, manual run, 24 Nov): passed flash, provisioning, Bluetooth advertising, serial wake line, app install. Failed: the app-flow step, the automation server on the Pi did not answer. (source: pipeline run, 24 Nov)
- Time: no measured total for the day is quoted here.

---

## LinkedIn, Deutsch (Ebene 1: die Geschichte)

Drei Prüfungen, und eine davon hat unseren eigenen Prüfer korrigiert.

Unsere KI-Agenten bauen eine App zur Pflanzenüberwachung samt Cloud- und Firmware-Teilen. Am 24. November haben mehrere Entwickler-Agenten gearbeitet, und jede Änderung durchlief eine Prüfkette: ein Architektur-Review, einen QA-Durchlauf, der die gesamte Testsuite erneut ausführt und absichtlich Fehler einbaut („Mutanten“), die die Tests erkennen müssen, und eine Pipeline-Prüfung.

Drei echte Funde dieses Tages, und wer jeweils falsch lag:

1. Eine automatische Prüfung fand den Fehler eines Entwicklers. Ein übrig gebliebener Import ließ die Code-Stilprüfung in der Pipeline fehlschlagen. In einer Runde war es behoben.
2. Ein Prüfer lag falsch. Der Architekt meinte, eine Entscheidung sei noch offen. Das stimmte nicht, und die Aussage wurde anhand der festgehaltenen Entscheidung des Inhabers korrigiert. Wir erzählen das, weil die Kette auch die Prüfer prüfen soll.
3. Ein Prüfer fand einen Fehler eines Entwicklers. Eine Fehlermeldung in der App lautete: „Der Schlüssel wurde nicht erstellt.“ Geht aber eine Antwort unterwegs verloren, kann der Schlüssel sehr wohl erstellt worden sein. Der Wortlaut wurde korrigiert, und der Bildschirm lädt nach einer verlorenen Antwort die Schlüsselliste neu vom Server. Dieser Bildschirm wurde nur gegen ein simuliertes Backend getestet; die Server-Funktion zum Erstellen und Widerrufen von Schlüsseln gibt es noch nicht.

Nichts davon ist dramatisch. Genau darum geht es: Kleine Fehler sind billig, wenn jemand anderes hinschaut, und manchmal irrt sich auch dieser andere.

Und der Prüfstand? Unser echter Raspberry-Pi-Prüfstand lief heute mit dem aktuellen Stand des Hauptzweigs. Die Platine wurde geflasht, eingerichtet, hat sich per Bluetooth gemeldet und ihre Startzeile ausgegeben. Auf dem Telefon wurde die App installiert. Dann ist der Schritt „App-Ablauf“ gescheitert, noch bevor die App startete, weil der Test-Automatisierungsserver auf dem Pi nicht geantwortet hat. Also: Teilerfolg, ein Schritt blieb rot. Eine Funktionsprüfung (Health-Check), die diese Ursache in einer klaren Zeile nennt, ist gebaut und offline getestet. Sie ist noch in der Prüfung, nicht übernommen, und noch nicht auf dem Pi gelaufen.

Noch nicht gebaut: das Liniendiagramm für 30 und 90 Tage. Die Daten enthalten noch keine tageweise Zeitreihe, deshalb wartet der Umfang auf die Entscheidung des Inhabers. Nichts lief auf einem Telefon oder gegen ein echtes Backend.

KI-Agenten, geleitet und geprüft von Menschen. Ein Mensch gibt diesen Beitrag frei, bevor er erscheint.

**Für Ingenieure** (Stand 24.11.2026, Berlin; bei jeder Zahl „im Hauptzweig“ oder „in Prüfung“)
- App, Premium-Dashboard (im Hauptzweig): Balkendiagramme für den Bodenfeuchte-Bereich und den Vergleich der ersten mit der letzten Woche, einschließlich des Umgangs mit fehlenden Messwerten. Gesamte App-Testsuite: 443 Tests bestanden im Hauptzweig (Quelle: CI-Lauf, 24.11.). Weder auf einem Telefon noch gegen ein echtes Backend gelaufen.
- App, neuer Bildschirm „Connect your AI“ (in Prüfung, nicht übernommen): Mit diesem Bildschirm: 475 Tests bestanden. Nur gegen ein simuliertes Backend getestet; die Server-Funktion zum Erstellen und Widerrufen von Schlüsseln gibt es noch nicht. (Quelle: lokaler QA-Lauf, 24.11.)
- Cloud, Analyse-Endpunkt (im Hauptzweig): nur Premium; die Premium-Prüfung läuft, bevor ein Messwert gelesen wird (lokaler Test mit simuliertem Datenbank-Client). 13 Endpunkt-Tests bestanden. Nicht gegen ein echtes Backend gelaufen. (Quelle: übernommene Änderung und ihr QA-Durchlauf, 24.11.)
- Cloud, Regel für Gießereignisse (in Prüfung, nicht übernommen): Anstieg der Bodenfeuchte um mindestens 10 Prozentpunkte; Messwerte mit mehr als 2 Stunden Abstand werden nicht verbunden; im Hauptzweig zählt die Regel bisher nur Anstiege über 10. In der offenen Änderung: Adapter-Tests 7, Aggregat-Tests 13, Grenztests bei genau 10 Punkten und genau 2 Stunden, 6 von 6 absichtlichen Fehlern gefunden (ad hoc erzeugte Mutanten, nicht die Mutationssuite in CI). (Quelle: QA-Durchlauf der offenen Änderung, 24.11.)
- Firmware-Schutz gegen Boot-Schleifen (in Prüfung, nicht übernommen): reines C, nur Host-Tests. 433 Prüfungen, 46 von 46 absichtlichen Fehlern gefunden; kompiliert in CI für den ESP32-C3. Nicht in die Firmware eingebunden; nie auf einer Platine gelaufen. (Quelle: QA-Durchlauf und CI-Lauf der offenen Änderung, 24.11.)
- Prüfstand-Pipeline (im Hauptzweig, manueller Lauf, 24.11.): Bestanden: Flashen, Einrichtung, Bluetooth-Advertising, serielle Startzeile, App-Installation. Gescheitert: Schritt App-Ablauf, der Automatisierungsserver auf dem Pi antwortete nicht. (Quelle: Pipeline-Lauf, 24.11.)
- Zeit: Für den Tag wird keine gemessene Gesamtzahl genannt.

---

## Instagram carousel (outline, 5 cards per language; text cards from brand templates, not AI imagery; no image built yet)

EN and DE are separate carousels (separate cards), so each card stays short enough for a phone. Both captions carry the human-review line.

Caption (EN): Three checks, one of them caught our own reviewer. A machine check, a reviewer's mistake and a builder's miss from one day of our AI agent team, plus one step on the bench that stayed red. AI agents, led and reviewed by humans. A human approves this post before it goes out. @nilwerk nilwerk.de

Caption (DE): Drei Prüfungen, und eine davon hat unseren eigenen Prüfer korrigiert. Eine automatische Prüfung, ein Irrtum eines Prüfers und ein Fehler eines Entwicklers aus einem Tag unseres KI-Agenten-Teams, dazu ein Schritt am Prüfstand, der rot blieb. KI-Agenten, geleitet und geprüft von Menschen. Ein Mensch gibt diesen Beitrag frei, bevor er erscheint. @nilwerk nilwerk.de

English carousel

| Card | Text on card | Alt text |
|---|---|---|
| 1 | Three checks, one of them caught our own reviewer. | Title card on a light background: "Three checks, one of them caught our own reviewer." |
| 2 | Check 1, a machine: a leftover import broke the code-style check. The pipeline caught it. Fixed in one round. | Text card: check one, a machine check catching a leftover import. |
| 3 | Check 2, our reviewer was wrong: a decision was called open, but the owner's recorded decision said otherwise. Corrected. | Text card: check two, a reviewer's wrong claim corrected against the owner's recorded decision. |
| 4 | Check 3, a builder's miss: an error said "key not created", but a lost reply can mean it was. Wording and key-list reload fixed. Tested on a mocked backend only. | Text card: check three, a misleading error message fixed, with a note that only a mocked backend was used. |
| 5 | For engineers: bench run on main, 24 Nov: 5 steps green, the app-flow step red (automation server did not answer). Health check: in review, not run on the Pi. Tests: 443 on main; more in review. Source: CI and pipeline runs, 24 Nov. AI agents, led and reviewed by humans. | Text card: bench result with five green steps and one red step, and a note that further tests are in review. |

German carousel

| Karte | Text auf der Karte | Alt-Text |
|---|---|---|
| 1 | Drei Prüfungen, und eine davon hat unseren eigenen Prüfer korrigiert. | Titelkarte auf hellem Hintergrund: „Drei Prüfungen, und eine davon hat unseren eigenen Prüfer korrigiert.“ |
| 2 | Prüfung 1, eine Maschine: Ein übrig gebliebener Import ließ die Stilprüfung fehlschlagen. Die Pipeline fand ihn. In einer Runde behoben. | Textkarte: Prüfung eins, eine automatische Prüfung findet einen übrig gebliebenen Import. |
| 3 | Prüfung 2, unser Prüfer lag falsch: Eine Entscheidung galt als offen, die festgehaltene Entscheidung des Inhabers sagte etwas anderes. Korrigiert. | Textkarte: Prüfung zwei, die falsche Aussage eines Prüfers wird anhand der festgehaltenen Entscheidung des Inhabers korrigiert. |
| 4 | Prüfung 3, ein Fehler des Entwicklers: Eine Meldung lautete „Schlüssel nicht erstellt“, obwohl er bei einer verlorenen Antwort doch erstellt sein kann. Wortlaut korrigiert, Schlüsselliste wird neu geladen. Nur gegen ein simuliertes Backend getestet. | Textkarte: Prüfung drei, eine irreführende Fehlermeldung wurde korrigiert, mit dem Hinweis, dass nur ein simuliertes Backend genutzt wurde. |
| 5 | Für Ingenieure: Prüfstand-Lauf auf dem Hauptzweig, 24.11.: 5 Schritte grün, Schritt App-Ablauf rot (Automatisierungsserver antwortete nicht). Funktionsprüfung (Health-Check): in Prüfung, nicht auf dem Pi gelaufen. Tests: 443 im Hauptzweig; weitere in Prüfung. Quelle: CI- und Pipeline-Läufe, 24.11. KI-Agenten, geleitet und geprüft von Menschen. | Textkarte: Prüfstand-Ergebnis mit fünf grünen und einem roten Schritt und dem Hinweis, dass weitere Tests in Prüfung sind. |

---

## Claim sources

Types: measured = a test or CI run result; observed = seen in a run, local test or review; decision = a recorded owner decision. Nothing in this pack is simulated or estimated. "State" says whether the item is on main or only in an open change (checked 24 Nov 2026 evening against the main branch).

| Claim | Type | State | Where from |
|---|---|---|---|
| Several builder agents; each change goes through architect review, QA (suite re-run plus deliberate bugs) and pipeline check | observed | - | Review comments on the day's changes, 24 Nov |
| Catch 1: leftover import broke the lint step, caught by CI (machine), fixed in one round | observed | the fix is in the open analytics change | CI lint job failed then passed, run 45436179092, 24 Nov |
| Catch 2: the architect's claim that a decision was open was wrong, withdrawn after the owner's recorded decision was supplied | observed | - | Architect review comment, amended, 24 Nov |
| Catch 3: "key was not created" message could be wrong after a lost reply; wording fixed; screen reloads the key list after a lost reply; 6 of 6 mutants killed | observed | in review | Architect finding and QA re-check on the open Connect-your-AI change, 24 Nov |
| Connect-your-AI screen tested against a mocked backend only; key create and revoke server function does not exist yet | observed | in review | Architect and QA comments on that change, 24 Nov |
| Premium dashboard: bar graphs (soil range, first week vs last week), missing readings handled | observed | on main | Dashboard QA comment, 24 Nov |
| 30/90-day line chart not built; no daily series in the data contract; scope awaits the owner's decision | decision | on main (statement about main) | Dashboard architect and QA comments, 24 Nov |
| 443 app tests | measured | on main | CI run 45434946642, job 138590263845, on main, 24 Nov |
| 475 app tests with the Connect-your-AI screen | measured | in review | QA local run on the open change, 24 Nov (CI count not read) |
| App and endpoint not run on a phone or live backend | observed | - | QA notes, 24 Nov |
| Endpoint premium-only, premium check before any reading is touched | observed (local test with a fake database client) | on main | Merged endpoint change and QA comment, 24 Nov |
| 13 endpoint tests passing | measured | on main | QA comment on the merged endpoint change, 24 Nov |
| Watering rule: rise of 10 points or more; readings over 2 hours apart do not join (main still counts only rises above 10) | decision | in review | Owner's decision; the open change's QA comment and the main branch code, 24 Nov |
| Adapter tests 7, aggregate tests 13 | measured | in review | QA comment on the open analytics change, 24 Nov |
| Boundary tests at exactly 10 points and exactly 2 hours; 6 of 6 deliberate bugs caught | measured | in review | QA comment on the open analytics change (scratch mutants), 24 Nov |
| Boot-loop guard: 433 checks, 46 of 46 deliberate bugs caught (host tests, pure C) | measured | in review | QA comment on the open firmware change, 24 Nov |
| Boot-loop guard compiles for the ESP32-C3 in CI | measured | in review | firmware job 138602239489, run 45438308327, 24 Nov |
| Boot-loop guard not wired into firmware; never run on a board | observed | in review | QA comment, 24 Nov |
| Bench: flash, provisioning, Bluetooth advertising, serial wake line, app install passed | measured | on main (run on main) | Bench pipeline run 45434991511 (manual), 24 Nov |
| Bench: app-flow step failed because the automation server on the Pi did not answer | measured | on main (run on main) | Bench pipeline run 45434991511, 24 Nov |
| Health check naming that cause built and tested offline (5 of 5 cases), not merged, not run on the Pi | observed | in review | QA comments on the open health-check change, 24 Nov |
| No time figure quoted | none | - | No measured total for the day found in a daily report at drafting time |

## Open before posting
- Owner approval; technical check; native German check.
- Recount on the posting day: the changes marked "in review" may be merged or changed (the 10-point rule, the tests, the boot-loop guard, the Connect-your-AI screen, the health check), and the bench step may be green; update every "on main / in review" label and number.
- Build the card images from the brand templates; run the brand and contrast checks. Instagram needs a media URL that the scheduling tool can read.
