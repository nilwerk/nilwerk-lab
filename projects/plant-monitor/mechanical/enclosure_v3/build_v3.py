"""Export enclosure v3 (STEP, STL, 3MF per part) to projects/plant-monitor/enclosure/v3/. Never overwrites other versions (v3 only)."""
import pathlib
import cadquery as cq
import enclosure_v3 as E

OUT = pathlib.Path(__file__).resolve().parents[2] / "enclosure" / "v3"


def parts():
    return {"tray": E.tray(), "lid": E.lid(), "tail_plug": E.plug()}


def export_all():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, wp in parts().items():
        for ext in ("step", "stl", "3mf"):
            f = str(OUT / f"enclosure_v3_{name}.{ext}")
            if ext == "step":
                cq.exporters.export(wp, f)
            else:
                cq.exporters.export(wp, f, tolerance=0.01, angularTolerance=0.1)
    asm = cq.Workplane("XY").add(E.tray().val()).add(E.lid().val()).add(E.plug().val())
    cq.exporters.export(cq.Workplane("XY").newObject([cq.Compound.makeCompound([E.tray().val(), E.lid().val(), E.plug().val()])]), str(OUT / "enclosure_v3_assembly.step"))
    cq.exporters.export(cq.Workplane("XY").newObject([cq.Compound.makeCompound([E.board_ghost().val(), E.cell_ghost().val()])]), str(OUT / "enclosure_v3_reference_board_cell.step"))
    print("exported to", OUT)


if __name__ == "__main__":
    export_all()
