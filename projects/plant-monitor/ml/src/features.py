"""Device-side feature pipeline for Model A (thirst forecast), integer / int8 friendly.

Implements docs/edge-ai-concept.md section 2.1 (shared device-side feature pipeline) and the 14 Model A
inputs of section 2.2. Traces to FR-E01 (thirst forecast), FR-E04 (runs on device: int8, <20 KB RAM, <50 ms),
NFR-01 (15-min wake cadence, deep sleep), NFR-02 (relative moisture from per-device calibration).

Everything below is integer arithmetic only (no float, no libm) so the same code can be ported 1:1 to C.
C port notes (for 4.AI2/4.F-series):
  * `>>` on negative values is an arithmetic shift (floor); gcc/riscv32 do this, and Python does it by definition.
  * all intermediates fit int32 (worst case 512 * sum(x2*y) ~ 2.4e8 < 2^31).
  * sin/cos of the hour come from a literal table, not from a libm call.
The golden vectors in tests/golden/features_golden.json are the contract between this file and the C port.

SYNTHETIC-ONLY STATUS: nothing in here has been run on real data (dataset hosts blocked, A-007).

Device sample formats (history ring buffer, 96 samples = 24 h at 15 min, concept 2.1):
    m_u8     uint8  relative moisture 0..100 (round half up of the 0-100 value, NFR-02 calibration)
    temp_u8  uint8  temperature in whole degC + TEMP_OFFSET (so -20 .. 235 degC representable)
    light_u8 uint8  log-compressed light level (already compressed on the device; "log light" of the concept)
Feature vector: 14 int8 values, order FEATURE_NAMES, scale/zero-point in FEATURE_SPEC.
"""
from __future__ import annotations

import numpy as np

# ---- constants (each one is a documented parameter, not a result)
HIST = 96                    # samples kept = 24 h at 15 min (FR-E01, concept 2.1)
W_1H, W_6H, W_24H = 4, 24, 96  # slope windows in samples: last 4 / 24 / 96 samples (<= HIST)
LIGHT_WINDOW = 24            # 6 h light mean (concept 2.2)
HORIZON_TICKS = 288          # 72 h at 15 min = FR-E01 horizon; also cap of "hours since event"
TEMP_OFFSET = 20             # temp_u8 = degC + 20
RISE_PTS = 10                # wetting detector: m[t] - m[t-RISE_WINDOW] >= RISE_PTS (same as prep.label_events)
RISE_WINDOW = 2
REFRACTORY = 8               # ticks; an onset within 8 ticks of the last onset is suppressed
DEFAULT_T = 25               # default dry threshold, relative points (Arsany G1 answer 10); a DB field
SOIL_CODES = {"unknown": 0, "pot": 1, "garden": 2}  # FR-A04 soil code, one value (0 = unknown/reserved)
# Architect C4 (PR #13): the code is a function of db-schema plants.soil_type ONLY; the server computes it and
# pushes config.soil_code. potting/peat/other -> 1 (pot), garden/sand/clay -> 2 (garden).
SOIL_TYPE_TO_CODE = {"potting": 1, "peat": 1, "other": 1, "garden": 2, "sand": 2, "clay": 2}
FORECAST_CAPPED_H = 72.0     # Architect C2: forecast_h = 72 means "72 h or more"; null = no forecast yet (never for capped)
FEATURE_INPUT_SCALE, FEATURE_INPUT_ZERO_POINT = 1.0, 0   # Architect C5: required converter input quant for 4.AI2

FEATURE_NAMES = ("m_now", "slope_1h", "slope_6h", "slope_24h", "m_min_24h", "m_max_24h", "temp_now",
                 "temp_mean_24h", "light_mean_6h", "sin_hour", "cos_hour", "T", "hours_since_event", "soil")
# int8 = clip(value_in_unit - zero_point); unit documented per feature. slope units: 1/2, 1/8, 1/16 pp/h.
FEATURE_SPEC = {
    "m_now": ("pp", 50), "slope_1h": ("1/2 pp/h", 0), "slope_6h": ("1/8 pp/h", 0), "slope_24h": ("1/16 pp/h", 0),
    "m_min_24h": ("pp", 50), "m_max_24h": ("pp", 50), "temp_now": ("degC", 0), "temp_mean_24h": ("degC", 0),
    "light_mean_6h": ("log level", 128), "sin_hour": ("1/127", 0), "cos_hour": ("1/127", 0), "T": ("pp", 50),
    "hours_since_event": ("h", 0), "soil": ("code", 0),
}

# round(127 * sin(2*pi*h/24)) for h = 0..23; cos(h) = SIN[(h + 6) % 24]. Literal table (no libm on device).
SIN_HOUR = (0, 33, 64, 90, 110, 123, 127, 123, 110, 90, 64, 33, 0, -33, -64, -90, -110, -123, -127, -123,
            -110, -90, -64, -33)


