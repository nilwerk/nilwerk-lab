# Claim check: Logbook Day 5 (we caught a mistake)

Source of truth: `showcase/content/2026-11-07/claim-check.md` (post 1, checked by Ines: formula confirmed against TP4056 datasheet REV_2.4; Theo keeps sign-off). Every figure below is the same as there.

| # | Claim | Type | Source | Status |
|---|---|---|---|---|
| 1 | R9 decides the charge current; first value too high for a 1000 mAh cell (about 0.9 A) | C | `projects/plant-monitor/hardware/bom/bom-draft.md` R9 section; Ines QA comment (1.2 kOhm = 900 mA) | ok |
| 2 | Found by our reviewing AI agent (architect), new value by the PCB agent | D | `team/reports/2026-11-06.md` (Theo reviews, "R9 charger resistor error"); commit db782c5 | ok |
| 3 | Nothing had been ordered; fix cost one spreadsheet line | D | bom-draft.md header "Nothing was ordered" | ok |
| 4 | 2.4 kOhm = about 458 mA (0.46C), worst case 527 mA (+15 %) | C | bom-draft.md; formula I = (VPROG/RPROG) x 1100 | ok |
| 5 | Calculated, not measured; to be checked on a real board | D | bom-draft.md open items | ok |
| 6 | "review of 6 Nov" | D | report 6 Nov, extra round | ok |
| 7 | No "every/each" statement about reviews; no time numbers | n/a | Theo's rules | ok |
