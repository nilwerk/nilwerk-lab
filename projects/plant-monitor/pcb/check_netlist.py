#!/usr/bin/env python3
"""Netlist sanity + BOM consistency check (stands in for ERC where kicad-cli is not available).  Run: python3 check_netlist.py
Independent of the generator: it parses plant-monitor.kicad_sch with its own S-expression reader, rebuilds nets from label
positions at pin ends, and compares with design.py, hardware/bom/bom-draft.csv and the sleep budget.  Exit 1 on any FAIL."""
from __future__ import annotations
import csv, math, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
BOM_DRAFT = os.path.join(HERE, "..", "hardware", "bom", "bom-draft.csv")
FAILS: list[str] = []


def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)


# ---------------- minimal S-expression parser ----------------
def parse(text):
    tok = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+', text)
    pos = 0
    def rd():
        nonlocal pos
        t = tok[pos]; pos += 1
        if t == "(":
            lst = []
            while tok[pos] != ")":
                lst.append(rd())
            pos += 1
            return lst
        return t[1:-1] if t.startswith('"') else t
    return rd()


def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def schematic_nets(path):
    root = parse(open(path).read())
    libs = {}
    for s in find(find(root, "lib_symbols")[0], "symbol"):
        pins = {}
        for sub in find(s, "symbol"):
            for pn in find(sub, "pin"):
                at = find(pn, "at")[0]; num = find(pn, "number")[0][1]
                pins[num] = (float(at[1]), float(at[2]))
        libs[s[1]] = pins
    pin_pts, refs = {}, {}
    for s in find(root, "symbol"):
        lid = find(s, "lib_id")[0][1]; at = find(s, "at")[0]
        ref = [p[2] for p in find(s, "property") if p[1] == "Reference"][0]
        refs[ref] = {p[1]: p[2] for p in find(s, "property")}
        for pn in find(s, "pin"):
            x, y = libs[lid][pn[1]]
            pin_pts[(ref, pn[1])] = (round(float(at[1]) + x, 2), round(float(at[2]) - y, 2))
    labels = [(l[1], tuple(round(float(v), 2) for v in find(l, "at")[0][1:3])) for l in find(root, "label")]
    ncs = {tuple(round(float(v), 2) for v in find(n, "at")[0][1:3]) for n in find(root, "no_connect")}
    by_pt = defaultdict(set)
    for n, pt in labels:
        by_pt[pt].add(n)
    nets = defaultdict(list); unconnected = []; nc_pins = []
    for key, pt in pin_pts.items():
        names = by_pt.get(pt, set())
        if len(names) > 1:
            FAILS.append(f"two labels on pin {key}: {names}")
        if names:
            nets[next(iter(names))].append(key)
        elif pt in ncs:
            nc_pins.append(key)
        else:
            unconnected.append(key)
    return nets, nc_pins, unconnected, refs, pin_pts, labels, len(find(root, "symbol"))


def expand(ref):
    out = []
    for part in ref.split(","):
        m = re.fullmatch(r"([A-Z]+)(\d+)-([A-Z]+)?(\d+)", part)
        if m:
            out += [f"{m[1]}{i}" for i in range(int(m[2]), int(m[4]) + 1)]
        else:
            out.append(part)
    return out


# ---------------- 1 schematic vs model ----------------
nets, nc_pins, unconn, refs, pin_pts, labels, nsym = schematic_nets(os.path.join(HERE, "plant-monitor.kicad_sch"))
model_nets = defaultdict(list); model_nc = []
for p in D.PARTS:
    for num, name, net, side in p.pins:
        (model_nc if net == "NC" else model_nets[net]).append((p.ref, num))
check(nsym == len(D.PARTS), f"symbols in sheet = parts in model ({nsym})")
check(not unconn, f"no unconnected pin without a no-connect flag ({len(unconn)}) {unconn[:5]}")
check({k: sorted(v) for k, v in nets.items()} == {k: sorted(v) for k, v in model_nets.items()},
      f"nets rebuilt from the .kicad_sch labels equal the model ({len(nets)} nets)")
check(sorted(nc_pins) == sorted(model_nc), f"no-connect pins match the model ({len(nc_pins)})")
single = {n: v for n, v in nets.items() if len(v) < 2}
check(not single, f"every net has >= 2 pins (dangling labels: {sorted(single)})")
pts = defaultdict(list)
for k, pt in pin_pts.items():
    pts[pt].append(k)