# --------------------------------------------------------------------------- integer helpers
def clip(x: int, lo: int, hi: int) -> int:
    """Saturate x to [lo, hi]."""
    return lo if x < lo else hi if x > hi else x


def rshift_round(x: int, s: int) -> int:
    """x / 2**s rounded half up, arithmetic shift (s >= 1)."""
    return (x + (1 << (s - 1))) >> s


def div_round(a: int, b: int) -> int:
    """a / b rounded half away from zero, b > 0. C: (a >= 0) ? (2a + b) / (2b) : -((-2a + b) / (2b))."""
    if a >= 0:
        return (2 * a + b) // (2 * b)
    return -((-2 * a + b) // (2 * b))


def quantise_m(m: float) -> int:
    """Relative moisture float -> uint8 0..100 (round half up, saturating). FR-E04, NFR-02."""
    return clip(int(np.floor(m + 0.5)), 0, 100)


def quantise_temp(deg_c: float) -> int:
    """degC -> temp_u8 (whole degrees + TEMP_OFFSET, saturating 0..255)."""
    return clip(int(np.floor(deg_c + 0.5)) + TEMP_OFFSET, 0, 255)


def soil_code(soil_type: str) -> int:
    """db-schema soil_type -> device soil code (C4). Unknown strings give 0. FR-A04."""
    return SOIL_TYPE_TO_CODE.get(soil_type, SOIL_CODES.get(soil_type, 0))


def local_minute_of_day(utc_minute_of_day: int, utc_offset_min: int) -> int:
    """Plant-local minute of day from UTC minute and config.utc_offset_min (C4; device has no timezone). FR-E01."""
    return (utc_minute_of_day + utc_offset_min) % 1440


def lux_to_light_u8(lux: float) -> int:
    """Light level uint8 = min(255, round(16*log2(1+lux))) (C3, Theo's proposal; lux 0..100000). Host-side float
    reference; the C port needs a literal lookup table (no libm). Unverified on real sensor data. FR-E01."""
    import math
    return clip(int(math.floor(16.0 * math.log2(1.0 + max(0.0, lux)) + 0.5)), 0, 255)


def forecast_h_from_model(raw_h: float) -> float:
    """Clip model output to [0, 72]. 72.0 = '72 h or more' and is emitted as 72.0, never null (C2). FR-E01."""
    return min(FORECAST_CAPPED_H, max(0.0, float(raw_h)))


def forecast_ready(samples_since_cold_boot: int) -> bool:
    """C1(a): no forecast until HIST (96) samples exist after a cold boot; device twin of export `feat_valid`."""
    return samples_since_cold_boot >= HIST


# --------------------------------------------------------------------------- slope
def slope_x64(y: list[int] | np.ndarray) -> int:
    """Least-squares slope of the samples y (oldest first, 15-min spacing) in pp/h * 64, integer only.

    With x2 = 2x - (N-1): slope per tick = 2*sum(x2*y)/sum(x2^2); per hour = 8*...; times 64 = 512*num/den.
    FR-E01 (slopes over 1 h / 6 h / 24 h are named model inputs).
    """
    n = len(y)
    if n < 2:
        raise ValueError("need at least 2 samples")
    num = 0
    den = 0
    for i in range(n):
        x2 = 2 * i - (n - 1)
        num += x2 * int(y[i])
        den += x2 * x2
    return div_round(512 * num, den)


# --------------------------------------------------------------------------- wetting tracker (streaming)
class EventTracker:
    """Streaming wetting-event detector; the C port keeps this state in RTC memory across deep sleeps.

    Mirrors prep.label_events (rise >= RISE_PTS over RISE_WINDOW ticks, onset = first tick of a rise run,
    refractory REFRACTORY ticks). State: the last RISE_WINDOW samples (with validity), the previous rise flag,
    ticks since the last onset (saturating at HORIZON_TICKS = 72 h), ticks since last onset for the refractory.
    FR-E01 (feature "time since last detected wetting event").
    """

    def __init__(self) -> None:
        self.hist: list[tuple[int, bool]] = []     # last RISE_WINDOW (m, valid)
        self.prev_rise = False
        self.since = HORIZON_TICKS                 # unknown / none yet = saturated
        self.since_refractory = 10**9              # ticks since last kept onset (for suppression)

    RTC_LAYOUT_VERSION = 1

    @staticmethod
    def _crc8(data: bytes) -> int:
        crc = 0
        for b in data:
            crc ^= b
            for _ in range(8):
                crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
        return crc

    def to_rtc(self) -> bytes:
        """RTC image: version, CRC8, then state (C1b). Layout is the contract for the C port; changes bump the version."""
        h = [(m, int(v)) for m, v in self.hist] + [(0, 0)] * (RISE_WINDOW - len(self.hist))
        body = bytes([len(self.hist), h[0][0], h[0][1], h[1][0], h[1][1], int(self.prev_rise),
                      self.since & 0xFF, self.since >> 8, min(self.since_refractory, 255)])
        return bytes([self.RTC_LAYOUT_VERSION, self._crc8(body)]) + body

    @classmethod
    def from_rtc(cls, blob: bytes | None) -> "EventTracker":
        """Restore from RTC image; wrong length, version or CRC (cold boot, brown-out, OTA layout change) gives a
        cold-boot tracker: since = 288 (72 h or unknown), empty history (C1a, C1b)."""
        tr = cls()
        if blob is None or len(blob) != 11 or blob[0] != cls.RTC_LAYOUT_VERSION or cls._crc8(blob[2:]) != blob[1]:
            return tr
        b = blob[2:]
        if b[0] > RISE_WINDOW or b[5] > 1 or (b[6] | b[7] << 8) > HORIZON_TICKS:
            return tr
        tr.hist = [(b[1], bool(b[2])), (b[3], bool(b[4]))][:b[0]]
        tr.prev_rise = bool(b[5])
        tr.since = b[6] | b[7] << 8
        tr.since_refractory = b[8] if b[8] < 255 else 10**9
        return tr

    def step(self, m: int, valid: bool = True) -> bool:
        """Feed one 15-min sample; returns True when a wetting onset is detected at this tick."""
        rise = False
        if valid and len(self.hist) == RISE_WINDOW:
            m0, v0 = self.hist[0]
            rise = v0 and (m - m0) >= RISE_PTS
        onset = rise and not self.prev_rise
        self.since_refractory = min(self.since_refractory + 1, 10**9)
        kept = onset and self.since_refractory > REFRACTORY
        self.since = clip(self.since + 1, 0, HORIZON_TICKS)
        if kept:
            self.since = 0
            self.since_refractory = 0
        self.prev_rise = rise
        self.hist.append((m, valid))
        if len(self.hist) > RISE_WINDOW:
            self.hist.pop(0)
        return kept


def ticks_since_event_series(m_u8: list[int] | np.ndarray, valid: list[bool] | None = None) -> np.ndarray:
    """Run EventTracker over a whole series; returns ticks-since-last-onset at every tick (saturating 288)."""
    tr = EventTracker()
    out = np.empty(len(m_u8), dtype=np.int32)
    for i, m in enumerate(m_u8):
        tr.step(int(m), True if valid is None else bool(valid[i]))
        out[i] = tr.since
    return out


# --------------------------------------------------------------------------- feature vector
def feature_vector(m_hist: list[int] | np.ndarray, temp_hist: list[int] | np.ndarray,
                   light_hist: list[int] | np.ndarray, minute_of_day: int, T: int, ticks_since_event: int,
                   soil: int) -> list[int]:
    """The 14 int8 Model A inputs (concept 2.2) from the 96-sample history ending at 'now' (oldest first).

    m_hist/temp_hist/light_hist: HIST uint8 samples. minute_of_day 0..1439. T: dry threshold (pp, 0..100).
    ticks_since_event: from EventTracker (saturating 288). soil: SOIL_CODES value.
    Returns ints already inside int8 range (value - zero point, saturated). FR-E01, FR-E04.
    """
    if len(m_hist) != HIST or len(temp_hist) != HIST or len(light_hist) != HIST:
        raise ValueError(f"histories must have exactly {HIST} samples")
    m = [int(v) for v in m_hist]
    t = [int(v) for v in temp_hist]
    lt = [int(v) for v in light_hist]
    hour = minute_of_day // 60
    raw = {
        "m_now": m[-1] - FEATURE_SPEC["m_now"][1],
        "slope_1h": rshift_round(slope_x64(m[-W_1H:]), 5),
        "slope_6h": rshift_round(slope_x64(m[-W_6H:]), 3),
        "slope_24h": rshift_round(slope_x64(m[-W_24H:]), 2),
        "m_min_24h": min(m) - 50,
        "m_max_24h": max(m) - 50,
        "temp_now": t[-1] - TEMP_OFFSET,
        "temp_mean_24h": div_round(sum(t), HIST) - TEMP_OFFSET,
        "light_mean_6h": div_round(sum(lt[-LIGHT_WINDOW:]), LIGHT_WINDOW) - 128,
        "sin_hour": SIN_HOUR[hour],
        "cos_hour": SIN_HOUR[(hour + 6) % 24],
        "T": T - 50,
        "hours_since_event": clip(ticks_since_event, 0, HORIZON_TICKS) // 4,
        "soil": soil,
    }
    return [clip(raw[k], -128, 127) for k in FEATURE_NAMES]
