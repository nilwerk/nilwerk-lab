#!/usr/bin/env python3
"""Plant Monitor power budget and battery sizing (Plan task 2.3, NFR-01).

Python 3.11, standard library only.  Run:

    python3 power_budget.py                 # all tables as Markdown
    python3 power_budget.py --rated 1500    # life of one rated capacity (mAh)

Model (all numbers per day, battery-terminal mAh; the 3.3 V rail is an LDO, so
load current = battery current, no conversion gain or loss, only the LDO Iq):

  sleep      I_sleep(whole board) x 24 h
  sample     (24*60/interval) wakes x (boot + sense/warm-up + inference + store)
  wifi       (reports/day + critical wakes/day) sessions
             x (connect + cloud POST + hub MQTT/hub_every_n) x avg session current

Sizing rule, applied LITERALLY for every headline figure (Arsany, PR #2 item 12
and the NFR-01 row of the acceptance matrix):

    projected life = (0.8 x RATED capacity) / average current   >= NFR01_HOURS (2190 h = 3 months)

There is NO self-discharge term in that rule.  Self-discharge (fraction of RATED
capacity per month, an assumption) is computed only as a separately labelled
extra-margin figure (`with_self_discharge=True`); whether it belongs in the rule
is a question for Arsany (power-budget.md section 1).

Every parameter carries a source tag.  Tags starting with "datasheet-unverified"
are values recalled from the named datasheet and NOT read; "datasheet-read" names the
table that was read on 2026-11-07 (ESP32-C3 series datasheet v2.4 only; the module,
Aosong and ROHM datasheets are still unread); "assumption" is Emil's engineering
estimate; "edge-ai" / "ADR-012" quote the repo documents.  None is a measurement.
Task 5.4 replaces them (see power-budget.md section 9).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace

NFR01_MONTHS = 3.0           # NFR-01 (A-020: 3 months; 6 months is an information-only stretch goal)
HOURS_PER_MONTH = 730.0      # 4380 h = 6 months, 2190 h = 3 months (acceptance matrix, 5.4)
NFR01_HOURS = NFR01_MONTHS * HOURS_PER_MONTH
STRETCH_HOURS = 6 * HOURS_PER_MONTH   # 6-month stretch goal, information line only
CELL_RATED_TYP_MAH = 1100.0   # A-020: 603449 LiPo 3.7 V, typical capacity (EEMB LP603449 datasheet: 1100 nominal)
CELL_RATED_MIN_MAH = 1000.0   # A-020: minimum capacity; the NFR-01 verdict uses this (A-021)
# Cell candidates (A-034): name -> (typical mAh, MINIMUM mAh, envelope T x W x L mm, source).  The verdict uses the minimum.
CELLS = {
    "EEMB LP603449 bare cell (A-020)": (1100.0, 1000.0, (6.3, 34.5, 50.0), "EEMB datasheet, read 2026-11-07"),
    "Jauch LP503030JU+PCM+2IC+NTC (A-034 candidate)": (450.0, 430.0, (5.2, 30.0, 30.0), "Jauch datasheet LP503030JU v1.0; size from Jauch product list"),
    "Jauch LP603443JU+PCM+2 wires (DigiKey alternative)": (900.0, 850.0, (6.5, 34.5, 45.0), "Jauch datasheet 246512 Rev 1.1; size from DigiKey"),
}
BAY_MM = (51.0, 34.5, 6.3)   # A-020: cell envelope L x W x H, mm (input note for PCB outline / enclosure v3, 4.E3)
NFR12_MARGIN = 0.4            # NFR-12 limit = this share of the typical-case limit (134 uA -> 53.8), rounded down ...
NFR12_STEP_UA = 25.0          # ... to a multiple of this (uA) -> 50 uA (accepted by Arsany, A-027)
NFR12_CEILING_UA = 100.0      # absolute upper ceiling the budget would still tolerate (not the recommendation)
DERATING = 0.80               # Arsany, PR #2 item 12: rated capacity less 20 %
LOW_BATTERY_V = 3.4           # low-battery warning threshold in volts (Arsany, Needs Arsany A-008.2 answered 'ok' on PR #2, 'low-battery 3.4 V')


@dataclass(frozen=True)
class Params:
    # --- deep sleep, whole board, uA ------------------------------------
    i_mcu_sleep_ua: float
    i_ldo_iq_ua: float
    i_charger_prot_ua: float
    r_divider_mohm: float          # battery sense divider total resistance
    i_aht20_sleep_ua: float
    i_bh1750_pd_ua: float
    i_soil_gate_leak_ua: float
    # --- 15-min sample wake ---------------------------------------------
    interval_min: float
    t_boot_s: float
    t_sense_s: float               # soil warm-up + spaced samples + AHT20 + BH1750 + ADC
    t_infer_s: float               # model A + B Invoke()
    t_store_s: float               # ring-buffer write
    i_cpu_ma: float                # CPU active, radio off
    i_periph_ma: float             # soil oscillator + I2C sensors while sensing
    # --- Wi-Fi session ---------------------------------------------------
    reports_per_day: float
    critical_wakes_per_day: float
    t_connect_s: float             # association + DHCP
    t_cloud_s: float               # SNTP + TLS + POST + response
    t_hub_s: float                 # TCP + TLS + MQTT connect + QoS1 publish
    hub_every_n: float             # 1 = hub publish in every report (ADR-012)
    i_rx_ma: float                 # connected, receiving / listening, CPU on
    i_tx_ma: float                 # transmitting
    f_tx: float                    # fraction of the session spent transmitting
    # --- cell --------------------------------------------------------------
    self_discharge_pct_month: float
    usable_fraction: float         # share of derated capacity above 3.4 V (1.0 = derating covers it)
    # --- optional: soil warm-up spent in light sleep instead of CPU active --
    t_warmup_s: float = 0.0        # part of t_sense_s that is pure soil warm-up (CPU idle-able)
    i_warmup_cpu_ma: float = -1.0  # CPU current during warm-up; negative = same as i_cpu_ma (no lever)


# source tag for every field (checked by the unit test)
SOURCES: dict[str, str] = {
    "i_mcu_sleep_ua": "datasheet-read: ESP32-C3 series datasheet v2.4, Table 5-9 (p. 57), Deep-sleep RTC timer + RTC memory 5 uA typ (matches best/typical); worst 10 uA adds module flash leakage at temperature (assumption, module datasheet not read)",
    "i_ldo_iq_ua": "assumption: LDO not chosen yet (4.P1); needs a low-Iq part, an AMS1117-class LDO (mA quiescent) is excluded",
    "i_charger_prot_ua": "assumption: charger IC plus protection IC drain from BAT with USB unplugged; parts not chosen (4.P1)",
    "r_divider_mohm": "computed: I = 3.7 V / R (nominal cell voltage); R is a design choice for 4.P1, a high-side switch would give about 0",
    "i_aht20_sleep_ua": "datasheet-unverified: Aosong AHT20 datasheet, sleep current (about 0.25 uA); worst is assumption",
    "i_bh1750_pd_ua": "datasheet-unverified: ROHM BH1750FVI datasheet, power-down current (about 0.01 uA); worst is assumption",
    "i_soil_gate_leak_ua": "assumption: soil oscillator gated off by a MOSFET, leakage only",
    "interval_min": "FR-D01 / edge-ai-concept 2.1: wake every 15 min",
    "t_boot_s": "assumption: ESP32-C3 wake from deep sleep to app_main; measure in 5.4",
    "t_sense_s": "edge-ai-concept 2.4: warm-up >= 1.5 s, sensor warm-up and samples about 2-3 s (estimate)",
    "t_infer_s": "edge-ai-concept 2.2/2.3: model A under 1 ms, model B a few ms (estimates), limit 50 ms (FR-E04)",
    "t_store_s": "assumption: one flash ring-buffer append",
    "i_cpu_ma": "datasheet-read: ESP32-C3 series datasheet v2.4, Table 5-8 (p. 57), Modem-sleep CPU running 160 MHz: 23 mA typ (peripheral clocks off) / 28 mA (on); model values 15/20/30 are below the datasheet in best and typical (not changed here, see verified-currents.md what-if)",
    "i_periph_ma": "assumption: soil oscillator about a few mA plus AHT20 (datasheet-unverified, tens of uA) and BH1750 (datasheet-unverified, about 0.12 mA)",
    "reports_per_day": "FR-D02: hourly report, 24 per day",
    "critical_wakes_per_day": "edge-ai-concept 2.4: max 1 per class per 6 h; 4 critical classes; typical and worst are assumptions",
    "t_connect_s": "assumption: to be measured; edge-ai-concept 2.4 estimates association + TLS + POST together at 3-10 s",
    "t_cloud_s": "assumption: to be measured (see t_connect_s)",
    "t_hub_s": "ADR-012: +1 s awake for the hub publish (unmeasured); best/worst are assumptions",
    "hub_every_n": "ADR-012: hub publish with every report; 2 is the ADR-012 fallback",
    "i_rx_ma": "datasheet-read: ESP32-C3 series datasheet v2.4, Table 5-7 (p. 56), RX 802.11b/g/n HT20 84 mA, HT40 87 mA (peak); model best 70 is below the datasheet; ADR-012 assumes about 100 mA",
    "i_tx_ma": "datasheet-read: ESP32-C3 series datasheet v2.4, Table 5-7 (p. 56), TX peak 335 mA (11b 1 Mbps @21 dBm), 285 (11g 54M @19 dBm), 276 (11n MCS7 @18.5 dBm), 100 % duty at 3.3 V; model best 200 is below the datasheet at maximum power (lower TX power settings are not tabulated)",
    "f_tx": "assumption: share of the session spent transmitting; measure in 5.4",
    "self_discharge_pct_month": "assumption: commonly quoted LiPo figure of 1-3 % per month, no datasheet read; cell not chosen",
    "t_warmup_s": "edge-ai-concept 2.4: warm-up >= 1.5 s (best/worst are assumptions); the share of t_sense_s in which the CPU only waits",
    "i_warmup_cpu_ma": "assumption: default = i_cpu_ma (CPU busy-waits, the model baseline); the light-sleep lever sets an assumption (datasheet-unverified: ESP32-C3 light-sleep current, order of 0.1-1 mA incl. peripherals; measure in M3)",
    "usable_fraction": "assumption: the 20 % derating is taken to cover capacity unusable below 3.4 V; to be checked in 5.4 with a discharge curve at the real load",
}

BEST = Params(5, 1, 1, 4.0, 0.25, 0.01, 0.1,
              15, 0.15, 1.5, 0.002, 0.02, 15, 1.5,
              24, 0, 1.0, 0.8, 0.5, 1, 70, 200, 0.03,
              1.0, 1.0, 1.0)
TYPICAL = Params(5, 2, 4, 2.0, 0.25, 0.01, 0.1,
                 15, 0.30, 2.5, 0.010, 0.05, 20, 3.5,
                 24, 1, 2.5, 2.0, 1.0, 1, 85, 260, 0.08,
                 2.0, 1.0, 1.5)
WORST = Params(10, 5, 10, 1.0, 1.0, 1.0, 1.0,
               15, 0.60, 3.0, 0.050, 0.10, 30, 7.0,
               24, 4, 6.0, 5.0, 3.0, 1, 100, 340, 0.15,
               3.0, 1.0, 2.0)
SCENARIOS = {"best": BEST, "typical": TYPICAL, "worst": WORST}


# --------------------------------------------------------------------------
def sleep_current_ua(p: Params, v_batt: float = 3.7) -> float:
    """Whole-board deep-sleep current in uA (battery terminal, USB unplugged)."""
    divider = v_batt / p.r_divider_mohm          # V / MOhm = uA
    return (p.i_mcu_sleep_ua + p.i_ldo_iq_ua + p.i_charger_prot_ua + divider
            + p.i_aht20_sleep_ua + p.i_bh1750_pd_ua + p.i_soil_gate_leak_ua)


def wifi_avg_ma(p: Params) -> float:
    return p.f_tx * p.i_tx_ma + (1.0 - p.f_tx) * p.i_rx_ma


def wifi_session_s(p: Params) -> float:
    return p.t_connect_s + p.t_cloud_s + p.t_hub_s / p.hub_every_n


def sample_wake_mas(p: Params) -> float:
    """Charge of one 15-min sample wake in mA*s."""
    warm = min(p.t_warmup_s, p.t_sense_s)
    i_warm = p.i_cpu_ma if p.i_warmup_cpu_ma < 0 else p.i_warmup_cpu_ma
    return ((p.t_boot_s + p.t_infer_s + p.t_store_s) * p.i_cpu_ma
            + (p.t_sense_s - warm) * (p.i_cpu_ma + p.i_periph_ma)
            + warm * (i_warm + p.i_periph_ma))


def wifi_session_mas(p: Params) -> float:
    return wifi_session_s(p) * wifi_avg_ma(p)


def daily_budget(p: Params) -> dict[str, float]:
    """Load charge per day in mAh by contributor (no self-discharge)."""
    wakes = 24 * 60 / p.interval_min
    sessions = p.reports_per_day + p.critical_wakes_per_day
    sleep = sleep_current_ua(p) / 1000.0 * 24.0
    sample = wakes * sample_wake_mas(p) / 3600.0
    wifi = sessions * wifi_session_mas(p) / 3600.0
    return {"sleep": sleep, "sample": sample, "wifi": wifi,
            "total": sleep + sample + wifi}


def avg_current_ma(p: Params) -> float:
    """Average battery current over a day in mA (no self-discharge)."""
    return daily_budget(p)["total"] / 24.0


def _sd_fraction(p: Params, hours: float) -> float:
    return p.self_discharge_pct_month / 100.0 * (hours / 730.0)


def required_rated_mah(p: Params, hours: float = NFR01_HOURS,
                       derating: float = DERATING, with_self_discharge: bool = False) -> float:
    """Smallest RATED capacity (mAh) with derating*C / I_avg >= `hours`.

    Default = Arsany's rule literally (no self-discharge).  with_self_discharge=True
    is the extra-margin figure: the cell's own loss (fraction of C per month) is
    subtracted from the usable share."""
    load = daily_budget(p)["total"] * hours / 24.0
    sd = _sd_fraction(p, hours) if with_self_discharge else 0.0
    avail = derating * p.usable_fraction - sd
    if avail <= 0:
        return float("inf")
    return load / avail


def life_days(p: Params, rated_mah: float, derating: float = DERATING,
              with_self_discharge: bool = False) -> float:
    """Days until the derated capacity is used up: derating*C / I_avg (rule);
    with_self_discharge=True adds the cell's own loss per day (extra margin)."""
    per_day = daily_budget(p)["total"]
    if with_self_discharge:
        per_day += p.self_discharge_pct_month / 100.0 * rated_mah / 30.4167
    return derating * p.usable_fraction * rated_mah / per_day


