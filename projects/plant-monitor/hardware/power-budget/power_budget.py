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
  self-disch. fraction of RATED capacity per month x months (LiPo cell loss)

Sizing rule (Arsany, PR #2 item 12): the RATED capacity of the chosen 1S LiPo
is derated by 20 %.  Required: derating * C_rated >= load energy + self-discharge,
for NFR-01 = 6 months = 4380 h (acceptance matrix 5.4 arithmetic).

Every parameter carries a source tag.  Tags starting with "datasheet-unverified"
are values recalled from the named datasheet and NOT read in this session (the
session network blocks espressif.com); "assumption" is Emil's engineering
estimate; "edge-ai" / "ADR-012" quote the repo documents.  None is a measurement.
Task 5.4 replaces them (see power-budget.md section 7).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace

NFR01_HOURS = 4380.0          # 6 months, as used in the acceptance matrix (5.4)
DERATING = 0.80               # Arsany, PR #2 item 12: rated capacity less 20 %
LOW_BATTERY_V = 3.4           # low-battery warning threshold in volts (task brief, Arsany)


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


# source tag for every field (checked by the unit test)
SOURCES: dict[str, str] = {
    "i_mcu_sleep_ua": "datasheet-unverified: ESP32-C3 series datasheet, low-power current table, deep sleep with RTC timer (about 5 uA); worst adds module flash leakage at temperature (assumption)",
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
    "i_cpu_ma": "datasheet-unverified: ESP32-C3 series datasheet, active current, CPU 160 MHz, radio off (about 20 mA)",
    "i_periph_ma": "assumption: soil oscillator about a few mA plus AHT20 (datasheet-unverified, tens of uA) and BH1750 (datasheet-unverified, about 0.12 mA)",
    "reports_per_day": "FR-D02: hourly report, 24 per day",
    "critical_wakes_per_day": "edge-ai-concept 2.4: max 1 per class per 6 h; 4 critical classes; typical and worst are assumptions",
    "t_connect_s": "assumption: to be measured; edge-ai-concept 2.4 estimates association + TLS + POST together at 3-10 s",
    "t_cloud_s": "assumption: to be measured (see t_connect_s)",
    "t_hub_s": "ADR-012: +1 s awake for the hub publish (unmeasured); best/worst are assumptions",
    "hub_every_n": "ADR-012: hub publish with every report; 2 is the ADR-012 fallback",
    "i_rx_ma": "datasheet-unverified: ESP32-C3 series datasheet, Wi-Fi RX current (order of 80-100 mA); ADR-012 assumes about 100 mA",
    "i_tx_ma": "datasheet-unverified: ESP32-C3 series datasheet, Wi-Fi TX current by rate and power (order of 200-340 mA)",
    "f_tx": "assumption: share of the session spent transmitting; measure in 5.4",
    "self_discharge_pct_month": "assumption: commonly quoted LiPo figure of 1-3 % per month, no datasheet read; cell not chosen",
    "usable_fraction": "assumption: the 20 % derating is taken to cover capacity unusable below 3.4 V; to be checked in 5.4 with a discharge curve at the real load",
}

BEST = Params(5, 1, 1, 4.0, 0.25, 0.01, 0.1,
              15, 0.15, 1.5, 0.002, 0.02, 15, 1.5,
              24, 0, 1.0, 0.8, 0.5, 1, 70, 200, 0.03,
              1.0, 1.0)
TYPICAL = Params(5, 2, 4, 2.0, 0.25, 0.01, 0.1,
                 15, 0.30, 2.5, 0.010, 0.05, 20, 3.5,
                 24, 1, 2.5, 2.0, 1.0, 1, 85, 260, 0.08,
                 2.0, 1.0)
WORST = Params(10, 5, 10, 1.0, 1.0, 1.0, 1.0,
               15, 0.60, 3.0, 0.050, 0.10, 30, 7.0,
               24, 4, 6.0, 5.0, 3.0, 1, 100, 340, 0.15,
               3.0, 1.0)
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
    return ((p.t_boot_s + p.t_infer_s + p.t_store_s) * p.i_cpu_ma
            + p.t_sense_s * (p.i_cpu_ma + p.i_periph_ma))


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


def required_rated_mah(p: Params, hours: float = NFR01_HOURS,
                       derating: float = DERATING, with_self_discharge: bool = True) -> float:
    """Smallest RATED capacity (mAh) such that derating*usable*C covers the load
    for `hours` plus self-discharge of the cell (fraction of C per month)."""
    load = daily_budget(p)["total"] * hours / 24.0
    sd = p.self_discharge_pct_month / 100.0 * (hours / 730.0) if with_self_discharge else 0.0
    avail = derating * p.usable_fraction - sd
    if avail <= 0:
        return float("inf")
    return load / avail


def life_days(p: Params, rated_mah: float, derating: float = DERATING) -> float:
    """Days until the derated capacity is used up (load + self-discharge)."""
    per_day = daily_budget(p)["total"] + p.self_discharge_pct_month / 100.0 * rated_mah / 30.4167
    return derating * p.usable_fraction * rated_mah / per_day


def max_sleep_current_ua(p: Params, rated_mah: float, hours: float = NFR01_HOURS,
                         derating: float = DERATING) -> float:
    """Largest whole-board deep-sleep current (uA) for which `rated_mah` still
    reaches `hours`, every other parameter as in `p`.  Negative: cannot reach."""
    budget_mah = (derating * p.usable_fraction
                  - p.self_discharge_pct_month / 100.0 * hours / 730.0) * rated_mah
    d = daily_budget(p)
    other_per_day = d["sample"] + d["wifi"]
    return (budget_mah / (hours / 24.0) - other_per_day) / 24.0 * 1000.0


def with_(p: Params, **kw: float) -> Params:
    return replace(p, **kw)


# --------------------------------------------------------------------------
# Markdown report
CAPACITIES = (500, 750, 1000, 1500, 2000, 2500, 3000)   # generic rated values, not products


def _row(cells) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _table(head, rows) -> str:
    return "\n".join([_row(head), _row(["---"] * len(head))] + [_row(r) for r in rows])


def report() -> str:
    out: list[str] = []
    out.append("### Scenario results\n")
    rows = []
    for n, p in SCENARIOS.items():
        d = daily_budget(p)
        rows.append([n, f"{sleep_current_ua(p):.1f}", f"{d['sleep']:.2f}", f"{d['sample']:.2f}",
                     f"{d['wifi']:.2f}", f"{d['total']:.2f}",
                     f"{d['total'] * NFR01_HOURS / 24:.0f}",
                     f"{required_rated_mah(p, with_self_discharge=False):.0f}",
                     f"{required_rated_mah(p):.0f}"])
    out.append(_table(["case", "sleep uA", "sleep mAh/d", "sample mAh/d", "Wi-Fi mAh/d", "total mAh/d",
                       "load 4380 h mAh", "rated mAh (no self-disch.)", "rated mAh needed"], rows))

    out.append("\n### Life in months per rated capacity (derated 80 %, self-discharge included)\n")
    rows = []
    for c in CAPACITIES:
        rows.append([c, f"{DERATING * c:.0f}"] + [f"{life_days(p, c) / 30.4167:.1f}" for p in SCENARIOS.values()])
    out.append(_table(["rated mAh", "derated mAh", "best", "typical", "worst"], rows))

    out.append("\n### Deep-sleep limit (whole board) that still reaches 6 months, uA\n")
    rows = []
    for c in CAPACITIES:
        rows.append([c] + [f"{max_sleep_current_ua(p, c):.0f}" for p in SCENARIOS.values()])
    out.append(_table(["rated mAh", "other terms best", "other terms typical", "other terms worst"], rows))

    out.append("\n### Sensitivity, one parameter at a time around TYPICAL\n")
    sweeps = [
        ("Wi-Fi connect time s (t_connect_s)", "t_connect_s", (1.0, 2.5, 4.0, 6.0, 10.0)),
        ("Deep-sleep current uA (MCU term; whole board = this + 8.2)", "i_mcu_sleep_ua", (5, 10, 25, 50, 100)),
        ("TX current mA (i_tx_ma)", "i_tx_ma", (200, 260, 340)),
    ]
    for title, key, vals in sweeps:
        rows = []
        for v in vals:
            p = with_(TYPICAL, **{key: v})
            d = daily_budget(p)
            rows.append([v, f"{sleep_current_ua(p):.1f}", f"{d['total']:.2f}", f"{required_rated_mah(p):.0f}",
                         f"{life_days(p, 1500) / 30.4167:.1f}"])
        out.append(f"**{title}**\n")
        out.append(_table(["value", "board sleep uA", "mAh/day", "rated mAh needed", "months @1500 mAh"], rows))
        out.append("")

    out.append("### What-if levers (TYPICAL as base)\n")
    levers = [
        ("base (typical)", {}),
        ("hub publish every 2nd report (ADR-012 fallback)", {"hub_every_n": 2}),
        ("no hub publish at all (cloud only)", {"t_hub_s": 0.0}),
        ("fast connect: cached BSSID/channel + static IP (connect 1.0 s)", {"t_connect_s": 1.0}),
        ("30-min sampling (O-1 fallback)", {"interval_min": 30}),
        ("critical wakes at the rate-limit cap (16/day)", {"critical_wakes_per_day": 16}),
        ("no critical wakes", {"critical_wakes_per_day": 0}),
    ]
    rows = []
    for name, kw in levers:
        p = with_(TYPICAL, **kw)
        rows.append([name, f"{daily_budget(p)['total']:.2f}", f"{required_rated_mah(p):.0f}"])
    out.append(_table(["lever", "mAh/day", "rated mAh needed"], rows))
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rated", type=float, help="rated capacity in mAh to evaluate")
    a = ap.parse_args()
    if a.rated:
        for n, p in SCENARIOS.items():
            print(f"{n}: {life_days(p, a.rated) / 30.4167:.1f} months, "
                  f"sleep limit {max_sleep_current_ua(p, a.rated):.0f} uA")
    else:
        print(report())


if __name__ == "__main__":
    main()
