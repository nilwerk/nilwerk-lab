# Logbook: "We caught a mistake: a test that could not fail" (draft pack, v2 after Theo's fact-check, PR #76 and the fixes PR)

Status: **DRAFT, nothing scheduled, nothing published.** Arsany approves and posts himself (Instagram via the Metricool planner, LinkedIn by hand). German to be checked by Theo or Nora, then Arsany. Claims and sources: `claim-check.md`. Every changing number is "as of 10 Nov 2026, 10:45 Berlin": **recount on the day of posting** (merge state of the five changes, CI, QA re-run of the enclosure fix). Episode type: *We caught a mistake* (series.md). Not tied to a fixed calendar day: see `showcase/content/company/calendar.md` for the proposed slot.

**Images (5 slides, EN and DE, 1080x1350, code-generated from real data, no AI imagery, so no AI flag):** `images/catches-s{1..5}-{en,de}-portrait-1080x1350.png` (+ .svg). Slide 1 embeds the real plan render of the enclosure model (`images/source-enclosure-v3-plan.png`). Rebuild: `build_images.py` (texts in `catches_data.py`). No LinkedIn 1200x627 version built.

**Alt text (EN):** 1: Plan view of the enclosure model with the board outline in green, the battery cavity in orange and six screw posts. 2: Two tiles: 6.0 millimetres typed into the check and 4.5 millimetres in the real board file. 3: Two tiles: one failing check found by QA on the older version, zero failing checks in the author's run after the fix. 4: Five short rows: a switch wired to ground, 16 vias moved out of pads, a start-up pin that cannot be a button, a name that was trimmed only for checking, and 41 of 41 deliberate bugs caught. 5: Three tiles: four of five changes merged, one draft still open, five of five with architect and QA verdicts (enclosure on earlier heads).
**Alt text (DE):** in `catches_data.py`, key `alt`, language `de`.

## LinkedIn (EN)

Nilwerk Logbook: we caught a mistake. Our own test could not fail.

Our enclosure check (head a405f53) said PASS on all 35 rows. Our QA agent did not trust the green. It re-ran the check against the newest version of the circuit board, and found that four of the 35 checks (on head a405f53) printed exactly the same answer on the old and the new board. The reason: one measurement, how far the antenna sticks out past the board, had been typed into the check by hand. It said 6.0 mm. The real board file says 4.5 mm. A test that cannot change its answer proves nothing.

The same re-run also found a real clash between the printed tray and the USB-C shell of the J1 connector. Both are fixed in the code now: the check reads the board file itself, and a new test fails if its stored copy of the board ever drifts from the design. The re-run of the fixed version is QA's next step.

The same week, the same habit showed up elsewhere: a placeholder switch that would have wired a signal straight to ground, 16 tiny holes (vias) moved out of solder pads, a start-up pin that cannot be the "hold at power-up" button, a name field checked trimmed but sent untrimmed, and a delete-account function where the tests caught all 41 deliberate bugs we planted.

Where things stand, as of 10 Nov 2026, 10:45 Berlin: four of the five changes are merged. The enclosure change is still a draft. Nothing is printed, ordered or run on a board.

For engineers: on head a405f53, fit_check_v3 rows 2, 16, 17, 18 (1.00 / 26.2 / 28.4 / 21.2 mm) printed the same values on the slice-1 and slice-2 boards, because OVERHANG = 6.0 was hard-coded. The real overhang is 4.5 mm. On a405f53 that left 2.5 mm of air above the antenna; the fixed head b98bd69 reads the 1.0 mm gap from the board file by design, and its row 17 reads 27.7 mm. QA's re-run on head a405f53 with the #73 board: 34 PASS / 1 FAIL (tray vs board and parts, 0.686 mm3, J1 USB-C shell). The fix round on b98bd69: overhang, module position and cell cavity read from the board file, a drift test for the board copy (checked by a negative run), 35 PASS / 0 FAIL and 8 tests. That is the author's run plus green CI; QA has not re-run the fix round. Component heights are still assumed; nothing printed, no seal test. Firmware glue code was written without an ESP-IDF toolchain, compiled in CI after two fixes, and nothing ran on a board. The 41 mutants are the cloud suite's mutants (28 existing, 13 new); QA's full run on the delete-account head 9984d24 killed all 41. The tests use a local PostgreSQL, not real Supabase.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

