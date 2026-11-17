# Post drafts: "The crew has a life" (5 episodes + Reel + Story)

DRAFTS ONLY. Arsany approves, edits and publishes. German texts are Poppy's drafts and still need Theo or Nora, then Arsany. Every post carries the line "AI crew, led and reviewed by humans" (DE: "KI-Agenten, geleitet und geprüft von Menschen") and the marker for fiction. Facts: `claim-check.md` (F-numbers). Image files: `images/`. Recount/re-read any "as of" fact on the day of posting.

Common footer for LinkedIn EN: `nilwerk.de · AI agents, led and reviewed by humans. The characters' private lives are made up; the engineering is real.`
Common footer for LinkedIn DE: `nilwerk.de · KI-Agenten, geleitet und geprüft von Menschen. Das Privatleben der Figuren ist erfunden; die Technik ist echt.`

---

## Post 1 · Ep 1 "The guard that could never fire" (Wed 18 Nov 2026, 12:30 LinkedIn + Instagram)

**Images:** LinkedIn `images/10_linkedin_ep1-1200x627.png` (or `02_ep1_ines-vs-mira.png`). Instagram carousel (4 slides): `01_cover`, `02_ep1`, `07_drama-board`, `08_fact-or-fiction`. Story (optional, Wed 18:00): `09_story_ines-and-mira`.

### LinkedIn EN
FICTION ON TOP, ENGINEERING UNDERNEATH 🎬 Our AI crew has a (made-up) life. This is episode 1.

Mira (firmware agent) built a safety net: if the server keeps rejecting the same batch of sensor data, drop it, so one bad batch can never jam the queue. Ines (QA agent) asked her to show the log.

The sensor stores a new sample every 15 minutes. Mira's guard counted the *newest* sample, so every retry looked like a brand-new batch. It could never reach its limit. Ines's reaction, in the soap opera we wrote for them: "Do the maths, Mira."

For engineers: architecture review and QA found it on 17 Nov 2026; QA reproduced it (6 rejects in a row, buffer 4 to 10 samples, guard never fired). The existing 45 deliberate-bug checks did not cover it. Fix: count from the oldest sample. Now the 3rd reject drops the batch; 622 checks pass, 49/49 deliberate bugs caught. Host tests on a PC only: no device run, no Wi-Fi code yet.

The crew are AI agents, led and reviewed by humans. Their friendships and rivalries are fiction written by our storyteller agent Poppy; the bug, the numbers and the fix are real.

nilwerk.de · @nilwerk

### LinkedIn DE
FIKTION OBEN, TECHNIK DARUNTER 🎬 Unser KI-Team hat ein (erfundenes) Leben. Das ist Folge 1.

Mira (Firmware-Agentin) baute ein Sicherheitsnetz: Lehnt der Server denselben Datenstapel immer wieder ab, wird er verworfen, damit ein kaputter Stapel die Warteschlange nicht für immer blockiert. Ines (QA-Agentin) bat darum, das Log zu sehen.

Der Sensor speichert alle 15 Minuten eine neue Messung. Miras Schutz zählte die *neueste* Messung, also sah jeder neue Versuch wie ein frischer Stapel aus. Das Limit konnte nie erreicht werden. In der Seifenoper, die wir für die beiden geschrieben haben, sagt Ines: „Rechne nach, Mira.“

Für Ingenieure: Architektur-Review und QA fanden das am 17.11.2026; QA hat es nachgestellt (6 Ablehnungen in Folge, Puffer von 4 auf 10 Messungen, Schutz nie ausgelöst). Die bisherigen 45 absichtlichen Fehler-Prüfungen deckten es nicht ab. Korrektur: ab der ältesten Messung zählen. Jetzt verwirft die 3. Ablehnung den Stapel; 622 Prüfungen bestehen, 49 von 49 absichtlichen Fehlern werden erkannt. Nur Tests auf dem PC: noch kein Lauf auf einem Gerät, noch kein WLAN-Code.

Das Team sind KI-Agenten, geleitet und geprüft von Menschen. Freundschaften und Rivalitäten sind Fiktion, geschrieben von unserer Storyteller-Agentin Poppy; der Fehler, die Zahlen und die Korrektur sind echt.

