# Interface note: battery bay, PCB outline and enclosure v3

Author: Emil (PCB Designer) · Date: 2026-11-06 · Status: **input note** for the PCB outline (4.P2) and enclosure v3 (4.E3, Yara) · Source: Arsany's answer to A-020

## Battery cell (A-020)

| Item | Value |
|---|---|
| Cell | 603449 LiPo, 1S, 3.7 V nominal |
| Capacity | 1100 mAh typical, 1000 mAh minimum (maker figures as given; no cell datasheet read) |
| Mass | about 22 g |
| **Bay envelope (cell)** | **51 mm (L) x 34.5 mm (W) x 6.3 mm (H)** |

## What this means for the other side

- **Yara (4.E3):** the bay must hold at least 51 x 34.5 x 6.3 mm. Add the swelling and wire/connector clearance yourself (not set by Emil) and tell Emil the usable bay inside enclosure v3.
- **Emil (4.P2):** the cell is a separate part from the PCB. Either the PCB outline leaves the 51 x 34.5 footprint free (cell beside or under the board), or the cell sits outside the board area. The decision is made when the outline is drawn; **any outline change is announced to the Lead the same day** (playbook rule).
- **Open from the cell datasheet (not yet read):** protection circuit on the cell or not, connector type and wire length, maximum discharge current, tolerance on the envelope.
- Power budget on this cell: `hardware/power-budget/power-budget.md` (typical case 4.5 months at the 1000 mAh minimum against the 3-month NFR-01; all currents unverified).
