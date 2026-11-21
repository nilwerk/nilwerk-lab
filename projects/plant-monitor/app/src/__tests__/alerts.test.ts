// Alert rules (FR-A07, FR-D06). Boundary cases follow tests/acceptance-matrix.md (FR-A07 row): offline at 2 h 50 / 3 h 05 no alert, 3 h 15 alert;
// moisture 29.9 % keeps the dry alert open, 30.0 % closes it; battery 3399 mV opens, 3500 mV clears.
import { evaluateAlerts, alertsForPlant, LOW_BATTERY_MV, OFFLINE_AFTER_MIN, type AlertInput, type AlertPoint } from '../plants/alerts';
import { sampleFixture } from '../plants/fakePlants';

const NOW = new Date('2026-11-20T12:00:00.000Z');
const MIN = 60_000;
/** points spaced one hour apart, oldest first, ending one hour before NOW (the latest report is added by each test when needed) */
const series = (values: { m?: number | null; v?: number | null }[]): AlertPoint[] => {
  const n = values.length;
  return values.map((x, i) => ({ ts: new Date(NOW.getTime() - (n - i) * 60 * MIN).toISOString(), moisturePct: x.m ?? null, vbatMv: x.v ?? null }));
};
const seenMinAgo = (min: number) => new Date(NOW.getTime() - min * MIN).toISOString();
const base = (over: Partial<AlertInput> = {}): AlertInput => ({
  now: NOW, hasSensor: true, dryThresholdPct: 25, wetThresholdPct: 85, lastSeenAt: seenMinAgo(5), points: series([{ m: 40, v: 3800 }]), ...over,
});
const kinds = (a: ReturnType<typeof evaluateAlerts>) => a.map((x) => x.kind);

describe('no alert', () => {
  test('healthy plant: moisture in range, battery fine, reported 5 min ago', () => {
    expect(evaluateAlerts(base())).toEqual([]);
  });
  test('plant without a sensor never raises an alert, even with bad values', () => {
    expect(evaluateAlerts(base({ hasSensor: false, lastSeenAt: null, points: series([{ m: 2, v: 2900 }]) }))).toEqual([]);
  });
  test('no points and a fresh report: no moisture or battery alert', () => {
    expect(evaluateAlerts(base({ points: [] }))).toEqual([]);
  });
  test('never reported (lastSeenAt null) is not an offline alert (server needs last_seen_at)', () => {
    expect(evaluateAlerts(base({ lastSeenAt: null }))).toEqual([]);
  });
});

describe('too dry', () => {
  test('latest soil 20 % opens too_dry with the value and the threshold', () => {
    const a = evaluateAlerts(base({ points: series([{ m: 40 }, { m: 20 }]) }));
    expect(a).toEqual([{ kind: 'too_dry', value: 20, threshold: 25 }]);
  });
  test('exactly 25 % is not dry (the rule is strictly below)', () => {
    expect(evaluateAlerts(base({ points: series([{ m: 25 }]) }))).toEqual([]);
  });
  test('24.9 % is dry', () => {
    expect(kinds(evaluateAlerts(base({ points: series([{ m: 24.9 }]) })))).toEqual(['too_dry']);
  });
  test('stays open at 29.9 %, clears at 30.0 % (threshold + 5)', () => {
    expect(kinds(evaluateAlerts(base({ points: series([{ m: 20 }, { m: 29.9 }]) })))).toEqual(['too_dry']);
    expect(evaluateAlerts(base({ points: series([{ m: 20 }, { m: 30 }]) }))).toEqual([]);
  });
  test('a plant with its own dry threshold (30 %) uses it', () => {
    expect(kinds(evaluateAlerts(base({ dryThresholdPct: 30, points: series([{ m: 28 }]) })))).toEqual(['too_dry']);
  });
  test('null moisture is skipped, not read as 0', () => {
    expect(evaluateAlerts(base({ points: series([{ m: null, v: 3800 }]) }))).toEqual([]);
  });
});

