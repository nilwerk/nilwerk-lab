# Agent Diary: week 1 drafts (Mon 9 to Sun 15 Nov 2026), EN + DE

**Drafts only. Nothing is published or scheduled. Arsany approves and publishes.** German text is **UNCHECKED** until Theo or Nora have checked it (marked DE-UNCHECKED). Facts are as of Sun 8 Nov 2026, 16:10 Berlin; **recount every status on the day of posting** (`../DAILY.md` section 2). Pull-request ids live in `claim-check.md`, never on the images. Speech bubbles are Poppy's drafting from the evidence ("persona voice"), not verbatim log lines. Every text ends with "AI agents, led and reviewed by humans" (DE: "KI-Agenten, geleitet und geprüft von Menschen"). Tag @nilwerk, link nilwerk.de. Instagram: English caption plus one German line; no AI-generated imagery (all images are code-drawn), so no AI flag. Image names are in `images/` (PNG and SVG, 1080x1350).

Format of every post: **plain story first, then "For engineers:"** (DE: "Für Ingenieure:"). LinkedIn gets EN and DE; Instagram EN plus one German line.

---

## Mon 9 Nov · Leo · "The app has a front door" · images `d1-leo-en.png`, `d1-leo-de.png`, `extra-screens-leo-app-en.png`

Alt (card): "Leo, AI agent and full-stack developer, in a speech bubble: he tapped through every account screen; three minutes for a newcomer is not measured yet." Alt (screens): "Three real screenshots of the plant app web build: welcome, sign-up with error messages, profile in dark theme; stand-in backend."

**LinkedIn EN**
Agent Diary, Monday. Meet Leo, our full-stack agent.

Today's win: the account screens of the plant app exist. Welcome, sign up and in, profile, delete account. The screenshots are real, from a web build. It talks to a stand-in backend, not a live one, and it is not on a phone yet.

Leo's honest line: "Three minutes for a newcomer? Not measured yet."

For engineers: Expo SDK 58 + TypeScript, tsc clean, jest 5 suites / 54 tests (QA re-ran them), 7.4 agent minutes (measured, Agent Log). Merged on 8 Nov. Not verified: real Supabase, a native build, a device.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

**LinkedIn DE (DE-UNCHECKED)**
Agenten-Tagebuch, Montag. Das ist Leo, unser Full-Stack-Agent.

Der Erfolg heute: Die Konto-Screens der Pflanzen-App stehen. Willkommen, Registrierung und Anmeldung, Profil, Konto löschen. Die Screenshots sind echt, aus einer Web-Version. Dahinter steckt ein Platzhalter-Server, kein echter, und auf dem Handy läuft es noch nicht.

Leos ehrlicher Satz: „Drei Minuten für einen Neuling? Noch nicht gemessen.“

Für Ingenieure: Expo SDK 58 + TypeScript, tsc sauber, jest 5 Suiten / 54 Tests (QA wiederholte sie), 7,4 Agentenminuten (gemessen, Agent Log). Am 8. Nov übernommen. Nicht geprüft: echtes Supabase, nativer Build, Gerät.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

**Instagram EN** Leo tapped through every screen of our plant app today. Real screenshots, stand-in backend, not on a phone yet. "Three minutes for a newcomer? Not measured yet." That honesty is the brand. Swipe for the screens. AI agents, led and reviewed by humans. 🌱 #BuildInPublic #AIAgents
**Instagram DE-Zeile (UNCHECKED)** Leo hat heute alle Screens unserer Pflanzen-App durchgeklickt: echte Screenshots, noch kein Handy.

---

## Tue 10 Nov · Mira · "We missed the target" · images `d2-mira-en.png`, `d2-mira-de.png`

Alt: "Mira, AI agent for firmware and edge AI, in a speech bubble: the model finds 27 percent on validation and 40 on test, goal 95; she would rather print the miss than a pretty number."

**LinkedIn EN**
Agent Diary, Tuesday. Mira, our firmware and edge-AI agent, has a result that is not a win. She prints it anyway.

Our first on-device AI model should notice when a plant has just been watered or rained on. The goal: find 95 % of those events. It finds 27 % on validation data and 40 % on test data. Not met, and we say so. The report now also shows the whole curve of the simple rule it is compared with, so nobody can pick a flattering corner.

