# Interface note: battery bay, PCB outline and enclosure v3

Author: Emil (PCB Designer) · Date: 2026-11-06 · Updated: 2026-11-08 (cell decided) · Status: **input note** for the PCB outline (4.P2) and enclosure v3 (4.E3, Yara) · Source: Arsany's answer to A-020

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
- Power budget on this cell: `hardware/power-budget/power-budget.md` (typical case 4.5 months at the 1000 mAh minimum against the 3-month NFR-01; all currents unverified).

## Usable bay inside enclosure v3 (answer from Yara, 2026-11-08)
Single source: `mechanical/params.py` (inputs and allowances) and `mechanical/bay.py::dims()`, tabulated in `mechanical/README.md`. Cavity (what the cell may occupy), L x W x H in mm:

| Cell | Usable cavity | Bay module outer (tray + lid, bay only) |
|---|---|---|
| **EEMB LP603449-PCM (A-020, A-034: selected, ordered)** | 53.0 x 35.1 x 7.2 | 56.2 x 38.3 x 10.4 |
| Jauch LP603443JU (not selected, study only) | 47.0 x 35.1 x 7.4 | 50.2 x 38.3 x 10.6 |

Board, USB-C, seal and lid retention are not included (wait for the PCB outline). Values change only through `params.py`; do not copy them elsewhere.

## Update 2026-11-08: the cell is decided (A-034), dimensions for Yara

Arsany buys the **EEMB LP603449-PCM, Amazon.de ASIN B08FD39Y5R** (listing read 2026-11-08, details and unverified items in `hardware/bom/cell-decision-A034.md`). It is the same 603449-class cell the A-020 bay was drawn for; **the bay envelope does not change.**

| Item | Value | Status |
|---|---|---|
| Cell (nominal) L x W x H | **51 x 34.5 x 6.3 mm** | Amazon listing bullet; the listing's structured field says 34 x 51 x 6 mm; EEMB's datasheet (read 2026-11-07) says <= 50 x 34.5 x 6.3 mm |
| Tolerance, swelling | not stated | **unverified**. Yara adds her own allowance (a LiPo swells with age; one reviewer wrote his unit did not fit "as stated"); Arsany can measure the first real cell. I set no number |
| Mass | about 22 g | listing |
| Capacity | 1100 mAh typical / 1000 mAh minimum, 3.7 V | listing bullet |
| Protection | PCM board built in (on the cell, size and position not stated) | listing; the PCM sits at one end of the cell and its wires leave there: **unverified, check the first cell** |
| Connector and wires | JST plug (pitch unverified, PH 2.0 mm assumed), 2 wires assumed, **length not stated** | unverified: needs Arsany's read of photo 3. The PCB side is J2 JST PH 2-pin SMD (S2B-PH-SM4-TB, right angle, about 6 x 4.5 mm footprint plus the mating housing) |

What Yara needs to plan: a bay of at least 51 x 34.5 x 6.3 mm plus her own tolerance, swelling and wire-routing clearance (the plug end needs room for the wires to bend, length unknown until the cell arrives), the cell sitting beside or under the PCB (4.P2 decides the outline; any outline change is announced to the Lead the same day), and a polarity warning on the assembly drawing (check the plug polarity with a meter before connecting).

## Update 2026-11-10: enclosure v3 inner size (Q2 answer, Yara, slice 2)
Inner cavity **93.3 x 52.9 x 7.6 mm** (re-run on the #73 board), outer 98.1 x 57.7 x 11.6 mm (PETG review A-071) (walls 2.4, floor 1.6, lid 2.0), cell beside the board, 0.3 mm beyond the J1 shell, 1.0 mm above the antenna (overhang 4.5) (ASSUMED). The cell cavity above is unchanged. Details, assumptions and what Emil must keep fixed: `enclosure/v3/README.md`; numbers in `mechanical/enclosure_v3/params_v3.py`.
