# Playbook: 3D designer

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- Design for the in-house Bambu Lab P1S + AMS only (256 × 256 × 256 mm, 0.4 mm nozzle, FDM); never assume moulding or CNC. *Why:* Arsany decided on in-house small-batch manufacturing. *Source:* standards/3d-manufacturing.md, 2026-11-07.
- PETG by default; ASA for outdoor/UV; TPU only for flexible parts; never PLA for heat or load. *Source:* standards/3d-manufacturing.md §2.
- Never invent a component dimension — datasheet, vendor CAD, PCB export or a measurement, else raise it. *Source:* standards/3d-manufacturing.md §7.
- One good print is not approval: Prototype 1–3, then a 5–10 unit pilot batch. *Source:* standards/3d-manufacturing.md §10.
- Never mount a light sensor where it can't see ambient light (e.g. under the pot). *Why:* earlier concept put the unit underneath the pot with a light sensor. *Source:* learning log 02.
- Never overwrite an older version folder in Drive; export to the next vN. *Source:* project README.
