'use strict';
// App end-to-end flow on the bench phone (Appium 2.x, UiAutomator2). Called by bench/app/run_appium.sh,
// which checks the inputs first. Scope (owner decision, 21 Nov 2026): communication only. The flow
// asserts screen text. It never reads or asserts a sensor value.
// Secrets (test sign-in, board label code, Wi-Fi, phone id) come from the environment only. They are
// never printed, and they are scrubbed from every log line and from result.json.
const fs = require('node:fs');
const { Appium } = require('./w3c');

const APPIUM_URL = 'http://localhost:4723';
const APP_PACKAGE = 'de.nilwerk.plantmonitor';
const APP_ACTIVITY = '.MainActivity';
const RESULT_FILE = process.env.BENCH_RESULT_FILE;
const LONG = 60000;
const LINK = 180000;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Inputs (names only; values never printed).
const serial = process.env.BENCH_ANDROID_SERIAL || '';
const email = process.env.BENCH_TEST_EMAIL || '';
const password = process.env.BENCH_TEST_EMAIL_PASSWORD || '';
const pop = process.env.BENCH_BOARD_POP || '';
const ssid = process.env.BENCH_WIFI_SSID || '';
const wifiPassword = process.env.BENCH_WIFI_PASSWORD || '';
const blePrefix = process.env.BENCH_BLE_PREFIX || '';

const required = { BENCH_ANDROID_SERIAL: serial, BENCH_TEST_EMAIL: email, BENCH_TEST_EMAIL_PASSWORD: password,
  BENCH_BOARD_POP: pop, BENCH_WIFI_SSID: ssid, BENCH_WIFI_PASSWORD: wifiPassword, BENCH_BLE_PREFIX: blePrefix,
  BENCH_RESULT_FILE: RESULT_FILE };
const missing = Object.keys(required).filter((k) => !required[k]);
if (missing.length) {
  console.error(`app flow: not configured: missing ${missing.join(', ')}. Nothing tested.`);
  process.exit(1);
}

const secrets = [serial, email, password, pop, ssid, wifiPassword].filter(Boolean);
function scrub(text) {
  let out = String(text);
  for (const s of secrets) out = out.split(s).join('[redacted]');
  return out;
}

const steps = [];
let stopped = false;
let app = null;

function log(line) { console.log(scrub(line)); }

async function step(name, fn) {
  if (stopped) { steps.push({ step: name, status: 'not_run' }); return; }
  log(`${name}: start`);
  try {
    const detail = await fn();
    steps.push(typeof detail === 'string' ? { step: name, status: 'pass', detail } : { step: name, status: 'pass' });
    log(`${name}: pass`);
  } catch (e) {
    stopped = true;
    const detail = scrub(e && e.message ? e.message : e);
    steps.push({ step: name, status: 'fail', detail });
    log(`${name}: FAIL, ${detail}`);
  }
}

// UiAutomator selectors. Quotes and backslashes are escaped.
const q = (s) => String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
const byText = (t) => `new UiSelector().text("${q(t)}")`;
const byDesc = (d) => `new UiSelector().description("${q(d)}")`;

async function findExact(t) {
  return (await app.find(byText(t))) || (await app.find(byDesc(t)));
}
async function findContaining(t) {
  return (await app.find(`new UiSelector().textContains("${q(t)}")`)) ||
    (await app.find(`new UiSelector().descriptionContains("${q(t)}")`));
}
async function waitUntil(fn, ms, what) {
  const end = Date.now() + ms;
  for (;;) {
    const r = await fn();
    if (r) return r;
    if (Date.now() > end) throw new Error(`not shown in time: ${what}`);
    await sleep(500);
  }
}
async function see(t, ms = LONG) { return waitUntil(() => findExact(t), ms, `"${t}"`); }
async function tap(t, ms = LONG) {
  const el = await waitUntil(async () =>
    (await app.find(`new UiSelector().text("${q(t)}").clickable(true)`)) ||
    (await app.find(`new UiSelector().description("${q(t)}").clickable(true)`)) ||
    (await findExact(t)), ms, `button "${t}"`);
  await app.click(el);
}
async function type(label, value, ms = LONG) {
  const el = await waitUntil(() => app.find(byDesc(label)), ms, `field "${label}"`);
  await app.clear(el);
  await app.sendKeys(el, value);
}
// Android runtime permission prompts (Bluetooth, location on Android 8.1). Labels are unverified on this phone.
async function dismissSystemDialogs() {
  for (let i = 0; i < 3; i++) {
    const el = await app.find('new UiSelector().textMatches("(?i)^(allow|while using the app)$")');
    if (!el) return;
    await app.click(el);
    await sleep(1000);
  }
}
// Waits for one of the expected screens; stops with a message if an error screen shows instead.
async function waitForScreen(wanted, errors, ms = LINK) {
  const end = Date.now() + ms;
  for (;;) {
    for (const w of wanted) if (await findExact(w)) return w;
    for (const e of errors) if (await findContaining(e)) throw new Error(`stopped on screen: "${e}"`);
    if (Date.now() > end) throw new Error(`none shown in time: ${wanted.join(' | ')}`);
    await sleep(500);
  }
}
const SETUP_ERRORS = ["Wi-Fi didn't work", 'Linking to your account failed', 'Sensor already belongs',
  'Setup mode closed', 'Sensor not found', 'Something went wrong'];