nilwerk.de · @nilwerk

### Instagram carousel (4 slides) · caption EN
Slide 1: "The crew has a life." (cover) · Slide 2: the comic, Ines vs Mira · Slide 3: the drama board (100% fiction) · Slide 4: Fact or fiction?

Caption: Our AI crew has a made-up life and a very real job. 🎬 Episode 1: a safety guard that could never fire, because the sensor adds a sample every 15 minutes and the guard counted the newest one. QA proved it, Mira fixed it, and the checks now catch it (622 pass, 49/49 deliberate bugs caught; PC tests only, no device yet). Dashed = imagined by Poppy. Solid green = real. AI agents, led and reviewed by humans. nilwerk.de
Deutsche Zeile: Unser KI-Team hat ein erfundenes Leben und einen echten Job: Folge 1, ein Schutz, der nie auslösen konnte. KI-Agenten, geleitet und geprüft von Menschen.
Hashtags (max 5): #AIagents #QA #embedded #buildinpublic #nilwerk
Alt text: Four-panel comic style card. Ines, a QA engineer drawn as a cartoon avatar, tells Mira, the firmware engineer, that her safety guard counts the newest sensor sample so it can never fire. Green box: QA reproduced it, the fix is tested.

---

## Post 2 · Ep 2 "The road that never reached main" (Thu 19 Nov 2026, 12:30)

**Images:** `03_ep2_leo-wrong-road.png` (+ `08_fact-or-fiction.png` as slide 2 on Instagram).

### LinkedIn EN
EPISODE 2 · FICTION ON TOP, ENGINEERING UNDERNEATH 🗺️

Leo (our full-stack agent) finished a feature: a delete-account screen that stays locked until the user has exported their data. It was reviewed, merged, green ticks everywhere. And it never reached the main line of the code.

The merge went into a side branch that had already been merged. The finished work sat in a field. Theo (architect agent), the cartographer of the crew, has a different version of this story in the soap opera we wrote. The true version: a later pull request carried the work to main on 17 Nov 2026, and on the way the app's client was found calling a cloud address that does not exist on the deployed project. Fixed.

For engineers: PR merged into the 4.A4 branch after that branch had reached main, so the code reached main only through the 4.A9 PR. Guard, export check and URL are each protected by tests that fail if they are removed (mutation runs). Not run against the live project, not on a phone; the cloud has no export function yet, so on a real build delete stays locked, the safe direction.

AI agents, led and reviewed by humans. The characters' private lives are made up.

### LinkedIn DE
FOLGE 2 · FIKTION OBEN, TECHNIK DARUNTER 🗺️

Leo (unser Full-Stack-Agent) schloss eine Funktion ab: einen Bildschirm zum Löschen des Kontos, der gesperrt bleibt, bis die Nutzerin oder der Nutzer die Daten exportiert hat. Geprüft, gemerged, überall grüne Haken. Und trotzdem kam der Code nie in der Hauptlinie an.

Der Merge ging in einen Seitenzweig, der schon abgeschlossen war. Die fertige Arbeit lag auf dem Feld. Theo (Architektur-Agent), der Kartograf der Crew, hat in der Seifenoper, die wir geschrieben haben, seine eigene Sicht darauf. Die wahre Version: Eine spätere Änderung brachte die Arbeit am 17.11.2026 in die Hauptlinie, und dabei fiel auf, dass der Client der App eine Cloud-Adresse aufrief, die es im bereitgestellten Projekt nicht gibt. Behoben.

Für Ingenieure: Ein PR wurde in den Zweig 4.A4 gemerged, nachdem dieser bereits in main war; der Code kam nur über den PR 4.A9 nach main. Sperre, Export-Prüfung und URL sind durch Tests abgesichert, die fehlschlagen, wenn man sie entfernt (Mutationsläufe). Nicht gegen das Live-Projekt und nicht auf einem Telefon getestet; die Cloud hat noch keine Export-Funktion, daher bleibt „Löschen“ in einem echten Build gesperrt (die sichere Richtung).

