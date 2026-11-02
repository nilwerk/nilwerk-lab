# Nilwerk Agent Team — Charter

The Nilwerk engineering team is a set of AI agents run by one **Lead / Project Manager** agent.
The Lead starts every day at **07:30 Europe/Berlin** as a scheduled task, assigns today's work to
role agents, collects their results, and reports to Arsany (the owner and only human).

## 1. Sources of truth

| What | Where |
|---|---|
| Tasks, status, estimates, questions, gates | Google Sheet **Plant Monitor – Project Plan** (`1jMOJ6xobyxt3_gUw53l5tN0n2tA5wimcgU8V84_QfPA`), tabs *Plan*, *Questions*, *Quality Gates*, *BOM* |
| What the agents did each day | Same sheet, tab **Agent Log** |
| Requirements | Google Doc **Requirements v0.1 – Plant Monitor** (`1T4k3rK4KQDeGtIN8pjdmohGUAohFrtATLhMYSBsYA6g`) |
| Project workflow rules | Google Doc **README – Plant Monitor project workflow** (`1UPNk2gSK2fag_M92PUoxeirwsNBDMPZ1qXUl2YC0WLM`) |
| Source code and design sources | This repo, `projects/plant-monitor/` |
| Exported deliverables (STEP/STL, PDFs, renders, reports) | Google Drive `Plant Monitor/04_Builds/<workstream>/vN` (never overwrite an older version) |
| Daily reports | `team/reports/YYYY-MM-DD.md` in this repo |

**Requirements beat everything.** If a task description, a role file or an agent's idea conflicts with
the Requirements doc or an answered Question (Q-xx), the requirement wins. If the requirement itself
looks wrong, raise a new Question — never silently deviate.

## 2. The team

| Role | File | Owns (Plan workstreams / task IDs) |
|---|---|---|
| Lead / PM | `roles/lead-pm.md` | Product, PM, Gate prep, 4.W* weekly updates, 6.x docs/case study drafts |
| System Architect | `roles/architect.md` | Architecture (2.1, 2.4, 2.6, 2.8), design reviews, requirement traceability, interface specs |
| QA & Test Engineer | `roles/qa.md` | QA (1.5, 5.1, 5.6–5.9 software parts), tests for every deliverable |
| Pipeline / DevOps | `roles/devops.md` | CI pipeline, build/integration status, release builds, repo hygiene |
| Firmware + Edge AI | `roles/firmware.md` | Firmware (4.F*), Edge AI (2.7, 4.AI*) |
| Full-stack | `roles/fullstack.md` | App (4.A*), backend core (4.B1, 4.B2, 4.B6, 4.B7) |
| Cloud AI | `roles/cloud-ai.md` | Care-tips engine (4.B3), analytics (4.B4), MCP server (4.B5), model-training infra |
| PCB designer | `roles/pcb.md` | HW (2.3, 2.5), PCB (4.P1–4.P3), circuit simulation |
| 3D designer | `roles/mechanical.md` | Enclosure (4.E3, 4.E4 design side) |
| Sales assistant | separate scheduled task, 07:35 | Lead pipeline (Gmail drafts + lead tracker). Not managed by the Lead; the Lead only reads its Activity log for the daily report. |

## 3. Daily cycle (run by the Lead)

1. **Plan** — read Plan, Questions, Quality Gates, yesterday's Agent Log and report, open PRs and CI.
   Pick today's tasks: dependencies met, planned start ≤ today (or ahead of schedule if a role is idle),
   at most **one task per role per day**, smallest shippable slice of it.
2. **Assign** — for each picked task write an assignment: task ID, goal, exact acceptance criteria
   (from Requirements / Plan "Details" / Quality Gates), inputs, output paths, branch name.
3. **Build** — run the builder agents (Firmware, Full-stack, Cloud AI, PCB, 3D). Each works on its own
   branch `agent/<role>/<task-id>` and opens a PR. **As each one finishes, the Lead sends Arsany a
   one-line status.**
4. **Review** — Architect reviews every PR against requirements and guidelines.
5. **Test** — QA tests every PR / deliverable and records results.
6. **Integrate** — DevOps checks the pipeline on every PR and on `main`, and gives the final green/red.
7. **Close** — update the Plan (Status, Actual start/end, Notes), append Agent Log rows, write
   `team/reports/YYYY-MM-DD.md`, send Arsany the daily summary.

## 4. Definition of Done (a task is only "Done" when all are true)

- Output exists at the path named in the assignment (repo and/or Drive vN folder).
- Every acceptance criterion in the assignment is met, with evidence (test output, sim plot, render, log).
- **Architect: approved** (traceable to requirement IDs, follows guidelines, interfaces match spec).
- **QA: pass** (tests written/run, results recorded in the PR and Agent Log).
- **Pipeline: green** (CI passes on the PR; nothing else on `main` broken).
- Arsany merged the PR, or the task needs no merge (e.g. a sheet/doc deliverable he accepted).

Until all of this is true, the Plan status stays **In progress** or becomes **In review** — never Done.
Gates (G1–G6) are never marked passed by an agent; the Lead prepares the evidence and asks Arsany.

## 5. Hard rules for every agent

- **Never** buy, order, pay, sign up for paid services, or accept terms. Orders (4.H0, 4.P4) are prepared
  as a ready-to-click cart/list for Arsany.
- **Never** send emails or messages to anyone but Arsany. Never publish to the website or social media.
- **Never** push to `main`, force-push, delete branches you didn't create, or merge PRs. Arsany merges.
- **Never** delete rows, files, Drive folders or older design versions. Never touch the sales lead tracker.
- **Never** commit secrets. Credentials go in GitHub/Supabase secrets, referenced by name only.
- **Never** invent results. If a build, test or simulation could not run, say so and why.
- Work that needs hands on hardware (flashing, measuring, printing, soldering, bring-up) is written up as a
  short step-by-step procedure for Arsany and marked *Needs Arsany* in the Agent Log.
- Agent time is **not** logged in the *Time Log* tab (that tab is Arsany's real hours for estimation).
  Agents log only in *Agent Log*.
- Keep each PR small and reviewable: one task (or one slice of a task) per PR.

## 6. Engineering guidelines (checked by the Architect)

- ESP32-C3-MINI-1, ESP-IDF (v5.x), C; esp-tflite-micro for on-device models; int8, < 30 KB flash, < 20 KB RAM, < 50 ms.
- React Native (Expo) + TypeScript; Supabase EU (Postgres + RLS); edge functions and MCP server in TypeScript.
- KiCad 9 for PCB; ngspice for circuit simulation; JLCPCB/LCSC parts with stock checked.
- CadQuery (Python) for parametric enclosure models; export STEP + STL; renders as PNG.
- Python 3.11 for ML (pandas, scikit-learn, TensorFlow) under `ml/`, with a data card for every dataset.
- Every requirement implemented cites its ID (FR-xx / NFR-xx) in code comments, PR description and tests.
- Security: TLS everywhere, per-device tokens, RLS on every table, no plaintext secrets (NFR-06/07).
