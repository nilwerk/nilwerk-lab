# Logbook Day 5 (Fri 13 Nov): we caught a mistake. Draft, nothing published or scheduled.

Facts are as of Sun 8 Nov 2026; the five pull requests (#41, #42, #44, #45, #46) were open and not merged then. **On the day of posting: recheck merge status and wording ("waiting for a human" may be "merged").** Images: `images/day5-caught-mistakes-{en,de}-{portrait-1080x1350,linkedin-1200x627}.png` (light theme). Alt text EN: "Two tiles: 3 mistakes caught by review before merge; first edge-AI model finds 27 to 40 percent of wetting events against a 95 percent target. Status: counted from review comments, as of 8 November." Claims: `claim-check.md`.

**German check needed:** the DE texts below and the DE images must be checked by Theo or Nora before Arsany sees them. Not checked yet.

## LinkedIn (EN)

Nilwerk Logbook, day 5. Review found three wrong things, and two results we are not proud of.

On Sunday 8 November five AI agents each built one piece of our plant sensor: the circuit schematic, the app's sign-in screens, the cloud interface for sensor readings, the first on-device AI model and the battery bay of the enclosure. Each took between 6 and 15 minutes of agent time. Then a second AI agent reviewed each piece and a third tested it. They found:

1. The temperature and humidity sensor was wired in the schematic with pins that did not match its datasheet. Fixed before any circuit board layout.
2. A caption said the battery bay grows "from 6.3 to 7.4 mm". The real change is 7.2 to 7.4 mm, just 0.2 mm.
3. A report said our AI model "beats the simple rule". The rule had been set so strictly that it found nothing, so the comparison proved nothing. Reworded.

The honest part: the first AI model finds 27 to 40 percent of the wetting events in real data. Our target is 95 percent. It does not meet it. And the electrical rules check of the schematic has never run yet, because our automated pipeline broke before it started.

None of the five is merged: a human decides that. That is the point of reviewing.

For engineers: Model B int8 MLP, recall 27 % val / 40 % test (8/20, 95 % CI 22-61 %), 0.52 false alerts per unit-week, target 95 % at <= 1 (FR-E02 not met); a rise-rule baseline finds 0 % at <= 1 FA/week (degenerate threshold), 30 % at about 9 and 80 % at 25. 134 tests pass (QA re-ran with the raw data). KiCad ERC: CI job fails at checkout (EACCES), never executed; our own netlist check passes and caught 7 of 8 deliberate bugs. Not run: real Supabase, native app build, chip latency, a print.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

#BuildInPublic #IoT #Hardware #EdgeAI #Engineering

## LinkedIn (DE), to be checked by Theo/Nora, not yet checked

Nilwerk Logbuch, Tag 5. Die Prüfung hat drei Fehler gefunden, und wir haben zwei Ergebnisse, auf die wir nicht stolz sind.

Am Sonntag, 8. November, haben fünf KI-Agenten je einen Baustein unseres Pflanzensensors gebaut: den Schaltplan, die Anmeldung in der App, die Cloud-Schnittstelle für Messwerte, das erste KI-Modell für das Gerät und die Akku-Aussparung des Gehäuses. Jeder brauchte zwischen 6 und 15 Minuten Agentenzeit. Danach hat ein zweiter KI-Agent jeden Baustein geprüft und ein dritter getestet. Gefunden wurde:

1. Der Temperatur- und Feuchtesensor war im Schaltplan mit Anschlüssen verdrahtet, die nicht zum Datenblatt passten. Behoben, bevor ein Platinenlayout entstand.
2. Eine Bildunterschrift sagte, die Akku-Aussparung wachse „von 6,3 auf 7,4 mm“. Tatsächlich sind es 7,2 auf 7,4 mm, also nur 0,2 mm.
3. Ein Bericht sagte, unser KI-Modell „schlägt die einfache Regel“. Die Regel war so streng eingestellt, dass sie nichts fand; der Vergleich bewies also nichts. Umformuliert.

Der ehrliche Teil: Das erste KI-Modell erkennt 27 bis 40 Prozent der Bewässerungsereignisse in echten Daten. Unser Ziel sind 95 Prozent. Es ist nicht erreicht. Und die elektrische Regelprüfung (ERC) des Schaltplans ist noch nie gelaufen, weil unsere automatische Pipeline vorher ausgefallen ist.

Keiner der fünf Bausteine ist gemergt: Das entscheidet ein Mensch. Dafür ist die Prüfung da.

Für Ingenieure: Modell B, int8-MLP, Recall 27 % Val / 40 % Test (8/20, 95-%-Intervall 22-61 %), 0,52 Fehlalarme pro Gerät und Woche, Ziel 95 % bei <= 1 (FR-E02 nicht erfüllt); eine Anstiegsregel als Vergleich findet 0 % bei <= 1 Fehlalarm/Woche (entarteter Schwellwert), 30 % bei etwa 9 und 80 % bei 25. 134 Tests bestanden (QA hat mit den Rohdaten neu laufen lassen). KiCad-ERC: CI-Job scheitert beim Checkout (EACCES), nie ausgeführt; unsere eigene Netzlistenprüfung besteht und fand 7 von 8 absichtlichen Fehlern. Nicht gelaufen: echtes Supabase, native App, Latenz auf dem Chip, ein Druck.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

## Instagram (EN)

Logbook, day 5. Review found 3 wrong things before anything was merged. 🔍
A pin map that did not match the datasheet, a caption off by 1.1 mm (7.2 to 7.4, not 6.3 to 7.4), and "beats the rule" that hid a useless baseline.
Honest: our first AI model finds 27-40 % of wetting events, target 95 %. The circuit rules check (ERC) has never run yet.
For engineers: recall 8/20 on test (95 % CI 22-61 %), 0.52 false alerts/unit-week; ERC blocked by a CI checkout error.
AI agents, led and reviewed by humans. nilwerk.de · @nilwerk
Deutsch: Die Prüfung fand 3 Fehler; unser KI-Modell erreicht 27-40 % statt 95 %. (to be checked)

#nilwerk #buildinpublic #iot #edgeai

## Metricool

Not created. On 8 Nov only Instagram `nilwerk` is connected in Metricool (no LinkedIn), the images have no public URL yet, and the DE text is unchecked. Text drafts only; nothing scheduled or published.
