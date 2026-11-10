# Logbook: "We caught a mistake: a test that could not fail" (draft pack, built 10 Nov 2026)

Status: **DRAFT, nothing scheduled, nothing published.** Arsany approves and posts himself (Instagram via the Metricool planner, LinkedIn by hand). German to be checked by Theo or Nora, then Arsany. Technical rows to be checked by Theo. Claims and sources: `claim-check.md`. Every changing number is "as of 10 Nov 2026, 08:40 Berlin": **recount on the day of posting** (merge state of the five changes, CI, minutes). Episode type: *We caught a mistake* (series.md). Not tied to a fixed calendar day: see `showcase/content/calendar.md` for the proposed slot.

**Images (5 slides, EN and DE, 1080x1350, code-generated from real data, no AI imagery, so no AI flag):** `images/catches-s{1..5}-{en,de}-portrait-1080x1350.png` (+ .svg). Slide 1 embeds the real plan render of the enclosure model (`images/source-enclosure-v3-plan.png`, copied unchanged from the showcase item of the enclosure change). Rebuild: `build_images.py` (texts in `catches_data.py`). Not rendered: a LinkedIn 1200x627 version (Arsany can post the carousel as a document or use slide 2 as the single image; say if you want the 1200x627 template built).

**Alt text (EN):** 1: Plan view of the enclosure model with the board outline in green, the battery cavity in orange and six screw posts. 2: Two tiles: 6.0 millimetres typed into the check and 4.5 millimetres in the real board file. 3: Two tiles: one failing check found on the new board, zero failing checks after the fix. 4: Five short rows: a switch wired to ground, 16 vias moved out of pads, a start-up pin that cannot be a button, a name that was trimmed only for checking, and 41 of 41 deliberate bugs caught. 5: Three tiles: five of five changes with architect and QA verdicts, zero merged yet, about 100 agent minutes today.
**Alt text (DE):** in `catches_data.py`, key `alt`, language `de`.

## LinkedIn (EN)

Nilwerk Logbook: we caught a mistake. Our own test could not fail.

Today our enclosure check said PASS on all 35 rows. Our QA agent did not trust the green. It re-ran the check against the newest version of the circuit board, and found that four of the 35 checks printed exactly the same answer on the old and the new board. The reason: one measurement, how far the antenna sticks out past the board, had been typed into the check by hand. It said 6.0 mm. The real board file says 4.5 mm. A test that cannot change its answer proves nothing.

The same re-run also found a real clash between the printed tray and a connector. Both are fixed now: the check reads the board file itself, and a new test fails if its stored copy of the board ever drifts from the design.

The same day, the same habit showed up elsewhere: a placeholder switch that would have wired a signal straight to ground, 16 tiny holes (vias) moved out of solder pads, a start-up pin that cannot be the "hold at power-up" button, a name field checked trimmed but sent untrimmed, and a delete-account function where the tests caught all 41 deliberate bugs we planted.

None of it is merged yet. A human decides. Nothing is printed, ordered or run on a board.

