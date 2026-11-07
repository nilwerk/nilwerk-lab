// Cut the English caption out of assets/v2-back-shell.png (top 50 px) -> assets/v2-back-shell-nocap.png (used on slide 6, EN and DE).
// Usage: NODE_PATH=<dir with playwright> node crop_nocap.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 250, height: 360 } });
  await p.goto('file://' + path.join(__dirname, 'assets', 'v2-back-shell.png'));
  await p.screenshot({ path: path.join(__dirname, 'assets', 'v2-back-shell-nocap.png'), clip: { x: 0, y: 50, width: 250, height: 310 } });
  await b.close();
})();
