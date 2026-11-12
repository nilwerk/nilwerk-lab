#!/usr/bin/env python3
"""Pack the KiCad 9 export of build_gerber.sh into the JLCPCB file set (board and 2-up panel).

Usage: python3 -I package_jlc.py <raw-dir> <this-dir>
  <raw-dir>  the /out directory of build_gerber.sh (board/ and panel/ subfolders)
  <this-dir> the gerber/ folder: writes the two zips and SHA256SUMS here
The names follow the EasyEDA/JLCPCB convention (Gerber_TopLayer.GTL ... Drill_NPTH_Through.DRL), checked by
verify_gerber.py. The gbrjob's Path entries are renamed with the same map, so the job file matches the zip.
Deterministic zips (fixed 1980 timestamps). Nothing is uploaded. Emil (PCB Designer).
"""
import hashlib, json, os, re, sys, zipfile

NAME_MAP = [  # (KiCad suffix after the board name, JLCPCB name)
    ("F_Cu.gtl", "Gerber_TopLayer.GTL"),
    ("B_Cu.gbl", "Gerber_BottomLayer.GBL"),
    ("F_Mask.gts", "Gerber_TopSolderMaskLayer.GTS"),
    ("B_Mask.gbs", "Gerber_BottomSolderMaskLayer.GBS"),
    ("F_Silkscreen.gto", "Gerber_TopSilkscreenLayer.GTO"),
    ("B_Silkscreen.gbo", "Gerber_BottomSilkscreenLayer.GBO"),
    ("F_Paste.gtp", "Gerber_TopPasteMaskLayer.GTP"),
    ("B_Paste.gbp", "Gerber_BottomPasteMaskLayer.GBP"),
    ("Edge_Cuts.gm1", "Gerber_BoardOutlineLayer.GKO"),
    ("PTH.drl", "Drill_PTH_Through.DRL"),
    ("NPTH.drl", "Drill_NPTH_Through.DRL"),
    ("PTH-drl_map.gbr", "Drill_PTH_Through_Map.GBR"),
    ("NPTH-drl_map.gbr", "Drill_NPTH_Through_Map.GBR"),
    ("drill.rpt", "Drill_Report.rpt"),
    ("job.gbrjob", "Gerber_JobFile.gbrjob"),
]
PREFIX = re.compile(r"^plant-monitor(-panel)?-")

def jlc_name(kicad_name):
    base = PREFIX.sub("", kicad_name)
    for suf, jlc in NAME_MAP:
        if base == suf:
            return jlc
    return None  # cpl.csv and anything else is not part of the fab set

def pack(src_dir, zip_path):
    members = {}
    for f in sorted(os.listdir(src_dir)):
        j = jlc_name(f)
        if j is None:
            continue
        data = open(os.path.join(src_dir, f), "rb").read()
        if j == "Gerber_JobFile.gbrjob":
            job = json.loads(data.decode("utf8"))
            for entry in job.get("FilesAttributes", []):
                entry["Path"] = jlc_name(os.path.basename(entry["Path"])) or entry["Path"]
            data = json.dumps(job, indent=2).encode("utf8")
        members[j] = data
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, members[name])
    return sorted(members)

def main():
    raw, out = sys.argv[1], sys.argv[2]
    res = {}
    res["board"] = pack(os.path.join(raw, "board"), os.path.join(out, "plant-monitor-jlc-board.zip"))
    res["panel"] = pack(os.path.join(raw, "panel"), os.path.join(out, "plant-monitor-jlc-panel-2up.zip"))
    lines = []
    for z in ("plant-monitor-jlc-board.zip", "plant-monitor-jlc-panel-2up.zip"):
        lines.append("%s  %s" % (hashlib.sha256(open(os.path.join(out, z), "rb").read()).hexdigest(), z))
    open(os.path.join(out, "SHA256SUMS"), "w").write("\n".join(lines) + "\n")
    for k, v in res.items():
        print(k, len(v), "files:", ", ".join(v))

if __name__ == "__main__":
    main()