async function main() {
  const startedUtc = new Date().toISOString();
  const plantName = `Bench e2e ${startedUtc.slice(0, 16).replace(/[-:T]/g, '')}`;
  app = new Appium(APPIUM_URL);

  try {
    await step('1_launch', async () => {
      await app.createSession({
        platformName: 'Android',
        'appium:automationName': 'UiAutomator2',
        'appium:udid': serial,
        'appium:appPackage': APP_PACKAGE,
        'appium:appActivity': APP_ACTIVITY,
        'appium:noReset': true,
        'appium:newCommandTimeout': 900,
      });
      await waitUntil(async () =>
        (await findExact('Create account')) || (await findExact('My plants')) ||
        (await findExact('I already have an account')) || (await findExact('Sign in')),
        LONG, 'a start screen (Welcome, Sign in or My plants)');
      if (await findContaining('MOCK:')) throw new Error('the mock build is installed, not the real app; nothing tested');
      return 'app launched';
    });

    await step('2_sign_in', async () => {
      if (await findExact('My plants')) return 'already signed in (session kept from an earlier run)';
      if (await findExact('I already have an account')) await tap('I already have an account');
      await type('E-mail', email);
      await type('Password', password);
      await tap('Sign in');
      await waitForScreen(['My plants'], ['is not right', 'not connected to a server']);
      return 'signed in';
    });

    await step('3_add_plant', async () => {
      await tap('Profile');
      await tap('Add a sensor');
      await tap('Find my sensor');
      const dev = await waitUntil(async () => {
        await dismissSystemDialogs();
        return app.find(`new UiSelector().textStartsWith("${q(blePrefix)}")`);
      }, LONG, `a sensor whose name starts with the expected prefix`);
      await app.click(dev);
      await see('Connect to your sensor');
      await type('Sensor code (from the label)', pop);
      await tap('Connect');
      await see('Choose your Wi-Fi', LINK);
      await tap('Other network...');
      await type('Network name', ssid);
      await type('Wi-Fi password', wifiPassword);
      await tap('Continue');
      await see('Name your sensor');
      await type('Sensor name', plantName);
      await tap('Connect sensor');
      await waitForScreen(['Take a photo'], SETUP_ERRORS, LINK);
      await tap('Skip for now');
      await see('About your plant');
      await type('Plant name', plantName);
      await type('Room or area', 'Bench');
      await type('City', 'Berlin');
      await tap('Save plant');
      await waitForScreen(['All set!'], ['could not be saved', 'Something went wrong'], LONG);
      return 'setup finished on the All set screen';
    });

    await step('4_confirm_connected_and_listed', async () => {
      await waitUntil(() => findContaining(`${plantName} is connected`), LONG, 'device shown as connected');
      await tap('Done');
      await tap('Plants');
      await see('My plants');
      const end = Date.now() + LONG;
      for (;;) {
        if (await findContaining(plantName)) return 'plant shown on My plants';
        if (await findContaining('Could not load your plants') || await findContaining('not connected to a server')) {
          throw new Error('My plants shows an error: plant list is not wired in this build');
        }
        if (Date.now() > end) throw new Error('plant not shown on My plants');
        await sleep(1000);
      }
    });
  } finally {
    await app.deleteSession().catch(() => {});
  }

  const overall = steps.every((s) => s.status === 'pass') ? 'pass' : 'fail';
  const out = {
    flow: 'app-e2e',
    scope: 'communication only; no sensor value is read or asserted',
    started_utc: startedUtc,
    ended_utc: new Date().toISOString(),
    result: overall,
    steps,
  };
  fs.writeFileSync(RESULT_FILE, JSON.stringify(out, null, 2) + '\n');
  log(`app flow: ${overall} (${steps.length} steps); result written to ${RESULT_FILE}`);
  process.exitCode = overall === 'pass' ? 0 : 1;
}

main().catch((e) => {
  console.error(`app flow: unexpected error: ${scrub(e && e.message ? e.message : 'unknown')}`);
  process.exitCode = 1;
});
