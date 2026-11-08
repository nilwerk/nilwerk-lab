"""Plant Monitor PCB schematic data model (Plan 4.P1).  Single source for schematic, BOM and checks.

Every part: ref, symbol type, value, footprint, LCSC number, MPN, pins [(num, name, net, side)], flags.
Net "NC" = pin intentionally unconnected (gets a no-connect flag).  Pin numbers marked pin_verified=False were
written from memory/listing, NOT from a read datasheet: they must be checked against the datasheet before 4.P2.
Requirements: NFR-01 (best and typical case >= 3 months, worst case > 1 month; relaxed by Arsany 2026-11-08), NFR-12 (whole-board deep sleep <= 50 uA, design target 25 uA).
Decisions applied 2026-11-08 (Arsany): A-034 cell = EEMB LP603449-PCM from Amazon.de (ASIN B08FD39Y5R); A-045 Option A (no Q2/R6, permanent
divider R7/R8, IO1 free); A-046 Option A (no power path in v1: the board needs a cell).
"""
from __future__ import annotations
from dataclasses import dataclass, field

NFR01_MONTHS = 3          # NFR-01 best and typical case (A-020); single parameter, same name as the power budget
NFR01_WORST_MONTHS = 1    # NFR-01 worst case: MORE than this (relaxed by Arsany 2026-11-08)
NFR12_MAX_UA = 50.0       # NFR-12, A-027
NFR12_TARGET_UA = 25.0

# ---------------------------------------------------------------------------------------------
# CHARGE CURRENT (R9).  TP4056 datasheet REV_2.4 p.9: R_PROG[kOhm] = 1100 / I_BAT[mA].
# A-034 DECIDED 2026-11-08: EEMB LP603449-PCM (Amazon.de B08FD39Y5R): 1000 mAh minimum (1100 typical), PCM built in,
# maximum charging current 1100 mA per the listing (A+ text).  Target <= 0.5C of the MINIMUM capacity (500 mA),
# rounded to an E24 value that keeps the LCSC number already verified.  Change ONLY this block when the cell changes;
# the schematic value, the BOM CSV and the check script all derive from it.
CELL_MIN_MAH = 1000        # EEMB LP603449-PCM, minimum capacity (listing bullet; EEMB datasheet read 2026-11-07)
CELL_MAX_CHARGE_MA = 1100  # listing A+ text: "Maximum charging current: 1100 mA"
R9_OHM = 2400              # E24; 1100/2.4 = 458 mA = 0.46C of 1000 mAh; +15 % TP4056 tolerance 527 mA = 0.53C < 1C (1100 mA)
R9_LCSC = "C22940"         # 0603WAF2401T5E.  0.50C exactly would be 2.2k (500 mA): LCSC number not looked up, kept 2.4k (0.46C)
# ---------------------------------------------------------------------------------------------
I_CHG_MA = 1100.0 / (R9_OHM / 1000.0)


@dataclass
class Part:
    ref: str
    sym: str                      # symbol type name (shared symbol per type)
    value: str
    footprint: str
    lcsc: str
    mpn: str
    pins: list                    # (number, name, net, side)  side in L R B
    note: str = ""
    in_bom: bool = True
    pin_verified: bool = True     # False: pin numbers not read from a datasheet
    custom_fp: bool = False       # footprint must still be drawn (not in the KiCad library)
    block: str = ""


PARTS: list[Part] = []


def add(*a, **k):
    PARTS.append(Part(*a, **k))


# ------------------------------- helpers for passives ----------------------------------------
R_FP, C_FP = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric"


def res(ref, val, lcsc, mpn, a, b, block, note=""):
    add(ref, "R", val, R_FP, lcsc, mpn, [("1", "1", a, "L"), ("2", "2", b, "R")], note, block=block)


def cap(ref, val, lcsc, mpn, a, b, block, note=""):
    add(ref, "C", val, C_FP, lcsc, mpn, [("1", "1", a, "L"), ("2", "2", b, "R")], note, block=block)


R10K = ("10k", "C25804", "0603WAF1002T5E")
C100N = ("100nF", "C14663", "CC0603KRX7R9BB104")
C10U = ("10uF", "C19702", "CL10A106KP8NNNC")

