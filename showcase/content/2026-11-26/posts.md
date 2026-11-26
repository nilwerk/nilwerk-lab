# Content pack 26 Nov 2026: "Three bugs stood between a sensor and its first reading"

**Status: DRAFT. Not published, not scheduled, not in Metricool, not for posting.**
Before any of these posts goes out: the owner's approval (a Needs Arsany row, type *Post approval*, to be opened by the team lead), a technical check by the architect review, a native German check for the German text, and a recount on the posting day. Every state claim below is dated "as of 26 Nov 2026, 08:20 Berlin" and must be re-read that day.

**Image status: none.** No image exists for any of the three drafts. The one showcase item from today has a caption only. Instagram rejects a text-only post, so the Instagram draft is not created until an image exists. Do not add an image that is not a real capture; the Instagram caption will say "no picture yet" until one exists.

Contents:
1. LinkedIn, English (layer 1 story, then "For engineers")
2. LinkedIn, Deutsch (Ebene 1 Geschichte, dann "Für Ingenieure")
3. Instagram caption for @nilwerk (English with a German line), for the premium dashboard item

Public text in items 1 to 3 carries no PR numbers, no task IDs, no decision IDs, no first names and no file paths. File paths and commit IDs appear only in the "For engineers" blocks and in the claim-check table, which is for reviewers and not for posting.

---

## 1. LinkedIn, English

**Three bugs stood between a sensor and its first reading.**

Our AI agents are building the app, the cloud and the firmware for a plant monitor. On 25 November we ran the setup on our bench: a real board, an Android phone and real Wi-Fi. The first two steps passed. The third, the first reading on the plant list, did not.

So we looked for causes instead of guesses. There were three, and each had its own fix:

1. **The phone could not find the sensor.** The board announced the wrong Bluetooth service ID.
2. **The board refused to be claimed.** It had not switched into its setup state, so it said no.
3. **After Wi-Fi setup, the app started a second connection.** The board rejected it and dropped Bluetooth. The app now stops asking the sensor once setup has succeeded, and the cloud decides what happens next.

All three fixes have been on our main branch since 25 November. The reading still does not show on the screen. In the latest run it reached the cloud, but the app did not show it within 15 minutes. The calibration values are still placeholders, so the number itself means nothing yet. We would rather say that than guess. The next run will capture the screen and the server response.

Even our pipeline had a bug of its own: one workflow file did not parse, so every push to main failed within seconds. The fix is on a branch, awaiting merge.

The same team is working on a guard that stops the board from restarting in a loop. It is drafted and not yet run on hardware.

The setup changes had an architect review, and a human owner decides what gets merged. AI agents, led and reviewed by humans.

**For engineers** (as of 26 Nov 2026, 08:20 Berlin; "on main" means the commit is an ancestor of main, checked with `git merge-base --is-ancestor`)
- Bench, latest run: step 1 (sign in) and step 2 (add sensor, Wi-Fi link) passed. Step 3 (first reading on the plant list) failed after 900 s in two runs. Source: `team/reports/2026-11-25.md`, "Bench, latest run".
- Root cause 1, wrong advertised service UUID: fixed on main (commit 3669b0b). Source: the same report, root-cause section 1.
- Root cause 2, claim refused because the board never entered the session state: fixed on main (commit 3c0e6b4). Source: root-cause section 2.
- Root cause 3, second handshake after Wi-Fi apply (the status poll started a new handshake; the board rejected it and dropped BLE): fixed in the app on main (commit 257a7ee). The app sends no BLE request after a successful apply; the cloud row decides. Source: root-cause section 3; architect review of the change.
- Latest run: device claimed and linked, readings reached the cloud (in the cloud, not on screen). The reading shows 100 % because the calibration values are placeholders. Source: the report's "Bench, latest run".
- rc=30 BLE log line: expected, BLE is switched off after setup. Not a radio fault. Source: the report.
- CI: `.github/workflows/ci.yml` did not parse; every push to main failed in 0 s (team check, 26 Nov). The fix is commit ca85061 on a branch; not an ancestor of main at 08:20 Berlin.
- Boot-loop guard: a bench procedure draft (commit 7aa20d8) exists on a branch, not on main. Not run on hardware.

---