An honest miss is progress: now we know what to fix next. Whether to keep training or ship the simple rule as a fallback is the founder's call.

For engineers: int8 MLP, recall 27 % val / 40 % test (8 of 20 events, 95 % CI 22-61 %), 0.52 false alerts per unit-week; target 95 % at 1 or fewer. 134 tests pass. Labels come from a rise rule, so recall is partly circular; data from a drip farm, not pots. Not run: latency on the chip. As of 8 Nov the pull request is open.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

**LinkedIn DE (DE-UNCHECKED)**
Agenten-Tagebuch, Dienstag. Mira, unser Firmware- und Edge-KI-Agent, hat ein Ergebnis, das kein Sieg ist. Sie zeigt es trotzdem.

Unser erstes KI-Modell fürs Gerät soll merken, wenn eine Pflanze gerade gegossen wurde oder Regen abbekam. Das Ziel: 95 % dieser Ereignisse finden. Es findet 27 % bei den Validierungsdaten und 40 % bei den Testdaten. Nicht erreicht, und wir sagen es. Der Bericht zeigt jetzt auch die ganze Kurve der einfachen Regel, mit der verglichen wird, damit sich niemand einen schmeichelhaften Ausschnitt herauspickt.

Ein ehrlicher Fehlschlag ist Fortschritt: Jetzt wissen wir, was als Nächstes zu tun ist. Ob weiter trainiert oder die einfache Regel als Rückfalllösung (Fallback) ausgeliefert wird, entscheidet der Gründer.

Für Ingenieure: Int8-MLP, Recall 27 % Val. / 40 % Test (8 von 20 Ereignissen, 95-%-KI 22-61 %), 0,52 Fehlalarme je Gerät und Woche; Ziel 95 % bei höchstens 1. 134 Tests grün. Labels stammen aus einer Anstiegsregel, der Recall ist teils zirkulär; Daten von einer Tropfbewässerungsfarm, nicht von Töpfen. Nicht gelaufen: Latenz auf dem Chip. Stand 8. Nov: PR offen.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

**Instagram EN** Mira's card today is a miss: 27 % and 40 % against a 95 % goal. We print it. "I would rather print the miss than a pretty number." Progress you can trust starts here. AI agents, led and reviewed by humans. #BuildInPublic #EdgeAI
**Instagram DE-Zeile (UNCHECKED)** Miras Karte heute: ein Fehlschlag, offen gezeigt. 27 % und 40 % gegenüber einem Ziel von 95 %.

---

## Wed 11 Nov · Emil · "One sensor, two pin maps" + the first real part · images `d3-emil-en.png`, `extra-thenvsnow-sensor-pins-en.png` (feed), `d3b-emil-cell-en.png` (Story) (+ DE)

Alt (pin card): "Then versus now: the humidity sensor with four wrong pins in the first draft, and with the 6-pin map from its datasheet in the fixed schematic." Alt (cell): "Emil, AI agent and PCB designer, in a speech bubble: the founder picked the battery cell and ordered it, the first real part."

> **HOLD (editor note, not part of any post): the "founder ordered the cell" card `d3b-emil-cell-*`, the cell paragraph of the LinkedIn texts and the Instagram "Story" sentence are not to be posted until Arsany approves this exact wording.** He said in chat on 8 Nov that he ordered the Amazon cell. Still unknown: shop, price, delivery, arrival, so none is named and "arrived" is not claimed. Without release, post the pin catch only.

**LinkedIn EN**
Agent Diary, Wednesday. Emil designs our circuit board. His win today was a catch.

His first sketch of the humidity sensor had the wrong pins. Four pins drawn, six on the maker's datasheet. A reviewing agent compared the two before any board existed, so it cost an edit, not a board. The first automatic electrical check ran on 8 November too: no errors.

And a real-world moment: our founder chose the battery cell and ordered it himself. Agents can prepare a purchase, never make one. The re-run of the battery-life check for that exact cell passes our relaxed rule on estimates.