#BuildInPublic #Hardware #IoT #QualityAssurance #AIAgents

## LinkedIn (DE), to be checked by Theo/Nora

Nilwerk Logbuch: Wir haben einen Fehler gefunden. Unser eigener Test konnte nicht scheitern.

Auf dem Stand a405f53 meldete unsere Gehäuseprüfung bei allen 35 Zeilen BESTANDEN. Unser QA-Agent traute dem Grün nicht. Er ließ die Prüfung gegen die neueste Version der Leiterplatte laufen und stellte fest: Vier der 35 Prüfungen lieferten auf dem Stand a405f53 auf der alten und der neuen Platine genau dasselbe Ergebnis. Der Grund: Ein Maß, nämlich wie weit die Antenne über die Platine hinausragt, war von Hand in die Prüfung getippt. Dort stand 6,0 mm. Die echte Platinendatei sagt 4,5 mm. Ein Test, der seine Antwort nie ändern kann, beweist nichts.

Derselbe Lauf fand außerdem eine echte Kollision zwischen der gedruckten Gehäuseschale und der USB-C-Buchse J1. Beides ist im Code behoben: Die Prüfung liest jetzt die Platinendatei selbst, und ein neuer Test schlägt fehl, wenn ihre gespeicherte Kopie der Platine vom Entwurf abweicht. Der QA-Nachlauf der korrigierten Fassung ist der nächste Schritt.

In derselben Woche zeigte sich dieselbe Gewohnheit an anderer Stelle: ein Platzhalter-Taster, der ein Signal direkt mit Masse verbunden hätte, 16 winzige Bohrungen (Vias) aus Lötflächen verschoben, ein Startpin, der keinen Taster „beim Einschalten halten“ tragen kann, ein Namensfeld, das getrimmt geprüft, aber ungetrimmt gesendet wurde, und eine Funktion „Konto löschen“, bei der die Tests alle 41 absichtlich eingebauten Fehler entdeckten.

Stand 10. November 2026, 10:45 Uhr Berliner Zeit: Vier der fünf Änderungen sind gemergt. Die Gehäuseänderung ist noch ein Entwurf. Nichts ist gedruckt, bestellt oder auf einer Platine gelaufen.

Für Ingenieure: Auf Stand a405f53 zeigten die Zeilen 2, 16, 17, 18 von fit_check_v3 (1,00 / 26,2 / 28,4 / 21,2 mm) auf der Platine von Slice 1 und Slice 2 dieselben Werte, weil OVERHANG = 6.0 fest eingetragen war. Der echte Überstand ist 4,5 mm. Auf a405f53 blieben so 2,5 mm Luft über der Antenne; die korrigierte Fassung (Stand b98bd69) liest den Abstand von 1,0 mm aus der Platinendatei, so gewollt, und Zeile 17 zeigt dort 27,7 mm. QA-Lauf auf a405f53 mit der Platine von #73: 34 PASS / 1 FAIL (Gehäuse gegen Platine und Bauteile, 0,686 mm³, USB-C-Schale J1). Korrekturrunde auf b98bd69: Überstand, Modulposition und Akkufach aus der Platinendatei, Drift-Test per Negativlauf belegt, 35 PASS / 0 FAIL und 8 Tests. Das ist der Lauf des Autors plus grüne CI; QA hat die Korrekturrunde noch nicht nachgeprüft. Bauteilhöhen sind weiter angenommen; nichts gedruckt, kein Dichtheitstest. Der Firmware-Code wurde ohne ESP-IDF-Toolchain geschrieben, in der CI nach zwei Korrekturen übersetzt, nichts lief auf einer Platine. Die 41 Mutanten sind die Mutanten der Cloud-Testsuite (28 bestehende, 13 neu); QA-Vollauf auf dem Stand 9984d24 (Konto löschen) hat alle 41 getötet. Die Tests nutzen eine lokale PostgreSQL, nicht echtes Supabase.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

#BuildInPublic #Hardware #IoT #Qualitätssicherung #KIAgenten

## Instagram carousel (EN), 5 slides, for the Metricool planner

Slide order: 1 cover with the real plan render, 2 the catch (6.0 vs 4.5 mm), 3 the fix, 4 five more checks the same week, 5 the human step. Slot proposal: 10:00 Europe/Berlin on a weekday (Metricool best-time data, 8 Nov: weekday peak at 10:00; the account is days old, so treat it as a benchmark).

