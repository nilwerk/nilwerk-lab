#!/usr/bin/env python3
"""Build the JLCPCB panel as a KiCad 9 board file (Plan 4.P4, Ines F6).

Input : ../plant-monitor.kicad_pcb (the board, unchanged) and the panel geometry of ../jlcpcb/panel.py
Output: panel/plant-monitor-panel.kicad_pcb (written next to this script, path given as argument)

The board is copied N_BOARDS times with a pure translation (no rotation, no change to any item except its
position and its UUID). Rails are the panel outline on Edge.Cuts; tooling holes are 2 mm NPTH pads; fiducials
are 1 mm copper pads with a 2 mm mask opening. There are NO breakaway tabs or mouse bites yet (not designed).
Run with: python3 -I make_panel.py <board.kicad_pcb> <jlcpcb_dir> <out.kicad_pcb>
Emil (PCB Designer).
"""
import copy, os, re, sys, uuid

def tokenize(text):
    tok = re.compile(r'\s+|(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+)')
    pos, out = 0, []
    while pos < len(text):
        m = tok.match(text, pos)
        if not m:
            raise ValueError("tokenizer stuck at %d" % pos)
        pos = m.end()
        if m.group(1): out.append("(")
        elif m.group(2): out.append(")")
        elif m.group(3) or m.group(4): out.append(m.group(3) or m.group(4))
    return out

def parse(tokens):
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(t)
    assert len(stack) == 1, "unbalanced parentheses"
    return stack[0][0]

def ser(node):
    if isinstance(node, list):
        return "(" + " ".join(ser(c) for c in node) + ")"
    return node

def fmt(v):
    s = ("%.6f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def is_list(n, key):
    return isinstance(n, list) and n and n[0] == key

def shift_all(node, dx, dy):
    """Shift every start/end/mid/center/at/xy pair found at any depth (used for non-footprint items)."""
    if not isinstance(node, list):
        return
    if len(node) == 3 and node[0] in ("start", "end", "mid", "center", "at", "xy"):
        node[1] = fmt(float(node[1]) + dx); node[2] = fmt(float(node[2]) + dy)
        return
    for c in node:
        shift_all(c, dx, dy)

def new_uuid(seed):
    return '"%s"' % uuid.uuid5(uuid.NAMESPACE_URL, seed)

def retag_uuids(node, tag):
    """Every copy gets its own UUIDs (derived from the old one), so no two items share an identity."""
    if not isinstance(node, list):
        return
    if len(node) == 2 and node[0] == "uuid":
        node[1] = new_uuid(tag + node[1].strip('"'))
        return
    for c in node:
        retag_uuids(c, tag)

def copy_item(item, dx, dy, tag):
    new = copy.deepcopy(item)
    if is_list(new, "footprint"):
        for c in new:
            if is_list(c, "at"):
                c[1] = fmt(float(c[1]) + dx); c[2] = fmt(float(c[2]) + dy)
                break
    else:
        shift_all(new, dx, dy)
    retag_uuids(new, tag)
    return new

def line_seg(x1, y1, x2, y2, layer):
    return ["gr_line", ["start", fmt(x1), fmt(y1)], ["end", fmt(x2), fmt(y2)],
            ["stroke", ["width", "0.05"], ["type", "default"]], ["layer", '"%s"' % layer],
            ["uuid", new_uuid("panel-%s-%s" % (layer, (x1, y1, x2, y2)))]]

def fp_pad_np(x, y, d):
    return ["footprint", '"NW:Panel_Tooling_NPTH_%s"' % fmt(d), ["layer", '"F.Cu"'], ["at", fmt(x), fmt(y)],
            ["attr", "exclude_from_bom", "exclude_from_pos_files"],
            ["pad", '""', "np_thru_hole", "circle", ["at", "0", "0"], ["size", fmt(d), fmt(d)],
             ["drill", fmt(d)], ["layers", '"*.Cu"', '"*.Mask"']]]

def fp_fiducial(x, y, d, mask_margin):
    return ["footprint", '"NW:Panel_Fiducial_%s"' % fmt(d), ["layer", '"F.Cu"'], ["at", fmt(x), fmt(y)],
            ["attr", "smd", "exclude_from_bom", "exclude_from_pos_files"],
            ["pad", '"1"', "smd", "circle", ["at", "0", "0"], ["size", fmt(d), fmt(d)],
             ["layers", '"F.Cu"', '"F.Mask"'], ["solder_mask_margin", fmt(mask_margin)]]]

def main():
    board_path, jlc_dir, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    sys.path.insert(0, jlc_dir)
    import panel as P  # geometry and rules, the same numbers as the DXF and the checklist
    L = P.layout()
    assert all(ok for ok, _ in P.checks(L)), "panel geometry checks fail"
    b = L["b"]
    text = open(board_path, encoding="utf8").read()
    root = parse(tokenize(text))
    assert root[0] == "kicad_pcb"
    header, items = [], []
    for c in root[1:]:
        if isinstance(c, list) and c[0] in ("footprint", "segment", "via", "zone", "gr_line", "gr_rect", "gr_text", "gr_circle", "gr_arc", "gr_poly"):
            items.append(c)
        else:
            header.append(c)
    out_items = []
    for i, (ox, oy) in enumerate(L["offs"]):
        dx, dy = ox - b["x0"], oy - b["y0"]
        for it in items:
            out_items.append(copy_item(it, dx, dy, "copy%d-" % i))
    # panel outline (rails are the margin between this rectangle and the board copies)
    W, H = L["W"], L["H"]
    for (x1, y1, x2, y2) in [(0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]:
        out_items.append(line_seg(x1, y1, x2, y2, "Edge.Cuts"))
    for x, y in L["tools"]:
        out_items.append(fp_pad_np(x, y, P.TOOL_HOLE))
    for x, y in L["fids"]:
        out_items.append(fp_fiducial(x, y, P.FID_DIA, (P.FID_MASK - P.FID_DIA) / 2))
    lines = ["(kicad_pcb"]
    for c in header:
        lines.append("\t" + ser(c))
    for c in out_items:
        lines.append("\t" + ser(c))
    lines.append(")")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf8").write("\n".join(lines) + "\n")
    # the board's project file (DRC severities, net classes) is copied so the panel is checked with the same rules
    import shutil
    shutil.copyfile(os.path.splitext(board_path)[0] + ".kicad_pro", os.path.splitext(out_path)[0] + ".kicad_pro")
    print("wrote %s: %d board copies, %d outline segments, %d tooling holes, %d fiducials, panel %.1f x %.1f mm"
          % (out_path, len(L["offs"]), 4, len(L["tools"]), len(L["fids"]), W, H))

if __name__ == "__main__":
    main()