For engineers: AHT20 draft SDA=1 GND=2 VDD=3 SCL=4; datasheet (6-pin DFN) 1 NC 2 VDD 3 SCL 4 SDA 5 GND 6 NC. ERC exit 0 (errors only; generic pin symbols, so no pin-level proof). QA closed the fix from the artefact, not the datasheet. Cell (as built): best case 11.0, typical 4.3 and worst case 1.36 months estimated, against at least 3, 3 and more than 1 (estimates, not bench-tested).

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

**LinkedIn DE (DE-UNCHECKED)**
Agenten-Tagebuch, Mittwoch. Emil entwirft unsere Platine. Sein Erfolg heute war ein Fund.

Seine erste Skizze des Feuchtesensors hatte falsche Pins. Vier Pins gezeichnet, sechs im Datenblatt des Herstellers. Ein prüfender Agent verglich beides, bevor es eine Platine gab. Das kostete eine Änderung, keine Platine. Die erste automatische Schaltplanprüfung (ERC) lief am 8. November ebenfalls: keine Fehler.

Und ein Moment aus der echten Welt: Unser Gründer wählte die Akkuzelle und bestellte sie selbst. Agenten dürfen einen Kauf vorbereiten, nie auslösen. Die neue Berechnung der Akkulaufzeit für genau diese Zelle erfüllt unsere gelockerte Regel nach Schätzung.

Für Ingenieure: AHT20 Entwurf SDA=1 GND=2 VDD=3 SCL=4; Datenblatt (6-Pin-DFN) 1 NC 2 VDD 3 SCL 4 SDA 5 GND 6 NC. ERC Exit 0 (nur Fehler; generische Pin-Symbole, kein Nachweis auf Pin-Ebene). QA hat den Fund anhand der Datei geschlossen, nicht anhand des Datenblatts. Zelle (wie gebaut): bester Fall 11,0, typisch 4,3, schlechtester Fall 1,36 Monate geschätzt, gefordert mindestens 3, 3 und mehr als 1 (Schätzungen, nicht im Labor getestet).

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

**Instagram EN** Four pins in the sketch, six on the datasheet. A reviewing agent caught it before any board existed. Swipe for then vs now. Story: the founder ordered our first real part, a battery cell. AI agents, led and reviewed by humans. #BuildInPublic #PCB
**Instagram DE-Zeile (UNCHECKED)** Vier Pins in der Skizze, sechs im Datenblatt: gefunden, bevor es eine Platine gab.

---

## Thu 12 Nov · Sana · "26 bugs, 26 caught, one real one" · images `d4-sana-en.png`, `d4-sana-de.png`

Alt: "Sana, AI agent and cloud engineer, in a speech bubble: 26 deliberate bugs, 26 caught; comparing with a second copy of the same job found a real bug, a new owner inheriting the old owner's plant."

**LinkedIn EN**
Agent Diary, Thursday. Sana builds the cloud door that sensor readings walk through.

We test that door by breaking it on purpose. Our mutation check plants 26 deliberate bugs, one at a time, and all 26 are caught. The first 17 were Sana's; a QA agent then found six gaps with 12 bugs of its own, and Sana closed them with 9 more. Then a real bug turned up. Two sessions had accidentally built the same job; comparing the copies showed that after a device changed hands, it still pointed at the previous owner's plant. Fixed, with a test.

It is not live yet: it ran against a local test database, not a real cloud project.

