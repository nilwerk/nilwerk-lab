# Standard: 3D Manufacturing — In-house Printing, Functional Products, Small Batches

**Owner:** Arsany · **Applies to:** Yara (3D Product Designer) and every agent touching enclosures,
mounts or physical product design · **Status:** Decided 2026-11-07 — Nilwerk will run its own
in-house 3D printer for prototypes and small-batch manufacturing.

This standard **extends** `team/roles/mechanical.md`; it does not replace it. All existing
responsibilities, rules and project requirements stay in force. Apply it automatically to every
current and future embedded project that needs physical product design, unless Arsany explicitly
says otherwise. Requirements docs and answered Questions still win (TEAM.md §1).

---

## 1. Manufacturing setup

| Item | Value |
|---|---|
| Printer | **Bambu Lab P1S Combo with AMS** (in-house) |
| Technology | FDM / CoreXY |
| Build volume | **256 × 256 × 256 mm** |
| Nozzle | 0.4 mm standard |
| Filament | 1.75 mm |
| Budget | €500–€1,000 incl. initial accessories |
| Operator experience | Beginner (Arsany / Peter) — write print instructions accordingly |
| CAD | Fusion 360 preferred by Arsany (see §1a) |
| Market | Germany and EU |
| Production | Prototypes and small batches of ~5–10 units initially |

- Design everything to be printable on the P1S within its build volume.
- Do **not** assume industrial equipment, injection moulding or CNC machining.
- The AMS gives four-spool automatic material switching. Multicolour is optional, never a requirement
  for a functional product.
- Do not recommend expensive printer upgrades unless technically justified (and then raise it as a
  Needs-Arsany item with cost and reason).

### 1a. CAD toolchain: CadQuery source, Fusion 360-ready output
The agents run in the cloud and cannot operate Fusion 360. So:
- **CadQuery stays the generating source** (TEAM.md §6), fully parametric, all key values in `params.py`.
- Every release exports **STEP** (imports cleanly into Fusion 360) plus **STL and 3MF** for Bambu Studio.
- Every enclosure includes a short **"Fusion 360 strategy"** section in its design notes: the
  parameter table (names/values mirroring `params.py`), body/component split, and which features
  Arsany would edit in Fusion — so he can take over a design in Fusion without reverse-engineering it.
- If Arsany edits a design in Fusion, his exported STEP becomes the new reference for that version;
  flag any divergence from `params.py` rather than silently overwriting his change.

## 2. Material strategy

| Material | Primary application |
|---|---|
| **PETG** | **Default** — electronics enclosures, brackets, mounts, indoor functional products |
| **ASA** | Outdoor housings, UV exposure, weather-resistant products |
| **TPU** | Flexible feet, grips, bumpers, vibration dampers, cable protection |

- Stock to start: black, grey and white PETG.
- Recommend ASA or TPU only when their properties give a meaningful benefit — state the reason.
- PLA is never the default for parts exposed to heat or mechanical stress.
- ASA: note ventilation and safe operating conditions (enclosed P1S, ventilated room, no unattended
  long runs for a beginner). TPU: note that it may need direct feeding rather than the AMS.

## 3. Design and printing standards

Starting print settings:
- Layer height 0.16–0.20 mm · wall loops 4–5 · infill 20–35 % by load · 0.4 mm nozzle.
- Minimise supports; orient for mechanical strength (load paths along layers, not across them).
- Calibrate tolerances with test prints (keep a tolerance test coupon in the CAD library).

Starting clearances (put them in `params.py`, never hard-code):
- Sliding fits 0.2–0.4 mm.
- Screw holes sized for the actual fastener and measured printer tolerance.
- Snap fits designed and tested for the specific material.

These are starting values, not guarantees — update them from measured test prints and record the
result in `team/learnings/mechanical.md`.

Design for: mechanical strength, accurate dimensions, good surface quality, easy assembly,
replaceable components, minimal material waste, repeatable production, reasonable print time.
Keep each product inside the P1S volume where practical; split into modular parts only when necessary.

## 4. Industrial design and appearance

Target a **premium functional consumer-electronics** aesthetic (references: Apple, Bang & Olufsen,
professional industrial equipment).
- Minimalist and modern; matte black, grey and neutral colours.
- Clean edges, controlled proportions, consistent radii.
- Discreet branding (subtle Nilwerk mark).
- Hidden or minimal fasteners; integrated cable management; clean connector openings.
- No unnecessary decorative elements.
- Avoid the obvious hobbyist 3D-print look: choose geometry and print orientation that hide layer
  lines and support marks on visible faces.

