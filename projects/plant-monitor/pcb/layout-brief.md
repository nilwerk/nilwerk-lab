# Layout brief and DFM rules (Plan 4.P2 preparation, no layout yet)

Author: Emil (PCB Designer) · 2026-11-08 · Status: **prep**. Nothing is drawn, nothing is ordered. Inputs: `docs/interfaces/pcb-enclosure-bay.md`, `hardware/bom/cell-decision-A034.md`, `pcb/design.py`, ESP32-C3-MINI-1 datasheet v2.2 and the Espressif Hardware Design Guidelines (both read 2026-11-08), JLCPCB capabilities page (read 2026-11-08). Tags: **[read]** = taken from a source read today, **[mine]** = my proposal or assumption, **[open]** = needs an answer.

## 1. What is fixed

| Item | Value | Source |
|---|---|---|
| Cell (EEMB LP603449-PCM) | 51 x 34.5 x 6.3 mm, about 22 g; PCM at one end, wires/plug leave there; tolerance and swelling not stated | [read] A-034 listing; length is <= 50 mm in EEMB's datasheet, 51 is the bay input |
| Bay | at least 51 x 34.5 x 6.3 mm plus Yara's own allowance (not set by me) | `pcb-enclosure-bay.md` |
| Module U1 ESP32-C3-MINI-1-N4 | 13.2 x 16.6 x 2.4 mm (+-0.15), antenna at one short end, 48 pads 0.4 x 0.8 mm | [read] datasheet v2.2 Fig 11-1 / ordering table |
| USB-C J1 (HRO TYPE-C-31-M-12, C165948) | body size and shield-pad numbers **not yet read** from the drawing; budget 9 x 7.5 mm, 3.3 mm high | [open] read the C165948 drawing before drawing the footprint; budget is [mine] |
| Battery connector J2 | JST S2B-PH-SM4-TB, about 6 x 4.5 mm plus mating housing and bend room for wires | `pcb-enclosure-bay.md`; plug pitch/polarity unverified |
| Switches SW1-SW3 | 5.1 x 5.1 mm each (custom footprint `NW:SW_TS-1187A-B-A-B_5.1x5.1`, height not read) | BOM |
| Sensors | AHT20 DFN-6 3 x 3 x 1.0 mm (custom footprint), BH1750 WSOF-6 (custom footprint) | BOM |
| Layers / assembly | 2 layers, FR-4 1.6 mm, one assembled side (JLC SMT), 45 BOM pieces | role file, `bom-draft.csv` |
| Board interior | **not given**: Yara has not published enclosure v3 inner dimensions | [open] Q1-Q3 below |

## 2. Board outline constraints (checklist for 4.P2)

