// Render components.html (light and dark, full page) to PNG previews.
// Usage: NODE_PATH=<dir with playwright> node render_previews.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  for (const theme of ['light', 'dark']) {
    const ctx = await browser.newContext({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1, colorScheme: theme });
    const page = await ctx.newPage();
    await page.goto('file://' + path.join(__dirname, 'components.html') + '?theme=' + theme);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(__dirname, `components-${theme}.png`), fullPage: true });
    await ctx.close();
  }
  await browser.close();
})();