check(all(len(v) == 1 for v in pts.values()), "no two pin ends share a coordinate (no accidental connection)")
labpt = defaultdict(set)
for n, pt in labels:
    labpt[pt].add(n)
check(all(len(v) == 1 for v in labpt.values()), "no point carries two different labels")
check(len(set(p.ref for p in D.PARTS)) == len(D.PARTS), "reference designators unique")
check({"GND", "3V3", "VBAT", "VBUS", "CELL_NEG"} <= set(nets), "power nets present: GND 3V3 VBAT VBUS CELL_NEG")

# ---------------- 2 every part: LCSC + footprint ----------------
for p in D.PARTS:
    if p.in_bom:
        check(bool(p.lcsc and re.fullmatch(r"C\d+", p.lcsc)), f"{p.ref} LCSC number {p.lcsc}")
        check(bool(p.footprint), f"{p.ref} footprint {p.footprint}")
    else:
        check(bool(p.footprint), f"{p.ref} footprint {p.footprint} (no BOM line: board copper)")

# ---------------- 3 BOM consistency with hardware/bom/bom-draft.csv ----------------
draft = {}
for row in csv.DictReader(open(BOM_DRAFT)):
    if row["alternative"].strip().lower() == "yes" or row["ref"].startswith(("B", "J2b")):
        continue
    for r in expand(row["ref"]):
        draft[r] = (row["lcsc_pn"], int(row["qty_per_board"]) / len(expand(row["ref"])))
mine = {p.ref: p.lcsc for p in D.PARTS if p.in_bom}
# 2026-11-08 sync: hardware/bom/bom-draft.csv now carries Q2 removed, R3-R5 qty 3, R13-R16 added: no declared differences left.
ADDED = {}
REMOVED = {}
for r, (lcsc, _) in sorted(draft.items()):
    if r in REMOVED:
        check(r not in mine, f"BOM draft {r} {lcsc} removed from the schematic: {REMOVED[r]}")
        continue
    check(r in mine and mine[r] == lcsc, f"BOM draft {r} {lcsc} = schematic {mine.get(r)}")
extra = sorted(set(mine) - set(draft))
check(set(extra) == set(ADDED), f"schematic parts not in BOM draft are exactly the declared additions (none) {ADDED}: {extra}")
cnt = defaultdict(int)
for p in D.PARTS:
    if p.in_bom:
        cnt[p.lcsc] += 1
# group-level quantity check (shared LCSC numbers: 1k, 10k, 1uF, 100nF counted across BOM lines)
want = defaultdict(int)
for row in csv.DictReader(open(BOM_DRAFT)):
    if row["alternative"].strip().lower() != "yes" and row["lcsc_pn"]:   # B1 (cell) has no LCSC line
        want[row["lcsc_pn"]] += int(row["qty_per_board"])
for l, n in sorted(want.items()):
    check(cnt.get(l, 0) == n, f"qty of {l}: schematic {cnt.get(l, 0)} = BOM draft (+declared additions) {n}")
bom_csv = {}
for row in csv.DictReader(open(os.path.join(HERE, "bom.csv"))):
    for r in row["Designator"].split(","):
        bom_csv[r] = row["LCSC"]
check(bom_csv == mine, "pcb/bom.csv equals the schematic (regenerate with gen_schematic.py if not)")

# ---------------- 4 R9 / charger ----------------
r9 = next(p for p in D.PARTS if p.ref == "R9")
i_ma = 1100.0 / (D.R9_OHM / 1000.0)
check(i_ma / D.CELL_MIN_MAH <= 0.5 and i_ma * 1.15 <= D.CELL_MAX_CHARGE_MA,
      f"R9 {D.R9_OHM} ohm -> {i_ma:.0f} mA = {i_ma/D.CELL_MIN_MAH:.2f}C of {D.CELL_MIN_MAH} mAh (<= 0.5C); +15 % tolerance {i_ma*1.15:.0f} mA <= cell max charge {D.CELL_MAX_CHARGE_MA} mA")
check(r9.value == "2.4k" and r9.lcsc == "C22940", "R9 = 2.4k C22940 (EEMB LP603449-PCM, A-034 decided; parametrised in design.py)")
check(i_ma + 10 <= 500, f"VBUS draw {i_ma:.0f} mA charge + about 10 mA (one LED 3 mA, TP4056 supply) <= USB 2.0 500 mA; the board load comes from the cell (A-046 Option A: no power path), +15 % tolerance {i_ma*1.15:.0f} mA would exceed 500 mA (open point 3)")
check(not any(p.ref in ("Q2", "R6") for p in D.PARTS) and not any("BAT_SENS_EN" in [x[2] for x in p.pins] for p in D.PARTS),
      "A-045 Option A: no Q2, no R6, no BAT_SENS_EN net")