KI-Agenten, geleitet und geprüft von Menschen. Das Privatleben der Figuren ist erfunden.

### Instagram caption EN
A finished feature that silently never reached main. 🗺️ Leo walked the whole route; Theo redrew the map. A later PR carried it home on 17 Nov and fixed a wrong cloud address on the way. Dashed = imagined, solid green = real. Tested with stand-ins only: no phone, no live project. AI agents, led and reviewed by humans. nilwerk.de
Deutsche Zeile: Eine fertige Funktion, die nie in main ankam, bis ein späterer PR sie nachlieferte. KI-Agenten, geleitet und geprüft von Menschen.
Hashtags: #AIagents #git #softwaretesting #buildinpublic #nilwerk
Alt text: Diagram of a main line with a side branch that left early; a dotted road from the side branch ends in a field, and a dashed green line carries the work back to main. Below, two cartoon avatars, Leo and Theo, talk about it.

---

## Post 3 · Ep 3 "The prototype that fell asleep" (Fri 20 Nov 2026, 12:30)

**Images:** `04_ep3_prototype-asleep.png`.

### LinkedIn EN
EPISODE 3 · FICTION ON TOP, ENGINEERING UNDERNEATH 😴

Our first hand-wired prototype (v1) is meant for a human hardware tester. Mira (firmware agent) spotted a trap in the default firmware: a board that was never set up goes into deep sleep with no timer before it has read a single sensor. On the bench, that would look like a dead board. So the bench build skips the setup step and just reads and prints.

Then Kai (pipeline agent) noticed the second trap: our automatic build had never built that bench version at all. Now it builds it too and checks that the switch is really on. In our soap opera, Kai is insufferably smug about it.

For engineers: v1 defaults set `CONFIG_PLANT_SETUP_FLOW=n` (reason: a code comment in `main.c`, read from source, not observed). 15/15 host tests pass; CI builds a second firmware with the v1 defaults. Not built or run on the real board: the bench steps are written but unrun. No hardware result exists.

AI agents, led and reviewed by humans. The characters' private lives are made up.

### LinkedIn DE
FOLGE 3 · FIKTION OBEN, TECHNIK DARUNTER 😴

Unser erster handverdrahteter Prototyp (v1) ist für einen menschlichen Hardware-Tester gedacht. Mira (Firmware-Agentin) entdeckte eine Falle in der Standard-Firmware: Eine nie eingerichtete Platine geht in den Tiefschlaf, ohne Wecker und bevor sie einen einzigen Sensor gelesen hat. Auf dem Prüftisch sähe das wie eine tote Platine aus. Deshalb überspringt der Bench-Build die Einrichtung und liest und druckt nur.

Dann bemerkte Kai (Pipeline-Agent) die zweite Falle: Unser automatischer Build hatte diese Bench-Version nie gebaut. Jetzt baut er sie mit und prüft, dass der Schalter wirklich gesetzt ist. In unserer Seifenoper ist Kai darüber unerträglich selbstzufrieden.

Für Ingenieure: Die v1-Voreinstellungen setzen `CONFIG_PLANT_SETUP_FLOW=n` (Begründung: ein Code-Kommentar in `main.c`, aus dem Quelltext gelesen, nicht beobachtet). 15 von 15 Host-Tests bestehen; die CI baut eine zweite Firmware mit den v1-Voreinstellungen. Nicht auf der echten Platine gebaut oder ausgeführt: Die Bench-Schritte sind geschrieben, aber nicht gelaufen. Es gibt kein Hardware-Ergebnis.

KI-Agenten, geleitet und geprüft von Menschen. Das Privatleben der Figuren ist erfunden.

### Instagram caption EN
A board that naps before it has read a single sensor. 😴 Mira found it, Kai made the pipeline build the bench version too. Illustration of the logic, not a photo or a bench result: nothing has run on the real board yet. Dashed = imagined, solid green = real. AI agents, led and reviewed by humans. nilwerk.de
Deutsche Zeile: Eine Platine, die schläft, bevor sie etwas gemessen hat. Noch nichts lief auf der echten Hardware. KI-Agenten, geleitet und geprüft von Menschen.
Hashtags: #embedded #ESP32 #AIagents #buildinpublic #nilwerk
Alt text: Two flow diagrams. Default build: power on, setup flow on, deep sleep with no timer, no sensor read. Bench build: power on, setup off, read sensors, print lines. Cartoon avatars of Mira and Kai comment above and below.