# ------------------------------------- MCU ---------------------------------------------------
B = "1 MCU"
gnd_pads = ["1", "2", "11", "14"] + [str(i) for i in range(36, 54)]
add("U1", "ESP32-C3-MINI-1", "ESP32-C3-MINI-1-N4", "RF_Module:ESP32-C3-MINI-1", "C2838502", "ESP32-C3-MINI-1-N4",
    [("3", "3V3", "3V3", "L"), ("8", "EN", "EN", "L"),
     ("12", "IO0/ADC1_0", "BAT_SENS", "L"), ("13", "IO1", "NC", "L"),
     ("5", "IO2 (strap)", "GPIO2_STRAP", "L"), ("6", "IO3", "SOIL_PWR", "L"), ("18", "IO4", "SOIL_OUT", "L"),
     ("19", "IO5", "FACTORY_RST_N", "L"),
     ("20", "IO6", "I2C_SDA", "R"), ("21", "IO7", "I2C_SCL", "R"), ("22", "IO8 (strap)", "GPIO8_STRAP", "R"),
     ("23", "IO9 (strap)", "BOOT_N", "R"), ("16", "IO10", "NC", "R"),
     ("26", "IO18/USB_D-", "USB_DN", "R"), ("27", "IO19/USB_D+", "USB_DP", "R"),
     ("30", "RXD0/IO20", "NC", "R"), ("31", "TXD0/IO21", "NC", "R")]
    + [(p, "GND", "GND", "B") for p in gnd_pads],
    "FR-D01. Pin numbers verified by Theo against Espressif ESP32-C3-MINI-1 datasheet v2.2 Table 3-1 (PR #41 review). IO2 pulled up by R16; IO10/UART unused.",
    block=B)
cap("C5", *C100N[:1], C100N[1], C100N[2], "3V3", "GND", B, "U1 decoupling")
cap("C4", *C10U[:1], C10U[1], C10U[2], "3V3", "GND", B, "U1 bulk")
res("R3", *R10K, "3V3", "EN", B, "EN pull-up; EN RC = R3 x C12 = 10 ms")
cap("C12", "1uF", "C15849", "CL10A105KB8NNNC", "EN", "GND", B, "EN reset delay")
res("R4", *R10K, "3V3", "GPIO8_STRAP", B, "GPIO8 strap high (needed for download boot)")
res("R5", *R10K, "3V3", "BOOT_N", B, "GPIO9 strap: high = SPI boot, BOOT switch pulls low")
res("R16", *R10K, "3V3", "GPIO2_STRAP", B, "ADDED by 4.P1 fix round (Theo C4): ESP32-C3-MINI-1 datasheet v2.2 s.4.1 recommends a pull-up on GPIO2 (glitches); node at the rail, no sleep current")
add("SW1", "SW4P", "BOOT", "NW:SW_TS-1187A-B-A-B_5.1x5.1", "C318884", "TS-1187A-B-A-B",
    [("1", "1", "BOOT_N", "L"), ("2", "2", "BOOT_N", "L"), ("3", "3", "GND", "R"), ("4", "4", "GND", "R")],
    "BOOT (GPIO9 low at reset = download mode)", custom_fp=True, block=B)
add("SW2", "SW4P", "RESET", "NW:SW_TS-1187A-B-A-B_5.1x5.1", "C318884", "TS-1187A-B-A-B",
    [("1", "1", "EN", "L"), ("2", "2", "EN", "L"), ("3", "3", "GND", "R"), ("4", "4", "GND", "R")],
    "RESET (EN low)", custom_fp=True, block=B)
add("SW3", "SW4P", "FACTORY RESET (pinhole)", "NW:SW_TS-1187A-B-A-B_5.1x5.1", "C318884", "TS-1187A-B-A-B",
    [("1", "1", "FACTORY_RST_N", "L"), ("2", "2", "FACTORY_RST_N", "L"), ("3", "3", "GND", "R"), ("4", "4", "GND", "R")],
    "Pinhole factory reset on IO5 (RTC GPIO: wakes from deep sleep); firmware enables the internal pull-up", custom_fp=True, block=B)

