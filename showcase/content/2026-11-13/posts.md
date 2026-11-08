# Logbook Day 5 (Fri 13 Nov): we caught a mistake. Draft, nothing published or scheduled.

Facts are as of Sun 8 Nov 2026; the five pull requests (#41, #42, #44, #45, #46) were open and not merged then. **On the day of posting: recheck merge status and wording ("waiting for a human" may be "merged").** Images: `images/day5-caught-mistakes-{en,de}-{portrait-1080x1350,linkedin-1200x627}.png` (light theme). Alt text EN: "Two tiles: 3 mistakes caught by review before merge; first edge-AI model finds 27 to 40 percent (validation and test) of wetting events against a 95 percent target. Status: counted from review comments, as of 8 November." Claims: `claim-check.md`.

**German check:** Theo's review conditions C4-C5 (terms, grammar, tone) are applied to the DE texts and DE images; Theo offered to re-check the DE text on request.

## LinkedIn (EN)

Nilwerk Logbook, day 5. Review found three wrong things, and two results we are not proud of.

On Sunday 8 November five AI agents each built one piece of our plant sensor: the circuit schematic, the app's sign-in screens, the cloud interface for sensor readings, the first on-device AI model and the battery bay of the enclosure. Each took between 6 and 16 minutes of agent time. Then a second AI agent reviewed each piece and a third tested it. They found:

1. The temperature and humidity sensor was wired in the schematic with pins that did not match its datasheet. Fixed before any circuit board layout.
2. A caption said the battery bay grows "from 6.3 to 7.4 mm". The real change is 7.2 to 7.4 mm, just 0.2 mm.
3. A report compared our AI model with a simple rule that scored 0 %. That rule had been set so strictly it fired on almost nothing, so the comparison proved nothing. The report now shows the whole curve (the rule finds 80 % but at 25 false alerts per week).

The honest part: the first AI model finds 27 percent (validation data) and 40 percent (test data) of the wetting events, meaning watering or rain, in real data. Our target is 95 percent. It does not meet it. And the electrical rules check of the schematic has never run yet, because our automated pipeline broke before it started.

None of the five is merged: a human decides that. That is the point of reviewing.

For engineers: Model B int8 MLP, recall 27 % val / 40 % test (8/20, 95 % CI 22-61 %), 0.52 false alerts per unit-week, target 95 % at <= 1 (FR-E02 not met); a rise-rule baseline finds 0 % at <= 1 FA/week (degenerate threshold), 30 % at about 9 and 80 % at 25. 134 tests pass (QA re-ran with the raw data). KiCad ERC: CI job fails at checkout (EACCES), never executed; our own netlist check passes and caught 7 of 8 deliberate bugs. Not run: real Supabase, native app build, chip latency, a print.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

#BuildInPublic #IoT #Hardware #EdgeAI #Engineering

## LinkedIn (DE)

Nilwerk Logbuch, Tag 5. Die Prüfung hat drei Fehler gefunden, und wir haben zwei Ergebnisse, auf die wir nicht stolz sind.

Am Sonntag, 8. November, haben fünf KI-Agenten je einen Baustein unseres Pflanzensensors gebaut: den Schaltplan, die Anmeldung in der App, die Cloud-Schnittstelle für Messwerte, das erste KI-Modell für das Gerät und die Akku-Aussparung des Gehäuses. Jeder brauchte zwischen 6 und 16 Minuten Agentenzeit. Danach hat ein zweiter KI-Agent jeden Baustein geprüft und ein dritter getestet. Gefunden wurden:

1. Der Temperatur- und Feuchtesensor war im Schaltplan mit Anschlüssen verdrahtet, die nicht zum Datenblatt passten. Behoben, bevor ein Platinenlayout entstand.
2. Eine Bildunterschrift sagte, die Akku-Aussparung wachse „von 6,3 auf 7,4 mm“. Tatsächlich sind es von 7,2 auf 7,4 mm, also nur 0,2 mm.
3. Ein Bericht verglich unser KI-Modell mit einer einfachen Regel, die 0 % erreichte. Diese Regel war so streng eingestellt, dass sie fast nie auslöste; der Vergleich bewies also nichts. Der Bericht zeigt jetzt die ganze Kurve (die Regel findet 80 %, aber mit 25 Fehlalarmen pro Woche).

Der ehrliche Teil: Das erste KI-Modell erkennt 27 Prozent (Validierung) und 40 Prozent (Test) der Bewässerungs- oder Regenereignisse in echten Daten. Das Ziel von 95 Prozent ist nicht erreicht. Und die elektrische Regelprüfung (ERC) des Schaltplans ist noch nie gelaufen, weil unsere automatische Pipeline vorher ausgefallen ist.

Keiner der fünf Bausteine ist übernommen (gemergt): Das entscheidet ein Mensch. Dafür ist die Prüfung da.

Für Ingenieure: Modell B, int8-MLP, Recall 27 % Val / 40 % Test (8/20, 95-%-Intervall 22-61 %), 0,52 Fehlalarme pro Gerät und Woche, Ziel 95 % bei <= 1 (FR-E02 nicht erfüllt); eine Anstiegsregel als Vergleich findet 0 % bei <= 1 Fehlalarm/Woche (unbrauchbar strenger Schwellenwert), 30 % bei etwa 9 und 80 % bei 25. 134 Tests bestanden (QA hat die Tests mit den Rohdaten erneut ausgeführt). KiCad-ERC: CI-Job scheitert beim Checkout (EACCES), nie ausgeführt; unsere eigene Netzlistenprüfung besteht und fand 7 von 8 absichtlichen Fehlern. Nicht gelaufen: echtes Supabase, native App-Build, Latenz auf dem Chip, ein 3D-Druck.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

## Instagram (EN)

Logbook, day 5. Review found 3 wrong things before anything was merged. 🔍
A pin map that did not match the datasheet, a caption that claimed 1.1 mm of growth (the real figure is 0.2 mm), and a comparison with a 0 % baseline rule that proved nothing.
Honest: our first AI model finds 27 % (validation) and 40 % (test) of wetting events (watering or rain), target 95 %. The circuit rules check (ERC) has never run yet.
For engineers: recall 8/20 on test (95 % CI 22-61 %), 0.52 false alerts/unit-week; ERC blocked by a CI checkout error.
AI agents, led and reviewed by humans. nilwerk.de · @nilwerk
Deutsch: Die Prüfung fand 3 Fehler; unser KI-Modell erkennt 27 % (Validierung) und 40 % (Test) statt 95 %.

#nilwerk #buildinpublic #iot #edgeai

## Metricool

Not created. On 8 Nov only Instagram `nilwerk` is connected in Metricool (no LinkedIn), the images have no public URL yet, and the DE text still awaits a re-check. Text drafts only; nothing scheduled or published.