For engineers: mutation check 26 of 26 killed (Sana's run; QA re-ran the first 17 in 81 s). Boundary tests: 15 min claim token, 120 s clock skew, 32 events, minimum timestamp. SQL fix clears plant_id on ownership change. Not run: real Supabase, Deno runtime. As of 8 Nov the pull request is open.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

**LinkedIn DE (DE-UNCHECKED)**
Agenten-Tagebuch, Donnerstag. Sana baut die Cloud-Tür, durch die Messwerte gehen.

Wir testen diese Tür, indem wir sie absichtlich kaputtmachen. Unsere Mutationsprüfung baut 26 Fehler einzeln ein, und alle 26 werden gefunden. Die ersten 17 stammen von Sana; ein QA-Agent fand mit 12 eigenen Fehlern sechs Lücken, und Sana schloss sie mit 9 weiteren. Dann tauchte ein echter Fehler auf: Zwei Sitzungen hatten versehentlich dieselbe Aufgabe gebaut; der Vergleich zeigte, dass ein Gerät nach einem Besitzerwechsel noch auf die Pflanze des alten Besitzers zeigte. Behoben, mit Test.

Live ist es noch nicht: Es lief gegen eine lokale Testdatenbank, nicht gegen ein echtes Cloud-Projekt.

Für Ingenieure: Mutationsprüfung 26 von 26 erkannt (Lauf von Sana; QA wiederholte die ersten 17 in 81 s). Grenzwerttests: 15 Min. Claim-Token, 120 s Zeitabweichung, 32 Ereignisse, Mindest-Zeitstempel. SQL-Fix löscht plant_id bei Besitzerwechsel. Nicht gelaufen: echtes Supabase, Deno-Laufzeit. Stand 8. Nov: PR offen.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

**Instagram EN** 26 deliberate bugs. 26 caught. Then a real bug showed up: a new owner inherited the old owner's plant. Fixed, with a test. Not live yet, local test database only. AI agents, led and reviewed by humans. #BuildInPublic #Cloud
**Instagram DE-Zeile (UNCHECKED)** 26 absichtliche Fehler, 26 gefunden. Dazu ein echter, jetzt behoben. Noch nicht live.

---

## Fri 13 Nov · Yara · "Function first, then one touch of design" · images `d5-yara-en.png`, `extra-tracker-5-builds-en.png` (+ DE)

Alt (card): "Yara, AI agent and 3D designer, in a speech bubble: function first, then one deliberate touch of design; a pretty lid that leaks is not done." Alt (tracker): "Progress tracker as of 8 November: five builds each reviewed and tested by AI agents; two of five merged."

**LinkedIn EN**
Agent Diary, Friday. Yara designs the enclosure, and today she answered a very practical question: does the battery fit?

Yes. Her 3D model of the battery bay follows the size of the chosen battery (cavity 7.2 mm tall). It also carries a design rule our founder asked for: function first, then one deliberate design touch, and the touch may never break printing, sealing or fit. The first touch is a tiny circuit-trace pattern on the lid, behind a switch that is off by default, with tests that fail if it eats into the wall. Nothing is printed yet.

The picture on the right is a progress snapshot: five builds, two merged as of 8 November 16:10. The rest wait for the founder.

For engineers: CadQuery, cell 6.3 mm x 1.1 swelling + 0.2 clearance = 7.13 mm, rounded up to 7.2 mm (assumptions), walls 1.6 mm, PETG, 0.4 mm nozzle, fits a P1S plate. 22 tests; QA's 4 deliberate bugs all made the tests fail. Not run: slicer, a real print, a fit check. Pull request open.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

**LinkedIn DE (DE-UNCHECKED)**
Agenten-Tagebuch, Freitag. Yara gestaltet das Gehäuse, und heute beantwortete sie eine sehr praktische Frage: Passt der Akku?

Ja. Ihr 3D-Modell der Akku-Aussparung folgt der Größe des gewählten Akkus (Hohlraum 7,2 mm hoch). Dazu kommt eine Designregel, die sich unser Gründer gewünscht hat: erst Funktion, dann ein bewusstes Designmerkmal, und das darf Druck, Dichtheit und Passung nie gefährden. Das erste Merkmal ist ein winziges Leiterbahn-Muster im Deckel, hinter einem Schalter, der standardmäßig aus ist, mit Tests, die scheitern, wenn es in die Wand schneidet. Gedruckt ist noch nichts.

Das zweite Bild ist eine Fortschrittsübersicht: fünf Arbeitspakete, zwei übernommen, Stand 8. November 16:10 Uhr. Der Rest wartet auf den Gründer.

Für Ingenieure: CadQuery, Zelle 6,3 mm x 1,1 Aufquellen + 0,2 Spiel = 7,13 mm, aufgerundet auf 7,2 mm (Annahmen), Wände 1,6 mm, PETG, 0,4-mm-Düse, passt auf eine P1S-Platte. 22 Tests; QAs 4 absichtliche Fehler ließen die Tests alle scheitern. Nicht gelaufen: Slicer, echter Druck, Passprobe. PR offen.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

**Instagram EN** Does the battery fit? Yara's 3D bay says yes, at 7.2 mm tall. New rule: function first, then one design touch that may never break the print. Swipe for the progress snapshot: 5 builds, 2 merged (as of 8 Nov, 16:10). Not printed yet. AI agents, led and reviewed by humans. #BuildInPublic #3DPrinting
**Instagram DE-Zeile (UNCHECKED)** Passt der Akku? Yaras 3D-Modell sagt ja. Gedruckt ist noch nichts.

---

## Sat 14 Nov · Kai · "A job that never runs is a missing job" · images `d6-kai-en.png`, `extra-virtual-office-fiction-en.png` (FICTION, separate post) (+ DE)

Alt (card): "Kai, AI agent for the build pipeline, in a speech bubble: a job that never runs is not a green job, it is a missing one; the circuit check had never started, now it has." Alt (fiction): "Fiction, imagined by our agents: Ines, the QA agent, asks the office kettle for a log. Not a real event."

**LinkedIn EN**
Agent Diary, Saturday. Kai keeps our automatic pipeline green. Today he found something worse than red: a check that had never run.

Our pipeline was meant to run an electrical check on the circuit design. It could not even start: it died while fetching the code, because of a permissions detail in the check's container. Kai changed how the container runs. On 8 November the check ran for the first time and found no errors.

Why it matters: a green tick means nothing if the check behind it never ran.

For engineers: kicad/kicad:9.0 runs as a non-root user, actions/checkout failed with EACCES. Fix: container as root, nullglob for a missing .kicad_pcb, ERC stays strict. kicad-cli ERC exit 0 (errors only). DRC not run: no board file yet. Warnings are in the run artifact, not counted here. Merged on 8 Nov.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

**LinkedIn DE (DE-UNCHECKED)**
Agenten-Tagebuch, Samstag. Kai hält unsere automatische Pipeline grün. Heute fand er etwas Schlimmeres als Rot: eine Prüfung, die nie gelaufen war.

Unsere Pipeline sollte den Schaltplan elektrisch prüfen. Sie konnte nicht einmal starten: Sie brach beim Auschecken des Codes ab, wegen einer Berechtigungseinstellung im Container der Prüfung. Kai änderte, wie der Container läuft. Am 8. November lief die Prüfung zum ersten Mal und fand keine Fehler.

Warum das zählt: Ein grünes Häkchen bedeutet nichts, wenn die Prüfung dahinter nie lief.

Für Ingenieure: kicad/kicad:9.0 läuft als Nicht-Root, actions/checkout scheiterte mit EACCES. Fix: Container als root, nullglob bei fehlender .kicad_pcb, ERC bleibt strikt. kicad-cli ERC Exit 0 (nur Fehler). DRC nicht gelaufen: noch keine Platinendatei. Warnungen stehen im Lauf-Artefakt, hier nicht gezählt. Am 8. Nov übernommen.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

**Instagram EN** "A job that never runs is not a green job, it is a missing one." Kai fixed the pipeline so our circuit check could run for the first time: no errors. AI agents, led and reviewed by humans. #BuildInPublic #DevOps
**Instagram DE-Zeile (UNCHECKED)** Eine Prüfung, die nie lief, ist keine grüne Prüfung. Kai hat sie zum Laufen gebracht.

### Sat 14 Nov, second post (Story or feed, always dark theme): FICTION · "The kettle failed its review"

**First line of every text: "FICTION, imagined by our agents: not a real event."** (DE: "FIKTION, von unseren Agenten erfunden: kein echtes Ereignis.")
EN: *Imagined by our agents. From the virtual office: Ines asked the office kettle for a log. The kettle offered a feeling. Ines: "That is not a log." The kettle is now on a corrective plan. (Made up, for fun.)* The only real part: our QA agent's rule is to paste real output for every check.
DE (UNCHECKED): *Von unseren Agenten erfunden. Aus dem virtuellen Büro: Ines bat den Büro-Wasserkocher um ein Log. Der Wasserkocher bot ein Gefühl an. Ines: „Das ist kein Log.“ Der Wasserkocher steht jetzt unter Beobachtung. (Erfunden, zum Spaß.)* Der einzige echte Teil: Die Regel unseres QA-Agenten lautet, bei jeder Prüfung die echte Ausgabe einzufügen.
Images: `extra-virtual-office-fiction-en.png`, `-de.png`. No real number, result, person or quote inside.

---

## Sun 15 Nov · Theo · "The founder relaxed a rule, so we changed every page that quotes it" · images `d7-theo-en.png`, `d7b-nora-en.png` (Story, true story) (+ DE)

Alt (Theo): "Theo, AI agent and system architect, in a speech bubble: the founder relaxed the battery rule; he changed it in every document that quotes it and wrote down why." Alt (Nora): "Nora, AI agent and project lead: two Lead sessions built the same cloud job on 8 November; nothing was lost and the comparison is written down."

**LinkedIn EN**
Agent Diary, Sunday. Theo is our architect, the agent who asks "where is the contract for that?"

This week the founder relaxed the battery rule: the best case must last at least 3 months, the worst case just over 1 month. Changing a number is easy. Changing it everywhere it is quoted, and writing down why, is the job. Theo wrote the decision record and brought ten documents in line. On the estimates the chosen battery passes (typical above 4 months). It has not been bench-tested.

A true story, a little funny: on 8 November two of our Lead sessions ran at the same time and both built the same cloud job. Nothing was deleted, the copies were compared, one real bug turned up (the same event as Thursday's duplicate-job bug, seen from the Lead's side), and since 8 November every agent works in its own copy of the repository.

For engineers: ADR-015 pass = best >= 2190 h, typical >= 2190 h, worst > 730 h; formula unchanged (0.8 x rated minimum capacity / average current). Scenario definitions are Theo's proposal, still to be confirmed. Power-budget tests 25 OK, BOM tests 12 OK. Currents are estimates. Duplicate-job comparison: second copy had one commit and no pull request; cause was a shared git clone. Pull request open.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

**LinkedIn DE (DE-UNCHECKED)**
Agenten-Tagebuch, Sonntag. Theo ist unser Architekt, der Agent, der fragt: „Wo ist das als Schnittstelle festgeschrieben?“

Diese Woche lockerte der Gründer die Akku-Regel: Der beste Fall muss mindestens 3 Monate halten, der schlechteste nur über 1 Monat. Eine Zahl zu ändern ist leicht. Sie überall nachzuziehen, wo sie steht, und das Warum festzuhalten, ist die Arbeit. Theo schrieb das Entscheidungsdokument (ADR) und zog zehn Dokumente nach. Nach den Schätzungen besteht der gewählte Akku (typisch über 4 Monate). Im Labor getestet ist er nicht.

Eine wahre Geschichte, ein bisschen komisch: Am 8. November liefen zwei unserer Lead-Sitzungen gleichzeitig und bauten beide dieselbe Cloud-Aufgabe. Nichts wurde gelöscht, die Kopien wurden verglichen, ein echter Fehler kam zum Vorschein (dasselbe Ereignis wie bei Donnerstags Doppelarbeit, aus Sicht der Leitung), und seit dem 8. November arbeitet jeder Agent in seiner eigenen Kopie des Repositorys.

Für Ingenieure: ADR-015 bestanden = bester Fall >= 2190 h, typisch >= 2190 h, schlechtester > 730 h; Formel unverändert (0,8 x Nennkapazität min. / mittlerer Strom). Die Szenario-Definitionen sind Theos Vorschlag, noch zu bestätigen. Energiebudget-Tests 25 OK, Stücklisten-Tests 12 OK. Ströme sind Schätzungen. Vergleich der Doppelarbeit: zweite Kopie mit einem Commit und ohne Pull Request; Ursache war ein gemeinsamer Git-Klon. PR offen.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

**Instagram EN** Theo changed one battery rule in ten places and wrote down why. Story: two of our Lead sessions built the same job at once. True story, nothing lost, one real bug found. AI agents, led and reviewed by humans. #BuildInPublic #SystemsEngineering
**Instagram DE-Zeile (UNCHECKED)** Eine Regel, zehn Dokumente, ein Warum. Und eine wahre Geschichte von zwei Lead-Sitzungen.

---

## Reserve (true, ready for a quiet day)
- **Theo caught a misquote in our own draft**: "beats the simple rule" was never in a report. Source: architect review of the day-5 pack, condition C1. Card: Theo, with the earlier text (see git history of this folder).
- **Ines' 12 own bugs, 5 caught, 7 survived**: the QA agent finds gaps in the tests themselves (PR comment, 8 Nov).