describe('too wet', () => {
  test('latest soil 90 % opens too_wet', () => {
    expect(evaluateAlerts(base({ points: series([{ m: 90 }]) }))).toEqual([{ kind: 'too_wet', value: 90, threshold: 85 }]);
  });
  test('exactly 85 % is not wet (strictly above)', () => {
    expect(evaluateAlerts(base({ points: series([{ m: 85 }]) }))).toEqual([]);
  });
  test('stays open at 81 %, clears at 80 % (threshold - 5)', () => {
    expect(kinds(evaluateAlerts(base({ points: series([{ m: 90 }, { m: 81 }]) })))).toEqual(['too_wet']);
    expect(evaluateAlerts(base({ points: series([{ m: 90 }, { m: 80 }]) }))).toEqual([]);
  });
});

describe('low battery', () => {
  test('3399 mV opens low_battery (FR-D06, 3.4 V)', () => {
    expect(evaluateAlerts(base({ points: series([{ v: 3399 }]) }))).toEqual([{ kind: 'low_battery', value: 3399, threshold: LOW_BATTERY_MV }]);
  });
  test('exactly 3400 mV is not low', () => {
    expect(evaluateAlerts(base({ points: series([{ v: 3400 }]) }))).toEqual([]);
  });
  test('stays open at 3450 mV, clears at 3500 mV', () => {
    expect(kinds(evaluateAlerts(base({ points: series([{ v: 3399 }, { v: 3450 }]) })))).toEqual(['low_battery']);
    expect(evaluateAlerts(base({ points: series([{ v: 3399 }, { v: 3500 }]) }))).toEqual([]);
  });
  test('impossible values (0 mV, above 5000 mV) are ignored, so they cannot open an alert', () => {
    expect(evaluateAlerts(base({ points: series([{ v: 0 }]) }))).toEqual([]);
    expect(evaluateAlerts(base({ points: series([{ v: 5001 }]) }))).toEqual([]);
  });
  test('a custom device threshold is used', () => {
    expect(kinds(evaluateAlerts(base({ lowBatteryMv: 3600, points: series([{ v: 3500 }]) })))).toEqual(['low_battery']);
  });
});

describe('device offline', () => {
  test('reported 3 h 05 min ago: no alert', () => {
    expect(evaluateAlerts(base({ lastSeenAt: seenMinAgo(185) }))).toEqual([]);
  });
  test('reported exactly 3 h 10 min ago: no alert (strictly older than the limit)', () => {
    expect(evaluateAlerts(base({ lastSeenAt: seenMinAgo(OFFLINE_AFTER_MIN) }))).toEqual([]);
  });
  test('reported 3 h 15 min ago: offline alert with minutes since the last report', () => {
    expect(evaluateAlerts(base({ lastSeenAt: seenMinAgo(195) }))).toEqual([{ kind: 'device_offline', value: 195, threshold: OFFLINE_AFTER_MIN }]);
  });
  test('offline is not cleared by old readings: the last report decides', () => {
    expect(kinds(evaluateAlerts(base({ lastSeenAt: seenMinAgo(300) })))).toEqual(['device_offline']);
  });
});

describe('several alerts at once', () => {
  test('offline, dry and low battery together, offline first', () => {
    const a = evaluateAlerts(base({ lastSeenAt: seenMinAgo(300), points: series([{ m: 12, v: 3350 }]) }));
    expect(kinds(a)).toEqual(['device_offline', 'too_dry', 'low_battery']);
  });
  test('points given out of order are replayed by time', () => {
    const pts = series([{ m: 20 }, { m: 40 }, { m: 90 }]);
    // newest is 90 (too wet); shuffled input must give the same answer as sorted input
    expect(kinds(evaluateAlerts(base({ points: [pts[2], pts[0], pts[1]] })))).toEqual(['too_wet']);
  });
});

describe('fixture plants (mock build) agree with their mock status chips', () => {
  test('evaluated alerts match the openAlerts of the five sample plants', () => {
    const { plants, hourly } = sampleFixture(NOW);
    for (const p of plants) {
      const got = alertsForPlant(p, (hourly[p.id] ?? []).map((h) => ({ hour: h.hour, moistureAvg: h.moistureAvg, vbatMinMv: h.vbatMinMv })), NOW);
      expect([...kinds(got)].sort()).toEqual([...p.openAlerts.filter((k) => ['too_dry', 'too_wet', 'low_battery', 'device_offline'].includes(k))].sort());
    }
  });
});
