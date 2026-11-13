# Role map — which skills and guidelines each agent reads

Online references are in `skills/*.md`. Ready-to-run third-party skills are in `skills/vendor/` (read `skills/vendor/README.md` first for the usage rules).

Every role agent reads, before a task: its role file (`team/roles/<role>.md`), its playbook (`team/learnings/<role>.md`), then the rows below.

| Role | Skills (online) | Guidelines (repo) |
|---|---|---|
| Theo · Architect | `skills/architecture.md` | `guidelines/prototype/` (all), `guidelines/by-role/architect.md` |
| Ines · QA | `skills/pipeline-qa.md`, `skills/software.md` (test parts) | `guidelines/prototype/testing.md`, `guidelines/by-role/qa.md` |
| Kai · Pipeline | `skills/pipeline-qa.md` | `guidelines/prototype/pipeline.md`, `guidelines/by-role/devops.md` |
| Mira · Firmware + Edge AI | `skills/embedded.md` | `guidelines/prototype/firmware-edge-ai.md`, `guidelines/by-role/firmware.md` |
| Leo · Full-stack | `skills/software.md` | `guidelines/prototype/app-cloud.md`, `guidelines/by-role/fullstack.md` |
| Sana · Cloud AI | `skills/software.md` (Supabase, Deno, MCP, Python ML) | `guidelines/prototype/app-cloud.md`, `guidelines/by-role/cloud-ai.md` |
| Emil · PCB | `skills/pcb-cad.md` | `guidelines/prototype/pcb.md`, `guidelines/by-role/pcb.md` |
| Yara · 3D | `skills/pcb-cad.md` (CAD and print parts) | `guidelines/prototype/enclosure.md`, `guidelines/by-role/mechanical.md` |
| Poppy · PR & Social | — | `guidelines/by-role/pr-social.md` (facts and claim sources) |
| Nora · Lead | all (read) | `guidelines/prototype/`, `team/TEAM.md` |

## Vendored skills per role (`skills/vendor/<name>/SKILL.md`)
| Role | Use these | For |
|---|---|---|
| Emil · PCB | `kicad`, `kicad-tools`, `spice`, `emc`, `datasheets`, `bom`, `lcsc`, `jlcpcb` | schematic/PCB/Gerber analysis, ERC/DRC/DFM, simulation, EMC pre-check, datasheet extraction, BOM and JLCPCB assembly feasibility |
| Yara · 3D | `cadquery`, `print-prep`, `structural-analysis` | parametric source, mesh and orientation checks, strength estimates for PETG |
| Mira · Firmware + Edge AI | `datasheets`, `new-component` (adapt to ESP-IDF layout), `agents-reference/firmware.instructions.md` (ideas only) | pin and limit extraction, component skeletons |
| Theo · Architect | `kicad`, `datasheets`, `emc`, `spice` | review evidence (read-only use) |
| Ines · QA | `kicad`, `spice`, `print-prep`, `cadquery/scripts/inspect_model.py` | independent re-runs of design checks |
| Kai · Pipeline | `kicad`, `kicad-tools` | possible CI checks (to be proven) |
| Nora · Lead | `bom`, `jlcpcb`, `lcsc` | ready-to-click order lists for Arsany (never ordered by agents) |
| Leo, Sana, Poppy | none | |

## Reference projects (`skills/references/old-projects.md`)
| Role | Read | For |
|---|---|---|
| Yara · 3D | `orbit-case`, `Soil Monitor case` (Drive links in the file) | CadQuery fit-check pipeline, probe guide channel, honest limits |
| Emil · PCB | `v4_c6_lipo` (Drive link in the file) | charger power path, local footprints, JLCPCB BOM/CPL package, via-in-pad option, validation record |
| Theo · Architect, Ines · QA | the same file, read-only | to compare claims against earlier results |
