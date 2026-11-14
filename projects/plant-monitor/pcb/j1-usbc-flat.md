# J1 USB-C: flat / edge-mount (A-087)

Emil (PCB Designer), 2026-11-14. Decision A-087 (Arsany, 2026-11-13): J1 is flat / edge-mount, not upright.
Requirements: NFR-08 (ESD on USB, antenna far from J1, unchanged), NFR-09 (BOM cost, price not re-checked here).

## Result

**No part change is needed.** The BOM part `C165948` (HRO `TYPE-C-31-M-12`) is already a flat, right-angle, edge-mount SMT USB-C receptacle. The board already uses it that way: J1 rotated 90 deg, mouth flush with the right outline edge (`check_layout.py`, "USB-C mouth ... flush with the right outline edge", PASS).

| Item | Value | Source | Status |
|---|---|---|---|
| Part | `C165948`, TYPE-C-31-M-12, Korean Hroparts Elec, USB-C receptacle, 16 position, surface mount | LCSC product API `wmsc.lcsc.com/ftps/wm/product/detail?productCode=C165948`, read 2026-11-14 | read |
| Mounting / gender | "Surface Mount, Right Angle", Female | same LCSC record, parameter list | read |
| Stock | 517645 pcs at LCSC | same record, 2026-11-14 | live read, one source (not the JLC parts library) |
| **Height above PCB seating plane** | **3.26 mm** | HRO drawing, side view, dimension "3.26" (shell top to the seating plane, 0.10 flatness mark at the seating plane) | **read from the drawing**, ambiguity noted below |
| Mouth width x shield width | 8.34 (+0.06/-0.02) mm mouth, 8.64 mm shell | same drawing, front view | read |
| Body length (front to back) | 6.77 mm side view; 6.28 mm plan view | same drawing | read |
| Shield legs below the board | 4 legs, 1.01 mm | same drawing, side view "4-1.01" | read |

Datasheet file: `https://datasheet.lcsc.com/datasheet/pdf/9e56b777c022540fcce7c7f67825f55e.pdf?productCode=C165948` (one-page HRO drawing, 118176 bytes, SHA-256 `6ae33d50ac47820114661138dc4e4659f40fdc5d4f485b46685dfec338da1a9e`, downloaded 2026-11-14, not committed: vendor PDF). The drawing has no text layer (`pdftotext` returns nothing useful), so the numbers were read from the rendered image at 300 dpi. Note: the page has no separate "H" label for the overall height; 3.26 is the only vertical dimension on the side view. A second read by another person (Ines) is the check.

## What this changes for the enclosure (Yara, Theo)

- Enclosure model value is 3.30 mm (ASSUMED in `mechanical/enclosure_v3/params_v3.py`, `H_SRC["J1"]`). The drawing says 3.26 mm: the model is 0.04 mm conservative. Source status can move from ASSUMED to DATASHEET once Ines confirms the reading. Not edited here (Yara's files).
- The "upright male 11.94 +-0.25 mm" figure in `LOCKED_INTERFACE.md` / `params_v3.py` is **not in this drawing**: the drawing is of a female right-angle receptacle and has no 11.94 anywhere. Its source is "the review brief", PDF not read. Suggest it is removed or relabelled as not applicable to C165948, since A-087 is decided as flat.

## Not verified (OPEN, not PASS)

- **Footprint vs drawing: UNVERIFIED.** The placed footprint is the KiCad library `USB_C_Receptacle_HRO_TYPE-C-31-M-12` (`footprints/SOURCES.md`), not compared with the pad and slot dimensions of this drawing (PCB layout: 16 x 0.20 +-0.05 signal pad width, 4 x 0.60 shield slots, 6.40 / 5.78 / 8.65 spacings). `pin_verified=False` stays in `design.py`. (Dry-run A9 stays UNVERIFIED for J1.)
- Pin map from the drawing table matches the `design.py` signal names (A5 CC1, B5 CC2, A6/B6 DP, A7/B7 DN, A8/B8 SBU, A4/B9/A9/B4 VBUS, A1/A12/B1/B12 GND) by eye only; no script check.
- Height 3.26 mm: one reader (Emil). JLC library-part page (Basic/Extended, CPL rotation) not opened.
- Open since earlier: VBUS pad A9 and CC1 routing near J1 (`layout-4P2.md`).
- Lifecycle (active / NRND / EOL) of C165948: the LCSC record has no lifecycle field; **not checked**.
- Alternative `C2765186` (noted in `hardware/bom/bom-draft.csv`) was not looked at; no reason to switch.