def max_sleep_current_ua(p: Params, rated_mah: float, hours: float = NFR01_HOURS,
                         derating: float = DERATING, with_self_discharge: bool = False) -> float:
    """Largest whole-board deep-sleep current (uA) for which `rated_mah` still
    reaches `hours`, every other parameter as in `p`.  Negative: cannot reach."""
    sd = _sd_fraction(p, hours) if with_self_discharge else 0.0
    budget_mah = (derating * p.usable_fraction - sd) * rated_mah
    d = daily_budget(p)
    other_per_day = d["sample"] + d["wifi"]
    return (budget_mah / (hours / 24.0) - other_per_day) / 24.0 * 1000.0


def derated_hours(p: Params, rated_mah: float, derating: float = DERATING) -> float:
    """NFR-01 verdict figure in hours: derating x RATED capacity / average current (literal rule)."""
    return derating * p.usable_fraction * rated_mah / avg_current_ma(p)


def nfr12_limit_ua(p: Params = None, rated_mah: float = CELL_RATED_MIN_MAH,
                   margin: float = NFR12_MARGIN, step_ua: float = NFR12_STEP_UA) -> float:
    """NFR-12 whole-board deep-sleep limit (uA), derived, not chosen:
    margin x (largest sleep current at which `rated_mah` still reaches NFR01_HOURS
    with the TYPICAL sample/Wi-Fi terms), rounded down to a multiple of step_ua."""
    import math
    raw = max_sleep_current_ua(TYPICAL if p is None else p, rated_mah) * margin
    return max(0.0, math.floor(raw / step_ua) * step_ua)


