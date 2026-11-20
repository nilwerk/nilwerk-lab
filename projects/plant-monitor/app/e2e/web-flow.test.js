// Simulator-level flow test for the Plant Monitor app in Expo web (mock build).
// Runs in headless Chromium via Playwright against the static web export with EXPO_PUBLIC_MOCK_AUTH=1.
// Covers: welcome -> sign-up with error -> sign-up success -> profile (+ mocked BLE scan) -> plant list -> plant detail.
// MOCKS: auth, plants and readings are in-memory fixtures; the sensor setup is a fake BLE provisioning service.
// NOT TESTED: real Bluetooth, the real sensor, the live Supabase backend. Screens say "MOCK" on every page (app.mockBanner).
// Run: npm run test:web-flow   (from projects/plant-monitor/app). Screenshots go to WEB_FLOW_EVIDENCE_DIR
// (default ~/sim-evidence/app), never into the repo. Build dir: WEB_FLOW_BUILD_DIR (default: a temp dir).
// Requirements: FR-A01 (sign-up/sign-in/profile), FR-A03/FR-A04 (sensor setup, mock), FR-A06 (plant list and detail), FR-A07 (thresholds shown).
'use strict';
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');

const APP_DIR = path.resolve(__dirname, '..');
const BUILD_DIR = process.env.WEB_FLOW_BUILD_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'plant-web-flow-'));
const EVIDENCE_DIR = process.env.WEB_FLOW_EVIDENCE_DIR || path.join(os.homedir(), 'sim-evidence', 'app');
const MOCK_BANNER = /MOCK: test values and a fake sensor, not real data/;
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon', '.ttf': 'font/ttf', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff' };

let browser; let server; let baseUrl; let page;

function serve(root) {
  return http.createServer((req, res) => {
    const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let file = path.join(root, urlPath);
    if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(root, 'index.html'); // SPA fallback
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
}

async function shot(name) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  await page.screenshot({ path: path.join(EVIDENCE_DIR, name), scale: 'css' });
}

before(async () => {
  const exp = spawnSync('npx', ['expo', 'export', '--platform', 'web', '--output-dir', BUILD_DIR], {
    cwd: APP_DIR, env: { ...process.env, EXPO_PUBLIC_MOCK_AUTH: '1' }, stdio: ['ignore', 'ignore', 'inherit'], timeout: 540000,
  });
  assert.equal(exp.status, 0, 'expo web export failed');
  server = serve(BUILD_DIR);
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  baseUrl = `http://127.0.0.1:${server.address().port}/`;
  browser = await chromium.launch(); // pre-installed Chromium (PLAYWRIGHT_BROWSERS_PATH); no playwright install
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, locale: 'en-US' });
  page = await ctx.newPage();
  await page.goto(baseUrl);
}, { timeout: 600000 });

after(async () => {
  if (browser) await browser.close();
  if (server) server.close();
});

test('mock build: welcome, sign-up, profile, mocked sensor setup, plant list and detail', async (t) => {
  await t.test('welcome screen shows the mock label and both entry buttons', async () => {
    await page.getByText('Know when your plants are thirsty').waitFor({ timeout: 60000 });
    await page.getByText(MOCK_BANNER).waitFor();
    await page.getByRole('button', { name: 'Create account' }).waitFor();
    await page.getByRole('button', { name: 'I already have an account' }).waitFor();
    await shot('01-welcome.png');
  });

  await t.test('sign-up with invalid data shows field errors', async () => {
    await page.getByRole('button', { name: 'Create account' }).click();
    await page.getByLabel('E-mail', { exact: true }).fill('bad');
    await page.getByLabel('Password', { exact: true }).fill('short');
    await page.getByRole('button', { name: 'Create account' }).click();
    await page.getByText('Enter a valid e-mail, for example you@example.com.').waitFor();
    await page.getByText('Use at least 8 characters.').waitFor();
    await page.getByText(MOCK_BANNER).waitFor();
    await shot('02-sign-up-error.png');
  });

  await t.test('sign-up with valid data lands on My plants', async () => {
    await page.getByLabel('E-mail', { exact: true }).fill('sim-test@example.com');
    await page.getByLabel('Password', { exact: true }).fill('correct-horse-1');
    await page.getByRole('button', { name: 'Create account' }).click();
    await page.getByText('My plants', { exact: true }).first().waitFor({ timeout: 15000 });
  });

  await t.test('profile shows the account, the free plan and the mocked add-sensor flow', async () => {
    await page.getByRole('tab', { name: 'Profile' }).click();
    await page.getByText('sim-test@example.com').waitFor();
    await page.getByText('Free', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Sign out' }).waitFor();
    await page.getByText(MOCK_BANNER).waitFor();
    await shot('03-profile.png');
    // mocked BLE provisioning: the fake service "scans" and reports one fake sensor (no Bluetooth is used)
    await page.getByRole('button', { name: 'Add a sensor' }).click();
    await page.getByRole('button', { name: 'Find my sensor' }).click();
    await page.getByText('NW-d4e5f6').waitFor({ timeout: 15000 });
    await page.getByRole('button', { name: 'Go back' }).click(); // leaves setup without connecting
    await page.getByRole('button', { name: 'Sign out' }).waitFor();
  });

  await t.test('plant list shows the five mock plants with their mock soil values', async () => {
    await page.getByRole('tab', { name: 'Plants' }).click();
    for (const name of ['Basil', 'Cactus', 'Fern', 'Orchid', 'Rubber tree']) {
      await page.getByText(name, { exact: true }).first().waitFor();
    }
    await page.getByText('38 %').first().waitFor(); // Basil, mock reading
    await page.getByText(MOCK_BANNER).waitFor();
    await shot('04-plant-list.png');
  });

  await t.test('plant detail shows the mock latest reading, chart and thresholds', async () => {
    await page.getByText('Basil', { exact: true }).first().click();
    await page.getByText('Latest reading').waitFor();
    await page.getByText('Soil moisture, last 7 days (hourly)').waitFor();
    await page.getByText('Dry below 25 %, wet above 85 %').waitFor();
    await page.getByText(MOCK_BANNER).waitFor();
    await shot('05-plant-detail.png');
  });
});