# ------------------------------- USB-C + ESD -------------------------------------------------
B = "2 USB-C"
add("J1", "USBC16", "USB-C (power + USB-JTAG data)", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "C165948",
    "TYPE-C-31-M-12",
    [("A1B12", "GND", "GND", "L"), ("B1A12", "GND", "GND", "L"), ("A4B9", "VBUS", "VBUS", "L"), ("B4A9", "VBUS", "VBUS", "L"),
     ("A5", "CC1", "CC1", "L"), ("B5", "CC2", "CC2", "L"), ("A8", "SBU1", "NC", "L"), ("B8", "SBU2", "NC", "L"),
     ("A6", "DP1", "USB_DP", "R"), ("B6", "DP2", "USB_DP", "R"), ("A7", "DN1", "USB_DN", "R"), ("B7", "DN2", "USB_DN", "R"),
     ("S1", "SHIELD", "GND", "R")],
    "BOM calls it power only; D+/D- are wired to IO19/IO18 (USB Serial/JTAG) so D1 has a job: OPEN POINT 6. Signal-to-pad map verified against the HRO TYPE-C-31-M-12 drawing (LCSC C165948); shield pad numbers belong to the 4.P2 footprint.",
    block=B)
res("R1", "5.1k", "C23186", "0603WAF5101T5E", "CC1", "GND", B, "USB-C sink Rd")
res("R2", "5.1k", "C23186", "0603WAF5101T5E", "CC2", "GND", B, "USB-C sink Rd")
add("D1", "USBLC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", "C7519", "USBLC6-2SC6",
    [("1", "I/O1", "USB_DP", "L"), ("2", "GND", "GND", "L"), ("3", "I/O2", "USB_DN", "L"),
     ("6", "I/O1", "USB_DP", "R"), ("5", "VBUS", "VBUS", "R"), ("4", "I/O2", "USB_DN", "R")],
    "ESD on USB (NFR-08); both I/O pins of a channel on the same net", block=B)
cap("C10", *C100N, "VBUS", "GND", B, "VBUS HF bypass at connector")

# ------------------------------- charger + protection ----------------------------------------
B = "3 Charger + protection"
add("U3", "TP4056", "TP4056", "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.81mm", "C16581", "TP4056-42-ESOP8",
    [("4", "VCC", "VBUS", "L"), ("8", "CE", "VBUS", "L"), ("2", "PROG", "PROG", "L"), ("1", "TEMP", "GND", "L"),
     ("5", "BAT", "VBAT", "R"), ("6", "STDBY", "STDBY_N", "R"), ("7", "CHRG", "CHRG_N", "R"),
     ("3", "GND", "GND", "R"), ("9", "EP", "GND", "R")],
    "TEMP tied to GND = temperature sense disabled (datasheet p.7): the decided cell (EEMB LP603449-PCM, A-034) lists no NTC (wire count not stated in the listing). "
    "CE tied high = always enabled.", block=B)
res("R9", f"{R9_OHM/1000:g}k", R9_LCSC, "0603WAF2401T5E", "PROG", "GND", B,
    f"R_PROG = 1100/I_BAT -> {I_CHG_MA:.0f} mA = {I_CHG_MA/CELL_MIN_MAH:.2f}C of {CELL_MIN_MAH} mAh (cell max charge {CELL_MAX_CHARGE_MA} mA). A-034 decided: see CHARGE CURRENT block in design.py")
cap("C1", *C10U, "VBUS", "GND", B, "TP4056 VCC input")
cap("C2", *C10U, "VBAT", "GND", B, "TP4056 BAT output")
res("R10", "1k", "C21190", "0603WAF1001T5E", "VBUS", "LED_CHRG_A", B, "CHRG LED series; no current when USB is unplugged")
add("D2", "LED", "LED red CHRG", "LED_SMD:LED_0603_1608Metric", "C2286", "KT-0603R",
    [("1", "K", "CHRG_N", "L"), ("2", "A", "LED_CHRG_A", "R")], "pin 1 = cathode assumed; check footprint polarity", block=B)
res("R11", "1k", "C21190", "0603WAF1001T5E", "VBUS", "LED_STDBY_A", B, "STDBY LED series")
add("D3", "LED", "LED green STDBY", "LED_SMD:LED_0805_2012Metric", "C2297", "KT-0805G",
    [("1", "K", "STDBY_N", "L"), ("2", "A", "LED_STDBY_A", "R")], "pin 1 = cathode assumed", block=B)
add("J2", "JSTPH2", "JST PH 2-pin (cell)", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal", "C295747",
    "S2B-PH-SM4-TB(LF)(SN)",
    [("1", "CELL+", "VBAT", "R"), ("2", "CELL-", "CELL_NEG", "R"), ("MP1", "MP", "NC", "R"), ("MP2", "MP", "NC", "R")],
    "Cell EEMB LP603449-PCM (A-034): listing says 'JST plug', PITCH AND POLARITY UNVERIFIED (read the plug label / photo 3 on the Amazon listing: "
    "PH 2.0 mm is assumed). CHECK PLUG POLARITY with a meter before first connection (an Amazon review of this listing reports a reversed plug). "
    "2-pin cell, no NTC: TP4056 TEMP stays tied to GND. Variant J2b (3-pin Molex C564183, Jauch cell) is NOT used.",
    block=B)
