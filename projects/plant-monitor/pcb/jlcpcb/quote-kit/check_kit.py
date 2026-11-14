#!/usr/bin/env python3
"""Re-check the quote-kit BOM/CPL against the board file, pcb/bom.csv and the CI cpl.csv (QUOTE ONLY).
Usage: /usr/bin/python3 -I check_kit.py <ci-cpl.csv> [kit-dir]   Nothing is uploaded. Emil (PCB Designer)."""
import csv, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); PCB = os.path.normpath(os.path.join(HERE, "..", ".."))
ci = sys.argv[1]; kit = sys.argv[2] if len(sys.argv) > 2 else HERE
fails = 0
def ok(c, m):
    global fails
    print(("PASS  " if c else "FAIL  ") + m); fails += (not c)
def refs(s): return [x.strip() for x in s.split(",") if x.strip()]
board = open(os.path.join(PCB, "plant-monitor.kicad_pcb"), encoding="utf8").read()
board_refs = set(re.findall(r'\(property "Reference" "([A-Z]+[0-9]+)"', board))
bom = list(csv.DictReader(open(os.path.join(kit, "QUOTE-ONLY_bom-jlc.csv"), encoding="utf8")))
cpl = list(csv.DictReader(open(os.path.join(kit, "QUOTE-ONLY_cpl-jlc.csv"), encoding="utf8")))
src = list(csv.DictReader(open(os.path.join(PCB, "bom.csv"), encoding="utf8")))
cic = list(csv.DictReader(open(ci, encoding="utf8")))
bom_d = [d for r in bom for d in refs(r["Designator"])]
ok(len(bom_d) == len(set(bom_d)), f"BOM designators unique ({len(bom_d)})")
ok(all(r["LCSC Part #"].startswith("C") for r in bom), f"LCSC Part # on all {len(bom)} BOM lines")
src_d = {d for r in src for d in refs(r["Designator"])}
nolcsc = sorted(d for r in src if not r["LCSC"].startswith("C") for d in refs(r["Designator"]))
ok(set(bom_d) == src_d - set(nolcsc), f"BOM set = pcb/bom.csv minus parts without LCSC {nolcsc}")
ok(set(bom_d) <= board_refs, "every BOM designator exists on the board file")
cpl_d = [r["Designator"] for r in cpl]
ok(set(cpl_d) == set(bom_d), f"CPL designators = BOM designators ({len(cpl_d)})")
ok(all(r["Layer"] == "Top" for r in cpl), "CPL all Top")
cm = {r["Ref"]: r for r in cic}
ok(set(cm) == set(cpl_d), "CPL designators = CI cpl.csv (current main head)")
bad = [r["Designator"] for r in cpl if abs(float(r["Mid X"]) - float(cm[r["Designator"]]["PosX"])) > 1e-3
       or abs(float(r["Mid Y"]) - float(cm[r["Designator"]]["PosY"])) > 1e-3
       or abs(float(r["Rotation"]) - float(cm[r["Designator"]]["Rot"])) > 1e-3]
ok(not bad, f"CPL X/Y/rotation equal CI cpl.csv for all parts {bad}")
for r in src:
    if r["LCSC"].startswith("C"):
        b = [x for x in bom if set(refs(x["Designator"])) == set(refs(r["Designator"]))]
        ok(b and b[0]["LCSC Part #"] == r["LCSC"], f"LCSC {r['LCSC']} for {r['Designator']} same in BOM and bom.csv")
print("RESULT:", "ALL PASS" if not fails else f"{fails} FAIL"); sys.exit(1 if fails else 0)
