"""Tests for Architect conditions C1-C6 (PR #13 slice 2 review). SYNTHETIC data only.
Traces to: FR-E01, FR-E04, FR-D05 (OTA changes RTC layout), NFR-01, NFR-02.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import export as E
import features as F

ROOT = Path(__file__).resolve().parents[1]


def test_c1_cold_boot_and_invalid_rtc_give_saturated_counter():          # C1(a)(b)
    for blob in (None, b"", b"\x01" * 11):
        tr = F.EventTracker.from_rtc(blob)
        assert tr.since == F.HORIZON_TICKS and tr.hist == []


def test_c1_rtc_roundtrip_and_corruption():                               # C1(b)
    tr = F.EventTracker()
    for m in (10, 10, 30, 31, 31):
        tr.step(m)
    blob = tr.to_rtc()
    assert len(blob) == 11
    r = F.EventTracker.from_rtc(blob)
    assert (r.hist, r.prev_rise, r.since) == (tr.hist, tr.prev_rise, tr.since)
    bad_crc = bytearray(blob); bad_crc[5] ^= 0x01
    assert F.EventTracker.from_rtc(bytes(bad_crc)).since == F.HORIZON_TICKS
    bad_ver = bytearray(blob); bad_ver[0] = 2                              # OTA layout change
    assert F.EventTracker.from_rtc(bytes(bad_ver)).since == F.HORIZON_TICKS


def test_c1_failed_read_still_advances_counter():                          # C1(c)
    tr = F.EventTracker()
    tr.step(10); tr.step(10); tr.step(30)
    assert tr.since == 0
    tr.step(0, valid=False)
    tr.step(0, valid=False)
    assert tr.since == 2


def test_c1_no_forecast_until_96_samples():                                # C1(a)
    assert not F.forecast_ready(95) and F.forecast_ready(96)


def test_c2_capped_forecast_is_72_never_null():
    assert F.forecast_h_from_model(500.0) == 72.0 and F.forecast_h_from_model(72.0) == 72.0
    assert F.forecast_h_from_model(-3) == 0.0 and F.forecast_h_from_model(10.5) == 10.5
    assert F.forecast_h_from_model(1e9) is not None


def test_c3_lux_mapping_and_pinned_placeholders():
    assert F.lux_to_light_u8(0) == 0 and F.lux_to_light_u8(100000) == 255 and F.lux_to_light_u8(1) == 16
    assert F.lux_to_light_u8(-5) == 0
    f = E.build_features(_seg())
    assert not f["light_known"].iloc[0] and (f["m_u8"].notna().all())


def test_c4_soil_code_function_of_soil_type_only():
    exp = {"potting": 1, "peat": 1, "other": 1, "garden": 2, "sand": 2, "clay": 2}
    assert {k: F.soil_code(k) for k in exp} == exp
    assert F.soil_code("nonsense") == 0


def test_c4_local_minute_of_day_wraps():
    assert F.local_minute_of_day(23 * 60 + 30, 120) == 90
    assert F.local_minute_of_day(30, -60) == 1410


def test_c5_converter_input_quant_is_identity():
    assert (F.FEATURE_INPUT_SCALE, F.FEATURE_INPUT_ZERO_POINT) == (1.0, 0)


def _seg():
    t = pd.date_range("2025-03-03", periods=400, freq="15min")
    k = np.arange(len(t))
    m = 80 - (k % 100) * 0.6
    return pd.DataFrame({"time": t, "m": m, "plant": "a", "source": "mendeley", "segment": 0})


def test_c6_event_agreement_reports_rate():
    r = E.event_agreement(_seg())
    assert r["label_events"] >= 3 and 0.0 <= r["agreement_rate"] <= 1.0
    assert r["matched"] == r["label_events"] == r["device_events"]          # clean synthetic sawtooth: full agreement


def test_golden_file_matches_generator():                                   # QA note: drift test
    gp = ROOT / "tests" / "golden" / "features_golden.json"
    before = json.loads(gp.read_text())
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_golden.py")], check=True, cwd=ROOT)
    after = json.loads(gp.read_text())
    assert before == after