add("U4", "DW01A", "DW01A", "Package_TO_SOT_SMD:SOT-23-6", "C351410", "DW01A",
    [("5", "VCC", "VBAT", "L"), ("6", "VSS", "CELL_NEG", "L"), ("2", "CS", "DW_CS", "R"), ("1", "OD", "DW_OD", "R"),
     ("3", "OC", "DW_OC", "R"), ("4", "TD", "NC", "R")],
    "Cell protection. Pins verified against LCSC C351410 datasheet (pin 2 is called VM there = the CS/sense input). The decided cell has its own PCM, so U4/Q1 are a second, redundant protection (open point 4: keep or delete, decision for Arsany).",
    block=B)
add("Q1", "FS8205", "8205A dual N-MOSFET", "Package_SO:TSSOP-8_4.4x3mm_P0.65mm", "C5148694", "8205A",
    [("4", "G1", "DW_OD", "L"), ("5", "G2", "DW_OC", "L"),
     ("2", "S1", "CELL_NEG", "R"), ("3", "S1", "CELL_NEG", "R"), ("1", "D1/2", "FET_MID", "R"), ("8", "D1/2", "FET_MID", "R"),
     ("6", "S2", "GND", "R"), ("7", "S2", "GND", "R")],
    "FET1 (S1 = B-) gate = OD blocks discharge; FET2 (S2 = P- = GND) gate = OC blocks charge. LCSC C5148694 (HXY) is TSSOP-8; "
    "pin map 1 D1, 2-3 S1, 4 G1, 5 G2, 6-7 S2, 8 D2 read from the package drawing in the datasheet (no numbered table printed).", block=B)
res("R15", "1k", "C21190", "0603WAF1001T5E", "DW_CS", "GND", B, "ADDED by 4.P1 (not in BOM draft): DW01A CS series resistor to P-")
cap("C9", *C100N, "VBAT", "CELL_NEG", B, "DW01A VCC-VSS")

# ------------------------------- LDO + battery sense -----------------------------------------
B = "4 Power rail + battery sense"
add("U2", "XC6220", "XC6220B331MR-G (3.3 V)", "Package_TO_SOT_SMD:SOT-23-5", "C86534", "XC6220B331MR-G",
    [("1", "VIN", "VBAT", "L"), ("3", "CE", "VBAT", "L"), ("2", "VSS", "GND", "R"), ("5", "VOUT", "3V3", "R"),
     ("4", "NC", "NC", "R")],
    "Iq 8 uA typ (datasheet, PS mode, IOUT 0.1 mA; 18 uA max A/B series). CE tied to VIN. SOT-25 pins verified: VIN 1, VSS 2, CE 3, NC 4, VOUT 5.", block=B)
cap("C3", *C10U, "VBAT", "GND", B, "LDO input")
cap("C14", "22uF", "C59461", "CL10A226MQ8NRNC", "3V3", "GND", B, "LDO output / Wi-Fi burst")
cap("C13", "1uF", "C15849", "CL10A105KB8NNNC", "3V3", "GND", B, "extra 1 uF on the rail near the sensors")
res("R7", "1M", "C22935", "0603WAF1004T5E", "VBAT", "BAT_SENS", B, "divider top (permanent, A-045 Option A)")
res("R8", "1M", "C22935", "0603WAF1004T5E", "BAT_SENS", "GND", B,
    "divider bottom. A-045 Option A (Arsany 2026-11-08): permanent divider, Q2 and R6 dropped; 4.2 V / 2 MOhm = 2.1 uA, BAT_SENS never above 2.1 V")
cap("C11", *C100N, "BAT_SENS", "GND", B, "ADC source-impedance reservoir (500 k source)")

