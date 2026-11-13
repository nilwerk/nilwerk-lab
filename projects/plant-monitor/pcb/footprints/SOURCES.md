# Footprint sources (4.P2 slice 2)

Pad geometry in these `.kicad_mod` files is used by `gen_pcb.py` through `kmod.py`. Files are unmodified copies, fetched 2026-11-10.

| File | Source | Note |
|---|---|---|
| `ESP32-C3-MINI-1.kicad_mod` | https://github.com/espressif/kicad-libraries (master, `footprints/Espressif.pretty/`) | Espressif footprint "designed according to the Recommended PCB Land Pattern" of the datasheet. I checked it against Fig 11-1 of datasheet v2.2: 48 side pads 0.4 x 0.8, 4 corner pads 0.7 x 0.7, 3 x 3 centre ground pads 1.45 x 1.45 (pad 49), top pad row 5.7 mm below the module end. Licence of this repo not checked. |
| `R_0603`, `C_0603`, `LED_0603`, `LED_0805`, `SOT-23-5`, `SOT-23-6`, `TSSOP-8_4.4x3mm_P0.65mm`, `SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.81mm`, `JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal`, `USB_C_Receptacle_HRO_TYPE-C-31-M-12` | https://gitlab.com/kicad/libraries/kicad-footprints tag 9.0.0 | KiCad official library (CC-BY-SA 4.0 with the library exception). Not compared with the vendor drawings by me (JST, HRO). |

Drawn by hand from a manufacturer drawing (in `gen_pcb.py`): `NW:SW_TS-1187A-B-A-B_5.1x5.1` from the XKB TS-1187A "P.C.B. LAYOUT" (LCSC C318884 datasheet).
Still placeholders (no recommended land pattern found): AHT20 (`U5`), BH1750 (`U6`). `E1` is our own copper.

## Slice 3 (2026-11-12): U5 and U6, from LCSC / JLCEDA footprint data

| File | Part and source | Note |
|---|---|---|
| `AHT20_DFN-6_3x3.kicad_mod` | AHT20, LCSC C2757850 (ASAIR/Aosong). Pad geometry: JLCEDA/EasyEDA Official Library, read through the LCSC/EasyEDA component API (`https://easyeda.com/api/products/C2757850/components?format=json`, package SENSOR-SMD_L3.0-W3.0-P1.00-BR). Datasheet: `https://datasheet.lcsc.com/datasheet/pdf/4041f814f74dc23f80e16d036fbdeb72.pdf` (ASAIR AHT20, 2024-07). | Source of this file: 嘉立创EDA/EasyEDA官方库 (JLCEDA/EasyEDA Official Library), homepage https://lceda.cn/ and https://easyeda.com. Units converted from EasyEDA 10-mil units (0.254 mm). **UNVERIFIED**: datasheet Fig 1 pads 0.55 x 0.4 mm vs 0.8 x 0.5 mm here; pad 1 orientation vs Table 5 not compared. |
| `WSOF-6_BH1750FVI.kicad_mod` | BH1750FVI, LCSC C78960 (ROHM). Pad geometry: same JLCEDA/EasyEDA library via `https://easyeda.com/api/products/C78960/components?format=json`. Datasheet: `https://datasheet.lcsc.com/datasheet/pdf/db8941b530fa436ba7aa948426c637fa.pdf` (ROHM BH1750FVI Rev.D, p. 14 package drawing, note 10 on the central pad). | Same library credit as above. The central pad (EP, pad 7) is not in the file on purpose (datasheet note 10: do not solder, no electrical connection). **UNVERIFIED**: pad end 0.18 mm beyond body vs about 0.275 mm on the ROHM drawing; the ROHM Jisso land pattern was not read. |
