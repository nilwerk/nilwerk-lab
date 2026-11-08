#!/usr/bin/env python3
"""Rebuild bom-draft.csv from the line definitions below plus LIVE shop data (read-only, nothing is ordered).

    python3 refresh_live.py            # writes bom-draft.csv next to this file

Live sources (no login): LCSC product page (stock, price breaks, sales status) and the public JLCPCB parts
search API (JLC stock, library type base/expand, preferred flag).  Needs outbound HTTPS and `curl`.
Stock and prices change daily: the run time is written into every row (`verified_utc`).
Lines with an empty LCSC part number are never looked up and carry status `unverified`.
"""
from __future__ import annotations

import csv
import datetime
import json
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent

# ref, description, qty, LCSC part, MPN, manufacturer, package, note
LINES = [
    ("U1", "ESP32-C3-MINI-1-N4 module (MCU, Wi-Fi/BLE, antenna)", 1, "C2838502", "ESP32-C3-MINI-1-N4", "ESPRESSIF", "SMD,16.6x13.2mm", "FR-D01, NFR-01"),
    ("U2", "3.3 V LDO, low Iq (XC6220B331MR-G; 8 uA / 1 A per LCSC listing, datasheet not read)", 1, "C86534", "XC6220B331MR-G", "TOREX", "SOT-25", "Basic LDOs checked and rejected for current: XC6206P332MR-G C5446 (200 mA), HT7533-1 C14289 (100 mA), both per LCSC/JLC listing; AMS1117 Iq in mA. ME6211 C82942 is Extended too and Iq ~40 uA (unverified)"),
    ("U3", "LiPo charger TP4056 (R9 programs the charge current)", 1, "C16581", "TP4056-42-ESOP8", "TOP POWER ASIC", "ESOP-8", "alt TP4057 SOT-23-6 C12044 (not checked); no Basic charger exists in the JLC library"),
    ("U4", "Cell protection DW01A", 1, "C351410", "DW01A", "PUOLOP", "SOT-23-6L", "dropped if the cell has a protection module (PCM), see bom-draft.md section 'Variants'; no Basic DW01A exists"),
    ("Q1", "Dual N-MOSFET 8205A for U4 (TSSOP-8)", 1, "C5148694", "8205A", "HXY MOSFET", "TSSOP-8", "FS8205A C32254 sold out; many 8205A listings are SOT-23-6, check footprint; no Basic 8205A exists"),
    ("U5", "AHT20 temp/humidity (I2C)", 1, "C2757850", "AHT20", "Aosong", "SMD", ""),
    ("U6", "BH1750FVI light (I2C)", 1, "C78960", "BH1750FVI-TR", "ROHM", "WSOF-6", ""),
    ("U7", "Soil front end: Schmitt-trigger inverter, RC relaxation oscillator with the probe capacitance, powered from a GPIO (SN74LVC1G14)", 1, "C7835", "SN74LVC1G14DBVR", "Texas Instruments", "SOT-23-5", "NEW 2.5-followup; no Basic Schmitt gate exists; sizing in soil_frontend.py"),
    ("J1", "USB-C receptacle 16-pin (power + USB Serial/JTAG data)", 1, "C165948", "TYPE-C-31-M-12", "Korean Hroparts Elec", "SMD", "cheaper alt C2765186 (footprint check); no Basic USB-C found"),
    ("D1", "USB ESD array USBLC6-2SC6 (NFR-08)", 1, "C7519", "USBLC6-2SC6", "ST", "SOT-23-6L", "no Basic ESD array found"),
    ("J2", "Battery connector JST PH 2-pin SMD (board side)", 1, "C295747", "S2B-PH-SM4-TB(LF)(SN)", "JST", "SMD,P=2mm,Surface Mount,Right Angle", "clone alt C54582899 XY-S2B-PH-SM4-TB (cheaper, mechanical equivalence unverified); through-hole C173752 breaks single-side SMT"),
    ("B1", "LiPo cell EEMB LP603449-PCM (Amazon.de ASIN B08FD39Y5R): 3.7 V, 1100 mAh typ / 1000 mAh MIN, built-in PCM (OC/OD/over-current/short), JST plug. Order 5 = 3 builds + 2 spare (A-034)", 1, "", "LP603449-PCM", "EEMB", "pouch, 51 x 34.5 x 6.3 mm (listing)", "DECIDED by Arsany 2026-11-08 (A-034). Price, seller, delivery, plug pitch (PH 2.0 assumed) and wire polarity UNVERIFIED (cell-decision-A034.md). CHECK PLUG POLARITY with a meter before first connection. 2-wire, no NTC. Not assembled by JLC; bought by Arsany, never by the agent"),
    ("B2", "A-034 candidate: Jauch LP503030JU+PCM+2IC+NTC+Mol. 78172-3 50MM, 450 mAh typ / 430 mAh MIN, PCM with 2nd IC, 10k NTC, Molex 78172-3 plug (3 circuits). DigiKey 3027-LP503030JU+PCM+2IC+NTC+Mol.78172-350MM-ND", 1, "", "LP503030JU+PCM+2IC+NTC+Mol. 78172-3 50MM", "Jauch Quartz", "pouch, 5.2 x 30 x 30 mm", "FAILS NFR-01 (430 mAh min, typical 1.9 months vs 3). DigiKey read 2026-11-07: EUR 8.47 at 1, 6.924 at 10, 6.1252 at 50 (excl. VAT), stock 85, ships ~6 days from Jauch, MOQ 1; unverified except those page values. Needs a 3-pin 1.2 mm Pico-EZmate header on the board instead of J2 (see cell-decision-A034.md)"),
    ("B3", "DigiKey alternative: Jauch LP603443JU+PCM+2 WIRES 70MM, 900 mAh typ / 850 mAh MIN, PCM, bare wires (no connector, no NTC). DigiKey 1908-LP603443JU+PCM+2WIRES70MM-ND", 1, "", "LP603443JU+PCM+2 WIRES 70MM", "Jauch Quartz", "pouch, 6.5 x 34.5 x 45 mm (DigiKey)", "PASSES NFR-01 (typical 3.8 months). 0.2 mm above the 6.3 mm minimum bay (input to Yara, enclosure v3 not built) and zero width margin; IEC 62133 NO on the Jauch datasheet (Rev 1.2); no NTC, no 2nd IC. DigiKey digikey.com read 2026-11-07: USD 11.11 at 1, 9.24 at 10, 8.1244 at 50, stock 516, lead time listed 28 weeks (inconsistent with stock); unverified except those page values. Wires need a connector or pigtail"),
    ("J2b", "ALTERNATIVE to J2 for the Jauch A-034 cell: Molex Pico-EZmate header 78171-0003, 3 circuits, 1.2 mm, SMD (mating with the cell plug Molex 78172-3 = 78172-0003 receptacle is UNVERIFIED, Molex datasheet not read)", 1, "C564183", "781710003", "MOLEX", "SMD,1.2mm", "only if B2 is chosen; replaces J2 (JST PH); third pin = NTC to TP4056 TEMP"),
    ("SW1,SW2,SW3", "Tact switch BOOT, RESET, pinhole factory reset", 3, "C318884", "TS-1187A-B-A-B", "XKB Connection", "SMD-4P,5.1x5.1mm", ""),
    ("D2", "LED red (CHRG)", 1, "C2286", "KT-0603R", "Hubei KENTO Elec", "0603", ""),
    ("D3", "LED green (STDBY/status), 0805", 1, "C2297", "KT-0805G", "Hubei KENTO Elec", "0805", "CHANGED: was KT-0603G C12624 (Extended); 0805 green is a Basic part"),
    ("R1,R2", "5.1k 0603 USB-C CC", 2, "C23186", "0603WAF5101T5E", "UNI-ROYAL", "0603", ""),
    ("R3-R5", "10k 0603 pull-ups (EN R3, GPIO8 strap R4, GPIO9 strap R5)", 3, "C25804", "0603WAF1002T5E", "UNI-ROYAL", "0603", "R6 (Q2 gate pull-down) removed by A-045 Option A; EN RC = R3 x C12 = 10 ms"),
    ("R16", "10k 0603 GPIO2 strap pull-up (Espressif datasheet v2.2 s.4.1)", 1, "C25804", "0603WAF1002T5E", "UNI-ROYAL", "0603", "ADDED by 4.P1 (Theo C4); same part as R3-R5"),
    ("R7,R8", "1M 0603 battery divider (2 MOhm total)", 2, "C22935", "0603WAF1004T5E", "UNI-ROYAL", "0603", ""),
    ("R9", "2.4k 0603 TP4056 PROG: I = 1100/R = 458 mA (0.46C of 1000 mAh)", 1, "C22940", "0603WAF2401T5E", "UNI-ROYAL", "0603", "CHANGED: was 1.2k (917 mA). See bom-draft.md section 'R9'"),
    ("R10,R11", "1k 0603 LED series", 2, "C21190", "0603WAF1001T5E", "UNI-ROYAL", "0603", ""),
    ("R12", "470k 0603 soil oscillator timing resistor (U7 output to input)", 1, "C23178", "0603WAF4703T5E", "UNI-ROYAL", "0603", "NEW; value from soil_frontend.py, to be tuned on the real stake in 4.P1/5.x"),
    ("R13,R14", "4.7k 0603 I2C pull-ups (SDA, SCL)", 2, "C23162", "0603WAF4701T5E", "UNI-ROYAL", "0603", "ADDED by 4.P1; BOM draft had no I2C pull-ups"),
    ("R15", "1k 0603 DW01A CS resistor (U4 CS to P-)", 1, "C21190", "0603WAF1001T5E", "UNI-ROYAL", "0603", "ADDED by 4.P1; same part as R10,R11. Goes away together with U4/Q1/C9 if the second protection is deleted (open point 4)"),
    ("C1-C4", "10 uF 0603", 4, "C19702", "CL10A106KP8NNNC", "Samsung Electro-Mechanics", "0603", ""),
    ("C5-C11", "100 nF 0603 (incl. U7 decoupling)", 7, "C14663", "CC0603KRX7R9BB104", "YAGEO", "0603", "qty 6 -> 7 (U7). LCSC stock was 0 at read time while JLC stock is large: re-check; Samsung CL10B104KB8NNNC C1591 is Extended"),
    ("C12,C13", "1 uF 0603", 2, "C15849", "CL10A105KB8NNNC", "Samsung Electro-Mechanics", "0603", ""),
    ("C14", "22 uF 0603 (LDO out / Wi-Fi burst)", 1, "C59461", "CL10A226MQ8NRNC", "Samsung Electro-Mechanics", "0603", ""),
]

