# Post draft 2026-11-19: "The fix that went to the wrong place"

INTERNAL BANNER (not part of any copy-paste text): **NOT FOR POSTING before the pull request that carries the rescued fix is merged AND Arsany has approved.** DRAFT ONLY: text, no image (the evidence is test output; nothing was run on a phone, a board or a live backend). Nothing was posted, scheduled or drafted in Metricool; no Canva. The German text is Poppy's draft and needs Theo or Nora, then Arsany. Facts and sources: `claim-check.md`. Status as of 19 Nov 2026, 08:10 Berlin: the rescue PR is open, not merged; recount on posting day.

Everything below the lines "COPY STARTS" is the text to paste. It carries no source markers and no banner.
Footer EN: `nilwerk.de · AI agents, led and reviewed by humans.`  Footer DE: `nilwerk.de · KI-Agenten, geleitet und geprüft von Menschen.`  Tag `@nilwerk`.

---

## LinkedIn EN — COPY STARTS
Ooh, here is a true story about a fix that went to the wrong place.

Our prototype's cloud has a function that exports all of a user's data, including links to their photos. One of our AI agents added a safety check to it: a photo path that tries to wander outside the user's own folder never gets a link. The check was reviewed, tested and merged. Done, right?

Not quite. It was merged into a side branch that had already landed in the main one, so the main code never got it. The fix was approved, green and, for the product, simply absent.

It turned out to be missing, and an AI agent carried it over. Our reviewing AI agent then compared the two versions line by line and found the code lines identical. Our QA agent ran the full cloud tests and tried to break the check with seven deliberately planted bugs. Five were caught. Two were not, and both were written down instead of hidden: one is a redundant check (harmless), the other is a real gap in the tests, recorded as a note with a suggested test.

The lesson we like: "merged" and "on main" are two different facts, and somebody has to check the second one.

For engineers: the guard `isSafePhotoPath` accepts only `<uid>/<folder>/<file>`, each segment from `[A-Za-z0-9._-]`; traversal (`..`), a leading slash, a backslash, `%` and other users' prefixes give `url: null` and are never signed. The commit had gone into the export function's branch after that branch reached main; it was cherry-picked onto current main without conflicts. Evidence (local run, Postgres 16.15, Node 22.23.5): export tests 19/19 (including the two guard tests), care-tips tests 68/68 (31 in the first test file alone), the whole cloud run ends green. The reviewer compared the 9-file change with the original commit: the code lines were identical (the README and API description later gained one sentence each about the upload path). QA's 7 hand-made mutants of the guard: 5 killed, 2 survived (the leading-slash check is redundant; no test has a 3-segment path with `%` or a space). Not run: Deno lint and type check (Deno is not installed in the session; CI runs them), the mutation script, anything deployed. Status as of 19 Nov 2026, 08:10 Berlin: pull request open, not merged.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

## LinkedIn DE — COPY STARTS
Ooh, eine wahre Geschichte über eine Korrektur, die am falschen Ort landete.

Die Cloud unseres Prototyps hat eine Funktion, die alle Daten einer Nutzerin oder eines Nutzers exportiert, auch die Links zu den Fotos. Einer unserer KI-Agenten baute einen Schutz ein: Ein Foto-Pfad, der aus dem eigenen Ordner der Person ausbrechen will, bekommt nie einen Link. Der Schutz wurde geprüft, getestet und gemergt (in den Code übernommen). Fertig?

Nicht ganz. Er landete in einem Nebenzweig, der schon in den Hauptzweig gemergt worden war. Der Hauptzweig bekam ihn also nie. Die Korrektur war freigegeben, grün und für das Produkt schlicht nicht vorhanden.

Es stellte sich heraus, dass sie fehlte, und ein KI-Agent trug sie hinüber. Unser prüfender KI-Agent verglich danach beide Fassungen Zeile für Zeile und fand die Code-Zeilen identisch. Unser QA-Agent ließ die kompletten Cloud-Tests laufen und versuchte, den Schutz mit sieben absichtlich eingebauten Fehlern zu knacken. Fünf wurden entdeckt, zwei nicht. Beides wurde ehrlich notiert statt versteckt: Eine Code-Prüfung ist doppelt gemoppelt (harmlos), die andere ist eine echte Testlücke, als Hinweis mit Testvorschlag festgehalten.

Unsere Lehre: „Gemergt“ und „im Hauptzweig“ sind zwei verschiedene Tatsachen, und jemand muss die zweite prüfen.

Für Ingenieure: Die Schutzprüfung `isSafePhotoPath` akzeptiert nur `<uid>/<Ordner>/<Datei>`, jedes Segment aus `[A-Za-z0-9._-]`; Pfadtricks (`..`), führender Schrägstrich, Backslash, `%` und fremde Präfixe ergeben `url: null` und werden nie signiert. Der Commit war in den Zweig der Export-Funktion gelangt, nachdem dieser schon im Hauptzweig war; er wurde ohne Konflikte auf den aktuellen Hauptzweig übertragen (cherry-pick). Belege (lokaler Lauf, Postgres 16.15, Node 22.23.5): Export-Tests 19/19 (mit den zwei Schutz-Tests), Pflegetipp-Tests 68/68 (31 allein in der ersten Testdatei), der gesamte Cloud-Lauf endet grün. Der Reviewer verglich die Änderung mit 9 Dateien mit dem Original-Commit: Die Code-Zeilen waren identisch (README und API-Beschreibung bekamen später je einen Satz zum Upload-Pfad dazu). Die 7 Handmutanten der QA: 5 erkannt, 2 überlebt (die Schrägstrich-Prüfung ist redundant; kein Test hat einen Pfad mit 3 Segmenten und `%` oder Leerzeichen). Nicht gelaufen: Deno-Lint und Typprüfung (Deno fehlt in der Sitzung; die CI führt sie aus), das Mutationsskript, alles Deployte. Stand 19.11.2026, 08:10 Uhr (Berlin): Pull Request offen, nicht gemergt.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

---

## Instagram EN — COPY STARTS
A safety fix, reviewed, tested, merged... into the wrong branch. So it never reached the main code. 🕵️ It turned out to be missing, and it was carried over. Our QA agent then tried to break it with 7 planted bugs: 5 caught, 2 survived, both written down honestly. "Merged" is not "on main". Tests run locally; Deno lint not run; nothing deployed. AI agents, led and reviewed by humans. nilwerk.de @nilwerk #buildinpublic #testing

## Instagram DE — COPY STARTS
Eine Sicherheitskorrektur, geprüft, getestet, gemergt ... in den falschen Zweig. Im Hauptcode kam sie nie an. 🕵️ Es stellte sich heraus, dass sie fehlte, und sie wurde hinübergetragen. Unser QA-Agent versuchte danach, sie mit 7 eingebauten Fehlern zu knacken: 5 erkannt, 2 überlebt, beides ehrlich notiert. „Gemergt“ heißt nicht „im Hauptcode“. Tests lokal gelaufen; Deno-Lint nicht; nichts deployt. KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de @nilwerk

## Alt text (if an image is added)
No image yet. If a terminal render is added: "Terminal output of the cloud test run: export tests 19 of 19 passed, care-tips tests 68 of 68 passed, final line ALL CLOUD TESTS PASSED."

Other real stories of the day are not drafted; see `plan-notes.md`.
