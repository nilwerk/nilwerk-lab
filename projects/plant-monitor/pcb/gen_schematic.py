#!/usr/bin/env python3
"""Generate the KiCad 9 schematic, project file and pcb/bom.csv from design.py.  Run: python3 gen_schematic.py
No GUI/KiCad needed.  Every pin gets a net label at its connection point (no wires), so connectivity = label names."""
from __future__ import annotations
import csv, json, math, os, uuid
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
NS = uuid.UUID("6d1c0a52-7a54-4f1e-9a53-4e696c776572")
ROOT = str(uuid.uuid5(NS, "root"))
PIN_LEN = 2.54


def uid(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', "'") + '"'


def fmt(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")


def geometry(p: D.Part):
    L = [x for x in p.pins if x[3] == "L"]; R = [x for x in p.pins if x[3] == "R"]; Bt = [x for x in p.pins if x[3] == "B"]
    rows = max(len(L), len(R), 1)
    passive = len(p.pins) == 2 and not Bt
    w = 5.08 if passive else max(25.4, math.ceil((len(Bt) * 2.54 + 2.54) / 2.54) * 2.54)
    if not passive:
        w = math.ceil(max(w, 25.4) / 2.54) * 2.54
    h = rows * 2.54 + (0 if passive else 2.54)
    pos = {}   # (num) -> (x, y, angle, side)  lib coordinates (y up)
    for side, lst in (("L", L), ("R", R)):
        for i, pin in enumerate(lst):
            y = ((rows - 1) / 2 - i) * 2.54
            x = -(w / 2 + PIN_LEN) if side == "L" else (w / 2 + PIN_LEN)
            pos[pin[0]] = (x, y, 0 if side == "L" else 180, side)
    for j, pin in enumerate(Bt):
        x = (j - (len(Bt) - 1) / 2) * 2.54
        pos[pin[0]] = (x, -(h / 2 + PIN_LEN), 90, "B")
    return w, h, pos


def lib_symbol(p: D.Part):
    w, h, pos = geometry(p)
    nm = f"NW_PM:{p.sym}"
    eff = "(effects (font (size 1.27 1.27)))"
    props = [("Reference", "U", (0, h / 2 + 2.54), False), ("Value", p.sym, (0, -h / 2 - 5.08), False),
             ("Footprint", "", (0, 0), True), ("Datasheet", "", (0, 0), True), ("LCSC", "", (0, 0), True)]
    s = [f"    (symbol {q(nm)} (exclude_from_sim no) (in_bom yes) (on_board yes)"]
    for k, v, (x, y), hide in props:
        s.append(f"      (property {q(k)} {q(v)} (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)){' (hide yes)' if hide else ''}))")
    s.append(f"      (symbol {q(p.sym + '_0_1')}")
    s.append(f"        (rectangle (start {fmt(-w/2)} {fmt(h/2)}) (end {fmt(w/2)} {fmt(-h/2)}) (stroke (width 0.254) (type default)) (fill (type background))))")
    s.append(f"      (symbol {q(p.sym + '_1_1')}")
    for pin in p.pins:
        x, y, a, side = pos[pin[0]]
        nm_ = "~" if len(p.pins) == 2 else pin[1]
        s.append(f"        (pin passive line (at {fmt(x)} {fmt(y)} {a}) (length {PIN_LEN}) (name {q(nm_)} (effects (font (size 1.016 1.016)))) (number {q(pin[0])} (effects (font (size 1.016 1.016)))))")
    s.append("      ))")
    return "\n".join(s)


def layout():
    """Row-wrapping placement per block.  Returns {ref: (x, y)} in mm (sheet coords, y down) and block title positions."""
    place, titles = {}, []
    y = 40.0
    blocks = []
    for p in D.PARTS:
        if p.block not in blocks:
            blocks.append(p.block)
    for b in blocks:
        parts = [p for p in D.PARTS if p.block == b]
        titles.append((b, 20.0, y))
        y += 12
        x, row_h, x0 = 40.0, 0.0, 40.0
        for p in parts:
            w, h, _ = geometry(p)
            maxlab = max(len(n[2]) for n in p.pins) * 1.4
            wid = w + 2 * PIN_LEN + 2 * maxlab + 24
            if x + wid > 760 and x > x0:
                x = x0; y += row_h + 22; row_h = 0.0
            hh = h + 2 * PIN_LEN + 22
            place[p.ref] = (round((x + maxlab + PIN_LEN + w / 2 + 12) / 2.54) * 2.54, round((y + hh / 2) / 2.54) * 2.54)
            x += wid
            row_h = max(row_h, hh)
        y += row_h + 22
    return place, titles


def sheet() -> str:
    place, titles = layout()
    syms = {}
    for p in D.PARTS:
        syms.setdefault(p.sym, p)
    out = ["(kicad_sch", "  (version 20250114)", '  (generator "nilwerk_gen_schematic")', '  (generator_version "9.0")',
           f"  (uuid {q(ROOT)})", '  (paper "A1")',
           f"  (title_block (title {q(D.TITLE)}) (date \"2026-11-08\") (rev \"P1\") (company \"Nilwerk\")"
           f" (comment 1 \"NFR-01 best/typ 3 mo, worst > 1 mo (Arsany 2026-11-08); NFR-12 <= 50 uA, target 25 uA (A-027)\")"
           f" (comment 2 \"R9 = {D.R9_OHM/1000:g}k -> {D.I_CHG_MA:.0f} mA = {D.I_CHG_MA/D.CELL_MIN_MAH:.2f}C; cell EEMB LP603449-PCM (A-034 decided)\"))",
           "  (lib_symbols"]
    out += [lib_symbol(p) for p in syms.values()]
    out.append("  )")
    for i, (t, x, y) in enumerate(titles):
        out.append(f"  (text {q(t)} (exclude_from_sim no) (at {fmt(x)} {fmt(y)} 0) (effects (font (size 3.81 3.81) bold) (justify left)) (uuid {q(uid('title', i))}))")
    for i, n in enumerate(D.NOTES):
        out.append(f"  (text {q(n)} (exclude_from_sim no) (at 20 {fmt(14 + i * 4)} 0) (effects (font (size 1.905 1.905)) (justify left)) (uuid {q(uid('note', i))}))")
    for p in D.PARTS:
        X, Y = place[p.ref]
        w, h, pos = geometry(p)
        out.append(f"  (symbol (lib_id {q('NW_PM:' + p.sym)}) (at {fmt(X)} {fmt(Y)} 0) (unit 1) (exclude_from_sim no) (in_bom {'yes' if p.in_bom else 'no'}) (on_board yes) (dnp no) (uuid {q(uid('sym', p.ref))})")
        for k, v, dy, hide in (("Reference", p.ref, h / 2 + 2.54, False), ("Value", p.value, -h / 2 - 5.08, False),
                               ("Footprint", p.footprint, 0, True), ("Datasheet", "", 0, True), ("LCSC", p.lcsc, 0, True)):
            out.append(f"    (property {q(k)} {q(v)} (at {fmt(X)} {fmt(Y - dy)} 0) (effects (font (size 1.27 1.27)){' (hide yes)' if hide else ''}))")
        for pin in p.pins:
            out.append(f"    (pin {q(pin[0])} (uuid {q(uid('pin', p.ref, pin[0]))}))")
        out.append(f"    (instances (project \"plant-monitor\" (path {q('/' + ROOT)} (reference {q(p.ref)}) (unit 1))))")
        out.append("  )")
        for num, name, net, side in p.pins:
            x, y, a, sd = pos[num]
            px, py = X + x, Y - y
            if net == "NC":
                out.append(f"  (no_connect (at {fmt(px)} {fmt(py)}) (uuid {q(uid('nc', p.ref, num))}))")
                continue
            ang, just = {"L": (180, "right"), "R": (0, "left"), "B": (270, "left")}[side]
            out.append(f"  (label {q(net)} (at {fmt(px)} {fmt(py)} {ang}) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid {q(uid('lab', p.ref, num))}))")
    out += ['  (sheet_instances (path "/" (page "1")))', "  (embedded_fonts no)", ")"]
    return "\n".join(out) + "\n"


def bom_rows():
    groups = {}
    for p in D.PARTS:
        if not p.in_bom:
            continue
        groups.setdefault((p.lcsc, p.value, p.footprint, p.mpn), []).append(p)
    rows = []
    for (lcsc, val, fp, mpn), ps in groups.items():
        rows.append({"Designator": ",".join(sorted((x.ref for x in ps), key=lambda r: (r.rstrip("0123456789"), int(r[len(r.rstrip("0123456789")):])))),
                     "Qty": len(ps), "Value": val, "Footprint": fp, "LCSC": lcsc, "MPN": mpn,
                     "FootprintStatus": "to-draw-in-4.P2" if ps[0].custom_fp else "kicad-library-name",
                     "PinMapStatus": "signal-map-from-4.P1-not-checked-vs-4.P2-drawing" if not ps[0].pin_verified else "standard-pinout",
                     "Note": ps[0].note})
    return sorted(rows, key=lambda r: (r["Designator"][0], r["Designator"]))


def main():
    with open(os.path.join(HERE, "plant-monitor.kicad_sch"), "w") as f:
        f.write(sheet())
    with open(os.path.join(HERE, "plant-monitor.kicad_pro"), "w") as f:
        json.dump({"meta": {"filename": "plant-monitor.kicad_pro", "version": 3}, "board": {}, "libraries": {"pinned_symbol_libs": []},
                   "schematic": {"drawing": {"default_line_thickness": 6.0}}, "sheets": [[ROOT, "Root"]]}, f, indent=2)
        f.write("\n")
    rows = bom_rows()
    with open(os.path.join(HERE, "bom.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"wrote schematic ({len(D.PARTS)} parts), project, bom.csv ({len(rows)} lines)")


if __name__ == "__main__":
    main()