def with_(p: Params, **kw: float) -> Params:
    return replace(p, **kw)


# --------------------------------------------------------------------------
# Markdown report
CAPACITIES = (500, 750, 1000, 1100, 1500, 2000, 2500, 3000)   # rated values; 1000 / 1100 are the A-020 cell (min / typ), the rest generic


def _row(cells) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _table(head, rows) -> str:
    return "\n".join([_row(head), _row(["---"] * len(head))] + [_row(r) for r in rows])


MONTH_DAYS = 30.4167
SD = {"with_self_discharge": True}

LEVERS = [
    ("base (typical)", {}),
    ("light sleep during the soil warm-up (CPU 0.5 mA instead of 20 mA for 1.5 s, assumption)",
     {"i_warmup_cpu_ma": 0.5}),
    ("hub publish every 2nd report (ADR-012 fallback)", {"hub_every_n": 2}),
    ("no hub publish at all (cloud only)", {"t_hub_s": 0.0}),
    ("fast connect: cached BSSID/channel + static IP (connect 1.0 s)", {"t_connect_s": 1.0}),
    ("fast connect + hub every 2nd report (session 3.5 s)", {"t_connect_s": 1.0, "hub_every_n": 2}),
    ("fast connect + hub every 2nd + light-sleep warm-up",
     {"t_connect_s": 1.0, "hub_every_n": 2, "i_warmup_cpu_ma": 0.5}),
    ("hub unreachable every hour: 3 s timeout (Theo's review of ADR-012), hub tried every report",
     {"t_hub_s": 3.0}),
    ("hub unreachable, plus 1 s mDNS fallback lookup (assumption)", {"t_hub_s": 4.0}),
    ("hub unreachable, back-off: hub tried every 4th report only", {"t_hub_s": 3.0, "hub_every_n": 4}),
    ("30-min sampling (O-1 fallback)", {"interval_min": 30}),
    ("critical wakes at the rate-limit cap (16/day)", {"critical_wakes_per_day": 16}),
    ("no critical wakes", {"critical_wakes_per_day": 0}),
]