r7, r8 = (next(p for p in D.PARTS if p.ref == r) for r in ("R7", "R8"))
check({x[2] for x in r7.pins} == {"VBAT", "BAT_SENS"} and {x[2] for x in r8.pins} == {"BAT_SENS", "GND"} and r7.value == r8.value == "1M",
      "A-045: battery divider R7 (VBAT-BAT_SENS) + R8 (BAT_SENS-GND), 1M + 1M permanent: BAT_SENS max 2.1 V at 4.2 V")
tp = next(p for p in D.PARTS if p.ref == "U3")
check(any(x[1] == "TEMP" and x[2] == "GND" for x in tp.pins), "TP4056 TEMP tied to GND (the decided cell has no NTC)")

# ---------------- 5 strapping / pin sanity ----------------
u1 = {n: (nm, net) for n, nm, net, s in next(p for p in D.PARTS if p.ref == "U1").pins}
check(u1["23"][1] == "BOOT_N" and any(p.ref == "R5" and ("3V3" in [x[2] for x in p.pins]) and ("BOOT_N" in [x[2] for x in p.pins]) for p in D.PARTS),
      "GPIO9 (strap) has pull-up R5 and BOOT switch to GND")
check(u1["22"][1] == "GPIO8_STRAP" and any(p.ref == "R4" for p in D.PARTS), "GPIO8 (strap) pulled high by R4")
check(u1["5"][1] == "GPIO2_STRAP" and any(p.ref == "R16" and p.value == "10k" and {x[2] for x in p.pins} == {"3V3", "GPIO2_STRAP"} for p in D.PARTS),
      "GPIO2 (strap) pulled up to 3V3 by R16 10k (Espressif datasheet v2.2 s.4.1)")
u5 = {n: net for n, nm, net, s in next(p for p in D.PARTS if p.ref == "U5").pins}
check(u5 == {"1": "NC", "2": "3V3", "3": "I2C_SCL", "4": "I2C_SDA", "5": "GND", "6": "NC"}, "U5 AHT20 6-pin DFN map equals datasheet Table 5 (NC,VDD,SCL,SDA,GND,NC)")
gpio_used = [net for n, (nm, net) in u1.items() if nm.startswith("IO") and net != "NC"]
check(len(gpio_used) == len(set(gpio_used)), f"each GPIO net used once: {len(gpio_used)}")
check(all(n in (0, 1, 2, 3, 4, 5) for n in [int(re.match(r'IO(\d+)', nm)[1]) for n, (nm, net) in u1.items() if net in ("SOIL_PWR", "FACTORY_RST_N", "BAT_SENS")]),
      "pins that must hold/wake in deep sleep (IO0..IO5 = RTC GPIO): BAT_SENS, SOIL_PWR, FACTORY_RST_N")

# ---------------- 6 sleep budget vs NFR-12 ----------------
SLEEP = D_SLEEP = [  # (path, typ uA, worst uA, source/status)
    ("ESP32-C3 deep sleep, RTC timer + RTC memory", 5.0, 10.0, "datasheet read (series v2.4 Table 5-9); module flash leakage worst = assumption"),
    ("XC6220B331 LDO quiescent (U2)", 8.0, 10.0, "XC6220 datasheet: 8 uA typ (PS mode), 18 uA max; power budget assumed 2 uA typ: 6 uA worse"),
    ("TP4056 BAT drain, USB unplugged (U3)", 3.0, 6.0, "assumption (datasheet ~2-6 uA shutdown/standby, p.2 not re-read)"),
    ("DW01A operating current (U4)", 3.0, 6.0, "assumption (datasheet not read, ~3 uA typ)"),
    ("8205A leakage (Q1)", 0.05, 1.0, "assumption (both FETs on, Vds ~0)"),
    ("Battery divider R7+R8, permanent (A-045 Option A)", 2.1, 2.1, "4.2 V (full cell) / 2 MOhm; 1.85 uA at 3.7 V nominal; 1 % resistors"),
    ("AHT20 sleep (U5)", 0.25, 1.0, "power budget value (AHT20 datasheet 2024-07: sleep <= 0.2 uA max)"),
    ("BH1750 power-down (U6)", 0.01, 1.0, "datasheet unverified; needs a power-down command before sleep"),
    ("U7 soil gate, VCC = IO3 low", 0.1, 1.0, "IO3 must be held low in deep sleep (RTC hold); leakage only"),
    ("MLCC leakage C1-C14 (about 100 uF total on VBAT/3V3)", 0.1, 1.0, "assumption (>= 100 Mohm insulation resistance class)"),
    ("USBLC6 / LEDs / CC resistors, VBUS = 0", 0.0, 0.5, "no supply, only I/O leakage (USBLC6 datasheet not read)"),
    ("Pull-ups R3-R5, R16, R13/R14", 0.0, 0.0, "all nodes at the rail in sleep: no DC path (check: IO8/IO9/EN high)"),
]
typ = sum(r[1] for r in SLEEP); worst = sum(r[2] for r in SLEEP)
print(f"\nSleep budget (battery terminal, USB unplugged): typical {typ:.1f} uA, worst {worst:.1f} uA, NFR-12 limit {D.NFR12_MAX_UA:.0f} uA, target {D.NFR12_TARGET_UA:.0f} uA")
check(typ <= D.NFR12_TARGET_UA, f"typical sleep sum {typ:.1f} uA <= NFR-12 design target {D.NFR12_TARGET_UA:.0f} uA ({D.NFR12_TARGET_UA/typ:.1f}x margin)")
check(worst <= D.NFR12_MAX_UA, f"worst sleep sum {worst:.1f} uA <= NFR-12 limit {D.NFR12_MAX_UA:.0f} uA ({D.NFR12_MAX_UA/worst:.1f}x margin)")