ALTERNATIVES = {"B2", "B3", "J2b"}   # not in the sums: superseded candidates (B1 is the decided cell, A-034; it has no price so it is outside the sums as `unverified`)

FIELDS = ["ref", "description", "qty_per_board", "lcsc_pn", "mpn", "manufacturer", "package", "lcsc_stock",
          "jlc_stock", "jlc_library_type", "jlc_preferred", "lifecycle_lcsc", "lcsc_pack_qty",
          "price_breaks_usd(qty:price)", "status", "alternative", "verified_utc", "note"]


def curl(args):
    return subprocess.run(["curl", "-sS", "-m", "40", "-L"] + args, capture_output=True, text=True).stdout


def lcsc_api(c):
    """Fallback when the product page HTML does not parse: the JSON API behind it (same fields)."""
    r = (json.loads(curl([f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={c}"])).get("result") or {})
    if not r.get("productPriceList"):
        return None
    return dict(stock=int(r.get("stockNumber") or 0), cycle=r.get("productCycle") or "",
                pack=str(r.get("minPacketNumber") or ""), breaks=[(p["ladder"], p["usdPrice"]) for p in r["productPriceList"]])


def lcsc(c):
    return lcsc_html(c) or lcsc_api(c)


def lcsc_html(c):
    h = curl([f"https://www.lcsc.com/product-detail/{c}.html"])
    i = h.find(f'"productCode":"{c}"')
    if i < 0:
        return None
    seg = h[max(0, i - 6000): i + 20000]
    g = lambda p: (re.search(p, seg) or [None, None])[1]
    pl = re.search(r'"productPriceList":(\[[^\]]*\])', h[i:i + 20000])
    breaks = [(p["ladder"], p["usdPrice"]) for p in json.loads(pl.group(1))] if pl else []
    return dict(stock=int(g(r'"stockNumber":(\d+)') or 0), cycle=g(r'"productCycle":"([^"]*)"'),
                pack=g(r'"minPacketNumber":(\d+)'), breaks=breaks)


def jlc(c):
    body = json.dumps({"keyword": c, "currentPage": 1, "pageSize": 5, "searchSource": "search"})
    out = curl(["-X", "POST", "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList",
                "-H", "Content-Type: application/json", "-d", body])
    for x in (json.loads(out)["data"]["componentPageInfo"]["list"] or []):
        if x["componentCode"] == c:
            return x["stockCount"], x["componentLibraryType"], x["preferredComponentFlag"]
    return None, None, None


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    with open(HERE / "bom-draft.csv", "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for ref, desc, qty, c, mpn, mfr, pkg, note in LINES:
            row = dict(ref=ref, description=desc, qty_per_board=qty, lcsc_pn=c, mpn=mpn, manufacturer=mfr,
                       package=pkg, note=note, status="unverified", verified_utc="", alternative="yes" if ref in ALTERNATIVES else "")
            if c:
                L = lcsc(c)
                js, jt, jp = jlc(c)
                if L and L["breaks"]:
                    row.update({"lcsc_stock": L["stock"], "lifecycle_lcsc": L["cycle"], "lcsc_pack_qty": L["pack"] or "",
                                "price_breaks_usd(qty:price)": " ".join(f"{q}:{p}" for q, p in L["breaks"]),
                                "jlc_stock": js, "jlc_library_type": jt, "jlc_preferred": jp,
                                "status": "verified-live", "verified_utc": now})
            w.writerow(row)
    print("wrote", HERE / "bom-draft.csv", now)


if __name__ == "__main__":
    main()
