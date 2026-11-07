# Plant Monitor — Requirement Traceability

Owner: Theo (System Architect). One row per requirement or decision: requirement ID -> design element -> code path -> test.
Rows are added when the architect approves a PR. Code is cited by function name (line numbers drift). A test marked
"pending" is in an open PR and is not yet on `main`. Status here is trace only; it is not a test result and not acceptance.

| Requirement / decision | Design element | Code path | Tests | Status / note |
|---|---|---|---|---|
| A-032 (Arsany, 2026-11-06) -> FR-E02 (wetting class), FR-E01 | Model B wetting labels: positives = valve-coincident watering + rain-coincident only; unexplained wetting = ignore mask (onset +-`IGNORE_PAD_TICKS`); sector 5 fully ignored; FR-E02 claims cover wetting + sensor fault only; weak-label percentiles frozen. Mask semantics: ignore ticks are neither positive nor negative, dropped from training loss and from evaluation counts; consumers select `lbl_wetting_pos \| lbl_wetting_neg`. Data card: `ml/data-cards/mendeley-precision-irrigation.md` | `ml/src/labels.py::label_wetting_classes` (constants `EXCLUDED_WETTING_PLANTS`, `IGNORE_PAD_TICKS`, `FR_E02_CLAIM_CLASSES`, `FROZEN_WEAK_LABEL_RULE`); month x sector table: `ml/src/export.py::event_class_table` | `ml/tests/test_event_classes.py` (label rules, explicit pad, sector 5, frozen rule); `ml/tests/test_event_classes_default_pad.py` (default pad = 4; pending, PR #35) | Code on `main`; pad 4 pending PR #35. Open: the acceptance matrix row FR-E02 (`tests/acceptance-matrix.md`) does not yet say that masked ticks are excluded from recall/precision counts; Ines to add. |
