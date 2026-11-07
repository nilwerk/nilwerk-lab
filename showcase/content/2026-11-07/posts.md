# Content pack 2026-11-07: two post drafts (two-layer pattern)

Drafts only. Nothing is published or scheduled. Author: Poppy (PR & Social). Images are code-generated from the brand templates (`images/`, rebuild with `build_images.py`), so they are **not** AI imagery and need no AI flag. Claim sources: `claim-check.md`. Plain-word explanations of terms: `../../brand/glossary.md`. Brand look is a **proposal** until Arsany approves `showcase/brand/brand-kit.md`.

**Two layers in every text:** first the plain story (audience A: non-technical), then a paragraph marked "For engineers:" / "Für Ingenieure:" (audience B: numbers, how it was checked, what is unmeasured). One wording for the human side everywhere: "AI agents, led and reviewed by humans" (DE: "KI-Agenten, geleitet und geprüft von Menschen").

Status: English by Poppy; German is a plain-German draft and **must be checked by Theo or Nora, then Arsany** (Theo's wording from fix round 1 kept). Suggested slots: Post 1 Mon 9 Nov (A leads), Post 2 Tue 10 Nov (B leads, see `../calendar.md`). Tag @nilwerk, link nilwerk.de.

---

## Post 1: "A review caught a charger resistor before any order"

Image: `images/post1-r9-review-catch-portrait-1080x1350.png` (Instagram), `...-linkedin-1200x627.png` (LinkedIn), `...-square-1080x1080.png` (alternative). Light theme.
Alt text: "Before and after: charger resistor R9 of 1.2 kOhm gives about 0.9 A into a 1000 mAh cell; after review R9 of 2.4 kOhm gives 458 mA. Status: calculated, not yet bench-tested."

### LinkedIn (EN)

A tiny part decides how fast our plant sensor's battery charges. In our first parts-list draft, that part, the charger resistor R9, was 1.2 kOhm: about 0.9 A into a 1000 mAh cell, roughly 0.9C and well above the gentle 0.5C we want for this little plant sensor.

During review our reviewing AI agent flagged it, and our PCB agent redid the sum. R9 is now 2.4 kOhm, a much gentler charge. Nothing had been ordered, so the fix cost one line in a spreadsheet, not a board respin. That is the point of reviewing before buying.

Honest status: this is calculated from the datasheet, not yet measured. It still has to be checked on a real board.

For engineers: R9 programs the charge current of the charger IC (TP4056); we used the datasheet formula R = 1100 / I. 2.4 kOhm gives about 458 mA (0.46C of 1000 mAh) and 527 mA in the worst case with the chip's +15 % current tolerance (0.53C). Source: BOM draft revision 2. Open: thermal and cell-temperature behaviour, and the exact figure against the datasheet edition, are still to be checked.

How we work: AI agents, led and reviewed by humans.

nilwerk.de · @nilwerk

#Hardware #Electronics #PCB #AIAgents #Engineering #Prototyping #IoT #BuildInPublic

### LinkedIn (DE), to be checked by Theo/Nora

Ein winziges Bauteil entscheidet, wie schnell der Akku unseres Pflanzensensors geladen wird. In unserem ersten Stücklistenentwurf stand für dieses Bauteil, den Ladewiderstand R9, ein Wert von 1,2 kΩ. Das bedeutet etwa 0,9 A in eine Zelle mit 1000 mAh, rund 0,9C und damit deutlich mehr als die schonenden 0,5C, die wir für diesen kleinen Pflanzensensor wollen.

In der Prüfung hat unser Review-Agent den Wert markiert, und unser Platinen-Agent hat neu gerechnet. R9 ist jetzt 2,4 kΩ, ein deutlich sanfteres Laden. Bestellt war noch nichts. Ein falscher Widerstand kostet eine Zeile in der Tabelle, keine neue Platinenrunde. Genau dafür prüfen wir vor dem Einkauf.

Ehrlicher Stand: Das ist aus dem Datenblatt berechnet, noch nicht gemessen. Es muss noch an einer echten Platine geprüft werden.

Für Ingenieure: R9 legt den Ladestrom des Ladechips (TP4056) fest; wir haben die Datenblatt-Formel R = 1100 / I verwendet. 2,4 kΩ ergibt etwa 458 mA (0,46C bei 1000 mAh) und im ungünstigsten Fall (+15 % Toleranz des Chips) sogar 527 mA (0,53C). Quelle: Stücklistenentwurf, Revision 2. Offen: das thermische Verhalten, das Verhalten bei Zelltemperatur und die genauen Werte gegen die Datenblatt-Ausgabe.

So arbeiten wir: KI-Agenten, geleitet und geprüft von Menschen.

nilwerk.de · @nilwerk

#Hardware #Elektronik #Leiterplatte #KIAgenten #Engineering #Prototyping #IoT

### Instagram (EN) caption

Ooh, a good catch! A tiny part, the charger resistor R9, decides how hard the charger pushes into the battery. First draft: 1.2 kOhm, about 0.9 A into a 1000 mAh cell. After review by our reviewing AI agent: 2.4 kOhm, a much gentler charge. Nothing was ordered, so the fix cost one spreadsheet line.

Calculated from the datasheet, not yet measured: it still has to be checked on a real board.

For engineers: R = 1100 / I (charger datasheet) gives 458 mA (0.46C), 527 mA worst case with +15 % tolerance. BOM draft rev. 2.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk
Deutsch: Ein Review hat einen zu großen Ladestrom entdeckt, bevor etwas bestellt wurde. Berechnet, noch nicht gemessen.

Hashtags: #nilwerk #electronics #pcbdesign #hardwarestartup #aiagents #buildinpublic #iot #prototyping #engineering #plantmonitor

AI flag: not needed (code-generated image). Alt text: as above.

---

## Post 2: "User A cannot read user B's plant data"

Image: `images/post2-rls-proof-portrait-1080x1350.png` (Instagram), `...-linkedin-1200x627.png`, `...-square-1080x1080.png`. Dark theme.
Alt text: "Two tiles: row-level security on 14 of 14 tables of our own database schema, and zero foreign rows seen when user A tries to read, change, delete or forge rows of user B. Status: tested on a local PostgreSQL 16, not yet live."

### LinkedIn (EN)

Your plants, your data. How do you know the app really keeps it that way?

Our backend agent just wrote the first version of the cloud database, and the test that came with it does something simple: it creates user A and user B, then makes A try everything it should not be able to do. Read B's data. Change it. Delete it. Insert rows pretending to be B.

The result: A sees nothing of B's, changes and deletes touch 0 of B's rows, and forged inserts are rejected. The same test suite also checks how long data is kept: raw readings 3 months, hourly summaries 12.

Honest status: tested on a local database, not yet on a real Supabase project. Login identity (auth), the scheduler and file storage are stubbed or skipped locally. That comes next.

For engineers: row-level security (RLS) is enabled on all 14 tables of our schema; the test ran on a local PostgreSQL 16. A sees 0 foreign rows on every table; the forged-insert check passes on all 14. The retention test covers roll-up and cleanup, and the schema contract test passes on the migrated database. Not covered yet: real Supabase auth, pg_cron schedules, storage buckets.

A test that fails when the rule is broken beats a promise in a slide deck. AI agents, led and reviewed by humans.

nilwerk.de · @nilwerk

#Security #Backend #PostgreSQL #Supabase #DataPrivacy #AIAgents #IoT #BuildInPublic

### LinkedIn (DE), to be checked by Theo/Nora

Ihre Pflanzen, Ihre Daten. Woher wissen Sie, dass die App das wirklich einhält?

Unser Backend-Agent hat gerade die erste Version der Cloud-Datenbank geschrieben. Der zugehörige Test macht etwas Einfaches: Er legt Nutzer A und Nutzer B an und lässt A alles versuchen, was nicht gehen darf. Daten von B lesen. Verändern. Löschen. Zeilen im Namen von B einfügen.

Das Ergebnis: A sieht nichts von B, Änderungen und Löschversuche an Daten von B bleiben wirkungslos, eingeschmuggelte Zeilen werden abgelehnt. Dieselbe Testreihe prüft auch, wie lange Daten aufbewahrt werden: Rohdaten 3 Monate, stündliche Zusammenfassungen 12 Monate.

Ehrlicher Stand: getestet auf einer lokalen Datenbank, noch nicht auf einem echten Supabase-Projekt. Anmeldung, Zeitplaner und Dateispeicher sind lokal nur nachgebildet oder übersprungen. Das ist der nächste Schritt.

Für Ingenieure: Row-Level-Security (RLS) ist auf allen 14 Tabellen unseres Schemas aktiv; der Test lief auf einer lokalen PostgreSQL-16-Datenbank. A sieht auf jeder Tabelle 0 fremde Zeilen; die Prüfung eingeschmuggelter Zeilen besteht auf allen 14. Der Aufbewahrungstest deckt Zusammenfassung und Bereinigung ab, und der Schema-Vertragstest besteht auf der migrierten Datenbank. Noch nicht abgedeckt: echte Supabase-Anmeldung, pg_cron-Zeitpläne, Speicher-Buckets.

Ein Test, der fehlschlägt, wenn die Regel verletzt wird, ist mehr wert als ein Versprechen auf einer Folie. KI-Agenten, geleitet und geprüft von Menschen.

nilwerk.de · @nilwerk

#Datenschutz #Backend #PostgreSQL #Supabase #Sicherheit #KIAgenten #IoT

### Instagram (EN) caption

Can user A peek at user B's plants? We made them try. A tried to read, change, delete or forge B's data: none of the attempts succeeded. Plus: raw readings kept 3 months, hourly summaries 12.

Tested on a local database (login, scheduler and file storage stubbed), not yet on a live Supabase project.

For engineers: RLS enabled on all 14 tables of our schema, local PostgreSQL 16, 0 foreign rows seen.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk
Deutsch: Nutzer A kann die Daten von Nutzer B weder lesen noch ändern. Getestet auf lokaler Datenbank, noch nicht live.

Hashtags: #nilwerk #backend #postgresql #supabase #dataprivacy #aiagents #buildinpublic #iot #softwareengineering #plantmonitor

AI flag: not needed (code-generated image).
