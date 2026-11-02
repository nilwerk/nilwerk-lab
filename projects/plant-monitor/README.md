# Plant Monitor

Nilwerk's sales-demo product, run like a real client project (Prototype M package, 3–30 Nov 2026).

| | |
|---|---|
| Requirements | Google Doc *Requirements v0.1 – Plant Monitor* (`1T4k3rK4KQDeGtIN8pjdmohGUAohFrtATLhMYSBsYA6g`) |
| Plan / status | Google Sheet *Plant Monitor – Project Plan* (`1jMOJ6xobyxt3_gUw53l5tN0n2tA5wimcgU8V84_QfPA`) |
| Exported deliverables | Drive `Plant Monitor/04_Builds/<workstream>/vN` |

| Folder | Content | Owner role |
|---|---|---|
| `firmware/` | ESP-IDF firmware for ESP32-C3 | Firmware + Edge AI |
| `ml/` | Edge-AI datasets (fetch scripts + data cards), training, TFLite export | Firmware + Edge AI |
| `app/` | React Native (Expo) app | Full-stack |
| `cloud/` | Supabase: migrations, edge functions, tips, analytics, MCP server | Full-stack, Cloud AI |
| `pcb/` | KiCad 9 project, `sim/` ngspice simulations | PCB designer |
| `mechanical/` | CadQuery enclosure sources | 3D designer |
| `docs/` | Architecture, interfaces (contracts), ADRs, traceability | Architect |
| `tests/` | Acceptance matrix, results, bench procedures | QA |