HEADINGS = {
    "scenarios": "### Scenario results\n",
    "life": "### Life in months per rated capacity (rule: 0.8 x rated / average current; +SD = extra-margin line with self-discharge)\n",
    "sleep_limit": "### Deep-sleep limit (whole board) that still reaches NFR-01 (3 months), uA (rule; +SD = extra-margin line)\n",
    "cell": f"### A-020 cell (603449, 1S LiPo): NFR-01 verdict at {NFR01_HOURS:.0f} h\n",
    "cells": f"### Cell candidates against NFR-01 ({NFR01_HOURS:.0f} h), minimum rated capacity (A-021 rule)\n",
    "nfr12": "### Derived NFR-12 sleep-current limit (A-020 cell)\n",
    "sensitivity": "### Sensitivity, one parameter at a time around TYPICAL\n",
    "levers": "### What-if levers (TYPICAL as base)\n",
}


def report_sections() -> dict[str, str]:
    """Generated tables by name; power-budget.md embeds each between
    <!-- BEGIN:name --> and <!-- END:name --> and a test keeps them identical."""
    sec: dict[str, str] = {}
    rows = []
    for n, p in SCENARIOS.items():
        d = daily_budget(p)
        rows.append([n, f"{sleep_current_ua(p):.1f}", f"{d['sleep']:.2f}", f"{d['sample']:.2f}",
                     f"{d['wifi']:.2f}", f"{d['total']:.2f}",
                     f"{d['total'] * NFR01_HOURS / 24:.0f}",
                     f"{required_rated_mah(p):.0f}",
                     f"{required_rated_mah(p, **SD):.0f}"])
    sec["scenarios"] = _table(
        ["case", "sleep uA", "sleep mAh/d", "sample mAh/d", "Wi-Fi mAh/d", "total mAh/d",
         f"load {NFR01_HOURS:.0f} h mAh", "rated mAh needed (rule)", "extra: rated mAh incl. self-disch."], rows)

    rows = []
    for c in CAPACITIES:
        rows.append([c, f"{DERATING * c:.0f}"]
                    + [f"{life_days(p, c) / MONTH_DAYS:.1f}" for p in SCENARIOS.values()]
                    + [f"{life_days(p, c, **SD) / MONTH_DAYS:.1f}" for p in SCENARIOS.values()])
    sec["life"] = _table(
        ["rated mAh", "derated mAh", "best (rule)", "typical (rule)", "worst (rule)",
         "best +SD", "typical +SD", "worst +SD"], rows)

    rows = []
    for c in CAPACITIES:
        rows.append([c] + [f"{max_sleep_current_ua(p, c):.0f}" for p in SCENARIOS.values()]
                    + [f"{max_sleep_current_ua(p, c, **SD):.0f}" for p in SCENARIOS.values()])
    sec["sleep_limit"] = _table(
        ["rated mAh", "best (rule)", "typical (rule)", "worst (rule)",
         "best +SD", "typical +SD", "worst +SD"], rows)

    sweeps = [
        ("Wi-Fi connect time s (t_connect_s)", "t_connect_s", (1.0, 2.5, 4.0, 6.0, 10.0)),
        ("Deep-sleep current uA (MCU term; whole board = this + 8.2)", "i_mcu_sleep_ua", (5, 10, 25, 50, 100)),
        ("TX current mA (i_tx_ma)", "i_tx_ma", (200, 260, 340)),
    ]
    out: list[str] = []
    for title, key, vals in sweeps:
        rows = []
        for v in vals:
            p = with_(TYPICAL, **{key: v})
            d = daily_budget(p)
            rows.append([v, f"{sleep_current_ua(p):.1f}", f"{d['total']:.2f}", f"{required_rated_mah(p):.0f}",
                         f"{life_days(p, 1500) / MONTH_DAYS:.1f}",
                         f"{life_days(p, 1500, **SD) / MONTH_DAYS:.1f}"])
        out.append(f"**{title}**\n")
        out.append(_table(["value", "board sleep uA", "mAh/day", "rated mAh needed (rule)",
                           "months @1500 mAh (rule)", "extra: months @1500 incl. SD"], rows))
        out.append("")
    sec["sensitivity"] = "\n".join(out).rstrip()

    rows = []
    for name, kw in LEVERS:
        p = with_(TYPICAL, **kw)
        rows.append([name, f"{daily_budget(p)['total']:.2f}", f"{wifi_session_s(p):.1f}",
                     f"{required_rated_mah(p):.0f}", f"{required_rated_mah(p, **SD):.0f}"])
    sec["levers"] = _table(["lever", "mAh/day", "Wi-Fi session s", "rated mAh needed (rule)",
                            "extra: incl. self-disch."], rows)

    rows = []
    for cap_name, cap in (("minimum (verdict, A-021)", CELL_RATED_MIN_MAH), ("typical (info only)", CELL_RATED_TYP_MAH)):
        for n, p in SCENARIOS.items():
            h = derated_hours(p, cap)
            hs = life_days(p, cap, **SD) * 24
            rows.append([f"{cap:.0f} mAh {cap_name}", n, f"{DERATING * cap:.0f}", f"{avg_current_ma(p) * 1000:.0f}",
                         f"{h:.0f}", f"{h / HOURS_PER_MONTH:.1f}",
                         "PASS" if h >= NFR01_HOURS else "FAIL", f"{hs / HOURS_PER_MONTH:.1f}"])
    sec["cell"] = _table(["cell capacity", "case", "derated mAh", "average uA", "life h (rule)",
                          "months (rule)", f"vs {NFR01_HOURS:.0f} h", "extra: months incl. SD"], rows)

    rows = []
    for n, p in SCENARIOS.items():
        lim = max_sleep_current_ua(p, CELL_RATED_MIN_MAH)
        rows.append([n, f"{sleep_current_ua(p):.1f}", f"{lim:.0f}",
                     f"{lim / sleep_current_ua(p):.1f}" if lim > 0 else "n/a (cannot reach)"])
    rows.append([f"**NFR-12 limit** = floor({NFR12_MARGIN:g} x typical limit to {NFR12_STEP_UA:g} uA)",
                 "", f"**{nfr12_limit_ua():.0f}**", f"{nfr12_limit_ua() / sleep_current_ua(TYPICAL):.1f}"])
    crows = []   # own variable per table: never reuse `rows` (it clobbered the NFR-12 table once)
    for name, (typ, mn, (t, w, l), _src) in CELLS.items():
        ht, hb, hw = (derated_hours(p, mn) / HOURS_PER_MONTH for p in (TYPICAL, BEST, WORST))
        fits = t <= BAY_MM[2] and w <= BAY_MM[1] and l <= BAY_MM[0]
        crows.append([name, f"{typ:.0f}", f"{mn:.0f}", f"{t:g} x {w:g} x {l:g}", "yes" if fits else "no, thicker: input to Yara",
                     f"{hb:.1f}", f"{ht:.1f}", f"{hw:.1f}", "PASS" if ht * HOURS_PER_MONTH >= NFR01_HOURS else "FAIL",
                     f"{max_sleep_current_ua(TYPICAL, mn):.0f}"])
    sec["cells"] = _table(["cell", "typ mAh", "MIN mAh", "T x W x L mm", "fits 51 x 34.5 x 6.3", "months best",
                           "months typical", "months worst", "NFR-01 typical", "max sleep uA (typical terms)"], crows)
    sec["nfr12"] = _table(["case (other terms as in the case)", "board sleep estimate uA",
                           f"max sleep uA for {CELL_RATED_MIN_MAH:.0f} mAh rated, {NFR01_HOURS:.0f} h",
                           "limit / estimate"], rows)
    return sec