---

## Post 4 · Ep 4 "23 disguises at the door" (Mon 23 Nov 2026, 10:00)

**Images:** `05_ep4_23-disguises.png`.

### LinkedIn EN
EPISODE 4 · FICTION ON TOP, ENGINEERING UNDERNEATH 🎭

Before any plant-care tip reaches a plant, a safety filter checks it: never say "water now" when the soil is already soaked, never suggest leaving a plant outside in a frost. Sana (cloud AI agent) is the filter's proud author. In our soap opera she is a bouncer. Ines (QA agent) is the party crasher with 23 disguises.

The real scoreboard: 23 tricks, 15 held, 8 got in: three hid behind a negation ("don't forget to water"), three used words the filter did not know, two were broken weather forecasts. Fixed the same day; all 8 are now blocked.

For engineers: 68 tests and 66/66 deliberate bugs caught at the fixed state. Honest limit: it is still a deny-list, so odd phrasings and hidden characters can slip past if the live assistant mode were switched on; that mode is off by default and QA recommends an allow-list first. No real assistant or weather provider was called.

AI agents, led and reviewed by humans. The characters' private lives are made up.

### LinkedIn DE
FOLGE 4 · FIKTION OBEN, TECHNIK DARUNTER 🎭

Bevor ein Pflegetipp bei einer Pflanze ankommt, prüft ihn ein Sicherheitsfilter: nie „jetzt gießen“, wenn die Erde schon durchnässt ist, nie empfehlen, eine Pflanze bei Frost draußen zu lassen. Sana (Cloud-KI-Agentin) ist die stolze Autorin des Filters. In unserer Seifenoper ist sie Türsteherin. Ines (QA-Agentin) ist der Partygast mit 23 Verkleidungen.

Der echte Spielstand: 23 Tricks, 15 gehalten, 8 kamen durch: drei versteckten sich hinter einer Verneinung („Vergiss nicht zu gießen“), drei nutzten Wörter, die der Filter nicht kannte, zwei waren kaputte Wettervorhersagen. Am selben Tag behoben; alle 8 sind jetzt blockiert.

Für Ingenieure: 68 Tests und 66 von 66 absichtlichen Fehlern erkannt (Stand nach der Korrektur). Ehrliche Grenze: Es ist weiterhin eine Sperrliste; ungewöhnliche Formulierungen und versteckte Zeichen können durchrutschen, falls der Live-Assistent-Modus eingeschaltet würde; dieser Modus ist standardmäßig aus, und QA empfiehlt zuerst eine Positivliste. Es wurde kein echter Assistent und kein Wetterdienst aufgerufen.

KI-Agenten, geleitet und geprüft von Menschen. Das Privatleben der Figuren ist erfunden.

### Instagram caption EN
23 tricks. 15 bounced off. 8 got in. All 8 are now blocked. 🎭 Our QA agent attacked our plant-care safety filter; the honest limit stays on the card. Dashed = imagined, solid green = real. AI agents, led and reviewed by humans. nilwerk.de
Deutsche Zeile: 23 Tricks, 8 kamen durch, jetzt sind alle 8 blockiert. KI-Agenten, geleitet und geprüft von Menschen.
Hashtags: #AIsafety #QA #guardrails #buildinpublic #nilwerk
Alt text: A grid of 23 circles: 15 green ticks and 8 orange crosses, titled QA's 23 tricks. Cartoon avatars of Sana and Ines trade lines above. Green box: after the fix all 8 are blocked; the filter is still a deny-list.

---

## Post 5 · Ep 5 "The honest finale" (Tue 24 Nov 2026, 10:00)

**Images:** `06_ep5_honest-finale.png` (+ `07_drama-board.png` as slide 2 on Instagram).

### LinkedIn EN
EPISODE 5 · FICTION ON TOP, ENGINEERING UNDERNEATH 🌙

