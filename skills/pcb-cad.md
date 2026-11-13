# PCB and CAD skills

| Name | What | URL | Status | Used by |
|---|---|---|---|---|
| KiCad 9 docs | Schematic, layout, design rules | https://docs.kicad.org/9.0/ | to verify | Emil |
| KiCad 9 CLI | ERC, DRC, Gerber, BOM, drill export | https://docs.kicad.org/9.0/en/cli/cli.html | to verify (exit codes, flags) | Emil, Kai |
| ngspice manual | Circuit simulation | https://ngspice.sourceforge.io/docs.html | to verify | Emil |
| JLCPCB PCB capabilities | DFM limits (trace, drill, via-in-pad) | https://jlcpcb.com/capabilities/pcb-capabilities | to verify (current values) | Emil |
| JLCPCB help: shipping | Delivery countries and methods | https://jlcpcb.com/help/article/Do-you-ship-boards-to-my-country | checked 13 Nov (Lead web search), Egypt not confirmed | Lead, Arsany |
| LCSC | Parts, stock, lifecycle | https://www.lcsc.com | to verify | Emil |
| IPC-2221B | Trace width, clearance (paid standard; owner decides access) | https://www.ipc.org | to verify | Emil |
| Ucamco Gerber X2 | Gerber format spec | https://www.ucamco.com | to verify | Emil, Ines |
| gerbv | Gerber viewer for checks | http://gerbv.sourceforge.net | to verify | Emil |
| CadQuery docs | Parametric CAD source | https://cadquery.readthedocs.io/ | to verify | Yara |
| Fusion 360 docs | STEP import, parameter edits | https://help.autodesk.com/view/fusion360/ENU/ | to verify | Yara, Arsany |
| Bambu Lab wiki (P1S, PETG) | Build volume, print settings | https://wiki.bambulab.com/ | to verify | Yara, Peter |

Rule: the fab's DFM rules are loaded into the KiCad project at setup, so DRC shows violations during layout (Emil, meeting 13 Nov).
