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
- **Update 2026-11-07:** the reference datasheet EEMB LP603449 (see `hardware/bom/bom-draft.md`) was read: <= 50 mm x 34.5 mm x 6.3 mm, 1000 mAh minimum, max discharge 2200 mA, charge 0 to 45 C, **bare cell with solder tabs** in that listing. Still open and set by the purchase spec (Arsany): protection circuit (PCM), connector type (JST PH, polarity to be checked) and wire length. Note the datasheet length is <= 50 mm, the A-020 envelope uses 51 mm (keep 51 as the bay input).
- Power budget on this cell: `hardware/power-budget/power-budget.md` (typical case 4.5 months at the 1000 mAh minimum against NFR-01 (typical >= 3 months; worst case > 1 month since 2026-11-08, ADR-015); all currents unverified).
