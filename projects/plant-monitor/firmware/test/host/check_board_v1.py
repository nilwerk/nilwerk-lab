#!/usr/bin/env python3
"""v1 board config check (task 4.F1 v1 bench, FR-D01).
1. The NW_PIN_* macros in the PLANT_BOARD_V1_SUPERMINI block of main/board.h must equal the generated pin table in
   v1/WIRING.md section 3 (BEGIN:pins ... END:pins), and each must cite `v1/WIRING.md section 3`.
2. Kconfig must offer PLANT_BOARD_V1_SUPERMINI; sdkconfig.defaults.v1 must select it, route the console to USB Serial/JTAG
   (the SuperMini has no UART bridge) and turn the BLE setup flow off.
`--selftest` proves the check can fail: it mutates a pin in a temp copy and a doc row, and both must be caught."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parents[2]            # .../firmware
wiring = root.parent / "v1" / "WIRING.md"

def table(text):
    m = re.search(r"<!-- BEGIN:pins -->(.*?)<!-- END:pins -->", text, re.S)
    if not m: return None, ["WIRING.md has no BEGIN:pins block"]
    rows = {}
    for ln in m.group(1).splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) >= 5 and c[3].startswith("NW_PIN_"):
            g = re.match(r"GPIO(\d+)$", c[0])
            if g: rows[c[3]] = (int(g.group(1)), c[2])
    return rows, []

def v1_block(board):
    m = re.search(r"#ifdef CONFIG_PLANT_BOARD_V1_SUPERMINI(.*?)\n#else", board, re.S)
    return m.group(1) if m else None

def check(board, wtext, kconfig, defaults_v1):
    errors = []
    rows, e = table(wtext); errors += e
    blk = v1_block(board)
    if blk is None: return errors + ["board.h has no PLANT_BOARD_V1_SUPERMINI block"]
    found = {}
    for name, io, rest in re.findall(r"#define\s+(NW_PIN_\w+)\s+(\d+)\s+/\*(.*?)\*/", blk):
        found[name] = int(io)
        if "v1/WIRING.md section 3" not in rest: errors.append(f"{name}: no `v1/WIRING.md section 3` cite")
    if rows:
        if len(rows) != 6: errors.append(f"WIRING.md pin table has {len(rows)} board.h rows, expected 6")
        for name, (gpio, sig) in rows.items():
            if name not in found: errors.append(f"{name} (GPIO{gpio}) in WIRING.md but not in the v1 block")
            elif found[name] != gpio: errors.append(f"{name}: board.h v1 = {found[name]}, WIRING.md section 3 = GPIO{gpio}")
            elif sig not in blk: errors.append(f"{name}: signal {sig} not named in the v1 block")
        for name in found:
            if name not in rows: errors.append(f"{name} in the v1 block but not in WIRING.md section 3")
    if "PLANT_BOARD_V1_SUPERMINI" not in kconfig: errors.append("Kconfig has no PLANT_BOARD_V1_SUPERMINI")
    d = [l.strip() for l in defaults_v1.splitlines() if l.strip() and not l.startswith("#")]
    for want in ("CONFIG_PLANT_BOARD_V1_SUPERMINI=y", "CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y", "CONFIG_PLANT_SETUP_FLOW=n"):
        if want not in d: errors.append(f"sdkconfig.defaults.v1 lacks {want}")
    return errors

def main():
    board = (root / "main" / "board.h").read_text()
    wtext = wiring.read_text()
    kc = (root / "main" / "Kconfig.projbuild").read_text()
    dv1 = (root / "sdkconfig.defaults.v1").read_text()
    if "--selftest" in sys.argv:
        bad = 0
        m1 = board.replace("#define NW_PIN_I2C_SDA 6    /* v1/WIRING", "#define NW_PIN_I2C_SDA 8    /* v1/WIRING")
        m2 = re.sub(r"GPIO6 \| c2 r1", "GPIO8 | c2 r1", wtext, count=1)
        m3 = board.replace("v1/WIRING.md section 3: GPIO0 BAT_SENS", "GPIO0 BAT_SENS")
        for label, args in (("pin changed in board.h", (m1, wtext, kc, dv1)), ("pin changed in WIRING.md", (board, m2, kc, dv1)),
                            ("cite removed", (m3, wtext, kc, dv1)), ("console line removed", (board, wtext, kc, dv1.replace("USB_SERIAL_JTAG=y", "UART=y")))):
            if check(*args): print(f"ok  mutant caught: {label}")
            else: print(f"FAIL mutant survived: {label}"); bad += 1
        if check(board, wtext, kc, dv1): print("FAIL unmutated input does not pass"); bad += 1
        sys.exit(1 if bad else 0)
    errors = check(board, wtext, kc, dv1)
    if errors: print("\n".join("FAIL " + e for e in errors)); sys.exit(1)
    rows, _ = table(wtext)
    for n, (g, s) in sorted(rows.items(), key=lambda kv: kv[1][0]): print(f"ok  {n} = GPIO{g} ({s}) matches WIRING.md section 3")
    print("v1 board config OK")

main()
