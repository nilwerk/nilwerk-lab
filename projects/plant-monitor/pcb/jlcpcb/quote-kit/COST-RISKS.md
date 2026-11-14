# Cost drivers and risks from `../bom-lcsc.csv` (QUOTE ONLY)

Data: LCSC product API and JLC parts search, **read 2026-11-09 20:17Z (5 days old, not re-read today)**. Everything below is **UNVERIFIED for today**; re-read it on the JLC parts page during the quote.

| Item | Finding in bom-lcsc.csv | Risk / label |
|---|---|---|
| Extended parts | 11 unique: D1 C7519, J1 C165948, J2 C295747, Q1 C5148694, U1 C2838502, U2 C86534, U3 C16581, U4 C351410, U5 C2757850, U6 C78960, U7 C7835 | Each Extended part carries a JLC loading fee. Fee amount **UNVERIFIED** (not read). Biggest price driver together with U1 |
| Biggest parts cost | U1 ESP32-C3-MINI-1-N4 3.07 USD at 3 pcs (LCSC catalogue); U6 0.93; U5 0.81; U2 0.48 | Catalogue price only, **UNVERIFIED**. Total parts 6.56 USD per board at 3 or 6 boards, 4.01 at 1000 (no JLC fees) |
| Short LCSC stock | C15849 (1 uF, 2 per board) and C14663 (100 nF, 7 per board): **LCSC stock 0**, JLC stock 12,621,815 and 33,003,840, both Basic | JLC PCBA draws on JLC stock, so likely fine. **UNVERIFIED**: if the JLC page shows a shortage, write it down |
| Low JLC stock | J2 C295747 stock 3,295 (JLC 3,297); U1 12,312; D1 28,475 | Still far above 6-10 boards. Re-check on the page |
| Stock for all lines | all 25 LCSC numbers had stock at JLC on 2026-11-09 | **UNVERIFIED** today |
| Not on JLC | B1 LiPo cell (no LCSC number; Amazon.de ASIN B08FD39Y5R; price UNVERIFIED, A-034); E1 soil probe (bare copper, no part, not in BOM/CPL) | Arsany buys B1; E1 costs nothing extra but its size depends on Q5 |
| Placeholder footprints | U5 AHT20 DFN-6, U6 BH1750 WSOF-6 are Extended parts on placeholder pads | If the real footprint differs, rework before any order. Price unaffected |
| Price breaks | 37 line-quantity pairs use the first LCSC break (README A7) | Part costs at 5-10 boards may be a little off. **UNVERIFIED** |
| J1 | C165948 USB-C 3.26 mm datasheet height, **ASSUMED** flat, edge-mount (A-087) | Orientation/overhang unverified in JLC's CPL |
| SW1-3 | all one part C318884, Basic | 1 unique part, 3 placements: no extra fee |
