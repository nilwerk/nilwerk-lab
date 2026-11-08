# Playbook: 3D designer

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- Design for the in-house Bambu Lab P1S + AMS only (256 × 256 × 256 mm, 0.4 mm nozzle, FDM); never assume moulding or CNC. *Why:* Arsany decided on in-house small-batch manufacturing. *Source:* standards/3d-manufacturing.md, 2026-11-07.
- PETG only (black/grey/white) on the 0.4 mm nozzle for now; anything needing ASA, TPU, another colour or nozzle → raise it, don't specify it. *Why:* that's the only stock. *Source:* Arsany 2026-11-07, standards §2.
- Never invent a component dimension — datasheet, vendor CAD, PCB export or a measurement, else raise it. *Source:* standards/3d-manufacturing.md §7.
- One good print is not approval: Prototype 1–3, then a 5–10 unit pilot batch. *Source:* standards/3d-manufacturing.md §10.
- Never mount a light sensor where it can't see ambient light (e.g. under the pot). *Why:* earlier concept put the unit underneath the pot with a light sensor. *Source:* learning log 02.
- Never overwrite an older version folder in Drive; export to the next vN. *Source:* project README.
- Make the enclosure functional and practical first, then give it a deliberate touch of design that fits the product and where it lives (Plant Monitor: plant pots, balcony, home); a part that only looks good, or only works and looks like a hobby print, is not done. *Why:* Arsany wants a product that fits its environment, not a bare box. *Source:* Arsany 2026-11-08, PR #44.
- Do the design touch as ONE signature feature, built from the standard: a soft top-edge chamfer or fillet, a leaf-like softened profile line, a nilwerk trace-motif relief (2 to 3 layers deep, >= 0.8 mm wide, and the remaining skin must stay >= 1.2 mm, so a deeper relief needs a thicker part; brand paper #f6f4ef / ink #15181d / green #0f7a5c as inspiration), or a black/grey/white colour split via AMS; keep it parametric behind a flag in `params.py` with tests and a render. *Why:* one considered detail reads as design, many read as decoration (standards §4: no unnecessary decorative elements). *Source:* Arsany 2026-11-08, PR #44.
- Design must never break printability, seal or fit: no new overhangs or supports, walls >= 1.2 mm, relief only on non-sealing faces, verified bay/PCB dimensions unchanged; test it (watertight, same outer size, no overhang) before it goes in. *Why:* a pretty part that leaks, jams or needs supports fails NFR-05 and the 0.4 mm/P1S standard. *Source:* Arsany 2026-11-08, PR #44; standards §3-4.
