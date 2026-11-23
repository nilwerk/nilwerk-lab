# Draft pack 23 Nov 2026: "Before the sensor is wired up"

**Status: DRAFT. Not published, not scheduled, not for posting.** Open before posting: owner approval, technical check (architect role), native German check, and the points in `claim-check.md` marked OPEN.

Source item: the 20 Nov simulator evidence item (folder named in `claim-check.md`). Image: screenshot 04 (plant list) from that item. It is a code-generated screenshot of the web build with mock data, so it is not AI imagery.

Claim IDs in square brackets (for example [C2]) point to `claim-check.md`, which names the source file for each claim. Remove the IDs before posting: public text carries no file names.

---

## LinkedIn, English (layer 1: the story)

Before a sensor is wired up, what can we actually show?

Our AI agent team is building a plant monitor: an app, and the firmware for a small sensor board. The real board has not been tested yet, so the proof has to come from somewhere else.

Here is one result from the latest run. The app's main screens run in a browser, with fake sensor values. The firmware starts in a chip simulator and prints five readings. [C1] [C2]

[Image: the plant list screen in the English web build, with the banner "MOCK: test values and a fake sensor, not real data. No real account."]

Every screen with fake data is marked MOCK. The numbers are test values, not measurements, and nothing ran on a phone or on a real board. [C3] [C6]

Why publish it? A plan is easy to write. A real screen with its MOCK label is harder to fake, so we show one.

AI agents, led and reviewed by humans.

**For engineers**
- App: web build in a headless browser, a fake Bluetooth scan and fixed test readings. Five screens: welcome, sign-up error, profile, plant list, plant detail. [C1]
- Firmware: Espressif ESP32-C3 simulator (QEMU), ESP-IDF 5.4, v1 build with a simulator overlay. It prints five mock readings, numbered 0 to 4. [C2]
- Limits: fixed mock values; calibration constants are placeholders until they are set on the bench; QEMU has no USB serial; no live database. [C3]
- Time: agent minutes about 6.5 (app) and about 18.5 (firmware, including the toolchain install). [C4] Own human estimates for an experienced engineer: about 4 h and about 4 h (estimated). [C5]

---

## LinkedIn, German (Ebene 1: die Geschichte)

Bevor ein Sensor angeschlossen ist: Was können wir schon zeigen?

Unser Team aus KI-Agenten baut eine Pflanzenüberwachung: eine App und die Firmware für eine kleine Sensorplatine. Die echte Platine ist noch nicht getestet. Deshalb brauchen wir andere Belege.

Hier ist ein Ergebnis aus dem letzten Lauf. Die Hauptbildschirme der App laufen im Browser, mit gefälschten Sensorwerten. Die Firmware startet in einem Chip-Simulator und gibt fünf Messwerte aus. [C1] [C2]

[Bild: die Pflanzenliste in der englischen Web-Version, mit dem englischen Banner „MOCK: test values and a fake sensor, not real data. No real account.“]

Jeder Bildschirm mit Testdaten ist als MOCK markiert. Die Zahlen sind Testwerte, keine Messungen. Nichts davon lief auf einem Telefon oder auf einer echten Platine. [C3] [C6]

Warum veröffentlichen wir das? Ein Plan lässt sich leicht schreiben. Ein echter Bildschirm mit seiner MOCK-Kennzeichnung lässt sich schwerer vortäuschen. Deshalb zeigen wir einen davon.

KI-Agenten, geleitet und geprüft von Menschen.

**Für Ingenieure**
- App: Web-Build in einem Headless-Browser, ein gefälschter Bluetooth-Scan und feste Testwerte. Fünf Bildschirme: Willkommen, Anmeldefehler, Profil, Pflanzenliste, Pflanzendetail. [C1]
- Firmware: Espressif ESP32-C3 im Simulator (QEMU), ESP-IDF 5.4, v1-Build mit Simulator-Overlay. Die Firmware gibt fünf Mock-Messwerte aus, nummeriert von 0 bis 4. [C2]
- Grenzen: feste Mock-Werte; Kalibrierkonstanten sind Platzhalter, bis sie auf dem Prüfstand gesetzt werden; QEMU hat keine USB-Seriell-Schnittstelle; keine Live-Datenbank. [C3]
- Zeit: Agenten-Minuten etwa 6,5 (App) und etwa 18,5 (Firmware, inklusive Toolchain-Installation). [C4] Eigene Schätzung für eine erfahrene Ingenieurin oder einen erfahrenen Ingenieur ohne KI: etwa 4 h und etwa 4 h (geschätzt). [C5]

---

## Alt text

- EN: Screenshot of the plant list in the app's English web build. A banner says "MOCK: test values and a fake sensor, not real data. No real account." Five example plants with status labels: OK, Too dry, Low battery, Offline, No sensor yet. One plant shows "No reading" as its value.
- DE: Screenshot der Pflanzenliste in der englischen Web-Version der App. Ein Banner sagt „MOCK: test values and a fake sensor, not real data. No real account.“ Fünf Beispielpflanzen mit englischen Statusangaben: OK, Too dry, Low battery, Offline, No sensor yet. Eine Pflanze zeigt als Wert „No reading“.

## Not in this pack, on purpose

- No Instagram draft: no media URL is set up for it, and no Metricool draft is made from this pack.
- No boot-log image: the rendered boot-log picture shows build paths on screen. A cropped version (only the reading lines) would need its own review first.
- No "first", "best" or speed ratio: the time figures are estimates and are labelled as such.
