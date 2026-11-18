# Post drafts 2026-11-18: "All my data first" and "One setup code per sensor"

**NOT FOR POSTING before PR #131 is merged AND Arsany has approved.** DRAFTS ONLY: text, no image yet (the real
evidence for both items is test output; nothing was run on a phone or a board, so there is no real screenshot or
photo to show). Nothing was posted, scheduled or drafted in Metricool; no Canva. German texts are Poppy's drafts and still need
Theo or Nora, then Arsany. Facts and sources: `claim-check.md` (ids C1... in brackets there). As of 18 Nov 2026, 08:30 Berlin:
PRs #132 and #133 are open and not merged, #130 (the server side of the export) is open and not deployed, #129 is open.

Footer EN: `nilwerk.de · AI agents, led and reviewed by humans.`  Footer DE: `nilwerk.de · KI-Agenten, geleitet und geprüft von Menschen.`
Both posts are plain engineering with no made-up characters or fiction. Tag `@nilwerk`.

---

## Post 1 · "Delete my account must first give me ALL my data, photos included"

### LinkedIn EN
Imagine you tap "delete my account" in a plant-care app. Before it lets you, it should hand you everything it holds about you: your plants, your readings, and your photos. Not links to your photos. The photos.

That is the rule our AI agents built into the prototype app this week. The delete button stays locked until the app has saved one file to your phone with your data and every photo inside it. If a single photo fails to download, nothing is saved, delete stays locked, and the message says so plainly and tells you to try again.

Our reviewing AI agent also caught a wrong sentence in our own wording: one error text said "your data arrived" when nothing had been saved. We changed it to say what really happened.

For engineers: task 4.A9b (NFR-07, FR-A01, FR-A05). The JSON export only links the photos (signed URLs, valid 7 days). The app now downloads each photo behind those links, packs `export.json` plus the photos into one ZIP, hands it over, and only then opens the delete gate. A CSV export alone never unlocks delete, because it only links the photos. If photos are listed but none could be saved, the export fails; the photo URLs must point to the app's own storage host and path; a 150 MB size cap applies. Evidence: 287 app tests pass (220 on main before; type check clean), 11 deliberate-bug mutations in the author's run all caught by failing tests, and QA's own 14 mutation rows (M1 to M16) all caught. CI green at head 604ecea. Not verified: never run on a phone or simulator; the server side (PR #130, export function) is not merged or deployed; the 150 MB cap is not measured on a device; the archive is built in memory, so a very large photo library could run out of memory (the failure is safe: delete stays locked). Status as of 18 Nov 2026, 08:30 Berlin: PR open, not merged.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

### LinkedIn DE
Stellen Sie sich vor, Sie tippen in einer Pflanzen-App auf „Konto löschen“. Bevor die App das zulässt, sollte sie Ihnen alles mitgeben, was sie über Sie gespeichert hat: Ihre Pflanzen, Ihre Messwerte und Ihre Fotos. Nicht Links zu den Fotos. Die Fotos selbst.

Genau diese Regel haben unsere KI-Agenten diese Woche in den Prototyp der App eingebaut. Der Löschen-Knopf bleibt gesperrt, bis die App eine Datei auf Ihrem Handy gespeichert hat, in der Ihre Daten und jedes Foto stecken. Schlägt auch nur ein Foto-Download fehl, wird nichts gespeichert, Löschen bleibt gesperrt, und die Meldung sagt das klar und bittet um einen neuen Versuch.

Unser prüfender KI-Agent hat außerdem einen falschen Satz in unserem eigenen Text gefunden: Eine Fehlermeldung sagte „Ihre Daten sind angekommen“, obwohl nichts gespeichert war. Jetzt steht dort, was wirklich passiert ist.

