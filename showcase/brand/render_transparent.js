// Render SVG files to PNG with a TRANSPARENT background (RGBA). Usage:
//   NODE_PATH=<dir with playwright> node render_transparent.js <svg> <png> [<svg> <png> ...]
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const args = process.argv.slice(2);
  const browser = await chromium.launch();
  for (let i = 0; i < args.length; i += 2) {
    const svg = fs.readFileSync(args[i], 'utf8');
    const m = svg.match(/width="(\d+)" height="(\d+)"/);
    const w = +m[1], h = +m[2];
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    await page.setContent('<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:transparent}svg{display:block}</style>' + svg);
    await page.screenshot({ path: args[i + 1], omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } });
    await ctx.close();
    console.log('wrote (transparent)', args[i + 1]);
  }
  await browser.close();
})();
