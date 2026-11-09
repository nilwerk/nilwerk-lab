# JLCPCB order package: plant-monitor, Plan 4.P4 prep (dry run)

> **STATUS: DRAFT. NOT A RELEASE. NOT ORDERED.**
> Routing is **not done**: the board has 0 tracks. **7 distinct footprints are placeholders** (pad geometry not from the manufacturer drawings). **4 of the 5 simulations are not run.** The Gerbers here come from an **unrouted** board and are **not a release**. Gate **4.P3 (review) is Arsany's and comes first**. Nothing was logged in to JLCPCB, uploaded, ordered or paid. The package is for Arsany to review and submit himself.

Owner: Emil (PCB designer). Branch `agent/pcb/4.P4-prep`, stacked on PR #64 (`agent/pcb/4.P2`, head `da39d2c`): **merge #64 first, then this PR.**

## What is ready

| Item | File | Basis |
|---|---|---|
| Gerber + drill set (22 files, 2 layers, Edge.Cuts, one 0.30 mm PTH tool, 16 holes = 16 vias) | `gerbers/plant-monitor-gerber.zip` | copied from the CI `pcb-fab` artifact of run 42628752571 (job `pcb`, KiCad 9.0.9, head `da39d2c`); not re-exported locally, KiCad is not in the agent session |
| Assembly BOM in JLCPCB format (27 lines, 45 parts, LCSC Part # on every line) | `bom-jlc.csv` | generated from `pcb/bom.csv` |
| Pick-and-place, 45 parts, all top | `cpl-jlc.csv` | generated from the CI `cpl.csv`; positions match the board file (Y sign as KiCad position file) |
| BOM with LCSC stock, JLC stock, lifecycle, price breaks, cost at 3 / 5 / 1000 boards | `bom-lcsc.csv` | LCSC product API and JLC parts search, read 2026-11-09 by `hardware/bom/refresh_live.py` |
| Dry-run checklist, 40 items, each with a JLCPCB limit, its source and a result | `dry-run-checklist.md` | JLCPCB capability page, read 2026-11-09 |
| Cart list (what Arsany would click), marked NOT ORDERED | `cart-list.md` | generated |
| Hashes of all of the above | `MANIFEST.sha256` | |

Repo checks pass with `/usr/bin/python3 -I`: `check_layout.py` 18/18, `check_netlist.py` all PASS.

## What is blocked

Checklist results: **5 FAIL, 12 OPEN or UNVERIFIED** (`dry-run-checklist.md`, last line).

| Blocker | Why it blocks | Checklist |
|---|---|---|
| Routing (0 tracks, GND zone not filled) | no release, no order | R1, F7, F22 |
| Panel with rails, SMT tooling and fiducials | the outline is 34.5 x 67 mm, below JLCPCB's 70 x 70 mm panel minimum; no tooling holes or fiducials placed | F5, F6 |
| 7 placeholder footprints (U1 module pattern, J1 USB-C, J2 JST, SW1-SW3, U5 AHT20, U6 BH1750, E1 stake) | PCBA needs the drawn footprint; pad geometry is not from the drawings | A9 |
| Via in pad: 16 vias (12 under the module, 4 under the TP4056 pad) | JLCPCB needs filled and capped vias for vias in pads, or the vias move; the option price is not read | F12 |
| 4 simulations not run (divider, soil front end, charger thresholds, USB inrush) | release gate (4.P1 list) | R2 |
| Gate 4.P3 review | Arsany's gate, first | R3 |
| Enclosure inputs Q1-Q11 | the outline is still a proposal | R4 |

## What is unverified (needs JLCPCB's order pages or a physical check)

- CPL rotation per JLC library part and the CPL origin: the file matches the board file, but JLC's CAM preview must confirm both (A10, F23).
- JLC fab, PCBA labour, stencil and Extended-part fees (A7, A8). The cost table is LCSC catalogue price only.
- Price-break rows below their first LCSC break: 37 line-quantity pairs use the first break (A7).
- LCSC stock is 0 today for C15849 (C12, C13) and C14663 (C5-C11) while JLC stock is large (A6). JLC PCBA uses JLC stock (A5, pass).
- The LiPo cell (not in the JLC BOM, bought by Arsany): price, seller, stock and plug pitch and polarity unverified (A-034, A-053).
- Via pad 0.70 mm on 0.30 mm drill gives a 0.20 mm annular ring: JLC's minimum; the 0.25 mm recommendation is not met (F11, a NOTE).

## How it was generated

```
# 1. CI pcb-fab artifact of the board head (already done for da39d2c, run 42628752571)
gh run download 42628752571 -R nilwerk/nilwerk-lab -n pcb-fab -D <dir>
# 2. live LCSC / JLC data (writes hardware/bom/bom-draft.csv)
/usr/bin/python3 -I hardware/bom/refresh_live.py
# 3. package (nothing uploaded)
/usr/bin/python3 -I projects/plant-monitor/pcb/jlcpcb/make_jlcpcb_package.py --fab-dir <dir>
```

Step 3 reads the board file, `bom.csv`, the bom-draft snapshot and the CI export, and runs the two repo checks. It writes every file in this folder; nothing here is hand-edited.

## Sources

- JLCPCB PCB capabilities: https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09). Re-check on the order day.
- LCSC product API `wmsc.lcsc.com` and product pages (stock, price breaks, product cycle), read 2026-11-09 20:17Z.
- JLC parts search API (JLC stock, Basic or Extended), read the same time.

## Next steps (not for this PR)

1. Route the board (next 4.P2 slice), revert the `unconnected_items` downgrade, fill the GND zone.
2. Draw the 7 footprints from the manufacturer drawings; then set `pin_verified` back to true where it holds.
3. Design the panel (rails, tooling holes, fiducials) and decide the via-in-pad option.
4. Run the remaining 4 simulations.
5. Gate 4.P3 (Arsany), then the order is prepared again with new files and the cart list updated.
