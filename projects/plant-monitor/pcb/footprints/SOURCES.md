# Footprint sources (4.P2 slice 2)

Pad geometry in these `.kicad_mod` files is used by `gen_pcb.py` through `kmod.py`. Files are unmodified copies, fetched 2026-11-10.

| File | Source | Note |
|---|---|---|
| `ESP32-C3-MINI-1.kicad_mod` | https://github.com/espressif/kicad-libraries (master, `footprints/Espressif.pretty/`) | Espressif footprint "designed according to the Recommended PCB Land Pattern" of the datasheet. I checked it against Fig 11-1 of datasheet v2.2: 48 side pads 0.4 x 0.8, 4 corner pads 0.7 x 0.7, 3 x 3 centre ground pads 1.45 x 1.45 (pad 49), top pad row 5.7 mm below the module end. Licence of this repo not checked. |
| `R_0603`, `C_0603`, `LED_0603`, `LED_0805`, `SOT-23-5`, `SOT-23-6`, `TSSOP-8_4.4x3mm_P0.65mm`, `SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.81mm`, `JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal`, `USB_C_Receptacle_HRO_TYPE-C-31-M-12` | https://gitlab.com/kicad/libraries/kicad-footprints tag 9.0.0 | KiCad official library (CC-BY-SA 4.0 with the library exception). Not compared with the vendor drawings by me (JST, HRO). |

Drawn by hand from a manufacturer drawing (in `gen_pcb.py`): `NW:SW_TS-1187A-B-A-B_5.1x5.1` from the XKB TS-1187A "P.C.B. LAYOUT" (LCSC C318884 datasheet).
Still placeholders (no recommended land pattern found): AHT20 (`U5`), BH1750 (`U6`). `E1` is our own copper.