# ------------------------------- sensors ------------------------------------------------------
B = "5 Sensors + soil front end"
add("U5", "AHT20", "AHT20", "NW:AHT20_DFN-6_3x3", "C2757850", "AHT20",
    [("4", "SDA", "I2C_SDA", "L"), ("3", "SCL", "I2C_SCL", "L"), ("2", "VDD", "3V3", "R"), ("5", "GND", "GND", "R"),
     ("1", "NC", "NC", "R"), ("6", "NC", "NC", "R")],
    "Fix for Theo C1: LCSC C2757850 (Aosong/ASAIR AHT20, datasheet 2024-07 linked from the LCSC page) is a 6-pin DFN 3.0 x 3.0 x 1.0 mm: "
    "1 NC, 2 VDD, 3 SCL, 4 SDA, 5 GND, 6 NC (Table 5, top view). Custom footprint still to be drawn in 4.P2 from the datasheet figure 1. I2C 0x38.",
    custom_fp=True, block=B)
cap("C6", *C100N, "3V3", "GND", B, "AHT20 decoupling")
add("U6", "BH1750", "BH1750FVI", "NW:WSOF-6_BH1750FVI", "C78960", "BH1750FVI-TR",
    [("1", "VCC", "3V3", "L"), ("5", "DVI", "3V3", "L"), ("2", "ADDR", "GND", "L"),
     ("4", "SDA", "I2C_SDA", "R"), ("6", "SCL", "I2C_SCL", "R"), ("3", "GND", "GND", "R")],
    "ADDR low = 0x23. Pins verified against LCSC C78960 datasheet (1 VCC, 2 ADDR, 3 GND, 4 SDA, 5 DVI, 6 SCL). DVI tied to VCC directly: "
    "datasheet wants DVI low >= 1 us after VCC (RC example 1k/1uF) or a reset: OPEN POINT 7, firmware must also re-init after power-up.",
    custom_fp=True, block=B)
cap("C7", *C100N, "3V3", "GND", B, "BH1750 decoupling")
res("R13", "4.7k", "C23162", "0603WAF4701T5E", "3V3", "I2C_SDA", B,
    "ADDED by 4.P1 (BOM draft has no I2C pull-ups). LCSC number from memory: unverified")
res("R14", "4.7k", "C23162", "0603WAF4701T5E", "3V3", "I2C_SCL", B, "ADDED by 4.P1, see R13")
add("U7", "SN74LVC1G14", "SN74LVC1G14DBVR", "Package_TO_SOT_SMD:SOT-23-5", "C7835", "SN74LVC1G14DBVR",
    [("2", "A", "SOIL_PROBE", "L"), ("3", "GND", "GND", "L"), ("5", "VCC", "SOIL_PWR", "R"), ("4", "Y", "SOIL_OUT", "R"),
     ("1", "NC", "NC", "R")],
    "Schmitt oscillator; VCC from GPIO IO3 (must be held LOW in deep sleep). Sizing: hardware/soil-frontend/soil_frontend.py", block=B)
res("R12", "470k", "C23178", "0603WAF4703T5E", "SOIL_OUT", "SOIL_PROBE", B, "timing resistor, tune on the real stake (5.x)")
cap("C8", *C100N, "SOIL_PWR", "GND", B, "U7 decoupling")
add("E1", "PROBE", "Soil probe electrodes (PCB copper)", "NW:SOIL_PROBE_STAKE", "", "",
    [("1", "SENSE", "SOIL_PROBE", "L"), ("2", "REF", "GND", "R")],
    "Copper on the stake, no BOM line; layout 4.P2. Electrode ESD and wet/salty-soil loading: OPEN POINT 8",
    in_bom=False, custom_fp=True, block=B)

TITLE = "Plant Monitor board (Plan 4.P1)"
NOTES = [
    "NFR-01: best and typical case >= 3 months, worst case > 1 month (Arsany 2026-11-08). NFR-12: whole-board deep sleep <= 50 uA, target 25 uA (A-027).",
    f"R9 charge-current resistor: I = 1100/R9 = {I_CHG_MA:.0f} mA = {I_CHG_MA/CELL_MIN_MAH:.2f}C of the EEMB LP603449-PCM (A-034 decided 2026-11-08, 1000 mAh min): change CELL_MIN_MAH/R9_OHM in pcb/design.py only.",
    "Power: USB 5 V -> TP4056 -> cell (via DW01A + 8205A) = VBAT; XC6220 3.3 V LDO runs from VBAT. A-046 Option A: no power path in v1, the board needs a cell. A-045 Option A: permanent battery divider R7/R8 (no Q2/R6).",
    "Strapping: IO9 high (R5), IO8 high (R4), IO2 high (R16). Pin table: pcb/pinmap-sleep.md, must match firmware board.h (not yet in repo).",
]