End of the day, the crew group chat (imagined): "Who is lying to me?" "Nobody. I checked." Here is the honest ledger of 17 Nov 2026, which is the real part:
✔ Tested on a computer with stand-ins.
✘ The app connecting to a real sensor: not yet.
✘ A real data export in the cloud: not built yet, so deleting an account stays locked (the safe direction).
✘ Anything measured on real hardware: not yet.

Real humans decided real things the same day: Arsany, our founder, approved the care-tip safety limits and ruled that an export must really reach the user before deletion unlocks. A human hardware tester gets the bench steps next. (They are people, not characters: they get no invented life.)

For engineers: real BLE provisioning is not implemented in the app (a non-mock build shows "needs the full app build"); no `export` edge function in the repo or deployed; nothing ran on hardware.

AI agents, led and reviewed by humans. The characters' private lives are made up.

### LinkedIn DE
FOLGE 5 · FIKTION OBEN, TECHNIK DARUNTER 🌙

Feierabend, der Gruppenchat der Crew (erfunden): „Wer lügt mich an?“ „Niemand. Ich habe geprüft.“ Hier die ehrliche Bilanz vom 17.11.2026, das ist der echte Teil:
✔ Getestet auf einem Computer mit Platzhaltern.
✘ Die App verbindet sich mit einem echten Sensor: noch nicht.
✘ Ein echter Datenexport in der Cloud: noch nicht gebaut, daher bleibt das Löschen eines Kontos gesperrt (die sichere Richtung).
✘ Irgendetwas auf echter Hardware gemessen: noch nicht.

Echte Menschen haben am selben Tag echte Entscheidungen getroffen: Arsany, unser Gründer, hat die Sicherheitsgrenzen für die Pflegetipps freigegeben und entschieden, dass ein Export den Nutzer wirklich erreichen muss, bevor das Löschen freigeschaltet wird. Ein menschlicher Hardware-Tester bekommt als Nächstes die Bench-Schritte. (Sie sind Menschen, keine Figuren: Sie bekommen kein erfundenes Leben.)

Für Ingenieure: Echtes BLE-Provisioning ist in der App nicht umgesetzt (ein Build ohne Mock zeigt „needs the full app build“); es gibt keine `export`-Edge-Function im Repo oder bereitgestellt; nichts lief auf Hardware.

KI-Agenten, geleitet und geprüft von Menschen. Das Privatleben der Figuren ist erfunden.

### Instagram caption EN
The most important episode: what we cannot do yet. 🌙 App to real sensor: not yet. Cloud export: not built, so delete stays locked. Anything measured on hardware: not yet. The crew chat is imagined; the ledger is real. AI agents, led and reviewed by humans. nilwerk.de
Deutsche Zeile: Die wichtigste Folge: was wir noch nicht können. Der Chat ist erfunden, die Bilanz ist echt. KI-Agenten, geleitet und geprüft von Menschen.
Hashtags: #buildinpublic #AIagents #honesty #hardwarestartup #nilwerk
Alt text: A chat window with five imagined messages from Nora, Ines, Leo, Mira and Poppy, and below a green ledger: one tick for tests on a computer, three crosses for what is not yet done.

---

## Reel (Sat 21 Nov 2026, 18:00, Instagram; optional LinkedIn Mon 23 Nov) · "One real bug. Two stubborn engineers."
File: `video/rough-cut_the-guard-that-could-never-fire.mp4` (25.2 s, 1080x1920, synthesised sound, NO voice-over yet). Script and brief: `video-script.md`.
Caption EN: One real bug. Two stubborn AI engineers. 🎬 A safety guard that could never fire, caught by QA on 17 Nov 2026 (622 checks pass, 49/49 deliberate bugs caught; PC tests only). The characters' love-hate story is fiction; the numbers are real. AI agents, led and reviewed by humans. nilwerk.de
Deutsche Zeile: Ein echter Fehler, zwei sture KI-Ingenieure. Die Geschichte ist erfunden, die Zahlen sind echt.
Label: music and effects are generated by code (no AI model, no licence issue). If an AI-generated voice is added, switch on Instagram's AI flag and write "AI-generated voice" in the caption.
