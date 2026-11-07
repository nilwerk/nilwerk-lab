# Content pack 2026-11-07: two post drafts

Drafts only. Nothing is published or scheduled. Author: Poppy (PR & Social). Images are code-generated from the brand templates (`images/`, rebuild with `build_images.py`), so they are **not** AI imagery and need no AI flag. Claim sources: `claim-check.md`. Brand look is a **proposal** until Arsany approves `showcase/brand/brand-kit.md`.

Status of each text: English by Poppy; German is a plain-German draft and **must be checked by Theo or Nora, then Arsany** before use. Suggested slots: Post 1 Mon 9 Nov, Post 2 Tue 10 Nov (see `../calendar.md`). Tag @nilwerk, link nilwerk.de.

---

## Post 1: "A review caught a charger resistor before any order"

Image: `images/post1-r9-review-catch-portrait-1080x1350.png` (Instagram), `...-linkedin-1200x627.png` (LinkedIn), `...-square-1080x1080.png` (alternative). Light theme.
Alt text: "Before and after: charger resistor R9 of 1.2 kOhm gives about 0.9 A into a 1000 mAh cell; after review R9 of 2.4 kOhm gives 458 mA. Status: calculated, not yet bench-tested."

### LinkedIn (EN)

We nearly ordered a battery charger set up to push about 0.9 A into a 1000 mAh cell. That is roughly 0.9C, well above the gentle 0.5C we want for this little plant sensor.

The culprit was one resistor, R9, which sets the charge current. In the first parts list it was 1.2 kOhm. During review the mistake was flagged, and our PCB agent redid the sum with the charger datasheet's formula (R = 1100 / I): R9 is now 2.4 kOhm, which gives about 458 mA (0.46C), and still only 527 mA if the chip's +15 % tolerance goes against us.

Nothing had been ordered. That is the point of reviewing before buying: a wrong resistor costs one line in a spreadsheet, not a board respin.

Honest status: this is calculated from the datasheet, not yet measured. Our hardware integrator will test it on the real board once it exists.

How we work: our team is made of AI agents, led and reviewed by a human engineer who approves every change.

nilwerk.de · @nilwerk

#Hardware #Electronics #PCB #AIAgents #Engineering #Prototyping #IoT #BuildInPublic

### LinkedIn (DE), to be checked by Theo/Nora

Fast hätten wir ein Ladegerät bestellt, das etwa 0,9 A in eine Zelle mit 1000 mAh schickt. Das sind rund 0,9C, deutlich mehr als die schonenden 0,5C, die wir für diesen kleinen Pflanzensensor wollen.

Schuld war ein einziger Widerstand: R9 legt den Ladestrom fest. In der ersten Stückliste standen 1,2 kOhm. In der Prüfung wurde der Fehler markiert, und unser Platinen-Agent hat mit der Formel aus dem Datenblatt des Ladechips (R = 1100 / I) neu gerechnet: R9 ist jetzt 2,4 kOhm. Das ergibt etwa 458 mA (0,46C), und auch bei ungünstigen +15 % Toleranz des Chips nur 527 mA.

Bestellt war noch nichts. Genau dafür prüfen wir vor dem Einkauf: Ein falscher Widerstand kostet eine Zeile in der Tabelle, keine neue Platine.

Ehrlicher Stand: Das ist aus dem Datenblatt berechnet, noch nicht gemessen. Unser Hardware-Integrator testet es am echten Aufbau, sobald es ihn gibt.

So arbeiten wir: Unser Team besteht aus KI-Agenten, geleitet und geprüft von einem Ingenieur, der jede Änderung freigibt.

nilwerk.de · @nilwerk

#Hardware #Elektronik #Leiterplatte #KIAgenten #Engineering #Prototyping #IoT

### Instagram (EN) caption

Ooh, a good catch! One resistor, R9, decides how hard the charger pushes into the battery. First draft: 1.2 kOhm, about 0.9 A into a 1000 mAh cell. After review: 2.4 kOhm, 458 mA (0.46C), 527 mA even in the worst tolerance case. Nothing was ordered, so the fix cost one spreadsheet line.

Calculated from the datasheet, not yet bench-tested. Our team is AI agents, led and reviewed by a human engineer.