Für Ingenieure: Aufgabe 4.A9b (NFR-07, FR-A01, FR-A05). Der JSON-Export enthält die Fotos nur als Links (signierte URLs, 7 Tage gültig). Die App lädt jetzt jedes Foto hinter diesen Links herunter, packt `export.json` und die Fotos in ein ZIP, übergibt die Datei und öffnet erst dann die Löschsperre. Ein CSV-Export allein entsperrt Löschen nie, weil er die Fotos nur verlinkt. Sind Fotos aufgelistet, aber keines konnte gespeichert werden, schlägt der Export fehl; die Foto-URLs müssen auf den eigenen Speicher-Host und -Pfad der App zeigen; es gilt eine Größengrenze von 150 MB. Belege: 287 App-Tests bestanden (zuvor 220 auf main; Typprüfung sauber), 11 absichtlich eingebaute Fehler (Mutationen) im Lauf des entwickelnden KI-Agenten, alle von fehlschlagenden Tests erkannt, und die 14 Mutationszeilen (M1 bis M16) der QA ebenfalls alle erkannt. CI grün bei Stand 604ecea. Nicht überprüft: nie auf einem Handy oder Simulator gelaufen; die Server-Seite (PR #130, Export-Funktion) ist weder gemergt noch ausgerollt; die 150-MB-Grenze ist auf keinem Gerät gemessen; das Archiv entsteht im Arbeitsspeicher, eine sehr große Fotosammlung könnte ihn sprengen (der Fehlerfall ist sicher: Löschen bleibt gesperrt). Stand 18.11.2026, 08:30 Uhr (Berlin): Pull Request offen, nicht gemergt.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

---

## Post 2 · "One setup code per sensor, never in the repo"

### LinkedIn EN
Every plant sensor we build gets its own setup code, printed on its own label. Not one shared code for all of them. One per sensor.

The tricky part of a code like that is where it lives. Ours never goes into the project's code folder. Our new tool writes each sensor's secrets into a private folder outside the repository, with permissions only the owner can read, and it refuses to write inside a repository at all. It will not overwrite a sensor it has already prepared. The sensor itself never stores the code from the label, only a check value derived from it. And if the setup data on a sensor is missing, the wrong size or all zeros, the sensor does not even start Bluetooth setup.

For engineers: task 4.F2b (NFR-06, FR-D03, FR-D07). `nw_sec2_gen.py` makes a random 16-byte salt and an SRP verifier (3072-bit group, SHA-512) from an 8-character code (Crockford base32, 40 bits) per unit, plus the label text. The architect agent checked that no per-unit file is committed and that nothing per-unit appears in the tree; QA ran the tool by hand and confirmed files are mode 0600 and a second run for the same unit is refused. The verifier matches an independent library (pysrp 1.0.22). Evidence: 22 of 22 host tests pass (66 s), 29 mutants of the tool and validator caught in the author's run, and QA's own mutations: 16 of 17 caught (10 of 11 on the tool, 6 of 6 on the validator); the one survivor is an equivalent mutant, because a separate "file already exists" check still refuses. CI green at head 8a72ff8. Not verified: no board and no real Bluetooth handshake, no flashing step, and the bench procedure for the hardware tester has not been run. Known open risk: the check value is stored unencrypted on the sensor, so someone with a dump of its flash memory could try to guess a 40-bit code offline; accepted for the prototype and still open, as is where the list of codes is kept long term. Status as of 18 Nov 2026, 08:30 Berlin: PR open, not merged; it must merge after PR #129.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

### LinkedIn DE
Jeder Pflanzensensor, den wir bauen, bekommt seinen eigenen Einrichtungscode, gedruckt auf sein eigenes Etikett. Nicht ein gemeinsamer Code für alle. Einer pro Sensor.

Heikel ist bei so einem Code, wo er gespeichert wird. Bei uns landet er nie im Code-Ordner des Projekts. Unser neues Werkzeug schreibt die Geheimnisse jedes Sensors in einen privaten Ordner außerhalb des Repositorys, mit Rechten, die nur der Besitzer lesen kann, und es weigert sich, überhaupt in ein Repository zu schreiben. Einen bereits vorbereiteten Sensor überschreibt es nicht. Der Sensor selbst speichert nie den Code vom Etikett, nur einen daraus berechneten Prüfwert. Und fehlen die Einrichtungsdaten auf einem Sensor, haben sie die falsche Größe oder bestehen nur aus Nullen, startet der Sensor die Bluetooth-Einrichtung gar nicht erst.

Für Ingenieure: Aufgabe 4.F2b (NFR-06, FR-D03, FR-D07). `nw_sec2_gen.py` erzeugt pro Gerät ein zufälliges 16-Byte-Salz und einen SRP-Verifier (3072-Bit-Gruppe, SHA-512) aus einem 8-stelligen Code (Crockford-Base32, 40 Bit) sowie den Etikett-Text. Der Architektur-Agent hat geprüft, dass keine gerätespezifische Datei eingecheckt ist; die QA hat das Werkzeug von Hand ausgeführt und bestätigt: Dateien mit Modus 0600, ein zweiter Lauf für dasselbe Gerät wird abgelehnt. Der Verifier stimmt mit einer unabhängigen Bibliothek (pysrp 1.0.22) überein. Belege: 22 von 22 Host-Tests bestanden (66 s), 29 Mutanten von Werkzeug und Prüfer im Lauf des Autors erkannt, und eigene Mutationen der QA: 16 von 17 erkannt (10 von 11 am Werkzeug, 6 von 6 am Prüfer); der eine Überlebende ist ein gleichwertiger Mutant, weil eine separate Prüfung „Datei existiert bereits“ weiterhin ablehnt. CI grün bei Stand 8a72ff8. Nicht überprüft: kein Board und kein echter Bluetooth-Handshake, kein Flash-Schritt, und die Prüfanleitung für die Hardware-Testperson wurde nicht ausgeführt. Bekanntes offenes Risiko: Der Prüfwert liegt unverschlüsselt auf dem Sensor, wer ein Abbild des Flash-Speichers hat, könnte einen 40-Bit-Code offline erraten; für den Prototyp akzeptiert und weiter offen, ebenso wie die Frage, wo die Liste der Codes langfristig liegt. Stand 18.11.2026, 08:30 Uhr (Berlin): Pull Request offen, nicht gemergt; er muss nach PR #129 gemergt werden.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

---

## Before posting (checklist, Arsany or the Lead)

1. PR #131 merged, and Arsany approved or edited these two texts. (Needs-Arsany row type *Post approval* is the Lead's to create; no Metricool draft exists.)
2. Recount the status lines ("open, not merged", CI heads 604ecea and 8a72ff8) on the day. If #129/#130/#132/#133 have merged, update the "Not verified" and "Status" sentences; if #130 is merged but not deployed keep "not deployed".
3. German: native check by Theo or Nora (open doubts: "Mutanten", "Prüfwert" for verifier, "Hardware-Testperson").
4. Post 1: the owner has not yet accepted the open rule "photos with no file do not block delete" (listed in the PR); it is not used in the text on purpose. Do not add it as settled.
5. Post 2: decide whether the "known open risk" sentence is wanted in a public post (it is honest and sourced; the sentence about where the code list is kept is an open owner question, so only the existence of the question is named, no detail).
6. No image: if one is wanted, only a real one (test output screenshot) or a labelled illustration. Alt text then needed.
7. Impressum link, advertising labelling and alt-text checks as in `team/learnings/pr-social.md`.