## 5. Finishing workflow

Prioritise a good result straight off the printer. Only when necessary:
1. Remove supports. 2. Deburr and clean edges. 3. Selectively sand visible surfaces.
4. Filler primer. 5. Matte or satin coating. 6. Install brass heat-set inserts. 7. Assemble and inspect.

Avoid unnecessary sanding and painting; minimise manual labour per unit and state the minutes per unit.

## 6. Mechanical assembly standard

Prefer mechanical fastening over permanent glue. Standardise on:
- M2 and M3 screws · brass heat-set threaded inserts · PCB standoffs · mounting bosses
- replaceable covers · cable strain relief · modular mounting interfaces.

Reuse mounting patterns and enclosure components across projects. Products must be easy to open,
repair and maintain.

## 7. Embedded electronics integration

Applies to ESP32/ESP8266, Raspberry Pi, Home Assistant and MQTT devices, sensors and actuators,
displays and control panels, custom PCBs and controllers. Every enclosure must account for:
- exact PCB outline and mounting holes; component heights and clearances
- USB-C, USB-A, Ethernet and power connectors; programming and reset access
- antenna placement and wireless performance (no metal/carbon-filled material or thick walls over the antenna)
- ventilation and thermal management; sensor exposure and environmental needs
- cable routing and strain relief; mounting options and maintenance access.

**Never invent component dimensions.** Use datasheets, manufacturer CAD models, the PCB designer's
DXF/STEP, or measurements from Arsany/Peter. If a critical dimension is missing, raise it in
**Needs Arsany** (or a work order for Peter) before finalising CAD.

## 8. Reusable CAD library

Build and maintain shared parametric parts under `lib/mechanical/` (CadQuery), each with a short README:
PCB mounting patterns · M2/M3 screw + insert configurations · USB-C and USB-A openings · Ethernet
cut-outs · cable entries · ventilation patterns · wall and desk mounts · DIN-rail interface ·
standard enclosure bases and covers · tolerance test coupon.
Reuse library parts where appropriate; improve the library part instead of forking a copy.

## 9. Required deliverables for each product

**A. Product concept** — purpose and intended user; design concept; proposed dimensions.
**B. Mechanical architecture** — enclosure layout; PCB and component positions; mounting and
assembly strategy; connector access; ventilation and thermal considerations.
**C. CAD** — parametric strategy (CadQuery source + Fusion 360 strategy, §1a); dimensioned
specifications; part separation; STL/3MF for printing; STEP.
**D. Manufacturing** — material and nozzle; layer height, walls, infill; orientation and supports;
estimated print time; estimated material use (g). Take time/material from a Bambu Studio slice where
possible and say when a figure is an estimate.
**E. Assembly** — screws and inserts; hardware list; assembly sequence; maintenance instructions.
**F. Cost and business** — filament cost; hardware cost; electricity estimate; labour and finishing
time (at the Nilwerk rate); total unit manufacturing cost; suggested retail price; estimated gross
margin. Show the arithmetic and the assumptions (filament €/kg, kWh price, minutes per unit).
**G. Quality control** — dimensional accuracy; component fit; mechanical strength; thermal
performance; connector accessibility; assembly consistency.

## 10. Production validation

One successful print is never production approval. Process:
1. **Prototype 1** — dimensions and component fit.
2. **Prototype 2** — assembly and mechanical refinement.
3. **Prototype 3** — final material and print settings.
4. **Pilot batch** — 5–10 units.
5. **Quality inspection** and documented production settings (Bambu Studio profile / 3MF saved with the version).

Physical prints are done in-house by Arsany or Peter — write a work order (TEAM.md §12) with the exact
file, profile, material and what to measure.

Identify applicable EU product-safety, electrical, EMC, RoHS and CE requirements where relevant.
**Never claim compliance** without the appropriate assessment and evidence — list it as an open item instead.

## 11. Decision priorities

For every product, in this order:
1. Functional reliability
2. Mechanical strength
3. Electronics compatibility
4. Compatibility with the Bambu Lab P1S
5. Premium appearance
6. Low manufacturing cost
7. Repeatability and scalability

Avoid over-engineering, unnecessary upgrades and complicated finishing.

## Final objective

Turn Nilwerk's embedded electronics projects into original, premium-looking, functional products
that can be manufactured in small batches and sold commercially in Germany and across the EU.
Think beyond the prototype: design for the finished product, the customer experience, the
manufacturing process and business profitability.
