# Post draft 2026-11-19: "The fix that went to the wrong place"

**NOT FOR POSTING before the pull request that carries the rescued fix is merged AND Arsany has approved.** DRAFT ONLY: text, no image (the evidence is test output; nothing was run on a phone, a board or a live backend, so there is no real screenshot or photo). Nothing was posted, scheduled or drafted in Metricool; no Canva. The German text is Poppy's draft and needs Theo or Nora, then Arsany. Facts and sources: `claim-check.md` (ids C1... in brackets). Status as of 19 Nov 2026, 08:10 Berlin: the rescue PR is open, not merged; recount on posting day.

Footer EN: `nilwerk.de · AI agents, led and reviewed by humans.`  Footer DE: `nilwerk.de · KI-Agenten, geleitet und geprüft von Menschen.`  Tag `@nilwerk`. Plain engineering, no fiction.

---

## LinkedIn EN
Ooh, here is a true story about a fix that went to the wrong place.

Our prototype's cloud has a function that exports all of a user's data, including photo links. One of our AI agents added a safety check to it: a photo path that tries to wander outside the user's own folder never gets a link. The check was reviewed, tested and merged. Done, right?

Not quite. It was merged into a side branch that had already landed in the main one. So the main code never got it. The fix was approved, green and, for the product, simply absent. [C1, C2]

It was found missing and an AI agent carried it over, copy for copy: our reviewing AI agent compared the two diffs and found the added and removed lines identical. Then our QA agent ran the full cloud test suite and tried to break the check with seven deliberate bugs. Five were caught. Two were not, and both were written up honestly instead of hidden: one is a redundant check (harmless), one is a real gap in the tests, now on the to-do list. [C3, C4, C5]

The lesson we like: "merged" and "on main" are two different facts, and somebody has to check the second one.

For engineers: the guard `isSafePhotoPath` accepts only `<uid>/<folder>/<file>`, each segment from `[A-Za-z0-9._-]`; traversal, leading slash, backslash, `%` and other users' prefixes give `url: null` and are never signed. The commit had gone into the export function's branch after that branch reached main; it was cherry-picked onto current main without conflicts. Evidence (local run, Postgres 16.15, Node 22.23.5): export tests 19/19 (including the two guard tests), care-tips tests 68/68 (31 in the first test file alone), the whole cloud run ends green. The reviewer confirmed a 9-file diff, the 7 code files identical to the original commit. QA's 7 hand-made mutants of the guard: 5 killed, 2 survived (the leading-slash check is redundant; no test has a 3-segment path with `%` or a space). Not run: Deno lint and type check (Deno is not installed in the session; CI runs them), the mutation script, anything deployed. The design was not re-reviewed. Status as of 19 Nov 2026, 08:10 Berlin: pull request open, not merged. [C6-C10]

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

## LinkedIn DE
Ooh, eine wahre Geschichte über eine Korrektur, die am falschen Ort landete.

Die Cloud unseres Prototyps hat eine Funktion, die alle Daten einer Nutzerin oder eines Nutzers exportiert, auch die Links zu den Fotos. Eines unserer KI-Agenten-Teammitglieder baute eine Schutzprüfung ein: Ein Foto-Pfad, der aus dem eigenen Ordner der Person ausbrechen will, bekommt nie einen Link. Die Prüfung wurde begutachtet, getestet und übernommen. Fertig?

Nicht ganz. Sie landete in einem Nebenzweig, der schon in den Hauptzweig übernommen worden war. Der Hauptzweig bekam sie also nie. Die Korrektur war freigegeben, grün und für das Produkt schlicht nicht vorhanden. [C1, C2]

Sie fiel als fehlend auf, und ein KI-Agent trug sie Zeile für Zeile hinüber: Unser prüfender KI-Agent verglich beide Änderungen und fand hinzugefügte und entfernte Zeilen identisch. Danach ließ unser QA-Agent die komplette Cloud-Testsuite laufen und versuchte, die Prüfung mit sieben absichtlichen Fehlern zu knacken. Fünf wurden entdeckt, zwei nicht. Beides wurde ehrlich notiert statt versteckt: Eine Prüfung ist überflüssig (harmlos), eine ist eine echte Testlücke und steht jetzt auf der Aufgabenliste. [C3, C4, C5]

Unsere Lehre: „Übernommen“ und „im Hauptzweig“ sind zwei verschiedene Tatsachen, und jemand muss die zweite prüfen.

Für Ingenieure: Die Prüfung `isSafePhotoPath` akzeptiert nur `<uid>/<Ordner>/<Datei>`, jedes Segment aus `[A-Za-z0-9._-]`; Pfadtricks (`..`), führender Schrägstrich, Backslash, `%` und fremde Präfixe ergeben `url: null` und werden nie signiert. Der Commit war in den Zweig der Export-Funktion gelangt, nachdem dieser schon im Hauptzweig war; er wurde ohne Konflikte auf den aktuellen Hauptzweig übertragen. Belege (lokaler Lauf, Postgres 16.15, Node 22.23.5): Export-Tests 19/19 (mit den zwei Prüfungs-Tests), Pflegetipp-Tests 68/68 (31 allein in der ersten Testdatei), der gesamte Cloud-Lauf endet grün. Der Reviewer bestätigte 9 Dateien, die 7 Code-Dateien identisch zum Original-Commit. Die 7 Handmutanten der QA: 5 erkannt, 2 überlebt (die Schrägstrich-Prüfung ist redundant; kein Test hat einen Pfad mit 3 Segmenten und `%` oder Leerzeichen). Nicht gelaufen: Deno-Lint und Typprüfung (Deno fehlt in der Sitzung; die CI führt sie aus), das Mutationsskript, alles Deployte. Das Design wurde nicht erneut begutachtet. Stand 19.11.2026, 08:10 Uhr (Berlin): Pull Request offen, nicht übernommen. [C6-C10]

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

---

## Instagram EN (text only, no image yet; if Arsany wants a visual: a real terminal render of `test-output.txt` from the item)
A safety fix, reviewed, tested, merged... into the wrong branch. So it never reached the main code. 🕵️ Our AI agents spotted it was missing, carried it over, and our QA agent tried to break it with 7 planted bugs: 5 caught, 2 survived, both written up honestly. "Merged" is not "on main". Tests run locally; Deno lint not run; nothing deployed. AI agents, led and reviewed by humans. nilwerk.de @nilwerk #buildinpublic #hardware #testing

## Instagram DE
Eine Sicherheitskorrektur, geprüft, getestet, übernommen ... in den falschen Zweig. Im Hauptcode kam sie nie an. 🕵️ Unsere KI-Agenten bemerkten das Fehlen und trugen sie hinüber; der QA-Agent versuchte sie mit 7 eingebauten Fehlern zu knacken: 5 erkannt, 2 überlebt, beides ehrlich notiert. „Übernommen“ heißt nicht „im Hauptcode“. Tests lokal gelaufen; Deno-Lint nicht; nichts deployt. KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de @nilwerk

## Alt text
No image. If a terminal render is added: "Terminal output of the cloud test run: export tests 19 of 19 passed, care-tips tests 68 of 68 passed, final line ALL CLOUD TESTS PASSED."

## Other real stories of the day (not drafted; ideas in `plan-notes.md`)
