# Logbook Day 5 (Fri 13 Nov): we caught a mistake. Draft.

Images: `images/day5-caught-a-mistake-{en,de}-{portrait-1080x1350,linkedin-1200x627}.png`. Alt: "Before and after: charger resistor R9 of 1.2 kOhm gives about 0.9 A into a 1000 mAh cell; after review 2.4 kOhm gives 458 mA. Status: calculated, not yet measured." German to be checked by Theo/Nora, then Arsany. Claims: `claim-check.md`. Same facts as `content/2026-11-07` post 1 (confirmed there by Ines and Theo).

## LinkedIn (EN)

Nilwerk Logbook, day 5. We caught a mistake before it cost anything.

Our plant sensor has a small battery charger on its circuit board, and one tiny part decides how hard it pushes into the battery: a resistor called R9. In our first parts-list draft it had the wrong value for our battery: about 0.9 A into a 1000 mAh cell, much more than the gentle charge we want.

Our reviewing AI agent flagged it, and our PCB agent worked out a better value. Nothing had been ordered yet, so the fix cost one line in a spreadsheet, not a new board.

Honest status: the new value is calculated from the datasheet, not yet measured. It still has to be checked on a real board.

For engineers: R9 programs the charge current of the TP4056; from the datasheet, I = (VPROG / RPROG) x 1100. 1.2 kOhm gives about 900 mA; 2.4 kOhm gives about 458 mA (0.46C of 1000 mAh) and 527 mA in the worst case with +15 % tolerance. Source: BOM draft revision 2, review of 6 Nov. Open: thermal and cell-temperature behaviour.

AI agents, led and reviewed by humans. nilwerk.de · @nilwerk

#BuildInPublic #Hardware #PCB #AIAgents #Electronics

## LinkedIn (DE), to be checked by Theo/Nora

Nilwerk Logbuch, Tag 5. Wir haben einen Fehler gefunden, bevor er etwas gekostet hat.

Auf der Platine unseres Pflanzensensors sitzt ein kleiner Akku-Lader, und ein winziges Bauteil entscheidet, wie stark er in den Akku drückt: der Widerstand R9. In unserem ersten Stücklistenentwurf hatte er für unseren Akku den falschen Wert: etwa 0,9 A in eine Zelle mit 1000 mAh, deutlich mehr als das schonende Laden, das wir wollen.

Unser prüfender KI-Agent hat das markiert, und unser Platinen-Agent hat einen besseren Wert berechnet. Bestellt war noch nichts, die Korrektur kostete also eine Zeile in der Tabelle statt einer neuen Platine.

Ehrlicher Stand: Der neue Wert ist aus dem Datenblatt berechnet, noch nicht gemessen. Er muss noch an einer echten Platine geprüft werden.

Für Ingenieure: R9 legt den Ladestrom des TP4056 fest; laut Datenblatt gilt I = (VPROG / RPROG) x 1100. 1,2 kΩ ergibt etwa 900 mA; 2,4 kΩ ergibt etwa 458 mA (0,46C bei 1000 mAh) und im ungünstigsten Fall (+15 % Toleranz) 527 mA. Quelle: Stücklistenentwurf Revision 2, Prüfung vom 6. Nov. Offen: thermisches Verhalten und Verhalten bei Zelltemperatur.

KI-Agenten, geleitet und geprüft von Menschen. nilwerk.de · @nilwerk

## Instagram (EN)

Logbook, day 5. We caught a mistake before it cost anything. 🌱
A tiny resistor, R9, decides how hard the charger pushes into the battery. Our reviewing AI agent flagged the first value, nothing had been ordered, so the fix cost one spreadsheet line. New value: calculated, not yet measured.
For engineers: 1.2 kOhm = about 900 mA; 2.4 kOhm = about 458 mA (0.46C), 527 mA worst case.
AI agents, led and reviewed by humans. nilwerk.de · @nilwerk
Deutsch: Ein Review fand einen zu großen Ladestrom, bevor etwas bestellt wurde. Berechnet, noch nicht gemessen.

#nilwerk #buildinpublic #pcbdesign #aiagents #hardwarestartup
