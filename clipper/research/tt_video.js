// Open a TikTok video page, save the mp4 the player loads, plus item metadata.
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [url, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36', locale: 'en-US', viewport: {width: 1280, height: 900} });
  const page = await ctx.newPage();
  let saved = 0, meta = null;
  page.on('response', async (r) => {
    const ct = r.headers()['content-type'] || '';
    try {
      if (ct.includes('video/mp4') && !saved) {
        const b = await r.body(); if (b.length > 200000) { fs.writeFileSync(out + '.mp4', b); saved = b.length; }
      }
    } catch (e) {}
  });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const html = await page.content();
  const m = html.match(/<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([\s\S]*?)<\/script>/);
  if (m) { try { const d = JSON.parse(m[1]); meta = d.__DEFAULT_SCOPE__['webapp.video-detail']?.itemInfo?.itemStruct; } catch (e) {} }
  // fallback: fetch the playAddr inside the page context (cookies attached)
  for (let i = 0; i < 10 && !saved; i++) await page.waitForTimeout(1500);
  if (!saved && meta?.video?.playAddr) {
    const b64 = await page.evaluate(async (u) => { const r = await fetch(u, {credentials: 'include'}); const a = new Uint8Array(await r.arrayBuffer()); let s = ''; for (let i = 0; i < a.length; i += 0x8000) s += String.fromCharCode.apply(null, a.subarray(i, i + 0x8000)); return btoa(s); }, meta.video.playAddr).catch(() => null);
    if (b64) { const b = Buffer.from(b64, 'base64'); if (b.length > 200000) { fs.writeFileSync(out + '.mp4', b); saved = b.length; } }
  }
  if (meta) fs.writeFileSync(out + '.json', JSON.stringify({ desc: meta.desc, stats: meta.stats, video: { duration: meta.video?.duration, width: meta.video?.width, height: meta.video?.height }, music: meta.music, textExtra: meta.textExtra, author: meta.author?.uniqueId, authorStats: meta.authorStats }));
  console.log(url, 'mp4 bytes', saved, 'meta', !!meta);
  await browser.close();
})();