For engineers: fit_check_v3 rows 2, 16, 17, 18 (26.2 / 28.4 / 21.2 mm and a 1.0 mm gap) were identical on the slice-1 and slice-2 boards because OVERHANG = 6.0 was hard-coded (real 4.5 mm, real gap above the antenna tip 2.5 mm). QA re-run on the new board: 34 PASS / 1 FAIL (tray vs board and parts, 0.686 mm3). After the fix round: overhang, module position and cell cavity read from the board file, a drift test for the board copy (checked by a negative run), 35 PASS / 0 FAIL, 8 tests (author's run, CI green). Component heights are still assumed; nothing printed, no seal test. Firmware glue code was written without an ESP-IDF toolchain, compiled in CI after two fixes, nothing ran on a board. The 41 mutants are all cloud mutants in the suite (13 new); tests use a local PostgreSQL, not real Supabase. Status as of 10 Nov 2026, 08:40 Berlin: five pull requests open, CI green on all five heads. About 100 agent minutes today is the lead's rough figure, not yet in the Agent Log.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

#BuildInPublic #Hardware #IoT #QualityAssurance #AIAgents

## LinkedIn (DE), to be checked by Theo/Nora

Nilwerk Logbuch: Wir haben einen Fehler gefunden. Unser eigener Test konnte nicht scheitern.

Heute meldete unsere Gehäuseprüfung bei allen 35 Zeilen BESTANDEN. Unser QA-Agent traute dem Grün nicht. Er ließ die Prüfung gegen die neueste Version der Leiterplatte laufen und stellte fest: Vier der 35 Prüfungen lieferten auf der alten und der neuen Platine genau dasselbe Ergebnis. Der Grund: Ein Maß, nämlich wie weit die Antenne über die Platine hinausragt, war von Hand in die Prüfung getippt. Dort stand 6,0 mm. Die echte Platinendatei sagt 4,5 mm. Ein Test, der seine Antwort nie ändern kann, beweist nichts.

Derselbe Lauf fand außerdem eine echte Kollision zwischen der gedruckten Gehäuseschale und einem Stecker. Beides ist behoben: Die Prüfung liest jetzt die Platinendatei selbst, und ein neuer Test schlägt fehl, wenn ihre gespeicherte Kopie der Platine vom Entwurf abweicht.

Am selben Tag zeigte sich dieselbe Gewohnheit an anderer Stelle: ein Platzhalter-Taster, der ein Signal direkt mit Masse verbunden hätte, 16 winzige Bohrungen (Vias) aus Lötflächen verschoben, ein Startpin, der keinen Taster „beim Einschalten halten“ tragen kann, ein Namensfeld, das getrimmt geprüft, aber ungetrimmt gesendet wurde, und eine Funktion „Konto löschen“, bei der die Tests alle 41 absichtlich eingebauten Fehler entdeckten.

Nichts davon ist gemergt. Ein Mensch entscheidet. Nichts ist gedruckt, bestellt oder auf einer Platine gelaufen.

Für Ingenieure: Die Zeilen 2, 16, 17, 18 von fit_check_v3 (26,2 / 28,4 / 21,2 mm und 1,0 mm Abstand) waren auf der Platine von Slice 1 und Slice 2 identisch, weil OVERHANG = 6.0 fest eingetragen war (real 4,5 mm, realer Abstand über der Antennenspitze 2,5 mm). QA-Nachlauf auf der neuen Platine: 34 PASS / 1 FAIL (Gehäuseschale gegen Platine und Bauteile, 0,686 mm³). Nach der Korrekturrunde: Überstand, Modulposition und Akkufach kommen aus der Platinendatei, ein Drift-Test für die Platinenkopie (per Negativlauf geprüft), 35 PASS / 0 FAIL, 8 Tests (Lauf des Autors, CI grün). Bauteilhöhen sind weiter angenommen; nichts gedruckt, kein Dichtheitstest. Der Firmware-Code wurde ohne ESP-IDF-Toolchain geschrieben, in der CI nach zwei Korrekturen übersetzt, nichts lief auf einer Platine. Die 41 Mutanten sind alle Cloud-Mutanten der Testsuite (13 neu); die Tests nutzen eine lokale PostgreSQL, nicht echtes Supabase. Stand 10. November 2026, 08:40 Uhr Berliner Zeit: fünf Pull Requests offen, CI auf allen fünf Ständen grün. Die rund 100 Agentenminuten heute sind die grobe Zahl der Leitung, noch nicht im Agent Log.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

#BuildInPublic #Hardware #IoT #Qualitätssicherung #KIAgenten

## Instagram carousel (EN), 5 slides, for the Metricool planner

Slide order: 1 cover with the real plan render, 2 the catch (6.0 vs 4.5 mm), 3 the fix, 4 five more checks the same day, 5 the human step. Slot proposal: 10:00 Europe/Berlin on a weekday (Metricool best-time data, 8 Nov: weekday peak at 10:00; the account is days old, so treat it as a benchmark).

Caption:

A test that could not fail. 🔍

Our enclosure check said PASS on every row. Our QA agent asked: would it ever say anything else? It re-ran the check on the newest circuit board. One measurement (how far the antenna sticks out) had been typed in by hand: 6.0 mm, while the real board file says 4.5 mm. Four checks gave the same answer on both boards. Now the check reads the board file itself, and a new test catches any drift. The re-run also found a real clash with a connector. Fixed too.

Same day, same habit: a switch that would have shorted to ground, 16 vias out of solder pads, a pin that cannot be a power-up button, a trimmed-but-untrimmed name, 41 of 41 planted bugs caught.

Not merged yet: a human decides. Nothing printed, ordered or run on a board.

For engineers: fit-check rows 2, 16-18 were identical on both boards (hard-coded OVERHANG 6.0 vs 4.5 mm); QA re-run 34 PASS / 1 FAIL (0.686 mm3), after the fix 35 PASS / 0 FAIL (author's run, CI green). Heights assumed, nothing printed. As of 10 Nov 2026, 08:40 Berlin.

AI agents, led and reviewed by humans. nilwerk.de
#BuildInPublic #Hardware #IoT #QA #AIAgents

(Emoji: one. German line for the English feed:) Ein Test, der nicht scheitern konnte: Unsere QA hat es gemerkt, bevor etwas gedruckt wurde. KI-Agenten, geleitet und geprüft von Menschen.

## Instagram (DE) alternative caption, to be checked by Theo/Nora

Ein Test, der gar nicht scheitern konnte. 🔍

Unsere Gehäuseprüfung meldete bei jeder Zeile BESTANDEN. Unser QA-Agent fragte: Würde sie je etwas anderes melden? Er ließ sie gegen die neueste Leiterplatte laufen. Ein Maß (wie weit die Antenne übersteht) war von Hand eingetippt: 6,0 mm, die echte Platinendatei sagt 4,5 mm. Vier Prüfungen lieferten auf beiden Platinen dasselbe. Jetzt liest die Prüfung die Platinendatei selbst, und ein neuer Test fängt jede Abweichung. Außerdem fand der Lauf eine echte Kollision mit einem Stecker. Auch behoben.

Am selben Tag, dieselbe Gewohnheit: ein Taster mit Masseschluss, 16 Vias aus Lötflächen, ein Pin, der kein Einschalt-Taster sein kann, ein Name getrimmt geprüft und ungetrimmt gesendet, 41 von 41 eingebauten Fehlern entdeckt.

Noch nicht gemergt: Ein Mensch entscheidet. Nichts gedruckt, bestellt oder auf einer Platine gelaufen.

Für Ingenieure: Prüfzeilen 2, 16-18 auf beiden Platinen identisch (OVERHANG fest 6,0 statt 4,5 mm); QA-Nachlauf 34 PASS / 1 FAIL (0,686 mm³), nach der Korrektur 35 PASS / 0 FAIL (Lauf des Autors, CI grün). Höhen angenommen, nichts gedruckt. Stand 10. Nov. 2026, 08:40 Berliner Zeit.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de

## Checklist before posting (DAILY.md section 4)

- [ ] Recount: merge state of the five changes, CI on their newest commits, whether the enclosure change was re-verified by QA after the fix round (today it is the author's run plus green CI), agent minutes from the Agent Log; edit text, images (`AS_OF` in `catches_data.py`) and claim-check.
- [ ] Theo: technical rows. Theo or Nora: the German. Arsany: approval.
- [ ] Alt text added; Impressum link on the profile; no AI imagery (none used).
- [ ] Metricool: no draft was created (no public media URL, see `company/calendar.md` Metricool facts); Arsany uploads the five PNGs and pastes the caption.