## 2. LinkedIn, Deutsch

**Drei Fehler lagen zwischen einem Sensor und seiner ersten Messung.**

Unsere KI-Agenten bauen die App, die Cloud und die Firmware für eine Pflanzenüberwachung. Am 25. November haben wir die Einrichtung an unserem Prüfstand durchgespielt: eine echte Platine, ein Android-Telefon und ein echtes WLAN. Die ersten beiden Schritte waren grün. Der dritte, die erste Messung auf der Pflanzenliste, nicht.

Also haben wir nach Ursachen gesucht statt zu raten. Es waren drei, und jede hatte ihre eigene Korrektur:

1. **Das Telefon fand den Sensor nicht.** Die Platine meldete die falsche Bluetooth-Dienst-Kennung.
2. **Die Platine hat die Zuordnung zum Konto abgelehnt.** Sie war nicht in den Einrichtungsmodus gewechselt und hat deshalb Nein gesagt.
3. **Nach der WLAN-Einrichtung hat die App eine zweite Verbindung begonnen.** Die Platine hat sie abgelehnt und Bluetooth getrennt. Die App fragt den Sensor nach einer erfolgreichen Einrichtung nicht mehr ab, und die Cloud entscheidet, wie es weitergeht.

Alle drei Korrekturen sind seit dem 25. November im Hauptzweig. Die Messung erscheint trotzdem noch nicht auf dem Bildschirm. Im letzten Lauf ist sie in der Cloud angekommen, aber die App hat sie innerhalb von 15 Minuten nicht angezeigt. Die Kalibrierwerte sind noch Platzhalter, die Zahl sagt deshalb noch nichts aus. Das sagen wir lieber offen, als zu raten. Der nächste Lauf erfasst den Bildschirm und die Antwort des Servers.

Auch unsere Pipeline hatte einen eigenen Fehler: Eine Workflow-Datei ließ sich nicht lesen, deshalb ist jeder Push in den Hauptzweig innerhalb von Sekunden fehlgeschlagen. Die Korrektur liegt auf einem Zweig und wartet auf die Übernahme.

Dasselbe Team arbeitet an einem Schutz, der verhindert, dass sich die Platine in einer Startschleife neu startet. Er ist entworfen und noch nicht auf echter Hardware gelaufen.

Die Änderungen am Einrichtungsablauf hatten ein Architektur-Review, und ein Mensch entscheidet, was übernommen wird. KI-Agenten, geleitet und geprüft von Menschen.

**Für Ingenieure** (Stand 26.11.2026, 08:20 Berlin; „im Hauptzweig“ heißt: der Commit ist Vorfahre des Hauptzweigs, geprüft mit `git merge-base --is-ancestor`)
- Prüfstand, letzter Lauf: Schritt 1 (Anmeldung) und Schritt 2 (Sensor hinzufügen, WLAN-Verbindung) bestanden. Schritt 3 (erste Messung auf der Pflanzenliste) nach 900 s gescheitert, in zwei Läufen. Quelle: `team/reports/2026-11-25.md`, Abschnitt „Bench, latest run“.
- Ursache 1, falsche beworbene Service-UUID: im Hauptzweig behoben (Commit 3669b0b).
- Ursache 2, Anspruch abgelehnt, weil die Platine nie in den Sitzungszustand wechselte: im Hauptzweig behoben (Commit 3c0e6b4).
- Ursache 3, zweiter Handshake nach der WLAN-Übergabe: in der App im Hauptzweig behoben (Commit 257a7ee). Nach erfolgreicher Übergabe sendet die App keine BLE-Anfrage mehr; die Cloud entscheidet. Quelle: derselbe Bericht, Abschnitt zur Ursache 3; Architektur-Review der Änderung.
- Letzter Lauf: Gerät beansprucht und verknüpft, Messwerte in der Cloud angekommen, auf dem Bildschirm nicht sichtbar. Der Wert steht auf 100 %, weil die Kalibrierwerte Platzhalter sind. Quelle: derselbe Bericht.
- BLE-Logzeile rc=30: erwartet, BLE ist nach der Einrichtung absichtlich aus. Kein Funkfehler.
- CI: Die Workflow-Datei `.github/workflows/ci.yml` ließ sich nicht parsen; jeder Push in den Hauptzweig schlug in 0 s fehl (Teamprüfung, 26.11.). Die Korrektur ist Commit ca85061 auf einem Zweig, zum Prüfzeitpunkt nicht im Hauptzweig.
- Schutz gegen Startschleifen: Entwurf eines Prüfstand-Verfahrens (Commit 7aa20d8) auf einem Zweig, nicht im Hauptzweig. Nicht auf Hardware gelaufen.

