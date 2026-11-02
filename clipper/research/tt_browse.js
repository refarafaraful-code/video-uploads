// Render a TikTok page in headless Chromium and capture every video item from the JSON API responses.
const { chromium } = require('playwright');
(async () => {
  const url = process.argv[2], out = process.argv[3];
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36', locale: 'en-US', viewport: {width: 1280, height: 900} });
  const page = await ctx.newPage();
  const items = {};
  const grab = (o) => {
    if (!o || typeof o !== 'object') return;
    if (Array.isArray(o)) return o.forEach(grab);
    if (o.id && o.stats && (o.desc !== undefined || o.video)) items[o.id] = o;
    Object.values(o).forEach(grab);
  };
  page.on('response', async (r) => {
    const ct = r.headers()['content-type'] || '';
    if (!ct.includes('json')) return;
    try { grab(await r.json()); } catch (e) {}
  });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  for (let i = 0; i < 8; i++) { await page.waitForTimeout(2500); await page.mouse.wheel(0, 3000); }
  const html = await page.content();
  require('fs').writeFileSync(out, JSON.stringify({ url, items: Object.values(items), links: [...new Set((html.match(/\/@[A-Za-z0-9._]+\/video\/\d+/g) || []))] }));
  console.log(url, 'items', Object.keys(items).length);
  await browser.close();
})();
