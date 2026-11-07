// Render HTML pages (inline SVG + embedded fonts) to PNG with headless Chromium.
// Usage: NODE_PATH=<dir with playwright> node render.js jobs.json
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const { scale, jobs } = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  for (const j of jobs) {
    const ctx = await browser.newContext({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: scale });
    const page = await ctx.newPage();
    await page.goto('file://' + j.html);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: j.png, clip: { x: 0, y: 0, width: j.w, height: j.h } });
    await ctx.close();
    console.log('wrote', j.png);
  }
  await browser.close();
})();