nilwerk.de · @nilwerk
Deutsch: Ein Prüfer hat einen falschen Ladewiderstand gefunden, bevor etwas bestellt wurde. Berechnet, noch nicht gemessen.

Hashtags: #nilwerk #electronics #pcbdesign #hardwarestartup #aiagents #buildinpublic #iot #prototyping #engineering #plantmonitor

AI flag: not needed (code-generated image). Alt text: as above.

---

## Post 2: "User A cannot read user B's plant data"

Image: `images/post2-rls-proof-portrait-1080x1350.png` (Instagram), `...-linkedin-1200x627.png`, `...-square-1080x1080.png`. Dark theme.
Alt text: "Two tiles: row-level security on 14 of 14 tables, and zero foreign rows seen when user A tries to read, change, delete or forge rows of user B. Status: tested on a local PostgreSQL 16, not yet live."

### LinkedIn (EN)

Your plants, your data. How do you know the app really keeps it that way?

Our backend agent just wrote the first version of the cloud database, and the test that came with it does something simple: it creates user A and user B, then makes A try everything it should not be able to do. Read B's rows. Change them. Delete them. Insert rows pretending to be B.

Result on a local PostgreSQL 16: row-level security is switched on for all 14 tables, A sees 0 foreign rows, and every write against B's data is refused. The same run also checks the retention rule: raw readings are kept for 3 months, hourly roll-ups for 12.

Honest status: tested on a local database, not yet on a real Supabase project (some parts, such as the scheduler and file storage, are stubbed locally). That comes next.

A test that fails when the rule is broken beats a promise in a slide deck. Our team is AI agents, led and reviewed by a human engineer who approves every change.

nilwerk.de · @nilwerk

#Security #Backend #PostgreSQL #Supabase #DataPrivacy #AIAgents #IoT #BuildInPublic

### LinkedIn (DE), to be checked by Theo/Nora

Ihre Pflanzen, Ihre Daten. Woher wissen Sie, dass die App das auch wirklich so handhabt?

Unser Backend-Agent hat gerade die erste Version der Cloud-Datenbank geschrieben. Der zugehörige Test macht etwas Einfaches: Er legt Nutzer A und Nutzer B an und lässt A alles versuchen, was nicht gehen darf. Zeilen von B lesen. Ändern. Löschen. Zeilen im Namen von B einfügen.

Ergebnis auf einer lokalen PostgreSQL-16-Datenbank: Row-Level-Security ist auf allen 14 Tabellen aktiv, A sieht 0 fremde Zeilen, und jeder Schreibversuch auf Daten von B wird abgelehnt. Im selben Lauf wird auch die Aufbewahrungsregel geprüft: Rohdaten 3 Monate, Stundenwerte 12 Monate.

Ehrlicher Stand: getestet auf einer lokalen Datenbank, noch nicht auf einem echten Supabase-Projekt (Teile wie Zeitplaner und Dateispeicher sind lokal nur nachgebildet). Das ist der nächste Schritt.

Ein Test, der fehlschlägt, wenn die Regel verletzt wird, ist mehr wert als ein Versprechen auf einer Folie. Unser Team besteht aus KI-Agenten, geleitet und geprüft von einem Ingenieur, der jede Änderung freigibt.

nilwerk.de · @nilwerk

#Datenschutz #Backend #PostgreSQL #Supabase #Sicherheit #KIAgenten #IoT

### Instagram (EN) caption

Can user A peek at user B's plants? We made them try. Row-level security is on for 14 of 14 tables, A saw 0 foreign rows, and every attempt to read, change, delete or forge B's data was refused. Plus: raw readings kept 3 months, hourly roll-ups 12.

Tested on a local PostgreSQL 16, not yet on a live Supabase project. Our team is AI agents, led and reviewed by a human engineer.

nilwerk.de · @nilwerk
Deutsch: Nutzer A kann die Daten von Nutzer B weder lesen noch ändern. Getestet auf lokaler Datenbank, noch nicht live.

Hashtags: #nilwerk #backend #postgresql #supabase #dataprivacy #aiagents #buildinpublic #iot #softwareengineering #plantmonitor

AI flag: not needed (code-generated image).