def report() -> str:
    return "\n".join(f"{HEADINGS[k]}\n{v}\n" for k, v in report_sections().items())


def update_doc(path: str) -> None:
    """Rewrite the <!-- BEGIN:name --> ... <!-- END:name --> blocks of the doc."""
    import re
    text = open(path, encoding="utf-8").read()
    for name, body in report_sections().items():
        pat = re.compile(rf"(<!-- BEGIN:{name} -->\n).*?(<!-- END:{name} -->)", re.S)
        text, n = pat.subn(lambda m: m.group(1) + body + "\n" + m.group(2), text)
        if n != 1:
            raise SystemExit(f"marker {name} not found exactly once in {path}")
    open(path, "w", encoding="utf-8").write(text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rated", type=float, help="rated capacity in mAh to evaluate")
    ap.add_argument("--update-doc", metavar="MD", help="regenerate the table blocks in power-budget.md")
    a = ap.parse_args()
    if a.update_doc:
        update_doc(a.update_doc)
    elif a.rated:
        for n, p in SCENARIOS.items():
            print(f"{n}: {life_days(p, a.rated) / MONTH_DAYS:.1f} months (rule), "
                  f"{life_days(p, a.rated, **SD) / MONTH_DAYS:.1f} months incl. self-discharge (extra), "
                  f"sleep limit {max_sleep_current_ua(p, a.rated):.0f} uA (rule)")
    else:
        print(report())


if __name__ == "__main__":
    main()
