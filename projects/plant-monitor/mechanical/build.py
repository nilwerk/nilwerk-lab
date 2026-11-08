"""Build + export both variants: STEP, STL, 3MF per part into out/<variant>/. Run: python build.py"""
import pathlib
import cadquery as cq
import bay
import params as P

OUT = pathlib.Path(__file__).parent / "out"


def export_all():
    for key in P.VARIANTS:
        d = OUT / key
        d.mkdir(parents=True, exist_ok=True)
        for part, wp in (("tray", bay.tray(key)), ("lid", bay.lid(key))):
            for ext in ("step", "stl", "3mf"):
                f = str(d / f"bay_{key}_{part}.{ext}")
                if ext == "step":
                    cq.exporters.export(wp, f)
                else:
                    cq.exporters.export(wp, f, tolerance=0.01, angularTolerance=0.1)
    print("exported to", OUT)


if __name__ == "__main__":
    export_all()
