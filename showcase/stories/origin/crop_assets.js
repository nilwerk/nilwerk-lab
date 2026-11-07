// One-off: cut the real v1/v2 CAD renders and the PCB plot out of the first origin carousel (2026-11-05) into assets/.
// The Drive source files are not in the repo; these crops are the repo's copy of those renders (native resolution, not enlarged).
// Kept for the record: the old origin-01..10.png and build_carousel.py were removed afterwards (they are in the git history, commit d015d8a and earlier),
// so this script cannot be rerun from the current tree. The crops in assets/ are the repo's copy of the renders.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const SPECS = [
  ['v1-exploded', 'origin-02.png', 96, 640, 420, 410],
  ['pcb-v1', 'origin-02.png', 560, 520, 430, 700],
  ['v2-assembled', 'origin-03.png', 92, 520, 390, 470],
  ['v2-exploded', 'origin-01.png', 590, 700, 440, 420],
  ['v2-back-shell', 'origin-06.png', 350, 770, 250, 360],
];
(async () => {
  fs.mkdirSync(path.join(__dirname, 'assets'), { recursive: true });
  const browser = await chromium.launch();
  for (const [name, src, x, y, w, h] of SPECS) {
    const ctx = await browser.newContext({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    await page.goto('file://' + path.join(__dirname, src));
    await page.screenshot({ path: path.join(__dirname, 'assets', name + '.png'), clip: { x, y, width: w, height: h } });
    await ctx.close();
  }
  await browser.close();
})();
