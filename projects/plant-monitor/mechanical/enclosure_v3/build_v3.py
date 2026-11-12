"""Export enclosure v3 to projects/plant-monitor/enclosure/v3/ (STEP, STL, 3MF per printed part; STEP per tail variant).
Printed parts (tray, lid, tail_plug) do not depend on the tail length (TAIL_VARIANTS): one set serves both variants.
Variant files: assembly and reference board+cell, one per tail length (suffix _tail14 / _tail20).
Never overwrites other versions: slice-2 files (enclosure_v3_assembly.step, enclosure_v3_reference_board_cell.step) stay as the record of the 25 mm DXF tail."""
import pathlib
import cadquery as cq
import enclosure_v3 as E
import params_v3 as P

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
    for tail, exposed in P.TAIL_VARIANTS.items():
        tl = P.TAIL_L_VARIANT[tail]
        asm = cq.Compound.makeCompound([E.tray().val(), E.lid().val(), E.plug().val(), E.board_ghost(tl).val(), E.cell_ghost().val()])
        cq.exporters.export(cq.Workplane("XY").newObject([asm]), str(OUT / f"enclosure_v3_assembly_tail{tail}.step"))
        ref = cq.Compound.makeCompound([E.board_ghost(tl).val(), E.cell_ghost().val()])
        cq.exporters.export(cq.Workplane("XY").newObject([ref]), str(OUT / f"enclosure_v3_reference_board_cell_tail{tail}.step"))
    print("exported to", OUT)


if __name__ == "__main__":
    export_all()
