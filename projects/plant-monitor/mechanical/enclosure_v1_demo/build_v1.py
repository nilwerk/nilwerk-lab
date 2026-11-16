"""Export the v1 demo housing (4.E5) to projects/plant-monitor/enclosure/v1_demo_compact/: STEP (assembled position, for Fusion 360), STL + 3MF (print orientation)
per printed part, plus a STEP of the reference perfboard + parts + cell (not printed). Never touches enclosure/v3."""
import os, sys, pathlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
import enclosure_v1 as E

OUT = pathlib.Path(__file__).resolve().parents[2] / "enclosure" / "v1_demo_compact"


def parts_assembled():
    return {"base": E.tray(), "lid": E.lid()}


def parts_print():
    return {"base": E.tray(), "lid": E.lid_print()}


def export_all():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, wp in parts_assembled().items():
        cq.exporters.export(wp, str(OUT / f"enclosure_v1_demo_{name}.step"))
    for name, wp in parts_print().items():
        for ext in ("stl", "3mf"):
            cq.exporters.export(wp, str(OUT / f"enclosure_v1_demo_{name}.{ext}"), tolerance=0.01, angularTolerance=0.1)
    asm = cq.Compound.makeCompound([E.tray().val(), E.lid().val(), E.perfboard_ghost().val(), E.parts_ghost().val(), E.cell_ghost().val()])
    cq.exporters.export(cq.Workplane("XY").newObject([asm]), str(OUT / "enclosure_v1_demo_assembly_with_reference_parts.step"))
    print("exported to", OUT)


if __name__ == "__main__":
    export_all()