# ---------------- 7 generated doc table (drift check) ----------------
def render_md():
    L = ["# Pin map and sleep-leakage table (generated by check_netlist.py --write; do not edit by hand)", "",
         "Requirements: NFR-01 (best and typical >= 3 months, worst > 1 month), NFR-12 (whole-board deep sleep <= 50 uA, design target 25 uA). Matches design.py; "
         "`firmware/main/board.h` does not exist yet, Mira must copy this table.", "", "## ESP32-C3-MINI-1 pin map", "",
         "| Module pin | Function | Net | Note |", "|---|---|---|---|"]
    notes = {"IO0/ADC1_0": "ADC1_CH0, RTC", "IO1": "free (was BAT_SENS_EN; A-045 Option A removed Q2/R6)", "IO2 (strap)": "strap, pulled up by R16",
             "IO3": "RTC, holds U7 supply LOW in deep sleep", "IO4": "RTC, PCNT edge count", "IO5": "RTC wake, pinhole reset (internal pull-up)",
             "IO8 (strap)": "R4 pull-up", "IO9 (strap)": "R5 pull-up, BOOT switch", "IO18/USB_D-": "USB Serial/JTAG", "IO19/USB_D+": "USB Serial/JTAG"}
    for n, nm, net, side in next(p for p in D.PARTS if p.ref == "U1").pins:
        if nm != "GND":
            L.append(f"| {n} | {nm} | {net if net != 'NC' else 'unused'} | {notes.get(nm, '')} |")
    L += ["", "## Deep-sleep leakage paths (battery terminal, USB unplugged)", "", "| Path | typ uA | worst uA | Source / status |", "|---|---|---|---|"]
    for n, t, w, src in SLEEP:
        L.append(f"| {n} | {t:g} | {w:g} | {src} |")
    L.append(f"| **Sum** | **{typ:.1f}** | **{worst:.1f}** | NFR-12: limit {D.NFR12_MAX_UA:.0f}, target {D.NFR12_TARGET_UA:.0f} uA |")
    L += ["", f"Typical vs target: {D.NFR12_TARGET_UA/typ:.2f}x margin; worst vs limit: {D.NFR12_MAX_UA/worst:.2f}x margin. "
          "Most rows are assumptions (datasheets not read); the real number is the 5.2 / 4.P5 measurement.", ""]
    return "\n".join(L)


MD = os.path.join(HERE, "pinmap-sleep.md")
if "--write" in sys.argv:
    open(MD, "w").write(render_md())
check(os.path.exists(MD) and open(MD).read() == render_md(), "pcb/pinmap-sleep.md is up to date (run with --write to regenerate)")

print("\nParts whose pin numbers are NOT datasheet-verified: " + ", ".join(p.ref for p in D.PARTS if not p.pin_verified))
print("Footprints still to be drawn (not in KiCad library): " + ", ".join(p.ref for p in D.PARTS if p.custom_fp))
print(f"\n{'ALL CHECKS PASS' if not FAILS else str(len(FAILS)) + ' FAIL'}")
sys.exit(1 if FAILS else 0)
