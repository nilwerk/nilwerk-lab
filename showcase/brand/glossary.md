# Plain-language glossary (for posts aimed at non-technical readers)

One line each. Use these wordings in the plain layer of a post; link or repeat the line the first time a term appears. Draft by Poppy; Theo checks the technical accuracy.

| Term | In plain words |
|---|---|
| AI agent | A piece of software that does one job on its own (plan, design, test, review). At Nilwerk each agent has a role, and humans lead and review the work. |
| BOM (bill of materials) | The shopping list of every part on a board, with the exact part numbers. |
| PCB | The green circuit board that connects all the small electronic parts. |
| Schematic | The wiring plan of the circuit, drawn before the board layout. |
| ERC | An automatic check of the schematic for wiring mistakes, like a spell-checker for circuits. |
| Prototype | An early working version we build to learn from, not a finished product for sale. |
| R9 | The name of one small resistor on our board. It decides how strongly the battery is charged. |
| Resistor | A tiny part that limits how much electric current flows. |
| TP4056 | The small chip that charges the battery. |
| mAh / 1000 mAh cell | A measure of battery size. A 1000 mAh cell can deliver 1 A for about one hour. |
| 0.5C / 0.9C | Charging speed relative to battery size. 1C empties or fills the battery in about one hour; 0.5C is gentler (about two hours). |
| Datasheet | The manufacturer's official specification sheet for a part. |
| Tolerance (+15 %) | How far a real part may differ from its stated value. We plan for the worst case. |
| Calculated / simulated / measured | Calculated: worked out with a formula. Simulated: run in a computer model. Measured: checked on real hardware. Only "measured" proves it works in the real world. |
| Bench test | A test of real hardware on a workbench with measuring instruments. |
| Backend | The part of the system that runs on a server and stores the data, behind the app. |
| Database | An organised store for the data, such as sensor readings. |
| Schema | The blueprint of a database: which tables exist and what they hold. |
| RLS (row-level security) | A rule inside the database that lets every user see and change only their own rows of data. |
| PostgreSQL / Supabase | PostgreSQL is a widely used open-source database. Supabase is a hosted service built on it. |
| Stubbed | Replaced by a simple stand-in while testing, because the real service is not connected yet. |
| Test run / test | A small program that checks that something works, and fails loudly if it does not. |
| Mutation test | A check of our tests: we deliberately break the code a little and see whether a test notices. If none does, the tests were too weak. |
| Retention | How long data is kept: here raw readings 3 months, hourly summaries 12 months. |
| Pull request (PR) | A proposed change that others review before it becomes part of the project. |
| Pipeline / CI | The automatic checks that run on every change; "green" means all passed. |
| Edge AI | A small AI model that runs on the device itself, not in the cloud. |
| BLE | Bluetooth Low Energy, the short-range wireless link the app uses to set up the device. |
| Enclosure | The housing around the electronics. |
| Sprint | A one-week work block with a goal, reviewed on Friday. |
