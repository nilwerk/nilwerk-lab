// Usage: NODE_PATH=<playwright dir> node check_bbox.js pages.json  (pages: [{html, name}])
// Fails (exit 1) if any <text> reaches past x=1012 (right margin 1008) or below y=1340, or starts left of 60.
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const pages = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  let bad = 0;
  for (const p of pages) {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
    await page.goto('file://' + p.html);
    await page.evaluate(() => document.fonts.ready);
    const res = await page.evaluate(() => [...document.querySelectorAll('svg text')].map(t => {
      const b = t.getBBox(); return { s: t.textContent.slice(0, 40), l: b.x, r: b.x + b.width, b: b.y + b.height };
    }).filter(o => o.r > 1012 || o.l < 60 || o.b > 1340));
    for (const o of res) { console.log('OVERFLOW', p.name, JSON.stringify(o)); bad++; }
    await page.close();
  }
  await browser.close();
  console.log(bad ? `${bad} overflow(s)` : `bbox check: ${pages.length} images, 0 overflows`);
  process.exit(bad ? 1 : 0);
})();