Caption:

A test that could not fail. 🔍

Our enclosure check (head a405f53) said PASS on every row. Our QA agent asked: would it ever say anything else? It re-ran the check on the newest circuit board. One measurement (how far the antenna sticks out) had been typed in by hand: 6.0 mm, while the real board file says 4.5 mm. Four checks (head a405f53) gave the same answer on both boards. Now the check reads the board file itself, and a new test catches any drift. The re-run also found a real clash with the J1 USB-C shell. Fixed in the code; QA's re-run of the fix is next.

The same week, the same habit: a switch that would have shorted to ground, 16 vias out of solder pads, a pin that cannot be a power-up button, a trimmed-but-untrimmed name, 41 of 41 planted bugs caught.

Where things stand (10 Nov, 10:45 Berlin): four of five changes merged, the enclosure change still a draft. Nothing printed, ordered or run on a board.

For engineers: on a405f53, fit-check rows 2, 16, 17, 18 gave the same values on both boards (hard-coded OVERHANG 6.0 vs 4.5 mm). QA on head a405f53: 34 PASS / 1 FAIL (0.686 mm3). Fix on b98bd69: 35 PASS / 0 FAIL, 8 tests, the author's run with green CI; QA has not re-run it. Heights assumed, nothing printed. 41 of 41 mutants: QA's full run on head 9984d24.

AI agents, led and reviewed by humans. nilwerk.de
#BuildInPublic #Hardware #IoT #QA #AIAgents

(Emoji: one. German line for the English feed:) Ein Test, der nicht scheitern konnte: Unsere QA hat es gemerkt, bevor etwas gedruckt wurde. KI-Agenten, geleitet und geprüft von Menschen.

## Instagram (DE) alternative caption, to be checked by Theo/Nora

Ein Test, der gar nicht scheitern konnte. 🔍

Auf Stand a405f53 meldete unsere Gehäuseprüfung bei jeder Zeile BESTANDEN. Unser QA-Agent fragte: Würde sie je etwas anderes melden? Er ließ sie gegen die neueste Leiterplatte laufen. Ein Maß (wie weit die Antenne übersteht) war von Hand eingetippt: 6,0 mm, die echte Platinendatei sagt 4,5 mm. Auf a405f53 lieferten vier Prüfungen auf beiden Platinen dasselbe. Jetzt liest die Prüfung die Platinendatei selbst, und ein neuer Test fängt jede Abweichung. Außerdem fand der Lauf eine echte Kollision mit der USB-C-Schale von J1. Im Code behoben; der QA-Nachlauf kommt als Nächstes.

In derselben Woche, dieselbe Gewohnheit: ein Taster mit Masseschluss, 16 Vias aus Lötflächen, ein Pin, der kein Einschalt-Taster sein kann, ein Name getrimmt geprüft und ungetrimmt gesendet, 41 von 41 eingebauten Fehlern entdeckt.

Stand 10. Nov. 2026, 10:45 Uhr: Vier von fünf Änderungen gemergt, die Gehäuseänderung noch Entwurf. Nichts gedruckt, bestellt oder auf einer Platine gelaufen.

Für Ingenieure: auf a405f53 gaben Prüfzeilen 2, 16, 17, 18 auf beiden Platinen dieselben Werte (OVERHANG fest 6,0 statt 4,5 mm); QA auf a405f53: 34 PASS / 1 FAIL (0,686 mm³). Korrektur auf b98bd69: 35 PASS / 0 FAIL, 8 Tests, Lauf des Autors mit grüner CI; QA hat nicht nachgeprüft. Höhen angenommen, nichts gedruckt. 41 von 41 Mutanten: QA-Vollauf auf 9984d24.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de

## Checklist before posting (DAILY.md section 4)

- [ ] Recount on the day: merge state of the five changes (#71, #72, #73, #75 merged and #74 draft as of 10 Nov 10:45), CI on their newest commits, whether QA has re-run the enclosure fix on b98bd69. Edit the "as of" sentences in text and slides (`AS_OF` in `catches_data.py`) and the claim-check.
- [ ] Theo: technical rows. Theo or Nora: the German. Arsany: approval.
- [ ] Alt text added; Impressum link on the profile; no AI imagery (none used).
- [ ] Metricool: no draft was created (no public media URL, see `company/calendar.md` Metricool facts); Arsany uploads the five PNGs and pastes the caption.