O1. **Cell bay is not copper.** The 51 x 34.5 mm cell footprint (plus Yara's allowance) is a keep-out for parts taller than the bay height allows; beside = outside the board outline, under = board bottom side must be flat (no THT legs, no parts on the bottom: single-side assembly makes this free).
O2. **Antenna** (Espressif Hardware Design Guidelines, "Positioning a Module on a Base Board") [read]: put the module so the **PCB antenna is outside the base board or at the board edge** with the feed point at the edge; if it cannot overhang, **cut the board away on both sides of the antenna and below it**; never place the module in the middle of the board with clearance hollowed on all four sides; put solid ground copper and dense ground vias on the base board near the antenna. In the housing keep **at least 15 mm clear in all directions** around the antenna. The datasheet's pin-layout figure marks the keep-out zone on the module's antenna end; the board's copper, traces, parts, screws and the cell stay out of it on **both layers**.
   - Consequence for the cell: the cell must be **>= 15 mm from the antenna** (risk R-06 asks the same: no battery/probe cable near it). Metal heat-set inserts (brass, 3D standard) also stay 15 mm away from the antenna.
   - Consequence for the stake: the antenna end is the end **away from the soil** (R-06).
O3. **Ground under the module** body except the antenna area; the module's ground pad needs **at least nine ground vias** (Espressif guideline [read]); 2-layer power on top, solid GND on the bottom. Espressif **recommends 4 layers**; the role file says 2. I keep 2 layers for the 3-unit demo (cost) and put a risk line in the 4.P3 review: measure RSSI on the first board; escalate to 4 layers only if the closed-enclosure RSSI fails (R-06 trigger: > 10 dB below the dev kit).
O4. **USB-C J1** on a short or long edge, receptacle mouth flush with the outline, **far from the antenna** (cable and its shield detune the antenna); ESD D1 within 10 mm of J1, VBUS C10 at the connector, D+/D- short (<= 30 mm, over solid ground, 90 ohm differential per Espressif is not achievable to the letter on 2 layers: keep them short and paired) [mine]. Position (which edge, how far from the stake) is Yara question Q4.
O5. **Soil stake connector** (E1, nets SOIL_PROBE and GND): two options. **S1 (recommended for the 3 demo units): the electrodes are copper on a tail of the same board** (no connector, no contact corrosion, one part), tail at the end **opposite the antenna**, electrodes covered by solder mask (no bare copper in soil), ground guard on the electrode edges, SOIL_PROBE trace short, routed away from the antenna end and from the TP4056/LED area. **S2: separate stake PCB plus a 2-pin connector** (board edge, sealed by Yara's gasket): only if Yara or Arsany wants a replaceable stake; adds a part and a seal. Stake length, width, whether it is one piece: Q5.
O6. **Placement zones** [mine], for a board in portrait with the antenna at the top: top = antenna overhang + module; middle = power (J1, U3 TP4056, U2 LDO, D2/D3, C1-C4) kept **>= 10 mm away from U5 AHT20** (the TP4056 dissipates about 0.78 W while charging: AHT20 would read warm), U6 BH1750 on the face that sees the light window; bottom = soil front end (U7, R12, C8) right at the tail so SOIL_PROBE is short; switches SW1/SW2 (BOOT/RESET) reachable with the case open only, **SW3 pinhole under the wall hole** (position from Yara, Q6); J2 at the cell end.
O7. **Mounting holes**: 2 x M2 or M3 (hole size and positions from Yara, Q7), copper keep-out 0.3 mm + annular, none in the antenna keep-out, none near the USB-C pull-out force path without a pad.
O8. **Outline output**: DXF (outline + hole centres + keep-out polygons on a separate layer) and STEP for Yara; any change after the first export is announced to the Lead the same day (playbook rule 15).

## 3. Cell position: beside or under the board (Yara needs this answered)

My numbers, with a board area need of about 1200-1400 mm2 [mine: 219 mm2 module + 70 USB-C + 80 switches + about 250 passives/ICs with clearance, plus routing]; board 34.5 mm wide, about 38 mm long; the 15 mm antenna rule applies.

| | A. Beside (cell and board side by side, antenna at the far end) | B. Under (board on top of the cell, antenna end overhangs the cell by >= 15 mm) |
|---|---|---|
| Footprint L x W | about 51 + 5 + 38 = **94 x 34.5 mm** (5 mm cell-to-board gap for wires/J2) | about 51 + 15 = **66 x 34.5 mm** |
| Height | max(6.3, 1.6 + 3.3 USB-C) = **about 6.3 mm**, plus walls | 6.3 + 1.6 + 3.3 = **about 11.2 mm**, plus walls |
| RF | cell is about 30 mm from the antenna, 15 mm rule met by itself | overhang must be designed; cell and its PCM sit under the board next to the module ground: still >= 15 mm from the antenna feed |
| Thermal | cell away from TP4056 heat | TP4056 (0.78 W) heats the cell directly: charge limit 45 C, needs a thermal gap; **worse** |
| Assembly | simplest; cell can be swapped without lifting the board | board must be lifted for the cell; cell wires run under the board |
| Risk | long, flat enclosure, stake at the end | swelling cell presses on the bottom side; PCM end vs J2 position |

**Recommendation: A (beside) for v1 of the 3-unit demo**: RF and thermal are safe by geometry and the cell stays replaceable. B only if Yara's form needs a footprint under about 70 mm; then I need the overhang and a 2-3 mm thermal gap under U3 agreed first. This is a recommendation; the decision is Yara's and Arsany's.

## 4. Questions Yara must answer (before I draw the outline)

| # | Question | Why it matters |
|---|---|---|
| Q1 | Cell beside or under the board (section 3)? Which is your enclosure form? | footprint and height of the board |
| Q2 | Usable **inner length, width, height** of the electronics compartment (after walls, seal groove, standoffs), and the cell bay allowance (swelling, wire bend) you add to 51 x 34.5 x 6.3 | outline size and component height limit |
| Q3 | Board orientation in use (stake vertical, antenna up?) and which end is the top | antenna and stake end |
| Q4 | Where does the USB-C cable enter (which wall, height above the stake, seal)? Cut-out size? | J1 edge and position |
| Q5 | The stake: length, width, thickness, **one piece with the board** (my S1) or a separate part with a connector (S2)? Where does it pass the seal? Which part of it is in soil? | tail outline, electrode area, connector |
| Q6 | Pinhole position for SW3 (wall, centre, diameter, depth to the switch), BH1750 light window centre and size, AHT20 vent position | switch/sensor coordinates, tolerance |
| Q7 | Fastening: screws (M2/M3?) or snap fit; hole positions and diameters; are brass inserts near the antenna avoidable (15 mm)? | mounting holes and keep-outs |
| Q8 | Which wall do the cell wires exit and how long is the clear bay at the PCM end? (cell wire length is unverified) | J2 position |
| Q9 | Does the enclosure have an internal metal part (screws, inserts, label, shield) anywhere within 15 mm of the module's antenna end? | RF keep-out |

## 5. DFM and JLCPCB rules I will use

Capability numbers are from `jlcpcb.com/capabilities/pcb-capabilities`, read 2026-11-08 [read]; the "design rule" column is my choice with margin [mine]. Re-check on the day of the Gerber export (pages change).

| Topic | JLC capability [read] | Design rule [mine] |
|---|---|---|
| Layers, thickness, copper | 2-layer FR-4, 1.6 mm (tolerance +-10 %), 1 oz outer | 2 layers, 1.6 mm, 1 oz |
| Trace / space | minimum 0.15 / 0.15 mm under solder mask (1 oz); 3 mil extreme | **0.2 / 0.2 mm** default, 0.15 only at fine-pitch pads; power 0.4 mm (VBAT/3V3 0.5 mm) |
| Via | min hole 0.15 mm (0.2 preferred); via diameter >= hole + 0.15; PTH annular ring >= 0.2 mm | **0.3 mm drill / 0.7 mm pad**; hole-to-track >= 0.2 mm; none under pads except the module ground pad |
| Pad to pad (different nets) | 0.15 mm; pad to track 0.1 mm | 0.2 mm; keep 0.5 mm between the 5.1 x 5.1 switches and edges |
| Copper to routed edge | >= 0.2 mm; routed outline tolerance +-0.2 mm | **>= 0.5 mm** (more near V-cut or tabs: V-cut needs >= 0.4 mm) |
| Silkscreen | line >= 0.15 mm, text height >= 1.0 mm, pad to silk >= 0.15 mm | text 1.0 mm / 0.15 mm line, reference designators outside pads, **polarity marks for D2, D3, U-pin 1, J1** |
| Solder mask | bridge 0.10 mm; opening to neighbouring trace >= 0.09 mm | mask expansion 0.05 mm; fine-pitch (0.4 mm module pads) check bridges in DFM view |
| Surface finish | HASL (leaded / lead-free), ENIG, OSP | **lead-free HASL** for the demo; ENIG if the JLC DFM flags 0.4 mm pitch or flatness; stake electrodes stay under mask |
| Min board size / panel | min 5 x 5 mm; for SMT assembly: 5 mm tooling edges, 2 mm tooling holes, 1 mm fiducials 3.85 mm from the panel edge (mouse-bite panels) | Because the outline is irregular (tail, antenna cut-outs), order as a **JLC-made panel with breakaway rails**, not a bare irregular board; fiducials only on the rails |
| Assembly | single side, Economic PCBA (fee per Extended part, `bom-draft.md`) | all 45 SMD parts on **top**; bottom copper only GND and the stake side; no THT (J2 is SMD, USB-C shield pads SMD; check C165948 footprint for through-hole shield legs before choosing) |
| Parts | BOM LCSC numbers; 3 custom footprints (U5, U6, switches) + E1 + stake | footprints drawn from the datasheet figures and checked in the JLC DFM / 3D view; CPL rotation per JLC library (check pin 1 of U1, U3, U4, U5, U6, U7, D1) |
| Module land pattern | datasheet Fig 11-1: 48 pads 0.4 x 0.8 mm, ground pad with **>= 9 vias** | use the datasheet pattern exactly; paste: window the ground pad (square grid) to avoid floating the module |
| USB lines | Espressif: 90 ohm differential on 4 layers | 2 layers: short, parallel, over continuous GND, no vias, series resistors not needed on IO18/IO19 |
| Cell / charger | TP4056 0.78 W peak: ESOP-8 exposed pad | copper pour under the EP on top **and** 4-6 thermal vias to bottom GND; no AHT20 within 10 mm |
| Checks before Gerber | ERC/DRC zero in CI (`kicad-cli`), netlist = `check_netlist.py` PASS | add the DRC rules above to the `.kicad_pro` net classes (the `JLC` rule set), 3D view check against the DXF/STEP for Yara |

## 6. Simulation status this week

**LDO dropout at low battery: run** (ngspice 42 installed with `apt-get install ngspice`; the earlier "not installable" note covered only pip). Script `pcb/sim/ldo_dropout.py`, plot `pcb/sim/ldo_dropout.png`, table `pcb/sim/ldo_dropout.txt`. Static LDO model, cell resistance and TX burst 360 mA (335 mA + 25 mA CPU, datasheet Table 5-7 peak):

| Cell open-circuit | R_bat (assumed) | LDO dropout reading | V(3V3) min | vs 3.0 V (VDD33 min, datasheet Table 6-2) |
|---|---|---|---|---|
| 3.4 V (warning point) | 0.15 ohm | 60 mV at 300 mA (datasheet typ) | 3.270 V | +0.27 V |
| 3.4 V | 0.15 ohm | 95 mV at 300 mA (datasheet max) | 3.228 V | +0.23 V |
| 3.4 V | 0.30 ohm | 95 mV at 300 mA | 3.174 V | +0.17 V |
| 3.4 V | 0.30 ohm | 655 mV at 1 A (listing, pessimistic) | 3.053 V | +0.05 V |
| 3.3 V | 0.30 ohm | 655 mV at 1 A | 2.953 V | **-0.05 V FAIL** |
| 3.0 V (PCM cut-off region) | 0.15 ohm | 60 mV at 300 mA | 2.870 V | **-0.13 V FAIL** |

Result: the rail sags below 3.3 V as soon as the cell is under about 3.4-3.6 V (LDO in dropout; depends on the dropout reading), but **at the 3.4 V warning point it stays at or above 3.05 V in every case I modelled**: the earlier hand estimate in the README ("negative margin") was too pessimistic, because it treated 3.3 V as the target instead of 3.0 V (the module's minimum). What is **not** safe: a cell at about 3.0-3.3 V under load (any case with the pessimistic 0.655 ohm reading or 0.30 ohm plus 3.0 V OCV): firmware should not start Wi-Fi TX below about 3.3 V cell voltage (reduce or skip TX; Mira). Limits of the model: static dropout, no loop dynamics, R_bat is an assumption (cell <= 40 mOhm, PCM, DW01A/8205A, connector and trace unmeasured; deleting U4/Q1 removes about 2 x the FET Rds(on) = see `README.md` open point 4), OCV fixed during the burst. **Measure on the real board in 5.x (M8).** The other four simulations (divider accuracy, soil front end, charger thresholds, USB inrush) are **not run**.

## 7. Next steps (when Yara has answered)

1. Fix the outline and keep-outs, export DXF + STEP, announce to the Lead. 2. Draw the custom footprints (U5, U6, switches, E1). 3. Place and route per section 2 and 5, run DRC. 4. Remaining simulations. 5. 4.P3 review prep with the risk lines: 2 layers vs Espressif's 4-layer recommendation, USB 500 mA, TEMP/cold charging, antenna in the closed enclosure.