---

## 3. Instagram caption, @nilwerk (English, with a German line)

**Status: caption only, no picture. Do not create the Instagram draft until a real image exists.** The item behind this caption has no image, and none will be made from a mock-up.

Caption (EN):

Premium dashboard: built, in review, not yet run on a phone. Each plant gets one daily soil-moisture line, over 30 or 90 days. A day with no reading stays a gap in the line, not a zero. Free accounts still see only the upgrade message. The analytics endpoint behind it is not deployed yet, so no real data has passed through the chart. AI agents, led and reviewed by humans. @nilwerk nilwerk.de

Caption (DE): Premium-Dashboard: gebaut, in Prüfung, noch nicht auf einem Telefon getestet. Jede Pflanze bekommt eine tägliche Bodenfeuchte-Linie über 30 oder 90 Tage. Ein Tag ohne Messwert bleibt eine Lücke, keine Null. KI-Agenten, geleitet und geprüft von Menschen. @nilwerk nilwerk.de

**For engineers** (as of 26 Nov 2026, 08:20 Berlin)
- The chart is on the open change, not on main. The item caption on its branch reports 503 app tests passing (mocked backend, typecheck clean). Source: the item caption on the branch, to be checked against the CI run before posting.
- Covers the 30- and 90-day windows, a gap day, an all-empty window and the premium gate. Not run on a phone, not checked at phone width, not run against a live backend. The analytics endpoint is not deployed.
- Image: none. No render exists; a screenshot will only be used once a real render exists.

---

## Claim-check (for reviewers, not for posting)

Types: measured = run or log result; observed = seen in a file or review; decision = recorded owner decision. "State" is checked against main as of 26 Nov 2026, 08:20 Berlin; recount on the posting day.

| Claim (where used) | Type | State | Source |
|---|---|---|---|
| Steps 1 and 2 passed; step 3 failed after 900 s in two runs (EN, DE) | measured | run on commit 257a7ee, on main | `team/reports/2026-11-25.md`, "Bench, latest run" |
| Three causes, each with a fix (EN 1 to 3) | observed | fixes on main: 3669b0b, 3c0e6b4, 257a7ee (ancestry checked) | `team/reports/2026-11-25.md`, "Root cause"; `git merge-base --is-ancestor` |
| Reading reached the cloud but not the screen within 900 s | measured | run on 257a7ee | `team/reports/2026-11-25.md`, "Bench, latest run" |
| Reading shows 100 % because calibration values are placeholders | observed | open | `team/reports/2026-11-25.md`, "Bench, latest run" |
| Architect review on the setup-flow changes | observed | on main | `team/reports/2026-11-25.md`, "Team work today" |
| Human owner decides what merges | policy | - | `team/TEAM.md` section 5 (the owner merges) |
| CI workflow file did not parse; every push to main failed in 0 s | measured (team check, 26 Nov) | fix commit ca85061 not on main at 08:20 Berlin | `git merge-base --is-ancestor ca85061 origin/main` |
| Boot-loop guard drafted, not run on hardware | observed | draft commit 7aa20d8 not on main | `git log`; the draft commit message |
| Premium chart 30 and 90 days, gap handling, premium gate | observed | in review, open change | item caption on its branch, 26 Nov |
| 503 app tests passing, typecheck clean | measured | open change, not main | item caption on its branch (check against CI before posting) |
| Not run on a phone, not against a live backend | observed | - | item caption on its branch |

## Open before posting
- The owner approves or edits (Needs Arsany row, opened by the team lead).
- The architect review checks the technical statements; a native German reader checks the German text.
- Recount on the posting day: the bench may have a new run; the three fixes may or may not be on main; the CI fix may be merged; the chart change may be merged. Update every "on main" and "in review" label.
- Instagram: no draft until a real image exists; the caption is held.
