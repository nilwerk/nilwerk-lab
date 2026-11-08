#!/usr/bin/env python3
"""board.h must cite pcb/pinmap-sleep.md instead of retyping a pin table (task 4.F1, FR-D01, NFR-12).
Every `#define NW_PIN_x <io>  /* pcb/pinmap-sleep.md:<line> <NET> ... */` is checked against that line of the pinmap:
the row must name IO<io> and the net <NET>. Also: IO1 must have no NW_PIN_ macro (A-045 Option A, free, not driven),
and the divider row cited in board.h must still say 2.1 uA."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parents[2]            # .../firmware
board = (root / "main" / "board.h").read_text()
pinmap_path = root.parent / "pcb" / "pinmap-sleep.md"
lines = pinmap_path.read_text().splitlines()

pat = re.compile(r"#define\s+(NW_PIN_\w+)\s+(\d+)\s+/\*\s*pcb/pinmap-sleep\.md:(\d+)\s+(\w+)")
found = pat.findall(board)
errors = []
if len(found) < 6 - 1:  # BAT_SENS, SOIL_PWR, SOIL_OUT, I2C_SDA, I2C_SCL
    errors.append(f"expected at least 5 cited pins in board.h, found {len(found)}")
seen_io = set()
for name, io, ln, net in found:
    io, ln = int(io), int(ln)
    seen_io.add(io)
    if not (1 <= ln <= len(lines)):
        errors.append(f"{name}: cited line {ln} does not exist"); continue
    cells = [c.strip() for c in lines[ln - 1].split("|")]
    if len(cells) < 5 or not re.match(rf"IO{io}(?!\d)", cells[2]) or cells[3] != net:
        errors.append(f"{name}: pinmap-sleep.md:{ln} is `{lines[ln-1]}`, expected IO{io} and net {net}")
    else:
        print(f"ok  {name} = IO{io}  <- pinmap-sleep.md:{ln} ({net})")
if 1 in seen_io:
    errors.append("IO1 is not connected (A-045 Option A) and must not get a NW_PIN_ macro")
if re.search(r"#define\s+\w*(BAT_SENS_EN|BATSENS_EN)\w*", board):
    errors.append("a BAT_SENS_EN macro exists: Q2/R6 were removed, there is no divider switch")
# the divider row cited for the resistor values
m = re.search(r"pinmap-sleep\.md:(\d+): 4\.2 V / 2 MOhm = 2\.1 uA", board)
if not m: errors.append("board.h does not cite the divider row (2.1 uA)")
elif "2.1" not in lines[int(m.group(1)) - 1] or "divider" not in lines[int(m.group(1)) - 1].lower():
    errors.append(f"divider cite pinmap-sleep.md:{m.group(1)} no longer is the divider row")
else:
    print(f"ok  divider row pinmap-sleep.md:{m.group(1)}")
# no retyped table: a Markdown table in board.h is a bug
if re.search(r"^\s*\|.*\|.*\|", board, re.M): errors.append("board.h contains a table; cite pinmap-sleep.md instead")
if errors:
    print("\n".join("FAIL " + e for e in errors)); sys.exit(1)
print("board.h pin cites OK")
