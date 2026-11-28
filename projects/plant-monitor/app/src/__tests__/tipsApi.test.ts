// Care tips client and contract checks (task 4.A7, FR-P02, FR-P04, NFR-06). Fake fetch only: no request leaves the test process.
import { createTipsClient, tipsUrl, TipsError } from '../tips/tipsApi';
import { parseTipsRow, parseTipItems, GUARDRAIL_VERSION_EXPECTED, TIP_TEXT_MAX } from '../tips/tipsModel';

const PLANT = '6f1c2a3e-0000-4000-8000-000000000001';
const NOW = new Date('2026-11-24T08:00:00Z');
const goodRow = {
  generated_at: '2026-11-24T06:00:00Z',
  guardrail_version: GUARDRAIL_VERSION_EXPECTED,
  content: { items: [{ id: 'w-1', category: 'watering', text: 'Water when the top 2 cm of soil is dry.' }] },
};
const resp = (status: number, body: unknown): Response => ({
  status,
  json: async () => { if (body === '__bad_json__') throw new Error('bad json'); return body; },
} as unknown as Response);
const client = (fetchImpl: jest.Mock, token: string | null = 'jwt-test') => createTipsClient({
  baseUrl: 'https://example.invalid/', publishableKey: 'pk-test', getAccessToken: async () => token, fetchImpl: fetchImpl as unknown as typeof fetch, now: () => NOW,
});

describe('tips request (FR-P02, NFR-06)', () => {
  test('reads the newest current row of this plant with the user token, filtered like mcp_get_tips', async () => {
    const f = jest.fn(async () => resp(200, [goodRow]));
    const out = await client(f).fetchPlantTips(PLANT);
    expect(out).toEqual({ plantId: PLANT, generatedAt: goodRow.generated_at, items: goodRow.content.items });
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit];
    const q = new URL(url).searchParams;
    expect(url.startsWith('https://example.invalid/rest/v1/tips?')).toBe(true);
    expect(q.get('plant_id')).toBe(`eq.${PLANT}`);
    expect(q.get('guardrail_version')).toBe(`eq.${GUARDRAIL_VERSION_EXPECTED}`);
    expect(q.get('expires_at')).toBe(`gt.${NOW.toISOString()}`);
    expect(q.get('order')).toBe('generated_at.desc');
    expect(q.get('limit')).toBe('1');
    expect(init.method).toBe('GET');
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer jwt-test');
    expect((init.headers as Record<string, string>).apikey).toBe('pk-test');
  });

  test('no signed-in session: unauthorized, nothing is requested', async () => {
    const f = jest.fn();
    await expect(client(f, null).fetchPlantTips(PLANT)).rejects.toMatchObject({ code: 'unauthorized' });
    expect(f).not.toHaveBeenCalled();
  });

  test('no row (no tips stored yet, or all expired): null, which the screen shows as the empty state', async () => {
    expect(await client(jest.fn(async () => resp(200, []))).fetchPlantTips(PLANT)).toBeNull();
  });

  test('a row whose items are all absent: null (empty state), not an error', async () => {
    const row = { ...goodRow, content: { items: [] } };
    expect(await client(jest.fn(async () => resp(200, [row]))).fetchPlantTips(PLANT)).toBeNull();
  });

  test.each([
    { name: '401', make: () => resp(401, {}), code: 'unauthorized' },
    { name: '403', make: () => resp(403, {}), code: 'unknown' },
    { name: '500', make: () => resp(500, {}), code: 'server' },
    { name: 'object body', make: () => resp(200, { not: 'an array' }), code: 'bad_response' },
    { name: 'invalid json', make: () => resp(200, '__bad_json__'), code: 'bad_response' },
  ])('$name answer maps to $code', async ({ make, code }) => {
    await expect(client(jest.fn(async () => make())).fetchPlantTips(PLANT)).rejects.toMatchObject({ code });
  });

  test('network failure maps to network', async () => {
    await expect(client(jest.fn(async () => { throw new Error('offline'); })).fetchPlantTips(PLANT)).rejects.toBeInstanceOf(TipsError);
    await expect(client(jest.fn(async () => { throw new Error('offline'); })).fetchPlantTips(PLANT)).rejects.toMatchObject({ code: 'network' });
  });

  test('tipsUrl encodes the plant id and trims the base url', () => {
    expect(tipsUrl('https://x.invalid//', 'a&b', '2026-01-01T00:00:00.000Z')).toContain('plant_id=eq.a%26b');
    expect(tipsUrl('https://x.invalid//', PLANT, '2026-01-01T00:00:00.000Z').startsWith('https://x.invalid/rest/v1/tips?')).toBe(true);
  });
});

describe('stored tips must match the contract (FR-P02, same rule as the MCP server)', () => {
  test('a row stored under another guardrail version is refused', () => {
    expect(parseTipsRow({ ...goodRow, guardrail_version: 'g0.9' }, PLANT)).toBeNull();
  });
  test('one bad item fails the whole row', () => {
    const bad = { ...goodRow, content: { items: [goodRow.content.items[0], { id: 'x', category: 'fertiliser', text: 'Feed weekly.' }] } };
    expect(parseTipsRow(bad, PLANT)).toBeNull();
    expect(parseTipsRow({ ...goodRow, content: { items: [{ id: 'x', category: 'watering' }] } }, PLANT)).toBeNull();
    expect(parseTipsRow({ ...goodRow, content: { items: [{ id: '', category: 'watering', text: 'Water.' }] } }, PLANT)).toBeNull();
  });
  test('text longer than the contract maximum is refused', () => {
    expect(parseTipItems({ items: [{ id: 'x', category: 'other', text: 'a'.repeat(TIP_TEXT_MAX + 1) }] })).toBeNull();
    expect(parseTipItems({ items: [{ id: 'x', category: 'other', text: 'a'.repeat(TIP_TEXT_MAX) }] })).toHaveLength(1);
  });
  test('missing content, or a bad generated_at, is refused', () => {
    expect(parseTipsRow({ ...goodRow, content: null }, PLANT)).toBeNull();
    expect(parseTipsRow({ ...goodRow, generated_at: 'not a date' }, PLANT)).toBeNull();
    expect(parseTipsRow(null, PLANT)).toBeNull();
  });
  test('extra fields on an item (such as an internal reason) are not returned to the screen', () => {
    const row = { ...goodRow, content: { items: [{ ...goodRow.content.items[0], reason: 'internal', action: 'do' }] } };
    const out = parseTipsRow(row, PLANT);
    expect(out?.items[0]).toEqual({ id: 'w-1', category: 'watering', text: 'Water when the top 2 cm of soil is dry.' });
  });
});
